from django.conf import settings

MIGRATION_SNAPSHOT_FILENAME = getattr(
    settings, "MIGRATION_SNAPSHOT_FILENAME", "migration_snapshot"
)
MIGRATION_SNAPSHOT_DIR = getattr(
    settings, "MIGRATION_SNAPSHOT_DIR", "migration_snapshots/"
)

MIGRATION_SNAPSHOT_MODEL = getattr(settings, "MIGRATION_SNAPSHOT_MODEL", False)
DEFAULT_SNAPSHOT_FORMAT = getattr(settings, "DEFAULT_SNAPSHOT_FORMAT", "pdf")
