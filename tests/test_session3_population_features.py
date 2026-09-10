import unittest
from types import SimpleNamespace

import numpy as np

from defensive_network_disruption.data.receiver_choices import (
    active_in_period, attack_sign, attacking_xy, clock_microseconds,
    eligible_candidates, prepare_match, select_decision_frame,
)
from defensive_network_disruption.validation.ranking_features import choice_features


class PopulationFeatureTests(unittest.TestCase):
    def test_clock_direction_and_active_interval(self):
        self.assertEqual(clock_microseconds("01:02:03.40"), 3_723_400_000)
        self.assertEqual(clock_microseconds("62:03.4"), 3_723_400_000)
        self.assertEqual(attack_sign("home", "home", "left_to_right"), 1)
        self.assertEqual(attack_sign("home", "away", "left_to_right"), -1)
        self.assertEqual(attacking_xy(3, -2, -1), (-3.0, -2.0))
        player = {"playing_time": {"by_period": [{"name": "period_1", "start_frame": 10, "end_frame": 20}]}}
        self.assertTrue(active_in_period(player, 1, 10))
        self.assertFalse(active_in_period(player, 2, 10))

    def test_m0_oracle_and_strict_m1_nesting(self):
        choice = SimpleNamespace(
            carrier_xy=(0.0, 0.0), candidate_xy=((3.0, 4.0), (-2.0, 0.0)),
            defender_xy=((3.0, 4.0), (1.0, 0.0)),
        )
        m0, _ = choice_features(choice, "m0")
        m1, _ = choice_features(choice, "m1")
        np.testing.assert_array_equal(m0, m1[:, :3])
        np.testing.assert_allclose(m0, [[5, 3, 4], [2, -2, 0]])
        self.assertEqual(m1[0, 3], 0.0)
        self.assertEqual(m1[0, 4], 0.0)

    def test_missing_defenders_rejected_by_m1_only(self):
        choice = SimpleNamespace(carrier_xy=(0.0, 0.0), candidate_xy=((1.0, 0.0),), defender_xy=())
        self.assertEqual(choice_features(choice, "m0")[0].shape, (1, 3))
        with self.assertRaises(ValueError):
            choice_features(choice, "m1")

    def test_candidate_construction_has_no_target_input(self):
        interval = {"playing_time": {"by_period": [{"name": "period_1", "start_frame": 1, "end_frame": 9}]}}
        roster = {
            "carrier": {"team_id": "home", **interval},
            "keeper": {"team_id": "home", **interval},
            "backward": {"team_id": "home", **interval},
            "opponent": {"team_id": "away", **interval},
        }
        positions = {name: (float(index), 0.0) for index, name in enumerate(roster)}
        self.assertEqual(
            eligible_candidates(roster, positions, "carrier", "home", 1, 5),
            ("backward", "keeper"),
        )

    def test_strict_same_period_frame_selection(self):
        frames = [(900_000, 9, {}), (1_000_000, 10, {}), (1_100_000, 11, {})]
        self.assertEqual(select_decision_frame(frames, 1_000_000)[1], 9)
        self.assertEqual(select_decision_frame(frames, 1_000_001)[1], 10)
        self.assertIsNone(select_decision_frame(frames, 1_200_001))

    def test_prepare_rejects_nondevelopment_before_access(self):
        with self.assertRaises(PermissionError):
            prepare_match("1953632", object())
