from __future__ import annotations

from fractions import Fraction as F
import json
from pathlib import Path
import tempfile
import unittest

from defensive_network_disruption.geometry import r9aa_terminal_authority as v2
from defensive_network_disruption.geometry import r9x_terminal_authority as v1
from defensive_network_disruption.validation import r9aa_acceptance as acceptance
from defensive_network_disruption.validation.r9aa_failure import AcquisitionFailureBoundary, CapturedFailure


class TestR9AARepair(unittest.TestCase):
    def test_schema_controls_and_compatibility_are_complete(self):
        rows, details = acceptance.schema_controls()
        self.assertEqual(len(rows), 17)
        self.assertTrue(all(row["passed"] for row in rows))
        self.assertEqual(details["legacy_relation"], "historical_v1_exact_identity")
        self.assertEqual(details["bound"]["pair_functions_bounded"], 2)
        self.assertFalse(details["bound"]["representative_substitution"])
        self.assertEqual(acceptance.compatibility_matrix()[1]["result"], "blocked_unchanged")

    def test_v2_round_trip_keeps_ordered_distinct_pair_references(self):
        first, second = acceptance.coefficient(4, 8), acceptance.coefficient(4, 9)
        record = acceptance.authority(first, second)
        loaded = v2.load_authority(json.loads(v1.canonical(record)))
        self.assertEqual(loaded.source_version, 2)
        self.assertEqual(loaded.pair[0].authority_sha256, record["pair_left_ref"])
        self.assertEqual(loaded.pair[1].authority_sha256, record["pair_right_ref"])
        self.assertNotEqual(loaded.pair[0], loaded.pair[1])
        self.assertEqual(v1.canonical(record), v1.canonical(loaded.record))

    def test_v2_rejects_invalid_authority(self):
        mutations = (
            lambda value: value["tie_authority"].update(scope="point"),
            lambda value: value["tie_authority"].pop("interval_authority_sha256"),
            lambda value: value.update(schema_version=7),
            lambda value: value.update(provenance_sha256="0" * 64),
            lambda value: value.update(competitors=[]),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                record = acceptance.authority(acceptance.coefficient(4, 8), acceptance.coefficient(4, 9))
                mutation(record)
                with self.assertRaises(ValueError):
                    v2.load_authority(record)

    def test_relation_semantics_require_identity_or_distinctness(self):
        first, second = acceptance.coefficient(4, 8), acceptance.coefficient(4, 9)
        with self.assertRaisesRegex(ValueError, "symbolic_identity_refs"):
            acceptance.authority(first, second, "symbolic_identity")
        with self.assertRaisesRegex(ValueError, "distinct_relation_refs"):
            acceptance.authority(first, first, "common_inactive_branch")

    def test_historical_v1_loader_is_unchanged_and_not_upgraded(self):
        first = acceptance.coefficient(4, 8)
        old = v1.create_authority(ordinal=1, depth=2, left=F(1, 2), right=F(1),
                                  pair=(first, first),
                                  competitors=(acceptance.coefficient(4, 16),),
                                  source=acceptance.SOURCE)
        raw = v1.canonical(old)
        loaded = v2.load_authority(json.loads(raw))
        self.assertEqual(loaded.source_version, 1)
        self.assertEqual(loaded.relation_type, "historical_v1_exact_identity")
        self.assertEqual(v1.canonical(loaded.record), raw)

    def test_bound_terminal_evaluates_two_pair_functions_and_each_competitor(self):
        first, second = acceptance.coefficient(4, 8), acceptance.coefficient(4, 9)
        record = acceptance.authority(first, second, competitors=(acceptance.coefficient(4, 16), acceptance.coefficient(4, 25)))
        calls = []
        original = v1.Coefficients.bounds

        def observe(instance, left, right):
            calls.append(instance.authority_sha256)
            return original(instance, left, right)

        v1.Coefficients.bounds = observe
        try:
            result = v2.bound_terminal(record)
        finally:
            v1.Coefficients.bounds = original
        self.assertEqual(result["pair_functions_bounded"], 2)
        self.assertEqual(result["competitor_functions_bounded"], 2)
        self.assertEqual(result["pair_competitor_comparisons"], 4)
        self.assertGreaterEqual(set(calls), {first.authority_sha256, second.authority_sha256})

    def test_failure_capture_precedes_callbacks_and_binds_traceback(self):
        folder = Path(tempfile.mkdtemp())
        boundary = AcquisitionFailureBoundary(folder)
        order = []
        try:
            raise RuntimeError("synthetic")
        except RuntimeError as error:
            result = boundary.close(
                error, "validation", timestamp="2026-09-22T00:00:00Z",
                write_blocked_qc=lambda captured: order.append(("qc", captured.traceback_sha256, boundary.controller.traceback_path.exists())),
                publish=lambda captured: order.append(("publish", captured.traceback_sha256, boundary.controller.original_path.exists())))
        self.assertEqual(result["events"], ("traceback_captured", "capture_validated", "blocked_qc", "publication"))
        self.assertEqual([row[0] for row in order], ["qc", "publish"])
        self.assertEqual(order[0][1], order[1][1])
        self.assertEqual(order[0][1], boundary.controller.validate()["traceback_sha256"])
        self.assertTrue(order[0][2] and order[1][2])

    def test_secondary_failure_is_separate_and_original_is_immutable(self):
        for failed in ("qc", "publication"):
            with self.subTest(failed=failed):
                folder = Path(tempfile.mkdtemp())
                boundary = AcquisitionFailureBoundary(folder)

                def qc(_):
                    if failed == "qc":
                        raise OSError("qc")

                def publish(_):
                    if failed == "publication":
                        raise OSError("publication")

                try:
                    raise RuntimeError("original")
                except RuntimeError as error:
                    result = boundary.close(error, failed, timestamp="2026-09-22T00:00:00Z", write_blocked_qc=qc, publish=publish)
                before = boundary.controller.original_path.read_bytes()
                self.assertEqual(result["publication_error"], "OSError")
                self.assertTrue((folder / "publication_failure.json").is_file())
                self.assertEqual(boundary.controller.original_path.read_bytes(), before)
                self.assertEqual(boundary.controller.validate()["exception_type"], "RuntimeError")

    def test_forged_capture_descriptor_is_rejected(self):
        with self.assertRaisesRegex(TypeError, "captured_failure_required"):
            CapturedFailure(Path("/tmp/fake"), "x", "E", "m", "0" * 64, object())

    def test_original_exception_is_reraised_after_capture(self):
        folder = Path(tempfile.mkdtemp())
        boundary = AcquisitionFailureBoundary(folder)
        with self.assertRaisesRegex(ValueError, "original"):
            try:
                raise ValueError("original")
            except ValueError as error:
                boundary.close(error, "reraise", timestamp="2026-09-22T00:00:00Z",
                               write_blocked_qc=lambda _: None, publish=lambda _: None,
                               reraise=True)
        self.assertEqual(boundary.controller.validate()["exception_type"], "ValueError")

    def test_runner_contains_no_empirical_route_tokens(self):
        root = Path(__file__).resolve().parents[1]
        text = (root / "scripts/session_14r9aa_terminal_cell_pair_schema_traceback_repair.py").read_text()
        for token in ("load_prepared", "evaluate_edge", "classify_terminal(", "selected_edge.json"):
            self.assertNotIn(token, text)


if __name__ == "__main__":
    unittest.main()
