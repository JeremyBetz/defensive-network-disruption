import copy
import importlib.util
import json
from pathlib import Path
import unittest

from defensive_network_disruption.validation.empirical_lifecycle import (
    EmpiricalLifecycle, ValidationMode, capture_unexpected_failure,
    make_preinitialization_failure, make_progress_view, package_record,
    validate_cross_file_package, validate_journal, validate_progress_view,
)
from defensive_network_disruption.validation.state_lifecycle import LifecycleError, snapshot_digest


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "session_14af_empirical_lifecycle_publication.py"
SPEC = importlib.util.spec_from_file_location("session14af", RUNNER)
session14af = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(session14af)


class Session14afEmpiricalLifecycleTests(unittest.TestCase):
    def test_modes_accept_zero_and_nonzero_access_in_context(self):
        pre, pre_view = session14af.pre_access_control()
        validate_progress_view(pre_view, pre.journal)
        partial, failure = session14af.partial_failure_control()
        self.assertGreater(failure.progress_view["access"]["states_opened"], 0)
        self.assertGreater(failure.progress_view["access"]["edges_opened"], 0)
        validate_progress_view(failure.progress_view, partial.journal)
        success, success_view = session14af.empirical_success_control()
        validate_progress_view(success_view, success.journal)
        bad = copy.deepcopy(failure.progress_view); bad["validation_mode"] = "pre_access"
        with self.assertRaisesRegex(LifecycleError, "pre_access_nonzero"):
            validate_progress_view(bad, partial.journal)

    def test_access_journal_is_authority_and_rejects_reset(self):
        authority, failure = session14af.partial_failure_control()
        result = validate_journal(authority.journal)
        self.assertEqual(result["states_opened"], 2)
        self.assertEqual(result["edges_opened"], 4)
        bad = copy.deepcopy(failure.progress_view)
        bad["access"] = {"states_opened":0,"edges_opened":0}
        bad["lifecycle"]["counters"]["states_opened"] = 0
        bad["lifecycle"]["counters"]["edges_opened"] = 0
        bad["lifecycle_sha256"] = snapshot_digest(bad["lifecycle"])
        with self.assertRaisesRegex(LifecycleError, "journal_view_mismatch|journal_access_mismatch"):
            validate_progress_view(bad, authority.journal)

    def test_cross_file_injections_execute_and_reject(self):
        authority, failure = session14af.partial_failure_control()
        rows = session14af.invalid_injections(authority, failure.progress_view)
        self.assertEqual(len(rows), 10)
        self.assertTrue(all(row["observed"].startswith("rejected:") for row in rows))
        self.assertIn("access_reset_to_zero", {row["injection"] for row in rows})

    def test_cross_file_status_hash_access_and_context(self):
        authority, failure = session14af.partial_failure_control()
        view = failure.progress_view
        records = list(session14af.views(view))
        validate_cross_file_package(mode=ValidationMode.EMPIRICAL_FAILURE, qc=records[0], manifest=records[1], evidence=records[2], report=records[3], journal=authority.journal)
        for index, field in ((1,"active_state"),(2,"active_edge"),(3,"failure_stage")):
            bad = copy.deepcopy(records); bad[index]["progress_authority"][field] = "changed"
            with self.assertRaises(LifecycleError):
                validate_cross_file_package(mode=ValidationMode.EMPIRICAL_FAILURE, qc=bad[0], manifest=bad[1], evidence=bad[2], report=bad[3], journal=authority.journal)
        with self.assertRaisesRegex(LifecycleError, "journal_required"):
            validate_cross_file_package(mode=ValidationMode.EMPIRICAL_FAILURE, qc=records[0], manifest=records[1], evidence=records[2], report=records[3], journal=None)

    def test_unexpected_failure_preserves_preterminal_and_traceback(self):
        authority, capture = session14af.partial_failure_control()
        pre = capture.pre_failure_snapshot["counters"]; terminal = capture.terminal_snapshot["counters"]
        self.assertEqual(pre["states_completed"], 1)
        self.assertEqual(pre["edges_completed"], 3)
        self.assertEqual(terminal["states_completed"], 1)
        self.assertEqual(capture.terminal_snapshot["active_state"], "state_02")
        self.assertEqual(capture.terminal_snapshot["active_edge"], "edge_02_02")
        self.assertIn("RuntimeError", capture.traceback_text)
        self.assertTrue(capture.progress_view["traceback_preserved"])
        self.assertEqual(capture.progress_view["access"], {"states_opened":2,"edges_opened":4})
        validate_progress_view(capture.progress_view, authority.journal)

    def test_active_context_after_completed_edge_before_state_completion(self):
        authority = EmpiricalLifecycle(); authority.discover_state("s", ("e1","e2")); authority.prepare_state("s")
        authority.authorize_access(); authority.open_state("s"); authority.start_state_evaluation("s")
        authority.open_edge("s","e1"); authority.start_edge("s","e1"); authority.complete_edge("s","e1")
        capture = capture_unexpected_failure(authority, lambda: (_ for _ in ()).throw(ValueError("stop")), stage="between_edges")
        self.assertEqual(capture.terminal_snapshot["active_state"], "s")
        self.assertIsNone(capture.terminal_snapshot["active_edge"])
        self.assertEqual(capture.terminal_snapshot["counters"]["edges_completed"], 1)

    def test_active_context_at_each_failure_stage(self):
        before = EmpiricalLifecycle(); before.discover_state("s", ("e",))
        c0 = capture_unexpected_failure(before, lambda: (_ for _ in ()).throw(RuntimeError()), stage="before_state")
        self.assertIsNone(c0.terminal_snapshot["active_state"]); self.assertIsNone(c0.terminal_snapshot["active_edge"])
        during_state = EmpiricalLifecycle(); during_state.discover_state("s", ("e",)); during_state.prepare_state("s"); during_state.start_state_evaluation("s")
        c1 = capture_unexpected_failure(during_state, lambda: (_ for _ in ()).throw(RuntimeError()), stage="state")
        self.assertEqual(c1.terminal_snapshot["active_state"], "s"); self.assertIsNone(c1.terminal_snapshot["active_edge"])
        during_edge = EmpiricalLifecycle(); during_edge.discover_state("s", ("e",)); during_edge.prepare_state("s"); during_edge.start_state_evaluation("s"); during_edge.start_edge("s","e")
        c2 = capture_unexpected_failure(during_edge, lambda: (_ for _ in ()).throw(RuntimeError()), stage="edge")
        self.assertEqual((c2.terminal_snapshot["active_state"],c2.terminal_snapshot["active_edge"]),("s","e"))

    def test_failure_before_initialization_is_distinct(self):
        try:
            raise RuntimeError("startup")
        except RuntimeError as exc:
            view = make_preinitialization_failure("startup", exc, "synthetic traceback")
        validate_progress_view(view)
        self.assertFalse(view["lifecycle_initialized"])
        self.assertIsNone(view["lifecycle"])

    def test_success_requires_complete_empirical_access(self):
        authority = EmpiricalLifecycle(); authority.discover_state("s", ("e",)); authority.prepare_state("s")
        authority.start_state_evaluation("s"); authority.start_edge("s","e"); authority.complete_edge("s","e"); authority.complete_state("s"); authority.succeed()
        with self.assertRaisesRegex(LifecycleError, "success_access_incomplete"):
            make_progress_view(authority, ValidationMode.EMPIRICAL_SUCCESS)

    def test_journal_chain_and_snapshot_tampering_rejected(self):
        authority, _ = session14af.pre_access_control()
        bad = list(authority.journal); bad[1]["previous_sha256"] = "0"*64
        with self.assertRaisesRegex(LifecycleError, "journal_chain"):
            validate_journal(bad)
        bad = list(authority.journal); bad[-1]["snapshot"]["counters"]["states_prepared"] = 0
        with self.assertRaises(LifecycleError): validate_journal(bad)

    def test_r4_style_launch_compatibility(self):
        result = session14af.r4_compatibility()
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["launch_state"], "EMPIRICAL_ACCESS_AUTHORIZED")
        self.assertTrue(result["partial_failure_validated"])
        self.assertGreater(result["synthetic_states_opened"], 0)
        self.assertEqual((result["real_states_opened"],result["real_edges_opened"]),(0,0))

    def test_runner_has_no_empirical_or_numerical_route(self):
        source = RUNNER.read_text()
        for forbidden in ("population.json", "option_network", "evaluate_field", "provider_product", "acquire"):
            self.assertNotIn(forbidden, source)
        self.assertEqual(set(session14af.FILES), {
            "authority_qualification.json","lifecycle_contract.json","validator_modes.json",
            "invalid_cross_file_injections.csv","valid_pre_access_control.json",
            "valid_empirical_partial_control.json","valid_empirical_success_control.json",
            "unexpected_failure_control.json","access_preservation_oracles.csv",
            "r4_wrapper_compatibility.json","qc.json",
        })

    def test_session14ae_history_unchanged(self):
        import hashlib
        expected = {
            "src/defensive_network_disruption/validation/state_lifecycle.py":"9aaff345990f2ea4d51afb86b024424ba8311dd2917d1cc417c2f76bcee991fe",
            "scripts/session_14ae_state_lifecycle_accounting.py":"06db5b26d3e68b8a8997ba8f5ddf001360733573ebb8a0fe2f506fbf1c8a6123",
            "docs/protocols/phase_14ae_state_lifecycle_accounting.md":"d500317a01afc30766974132623140e9ebd1de54cb1ae149869260195d54e232",
            "docs/session_14ae_state_lifecycle_accounting.md":"22d7d9e83e51d4187c4a02bd39c6f6940bca51450283e7d2fcaa51bb7d501fcf",
            "outputs/session14_state_lifecycle_accounting/manifest.json":"0bc787859ce4c7322cbb97be5d6859341a9c25b16ce476400b2027d58893fa01",
        }
        for name, digest in expected.items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(), digest)


if __name__ == "__main__": unittest.main()
