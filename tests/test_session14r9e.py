"""Synthetic tests for prospective Session 14R9E wiring."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import warnings

import numpy as np
from scipy.integrate import IntegrationWarning

from defensive_network_disruption.geometry import onset_owner_certification as owner
from defensive_network_disruption.geometry.occlusion_fields import CarrierOriginField
from defensive_network_disruption.geometry import r7_representation as historical
from defensive_network_disruption.geometry import r9e_representation as repaired
from defensive_network_disruption.validation import independent_certificate_verifier as certificate
from defensive_network_disruption.validation.r7_execution import Journal, Progress
from defensive_network_disruption.validation import r9e_publication as publication


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "session14r9e_runner", ROOT / "scripts/session_14r9e_empirical_execution.py")
RUNNER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(RUNNER)


def retained_geometry():
    path = ROOT / "outputs/session14am_constant_width_comparator_diagnosis/local/000010_selected_geometry.json"
    return json.loads(path.read_text())


def retained_structure():
    record = retained_geometry()
    base = np.asarray(record["carrier"], dtype=np.float64)
    end = np.asarray(record["receiver"], dtype=np.float64)
    defenders = np.asarray(record["defenders"], dtype=np.float64)
    field = CarrierOriginField("constant_width")

    def function(t):
        return field.individual_values(
            base, defenders, base[None, :] + t[:, None] * (end - base)[None, :])

    structure = owner.canonical_geometry(
        "constant_width", base, end, defenders, function)
    return record, base, end, defenders, function, structure


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
        record, base, end, defenders, _, structure = retained_structure()
        onsets, _, partitions, switches, _ = structure
        request = repaired._runtime_request(
            ROOT, candidate="constant_width",
            context={"alias": record["alias"], "origin": base,
                     "receiver": end, "defenders": defenders},
            lower=partitions[-2], upper=partitions[-1],
            partitions=partitions, onsets=onsets, switches=switches)
        registered, _, _ = certificate.load_session14ar_certificate(ROOT)
        self.assertEqual(request.integrand_specification_hash,
                         registered.integrand_specification_hash)
        changed = dict(record); changed["receiver"] = [record["receiver"][0] + 1e-12,
                                                       record["receiver"][1]]
        with self.assertRaisesRegex(certificate.CertificateError, "selected_geometry"):
            repaired._runtime_request(
                ROOT, candidate="constant_width",
                context={"alias": changed["alias"], "origin": changed["carrier"],
                         "receiver": changed["receiver"], "defenders": changed["defenders"]},
                lower=partitions[-2], upper=partitions[-1],
                partitions=partitions, onsets=onsets, switches=switches)

    def test_exact_warning_uses_registered_certificate(self):
        record, base, end, defenders, function, structure = retained_structure()
        onsets, _, partitions, switches, _ = structure
        _, retained, _ = certificate.load_session14ar_certificate(ROOT)

        historical_message = json.loads((
            ROOT / "outputs/session14ao_onset_only_adaptive_convergence/local/000121_piece.json"
        ).read_text())["message"]

        def warned(*args, **kwargs):
            warnings.warn(historical_message, IntegrationWarning)
            return retained.estimate, 2.3e-15

        with patch.object(repaired, "quad", side_effect=warned):
            result = repaired._piece(
                function, partitions[-2], partitions[-1], 1e-13, root=ROOT,
                candidate="constant_width",
                context={"alias": record["alias"], "origin": base,
                         "receiver": end, "defenders": defenders},
                partitions=partitions, onsets=onsets, switches=switches)
        self.assertEqual(result.status, certificate.SUCCESS_STATUS)
        self.assertEqual((result.adaptive_warning_count,
                          result.independently_certified_count,
                          result.blocking_warning_count), (1, 1, 0))

    def test_unmatched_warning_blocks(self):
        historical_message = json.loads((
            ROOT / "outputs/session14ao_onset_only_adaptive_convergence/local/000121_piece.json"
        ).read_text())["message"]
        def warned(*args, **kwargs):
            warnings.warn(historical_message, IntegrationWarning)
            return 0.2, 1e-15
        with patch.object(repaired, "quad", side_effect=warned), \
             self.assertRaises(certificate.CertificateError):
            repaired._piece(
                lambda t: np.ones((len(t), 1)), 0.0, 1.0, 1e-13, root=ROOT,
                candidate="isotropic",
                context={"alias": "synthetic", "origin": (0.0, 0.0),
                         "receiver": (1.0, 0.0), "defenders": ((2.0, 0.0),)},
                partitions=(0.0, 1.0), onsets=(), switches=())

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
