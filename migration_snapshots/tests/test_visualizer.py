from unittest.mock import MagicMock

from django.test import TestCase

from migration_snapshots.utils import MigrationHistoryUtil


class TestMigrationHistoryUtil(TestCase):
    def setUp(self):
        super().setUp()
        self.util_cls = MigrationHistoryUtil
        self.util = self.util_cls()

    def test_format_label(self):
        tupled_node = ("foo", "bar")
        label = self.util._format_label(tupled_node)
        assert label == "foo/bar"

    def test_get_node_details(self):
        mock = MagicMock()
        mock.app_label = "fizz"
        mock.name = "buzz"

        node_details = self.util_cls._get_node_details(mock)
        assert node_details == ("fizz", "buzz")
