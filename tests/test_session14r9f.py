"""Focused tests for the Session 14R9F portable authority."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from defensive_network_disruption.validation import r9f_portable_authority as authority

ROOT = Path(__file__).resolve().parents[1]


class Session14R9FTests(unittest.TestCase):
    def test_fixture_is_canonical_and_bound(self):
        value = authority.load_fixture(ROOT)
        self.assertEqual(value["semantic_projection_sha256"],
                         "b6e853d6cf3c97da328f4292a334b60e12ec98dfe624ad9602f04363008f0a2a")

    def test_deterministic_synthetic_fingerprints(self):
        context = {"alias": "synthetic", "origin": (0.0, -0.0),
                   "receiver": (1.0, 2.0), "defenders": ((3.0, 4.0),)}
        self.assertEqual(authority.selected_geometry_hash(context),
                         authority.selected_geometry_hash(context))
        changed = {**context, "receiver": (1.0, 2.0000000000000004)}
        self.assertNotEqual(authority.selected_geometry_hash(context),
                            authority.selected_geometry_hash(changed))

    def test_missing_and_tampered_fixture_fail(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as folder:
            base = Path(folder)
            with self.assertRaises(authority.PortableAuthorityError):
                authority.load_fixture(base)
            target = base / authority.FIXTURE
            target.parent.mkdir(parents=True)
            value = authority.load_fixture(ROOT)
            value["purpose"] = "changed"
            target.write_bytes(authority.canonical(value))
            for relative in (authority.MANIFEST, authority.INTERVAL):
                destination = base / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, destination)
            with self.assertRaises(authority.PortableAuthorityError):
                authority.load_fixture(base)

    def test_fixture_has_no_private_fallback_or_values(self):
        text = (ROOT / authority.FIXTURE).read_text().lower()
        for token in ("/users/", "/private/", "000010_selected_geometry.json",
                      "000020_structure.json", "000121_piece.json", "defenders"):
            self.assertNotIn(token, text)
        self.assertTrue(all(type(value) is not list for value in json.loads(text).values()))


if __name__ == "__main__":
    unittest.main()
