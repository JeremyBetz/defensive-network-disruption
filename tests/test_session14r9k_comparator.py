"""Session 14R9K prospective structural-comparator tests."""
from __future__ import annotations

from dataclasses import replace
import importlib.util
import math
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest import mock
import warnings
import tempfile

import numpy as np

from defensive_network_disruption.geometry import micro_interval_verifier as bounded
from defensive_network_disruption.geometry import onset_owner_certification as owner
from defensive_network_disruption.geometry import production_verification as pv
from defensive_network_disruption.geometry import r9e_representation as historical
from defensive_network_disruption.geometry import r9k_comparator as repaired
from defensive_network_disruption.geometry.occlusion_fields import CarrierOriginField
from defensive_network_disruption.validation import r9k_acceptance
from defensive_network_disruption.validation import r9k_evidence

ROOT = Path(__file__).resolve().parents[1]


def authority(partitions=(0.0, 1.0)):
    payload = SimpleNamespace(tie_intervals=())
    onsets = tuple(SimpleNamespace(canonical=value) for value in partitions[1:-1])
    return repaired.structural_authority(onsets, payload, partitions, (), ())


class ComparatorTests(unittest.TestCase):
    def test_smooth_analytic_integrals(self):
        controls = (
            (lambda t: np.column_stack((np.ones_like(t),)), 1.0),
            (lambda t: np.column_stack((t,)), 0.5),
            (lambda t: np.column_stack((t * t,)), 1.0 / 3.0),
            (lambda t: np.column_stack((np.abs(t - 0.5),)), 0.25),
        )
        for function, exact in controls:
            with self.subTest(exact=exact):
                result = repaired.structural_adaptive_comparator(
                    function, authority((0.0, 0.5, 1.0)))
                self.assertLessEqual(bounded.point_interval_distance(exact, result), 1e-10)

    def test_micro_residual_uses_full_piece_count(self):
        tiny = math.nextafter(0.0, 1.0)
        result = repaired.structural_adaptive_comparator(
            lambda t: np.ones((len(t), 1)), authority((0.0, tiny, 1.0)))
        self.assertEqual((result.structural_piece_count, result.bounded_piece_count,
                          result.quadrature_piece_count), (2, 1, 1))
        self.assertLessEqual(bounded.point_interval_distance(1.0, result), 1e-10)

    def test_authority_rejects_missing_extra_and_bad_order(self):
        envelope = SimpleNamespace(tie_intervals=())
        onset = SimpleNamespace(canonical=0.25)
        with self.assertRaisesRegex(pv.GateFailure, "structural_authority_mismatch"):
            repaired.structural_authority((onset,), envelope, (0.0, 1.0), (), ())
        with self.assertRaisesRegex(pv.GateFailure, "structural_authority_mismatch"):
            repaired.structural_authority((), envelope, (0.0, 0.25, 1.0), (), ())
        with self.assertRaisesRegex(pv.GateFailure, "partition_order"):
            repaired.structural_authority((), envelope, (0.0, 0.5, 0.4, 1.0), (), ())

    def test_witness_mismatch_blocks(self):
        switch = SimpleNamespace(canonical=0.5, owners_before=(0,), owners_at=(0, 1),
                                 owners_after=(1,))
        witness = owner.OwnerWitness(0.0, 0.25, 0.5, 0.75, 1.0,
                                     (1,), (0, 1), (1,))
        with self.assertRaisesRegex(pv.GateFailure, "witness_owners"):
            repaired.structural_authority((), SimpleNamespace(tie_intervals=()),
                                          (0.0, 0.5, 1.0), (switch,), (witness,))

    def test_invalid_tie_endpoint_blocks(self):
        boundary = SimpleNamespace(outside=0.25, inside=0.5, direction="entry")
        tie = SimpleNamespace(start=boundary, end=None)
        with self.assertRaisesRegex(pv.GateFailure, "invalid_tie_endpoint"):
            repaired.structural_authority((), SimpleNamespace(tie_intervals=(tie,)),
                                          (0.0, 0.25, 0.5, 1.0), (), ())

    def test_warning_and_biased_disagreement_remain_blocking(self):
        def warning_quad(*args, **kwargs):
            warnings.warn("synthetic unrelated warning", RuntimeWarning)
            return 0.0, 0.0
        with mock.patch.object(bounded.historical, "quad", warning_quad):
            with warnings.catch_warnings():
                warnings.simplefilter("error")
                with self.assertRaises(RuntimeWarning):
                    repaired.structural_adaptive_comparator(
                        lambda t: np.zeros((len(t), 1)), authority())
        first = bounded.IntegralInterval(0.0, 0.0, 0.0, 1, 1, 0)
        second = bounded.IntegralInterval(1e-9, 1e-9, 0.0, 1, 1, 0)
        self.assertGreater(bounded.interval_distance(first, second), 1e-10)

    def test_comparator_does_not_use_certificate_piece_route(self):
        with mock.patch.object(historical, "_integrate", side_effect=AssertionError("strict route")):
            result = repaired.structural_adaptive_comparator(
                lambda t: np.column_stack((t, 1.0 - t)), authority((0.0, 0.5, 1.0)))
        self.assertLessEqual(bounded.point_interval_distance(0.75, result), 1e-10)

    def test_real_switch_authority_and_mutation(self):
        base = np.array((0.0, 0.0)); end = np.array((20.0, 0.0))
        defenders = np.array(((8.0, 2.0), (12.0, -2.0)))
        field = CarrierOriginField("constant_width")
        function = lambda t: field.individual_values(
            base, defenders, base[None, :] + t[:, None] * (end - base)[None, :])
        structure = owner.canonical_geometry("constant_width", base, end, defenders, function)
        auth = repaired.structural_authority(structure[0], structure[1], structure[2],
                                             structure[3], structure[4])
        self.assertEqual(auth.partitions, structure[2])
        if auth.switch_coordinates:
            altered = list(auth.partitions); altered.remove(auth.switch_coordinates[0])
            with self.assertRaises(pv.GateFailure):
                repaired.structural_authority(structure[0], structure[1], tuple(altered),
                                              structure[3], structure[4])

    def test_production_and_piecewise_preserved_on_candidates(self):
        geometry = ((0.0, 0.0), (20.0, 0.0), ((8.0, 2.0), (12.0, -2.0)))
        for candidate in ("isotropic", "expanding", "constant_width"):
            with self.subTest(candidate=candidate):
                old_edge, old = historical.evaluate(candidate, *geometry, root=ROOT,
                    authority_context={"alias": "synthetic_r9k"})
                new_edge, new = repaired.evaluate(candidate, *geometry, root=ROOT,
                    authority_context={"alias": "synthetic_r9k"})
                self.assertEqual(old_edge, new_edge)
                self.assertEqual(old["estimates"], new["estimates"])
                self.assertEqual(old["intervals"], new["intervals"])
                self.assertEqual(old["partitions"], new["partitions"])
                self.assertEqual(old["maximum_interval"], new["maximum_interval"])
                self.assertEqual(old["certificate_evidence"]["strict"],
                                 new["certificate_evidence"]["strict"])
                self.assertEqual(old["certificate_evidence"]["repeat"],
                                 new["certificate_evidence"]["repeat"])

    def test_complete_historical_authority(self):
        spec = importlib.util.spec_from_file_location(
            "r9k_cases", ROOT / "scripts/session_14v_micro_interval_verifier.py")
        cases = importlib.util.module_from_spec(spec); spec.loader.exec_module(cases)
        count = components = permutations = 0
        for label, case in cases.authority_cases():
            _, result = repaired.evaluate(
                case["candidate"], case["origin"], case["receiver"], case["defenders"],
                root=ROOT, authority_context={"alias": "synthetic_r9k"}, synthetic=True,
                historical_failure=case["historical_failure"])
            expected = case["historical_vector"]
            self.assertEqual(result["intervals"], expected["intervals"], label)
            self.assertEqual(tuple(result["estimates"]), tuple(expected["estimates"]), label)
            for name, value in result["estimates"].items():
                old = expected["estimates"][name]
                tolerance = 64 * np.finfo(float).eps * max(1.0, abs(value), abs(old))
                self.assertLessEqual(abs(value - old), tolerance, (label, name))
            count += 1; components += len(result["estimates"])
            permutations += result["permutations"]
        self.assertEqual((count, components, permutations), (108, 366, 399))

    def test_frozen_synthetic_and_negative_families(self):
        positive = r9k_acceptance.synthetic_controls()
        negative = r9k_acceptance.negative_controls()
        self.assertEqual(len(positive), 9)
        self.assertTrue(all(row["status"] == "passed" for row in positive), positive)
        self.assertEqual(len(negative), 11)
        self.assertTrue(all(row["blocked"] for row in negative), negative)

    def test_evidence_complete_and_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp).resolve(); local = folder / "local"
            r9k_evidence.put(local / "access_attempt.json", {"synthetic": True})
            r9k_evidence.put(local / "access_materialized.json", {"synthetic": True})
            public = r9k_evidence.empty_public()
            r9k_evidence.record(public, "repair_contract.json", flags=dict.fromkeys(
                r9k_evidence.JSON_SCHEMAS["repair_contract.json"]["flags"], True),
                counts={"agreement_tolerance_power": 10, "synthetic_families": 12})
            r9k_evidence.record(public, "retained_edge_replay.json", flags=dict.fromkeys(
                r9k_evidence.JSON_SCHEMAS["retained_edge_replay.json"]["flags"], True),
                counts={"states_reopened": 1, "edges_reopened": 1, "candidates_run": 3}, timings={"seconds": 1.})
            r9k_evidence.record(public, "performance.json", flags=dict.fromkeys(
                r9k_evidence.JSON_SCHEMAS["performance.json"]["flags"], True),
                counts={"fixtures": 1, "structural_pieces": 2, "adaptive_calls": 2, "micro_pieces": 0},
                timings={"historical_seconds": 1., "repaired_seconds": 1., "overhead_ratio": 1.})
            r9k_evidence.record(public, "publication_validation.json", flags=dict.fromkeys(
                r9k_evidence.JSON_SCHEMAS["publication_validation.json"]["flags"], True),
                counts={"records": 1, "states_opened": 1, "edges_opened": 1, "states_completed": 0,
                        "edges_completed": 0, "field_started": 0, "field_completed": 0, "unresolved_edges": 1},
                timings={"seconds": 1.})
            rows = {
                "synthetic_acceptance.csv": [{"fixture":"x","candidate":"synthetic","family":"smooth","status":"passed",
                    "reference_kind":"analytic","within_gate":True,"production_preserved":True,"piecewise_preserved":True,
                    "boundaries_exact":True,"components":1,"permutations":0,"reason":"control"}],
                "negative_controls.csv": [{"fixture":"x","expected_failure":"x","blocked":True,"reason":"control"}],
                "candidate_regression.csv": [{"candidate":"isotropic","status":"passed","accepted_resolution":256,
                    "production_preserved":True,"piecewise_preserved":True,"comparator_passed":True,
                    "certificate_count":0,"warning_count":0,"reason":"control"}],
            }
            qc={"status":"complete","execution_valid":True,"classification":"A","readiness":1,
                "states_reopened":1,"edges_reopened":1,"exposure_uncertain":False}
            self.assertEqual(r9k_evidence.close(folder,public,rows,qc,{})["artifacts"],9)
            (folder / "performance.json").write_text("{}\n")
            with self.assertRaises(ValueError): r9k_evidence.publication_check(folder)

    def test_entry_marker_and_emergency(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "r9k_runner", ROOT / "scripts/session_14r9k_onset_only_comparator_repair.py")
        runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp).resolve()
            with self.assertRaisesRegex(RuntimeError, "synthetic"):
                runner.entry(folder, lambda _: (_ for _ in ()).throw(RuntimeError("synthetic")))
            self.assertTrue((folder / "local/outer_emergency.json").exists())
            with self.assertRaises(FileExistsError): runner.entry(folder, lambda _: None)


if __name__ == "__main__":
    unittest.main()
