import math
import time
import unittest

import numpy as np

from defensive_network_disruption.geometry.comparator_diagnosis import (
    DiagnosticTimeout, audit_partitions, maximum_simpson, sanitize_curve,
    split_simpson_curve, timed, uniform_simpson_curve,
)


class Session14akDiagnosisTests(unittest.TestCase):
    def test_partition_coverage_and_onsets(self):
        result = audit_partitions((0.0, 0.25, 0.75, 1.0), (0.25, 0.75))
        self.assertTrue(all(result[key] for key in
                            ("covers_domain", "strictly_ordered", "width_sum_exact", "onsets_once")))
        self.assertEqual(result["piece_count"], 3)

    def test_partition_defects_are_reported(self):
        result = audit_partitions((0.0, 0.5, 0.5, 1.0), (0.25,))
        self.assertFalse(result["strictly_ordered"])
        self.assertFalse(result["onsets_once"])

    def test_simpson_oracle(self):
        function = lambda t: np.column_stack((t * t, np.zeros_like(t)))
        self.assertAlmostEqual(maximum_simpson(function, 32), 1.0 / 3.0, places=15)

    def test_curves_are_deterministic_and_sanitized(self):
        function = lambda t: np.column_stack((t * t, 0.5 * t))
        a = uniform_simpson_curve(function, (16, 32, 64))
        b = split_simpson_curve(function, (0.0, 0.4, 1.0), (16, 32, 64))
        self.assertEqual([row["estimate"] for row in a], [row["estimate"] for row in uniform_simpson_curve(function, (16, 32, 64))])
        self.assertNotIn("estimate", sanitize_curve(a)[0])
        self.assertEqual(len(b), 3)

    def test_timeout(self):
        with self.assertRaises(DiagnosticTimeout):
            timed(lambda: time.sleep(0.05), limit_seconds=0.01)

    def test_nonfinite_and_parity_fail_closed(self):
        with self.assertRaises(ValueError):
            maximum_simpson(lambda t: np.ones((len(t), 1)), 3)
        with self.assertRaises(ValueError):
            maximum_simpson(lambda t: np.full((len(t), 1), math.nan), 4)


if __name__ == "__main__":
    unittest.main()
