"""Synthetic-only tests for the bounded Session 14ah tooling."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from defensive_network_disruption.validation.empirical_switch_diagnosis import (
    project_canonical_edge, project_prepared_edge, replay_journal_with_diagnostics,
    replay_with_diagnostics, selective_bytes,
)
from defensive_network_disruption.validation.r5_persistence import Journal, LifecycleError


def records(stage={"stage": "geometry"}, *, context=True):
    result = []
    def add(action, **payload):
        result.append({"schema_version": 1, "sequence": len(result), "previous": None,
                       "action": action, "payload": payload})
    add("initialized"); add("access_authorized"); add("state_discovered", state="s", edges=["e"])
    add("projection_attempt", attempt="a", state="s"); add("projection_materialized", attempt="a", edges=["e"])
    add("state_prepared", state="s"); add("state_evaluation_started", state="s")
    add("diagnostic_started", state="s", edge="e", candidate="constant_width")
    add("numerical_stage", state="s", edge="e" if context else "x", candidate="constant_width", detail=stage)
    add("failure", stage="canonical_switch_certification", exception="VerificationError",
        state="s", edge="e", candidate="constant_width")
    return result


class Session14ahDiagnosisTests(unittest.TestCase):
    def test_single_edge_projection_skips_other_receivers_and_targets(self):
        prepared = json.dumps({"alias": "development_01", "carrier": [0, 0],
            "receivers": [[{"forbidden": "other"}], [20, 1]], "defenders": [[5, 0]]})
        canonical = json.dumps({"match_id": "1886347", "event_id": "private",
            "carrier_xy": [0, 0], "candidate_ids": ["a", "b"],
            "candidate_xy": [[{"forbidden": "other"}], [20, 1]], "defender_xy": [[5, 0]],
            "target_index": {"forbidden": "target"}, "target_outside": ["forbidden"]})
        first = project_prepared_edge(prepared, 1); second = project_canonical_edge(canonical, 1)
        self.assertEqual(selective_bytes(first), selective_bytes(second))

    def test_wrong_ordinal_rejected(self):
        row = json.dumps({"alias": "development_01", "carrier": [0, 0],
                          "receivers": [[1, 1]], "defenders": [[5, 0]]})
        with self.assertRaisesRegex(ValueError, "receiver_ordinal"): project_prepared_edge(row, 2)

    def test_diagnostic_event_is_non_mutating(self):
        with_diag = replay_with_diagnostics(records())
        without = replay_with_diagnostics([item for item in records() if item["action"] != "numerical_stage"])
        self.assertEqual(with_diag["snapshot"], without["snapshot"])
        self.assertEqual(with_diag["diagnostic_count"], 1)

    def test_diagnostic_negative_controls(self):
        bad = ({}, {"stage": "unknown"}, {"stage": "routing", "pieces": "1"},
               {"stage": "routing", "pieces": 2, "bounded": 1, "quadrature": 2},
               {"stage": "geometry", "extra": 1})
        for detail in bad:
            with self.subTest(detail=detail), self.assertRaises(LifecycleError):
                replay_with_diagnostics(records(detail))
        with self.assertRaisesRegex(LifecycleError, "numerical_stage_context"):
            replay_with_diagnostics(records(context=False))

    def test_unknown_event_rejected(self):
        items = records(); items[8]["action"] = "surprise"
        with self.assertRaisesRegex(LifecycleError, "unknown_diagnostic_event"):
            replay_with_diagnostics(items)

    def test_journal_hash_and_failure_survive_diagnostics(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder).resolve() / "journal.jsonl"; journal = Journal(path)
            journal.append("initialized"); journal.append("access_authorized")
            journal.append("state_discovered", state="s", edges=["e"])
            journal.append("projection_attempt", attempt="a", state="s")
            journal.append("projection_materialized", attempt="a", edges=["e"])
            journal.append("state_prepared", state="s"); journal.append("state_evaluation_started", state="s")
            journal.append("diagnostic_started", state="s", edge="e", candidate="constant_width")
            journal.append("numerical_stage", state="s", edge="e", candidate="constant_width", detail={"stage": "geometry"})
            journal.append("failure", stage="test", exception="RuntimeError", state="s", edge="e", candidate="constant_width")
            head = journal.previous; journal.close()
            result = replay_journal_with_diagnostics(path, expected_head=head)
            self.assertEqual(result["snapshot"]["status"], "failure")
            self.assertEqual(result["diagnostic_count"], 1)

    def test_routing_schema(self):
        result = replay_with_diagnostics(records({"stage": "routing", "pieces": 3, "bounded": 1, "quadrature": 2}))
        self.assertEqual(result["diagnostic_stages"], ["routing"])

    def test_no_empirical_scientific_routes(self):
        import defensive_network_disruption.validation.empirical_switch_diagnosis as module
        for forbidden in ("load_model", "option_share", "target_index", "summarize_state", "acquire"):
            self.assertNotIn(forbidden, vars(module))


if __name__ == "__main__": unittest.main()
