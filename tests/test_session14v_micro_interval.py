"""Discoverable tests for the Session 14v bounded-residual verifier."""
from __future__ import annotations

import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import warnings
import importlib.util

import numpy as np
from scipy.integrate import IntegrationWarning

from defensive_network_disruption.geometry import micro_interval_verifier as m
from defensive_network_disruption.geometry import production_verification as p

ROOT = Path(__file__).resolve().parents[1]
HELPER_SPEC = importlib.util.spec_from_file_location(
    "session14ac_float_equivalence", ROOT / "tests/session14ac_float_equivalence.py")
HELPER = importlib.util.module_from_spec(HELPER_SPEC)
HELPER_SPEC.loader.exec_module(HELPER)
run_historical_acceptance = HELPER.run_historical_acceptance
SPEC = importlib.util.spec_from_file_location(
    "session14v_runner", ROOT / "scripts/session_14v_micro_interval_verifier.py")
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


def constant(value):
    return lambda t: np.full((len(t), 1), value, dtype=np.float64)


class Session14vMicroIntervalTests(unittest.TestCase):
    def test_interval_distances(self):
        a = m.IntegralInterval(1.0, 1.1, .1, 1, 0, 1)
        b = m.IntegralInterval(1.05, 1.2, .15, 1, 0, 1)
        c = m.IntegralInterval(1.3, 1.4, .1, 1, 0, 1)
        self.assertEqual(m.interval_distance(a, b), 0.0)
        self.assertAlmostEqual(m.interval_distance(a, c), .2)
        self.assertEqual(m.point_interval_distance(1.05, a), 0.0)
        self.assertAlmostEqual(m.point_interval_distance(1.3, a), .2)

    def test_field_bound_and_exact_constant_containment(self):
        tiny = 1e-13
        result = m.bounded_adaptive_maximum(constant(1.0), (0.0, tiny, 1.0), 1e-13)
        self.assertEqual(result.bounded_piece_count, 1)
        self.assertLessEqual(result.lower, 1.0)
        self.assertGreaterEqual(result.upper, 1.0)
        self.assertLessEqual(result.residual_bound, m.GLOBAL_RESIDUAL_BUDGET)
        with self.assertRaises(p.GateFailure):
            m.bounded_adaptive_maximum(constant(1.0), (0.0, 1.0), 1e-13,
                                       upper_bound=1.0000001)

    def test_zero_ordinary_and_multiple_micro_pieces(self):
        parts = (0.0, 1e-14, 2e-14, .5, 1.0)
        result = m.bounded_adaptive_maximum(constant(0.0), parts, 1e-13)
        self.assertEqual(result.bounded_piece_count, 2)
        self.assertEqual(result.quadrature_piece_count, 2)
        self.assertEqual(result.lower, 0.0)
        self.assertGreaterEqual(result.upper, 0.0)

    def test_realized_nextafter_threshold(self):
        count = 2
        threshold = m.GLOBAL_RESIDUAL_BUDGET / count
        below = float(np.nextafter(threshold, 0.0))
        above = float(np.nextafter(threshold, math.inf))
        accepted = m.bounded_adaptive_maximum(constant(.5), (0.0, below, 1.0), 1e-13)
        rejected = m.bounded_adaptive_maximum(constant(.5), (0.0, above, 1.0), 1e-13)
        self.assertEqual(accepted.bounded_piece_count, 1)
        self.assertEqual(rejected.bounded_piece_count, 0)

    def test_endpoint_adjacent_onset_and_switch_shapes(self):
        fixtures = {
            "endpoint": (0.0, float(np.nextafter(0.0, 1.0)), 1.0),
            "onset": (0.0, .5, float(np.nextafter(.5, 1.0)), 1.0),
            "switch": (0.0, float(np.nextafter(.5, 0.0)), .5, 1.0),
            "adjacent": (0.0, .25, float(np.nextafter(.25, 1.0)),
                         float(np.nextafter(np.nextafter(.25, 1.0), 1.0)), 1.0),
        }
        for name, parts in fixtures.items():
            with self.subTest(name=name):
                first = m.bounded_adaptive_maximum(constant(.25), parts, 1e-13)
                second = m.bounded_adaptive_maximum(constant(.25), parts, 1e-13)
                self.assertEqual(first, second)
                self.assertLessEqual(first.lower, .25)
                self.assertGreaterEqual(first.upper, .25)

    def test_structural_record_preserved_and_micro_not_quadrature(self):
        parts = (0.0, 1e-14, .4, 1.0)
        visited = []
        def fake_quad(function, lower, upper, **kwargs):
            visited.append((lower, upper)); return (upper - lower) * function(.5), 0.0
        with patch.object(p, "quad", side_effect=fake_quad):
            result = m.bounded_adaptive_maximum(constant(.5), parts, 1e-13)
        self.assertEqual(result.structural_piece_count, 3)
        self.assertEqual(visited, [(1e-14, .4), (.4, 1.0)])

    def test_warning_on_ordinary_piece_remains_blocking(self):
        def warned(*args, **kwargs):
            warnings.warn("ordinary warning", IntegrationWarning)
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            with patch.object(p, "quad", side_effect=warned):
                with self.assertRaises(IntegrationWarning):
                    m.bounded_adaptive_maximum(constant(.5), (0.0, .5, 1.0), 1e-13)

    def test_bad_partitions_and_nonfinite_comparison(self):
        for parts in ((0.0,), (0.0, 0.0, 1.0), (0.0, math.nan, 1.0)):
            with self.assertRaises(p.GateFailure):
                m.bounded_adaptive_maximum(constant(.5), parts, 1e-13)
        interval = m.IntegralInterval(0.0, 1.0, 1.0, 1, 0, 1)
        with self.assertRaises(p.GateFailure):
            m.point_interval_distance(math.nan, interval)

    def test_marker_collision_blocks_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = (Path(directory) / "marker").resolve()
            p.claim_execution(marker)
            with self.assertRaises(FileExistsError):
                p.claim_execution(marker)

    def test_complete_historical_synthetic_acceptance(self):
        cases, rows, comparisons = run_historical_acceptance(RUNNER)
        self.assertEqual(len(cases), 108)
        self.assertEqual(len(rows), 366)
        self.assertEqual(sum(case["permutations"] for case in cases), 399)
        self.assertTrue(all(row["passed"] for row in rows))
        self.assertTrue(all(row["equivalent"] for row in comparisons))

    def test_runner_routes_and_oracles(self):
        source = (ROOT / RUNNER.CODE[0]).read_text()
        self.assertIn('choices=("preflight", "audit", "publication-check")', source)
        for forbidden in ("acquire", "fit_model", "target_rank", "option_share"):
            self.assertNotIn(forbidden, source)
        rows = RUNNER.micro_oracles()
        self.assertEqual(len(rows), 9)
        self.assertTrue(all(row["contained"] for row in rows))


if __name__ == "__main__":
    unittest.main()
