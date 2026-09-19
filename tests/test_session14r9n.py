"""Pre-access contract tests for Session 14R9N."""
import hashlib
import importlib.util
import pathlib
import tempfile
import unittest
from unittest.mock import Mock, patch

from defensive_network_disruption.validation.checkpoint_ci_authority import (
    CIExpectation, canonical_bytes, receipt_from_github)

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "r9n", ROOT / "scripts/session_14r9n_empirical_representation_retry.py")
R = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(R)


def expectation():
    return CIExpectation("a" * 40, "b" * 64, "c" * 64, "d" * 64, "e" * 64)


def run_record(status="completed", conclusion="success"):
    jobs = []
    for index, name in enumerate(("distribution", "test (3.11)", "test (3.13)"), 1):
        jobs.append({"databaseId": index, "name": name, "status": status,
                     "conclusion": conclusion, "startedAt": "2026-09-19T00:00:00Z",
                     "completedAt": "2026-09-19T00:01:00Z", "url": "https://example.invalid/job",
                     "steps": []})
    return {"databaseId": 10, "headSha": "a" * 40, "name": "CI", "workflowName": "CI",
            "status": status, "conclusion": conclusion, "createdAt": "2026-09-19T00:00:00Z",
            "updatedAt": "2026-09-19T00:01:00Z", "url": "https://example.invalid/run", "jobs": jobs}


class R9NTests(unittest.TestCase):
    def test_surface_and_fresh_namespace(self):
        self.assertEqual(R.OUT, pathlib.Path("outputs/continuous_occlusion_empirical_retry_r9n"))
        self.assertEqual(tuple(R.main.__code__.co_consts).count("preflight"), 1)

    def test_explicit_repaired_evaluator_and_linear_publisher(self):
        self.assertEqual(R.evaluate_edge.__module__, "defensive_network_disruption.geometry.r9k_comparator")
        self.assertEqual(R.linear_review.__module__, "defensive_network_disruption.validation.r9j_linear_publication")
        self.assertNotIn("derive_progress", R.__dict__)

    def test_population_and_workload_authority(self):
        self.assertEqual(R.POP_SHA, "cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d")
        self.assertEqual(sum(R.COUNTS), 7227)
        self.assertEqual(sum(R.COUNTS) * 10, 72270)
        self.assertEqual(sum(R.COUNTS) * 30, 216810)

    def test_direct_entry_guard(self):
        old = R.PROGRESS
        R.PROGRESS = None
        try:
            with self.assertRaises(PermissionError):
                R.calculate_edge("isotropic", (0, 0), (1, 0), ((0, 1),), "x", 0, 0)
        finally:
            R.PROGRESS = old

    def test_offline_receipt_passes_without_network(self):
        expected = expectation()
        receipt = receipt_from_github(run_record(), expected, captured_at="2026-09-19T00:02:00Z")
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            relative = pathlib.Path(directory).relative_to(ROOT)
            receipt_path = relative / "receipt.json"
            sidecar = relative / "receipt.json.sha256"
            raw = canonical_bytes(receipt)
            (ROOT / receipt_path).write_bytes(raw)
            (ROOT / sidecar).write_text(hashlib.sha256(raw).hexdigest() + "\n")
            with patch.object(R, "CI_RECEIPT", receipt_path), patch.object(R, "CI_RECEIPT_HASH", sidecar), \
                 patch.object(R, "ci_expectation", return_value=expected), \
                 patch.object(R.subprocess, "check_output", side_effect=AssertionError("network_or_git_called")):
                authority = R.offline_ci_authority()
            self.assertTrue(authority["validated_offline"])
            self.assertFalse(authority["network_required"])
            self.assertEqual(authority["run_id"], 10)

    def test_receipt_tampering_blocks(self):
        expected = expectation()
        receipt = receipt_from_github(run_record(), expected, captured_at="2026-09-19T00:02:00Z")
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            relative = pathlib.Path(directory).relative_to(ROOT)
            receipt_path = relative / "receipt.json"
            sidecar = relative / "receipt.json.sha256"
            raw = canonical_bytes(receipt)
            (ROOT / receipt_path).write_bytes(raw + b" ")
            (ROOT / sidecar).write_text(hashlib.sha256(raw).hexdigest() + "\n")
            with patch.object(R, "CI_RECEIPT", receipt_path), patch.object(R, "CI_RECEIPT_HASH", sidecar), \
                 patch.object(R, "ci_expectation", return_value=expected):
                with self.assertRaises(ValueError):
                    R.offline_ci_authority()

    def test_unsuccessful_receipt_cannot_be_created(self):
        with self.assertRaises(ValueError):
            receipt_from_github(run_record("completed", "failure"), expectation(),
                                captured_at="2026-09-19T00:02:00Z")

    def test_failure_before_progress_is_traceback_bound(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            relative = pathlib.Path(directory).relative_to(ROOT)
            old_out, old_local, old_progress = R.OUT, R.LOCAL, R.PROGRESS
            R.OUT, R.LOCAL, R.PROGRESS = relative, relative / "local", None
            try:
                controller = R.FailureController(ROOT / R.LOCAL)
                R.close_failure("startup_import", RuntimeError("synthetic"), controller)
                record = controller.validate()
                self.assertEqual(record["stage"], "startup_import")
                self.assertTrue((ROOT / R.LOCAL / "numerical_traceback.txt").is_file())
            finally:
                R.OUT, R.LOCAL, R.PROGRESS = old_out, old_local, old_progress

    def test_journal_failure_uses_legacy_stage_and_same_traceback(self):
        class Journal:
            path = pathlib.Path("unused")
            previous = "f" * 64
        progress = Mock(context={"state": None})
        progress.journal = Journal()
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            relative = pathlib.Path(directory).relative_to(ROOT)
            old_out, old_local, old_progress = R.OUT, R.LOCAL, R.PROGRESS
            R.OUT, R.LOCAL, R.PROGRESS = relative, relative / "local", progress
            controller = R.FailureController(ROOT / R.LOCAL)
            try:
                with patch.object(R, "linear_review", return_value="authority"), \
                     patch.object(R, "retain_authority", side_effect=lambda value: value), \
                     patch.object(R, "publish") as publish:
                    R.close_failure("preaccess_authority", ConnectionError("offline"), controller)
                progress.failure.assert_called_once()
                self.assertEqual(progress.failure.call_args.args[0], "preparation")
                self.assertEqual(publish.call_args.kwargs["traceback_path"], controller.traceback_path)
                self.assertEqual(controller.validate()["stage"], "preaccess_authority")
            finally:
                R.OUT, R.LOCAL, R.PROGRESS = old_out, old_local, old_progress

    def test_publication_failure_is_separate(self):
        class Journal:
            path = pathlib.Path("unused")
            previous = "f" * 64
        progress = Mock(context=None)
        progress.journal = Journal()
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            relative = pathlib.Path(directory).relative_to(ROOT)
            old_out, old_local, old_progress = R.OUT, R.LOCAL, R.PROGRESS
            R.OUT, R.LOCAL, R.PROGRESS = relative, relative / "local", progress
            controller = R.FailureController(ROOT / R.LOCAL)
            try:
                with patch.object(R, "linear_review", side_effect=ValueError("publication")):
                    R.close_failure("analysis", RuntimeError("original"), controller)
                self.assertTrue((ROOT / R.LOCAL / "publication_failure.json").is_file())
                self.assertEqual(controller.validate()["exception_type"], "RuntimeError")
            finally:
                R.OUT, R.LOCAL, R.PROGRESS = old_out, old_local, old_progress

    def test_attempt_is_reserved_after_offline_ci_validation(self):
        source = (ROOT / "scripts/session_14r9n_empirical_representation_retry.py").read_text()
        verify = source[source.index("def verify(_context):"):source.index("def access(_context):")]
        self.assertLess(verify.index("offline_ci_authority()"), verify.index("empirical_attempt.marker"))
        self.assertNotIn('(\"gh\",', source)
        self.assertNotIn("api.github.com", source)

    def test_exact_nineteen_file_schema(self):
        self.assertEqual(len(R.PUBLIC_ARTIFACTS), 19)
        self.assertNotIn("lifecycle.json", R.PUBLIC_ARTIFACTS)
        self.assertIn("qc.json", R.PUBLIC_ARTIFACTS)
        self.assertIn("manifest.json", R.PUBLIC_ARTIFACTS)

    def test_r9m_authority_is_hash_bound(self):
        self.assertEqual(R.HISTORICAL["outputs/continuous_occlusion_preaccess_authority_repair/manifest.json"],
                         "222364223e3c6a9b4b9a91605794593d4ddacf2a42ba3cf509c2bd4ad0f41e26")

    def test_actual_run_entry_uses_offline_authority_then_access(self):
        events = []
        class FakeJournal:
            path = pathlib.Path("synthetic-journal")
            previous = "a" * 64
            def __init__(self, _path): pass
            def close(self): events.append("closed")
        class FakeProgress:
            context = None
            def __init__(self, journal): self.journal = journal
            def authorize_access(self): events.append("authorized")
            def succeed(self): events.append("succeeded")
        class FakeLaunch:
            def __init__(self, _path): pass
            def execute(self, *, discover, expected, produce, verify, access):
                events.append("launch")
                self.assertion = verify(None)
                access(None)
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            relative = pathlib.Path(directory).relative_to(ROOT)
            old_out, old_local, old_progress = R.OUT, R.LOCAL, R.PROGRESS
            R.OUT, R.LOCAL, R.PROGRESS = relative, relative / "local", None
            try:
                with patch.object(R, "preflight", return_value={"status": "ready"}), \
                     patch.object(R, "copy_inherited", side_effect=lambda: events.append("copied")), \
                     patch.object(R, "Launch", FakeLaunch), patch.object(R, "Journal", FakeJournal), \
                     patch.object(R, "Progress", FakeProgress), \
                     patch.object(R, "verify_inherited", return_value={}), \
                     patch.object(R, "strict_prerequisite"), \
                     patch.object(R, "offline_ci_authority", side_effect=lambda: events.append("ci") or {
                         "receipt_sha256": "b" * 64}), \
                     patch.object(R, "prepare", side_effect=lambda: events.append("prepared")), \
                     patch.object(R, "analyze", return_value=(relative / "staging", [])), \
                     patch.object(R, "linear_review", return_value="authority"), \
                     patch.object(R, "retain_authority", side_effect=lambda value: value), \
                     patch.object(R, "publish", return_value={"status": "valid"}):
                    R.run()
                self.assertLess(events.index("ci"), events.index("authorized"))
                self.assertLess(events.index("authorized"), events.index("prepared"))
                self.assertTrue((ROOT / R.LOCAL / "empirical_attempt.marker").is_file())
                self.assertTrue((ROOT / R.LOCAL / "validator_receipt.json").is_file())
            finally:
                R.OUT, R.LOCAL, R.PROGRESS = old_out, old_local, old_progress


if __name__ == "__main__":
    unittest.main()
