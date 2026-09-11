"""Public API stability and release-audit tests for Session 10."""
from __future__ import annotations

import builtins
import importlib.util
import inspect
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

import defensive_network_disruption as dnd
from defensive_network_disruption.examples import demonstration_models, synthetic_option_state

SPEC = importlib.util.spec_from_file_location(
    "session10", Path(__file__).parents[1] / "scripts/session_10_release_readiness.py")
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class PublicContractTests(unittest.TestCase):
    def test_exact_root_exports_and_signatures(self):
        self.assertEqual(tuple(sorted(dnd.__all__)), RUNNER.EXPECTED_EXPORTS)
        self.assertEqual(tuple(inspect.signature(dnd.evaluate_options).parameters), ("state", "model"))
        self.assertEqual(tuple(inspect.signature(dnd.compare_options).parameters), ("left", "right"))
        self.assertEqual(tuple(inspect.signature(dnd.plot_option_network).parameters),
                         ("state", "network", "pitch_length", "pitch_width", "ax", "title"))

    def test_session9_numerics_unchanged(self):
        state = synthetic_option_state()
        m0, m1 = demonstration_models()
        left = dnd.evaluate_options(state, model=m0)
        right = dnd.evaluate_options(state, model=m1)
        np.testing.assert_array_equal(
            [edge.utility for edge in left.edges],
            [-0.5111102550927978, -0.7150000000000001,
             -0.6060249675906655, -1.1520509831248422],
        )
        np.testing.assert_array_equal(
            [edge.option_share for edge in right.edges],
            [0.20312043172951616, 0.16603873434030011,
             0.5281581964924411, 0.10268263743774268],
        )
        self.assertEqual(right.top_options, ("C",))
        self.assertEqual(right.effective_option_count, 3.2961834464235378)

    def test_actionable_state_and_model_errors(self):
        with self.assertRaisesRegex(ValueError, "candidate_ids must contain"):
            dnd.OptionState((0, 0), (), (), ((1, 1),))
        with self.assertRaisesRegex(ValueError, "candidate_ids must be unique"):
            dnd.OptionState((0, 0), ("A", "A"), ((1, 1), (2, 2)), ((3, 3),))
        with self.assertRaisesRegex(ValueError, "carrier_xy"):
            dnd.OptionState(None, ("A",), ((1, 1),), ((3, 3),))
        with self.assertRaisesRegex(ValueError, "name must be"):
            dnd.FrozenOptionModel("m2", (), (), (), ())
        with self.assertRaisesRegex(TypeError, "OptionState"):
            dnd.evaluate_options(object(), model=demonstration_models()[0])

    def test_actionable_missing_optional_dependencies(self):
        state = synthetic_option_state()
        network = dnd.evaluate_options(state, model=demonstration_models()[1])
        original_import = builtins.__import__

        def missing(name, *args, **kwargs):
            if name == "pandas":
                raise ImportError("synthetic")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=missing):
            with self.assertRaisesRegex(ImportError, "dataframe.*pip install"):
                network.to_pandas()

    def test_engineering_sanity_gate(self):
        result = RUNNER.audit_api()
        self.assertEqual(result["evaluations"], 1000)
        self.assertFalse(result["performance_claim"])
        self.assertLess(result["elapsed_seconds"], 10.0)


class DistributionGuardTests(unittest.TestCase):
    def test_distribution_member_firewall(self):
        for name in ("../secret", "/root/file", "project/data/raw.json", "project/outputs/x"):
            with self.assertRaises(RuntimeError):
                RUNNER._safe_member(name)
        self.assertEqual(str(RUNNER._safe_member("project/src/package.py")),
                         "project/src/package.py")

    def test_runner_has_no_acquisition_or_fitting_command(self):
        choices = ("preflight", "audit-api", "audit-distributions", "publication-check")
        self.assertNotIn("acquire", choices)
        self.assertNotIn("fit", choices)


if __name__ == "__main__":
    unittest.main()
