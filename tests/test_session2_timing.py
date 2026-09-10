import unittest

from defensive_network_disruption.validation.timing import nearest_strictly_before


class TimingTests(unittest.TestCase):
    def test_strictly_before_and_tolerance(self):
        frames = [1.0, 1.1, 1.2]
        self.assertEqual(nearest_strictly_before(frames, 1.2), 1)
        self.assertEqual(nearest_strictly_before(frames, 1.2001), 2)
        self.assertIsNone(nearest_strictly_before(frames, 1.31))
        self.assertIsNone(nearest_strictly_before(frames, 1.0))
