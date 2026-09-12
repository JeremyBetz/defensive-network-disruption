from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from defensive_network_disruption.geometry.canonical_comparison import compare_raw_provenance, compare_records


ROOT = Path(__file__).parents[1]


class Session14abCanonicalComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.local = json.loads((ROOT / "outputs/cross_platform_root_determinism/local_diagnostic.json").read_text())
        cls.ci = json.loads((ROOT / "outputs/cross_platform_root_determinism/ci_diagnostic.json").read_text())

    def test_session14aa_regression_separates_raw_from_canonical(self):
        self.assertNotEqual(self.local["records"], self.ci["records"])
        comparison = compare_records(self.local, self.ci)
        provenance = compare_raw_provenance(self.local, self.ci)
        self.assertTrue(comparison.canonical_structural_equal)
        self.assertTrue(comparison.final_components_bitwise_equal)
        self.assertFalse(provenance["raw_solver_provenance_equal"])
        self.assertEqual(len(provenance["differences"]), 1)
        self.assertEqual(provenance["differences"][0]["ulp_distance"], 1)

    def changed(self, operation):
        other = copy.deepcopy(self.local)
        operation(other["records"][0])
        self.assertFalse(compare_records(self.local, other).canonical_structural_equal)

    def test_every_canonical_difference_is_rejected(self):
        operations = (
            lambda row: row["routing"]["partitions"].__setitem__(1, row["routing"]["partitions"][1] + 1e-6),
            lambda row: row["routing"]["partition_bits"].__setitem__(1, "0000000000000001"),
            lambda row: row["routing"].__setitem__("residual_bound", 1e-9),
            lambda row: row["routing"].__setitem__("bounded_count", row["routing"]["bounded_count"] + 1),
            lambda row: row["accepted"].__setitem__("intervals", row["accepted"]["intervals"] * 2),
            lambda row: row["comparison"][0].__setitem__("actual_bits", "0000000000000001"),
        )
        for operation in operations:
            with self.subTest(operation=operation): self.changed(operation)
        switch_row = next(row for row in self.local["records"] if row["routing"]["switches"])
        other = copy.deepcopy(self.local)
        target = next(row for row in other["records"] if row["fixture"] == switch_row["fixture"] and row["candidate"] == switch_row["candidate"])
        target["routing"]["switches"][0]["owners_after"] = [99]
        self.assertFalse(compare_records(self.local, other).canonical_structural_equal)

    def test_provenance_is_retained_and_serializable(self):
        result = compare_raw_provenance(self.local, self.ci)
        raw = json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False)
        self.assertIn("raw_solver_provenance_equal", raw)
        self.assertIn("local_bits", raw)
        self.assertEqual(raw, json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False))


if __name__ == "__main__": unittest.main()
