"""Pre-access tests for the fresh Session 14R9I execution wrapper."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "session14r9i_runner", ROOT / "scripts/session_14r9i_empirical_execution.py")
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


class Session14R9ITests(unittest.TestCase):
    def temporary_namespace(self):
        temporary = tempfile.TemporaryDirectory(dir=ROOT)
        return temporary, Path(temporary.name).relative_to(ROOT)

    def test_fresh_namespace_and_locked_base(self):
        base = RUNNER._load_base()
        self.assertEqual(base.START, RUNNER.START)
        self.assertEqual(base.OUT, RUNNER.OUT)
        self.assertEqual(base.LOCAL, RUNNER.LOCAL)
        self.assertEqual(base.PROTOCOL, RUNNER.PROTOCOL)
        self.assertEqual(base.TEST_COMMAND, RUNNER.TEST_COMMAND)
        self.assertIn("scripts/session_14r9i_empirical_execution.py", base.CODE)
        self.assertIn("outputs/continuous_occlusion_runner_authority_context/manifest.json",
                      base.HISTORICAL)

    def test_frozen_authority_is_complete_and_nonreconstructive(self):
        result = RUNNER.verify_frozen_authority()
        self.assertEqual(result["acceptance"],
                         {"cases": 108, "references": 366, "permutations": 399})
        self.assertTrue(result["visual_inherited"])
        fixture = json.loads((ROOT / RUNNER.FIXTURE).read_text())
        forbidden = {"coordinates", "roots", "partitions", "owner_ordinals", "event_keys"}
        self.assertFalse(forbidden & set(fixture))

    def test_authority_or_implementation_mutation_blocks(self):
        name = next(iter(RUNNER.FROZEN_IMPLEMENTATION))
        real = RUNNER._sha
        with patch.object(RUNNER, "_sha",
                          side_effect=lambda path: "0" * 64 if path.as_posix() == name else real(path)):
            with self.assertRaisesRegex(RuntimeError, "r9i_authority_changed"):
                RUNNER.verify_frozen_authority()

    def test_preflight_rejects_preaccess_marker(self):
        temporary, local = self.temporary_namespace()
        try:
            target = ROOT / local
            target.mkdir(exist_ok=True)
            (target / "preaccess.marker").write_text("reserved\n")
            with patch.object(RUNNER, "LOCAL", local), patch.object(
                    RUNNER, "verify_frozen_authority", return_value={}):
                with self.assertRaisesRegex(FileExistsError, "preaccess.marker"):
                    RUNNER.preflight(FakeBase())
        finally:
            temporary.cleanup()

    def test_same_runner_entry_persists_success_receipt(self):
        temporary, local = self.temporary_namespace()
        base = FakeBase()
        try:
            with patch.object(RUNNER, "LOCAL", local), patch.object(
                    RUNNER, "verify_frozen_authority", return_value={}), patch.object(
                    RUNNER.subprocess, "check_output", return_value="head\n"):
                RUNNER.run(base)
                self.assertEqual(base.runs, 1)
                self.assertTrue((ROOT / local / "preaccess.marker").is_file())
                saved = json.loads((ROOT / local / "final_validator_receipt.json").read_text())
                self.assertEqual(saved, base.receipt)
        finally:
            temporary.cleanup()

    def test_failure_is_independent_and_rerun_is_rejected(self):
        temporary, local = self.temporary_namespace()
        base = FakeBase(error=RuntimeError("synthetic_context_failure"))
        try:
            with patch.object(RUNNER, "LOCAL", local), patch.object(
                    RUNNER, "verify_frozen_authority", return_value={}), patch.object(
                    RUNNER.subprocess, "check_output", return_value="head\n"):
                with self.assertRaisesRegex(RuntimeError, "synthetic_context_failure"):
                    RUNNER.run(base)
                failure = json.loads((ROOT / local / "r9i_emergency_failure.json").read_text())
                self.assertEqual(failure["exception"], "RuntimeError")
                self.assertIn("synthetic_context_failure", failure["traceback"])
                with self.assertRaisesRegex(FileExistsError, "preaccess.marker"):
                    RUNNER.run(base)
        finally:
            temporary.cleanup()

    def test_publication_check_rejects_persisted_mismatch_and_false_success(self):
        temporary, local = self.temporary_namespace()
        try:
            target = ROOT / local
            target.mkdir(exist_ok=True)
            (target / "final_validator_receipt.json").write_text(
                '{"artifact_count":18,"status":"valid"}\n')
            with patch.object(RUNNER, "LOCAL", local):
                with self.assertRaisesRegex(RuntimeError, "final_validator_receipt_mismatch"):
                    RUNNER.publication_check(FakeBase())
            (target / "final_validator_receipt.json").write_text(
                '{"artifact_count":19,"status":"failure"}\n')
            with patch.object(RUNNER, "LOCAL", local):
                with self.assertRaisesRegex(RuntimeError, "final_validator_receipt_invalid"):
                    RUNNER.publication_check(FakeBase(
                        receipt={"artifact_count": 19, "status": "failure"}))
        finally:
            temporary.cleanup()

    def test_runner_exposes_only_governed_commands_and_no_data_shortcut(self):
        source = (ROOT / "scripts/session_14r9i_empirical_execution.py").read_text()
        self.assertIn('choices=("preflight", "run", "publication-check")', source)
        for phrase in ("project_line(", "load_model", "target_index", "render-synthetic",
                       "selected_geometry.json", "000020_structure.json"):
            self.assertNotIn(phrase, source)

    def test_nineteen_artifact_publication_and_lifecycle_contract(self):
        base = RUNNER._load_base()
        self.assertEqual(len(base.PUBLIC_ARTIFACTS), 19)
        self.assertNotIn("lifecycle_summary.json", base.PUBLIC_ARTIFACTS)
        validator = (ROOT / "src/defensive_network_disruption/validation/r9e_publication.py").read_text()
        self.assertIn('qc["progress_authority"] != actual', validator)
        self.assertIn('exposure["states_opened"]', validator)

    def test_population_and_target_free_projection_authority_are_inherited(self):
        base = RUNNER._load_base()
        self.assertEqual(base.POP_SHA,
                         "cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d")
        self.assertEqual(base.COUNTS, (885, 801, 952, 877, 861, 629, 764, 734, 724))
        projection = (ROOT / "src/defensive_network_disruption/data/representation_projection.py").read_text()
        self.assertIn("skip", projection)
        for phrase in ("target_rank", "chosen_receiver", "model_score", "option_share"):
            self.assertNotIn(phrase, projection)


if __name__ == "__main__":
    unittest.main()
