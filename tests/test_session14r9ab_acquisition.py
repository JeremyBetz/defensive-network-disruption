import copy
import json
import tempfile
import unittest
from pathlib import Path

from defensive_network_disruption.geometry import r9ab_acquisition as a
from defensive_network_disruption.geometry.r9aa_terminal_authority import load_authority
from defensive_network_disruption.geometry.r9x_terminal_authority import canonical, digest
from defensive_network_disruption.validation import r9ab_evidence as evidence
from defensive_network_disruption.validation import r9ab_linear as linear
from defensive_network_disruption.validation.r9v_publication_ownership import persist_authority

ROOT = Path(__file__).resolve().parents[1]


class R9ABTests(unittest.TestCase):
    def lineage(self):
        depths = list(range(1, 80)) + [80, 80]
        depths.insert(36, depths.pop())
        cells = [{"ordinal": i, "depth": depth, "pair_status": "separate",
                  "maximum_status": "maximum"} for i, depth in enumerate(depths)]
        cells[36] = {"ordinal": 36, "depth": 80, "pair_status": "equal",
                     "maximum_status": "unresolved"}
        return {"cells": cells, "ordered_partition_sha256": "1" * 64,
                "boundary_capture_sha256": "2" * 64,
                "selected_edge_sha256": "3" * 64}

    def selected(self):
        return {"alias": "synthetic", "carrier": [0.0, 0.0], "receiver": [0.25, 0.0],
                "defenders": [[2.0, 1.0], [3.0, 1.5], [1.0, -1.0], [1.0, -1.0]]}

    def construct(self):
        return a.construct(
            lineage=self.lineage(),
            boundary={"plateau": {"pair": [0, 1], "index": 0, "end": 1,
                                   "grid": [0.0, 1.0]}},
            selected=self.selected(), private_index_sha256="4" * 64,
            reference_implementation_sha256="5" * 64,
            verifier_sha256="6" * 64, onset_owner_sha256="7" * 64)

    def test_constructs_v2_with_distinct_pair_and_complete_competitors(self):
        value, receipt = self.construct(); loaded = load_authority(copy.deepcopy(value))
        self.assertEqual(loaded.source_version, 2)
        self.assertEqual(loaded.relation_type, "common_inactive_branch")
        self.assertNotEqual(value["pair_left_ref"], value["pair_right_ref"])
        self.assertEqual(receipt["competitor_position_count"], 2)
        self.assertEqual(receipt["unique_competitor_count"], 1)
        self.assertEqual(canonical(value), canonical(loaded.record))

    def test_lineage_relation_and_hash_mutations_block(self):
        for change in ("pair", "status", "depth", "bounds"):
            lineage = self.lineage()
            boundary = {"plateau": {"pair": [0, 1], "index": 0, "end": 1,
                                     "grid": [0.0, 1.0]}}
            selected = self.selected()
            if change == "pair": boundary["plateau"]["pair"] = [0, 0]
            elif change == "status": lineage["cells"][36]["pair_status"] = "separate"
            elif change == "depth": lineage["cells"][36]["depth"] = 79
            else: boundary["plateau"]["end"] = 3
            with self.assertRaises((ValueError, IndexError)):
                a.construct(lineage=lineage, boundary=boundary, selected=selected,
                    private_index_sha256="4"*64, reference_implementation_sha256="5"*64,
                    verifier_sha256="6"*64, onset_owner_sha256="7"*64)

    def test_linear_success_and_tamper(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "outputs") as tmp:
            path = Path(tmp) / "journal.jsonl"; journal = linear.Journal(path)
            journal.append("lineage_review", valid=True)
            journal.append("access_attempt", previously_exposed=True)
            journal.append("materialization", previously_exposed_states=1,
                           previously_exposed_edges=1, new_population_states=0,
                           new_population_edges=0)
            journal.append("authority_persistence", valid=True, authority_sha256="1"*64)
            journal.append("structural_validation", valid=True,
                           pair_refs_distinct=True, competitors_complete=True)
            journal.append("terminal_success"); journal.close()
            authority = linear.review(path, expected_head=journal.previous)
            self.assertEqual(authority.record()["status"], "success")
            raw = path.read_bytes(); path.write_bytes(raw.replace(b'"valid":true', b'"valid":false', 1))
            with self.assertRaises(Exception): linear.review(path)

    def test_linear_failure_requires_traceback(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "outputs") as tmp:
            journal = linear.Journal(Path(tmp) / "journal.jsonl")
            journal.append("terminal_failure", stage="lineage", exception="ValueError",
                           traceback_sha256="1" * 64); journal.close()
            self.assertEqual(linear.review(journal.path).record()["status"], "failure")

    def test_evidence_closure_and_false_acceptance(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "outputs") as tmp:
            folder = Path(tmp); local = folder / "local"; local.mkdir()
            journal = linear.Journal(local / "journal.jsonl")
            for action, payload in (
                ("lineage_review", {"valid": True}),
                ("access_attempt", {"previously_exposed": True}),
                ("materialization", {"previously_exposed_states": 1, "previously_exposed_edges": 1,
                                     "new_population_states": 0, "new_population_edges": 0}),
                ("authority_persistence", {"valid": True}),
                ("structural_validation", {"valid": True}),
                ("terminal_success", {})):
                journal.append(action, **payload)
            journal.close(); authority = linear.review(journal.path)
            descriptor = persist_authority(local, authority)
            records = {name: {"schema_version": 1, "status": "complete",
                               "flags": {"valid": True}, "counts": {"count": 1}}
                       for name in evidence.NAMES[:-2]}
            qc = {"status": "complete", "execution_valid": True, "classification": "A",
                  "readiness": 1, "authority_schema_version": 2,
                  "ordered_pair_refs_distinct": True, "competitors_complete": True,
                  "interval_relation_lineage_valid": True, "canonical_round_trip": True,
                  "states_reopened": 1, "edges_reopened": 1,
                  "new_population_states": 0, "new_population_edges": 0,
                  "candidate_evaluations": 0, "field_evaluations": 0,
                  "refinements": 0, "maximality_classifications": 0,
                  "exposure_uncertain": False}
            self.assertTrue(evidence.close(folder, records, qc, authority, descriptor)["valid"])
            changed = json.loads((folder / "qc.json").read_text()); changed["field_evaluations"] = 1
            (folder / "qc.json").write_text(json.dumps(changed) + "\n")
            with self.assertRaises(ValueError): evidence.publication_check(folder)

    def test_runner_has_no_prohibited_routes(self):
        source = (ROOT / "scripts/session_14r9ab_terminal_cell_authority_v2_acquisition.py").read_text()
        for token in ("bound_terminal(", "classify_terminal(", "evaluate_edge(",
                      "prepared.jsonl", "provider", "owner_certification", "localization"):
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
