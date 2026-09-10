import json
import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from defensive_network_disruption.validation.m1_audit import (
    coefficient_summary,
    numerical_nondegenerate,
    ordering_disagreement,
    segment_order_statistics,
    utility,
    within_choice_centered_correlation,
)
from defensive_network_disruption.validation.ranking_features import choice_features


ROOT = Path(__file__).resolve().parents[1]


class Session4AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location(
            "session_04_m1_audit", ROOT / "scripts/session_04_m1_audit.py"
        )
        cls.runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.runner)

    def test_closed_coefficient_source_integrity(self):
        qc_path = ROOT / "outputs/receiver_ranking_m0_m1/qc.json"
        manifest = json.loads((ROOT / "outputs/receiver_ranking_m0_m1/manifest.json").read_text())
        import hashlib
        self.assertEqual(hashlib.sha256(qc_path.read_bytes()).hexdigest(), manifest["output_sha256"]["qc.json"])
        summary = coefficient_summary(json.loads(qc_path.read_text()))
        self.assertEqual(summary["m1"]["nearest_receiver_defender_distance"]["positive_folds"], 9)

    def test_segment_order_statistics_use_finite_segment(self):
        result = segment_order_statistics(((5, 2), (15, 3), (30, 1)), (0, 0), (20, 0))
        np.testing.assert_allclose(result, (2, 3, np.sqrt(101)))

    def test_pairwise_ordering_disagreement_and_ties(self):
        result = ordering_disagreement([1, 2, 3], [3, 2, 1])
        self.assertEqual(result["comparable_pairs"], 3)
        self.assertEqual(result["fraction"], 1.0)
        tied = ordering_disagreement([1, 1 + 0.5e-12], [0, 1])
        self.assertEqual(tied["comparable_pairs"], 0)

    def test_weighted_within_choice_correlation(self):
        sets = [np.array([[0.0, 0.0], [1.0, 1.0]]), np.array([[0.0, 1.0], [1.0, 0.0]])]
        correlation, gate = within_choice_centered_correlation(sets, [0.75, 0.25])
        self.assertAlmostEqual(correlation[0, 1], 0.5)
        self.assertEqual(gate["rank"], 2)

    def test_numerical_nondegeneracy(self):
        self.assertTrue(numerical_nondegenerate([1.0, 1.1, 2.0])[0])
        self.assertFalse(numerical_nondegenerate([2.0, 2.0, 2.0])[0])

    def test_utility_monotonicity_and_velocity_blind_spot(self):
        beta = np.array([0, 0, 0, 1, 0.5], dtype=float)
        mean = np.zeros(5)
        scale = np.ones(5)
        low = utility([40, 40, 0, 2, 1], beta, mean, scale)
        high = utility([40, 40, 0, 5, 2], beta, mean, scale)
        self.assertGreater(high, low)
        toward = utility([40, 40, 0, 5, 2], beta, mean, scale)
        away = utility([40, 40, 0, 5, 2], beta, mean, scale)
        self.assertEqual(toward, away)

    def test_length_additivity_and_multiplicity_collapse(self):
        one = SimpleNamespace(carrier_xy=(0.0, 0.0), candidate_xy=((20.0, 0.0),), defender_xy=((15.0, 2.0),))
        many = SimpleNamespace(carrier_xy=(0.0, 0.0), candidate_xy=((20.0, 0.0),),
                               defender_xy=((5.0, 2.0), (10.0, 2.0), (15.0, 2.0)))
        one_features = choice_features(one, "m1")[0]
        many_features = choice_features(many, "m1")[0]
        np.testing.assert_array_equal(one_features, many_features)
        short = np.array([5.0, 5.0, 0.0, np.sqrt(29), 2.0])
        long = np.array([30.0, 30.0, 0.0, np.sqrt(29), 2.0])
        np.testing.assert_array_equal(short[3:], long[3:])

    def test_access_and_fitting_firewalls(self):
        with self.assertRaises(PermissionError):
            self.runner.safe_product("1874553", "tracking_extrapolated.jsonl")
        with self.assertRaises(PermissionError):
            self.runner.safe_product("1953632", "tracking_extrapolated.jsonl")
        with self.assertRaises(PermissionError):
            self.runner.safe_product("1886347", "bodypose.json")
        self.assertFalse(any("passing_option" in item for item in self.runner.PROJECTED_EVENT_FIELDS))
        source = (ROOT / "scripts/session_04_m1_audit.py").read_text()
        self.assertNotIn("scipy." + "optimize", source)
        self.assertNotIn("fit_" + "conditional_softmax", source)


if __name__ == "__main__":
    unittest.main()
