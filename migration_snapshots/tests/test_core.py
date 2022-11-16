from migration_snapshots import settings


def test_default_migration_snapshot_filename():
    assert settings.MIGRATION_SNAPSHOT_FILENAME == "migration_snapshot"


def test_default_migration_snapshot_dir():
    assert settings.MIGRATION_SNAPSHOT_DIR == "migration_snapshots/"


def test_default_migration_snapshot_model_bool():
    assert settings.MIGRATION_SNAPSHOT_MODEL is False


def test_default_snapshot_format():
    assert settings.DEFAULT_SNAPSHOT_FORMAT == "pdf"

