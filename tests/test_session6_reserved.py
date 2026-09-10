import ast
import inspect
import tempfile
import unittest
from pathlib import Path

import numpy as np

from defensive_network_disruption.data.identity_compatibility import ProjectedMatch
from defensive_network_disruption.data.identity_compatibility import (
    project_event,
    project_metadata,
    project_tracking,
)
from defensive_network_disruption.data.session6_population import (
    Session6ContractError,
    prepare_match_session6,
    validate_input_contract,
)
from defensive_network_disruption.data.session6_source import (
    parse_lfs_pointer,
    safe_destination,
    source_path,
)
from defensive_network_disruption.validation.ranking_features import choice_features
from defensive_network_disruption.validation.session5 import choice_features_m1_m2

RESERVED = frozenset({"1874553"})


def player(player_id, team="home", periods=None):
    if periods is None:
        periods = [
            {"name": "period_1", "start_frame": 1, "end_frame": 99},
            {"name": "period_2", "start_frame": 100, "end_frame": 199},
        ]
    return {"id": player_id, "team_id": team, "playing_time": {"by_period": periods}}


def fixture(**event_changes):
    event = {
        "event_id": "event-one", "event_type": "player_possession",
        "pass_outcome": "successful", "period": "1", "time_end": "00:00.200",
        "player_id": "carrier", "player_in_possession_id": "carrier",
        "player_targeted_id": "target",
    }
    event.update(event_changes)
    metadata = {
        "home_team": {"id": "home"}, "away_team": {"id": "away"},
        "home_team_side": ["left_to_right", "right_to_left"],
        "players": [player("carrier"), player("target"), player("spare"), player("defender", "away")],
    }
    frame = {
        "frame": 10, "period": 1, "timestamp": "00:00.100",
        "player_data": [
            {"player_id": "carrier", "x": 0.0, "y": 0.0},
            {"player_id": "target", "x": 10.0, "y": 1.0},
            {"player_id": "spare", "x": -4.0, "y": 3.0},
            {"player_id": "defender", "x": 5.0, "y": 2.0},
        ],
    }
    return ProjectedMatch(metadata, (event,), (frame,))


class Session6ContractTests(unittest.TestCase):
    def test_valid_contract_and_fallback(self):
        projected = fixture(player_id="", player_in_possession_id="carrier")
        choices, qc, contract = prepare_match_session6("1874553", projected, allowlist=RESERVED)
        self.assertEqual((qc["evaluation_eligible"], qc["fit_eligible"]), (1, 1))
        self.assertEqual(contract["carrier_fallback_count"], 1)
        self.assertEqual(choices[0].candidate_ids, ("spare", "target"))

    def test_conflicting_carriers_stop(self):
        with self.assertRaisesRegex(Session6ContractError, "conflicting"):
            validate_input_contract(fixture(player_in_possession_id="target"))

    def test_blank_or_padded_required_identity_stops(self):
        for value in ("", "   ", " event-one"):
            with self.subTest(value=value), self.assertRaises(Session6ContractError):
                validate_input_contract(fixture(event_id=value))

    def test_optional_blank_is_allowed_but_padding_is_not(self):
        validate_input_contract(fixture(player_targeted_id=""))
        with self.assertRaises(Session6ContractError):
            validate_input_contract(fixture(player_targeted_id=" target"))

    def test_unknown_roster_or_tracking_identity_stops(self):
        projected = fixture()
        metadata = dict(projected.metadata)
        metadata["players"] = list(metadata["players"]) + [player("unknown-team-player", "unknown")]
        with self.assertRaises(Session6ContractError):
            validate_input_contract(ProjectedMatch(metadata, projected.events, projected.frames))
        frame = dict(projected.frames[0])
        frame["player_data"] = list(frame["player_data"]) + [{"player_id": "unknown", "x": 1, "y": 1}]
        with self.assertRaises(Session6ContractError):
            validate_input_contract(ProjectedMatch(projected.metadata, projected.events, (frame,)))

    def test_duplicates_direction_and_intervals_stop(self):
        projected = fixture()
        frame = dict(projected.frames[0])
        frame["player_data"] = list(frame["player_data"]) + [frame["player_data"][0]]
        with self.assertRaises(Session6ContractError):
            validate_input_contract(ProjectedMatch(projected.metadata, projected.events, (frame,)))
        metadata = dict(projected.metadata, home_team_side=["unknown", "right_to_left"])
        with self.assertRaises(Session6ContractError):
            validate_input_contract(ProjectedMatch(metadata, projected.events, projected.frames))
        metadata = dict(projected.metadata)
        metadata["players"] = list(metadata["players"]) + [player("malformed", periods=[{"name": "period_1", "start_frame": 9, "end_frame": 1}])]
        with self.assertRaises(Session6ContractError):
            validate_input_contract(ProjectedMatch(metadata, projected.events, projected.frames))

    def test_missing_period_is_inactive_without_inference(self):
        projected = fixture()
        metadata = dict(projected.metadata)
        roster = [dict(item) for item in metadata["players"]]
        roster[1] = player("target", periods=[])
        metadata["players"] = roster
        choices, qc, _ = prepare_match_session6("1874553", ProjectedMatch(metadata, projected.events, projected.frames), allowlist=RESERVED)
        self.assertEqual((qc["evaluation_eligible"], qc["fit_eligible"]), (1, 0))
        self.assertTrue(choices[0].target_outside)
        self.assertEqual(qc["target_outside_reasons"], {"target_outside_verified_active_interval": 1})

    def test_target_outside_remains_evaluation_only(self):
        projected = fixture()
        frame = dict(projected.frames[0])
        frame["player_data"] = [item for item in frame["player_data"] if item["player_id"] != "target"]
        choices, qc, _ = prepare_match_session6("1874553", ProjectedMatch(projected.metadata, projected.events, (frame,)), allowlist=RESERVED)
        self.assertEqual((qc["evaluation_eligible"], qc["fit_eligible"]), (1, 0))
        self.assertIsNone(choices[0].target_index)

    def test_candidate_membership_is_label_and_outcome_independent(self):
        first, _, _ = prepare_match_session6("1874553", fixture(), allowlist=RESERVED)
        second, _, _ = prepare_match_session6(
            "1874553", fixture(player_targeted_id="spare", pass_outcome="unsuccessful"), allowlist=RESERVED
        )
        self.assertEqual(first[0].candidate_ids, second[0].candidate_ids)

    def test_strict_timing(self):
        projected = fixture()
        equal = dict(projected.frames[0], timestamp="00:00.200")
        choices, qc, _ = prepare_match_session6("1874553", ProjectedMatch(projected.metadata, projected.events, (equal,)), allowlist=RESERVED)
        self.assertEqual(choices, [])
        self.assertEqual(qc["exclusions"]["invalid_decision_frame"], 1)

    def test_nonplaying_period_records_are_counted_and_ignored(self):
        projected = fixture()
        nonplaying = {"frame": 0, "period": None, "timestamp": None, "player_data": [{"player_id": "not-parsed", "x": None, "y": None}]}
        contract = validate_input_contract(ProjectedMatch(projected.metadata, projected.events, (nonplaying,) + projected.frames))
        self.assertEqual(contract["ignored_non_playing_period_records"], 1)

    def test_feature_nesting(self):
        choices, _, _ = prepare_match_session6("1874553", fixture(), allowlist=RESERVED)
        m0, _ = choice_features(choices[0], "m0")
        m1, m2, _ = choice_features_m1_m2(choices[0])
        np.testing.assert_array_equal(m0, m1[:, :3])
        np.testing.assert_array_equal(m1, m2[:, :5])

    def test_projection_discards_unapproved_sentinel_fields(self):
        projected_metadata = project_metadata({
            **fixture().metadata,
            "score": "SENTINEL",
            "players": [{**item, "name": "SENTINEL"} for item in fixture().metadata["players"]],
        })
        self.assertNotIn("score", projected_metadata)
        self.assertTrue(all("name" not in item for item in projected_metadata["players"]))
        header = (
            "event_id", "event_type", "pass_outcome", "period", "time_end",
            "player_id", "player_in_possession_id", "player_targeted_id", "vendor_score",
        )
        event = project_event(header, ("e", "player_possession", "ok", "1", "00:00.2", "p", "p", "t", "SENTINEL"))
        self.assertNotIn("vendor_score", event)
        tracking = project_tracking({**fixture().frames[0], "ball_data": "SENTINEL"})
        self.assertNotIn("ball_data", tracking)


class Session6SourceTests(unittest.TestCase):
    def test_partition_and_product_firewall(self):
        self.assertEqual(source_path("1874553", "events", RESERVED), "data/matches/1874553/1874553_dynamic_events.csv")
        for denied in ("1953632", "1886347", "../../1874553"):
            with self.assertRaises(PermissionError):
                source_path(denied, "events", RESERVED)
        with self.assertRaises(PermissionError):
            source_path("1874553", "pose", RESERVED)

    def test_symlink_destination_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").symlink_to(root / "outside")
            with self.assertRaises(PermissionError):
                safe_destination(root, "1874553", "events", RESERVED)

    def test_lfs_pointer_contract(self):
        digest = "a" * 64
        pointer = f"version https://git-lfs.github.com/spec/v1\noid sha256:{digest}\nsize 123\n".encode()
        self.assertEqual(parse_lfs_pointer(pointer), (digest, 123))
        with self.assertRaises(RuntimeError):
            parse_lfs_pointer(b"not-lfs\n")


class Session6CommandSeparationTests(unittest.TestCase):
    @staticmethod
    def called_names(function):
        tree = ast.parse(inspect.getsource(function))
        return {node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}

    def test_prepare_cannot_score_or_fit_and_score_cannot_acquire_or_fit(self):
        import scripts.session_06_reserved as runner
        prepare_calls = self.called_names(runner.prepare_reserved)
        score_calls = self.called_names(runner.score)
        self.assertTrue(prepare_calls.isdisjoint({"expected_credits", "fit_final_models", "fit_with_fail_closed_gate"}))
        self.assertTrue(score_calls.isdisjoint({"acquire_product", "fit_final_models", "fit_with_fail_closed_gate", "load_projected_match_session6"}))

    def test_execution_marker_is_exclusive_and_persistent(self):
        import scripts.session_06_reserved as runner
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "execution.json"
            runner.create_execution_marker(marker, "first\n")
            self.assertEqual(marker.read_text(), "first\n")
            with self.assertRaises(FileExistsError):
                runner.create_execution_marker(marker, "second\n")
            self.assertEqual(marker.read_text(), "first\n")


if __name__ == "__main__":
    unittest.main()
