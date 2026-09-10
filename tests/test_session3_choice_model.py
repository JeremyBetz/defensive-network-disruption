import unittest

import numpy as np
from scipy.optimize._numdiff import approx_derivative

from defensive_network_disruption.validation.choice_model import (
    conditional_objective,
    fit_conditional_softmax,
    identifiability,
    weighted_standardization,
)
from defensive_network_disruption.validation.ranking_metrics import expected_credits, match_macro


class ChoiceModelTests(unittest.TestCase):
    def test_training_match_weighted_standardization(self):
        features = {"a": [np.array([[0.0], [2.0]])], "b": [np.array([[8.0], [10.0]])]}
        mean, scale, zero = weighted_standardization(features)
        np.testing.assert_allclose(mean, [5.0])
        np.testing.assert_allclose(scale, [np.sqrt(17.0)])
        self.assertFalse(zero[0])

    def test_tie_expected_credit_and_outside_zero(self):
        credit = expected_credits(np.array([2.0, 2.0, 1.0]), 0)
        self.assertAlmostEqual(credit["rr"], 0.75)
        self.assertAlmostEqual(credit["hit1"], 0.5)
        self.assertEqual(credit["hit3"], 1.0)
        self.assertEqual(expected_credits(np.array([1.0, 0.0]), None)["rr"], 0.0)

    def test_equal_match_aggregation(self):
        self.assertEqual(match_macro({"a": {"mrr": 0.2}, "b": {"mrr": 0.8}}, "mrr"), 0.5)

    def test_analytic_gradient(self):
        features = {
            "a": [np.array([[0.1, -0.3], [0.7, 0.4]])],
            "b": [np.array([[1.2, 0.2], [-0.1, 0.8], [0.2, -0.5]])],
        }
        targets = {"a": [1], "b": [0]}
        beta = np.array([0.25, -0.4])
        _, analytic = conditional_objective(beta, features, targets)
        numeric = approx_derivative(lambda value: conditional_objective(value, features, targets)[0], beta)
        np.testing.assert_allclose(analytic, numeric, rtol=1e-6, atol=1e-8)

    def test_rank_and_separation_gates(self):
        deficient = identifiability(np.array([[1.0, 1.0], [-1.0, -1.0]]))
        self.assertEqual(deficient["rank"], 1)
        complete = identifiability(np.array([[1.0], [2.0]]))
        self.assertTrue(complete["complete_separation"])

    def test_deterministic_unregularized_fit(self):
        features = {
            "a": [np.array([[-1.0], [1.0]]), np.array([[1.0], [-1.0]])],
            "b": [np.array([[-2.0], [2.0]]), np.array([[2.0], [-2.0]])],
        }
        targets = {"a": [1, 1], "b": [0, 0]}
        first, first_qc = fit_conditional_softmax(features, targets)
        second, second_qc = fit_conditional_softmax(features, targets)
        np.testing.assert_array_equal(first, second)
        self.assertEqual(first_qc["objective"], second_qc["objective"])

    def test_tie_blocks_use_block_high(self):
        credit = expected_credits(np.array([1.0, 1.0 - 0.75e-12, 1.0 - 1.5e-12]), 2)
        self.assertAlmostEqual(credit["rr"], 1 / 3)
