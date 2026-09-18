import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from defensive_network_disruption.validation.checkpoint_ci_authority import (
    CIExpectation, FailureController, canonical_bytes, capture_github_receipt,
    compare_live, receipt_from_github, sha256_file, validate_receipt)


ROOT = Path(__file__).resolve().parents[1]


def expectation(commit="a" * 40):
    return CIExpectation(commit, "b" * 64, "c" * 64, "d" * 64, "e" * 64)


def github_run(commit="a" * 40):
    jobs = []
    for index, name in enumerate(("distribution", "test (3.11)", "test (3.13)"), 1):
        jobs.append({"databaseId": index, "name": name, "status": "completed", "conclusion": "success",
                     "startedAt": "2026-09-18T00:00:00Z", "completedAt": "2026-09-18T00:01:00Z",
                     "url": "https://example.invalid/job/" + str(index)})
    return {"databaseId": 10, "headSha": commit, "name": "CI", "workflowName": "CI",
            "status": "completed", "conclusion": "success", "createdAt": "2026-09-18T00:00:00Z",
            "updatedAt": "2026-09-18T00:02:00Z", "url": "https://example.invalid/run/10", "jobs": jobs}


def receipt(commit="a" * 40):
    return receipt_from_github(github_run(commit), expectation(commit), captured_at="2026-09-18T00:03:00Z")


class ReceiptTests(unittest.TestCase):
    def write(self, directory, value, canonical=True):
        target = Path(directory) / "receipt.json"
        target.write_bytes(canonical_bytes(value) if canonical else json.dumps(value).encode())
        return target

    def test_valid_offline_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            value = receipt(); target = self.write(d, value)
            authority = validate_receipt(target, expectation())
            self.assertEqual(authority.checkpoint_commit, "a" * 40)
            self.assertEqual(authority.run_id, 10)
            self.assertEqual(authority.receipt_sha256, hashlib.sha256(target.read_bytes()).hexdigest())

    def test_capture_uses_authenticated_command_result(self):
        with tempfile.TemporaryDirectory() as d:
            raw = json.dumps(github_run()).encode(); calls = []
            def command(args): calls.append(args); return raw
            target = Path(d) / "receipt.json"
            capture_github_receipt(target, 10, expectation(), command=command,
                                   captured_at="2026-09-18T00:03:00Z")
            self.assertEqual(calls[0][:4], ("gh", "run", "view", "10"))
            validate_receipt(target, expectation())

    def test_missing_receipt_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError): validate_receipt(Path(d) / "missing", expectation())

    def assert_mutation_blocks(self, mutate, expected=None):
        value = receipt(); mutate(value)
        with tempfile.TemporaryDirectory() as d:
            target = self.write(d, value)
            with self.assertRaises((ValueError, KeyError, TypeError)):
                validate_receipt(target, expected or expectation())

    def test_wrong_commit_blocks(self): self.assert_mutation_blocks(lambda x: x.update(checkpoint_commit="0" * 40))
    def test_wrong_repository_blocks(self): self.assert_mutation_blocks(lambda x: x.update(repository="other/repo"))
    def test_wrong_workflow_blocks(self): self.assert_mutation_blocks(lambda x: x["workflow"].update(name="other"))
    def test_pending_run_blocks(self): self.assert_mutation_blocks(lambda x: x["run"].update(status="in_progress", conclusion=""))
    def test_failed_run_blocks(self): self.assert_mutation_blocks(lambda x: x["run"].update(conclusion="failure"))
    def test_cancelled_job_blocks(self): self.assert_mutation_blocks(lambda x: x["jobs"][0].update(conclusion="cancelled"))
    def test_pending_job_blocks(self): self.assert_mutation_blocks(lambda x: x["jobs"][0].update(status="in_progress"))
    def test_missing_job_blocks(self): self.assert_mutation_blocks(lambda x: x["jobs"].pop())
    def test_duplicate_job_blocks(self): self.assert_mutation_blocks(lambda x: x["jobs"].append(copy.deepcopy(x["jobs"][0])))
    def test_binding_tamper_blocks(self): self.assert_mutation_blocks(lambda x: x["bindings"].update(protocol_sha256="0" * 64))
    def test_added_field_blocks(self): self.assert_mutation_blocks(lambda x: x.update(success=True))

    def test_frozen_hash_rejects_otherwise_valid_tamper(self):
        with tempfile.TemporaryDirectory() as d:
            value = receipt(); target = self.write(d, value); frozen = hashlib.sha256(target.read_bytes()).hexdigest()
            value["run"]["run_id"] += 1; target.write_bytes(canonical_bytes(value))
            with self.assertRaisesRegex(ValueError, "ci_receipt_hash"):
                validate_receipt(target, expectation(), expected_sha256=frozen)

    def test_noncanonical_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            target = self.write(d, receipt(), canonical=False)
            with self.assertRaisesRegex(ValueError, "noncanonical"):
                validate_receipt(target, expectation())

    def test_capture_rejects_bad_status_before_write(self):
        run = github_run(); run["jobs"][0]["conclusion"] = "failure"
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "receipt.json"
            with self.assertRaisesRegex(ValueError, "not_successful"):
                capture_github_receipt(target, 10, expectation(), command=lambda _: json.dumps(run).encode(),
                                       captured_at="2026-09-18T00:03:00Z")
            self.assertFalse(target.exists())

    def test_live_network_failure_does_not_invalidate(self):
        with tempfile.TemporaryDirectory() as d:
            authority = validate_receipt(self.write(d, receipt()), expectation())
            for error in (ConnectionError("offline"), TimeoutError("timeout"), OSError("dns")):
                result = compare_live(authority, lambda _run, error=error: (_ for _ in ()).throw(error))
                self.assertFalse(result["available"]); self.assertIsNone(result["matches"])

    def test_live_comparison_is_diagnostic(self):
        with tempfile.TemporaryDirectory() as d:
            authority = validate_receipt(self.write(d, receipt()), expectation())
            self.assertTrue(compare_live(authority, lambda _: {
                "headSha": "a" * 40, "status": "completed", "conclusion": "success"})["matches"])
            self.assertFalse(compare_live(authority, lambda _: {
                "headSha": "0" * 40, "status": "completed", "conclusion": "success"})["matches"])

    def test_create_once_capture(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "receipt.json"; command = lambda _: json.dumps(github_run()).encode()
            capture_github_receipt(target, 10, expectation(), command=command, captured_at="2026-09-18T00:03:00Z")
            with self.assertRaises(FileExistsError):
                capture_github_receipt(target, 10, expectation(), command=command, captured_at="2026-09-18T00:03:00Z")


class FailureTests(unittest.TestCase):
    def capture(self, kind=RuntimeError, stage="preaccess_authority"):
        temporary = tempfile.TemporaryDirectory(); controller = FailureController(Path(temporary.name))
        try: raise kind("failure")
        except BaseException as error: record = controller.capture(error, stage, timestamp="2026-09-18T00:00:00Z")
        return temporary, controller, record

    def test_original_traceback_is_bound(self):
        t, controller, record = self.capture()
        try:
            self.assertEqual(sha256_file(controller.traceback_path), record["traceback_sha256"])
            self.assertEqual(controller.validate()["status"], "valid")
            self.assertEqual(record["journal_stage"], "preparation")
        finally: t.cleanup()

    def test_traceback_tamper_rejected(self):
        t, controller, _ = self.capture()
        try:
            controller.traceback_path.write_text("changed")
            with self.assertRaisesRegex(ValueError, "traceback_binding"): controller.validate()
        finally: t.cleanup()

    def test_emergency_tamper_rejected(self):
        t, controller, _ = self.capture()
        try:
            value = json.loads(controller.emergency_path.read_text()); value["status"] = "changed"
            controller.emergency_path.write_bytes(canonical_bytes(value))
            with self.assertRaisesRegex(ValueError, "emergency_binding"): controller.validate()
        finally: t.cleanup()

    def test_failure_capture_is_create_once(self):
        t, controller, _ = self.capture()
        try:
            try: raise RuntimeError("second")
            except RuntimeError as error:
                with self.assertRaises(FileExistsError): controller.capture(error, "second")
        finally: t.cleanup()

    def test_publication_failure_preserves_original(self):
        t, controller, original = self.capture()
        try:
            before = sha256_file(controller.original_path)
            try: raise OSError("publication")
            except OSError as error: publication = controller.publication_failure(error, timestamp="2026-09-18T00:00:01Z")
            self.assertEqual(before, sha256_file(controller.original_path))
            self.assertEqual(publication["original_failure_sha256"], before)
            self.assertEqual(controller.validate()["traceback_sha256"], original["traceback_sha256"])
        finally: t.cleanup()

    def test_exception_matrix(self):
        for kind in (ConnectionError, TimeoutError, OSError, ImportError, FileExistsError, ValueError):
            t, controller, record = self.capture(kind, kind.__name__)
            try:
                self.assertEqual(controller.validate()["exception_type"], kind.__name__)
                self.assertEqual(record["stage"], kind.__name__)
            finally: t.cleanup()


class RunnerTests(unittest.TestCase):
    def load_runner(self):
        spec = importlib.util.spec_from_file_location("r9m_runner", ROOT / "scripts/session_14r9m_preaccess_authority_traceback_repair.py")
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

    def test_r9l_style_failure_publication_binds_traceback(self):
        module = self.load_runner()
        with tempfile.TemporaryDirectory(dir=ROOT / "outputs") as d:
            result = module._failure_package(Path(d))
        self.assertEqual(result["validator_status"], "valid")
        self.assertEqual(result["states_opened"], 0); self.assertEqual(result["edges_opened"], 0)
        self.assertTrue(result["traceback_bound"])
        self.assertEqual(result["journal_failure_stage"], "preparation")
        self.assertEqual(result["outer_failure_stage"], "preaccess_authority")

    def test_runner_has_no_mandatory_gh_call(self):
        text = (ROOT / "scripts/session_14r9m_preaccess_authority_traceback_repair.py").read_text()
        self.assertNotIn('"gh"', text); self.assertNotIn("api.github.com", text)

    def test_capture_tool_is_separate(self):
        text = (ROOT / "scripts/capture_checkpoint_ci_authority.py").read_text()
        self.assertIn("capture_github_receipt", text)
        runner = (ROOT / "scripts/session_14r9m_preaccess_authority_traceback_repair.py").read_text()
        self.assertNotIn("capture_github_receipt", runner)

    def test_no_empirical_routes(self):
        text = (ROOT / "scripts/session_14r9m_preaccess_authority_traceback_repair.py").read_text()
        for forbidden in ("project_line", "evaluate_edge", "population.jsonl", "authorize_access"):
            self.assertNotIn(forbidden, text)

    def test_historical_authorities_match(self):
        module = self.load_runner()
        for name, expected in module.HISTORICAL.items():
            self.assertEqual(sha256_file(ROOT / name), expected)


if __name__ == "__main__":
    unittest.main()
