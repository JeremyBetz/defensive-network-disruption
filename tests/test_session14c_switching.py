"""Synthetic contract tests for Session 14c envelope switching."""
from __future__ import annotations

import ast
import math
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np

from defensive_network_disruption.geometry.maximum_envelope import (
    EnvelopeError,
    find_envelope_switches,
    integrate_maximum_piecewise,
    partition_points,
    split_simpson_maximum,
    switch_slopes,
)
from defensive_network_disruption.geometry.occlusion_fields import CarrierOriginField


RUNNER_PATH = Path(__file__).parents[1] / "scripts/session_14c_maximum_switching.py"


def functions(*items):
    def evaluate(t):
        values = [np.asarray(item(np.asarray(t, dtype=np.float64)), dtype=np.float64)
                  for item in items]
        return np.column_stack(values)
    return evaluate


class MaximumEnvelopeTests(unittest.TestCase):
    def test_single_crossing_and_analytic_integral(self):
        values = functions(lambda t: t, lambda t: 1.0 - t)
        result = find_envelope_switches(values, grid_intervals=64)
        interior = [item for item in result.switches if not item.endpoint]
        self.assertEqual(len(interior), 1)
        self.assertEqual(interior[0].location, 0.5)
        self.assertEqual(interior[0].owners_before, (1,))
        self.assertEqual(interior[0].owners_after, (0,))
        integral = integrate_maximum_piecewise(values, result)
        self.assertAlmostEqual(integral.value, 0.75, places=14)
        direct, intervals, evaluations = split_simpson_maximum(
            values, integral.partitions, 128)
        self.assertAlmostEqual(direct, 0.75, places=14)
        self.assertEqual(intervals, 128)
        self.assertEqual(evaluations, 130)

    def test_non_envelope_crossing_and_no_switch(self):
        values = functions(lambda t: 0.2 + 0.1*t, lambda t: 0.3 - 0.1*t,
                           lambda t: np.full_like(t, 0.8))
        result = find_envelope_switches(values, grid_intervals=64)
        self.assertFalse(result.switches)
        self.assertEqual(result.maximizing_defenders, (2,))

    def test_multiple_crossings_and_slopes(self):
        values = functions(lambda t: 0.5 + 0.2*np.sin(4.0*math.pi*t),
                           lambda t: np.full_like(t, 0.5))
        result = find_envelope_switches(values, grid_intervals=128)
        locations = [item.location for item in result.switches if not item.endpoint]
        self.assertEqual(locations, [0.25, 0.5, 0.75])
        slopes = switch_slopes(values, result, partition_points(result, ()))
        self.assertEqual(len(slopes), 3)
        self.assertTrue(all(item["continuous"] for item in slopes))
        self.assertTrue(any(abs(item["slope_change"]) > 1.0 for item in slopes))

    def test_endpoint_tie_is_recorded(self):
        values = functions(lambda t: 0.5 + 0.4*t, lambda t: 0.5 - 0.1*t)
        result = find_envelope_switches(values, grid_intervals=64)
        endpoints = [item for item in result.switches if item.endpoint]
        self.assertEqual(len(endpoints), 1)
        self.assertEqual(endpoints[0].location, 0.0)
        self.assertEqual(endpoints[0].owners_at, (0, 1))

    def test_exact_maximal_tie_interval(self):
        values = functions(lambda t: np.full_like(t, 0.7),
                           lambda t: np.full_like(t, 0.7),
                           lambda t: np.full_like(t, 0.2))
        result = find_envelope_switches(values, grid_intervals=32)
        self.assertFalse(result.switches)
        self.assertEqual(len(result.tie_intervals), 1)
        self.assertEqual(result.tie_intervals[0].start, 0.0)
        self.assertEqual(result.tie_intervals[0].end, 1.0)
        self.assertEqual(result.tie_intervals[0].owners, (0, 1))

    def test_three_way_switch(self):
        values = functions(lambda t: t, lambda t: 1.0-t,
                           lambda t: np.full_like(t, 0.5))
        result = find_envelope_switches(values, grid_intervals=64)
        interior = [item for item in result.switches if not item.endpoint]
        self.assertEqual(len(interior), 1)
        self.assertEqual(interior[0].owners_at, (0, 1, 2))
        self.assertTrue(interior[0].multiway)

    def test_all_zero_support_has_no_owner(self):
        values = functions(lambda t: np.zeros_like(t), lambda t: np.zeros_like(t))
        result = find_envelope_switches(values, grid_intervals=32)
        self.assertFalse(result.switches)
        self.assertFalse(result.tie_intervals)
        self.assertFalse(result.maximizing_defenders)

    def test_permutation_equivalence(self):
        original = functions(lambda t: t, lambda t: 1.0-t,
                             lambda t: np.full_like(t, 0.2))
        permuted = functions(lambda t: np.full_like(t, 0.2),
                             lambda t: t, lambda t: 1.0-t)
        first = find_envelope_switches(original, grid_intervals=64)
        second = find_envelope_switches(permuted, grid_intervals=64)
        mapping = {0: 2, 1: 0, 2: 1}
        self.assertEqual([item.location for item in first.switches],
                         [item.location for item in second.switches])
        mapped = tuple(sorted(mapping[index] for index in second.switches[0].owners_at))
        self.assertEqual(mapped, first.switches[0].owners_at)

    def test_bracket_failure_is_fail_closed(self):
        values = functions(lambda t: 0.9*t + 0.001, lambda t: 1.0-t)
        with patch("defensive_network_disruption.geometry.maximum_envelope.brentq",
                   side_effect=RuntimeError("synthetic")):
            with self.assertRaisesRegex(EnvelopeError, "bracketed_root_failed"):
                find_envelope_switches(values, grid_intervals=64)

    def test_partition_deduplication(self):
        values = functions(lambda t: t, lambda t: 1.0-t)
        result = find_envelope_switches(values, grid_intervals=64,
                                        extra_partitions=(0.5 + 5e-13,))
        self.assertEqual(partition_points(result, (0.5 + 5e-13,)), (0.0, 0.5, 1.0))

    def test_occlusion_field_rigid_transform_invariance(self):
        origin = np.array((0.0, 0.0)); receiver = np.array((20.0, 3.0))
        defenders = np.array(((5.0, 1.0), (11.0, -2.0), (17.0, 4.0)))
        angle = 0.61
        rotation = np.array(((math.cos(angle), -math.sin(angle)),
                             (math.sin(angle), math.cos(angle))))
        shift = np.array((13.0, -8.0))

        def field_values(candidate, b, q, ds):
            field = CarrierOriginField(candidate)
            def evaluate(t):
                points = b[None, :] + np.asarray(t)[:, None]*(q-b)[None, :]
                return field.individual_values(b, ds, points)
            return evaluate

        transformed_origin = origin @ rotation.T + shift
        transformed_receiver = receiver @ rotation.T + shift
        transformed_defenders = defenders @ rotation.T + shift
        for candidate in ("isotropic", "expanding", "constant_width"):
            first = find_envelope_switches(field_values(candidate, origin, receiver, defenders),
                                           grid_intervals=1024)
            second = find_envelope_switches(field_values(candidate, transformed_origin,
                                                          transformed_receiver,
                                                          transformed_defenders),
                                            grid_intervals=1024)
            self.assertEqual(len(first.switches), len(second.switches))
            np.testing.assert_allclose([item.location for item in first.switches],
                                       [item.location for item in second.switches],
                                       atol=2e-15, rtol=0.0)
            self.assertEqual([item.owners_before for item in first.switches],
                             [item.owners_before for item in second.switches])

    def test_runner_has_no_empirical_or_model_route(self):
        if not RUNNER_PATH.exists():
            self.skipTest("runner not yet present")
        tree = ast.parse(RUNNER_PATH.read_text())
        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        self.assertFalse(names & {"evaluate_options", "FrozenOptionModel", "minimize", "urlopen"})
        text = RUNNER_PATH.read_text()
        for forbidden in ("population" + ".jsonl", "player_" + "targeted_id"):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
