"""Deferred until edge semantics and graph construction are defined."""

import unittest


class GraphContractTests(unittest.TestCase):
    @unittest.skip("No validated edge definition, node eligibility, or ordering contract")
    def test_deterministic_graph_construction(self):
        """Later check repeatability and specified handling of reordered inputs."""
