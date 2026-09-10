import unittest

from defensive_network_disruption.validation.benchmark_structure import (
    independent_candidate_ids,
    resolve_unique_target_link,
)


class BenchmarkStructureTests(unittest.TestCase):
    def test_target_join_missing_unique_and_duplicate(self):
        rows = [{"event_id": "a"}, {"event_id": "b"}]
        self.assertEqual(resolve_unique_target_link(rows, "a"), rows[0])
        self.assertIsNone(resolve_unique_target_link(rows, "missing"))
        with self.assertRaises(ValueError):
            resolve_unique_target_link(rows + [{"event_id": "a"}], "a")

    def test_candidates_are_target_and_vendor_independent(self):
        roster = {
            "carrier": {"team_id": "home"},
            "keeper": {"team_id": "home", "vendor_score": 0},
            "backward": {"team_id": "home", "eventual_target": True},
            "opponent": {"team_id": "away"},
            "off_pitch": {"team_id": "home"},
        }
        tracked = {
            "carrier": {"x": 0, "y": 0}, "keeper": {"x": -40, "y": 0},
            "backward": {"x": -5, "y": 3}, "opponent": {"x": 2, "y": 1},
            "off_pitch": {"x": 1, "y": 1},
        }
        result = independent_candidate_ids(
            roster, tracked, carrier_id="carrier", carrier_team_id="home",
            active_ids={"carrier", "keeper", "backward", "opponent"},
        )
        self.assertEqual(result, ("backward", "keeper"))
