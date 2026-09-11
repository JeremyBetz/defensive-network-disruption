"""Synthetic tests for the bounded Session 14s diagnostic path."""
from __future__ import annotations

import ast
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest
import warnings

import numpy as np
from scipy.integrate import IntegrationWarning

from defensive_network_disruption.geometry.max_warning_diagnosis import (
    WarningLocated, continuity_diagnostic, controlled_diagnostic, locate_warning,
    maximum_function, method_diagnostic, quad_diagnostic, width_summary,
)
from defensive_network_disruption.geometry.occlusion_fields import CarrierOriginField


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/session_14s_independent_max_warning_diagnosis.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("session14s", RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WarningDiagnosisTests(unittest.TestCase):
    def test_warning_locator_preserves_order_and_context(self):
        calls = []

        class Production:
            @staticmethod
            def quad(function, lower, upper, **kwargs):
                warnings.warn("synthetic warning", IntegrationWarning)
                return 0.25, 1e-9

        def evaluator(candidate, origin, receiver, defenders):
            calls.append((candidate, receiver))
            Production.quad(lambda _: 0.5, 0.1, 0.2, epsabs=1e-13)

        with self.assertRaises(WarningLocated) as caught:
            locate_warning(("isotropic", "expanding"), (0, 0), ((1, 0), (2, 0)),
                           ((0, 1),), evaluator, Production)
        record = caught.exception.record
        self.assertEqual(record.candidate, "isotropic")
        self.assertEqual(record.receiver_ordinal, 0)
        self.assertEqual((record.lower, record.upper), (0.1, 0.2))
        self.assertEqual(record.category, "IntegrationWarning")
        self.assertEqual(calls, [("isotropic", (1, 0))])

    def test_no_warning_returns_none_and_restores_quad(self):
        class Production:
            @staticmethod
            def quad(function, lower, upper, **kwargs):
                return 0.25, 0.0

        original = Production.quad

        def evaluator(candidate, origin, receiver, defenders):
            Production.quad(lambda _: 0.5, 0.0, 1.0)

        self.assertIsNone(locate_warning(("isotropic",), (0, 0), ((1, 0),),
                                        ((0, 1),), evaluator, Production))
        self.assertIs(Production.quad, original)

    def test_quad_full_output_is_bounded(self):
        result = quad_diagnostic(lambda x: x * x, 0.0, 1.0, 1e-13)
        self.assertAlmostEqual(result.value, 1 / 3)
        self.assertGreater(result.evaluations, 0)
        self.assertGreater(result.subdivisions, 0)
        self.assertIsNone(result.message)

    def test_partition_widths_and_adjacent_float(self):
        neighbor = float(np.nextafter(0.5, 1.0))
        result = width_summary((0.0, 0.5, neighbor, 1.0))
        self.assertEqual(result["piece_count"], 3)
        self.assertEqual(result["adjacent_float_pieces"], 1)
        self.assertEqual(result["minimum"], neighbor - 0.5)

    def test_invalid_partition_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_partition_width"):
            width_summary((0.0, 0.5, 0.5, 1.0))

    def test_controlled_joint_simpson_is_deterministic(self):
        field = CarrierOriginField("isotropic")
        result, estimates = controlled_diagnostic(field, (0, 0), (20, 0), ((5, 1), (10, -2)))
        self.assertTrue(result["converged"])
        self.assertTrue(result["finite"])
        self.assertTrue(result["deterministic"])
        self.assertIn(result["intervals"], (256, 512, 1024, 2048, 4096, 8192, 16384))
        self.assertEqual(set(estimates), {"individual_1", "individual_2", "union", "maximum"})

    def test_method_comparison_uses_authorized_methods(self):
        _, _, _, _, individual, onset, _, partitions = maximum_function(
            "expanding", (0, 0), (20, 0), ((5, 1), (10, -2)))
        values, differences, strict, repeat, unsplit, evaluations = method_diagnostic(
            individual, onset, partitions)
        self.assertEqual(set(values), {"piecewise_strict", "piecewise_repeat",
                                      "unsplit_adaptive", "direct_simpson_65536",
                                      "split_simpson_32768", "split_simpson_65536"})
        self.assertEqual(len(differences), 15)
        self.assertEqual(len(strict), len(partitions) - 1)
        self.assertEqual(len(repeat), len(strict))
        self.assertGreaterEqual(len(unsplit), 1)
        self.assertTrue(all(math.isfinite(value) for value in values.values()))
        self.assertEqual(len(evaluations), 2)

    def test_continuity_uses_independent_oracle(self):
        _, _, _, _, _, _, _, partitions = maximum_function(
            "constant_width", (0, 0), (20, 0), ((5, 1),))
        result = continuity_diagnostic("constant_width", (0, 0), (20, 0),
                                       ((5, 1),), partitions,
                                       (partitions[0], partitions[1]))
        self.assertTrue(result["analytical_continuity_obligation"])
        self.assertTrue(result["oracle_comparison_passed"])
        self.assertTrue(result["finite_step_is_not_continuity_proof"])

    def test_one_line_reads_only_requested_ordinal(self):
        runner = load_runner()
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "records.jsonl"
            path.write_text("first\nsecond\nthird\n")
            old_root = runner.ROOT
            try:
                runner.ROOT = Path(directory)
                self.assertEqual(runner.one_line(Path("records.jsonl"), 1), "second\n")
            finally:
                runner.ROOT = old_root

    def test_failing_row_is_exact_completed_state_count(self):
        runner = load_runner()
        self.assertEqual(runner.failing_row_ordinal({"states_completed": 1}), 1)
        for invalid in (True, -1, 1.0, None):
            with self.assertRaisesRegex(ValueError, "invalid_completed_state_count"):
                runner.failing_row_ordinal({"states_completed": invalid})

    def test_manifest_membership_and_finite_validation(self):
        runner = load_runner()
        self.assertEqual(len(runner.PUBLIC), 5)
        self.assertEqual(set(runner.PUBLIC), set(runner.SCHEMAS))
        runner.finite({"value": [1.0, 2.0]})
        with self.assertRaisesRegex(ValueError, "nonfinite_output"):
            runner.finite({"value": float("nan")})

    def test_runner_has_no_model_acquisition_or_science_routes(self):
        tree = ast.parse(RUNNER.read_text())
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(item.name for item in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        forbidden = ("receiver_ranking", "networks.options", "urllib", "requests", "socket", "kloppy")
        self.assertFalse(any(any(word in name for word in forbidden) for name in imports))
        commands = {node.value for node in ast.walk(tree)
                    if isinstance(node, ast.Constant) and isinstance(node.value, str)}
        self.assertTrue({"preflight", "diagnose", "publication-check"} <= commands)
        self.assertFalse({"analyze", "score", "fit", "acquire"} & commands)
        self.assertNotIn("partial_" + "summary", RUNNER.read_text())

    def test_failure_record_is_deterministic_and_sanitized(self):
        runner = load_runner()
        value = {"schema_version": 1, "status": "unresolved", "failure": "SyntheticError"}
        self.assertEqual(runner.encoded(value), runner.encoded(value))
        for forbidden in ("carrier_xy", "candidate_xy", "defender_xy", "event_id"):
            self.assertNotIn(forbidden, runner.encoded(value))


if __name__ == "__main__":
    unittest.main()
