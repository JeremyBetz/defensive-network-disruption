"""Deferred until the selected release's coordinate contract is verified."""

import unittest


class CoordinateContractTests(unittest.TestCase):
    @unittest.skip("P01 must specify units, axes, direction, dimensions, and tolerance")
    def test_coordinate_transform_contract(self):
        """Later check verified landmarks, inverse transforms, and period direction."""
