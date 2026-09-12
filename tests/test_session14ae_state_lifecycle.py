import copy
import importlib.util
import json
from pathlib import Path
import unittest

from defensive_network_disruption.validation.state_lifecycle import (
    LifecycleError, LifecycleProgress, snapshot_digest, validate_cross_file,
    validate_snapshot,
)


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "session_14ae_state_lifecycle_accounting.py"
SPEC = importlib.util.spec_from_file_location("session14ae", RUNNER)
session14ae = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(session14ae)


class Session14aeLifecycleTests(unittest.TestCase):
    def test_r3_regression_prepared_is_not_completed(self):
        progress = session14ae.prepared_only()
        progress.block("after_preparation", "synthetic_stop")
        snapshot = progress.snapshot(); validate_snapshot(snapshot)
        self.assertEqual(snapshot["counters"]["states_prepared"], 1)
        self.assertEqual(snapshot["counters"]["states_evaluation_started"], 0)
        self.assertEqual(snapshot["counters"]["states_completed"], 0)

    def test_state_and_edge_parent_child_transitions(self):
        p = LifecycleProgress(); p.discover_state("s", ("e1", "e2"))
        with self.assertRaisesRegex(LifecycleError, "invalid_state_start"): p.start_state_evaluation("s")
        p.prepare_state("s"); p.start_state_evaluation("s")
        with self.assertRaisesRegex(LifecycleError, "state_edges_incomplete"): p.complete_state("s")
        p.start_edge("s", "e1"); p.complete_edge("s", "e1")
        with self.assertRaisesRegex(LifecycleError, "state_edges_incomplete"): p.complete_state("s")
        p.start_edge("s", "e2"); p.complete_edge("s", "e2"); p.complete_state("s"); p.succeed()
        validate_snapshot(p.snapshot())

    def test_duplicate_and_terminal_transitions_rejected(self):
        p = LifecycleProgress(); p.discover_state("s", ("e",))
        with self.assertRaises(LifecycleError): p.discover_state("s", ("e",))
        p.prepare_state("s")
        with self.assertRaises(LifecycleError): p.prepare_state("s")
        p.block("gate", "stop")
        with self.assertRaisesRegex(LifecycleError, "terminal_progress"): p.start_state_evaluation("s")

    def test_failure_stages_preserve_partial_work(self):
        rows = {row["injection"]: row for row in session14ae.failure_controls()}
        self.assertEqual(rows["preparation"]["states_prepared"], 0)
        self.assertEqual(rows["after_preparation"]["states_evaluation_started"], 0)
        self.assertEqual(rows["evaluation_start"]["states_completed"], 0)
        self.assertEqual(rows["mid_edge"]["edges_completed"], 0)
        self.assertEqual(rows["after_one_edge"]["edges_completed"], 1)
        self.assertEqual(rows["publication_validation"]["states_completed"], 1)

    def test_state_failure_and_edge_failure_are_derived(self):
        p = session14ae.prepared_only(); p.start_state_evaluation("state_01"); p.start_edge("state_01", "edge_01")
        p.fail("edge", "SyntheticFailure", state_key="state_01", edge_key="edge_01")
        counters = p.snapshot()["counters"]
        self.assertEqual((counters["state_failures"], counters["edge_failures"]), (1, 1))
        self.assertEqual((counters["states_completed"], counters["edges_completed"]), (0, 0))

    def test_success_requires_complete_nonempty_work(self):
        with self.assertRaisesRegex(LifecycleError, "incomplete_success"): LifecycleProgress().succeed()
        p = session14ae.completed(2, 3); s = p.snapshot(); validate_snapshot(s)
        self.assertEqual(s["counters"]["states_completed"], 2)
        self.assertEqual(s["counters"]["edges_completed"], 6)

    def test_invalid_and_valid_publication_oracles(self):
        invalid, valid = session14ae.publication_oracles()
        self.assertEqual(len(invalid), 10)
        self.assertTrue(all(row["observed"].startswith("rejected:") for row in invalid))
        self.assertEqual(len(valid), 4)
        self.assertTrue(all(row["observed"] == "accepted" for row in valid))

    def test_access_is_separate_and_authorized(self):
        rows = {row["oracle"]: row for row in session14ae.access_oracles()}
        self.assertEqual((rows["no_access"]["synthetic_states_opened"], rows["no_access"]["synthetic_edges_opened"]), (0, 0))
        self.assertEqual((rows["state_only"]["synthetic_states_opened"], rows["state_only"]["synthetic_edges_opened"]), (1, 0))
        self.assertEqual((rows["state_and_first_edge"]["synthetic_states_opened"], rows["state_and_first_edge"]["synthetic_edges_opened"]), (1, 1))
        self.assertTrue(all(row["real_states_opened"] == row["real_edges_opened"] == 0 for row in rows.values()))
        p = LifecycleProgress(); p.discover_state("s", ("e",))
        with self.assertRaisesRegex(LifecycleError, "invalid_state_access"): p.open_state("s")

    def test_cross_file_digest_and_status(self):
        p = session14ae.completed(); snapshot = p.snapshot(); digest = snapshot_digest(snapshot)
        qc = {"schema_version":1,"status":"success","classification":"A","readiness":1,
              "real_access":{"states_opened":0,"edges_opened":0},"lifecycle":snapshot,"lifecycle_sha256":digest}
        manifest={"status":"success","lifecycle_sha256":digest}; evidence=dict(manifest); report=dict(manifest)
        validate_cross_file(qc,manifest,evidence,report)
        for record in (manifest,evidence,report):
            bad=copy.deepcopy(record);bad["lifecycle_sha256"]="0"*64
            args=[manifest,evidence,report];args[(manifest,evidence,report).index(record)]=bad
            with self.assertRaises(LifecycleError):validate_cross_file(qc,*args)
        bad=copy.deepcopy(qc);bad["lifecycle"]["counters"]["states_completed"]=0
        with self.assertRaises(LifecycleError):validate_cross_file(bad,manifest,evidence,report)

    def test_canonical_digest_is_order_stable_and_finite(self):
        a={"b":1,"a":{"z":0}};b={"a":{"z":0},"b":1}
        self.assertEqual(snapshot_digest(a),snapshot_digest(b))
        with self.assertRaises(LifecycleError):snapshot_digest({"x":float("nan")})

    def test_runner_has_no_prohibited_route(self):
        source=RUNNER.read_text()
        self.assertNotIn("representation_retry",source)
        self.assertNotIn("option_network",source)
        self.assertNotIn("population.json",source)
        self.assertNotIn("acquire",source)
        self.assertEqual(set(session14ae.FILES),{
            "lifecycle_contract.json","lifecycle_oracles.csv","publication_invalid_oracles.csv",
            "publication_valid_oracles.csv","access_accounting_oracles.csv","failure_controls.csv",
            "success_control.json","cross_file_validation.json","qc.json"})

    def test_historical_r3_files_are_bound_and_unchanged(self):
        expected={
            "scripts/session_14r3_occlusion_study.py":"23e054aabd8bc06ec500cfe2132969754e3824e3776f634370987c71c446a55c",
            "docs/protocols/phase_14r3_continuous_occlusion_empirical_retry.md":"26ed59932ebba135c6a1142a2e523ba1af7fb9caf59a978196ba0cfa8a0a965b",
            "docs/session_14r3_continuous_occlusion_empirical_retry.md":"f1a97f132aebe0fe79b71058cd46e3f371734a137a6e66a97f00009903a2e1e7",
            "outputs/continuous_occlusion_retry_14r3/manifest.json":"860e7a8a066795bfd3fda94d9e3adb4b496ed950c73ef1711ae3cea729efd03b",
        }
        import hashlib
        for path,value in expected.items():self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),value)


if __name__ == "__main__": unittest.main()
