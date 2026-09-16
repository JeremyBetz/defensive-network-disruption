"""Synthetic tests for Session 14R9H authority-context diagnosis."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from defensive_network_disruption.validation import r9h_authority_context as authority


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "session14r9h_runner", ROOT / "scripts/session_14r9h_runner_authority_context.py")
RUNNER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(RUNNER)


class Session14R9HTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.flow = authority.observe_actual_join(ROOT)

    def test_actual_chain_completes_context(self):
        self.assertTrue(self.flow["actual_chain_observed"])
        self.assertEqual(self.flow["identifier_context_fields"], ["alias", "edge", "state"])
        self.assertEqual(self.flow["runtime_context_fields"],
                         ["alias", "defenders", "edge", "origin", "receiver", "state"])
        self.assertFalse(self.flow["actual_loss_observed"])

    def test_evaluator_and_authority_builder_geometry_are_identical(self):
        self.assertTrue(self.flow["origin_identical"])
        self.assertTrue(self.flow["receiver_identical"])
        self.assertTrue(self.flow["defenders_identical_and_ordered"])
        self.assertTrue(self.flow["field_values_identical"])
        self.assertTrue(self.flow["authority_builder_received_complete_context"])

    def test_synthetic_context_cannot_match_empirical_authority(self):
        self.assertEqual(self.flow["synthetic_empirical_match_result"],
                         "authority_mismatch:selected_geometry")

    def test_geometry_mutations_and_identifier_false_match_reject(self):
        rows = authority.mutation_oracles()
        self.assertEqual({row["oracle"] for row in rows}, {
            "origin_coordinate", "receiver_coordinate", "defender_coordinate",
            "defender_order", "identifier_only_false_match"})
        self.assertTrue(all(row["alias_state_edge_unchanged"] for row in rows))
        self.assertTrue(all(row["fingerprint_changed"] for row in rows))
        self.assertTrue(all(row["exact_match_rejected"] for row in rows))

    def test_retained_certificate_orchestration(self):
        result = authority.retained_certificate_orchestration(ROOT)
        self.assertEqual(result["evidence_kind"],
                         "retained_observation_certificate_orchestration")
        self.assertTrue(result["warning_preserved"])
        self.assertTrue(result["exact_request_matched"])
        self.assertTrue(result["certificate_lookup_succeeded"])
        self.assertFalse(result["empirical_geometry_reconstructed"])

    def test_unmatched_warning_remains_blocking(self):
        result = authority.unmatched_warning_oracle(ROOT)
        self.assertTrue(result["warning_preserved"])
        self.assertTrue(result["blocking"])
        self.assertFalse(result["readiness"])
        self.assertFalse(result["fallback_certificate"])
        self.assertEqual(result["failure"], "authority_mismatch:interval_identity")

    def test_no_geometry_reopening_route(self):
        result = authority.no_reopening_guard(ROOT)
        self.assertTrue(result["passed"])
        self.assertFalse(result["provider_or_prepared_loader_present"])
        self.assertFalse(result["private_fallback_present"])

    def test_preflight_rejects_marker_collision(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as folder:
            relative = Path(folder).relative_to(ROOT)
            local = relative / "local"
            (ROOT / local).mkdir()
            (ROOT / local / "audit.marker").write_text("reserved\n")
            with patch.object(RUNNER, "OUT", relative), patch.object(RUNNER, "LOCAL", local):
                with self.assertRaisesRegex(FileExistsError, "audit_marker_exists"):
                    RUNNER.preflight()

    def test_runner_failure_preserves_exception_and_zero_access(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as folder:
            relative = Path(folder).relative_to(ROOT)
            local = relative / "local"
            with patch.object(RUNNER, "OUT", relative), patch.object(RUNNER, "LOCAL", local), \
                    patch.object(RUNNER, "execute_acceptance",
                                 side_effect=RuntimeError("synthetic_context_failure")):
                with self.assertRaisesRegex(RuntimeError, "synthetic_context_failure"):
                    RUNNER.audit()
                failure = json.loads((ROOT / local / "emergency_failure.json").read_text())
                self.assertEqual(failure["exception"], "RuntimeError")
                self.assertEqual(failure["empirical_access"], {"states": 0, "edges": 0})
                with self.assertRaisesRegex(FileExistsError, "audit_marker_exists"):
                    RUNNER.audit()

    def test_contract_has_no_empirical_or_scientific_route(self):
        source = (ROOT / "scripts/session_14r9h_runner_authority_context.py").read_text()
        for phrase in ("population.jsonl", "project_line(", "load_model", "target_index",
                       "summarize_state(", "Session 14R9G empirical"):
            self.assertNotIn(phrase, source)
        self.assertIn('choices=("preflight", "audit", "publication-check")', source)


if __name__ == "__main__":
    unittest.main()
