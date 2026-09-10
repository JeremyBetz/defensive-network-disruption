import tempfile
import unittest
from pathlib import Path

from defensive_network_disruption.data.skillcorner_session2 import safe_destination, source_path


class Session2FirewallTests(unittest.TestCase):
    def test_allows_only_development_products(self):
        self.assertEqual(
            source_path("1886347", "events"),
            "data/matches/1886347/1886347_dynamic_events.csv",
        )
        for denied in ("1874553", "1953632", "2016236", "../../1886347"):
            with self.assertRaises(PermissionError):
                source_path(denied, "events")
        with self.assertRaises(PermissionError):
            source_path("1886347", "phases")

    def test_rejects_symlink_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").symlink_to(root / "elsewhere")
            with self.assertRaises(PermissionError):
                safe_destination(root, "1886347", "events")
