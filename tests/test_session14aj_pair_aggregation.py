"""Synthetic tests for Session 14aj state-first pair aggregation."""
import importlib.util
import math
from pathlib import Path
import unittest

from defensive_network_disruption.geometry.representation_study import order_categories, spearman
from defensive_network_disruption.validation.pair_aggregation import (
    StatePairRecord, StateSummary, aggregate_pair_family, aggregate_states,
    inverse_ecdf_summary, reduce_categories_within_state,
    reduce_pairs_within_state,
)

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("session14aj", ROOT / "scripts/session_14aj_pair_aggregation.py")
RUNNER = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(RUNNER)


class Session14ajPairAggregationTests(unittest.TestCase):
    def row(self, records, alias="macro"):
        return next(row for row in aggregate_pair_family(records) if row["alias"] == alias)

    def test_unequal_pair_counts_have_equal_state_weight(self):
        records = (StatePairRecord("m", "a", (0.0,)),
                   StatePairRecord("m", "b", (1.0,) * 100))
        result = self.row(records, "m")
        self.assertEqual(result["mean"], 0.5)
        self.assertNotEqual(result["mean"], 100 / 101)
        self.assertEqual((result["observations"], result["source_observations"]), (2, 101))

    def test_r7_percentile_regression(self):
        records = (StatePairRecord("m", "a", (0.0, 1.0)),
                   StatePairRecord("m", "b", (1.0, 1.0)))
        result = self.row(records, "m")
        self.assertEqual((result["minimum"], result["q50"], result["maximum"]), (0.5, 0.5, 1.0))
        self.assertTrue(RUNNER.r7_regression()["repaired_passed"])
        self.assertTrue(RUNNER.r7_regression()["historical_differs"])

    def test_unequal_match_sizes_have_equal_macro_weight(self):
        records = [StatePairRecord("small", "s", (0.0,))]
        records += [StatePairRecord("large", str(i), (1.0,)) for i in range(100)]
        result = self.row(tuple(records))
        self.assertEqual(result["mean"], 0.5)
        self.assertEqual(result["q50"], 0.0)
        self.assertEqual(result["represented_matches"], 2)

    def test_categories_reduce_to_state_proportions(self):
        reduced = reduce_categories_within_state((
            ("m", "many", ("agreement",) * 100),
            ("m", "few", ("strict_reversal",)),
        ), ("agreement", "strict_reversal"))
        discovered = (("m", "many"), ("m", "few"))
        for values in reduced.values():
            result = next(row for row in aggregate_states(discovered, values) if row["alias"] == "m")
            self.assertEqual(result["mean"], 0.5)
            self.assertEqual(result["unit"], "state_pair_proportion")

    def test_unavailable_single_and_multiple_states(self):
        records = (StatePairRecord("m", "empty", ()), StatePairRecord("m", "single", (0.25,)),
                   StatePairRecord("m", "many", (0.0, 1.0)))
        reduced = reduce_pairs_within_state(records)
        self.assertEqual([(row.state, row.value) for row in reduced], [("single", 0.25), ("many", 0.5)])
        result = self.row(records, "m")
        self.assertEqual((result["states_total"], result["states_assessable"],
                          result["states_unavailable"]), (3, 2, 1))
        self.assertEqual(result["unavailable_reason"], "no_eligible_pairs")

    def test_pair_eligibility_count_is_preserved(self):
        records = (StatePairRecord("m", "a", (0.0, 1.0, 1.0)),
                   StatePairRecord("m", "b", (1.0,)))
        result = self.row(records, "m")
        self.assertEqual(result["source_observations"], 4)
        self.assertEqual(result["observations"], 2)

    def test_exact_tie_and_order_semantics_are_unchanged(self):
        categories = order_categories([1.0, 1.0, 2.0], [1.0, 2.0, 1.0])
        self.assertEqual(sum(map(sum, categories.values())), 3.0)
        self.assertEqual(categories["tie_removal"], [1.0, 0.0, 0.0])
        self.assertIsNone(spearman([1.0, 1.0], [1.0, 2.0]))

    def test_non_pair_summary_invariance(self):
        evidence = RUNNER.non_pair_invariance()
        self.assertTrue(evidence["exact"])
        self.assertEqual(len(evidence["families"]), 6)

    def test_inventory_covers_every_frozen_pair_family(self):
        families = {row[0] for row in RUNNER.INVENTORY}
        self.assertEqual(len(families), 10)
        self.assertIn("candidate_field_difference", families)
        self.assertIn("opposing_field_order", families)
        self.assertIn("session13_support_jaccard", families)
        self.assertFalse(any(row[2] == "raw_pair" for row in RUNNER.INVENTORY))
        self.assertTrue(all(row[3] in {"match", "unavailable"} for row in RUNNER.INVENTORY))
        self.assertTrue(all(row[4] in {"macro_match", "unavailable"} for row in RUNNER.INVENTORY))

    def test_inverse_ecdf_boundary_and_empty(self):
        self.assertEqual(inverse_ecdf_summary([0.5, 1.0], [0.5, 0.5])["q50"], 0.5)
        self.assertIsNone(inverse_ecdf_summary([], [])["mean"])

    def test_invalid_records_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "nonfinite"):
            StatePairRecord("m", "s", (math.nan,))
        with self.assertRaisesRegex(ValueError, "duplicate_state"):
            reduce_pairs_within_state((StatePairRecord("m", "s", (1.0,)),
                                       StatePairRecord("m", "s", (1.0,))))
        with self.assertRaisesRegex(ValueError, "unsupported_pair_unit"):
            StateSummary("m", "s", 1.0, 1, "pair")
        with self.assertRaisesRegex(ValueError, "unknown_category"):
            reduce_categories_within_state((("m", "s", ("other",)),), ("agreement",))

    def test_deterministic_serialization(self):
        value = {"schema_version": 1, "mean": 0.5, "passed": True}
        self.assertEqual(RUNNER.canonical(value), RUNNER.canonical(value))
        self.assertTrue(RUNNER.canonical(value).endswith(b"\n"))

    def test_all_governed_oracles_pass(self):
        for rows in (RUNNER.pair_count_oracles(), RUNNER.percentile_oracles(),
                     RUNNER.match_oracles(), RUNNER.ordering_oracles(),
                     RUNNER.unavailable_oracles()):
            self.assertTrue(all(row["passed"] for row in rows))

    def test_no_data_model_or_numerical_routes(self):
        source = (ROOT / "scripts/session_14aj_pair_aggregation.py").read_text()
        implementation = (ROOT / "src/defensive_network_disruption/validation/pair_aggregation.py").read_text()
        for forbidden in ("def project_line", "evaluate_edge(", "load_model(",
                          "OptionNetwork", "requests.get", "from defensive_network_disruption.data"):
            self.assertNotIn(forbidden, source + implementation)


if __name__ == "__main__":
    unittest.main()
