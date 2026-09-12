from __future__ import annotations

import math
import unittest

import numpy as np

from defensive_network_disruption.geometry.root_partition_determinism import (
    VerificationError,
    certify_switch,
    deterministic_directional_onsets,
    deterministic_partitions,
)
from defensive_network_disruption.geometry.verification_repair import find_verified_envelope


class Session14aaRootDeterminismTests(unittest.TestCase):
    @staticmethod
    def crossing(root: float, slope: float = 0.25):
        return lambda t: np.column_stack((np.full_like(t, 0.5), 0.5 + slope * (t - root)))

    def test_exact_and_between_float_crossings_are_certified(self):
        for seed in (1.0 / 7.0, 0.14285714285714282, 0.14285714285714285,
                     float(np.nextafter(0.5, 1.0))):
            function = self.crossing(1.0 / 7.0 if seed < 0.2 else 0.5)
            envelope = find_verified_envelope(function, grid_intervals=128)
            record = certify_switch(function, envelope.switches[0])
            self.assertLess(record.last_pre_switch, record.first_post_switch)
            self.assertEqual(record.canonical, record.first_post_switch)
            self.assertEqual(record.owners_before, (0,))
            self.assertEqual(record.owners_after, (1,))

    def test_shallow_steep_endpoint_adjacent_and_multiple_roots(self):
        for root, slope in ((0.25, 1e-6), (0.75, 0.4),
                            (float(np.nextafter(0.0, 1.0)), 0.25),
                            (float(np.nextafter(1.0, 0.0)), 0.25)):
            function = self.crossing(root, slope)
            envelope = find_verified_envelope(function, grid_intervals=256)
            if envelope.switches and not envelope.switches[0].endpoint:
                self.assertTrue(math.isfinite(certify_switch(function, envelope.switches[0]).canonical))
            elif envelope.switches:
                self.assertTrue(envelope.switches[0].endpoint)
        function = lambda t: np.column_stack((np.full_like(t, 0.5), 0.5 + 0.2 * (t - 0.25) * (t - 0.75)))
        envelope = find_verified_envelope(function, grid_intervals=256)
        self.assertEqual(len(envelope.switches), 2)
        self.assertEqual(len(tuple(certify_switch(function, item) for item in envelope.switches)), 2)

    def test_deterministic_onsets_use_post_branch_float(self):
        records = deterministic_directional_onsets((0.0, 0.0), (20.0, 0.0), ((5.0, 1.0),))
        self.assertEqual(len(records), 2)
        for item in records:
            self.assertEqual(float(np.nextafter(item.last_pre_branch, math.inf)), item.first_post_branch)
        repeated = deterministic_directional_onsets((0.0, 0.0), (20.0, 0.0), ((5.0, 1.0),))
        self.assertEqual(records, repeated)

    def test_partition_tags_preserve_tie_enclosure_endpoints(self):
        def plateau(t):
            second = np.where((t >= 0.25) & (t <= 0.75), 0.6, 0.5)
            first = np.full_like(t, 0.6)
            return np.column_stack((first, second))
        envelope = find_verified_envelope(plateau, grid_intervals=128)
        parts, switches = deterministic_partitions(plateau, envelope, ())
        self.assertFalse(switches)
        for tie in envelope.tie_intervals:
            for boundary in (tie.start, tie.end):
                if boundary is not None:
                    self.assertIn(boundary.outside, parts)
                    self.assertIn(boundary.inside, parts)

    def test_ambiguous_or_invalid_transition_fails_closed(self):
        function = lambda t: np.column_stack((np.full_like(t, 0.5), np.full_like(t, 0.5)))
        envelope = find_verified_envelope(function, grid_intervals=64)
        self.assertFalse(envelope.switches)
        with self.assertRaises(VerificationError):
            deterministic_directional_onsets((0.0, 0.0), (1.0, 0.0), ((0.0, 0.0),))


if __name__ == "__main__":
    unittest.main()
