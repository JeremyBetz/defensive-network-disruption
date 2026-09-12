"""Focused tests for the Session 14ac historical-vector contract."""
from __future__ import annotations

import copy
import importlib.util
import math
from pathlib import Path
import unittest

from defensive_network_disruption.geometry.canonical_comparison import compare_records

from session14ac_float_equivalence import compare_historical_vector, component_tolerance

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("session14ac_runner", ROOT / "scripts/session_14ac_final_float_equivalence.py")
RUNNER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(RUNNER)


class Session14acFloatEquivalenceTests(unittest.TestCase):
    def test_exact_one_ulp_signed_zero_and_scale(self):
        expected = {"a": .25, "b": 0.0}
        for actual in (expected, {"a": math.nextafter(.25, math.inf), "b": -0.0}):
            result = compare_historical_vector(512, expected, 512, actual)
            self.assertTrue(result["equivalent"], result)
        outside = .25 + 128 * math.ulp(1.0)
        result = compare_historical_vector(512, expected, 512, {"a": outside, "b": 0.0})
        self.assertFalse(result["equivalent"])
        self.assertEqual(result["failed_component"], "a")
        self.assertLess(component_tolerance(.25, outside), abs(.25 - outside))

    def test_nonfinite_order_membership_and_resolution_fail(self):
        expected = {"a": .25, "b": .5}
        controls = (
            (512, {"a": math.nan, "b": .5}, "a"),
            (512, {"a": math.inf, "b": .5}, "a"),
            (512, {"b": .5, "a": .25}, "component_order"),
            (512, {"a": .25}, "component_order"),
            (1024, expected, "accepted_intervals"),
        )
        for intervals, actual, failure in controls:
            with self.subTest(failure=failure):
                result = compare_historical_vector(512, expected, intervals, actual)
                self.assertFalse(result["equivalent"])
                self.assertEqual(result["failed_component"], failure)

    def test_structural_negative_control_and_runner_routes(self):
        local = __import__("json").loads((ROOT / RUNNER.LOCAL).read_text())
        changed = copy.deepcopy(local)
        changed["records"][0]["routing"]["quadrature_count"] += 1
        self.assertFalse(compare_records(local, changed).canonical_structural_equal)
        source = (ROOT / "scripts/session_14ac_final_float_equivalence.py").read_text()
        for forbidden in ("session_14r", "provider", "target_rank", "option_share", "fit_model"):
            self.assertNotIn(forbidden, source.lower())


if __name__ == "__main__":
    unittest.main()
