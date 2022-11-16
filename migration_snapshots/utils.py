import os
from datetime import datetime
from tempfile import NamedTemporaryFile
from typing import Any, Optional, Tuple, Union

from django.db import connection
from django.db.migrations.exceptions import NodeNotFoundError
from django.db.migrations.graph import MigrationGraph, Node
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.recorder import MigrationRecorder
from django.utils import timezone
from graphviz import Digraph


class TimeBasedMigrationLoader(MigrationLoader):
    """
    `TimeBasedMigrationLoader` inherits from Django's default `MigrationLoader`
    overriding the queryset from the `MigrationRecorder` - allowing the filtering of recorded migrations by any provided timestamp.
    The default is the current timezone-aware timestamp which will fetch all recorded migrations.
    """

    def __init__(
        self,
        *args: Any,
        date_end: Optional[datetime],
        **kwargs: bool,
    ) -> None:
        if not isinstance(date_end, datetime):
            raise ValueError("Datetime argument must be a datetime object")

        self.date_end = date_end or timezone.now()
        super().__init__(*args, **kwargs)

    def build_graph(self) -> None:
        """
        Build a migration dependency graph using both the disk and database.
        You'll need to rebuild the graph if you apply migrations. This isn't
        usually a problem as generally migration stuff runs in a one-shot process.
        """
        # Load disk data
        self.load_disk()
        # Load database data
        recorder = MigrationRecorder(self.connection)
        filtered_migration_qs = recorder.migration_qs.filter(applied__lt=self.date_end)

        self.applied_migrations = (
            {
                (migration.app, migration.name): migration
                for migration in filtered_migration_qs
            }
            if recorder.has_table()
            else {}
        )

        # To start, populate the migration graph with nodes for ALL migrations
        # and their dependencies. Also make note of replacing migrations at this step.
        self.graph = MigrationGraph()
        self.replacements = {}
        for key, migration in self.disk_migrations.copy().items():
            if key not in self.applied_migrations:
                del self.disk_migrations[key]
                continue

            self.graph.add_node(key, migration)

            # Replacing migrations.
            if migration.replaces:
                self.replacements[key] = migration
        for key, migration in self.disk_migrations.items():
            # Internal (same app) dependencies.
            self.add_internal_dependencies(key, migration)
        # Add external dependencies now that the internal ones have been resolved.
        for key, migration in self.disk_migrations.items():
            self.add_external_dependencies(key, migration)
        # Carry out replacements where possible and if enabled.
        if self.replace_migrations:
            for key, migration in self.replacements.items():
                # Get applied status of each of this migration's replacement
                # targets.
                applied_statuses = [
                    (target in self.applied_migrations) for target in migration.replaces
                ]
                # The replacing migration is only marked as applied if all of
                # its replacement targets are.
                if all(applied_statuses):
                    self.applied_migrations[key] = migration
                else:
                    self.applied_migrations.pop(key, None)
                # A replacing migration can be used if either all or none of
                # its replacement targets have been applied.
                if all(applied_statuses) or (not any(applied_statuses)):
                    self.graph.remove_replaced_nodes(key, migration.replaces)
                else:
                    # This replacing migration cannot be used because it is
                    # partially applied. Remove it from the graph and remap
                    # dependencies to it (#25945).
                    self.graph.remove_replacement_node(key, migration.replaces)
        # Ensure the graph is consistent.
        try:
            self.graph.validate_consistency()
        except NodeNotFoundError as excp:
            # Check if the missing node could have been replaced by any squash
            # migration but wasn't because the squash migration was partially
            # applied before. In that case raise a more understandable exception
            # (#23556).
            # Get reverse replacements.
            reverse_replacements = {}
            for key, migration in self.replacements.items():
                for replaced in migration.replaces:
                    reverse_replacements.setdefault(replaced, set()).add(key)
            # Try to reraise exception with more detail.
            if excp.node in reverse_replacements:
                candidates = reverse_replacements.get(excp.node, set())
                is_replaced = any(
                    candidate in self.graph.nodes for candidate in candidates
                )
                if not is_replaced:
                    tries = ", ".join("%s.%s" % c for c in candidates)
                    raise NodeNotFoundError(
                        "Migration {0} depends on nonexistent node ('{1}', '{2}'). "
                        "Django tried to replace migration {1}.{2} with any of [{3}] "
                        "but wasn't able to because some of the replaced migrations "
                        "are already applied.".format(
                            excp.origin, excp.node[0], excp.node[1], tries
                        ),
                        excp.node,
                    ) from excp
            raise
        self.graph.ensure_not_cyclic()


class MigrationHistoryUtil:
    def __init__(
        self,
        *,
        output_format: str = "pdf",
        filename: str = "migration_snapshot",
        delimiter: str = "/",
        **options: dict,
    ) -> None:
        """
        Initialize TimeBaseMigrationLoader based on timestamp
        and set object attributes
        """
        self.migration_loader = TimeBasedMigrationLoader(
            options.get("connection", connection),
            date_end=options.get("date_end", timezone.now()),
        )

        self.delimiter = delimiter
        self.filename = os.path.splitext(filename)[0]
        self.digraph = Digraph(format=output_format)

    def _format_label(self, tupled_node: Tuple[str, str]) -> str:
        """
        Hook to provide custom formatting if desired
        """
        return f"{self.delimiter}".join(tupled_node)

    @staticmethod
    def _get_node_details(node: Node) -> Tuple[str, str]:
        """
        Create node details tuple.
        """
        return (node.app_label, node.name)

    def construct_digraph(self) -> None:
        """
        Construct digraph by adding nodes and node dependencies to digraph object.
        """
        for node in sorted(self.graph.nodes.values(), key=self._get_node_details):
            self.add_node(node)
            self.add_nested_edges(node)

    def add_node(self, node: Node) -> None:
        """
        Create node label and add formatted node tuple.
        """
        node_label = self._format_label(self._get_node_details(node))
        self.digraph.node(node_label, node_label)

    def add_edges(self, node_to: Node, node_from: Node) -> None:
        """
        Add digraph edges between two nodes with formatted labels.
        """
        self.digraph.edge(self._format_label(node_from), self._format_label(node_to))

    def add_nested_edges(self, node: Node) -> None:
        """
        Loop over node dependencies and add respective edges.
        """
        for dep in node.dependencies:
            if dep[-1] == "__first__":
                self.add_edges(
                    self.graph.root_nodes(dep[0])[0], self._get_node_details(node)
                )
            elif dep[-1] == "__latest__":
                self.add_edges(
                    self.graph.leaf_nodes(dep[0])[0], self._get_node_details(node)
                )
            else:
                self.add_edges(dep, self._get_node_details(node))

    def create_snapshot(
        self, *, view: bool = False, temp_file: bool = False, **kwargs: Union[bool, str]
    ) -> str:
        """
        Construct digraph and create either:
        1.) a temporary file for view-only
        2.) graphical output to disk.
        """
        self.construct_digraph()
        if temp_file is True:
            with NamedTemporaryFile() as temp:
                filename = self.digraph.render(temp.name, view=True, **kwargs)
        else:
            filename = self.digraph.render(self.filename, view=view, **kwargs)

        return filename

    @property
    def graph(self) -> MigrationGraph:
        return self.migration_loader.graph

    @property
    def source(self) -> str:
        """
        Textual format output of a digraph structure.
        """
        return self.digraph.source
