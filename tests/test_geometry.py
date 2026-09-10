"""Deferred until a pure geometry API and degeneracy contract are specified."""

import unittest


class SegmentContractTests(unittest.TestCase):
    @unittest.skip("No line/segment API, endpoint rules, or numerical tolerance defined")
    def test_line_and_segment_contract(self):
        """Later use synthetic on/off-segment, endpoint, and zero-length cases."""
