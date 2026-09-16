"""Synthetic tests for prospective Session 14R9E wiring."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np

from defensive_network_disruption.geometry import r7_representation as historical
from defensive_network_disruption.geometry import r9e_representation as repaired
from defensive_network_disruption.validation import independent_certificate_verifier as certificate
from defensive_network_disruption.validation import r9f_portable_authority as portable
from defensive_network_disruption.validation.r7_execution import Journal, Progress
from defensive_network_disruption.validation import r9e_publication as publication


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "session14r9e_runner", ROOT / "scripts/session_14r9e_empirical_execution.py")
RUNNER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(RUNNER)


class Session14R9ETests(unittest.TestCase):
    def test_inherited_authority_hashes(self):
        authority = RUNNER.verify_inherited()
        self.assertEqual(authority["r9_manifest_sha256"],
                         RUNNER.HISTORICAL["outputs/continuous_occlusion_empirical_retry_r9/manifest.json"])

    def test_ordinary_path_preserves_estimates(self):
        arguments = ("isotropic", (0.0, 0.0), (20.0, 0.0), ((10.0, 2.0),))
        old, _ = historical.evaluate(*arguments)
        new, evidence = repaired.evaluate(
            *arguments, root=ROOT, authority_context={"alias": "synthetic"})
        self.assertEqual(old, new)
        self.assertEqual(evidence["certificate_evidence"]["strict"]["independently_certified_count"], 0)

    def test_runtime_request_is_derived_from_exact_geometry(self):
        fixture = portable.load_fixture(ROOT)
        registered, observation, authority = certificate.load_session14ar_certificate(ROOT)
        self.assertEqual(fixture["selected_geometry_authority_hash"],
                         authority["integrand_specification"]["selected_geometry_authority_hash"])
        self.assertEqual(observation.request, certificate.IntegralRequest(
            registered.interval_identity, registered.left_endpoint_binary64,
            registered.right_endpoint_binary64, registered.field_family,
            registered.frozen_parameters, registered.combination,
            registered.integrand_specification_hash,
            registered.structural_partition_authority_hash, registered.method_id,
            registered.provenance_hash, registered.governing_tolerance))
        synthetic = {"alias": "synthetic", "origin": (0.0, 0.0),
                     "receiver": (1.0, 0.0), "defenders": ((2.0, 1.0),)}
        first = portable.selected_geometry_hash(synthetic)
        changed = {**synthetic, "receiver": (1.0 + 1e-12, 0.0)}
        self.assertNotEqual(first, portable.selected_geometry_hash(changed))

    def test_exact_warning_uses_registered_certificate(self):
        _, retained, _ = certificate.load_session14ar_certificate(ROOT)
        result = repaired._certify_observation(
            ROOT, retained.estimate, retained.warning_class,
            retained.warning_message_sha256, retained.request)
        self.assertEqual(result.status, certificate.SUCCESS_STATUS)
        self.assertEqual((result.adaptive_warning_count,
                          result.independently_certified_count,
                          result.blocking_warning_count), (1, 1, 0))

    def test_unmatched_warning_blocks(self):
        _, retained, _ = certificate.load_session14ar_certificate(ROOT)
        wrong = certificate.IntegralRequest(
            "synthetic", retained.request.left_endpoint_binary64,
            retained.request.right_endpoint_binary64, retained.request.field_family,
            retained.request.frozen_parameters, retained.request.combination,
            retained.request.integrand_specification_hash,
            retained.request.structural_partition_authority_hash,
            retained.request.method_id, retained.request.provenance_hash,
            retained.request.governing_tolerance)
        with self.assertRaises(certificate.CertificateError):
            repaired._certify_observation(
                ROOT, retained.estimate, retained.warning_class,
                retained.warning_message_sha256, wrong)

    def test_progress_derives_state_exposure_from_receipts(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as folder:
            journal = Journal(Path(folder) / "journal.jsonl")
            progress = Progress(journal); progress.authorize_access()
            progress.discover_state("0", ("0", "1"))
            progress.project("0", lambda: object())
            progress.prepare_state("0")
            progress.failure("preparation", RuntimeError("synthetic"))
            authority = publication.derive_progress(
                journal.path, expected_head=journal.previous,
                mode="empirical_failure")
            self.assertEqual(authority["exposure"]["states_opened"], 1)
            self.assertEqual(authority["exposure"]["edges_opened"], 2)
            self.assertEqual(authority["snapshot"]["counters"]["edges_completed"], 0)
            journal.close()

    def test_success_constraints_are_validator_derived(self):
        counters = {
            "states_discovered": 7227, "states_prepared": 7227,
            "states_evaluation_started": 7227, "states_completed": 7227,
            "edges_discovered": 100, "edges_opened": 100,
            "edges_evaluation_started": 100, "edges_completed": 100,
            "unresolved_exposed_edges": 0, "projection_attempts": 7227,
            "unresolved_projection_attempts": 0,
            "field_evaluations_started": 300,
            "field_evaluations_completed": 300, "state_failures": 0,
        }
        authority = {
            "snapshot": {"access_authorized": True, "status": "success",
                "active": {"state": None, "edge": None, "candidate": None},
                "failure_stage": None, "exception": None, "counters": counters,
                "field_work_by_candidate": {
                    name: {"started": 100, "completed": 100}
                    for name in ("isotropic", "expanding", "constant_width")}},
            "exposure": {"states_opened": 7227, "edges_opened": 100,
                "field_evaluations_completed": 300},
        }
        publication._validate_success(authority)
        authority["exposure"]["states_opened"] = 0
        with self.assertRaisesRegex(publication.R9EPublicationError,
                                   "success_access_counts"):
            publication._validate_success(authority)

    def test_fresh_markers_and_empirical_guard(self):
        with patch.object(RUNNER, "PROGRESS", None):
            with self.assertRaises(PermissionError):
                RUNNER.calculate_edge("isotropic", (0, 0), (1, 0),
                                      ((2, 0),), "synthetic", 0, 0)
        with tempfile.TemporaryDirectory(dir=ROOT) as folder:
            marker = Path(folder) / "journal"
            first = Journal(marker); first.close()
            with self.assertRaises(FileExistsError):
                Journal(marker)

    def test_no_prohibited_scientific_routes(self):
        source = (ROOT / "scripts/session_14r9e_empirical_execution.py").read_text()
        for phrase in ("load_model", "evaluate_options", "requests.get",
                       "target_index]", "M1 shares", "pose_loader"):
            self.assertNotIn(phrase, source)


if __name__ == "__main__":
    unittest.main()
