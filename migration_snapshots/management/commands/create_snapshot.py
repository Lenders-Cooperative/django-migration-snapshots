from django.apps import apps
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--format", help="output format for digraph", required=False, default="pdf"
        )
        parser.add_argument(
            "--date",
            help="end date for migration history output",
            required=False,
            default="",
        )

    def handle(self, *args, **options):
        """
        Create migration snapshot using input arguments.
        Default format: 'pdf'
        """
        MigrationSnapshot = apps.get_model("migration_snapshots", "MigrationSnapshot")
        snapshot = MigrationSnapshot(
            output_format=options.get("format", MigrationSnapshot.PDF),
        )
        snapshot._date_end = options.get("date")
        snapshot.save()
