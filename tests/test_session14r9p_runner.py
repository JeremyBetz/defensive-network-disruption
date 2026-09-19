"""Runner and publication tests for Session 14R9P."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location("session_14r9p", ROOT / "scripts/session_14r9p_retained_journal_authority_reconciliation.py")
runner = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(runner)


class R9PRunnerTests(unittest.TestCase):
    def test_negative_controls_all_block(self):
        rows = runner.negative_controls()
        self.assertEqual(len(rows), 9)
        self.assertTrue(all(row["blocked"] and row["status"] == "blocked" for row in rows))

    def test_count_provenance_is_specific(self):
        value = runner._provenance()
        old = value["count_30881"]
        self.assertEqual(old["origin"], "R9I_RETAINED_JOURNAL")
        self.assertTrue(old["r9i_report_asserted"] and old["r9j_protocol_bound"] and old["copied_to_r9o_protocol"])
        self.assertFalse(old["asserted_by_r9n_protocol"] or old["asserted_by_r9n_report"])
        self.assertTrue(value["count_31161"]["r9n_report_binds_raw_hash"])

    def test_publication_checker_accepts_closed_synthetic_package(self):
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name).resolve()
            local = folder / "local"; local.mkdir()
            runner.put(local / "marker", {"synthetic": True})
            private = {"marker": runner.sha(local / "marker")}
            delta = [
                {"action": "numerical_stage", "r9i_count": 0, "r9n_count": 226, "delta": 226, "explanation": "additional_completed_evaluation_work"},
                {"action": "field_started", "r9i_count": 0, "r9n_count": 21, "delta": 21, "explanation": "additional_candidate_work"},
                {"action": "field_completed", "r9i_count": 0, "r9n_count": 21, "delta": 21, "explanation": "additional_candidate_work"},
                {"action": "edge_completed", "r9i_count": 0, "r9n_count": 10, "delta": 10, "explanation": "additional_completed_work"},
                {"action": "state_completed", "r9i_count": 0, "r9n_count": 1, "delta": 1, "explanation": "additional_completed_work"},
                {"action": "state_evaluation_started", "r9i_count": 0, "r9n_count": 1, "delta": 1, "explanation": "additional_started_work"},
            ]
            controls = [{"fixture": "synthetic", "status": "blocked", "blocked": True, "reason": "ValueError"}]
            public = {
                "reconciliation_contract.json": {"schema_version": 1},
                "count_provenance.json": {"schema_version": 1},
                "r9n_validation.json": {"schema_version": 1},
                "r9i_regression.json": {"schema_version": 1},
                "qc.json": {"schema_version": 1, "status": "success", "execution_valid": True, "r9o_mismatch_classification": "A", "classification": "A", "readiness": 1, "states_opened": 0, "edges_opened": 0, "scientific_computation": False, "numerical_computation": False, "negative_controls_passed": 1, "record_delta": 280},
            }
            runner._close(folder, public, delta, controls, private, {"protocol_sha256": "0" * 64, "implementation": {}})
            self.assertTrue(runner.publication_check(folder)["valid"])

    def test_publication_checker_rejects_cross_file_change(self):
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name).resolve()
            (folder / "local").mkdir()
            for public in runner.NAMES:
                if public.endswith(".csv"):
                    (folder / public).write_text("fixture,status,blocked,reason\n")
                else:
                    (folder / public).write_text("{}\n")
            with self.assertRaises(ValueError):
                runner.publication_check(folder)

    def test_runner_has_no_empirical_or_numerical_route(self):
        text = (ROOT / "scripts/session_14r9p_retained_journal_authority_reconciliation.py").read_text().lower()
        for prohibited in ("project_prepared_edge", "evaluate_edge", "scipy", "numpy", "population.json", "prepared.jsonl"):
            self.assertNotIn(prohibited, text)


if __name__ == "__main__":
    unittest.main()
