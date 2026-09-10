import math
import unittest

from defensive_network_disruption.geometry.segment import (
    IMPLEMENTATION_TOLERANCE_METRES,
    minimum_defender_segment_distance,
    point_to_segment_distance,
)


class SegmentDistanceTests(unittest.TestCase):
    def test_projection_regions_and_on_segment(self):
        self.assertEqual(point_to_segment_distance((-2, 0), (0, 0), (10, 0)), (2.0, 0.0))
        self.assertEqual(point_to_segment_distance((12, 0), (0, 0), (10, 0)), (2.0, 1.0))
        self.assertEqual(point_to_segment_distance((4, 3), (0, 0), (10, 0)), (3.0, 0.4))
        self.assertEqual(point_to_segment_distance((4, 0), (0, 0), (10, 0)), (0.0, 0.4))

    def test_endpoints_degenerate_and_ties(self):
        self.assertEqual(point_to_segment_distance((0, 0), (0, 0), (10, 0))[0], 0.0)
        self.assertEqual(point_to_segment_distance((3, 4), (0, 0), (0, 0)), (5.0, 0.0))
        near = IMPLEMENTATION_TOLERANCE_METRES / 2
        self.assertEqual(point_to_segment_distance((3, 4), (0, 0), (near, 0)), (5.0, 0.0))
        self.assertEqual(minimum_defender_segment_distance([], (0, 0), (1, 0)), None)
        self.assertEqual(minimum_defender_segment_distance([(0, 1), (1, 1)], (0, 0), (1, 0))[1], (0, 1))

    def test_rejects_nonfinite(self):
        with self.assertRaises(ValueError):
            point_to_segment_distance((math.nan, 0), (0, 0), (1, 0))
