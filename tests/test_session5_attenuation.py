import math
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np

from defensive_network_disruption.geometry.attenuation import summed_segment_attenuation
from defensive_network_disruption.validation.session5 import (
    choice_features_m1_m2,
    fail_closed_identifiability,
    fit_with_fail_closed_gate,
)


class Session5AttenuationTests(unittest.TestCase):
    def test_exact_anchors_and_multiplicity(self):
        start, end = (0.0, 0.0), (20.0, 0.0)
        self.assertEqual(summed_segment_attenuation(((10.0, 0.0),), start, end), 1.0)
        self.assertEqual(summed_segment_attenuation(((10.0, 5.0),), start, end), math.exp(-1))
        self.assertEqual(summed_segment_attenuation(((10.0, 10.0),), start, end), math.exp(-2))
        one = summed_segment_attenuation(((10.0, 5.0),), start, end)
        two = summed_segment_attenuation(((10.0, 5.0), (10.0, -5.0)), start, end)
        self.assertEqual(two, 2 * one)

    def test_multiplicity_monotonicity_and_permutation(self):
        start, end = (0.0, 0.0), (20.0, 0.0)
        one = ((15.0, 2.0),)
        three = ((5.0, 2.0), (10.0, 2.0), (15.0, 2.0))
        self.assertGreater(summed_segment_attenuation(three, start, end), summed_segment_attenuation(one, start, end))
        baseline = summed_segment_attenuation(three, start, end)
        self.assertEqual(baseline, summed_segment_attenuation(tuple(reversed(three)), start, end))
        self.assertGreaterEqual(summed_segment_attenuation(((5.0, 1.0), *three[1:]), start, end), baseline)
        self.assertLessEqual(summed_segment_attenuation(((5.0, 3.0), *three[1:]), start, end), baseline)

    def test_degenerate_extreme_and_rejections(self):
        value = summed_segment_attenuation(((3.0, 4.0),), (0.0, 0.0), (0.0, 0.0))
        self.assertEqual(value, math.exp(-1))
        self.assertEqual(summed_segment_attenuation(((0.0, 1e308),), (0.0, 0.0), (1.0, 0.0)), 0.0)
        with self.assertRaises(ValueError):
            summed_segment_attenuation((), (0.0, 0.0), (1.0, 0.0))
        with self.assertRaises(ValueError):
            summed_segment_attenuation(((math.nan, 0.0),), (0.0, 0.0), (1.0, 0.0))

    def test_strict_nesting(self):
        choice = SimpleNamespace(
            carrier_xy=(0.0, 0.0), candidate_xy=((3.0, 4.0), (-2.0, 0.0)),
            defender_xy=((3.0, 4.0), (1.0, 0.0)),
        )
        m1, m2, _ = choice_features_m1_m2(choice)
        np.testing.assert_array_equal(m1, m2[:, :5])
        self.assertEqual(m2.shape, (2, 6))

    def test_solver_status_fails_closed(self):
        inconclusive = SimpleNamespace(status=4, success=False, fun=math.nan)
        with self.assertRaises(RuntimeError):
            fail_closed_identifiability(np.array([[1.0], [-1.0]]), linprog_fn=Mock(return_value=inconclusive))

    def test_synthetic_fit_is_deterministic(self):
        features = {
            "a": [np.array([[-1.0, 0.2], [1.0, -0.1]]), np.array([[1.0, -0.3], [-1.0, 0.2]])],
            "b": [np.array([[-2.0, -0.3], [2.0, 0.2]]), np.array([[2.0, 0.3], [-2.0, -0.2]])],
        }
        targets = {"a": [1, 1], "b": [0, 0]}
        first, first_qc = fit_with_fail_closed_gate(features, targets)
        second, second_qc = fit_with_fail_closed_gate(features, targets)
        np.testing.assert_array_equal(first, second)
        self.assertEqual(first_qc, second_qc)
