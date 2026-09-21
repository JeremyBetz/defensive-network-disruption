import math
import tempfile
import time
import unittest
from pathlib import Path

import numpy as np

from defensive_network_disruption.geometry import r9v_tie_diagnosis as d
from defensive_network_disruption.geometry import verification_repair as repair


class TieDiagnosisTests(unittest.TestCase):
    def test_observer_preserves_exact_failure(self):
        inside = 0.5
        outside = float(np.nextafter(inside, -math.inf))
        def function(points):
            points = np.asarray(points)
            return np.column_stack((points,
                                    np.full(len(points), 0.5),
                                    np.full(len(points), 0.9)))
        observer = d.BoundaryObserver()
        with self.assertRaisesRegex(repair.VerificationError, "tie_boundary_not_maximal"):
            with observer.enabled():
                repair._certify_boundary(function, (0, 1), outside, inside, "entry")
        record = observer.result()
        self.assertEqual(record["pair"], (0, 1))
        self.assertEqual(record["pair_inside_difference"], 0.0)
        self.assertNotEqual(record["pair_outside_difference"], 0.0)
        self.assertFalse(set(record["pair"]).issubset(record["owners"]))

    def test_reference_establishes_third_defender_dominance(self):
        result = d.reference((0., 0.), (10., 0.),
            ((5., 2.), (5., 2.), (5., 0.1)), (0, 1), .7, .8,
            deadline=time.monotonic() + 10)
        self.assertTrue(result["complete"])
        self.assertEqual(result["classification"], "F")
        self.assertGreater(result["maximum_counts"]["dominated"], 0)

    def test_reference_limits_and_nonfinite_observation(self):
        with self.assertRaises(repair.VerificationError):
            d.reference((0., 0.), (10., 0.), ((5., 2.), (5., 2.)),
                        (0, 1), .8, .7, deadline=time.monotonic() + 1)
        with self.assertRaises(ValueError):
            d._finite_float(float("nan"))

    def test_twelve_frozen_controls(self):
        rows = d.synthetic_controls()
        self.assertEqual(len(rows), 12)
        self.assertTrue(all(row["passed"] for row in rows))
        self.assertEqual(len({row["fixture"] for row in rows}), 12)

    def test_classification_requires_named_mechanism(self):
        capture = {"pair": (0, 1), "owners": (2,),
                   "pair_inside_difference": 0.0}
        classification, specification = d.classify_observation(
            capture, {"classification": "F", "complete": True})
        self.assertEqual(classification, "NA")
        self.assertIn("non-maximal", specification)
        capture["pair_inside_difference"] = 1e-16
        self.assertEqual(d.classify_observation(
            capture, {"classification": "F", "complete": True})[0], "NB")
