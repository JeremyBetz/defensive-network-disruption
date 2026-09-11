"""Discoverable synthetic tests for Session 14h diagnostic preservation."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from defensive_network_disruption.geometry import failure_diagnostics as diagnostics

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "session14h_tests", ROOT / "scripts/session_14h_failure_localization.py"
)
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class DiagnosticTests(unittest.TestCase):
    def test_fixture_order_is_exact_session14g_order(self):
        self.assertEqual(
            tuple(diagnostics.production.engineering_functions()), diagnostics.FIXTURE_ORDER
        )

    def test_success_preserves_every_completed_row(self):
        persisted = []
        with patch.object(diagnostics, "mapped_signature", return_value=("stable",)):
            rows, failure = diagnostics.run_engineering_diagnostic(persisted.append)
        self.assertIsNone(failure)
        self.assertEqual(rows, persisted)
        self.assertEqual(tuple(row["fixture"] for row in rows), diagnostics.FIXTURE_ORDER)

    def test_typeerror_preserves_active_fixture_stage_and_traceback(self):
        original = diagnostics.find_verified_envelope
        calls = 0

        def injected(function, *args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise TypeError("injected container mismatch")
            return original(function, *args, **kwargs)

        persisted = []
        with patch.object(diagnostics, "find_verified_envelope", side_effect=injected):
            rows, failure = diagnostics.run_engineering_diagnostic(persisted.append)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows, persisted)
        self.assertEqual(failure.exception_class, "TypeError")
        self.assertEqual(failure.exception_message, "injected container mismatch")
        self.assertEqual(failure.active["fixture"], "crossing")
        self.assertEqual(failure.active["stage"], "switch_detection")
        self.assertEqual(failure.active["completed_checks"], 1)
        self.assertIn("injected container mismatch", failure.full_traceback)

    def test_combined_enclosure_partition_failure_is_identified(self):
        persisted = []
        with patch.object(
            diagnostics.production,
            "certified_partitions",
            side_effect=TypeError("partition record mismatch"),
        ):
            rows, failure = diagnostics.run_engineering_diagnostic(persisted.append)
        self.assertEqual(rows, [])
        self.assertEqual(failure.active["stage"], "enclosure_validation")
        self.assertEqual(failure.active["substage"], "certified_partitions_combined")
        self.assertEqual(failure.active["function"], "certified_partitions")
        self.assertEqual(failure.active["input_summary"]["python_type"], "VerifiedEnvelope")

    def test_signature_failure_records_container_summary(self):
        with patch.object(
            diagnostics, "mapped_signature", side_effect=TypeError("signature shape")
        ):
            _, failure = diagnostics.run_engineering_diagnostic(lambda _: None)
        self.assertEqual(failure.active["stage"], "signature_construction")
        self.assertEqual(failure.active["function"], "mapped_signature")
        self.assertEqual(failure.active["input_summary"]["python_type"], "VerifiedEnvelope")

    def test_permutation_detection_failure_keeps_completed_count(self):
        original = diagnostics.find_verified_envelope
        calls = 0

        def injected(function, *args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 3:
                raise RuntimeError("permutation detector")
            return original(function, *args, **kwargs)

        with patch.object(diagnostics, "find_verified_envelope", side_effect=injected):
            rows, failure = diagnostics.run_engineering_diagnostic(lambda _: None)
        self.assertEqual(len(rows), 1)
        self.assertEqual(failure.active["fixture"], "crossing")
        self.assertEqual(failure.active["stage"], "permutation_switch_detection")

    def test_progress_persistence_failure_does_not_claim_completion(self):
        with patch(
            "defensive_network_disruption.geometry.failure_diagnostics.production.engineering_functions",
            wraps=diagnostics.production.engineering_functions,
        ):
            rows, failure = diagnostics.run_engineering_diagnostic(
                lambda _: (_ for _ in ()).throw(OSError("append failed"))
            )
        self.assertEqual(rows, [])
        self.assertEqual(failure.active["stage"], "progress_persistence")
        self.assertEqual(failure.active["completed_checks"], 0)

    def test_field_evaluation_input_summary_is_bounded(self):
        def bad_function(_):
            raise TypeError("field evaluation")

        functions = diagnostics.production.engineering_functions()
        functions["constant"] = bad_function
        with patch.object(diagnostics.production, "engineering_functions", return_value=functions):
            _, failure = diagnostics.run_engineering_diagnostic(lambda _: None)
        self.assertEqual(failure.active["stage"], "field_evaluation")
        self.assertEqual(failure.active["fixture"], "constant")
        self.assertEqual(failure.active["input_summary"]["python_type"], "ndarray")
        self.assertIn("shape", failure.active["input_summary"])
        self.assertNotIn("values", failure.active["input_summary"])

    def test_traceback_sanitization_removes_private_prefix(self):
        try:
            raise TypeError("synthetic failure")
        except TypeError as error:
            failure = diagnostics.capture_failure(
                error, diagnostics.ActiveDiagnostic(fixture="constant"), []
            )
        text, frames = diagnostics.sanitize_traceback(failure.full_traceback, ROOT)
        self.assertNotIn(str(ROOT), text)
        self.assertIn("<REPOSITORY>", text)
        self.assertTrue(frames)
        self.assertTrue(any(frame["function"].startswith("test_") for frame in frames))

    def test_sanitized_records_are_deterministic(self):
        source = 'Traceback\n  File "' + str(ROOT / "example.py") + '", line 7, in work\nTypeError: x\n'
        first = diagnostics.sanitize_traceback(source, ROOT)
        second = diagnostics.sanitize_traceback(source, ROOT)
        self.assertEqual(first, second)
        self.assertEqual(first[1], [{"file": "<REPOSITORY>/example.py", "line": 7, "function": "work"}])

    def test_cause_classification_uses_active_operation(self):
        active = diagnostics.ActiveDiagnostic(
            fixture="rounded_plateau",
            stage="signature_construction",
            function="mapped_signature",
        )
        failure = diagnostics.DiagnosticFailure("TypeError", "x", "", active.__dict__, ())
        defect, expected, location = runner.classify_cause(
            failure, {"file": "<REPOSITORY>/x.py", "line": 4, "function": "mapped_signature"}
        )
        self.assertTrue(defect.startswith("B"))
        self.assertIn("order-comparable", expected)
        self.assertEqual(location, "<REPOSITORY>/x.py:4 in mapped_signature")

    def test_partial_progress_append_is_durable(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(
            runner, "ROOT", Path(directory).resolve()
        ):
            runner.append_progress(
                1,
                {
                    "fixture": "constant",
                    "passed": True,
                    "reason": None,
                    "permutations_checked": 1,
                    "partition_count": 2,
                },
            )
            path = runner.safe(runner.OUT / "local/engineering_progress.jsonl")
            self.assertEqual(len(path.read_text().splitlines()), 1)

    def test_exclusive_marker_rejects_second_execution(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(
            runner, "ROOT", Path(directory).resolve()
        ), patch.object(runner, "git", return_value="synthetic"), patch.object(
            runner, "ledger"
        ):
            runner.begin()
            with self.assertRaises(FileExistsError):
                runner.begin()

    def test_localized_failure_package_validates_and_cannot_rerun(self):
        row = {
            "fixture": "constant",
            "passed": True,
            "reason": None,
            "permutations_checked": 1,
            "partition_count": 2,
            "boundary_enclosures": [],
            "different_sections": [],
        }
        active = diagnostics.ActiveDiagnostic(
            check_index=2,
            fixture="crossing",
            stage="signature_construction",
            substage="baseline_signature",
            function="mapped_signature",
            input_summary={"python_type": "VerifiedEnvelope", "is_scalar": False},
            completed_checks=1,
        )
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory).resolve()
            failure = diagnostics.DiagnosticFailure(
                "TypeError",
                "tuple and NoneType",
                "Traceback (most recent call last):\n"
                f'  File "{temporary_root}/src/example.py", line 9, in mapped_signature\n'
                "TypeError: tuple and NoneType\n",
                active.__dict__,
                (row,),
            )

            def synthetic_run(persist):
                persist(row)
                return [row], failure

            original_environment = runner.environment()
            with patch.object(runner, "ROOT", temporary_root), patch.object(
                runner, "preflight"
            ), patch.object(runner, "git", return_value="synthetic_commit"), patch.object(
                runner, "environment", return_value=original_environment
            ), patch.object(
                runner, "run_engineering_diagnostic", side_effect=synthetic_run
            ):
                real_digest = runner.digest

                def synthetic_digest(path):
                    if str(path).startswith(str(runner.OUT) + "/"):
                        return real_digest(path)
                    return "0" * 64

                with patch.object(runner, "digest", side_effect=synthetic_digest):
                    self.assertEqual(runner.reproduce(), 0)
                    self.assertEqual(runner.validate(), runner.LOCALIZED)
                    self.assertTrue(
                        runner.safe(runner.OUT / "local/failure_full.json").exists()
                    )
                    summary = runner.read_json(runner.OUT / "failure_summary.json")
                    self.assertEqual(summary["completed_checks"], 1)
                    self.assertNotIn(str(temporary_root), summary["sanitized_traceback"])
                    with self.assertRaises(FileExistsError):
                        runner.reproduce()

    def test_route_guard_and_commands_exclude_empirical_work(self):
        runner.route_guard()
        source = (ROOT / runner.CODE[0]).read_text()
        self.assertIn('"preflight", "reproduce", "publication-check"', source)
        for route in ("analyze", "score", "acquire", "fit", "prepare-reserved"):
            self.assertNotIn(f'choices=("{route}"', source)


if __name__ == "__main__":
    unittest.main()
