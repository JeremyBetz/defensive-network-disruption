"""Pre-access tests for the fresh Session 14R9G execution wrapper."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "session14r9g_runner", ROOT / "scripts/session_14r9g_empirical_execution.py")
RUNNER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(RUNNER)


class FakeBase:
    def __init__(self, *, error=None, receipt=None):
        self.error = error
        self.receipt = receipt or {"status": "valid", "artifact_count": 19}
        self.runs = 0

    def preflight(self):
        return {"schema_version": 1, "status": "ready"}

    def run(self):
        self.runs += 1
        if self.error is not None:
            raise self.error

    def publication_check(self):
        return self.receipt


class Session14R9GTests(unittest.TestCase):
    def temporary_namespace(self):
        temporary = tempfile.TemporaryDirectory(dir=ROOT)
        root = Path(temporary.name)
        return temporary, root.relative_to(ROOT)

    def test_base_is_frozen_into_fresh_namespace(self):
        base = RUNNER._load_base()
        self.assertEqual(base.START, RUNNER.START)
        self.assertEqual(base.OUT, RUNNER.OUT)
        self.assertEqual(base.PROTOCOL, RUNNER.PROTOCOL)
        self.assertEqual(base.TEST_COMMAND, RUNNER.TEST_COMMAND)
        self.assertIn(RUNNER.FIXTURE.as_posix(), base.HISTORICAL)
        self.assertIn("scripts/session_14r9g_empirical_execution.py", base.CODE)

    def test_portable_fixture_is_exact_and_nonreconstructive(self):
        result = RUNNER._verify_fixture(FakeBase())
        self.assertEqual(result["sha256"], RUNNER.FIXTURE_SHA256)
        self.assertTrue(result["non_reconstructive"])
        self.assertFalse(result["private_fallback"])

    def test_changed_fixture_blocks(self):
        with patch.object(RUNNER, "_sha", return_value="0" * 64):
            with self.assertRaisesRegex(RuntimeError, "portable_fixture_bytes_changed"):
                RUNNER._verify_fixture(FakeBase())

    def test_preflight_rejects_marker_collision(self):
        temporary, local = self.temporary_namespace()
        try:
            with patch.object(RUNNER, "LOCAL", local), patch.object(
                    RUNNER, "_verify_fixture", return_value={"status": "valid"}):
                (ROOT / local).mkdir(exist_ok=True)
                (ROOT / local / "preaccess.marker").write_text("reserved\n")
                with self.assertRaisesRegex(FileExistsError, "preaccess.marker"):
                    RUNNER.preflight(FakeBase())
        finally:
            temporary.cleanup()

    def test_success_uses_same_entry_and_persists_receipt(self):
        temporary, local = self.temporary_namespace()
        base = FakeBase(receipt={"status": "valid", "artifact_count": 19})
        try:
            with patch.object(RUNNER, "LOCAL", local), patch.object(
                    RUNNER, "_verify_fixture", return_value={"status": "valid"}), patch.object(
                    RUNNER.subprocess, "check_output", return_value="head\n"):
                RUNNER.run(base)
                self.assertEqual(base.runs, 1)
                self.assertTrue((ROOT / local / "preaccess.marker").is_file())
                saved = json.loads((ROOT / local / "final_validator_receipt.json").read_text())
                self.assertEqual(saved, base.receipt)
        finally:
            temporary.cleanup()

    def test_failure_is_preserved_and_cannot_rerun(self):
        temporary, local = self.temporary_namespace()
        base = FakeBase(error=RuntimeError("synthetic_prerequisite_failure"))
        try:
            with patch.object(RUNNER, "LOCAL", local), patch.object(
                    RUNNER, "_verify_fixture", return_value={"status": "valid"}), patch.object(
                    RUNNER.subprocess, "check_output", return_value="head\n"):
                with self.assertRaisesRegex(RuntimeError, "synthetic_prerequisite_failure"):
                    RUNNER.run(base)
                failure = json.loads((ROOT / local / "r9g_emergency_failure.json").read_text())
                self.assertEqual(failure["status"], "failure")
                self.assertEqual(failure["exception"], "RuntimeError")
                with self.assertRaisesRegex(FileExistsError, "preaccess.marker"):
                    RUNNER.run(base)
        finally:
            temporary.cleanup()

    def test_publication_check_rejects_persisted_mismatch(self):
        temporary, local = self.temporary_namespace()
        try:
            target = ROOT / local
            target.mkdir(exist_ok=True)
            (target / "final_validator_receipt.json").write_text(
                '{"artifact_count":18,"status":"valid"}\n')
            with patch.object(RUNNER, "LOCAL", local):
                with self.assertRaisesRegex(RuntimeError, "final_validator_receipt_mismatch"):
                    RUNNER.publication_check(FakeBase())
        finally:
            temporary.cleanup()

    def test_runner_has_no_empirical_shortcut_or_render_route(self):
        source = (ROOT / "scripts/session_14r9g_empirical_execution.py").read_text()
        for phrase in ("project_line(", "load_model", "target_index", "render-synthetic",
                       "selected_geometry.json", "000020_structure.json"):
            self.assertNotIn(phrase, source)
        self.assertIn('choices=("preflight", "run", "publication-check")', source)

    def test_nineteen_artifact_contract_is_inherited(self):
        base = RUNNER._load_base()
        self.assertEqual(len(base.PUBLIC_ARTIFACTS), 19)
        self.assertNotIn("lifecycle_summary.json", base.PUBLIC_ARTIFACTS)
        self.assertIn("qc.json", base.PUBLIC_ARTIFACTS)


if __name__ == "__main__":
    unittest.main()
