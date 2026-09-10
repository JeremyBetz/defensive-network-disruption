import json
import tempfile
import unittest
from pathlib import Path

from defensive_network_disruption.data.identity_compatibility import (
    CompatibilityBlocked, ProjectedMatch, canonical_lines, id_form, project_event, project_metadata,
    project_tracking, restricted_prepare_match, safe_product, select_carrier,
)


def interval(team):
    return {"id": team, "team_id": team, "playing_time": {"by_period": [
        {"name": "period_1", "start_frame": 1, "end_frame": 99},
        {"name": "period_2", "start_frame": 100, "end_frame": 199},
    ]}}


class IdentityUnitTests(unittest.TestCase):
    def test_identity_forms_do_not_normalize(self):
        self.assertEqual(id_form(None), "null")
        self.assertEqual(id_form(""), "empty")
        self.assertEqual(id_form(" \t"), "whitespace_only")
        self.assertEqual(id_form(" 7"), "padded")
        self.assertEqual(id_form({"bad": 1}), "malformed")
        self.assertEqual(id_form(7), "ordinary")

    def test_carrier_precedence_and_conflict(self):
        self.assertEqual(select_carrier({"player_id": "p1", "player_in_possession_id": "p2"}), ("p1", False, True))
        self.assertEqual(select_carrier({"player_id": "", "player_in_possession_id": "p2"}), ("p2", True, False))
        self.assertEqual(select_carrier({"player_id": None, "player_in_possession_id": None}), ("", False, False))

    def test_projections_drop_extra_fields(self):
        metadata = project_metadata({
            "home_team": {"id": 1, "name": "drop"}, "away_team": {"id": 2},
            "players": [{"id": 3, "team_id": 1, "name": "drop", "playing_time": {"by_period": []}}],
            "home_team_side": ["left_to_right", "right_to_left"], "score": "drop",
        })
        self.assertNotIn("score", metadata)
        self.assertEqual(set(metadata["players"][0]), {"id", "team_id", "playing_time"})
        header = tuple(["event_id", "event_type", "pass_outcome", "period", "time_end", "player_id", "player_in_possession_id", "player_targeted_id", "vendor_score"])
        event = project_event(header, tuple(["e", "x", "ok", "1", "0:01", "p", "p", "t", "drop"]))
        self.assertNotIn("vendor_score", event)
        tracking = project_tracking({"frame": 1, "period": 1, "timestamp": "0:00.1", "player_data": [{"player_id": "p", "x": 0, "y": 1, "is_detected": True}], "possession": {}})
        self.assertNotIn("possession", tracking)
        self.assertNotIn("is_detected", tracking["player_data"][0])

    def test_firewall_rejects_reserved_withheld_traversal_and_symlink(self):
        for denied in ("1874553", "1953632", "../../1886347"):
            with self.assertRaises(PermissionError):
                safe_product(Path("/never-open"), denied, "events")
        with self.assertRaises(PermissionError):
            safe_product(Path("/never-open"), "1886347", "pose")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "elsewhere"
            target.mkdir()
            (root / "data").symlink_to(target)
            with self.assertRaises(PermissionError):
                safe_product(root, "1886347", "events")

    def test_deterministic_serialization(self):
        from defensive_network_disruption.data.receiver_choices import ChoiceSet
        choice = ChoiceSet("1886347", "e", ("b",), ((1.0, 2.0),), ((3.0, 4.0),), (0.0, 0.0), 0, False)
        self.assertEqual(canonical_lines([choice]), canonical_lines([choice]))


class RestrictedReaderSyntheticTests(unittest.TestCase):
    def make_projected(self, target="mate", carrier="carrier", fallback="carrier", target_tracked=True, target_team="home", target_active=True):
        players = [
            interval("home") | {"id": "carrier"},
            interval("home") | {"id": "mate", "team_id": target_team},
            interval("home") | {"id": "spare"},
            interval("away") | {"id": "def"},
        ]
        if not target_active:
            players[1]["playing_time"] = {"by_period": [{"name": "period_1", "start_frame": 20, "end_frame": 30}]}
        event = {"event_id": "e1", "event_type": "player_possession", "pass_outcome": "successful", "period": "1", "time_end": "00:00.200", "player_id": carrier, "player_in_possession_id": fallback, "player_targeted_id": target}
        pdata = [
            {"player_id": "carrier", "x": 0.0, "y": 0.0},
            {"player_id": "spare", "x": -3.0, "y": 1.0},
            {"player_id": "def", "x": 2.0, "y": 1.0},
        ]
        if target_tracked:
            pdata.append({"player_id": "mate", "x": 5.0, "y": 0.0})
        return ProjectedMatch(
            {"home_team": {"id": "home"}, "away_team": {"id": "away"}, "players": players, "home_team_side": ["left_to_right", "right_to_left"]},
            (event,), ({"frame": 10, "period": 1, "timestamp": "00:00.100", "player_data": pdata},),
        )

    def test_valid_and_separate_fit_evaluation(self):
        choices, qc, _ = restricted_prepare_match("1886347", self.make_projected())
        self.assertEqual((qc["evaluation_eligible"], qc["fit_eligible"]), (1, 1))
        self.assertEqual(choices[0].target_index, 0)

    def test_target_outside_is_evaluation_only(self):
        choices, qc, audit = restricted_prepare_match("1886347", self.make_projected(target_tracked=False))
        self.assertEqual((qc["evaluation_eligible"], qc["fit_eligible"]), (1, 0))
        self.assertTrue(choices[0].target_outside)
        self.assertEqual(audit["target"]["untracked"], 1)

    def test_target_exclusion_states(self):
        cases = [
            ("", "carrier", True, "home", True),
            ("carrier", "carrier", True, "home", True),
            ("unknown", "carrier", True, "home", True),
        ]
        for target, carrier, tracked, team, active in cases:
            with self.subTest(target=target):
                choices, qc, _ = restricted_prepare_match("1886347", self.make_projected(target, carrier, carrier, tracked, team, active))
                self.assertEqual(choices, [])
                self.assertEqual(qc["exclusions"]["missing_or_unusable_target"], 1)

    def test_other_team_and_inactive_targets_remain_independent(self):
        choices, qc, audit = restricted_prepare_match("1886347", self.make_projected(target_team="away"))
        self.assertEqual((qc["evaluation_eligible"], qc["fit_eligible"]), (1, 0))
        self.assertEqual(audit["target"]["other_team"], 1)
        choices, qc, audit = restricted_prepare_match("1886347", self.make_projected(target_active=False))
        self.assertEqual((qc["evaluation_eligible"], qc["fit_eligible"]), (1, 0))
        self.assertEqual(audit["target"]["inactive"], 1)

    def test_conflicting_carriers_use_primary(self):
        projected = self.make_projected(fallback="mate")
        choices, qc, audit = restricted_prepare_match("1886347", projected)
        self.assertEqual(qc["evaluation_eligible"], 1)
        self.assertEqual(audit["carrier"]["conflict"], 1)
        self.assertEqual(choices[0].carrier_xy, (0.0, 0.0))

    def test_missing_and_fallback_carriers(self):
        projected = self.make_projected(carrier="", fallback="carrier")
        choices, qc, audit = restricted_prepare_match("1886347", projected)
        self.assertEqual(qc["evaluation_eligible"], 1)
        self.assertEqual(audit["carrier"]["fallback_used"], 1)
        projected = self.make_projected(carrier="", fallback="")
        choices, qc, audit = restricted_prepare_match("1886347", projected)
        self.assertEqual(qc["exclusions"]["invalid_carrier"], 1)
        self.assertEqual(audit["carrier"]["both_missing"], 1)

    def test_unknown_roster_team_is_audited_without_repair(self):
        projected = self.make_projected()
        metadata = dict(projected.metadata)
        metadata["players"] = list(projected.metadata["players"]) + [interval("unknown") | {"id": "extra"}]
        _, _, audit = restricted_prepare_match("1886347", ProjectedMatch(metadata, projected.events, projected.frames))
        self.assertEqual(audit["membership"]["roster_unknown_team"], 1)

    def test_unknown_tracking_identity_is_audited_without_mapping(self):
        projected = self.make_projected()
        frame = dict(projected.frames[0])
        frame["player_data"] = list(frame["player_data"]) + [{"player_id": "unknown", "x": 1.0, "y": 1.0}]
        _, _, audit = restricted_prepare_match("1886347", ProjectedMatch(projected.metadata, projected.events, (frame,)))
        self.assertEqual(audit["membership"]["tracking_player_absent_roster"], 1)

    def test_duplicate_declared_team_is_blocked(self):
        projected = self.make_projected()
        metadata = dict(projected.metadata, away_team={"id": "home"})
        with self.assertRaises(CompatibilityBlocked):
            restricted_prepare_match("1886347", ProjectedMatch(metadata, projected.events, projected.frames))

    def test_duplicate_roster_and_tracking_are_hard_failures(self):
        projected = self.make_projected()
        metadata = dict(projected.metadata)
        metadata["players"] = list(projected.metadata["players"]) + [projected.metadata["players"][0]]
        with self.assertRaises(ValueError):
            restricted_prepare_match("1886347", ProjectedMatch(metadata, projected.events, projected.frames))
        frame = dict(projected.frames[0])
        frame["player_data"] = list(frame["player_data"]) + [frame["player_data"][0]]
        with self.assertRaises(ValueError):
            restricted_prepare_match("1886347", ProjectedMatch(projected.metadata, projected.events, (frame,)))

    def test_unknown_direction_and_malformed_interval_fail_closed(self):
        projected = self.make_projected()
        metadata = dict(projected.metadata, home_team_side=["unknown", "right_to_left"])
        choices, qc, audit = restricted_prepare_match("1886347", ProjectedMatch(metadata, projected.events, projected.frames))
        self.assertEqual(choices, [])
        self.assertEqual(qc["exclusions"]["invalid_carrier"], 1)
        self.assertEqual(audit["period_contract"]["unknown_direction"], 1)
        metadata = dict(projected.metadata)
        players = [dict(item) for item in projected.metadata["players"]]
        players[0]["playing_time"] = {"by_period": [{"name": "period_1", "start_frame": 20, "end_frame": 10}]}
        metadata["players"] = players
        _, _, audit = restricted_prepare_match("1886347", ProjectedMatch(metadata, projected.events, projected.frames))
        self.assertEqual(audit["period_contract"]["malformed_intervals"], 1)

    def test_strict_prior_timing_excludes_equal_or_stale_frames(self):
        projected = self.make_projected()
        equal = dict(projected.frames[0], timestamp="00:00.200")
        choices, qc, _ = restricted_prepare_match("1886347", ProjectedMatch(projected.metadata, projected.events, (equal,)))
        self.assertEqual(choices, [])
        self.assertEqual(qc["exclusions"]["invalid_decision_frame"], 1)
        stale = dict(projected.frames[0], timestamp="00:00.099")
        choices, qc, _ = restricted_prepare_match("1886347", ProjectedMatch(projected.metadata, projected.events, (stale,)))
        self.assertEqual(choices, [])
        self.assertEqual(qc["exclusions"]["invalid_decision_frame"], 1)

    def test_duplicate_event_ids_invalidate_match(self):
        projected = self.make_projected()
        projected = ProjectedMatch(projected.metadata, projected.events + projected.events, projected.frames)
        choices, qc, _ = restricted_prepare_match("1886347", projected)
        self.assertEqual(choices, [])
        self.assertEqual(qc["exclusions"]["invalid_event_or_transition"], 2)

    def test_candidate_independence_from_target_and_outcome(self):
        first, _, _ = restricted_prepare_match("1886347", self.make_projected())
        projected = self.make_projected()
        changed = dict(projected.events[0], pass_outcome="unsuccessful", player_targeted_id="mate")
        second, _, _ = restricted_prepare_match("1886347", ProjectedMatch(projected.metadata, (changed,), projected.frames))
        self.assertEqual(first[0].candidate_ids, second[0].candidate_ids)


if __name__ == "__main__":
    unittest.main()
