import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from defensive_network_disruption.validation.r9a_publication import (
    MANIFEST_MEMBERS,
    PUBLIC_ARTIFACTS,
    PublicationContractError,
    SCHEMA_ID,
    sha256_file,
    validate_public_package,
)


def snapshot(status="success"):
    counters = {
        "states_discovered": 1, "states_prepared": 1,
        "states_evaluation_started": 1, "states_completed": 1,
        "edges_discovered": 1, "edges_opened": 1,
        "edges_evaluation_started": 1, "edges_completed": 1,
        "unresolved_exposed_edges": 0, "projection_attempts": 1,
        "unresolved_projection_attempts": 0, "field_evaluations_started": 3,
        "field_evaluations_completed": 3, "state_failures": 0,
    }
    return {
        "schema_version": 1, "status": status, "access_authorized": True,
        "counters": counters,
        "field_work_by_candidate": {name: {"started": 1, "completed": 1}
                                    for name in ("isotropic", "expanding", "constant_width")},
        "active": {"state": None, "edge": None, "candidate": None},
        "failure_stage": None, "exception": None, "confirmed_zero_exposure": False,
    }


def progress(mode="empirical_success"):
    snap = snapshot("success" if mode == "empirical_success" else "failure")
    if mode == "empirical_failure":
        snap["failure_stage"] = "publication"; snap["exception"] = "RuntimeError"
    return {"schema_version": 2, "mode": mode, "journal_sha256": "1" * 64,
            "snapshot_sha256": "2" * 64, "snapshot": snap}


def write_package(folder: Path, *, status="success", authority=None):
    folder.mkdir()
    authority = authority or progress("empirical_success" if status == "success" else "empirical_failure")
    qc = {"schema_version": 1, "status": status, "progress_authority": authority,
          "stage": "closure", "exception": None if status == "success" else "RuntimeError",
          "scientific_comparisons_available": status == "success"}
    for name in MANIFEST_MEMBERS:
        path = folder / name
        if name == "qc.json": path.write_text(json.dumps(qc, sort_keys=True) + "\n")
        elif name.endswith(".json"): path.write_text("{}\n")
        elif name.endswith(".csv"): path.write_text("fixture\n")
        else: path.write_text("<svg/>\n")
    if status == "success":
        available = list(MANIFEST_MEMBERS); unavailable = []
    else:
        available = [name for name in MANIFEST_MEMBERS if name in {
            "preaccess_contract.json", "retained_observation_certificate_gate.json",
            "runner_failure_oracles.json", "runner_success_oracle.json",
            "synthetic_acceptance.json", "evidence_type_summary.json", "visual_qa.json",
            "synthetic_stress_summary.json", "qc.json", "synthetic_field_comparison.svg"}]
        unavailable = [name for name in MANIFEST_MEMBERS if name not in available]
        for name in unavailable: (folder / name).unlink()
    manifest = {
        "schema_version": 1, "status": status, "progress_authority": authority,
        "start": "0" * 40, "protocol": "3" * 64,
        "implementation": {"runner": "4" * 64}, "environment": {},
        "outputs": {name: sha256_file(folder / name) for name in available},
        "unavailable": unavailable, "private_evidence_sha256": "5" * 64,
        "private_manifest_sha256": "6" * 64,
    }
    (folder / "manifest.json").write_text(json.dumps(manifest, sort_keys=True) + "\n")
    return qc, manifest


class Session14R9aPublicationTests(unittest.TestCase):
    def package(self, status="success"):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        folder = Path(temp.name) / "package"
        qc, manifest = write_package(folder, status=status)
        return folder, qc, manifest

    def rewrite(self, folder, qc, manifest):
        (folder / "qc.json").write_text(json.dumps(qc, sort_keys=True) + "\n")
        manifest["outputs"]["qc.json"] = sha256_file(folder / "qc.json")
        manifest["progress_authority"] = qc["progress_authority"]
        (folder / "manifest.json").write_text(json.dumps(manifest, sort_keys=True) + "\n")

    def test_nineteen_artifact_success_uses_qc_lifecycle(self):
        folder, qc, _ = self.package()
        receipt = validate_public_package(folder)
        self.assertEqual(len(PUBLIC_ARTIFACTS), 19)
        self.assertEqual(receipt.schema_id, SCHEMA_ID)
        self.assertEqual(receipt.lifecycle_representation_source, "qc.json.progress_authority")
        self.assertEqual(receipt.result, "valid")
        self.assertEqual(qc["progress_authority"]["snapshot"]["counters"]["edges_opened"], 1)

    def test_missing_qc_lifecycle_field_blocks(self):
        folder, qc, manifest = self.package()
        del qc["progress_authority"]["snapshot"]["counters"]["edges_opened"]
        self.rewrite(folder, qc, manifest)
        with self.assertRaises(PublicationContractError): validate_public_package(folder)

    def test_conflicting_qc_lifecycle_field_blocks(self):
        folder, qc, manifest = self.package()
        qc["progress_authority"]["snapshot"]["counters"]["edges_completed"] = 2
        self.rewrite(folder, qc, manifest)
        with self.assertRaises(PublicationContractError): validate_public_package(folder)

    def test_stale_twentieth_file_not_required(self):
        folder, _, _ = self.package()
        self.assertFalse((folder / "lifecycle_summary.json").exists())
        self.assertEqual(validate_public_package(folder).artifact_count, 19)

    def test_consistent_optional_legacy_file_is_accepted(self):
        folder, qc, _ = self.package()
        receipt = validate_public_package(folder, optional_legacy_lifecycle=qc["progress_authority"])
        self.assertTrue(receipt.optional_legacy_lifecycle_checked)

    def test_conflicting_optional_legacy_file_blocks(self):
        folder, qc, _ = self.package()
        legacy = copy.deepcopy(qc["progress_authority"]); legacy["mode"] = "empirical_failure"
        with self.assertRaisesRegex(PublicationContractError, "legacy_lifecycle_conflict"):
            validate_public_package(folder, optional_legacy_lifecycle=legacy)

    def test_manifest_schema_mismatch_blocks(self):
        folder, _, manifest = self.package()
        manifest["unavailable"].append("lifecycle_summary.json")
        (folder / "manifest.json").write_text(json.dumps(manifest) + "\n")
        with self.assertRaises(PublicationContractError): validate_public_package(folder)

    def test_failure_package_is_valid_without_scientific_files(self):
        folder, _, _ = self.package("failure")
        receipt = validate_public_package(folder)
        self.assertEqual(receipt.package_status, "failure")

    def test_incomplete_success_blocks(self):
        folder, _, manifest = self.package()
        missing = "candidate_summary.json"; (folder / missing).unlink()
        del manifest["outputs"][missing]; manifest["unavailable"].append(missing)
        (folder / "manifest.json").write_text(json.dumps(manifest) + "\n")
        with self.assertRaisesRegex(PublicationContractError, "invalid_success"):
            validate_public_package(folder)

    def test_validator_derived_success_not_caller_flag(self):
        folder, qc, manifest = self.package()
        qc["scientific_comparisons_available"] = False
        self.rewrite(folder, qc, manifest)
        with self.assertRaisesRegex(PublicationContractError, "invalid_success"):
            validate_public_package(folder)

    def test_preaccess_failure_authority(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        folder = Path(temp.name) / "package"
        authority = {"schema_version": 2, "mode": "pre_access", "journal_sha256": None,
                     "snapshot_sha256": None, "snapshot": None}
        write_package(folder, status="failure", authority=authority)
        self.assertEqual(validate_public_package(folder).package_status, "failure")

    def test_no_numerical_or_empirical_route(self):
        source = Path(__import__("defensive_network_disruption.validation.r9a_publication",
                                 fromlist=["x"]).__file__).read_text()
        for forbidden in ("numpy", "scipy", "project_line", "evaluate_edge", "render_synthetic"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
