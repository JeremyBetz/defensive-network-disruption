from __future__ import annotations

import itertools
import unittest

import numpy as np

from defensive_network_disruption.geometry import production_verification as production
from defensive_network_disruption.geometry.verification_repair import (
    find_verified_envelope,
    mapped_signature,
)


def _historical_tie_records(result, permutation):
    owners = lambda seq: tuple(sorted(permutation[i] for i in seq))
    boundary = lambda value: None if value is None else (
        value.outside,
        value.inside,
        value.direction,
        tuple(sorted(permutation[i] for i in value.pair)),
        owners(value.owners),
    )
    return tuple(
        (boundary(item.start), boundary(item.end), owners(item.owners),
         tuple(sorted(tuple(sorted((permutation[a], permutation[b]))) for a, b in item.pairs)))
        for item in result.tie_intervals
    )


class Session14iSignatureRepairTests(unittest.TestCase):
    def test_historical_multiway_plateau_typeerror_and_repaired_signature(self):
        function = production.engineering_functions()["multiway_plateau"]
        envelope = find_verified_envelope(function)
        identity = tuple(range(4))
        records = _historical_tie_records(envelope, identity)
        self.assertTrue(any(record[0] is None for record in records))
        self.assertTrue(any(isinstance(record[0], tuple) for record in records))
        with self.assertRaisesRegex(TypeError, "NoneType"):
            tuple(sorted(records))

        signature = mapped_signature(envelope, identity)
        self.assertEqual(len(signature[1]), len(envelope.tie_intervals))
        self.assertTrue(any(record[0] is None for record in signature[1]))
        self.assertTrue(any(len(record[2]) >= 3 for record in signature[1]))
        self.assertEqual(signature, mapped_signature(envelope, identity))

    def test_endpoint_and_interior_boundaries_have_total_order(self):
        fixtures = {
            "both_endpoints": lambda t: np.column_stack((np.full_like(t, .6), np.full_like(t, .6))),
            "left_endpoint": lambda t: np.column_stack((np.full_like(t, .6), .6-.1*np.maximum(t-.75, 0.))),
            "right_endpoint": lambda t: np.column_stack((np.full_like(t, .6), .6-.1*np.maximum(.25-t, 0.))),
            "interior": lambda t: np.column_stack((np.full_like(t, .6), np.where(
                (t >= .251) & (t <= .749), .6, np.nextafter(.6, 0.)))),
            "isolated": lambda t: np.column_stack((t, 1.-t)),
            "multiple": lambda t: np.column_stack((np.full_like(t, .6), np.where(
                ((t >= .125) & (t <= .25)) | ((t >= .75) & (t <= .875)),
                .6, np.nextafter(.6, 0.)))),
        }
        for name, function in fixtures.items():
            with self.subTest(name=name):
                envelope = find_verified_envelope(function)
                first = mapped_signature(envelope, (0, 1))
                second = mapped_signature(envelope, (0, 1))
                self.assertEqual(first, second)
                if name == "both_endpoints":
                    self.assertIsNone(first[1][0][0])
                    self.assertIsNone(first[1][0][1])
                elif name == "left_endpoint":
                    self.assertIsNone(first[1][0][0])
                    self.assertIsNotNone(first[1][0][1])
                elif name == "right_endpoint":
                    self.assertIsNotNone(first[1][0][0])
                    self.assertIsNone(first[1][0][1])
                elif name == "isolated":
                    self.assertEqual(first[1], ())
                elif name == "multiple":
                    self.assertEqual(len(first[1]), 2)

    def test_multiway_plateau_all_permutations_map_identically(self):
        function = production.engineering_functions()["multiway_plateau"]
        identity = tuple(range(4))
        baseline = find_verified_envelope(function)
        expected = mapped_signature(baseline, identity)
        checked = 0
        for permutation in itertools.permutations(identity):
            observed = baseline if permutation == identity else find_verified_envelope(
                lambda t, order=permutation: function(t)[:, order]
            )
            self.assertEqual(expected, mapped_signature(observed, permutation))
            checked += 1
        self.assertEqual(checked, 24)

    def test_signature_call_does_not_change_numerical_envelope(self):
        function = production.engineering_functions()["multiway_plateau"]
        before = find_verified_envelope(function)
        samples_before = function(np.linspace(0., 1., 257, dtype=np.float64)).copy()
        mapped_signature(before, tuple(range(4)))
        after = find_verified_envelope(function)
        samples_after = function(np.linspace(0., 1., 257, dtype=np.float64))
        self.assertEqual(before, after)
        self.assertTrue(np.array_equal(samples_before, samples_after))


if __name__ == "__main__":
    unittest.main()
