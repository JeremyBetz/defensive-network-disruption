from __future__ import annotations

import ast
import csv
import io
import math
from pathlib import Path
import tempfile
import unittest

from defensive_network_disruption.validation import terminal_error_review as r


WARNING = ("The occurrence of roundoff error is detected, which prevents \n"
           "  the requested tolerance from being achieved.  The error may be \n"
           "  underestimated.")


def piece(left, right, tolerance, value=0.1, error=1e-16, *, warning=False,
          node=None):
    point = (left + right) / 2 if node is None else node
    trace = [[point, value]]
    warnings = [{"category": "IntegrationWarning", "message": WARNING}] if warning else []
    return {
        "a": left, "b": right, "callback_count": 1,
        "trace_sha256": r.digest(trace), "trace": trace, "warnings": warnings,
        "exception": None, "message": WARNING if warning else None,
        "normal": not warning, "exhausted": False, "estimate": value,
        "reported_error": error, "neval": 1, "last": 1,
        "alist": [left], "blist": [right], "rlist": [value], "elist": [error],
        "tolerance": tolerance, "limit": 1000, "seconds": 0.001,
    }


def fixtures(*, errors=None, warning_value=0.1):
    partitions = [i / 9 for i in range(10)]
    levels = []
    pieces_by_level = []
    hashes = []
    if errors is None:
        errors = [1e-16] * 6
    for level_index, tolerance in enumerate(r.TOLERANCES):
        pieces = [piece(partitions[i], partitions[i + 1], tolerance,
                        value=warning_value if level_index == 5 else 0.1,
                        error=errors[level_index],
                        warning=level_index == 5 and i == 8)
                  for i in range(9)]
        complete = level_index < 5
        estimate = math.fsum(item["estimate"] for item in pieces) if complete else None
        error = math.fsum(item["reported_error"] for item in pieces)
        level = {
            "tolerance": tolerance, "complete": complete, "normal": complete,
            "warnings": not complete, "exhausted": False, "neval": 9,
            "terminal_panels": 9, "subdivisions": 0,
            "onset_adjacent_panels": 9, "onset_error_fraction": 1.0,
            "estimate": estimate, "reported_error": error,
            "reported_bounds_met": complete,
            "seconds": 0.01,
            "trace_sha256": r.digest([item["trace_sha256"] for item in pieces]),
            "pieces_attempted": 9, "pieces_required": 9,
        }
        levels.append(level)
        pieces_by_level.append(pieces)
        hashes.append(r.digest(level))
    reference = {"anchor": 0.9, "bounds": [0.9, 0.9], "reference": 0.9}
    return reference, {"partitions": partitions}, levels, pieces_by_level, hashes


class TerminalErrorReviewTests(unittest.TestCase):
    def reviewed(self, **kwargs):
        return r.review_records(*fixtures(**kwargs))

    def write_package(self, folder):
        public = r.public_package(self.reviewed(), True, "0" * 64)
        private = folder / "local/private_index.json"
        r.atomic(private, {"schema_version": 1, "files": {}})
        for name in r.PUBLIC_FILES[:-1]:
            r.atomic(folder / name, public[name], raw=name.endswith(".csv"))
        qc = {"schema_version": 1, "status": "closed", "execution_valid": True,
              "classification": public["classification"], "readiness": public["readiness"],
              "retained_records": 68, "new_numerical_evaluations": 0,
              "empirical_records_opened": 0, "exact_values_public": False,
              "private_index_sha256": r.sha(private)}
        r.atomic(folder / "qc.json", qc)
        r.atomic(folder / "manifest.json", {
            "schema_version": 1, "status": "closed",
            "outputs": {name: r.sha(folder / name) for name in r.PUBLIC_FILES},
            "authority": {}, "private_index_sha256": r.sha(private)})
        expected = {name: public[name] for name in r.PUBLIC_FILES[:-1]}
        expected["qc.json"] = qc
        return public, expected

    def test_selected_record_count_and_names(self):
        names = r.selected_names()
        self.assertEqual(len(names), 68)
        self.assertEqual(sum(name.endswith("_piece.json") for name in names), 54)
        self.assertNotIn("000002_selected_geometry.json", names)
        self.assertFalse(any(name.endswith("_piece_started.json") for name in names))

    def test_complete_prefix_and_warning_sum(self):
        result = self.reviewed()
        self.assertEqual([row["status"] for row in result["level_rows"]],
                         ["complete"] * 5 + ["warning_partial"])
        self.assertEqual(result["level_rows"][5]["aggregate_kind"],
                         "reviewer_derived_piece_return_sum")
        self.assertTrue(result["facts"]["warning_level_sum_available"])

    def test_identical_trace_all_layers(self):
        result = self.reviewed()
        for row in result["level_rows"][1:]:
            self.assertIs(row["trace_nodes_equal_previous"], True)
            self.assertIs(row["trace_values_equal_previous"], True)
            self.assertIs(row["piece_hashes_equal_previous"], True)
            self.assertIs(row["terminal_arrays_equal_previous"], True)

    def test_changed_node_detected(self):
        data = list(fixtures())
        data[3][2][0]["trace"] = [[0.222, 0.1]]
        data[3][2][0]["trace_sha256"] = r.digest(data[3][2][0]["trace"])
        data[2][2]["trace_sha256"] = r.digest([p["trace_sha256"] for p in data[3][2]])
        result = r.review_records(*data)
        self.assertFalse(result["level_rows"][2]["trace_nodes_equal_previous"])

    def test_changed_value_detected(self):
        data = list(fixtures())
        target = data[3][3][1]
        target["estimate"] = target["rlist"][0] = target["trace"][0][1] = 0.1001
        target["trace_sha256"] = r.digest(target["trace"])
        data[2][3]["estimate"] = math.fsum(p["estimate"] for p in data[3][3])
        data[2][3]["trace_sha256"] = r.digest([p["trace_sha256"] for p in data[3][3]])
        result = r.review_records(*data)
        self.assertFalse(result["level_rows"][3]["trace_values_equal_previous"])

    def test_hash_only_trace_mismatch_rejected(self):
        data = list(fixtures())
        data[3][1][0]["trace"][0][0] = 0.2
        with self.assertRaisesRegex(ValueError, "trace_hash"):
            r.review_records(*data)

    def test_changed_terminal_topology_detected(self):
        data = list(fixtures())
        target = data[3][1][0]
        middle = (target["a"] + target["b"]) / 2
        target.update(last=2, alist=[target["a"], middle],
                      blist=[middle, target["b"]], rlist=[0.05, 0.05],
                      elist=[0.0, 1e-16])
        data[2][1]["terminal_panels"] = 10
        data[2][1]["subdivisions"] = 1
        result = r.review_records(*data)
        self.assertFalse(result["level_rows"][1]["terminal_arrays_equal_previous"])

    def test_terminal_gap_rejected(self):
        data = list(fixtures())
        target = data[3][0][0]
        target.update(last=2, alist=[target["a"], 0.07],
                      blist=[0.05, target["b"]], rlist=[0.05, 0.05],
                      elist=[5e-17, 5e-17])
        with self.assertRaisesRegex(ValueError, "terminal_coverage"):
            r.review_records(*data)

    def test_missing_warning_estimate_rejected(self):
        data = list(fixtures())
        data[3][5][-1]["estimate"] = None
        with self.assertRaisesRegex(ValueError, "terminal_value"):
            r.review_records(*data)

    def test_malformed_initialized_array_rejected(self):
        data = list(fixtures())
        data[3][0][0]["elist"] = []
        with self.assertRaisesRegex(ValueError, "initialized_array_length"):
            r.review_records(*data)

    def test_nonfinite_rejected(self):
        data = list(fixtures())
        data[3][0][0]["elist"] = [float("inf")]
        with self.assertRaisesRegex(ValueError, "terminal_nonfinite"):
            r.review_records(*data)

    def test_plateauing_error(self):
        result = self.reviewed(errors=[1e-12] * 6)
        self.assertEqual([row["error_behavior"] for row in result["level_rows"]],
                         ["anchor"] + ["plateau"] * 5)

    def test_shrinking_error(self):
        result = self.reviewed(errors=[1e-9, 5e-10, 2e-10, 1e-10, 5e-11, 2e-11])
        self.assertTrue(all(row["error_behavior"] == "shrink"
                            for row in result["level_rows"][1:]))

    def test_inflating_error(self):
        result = self.reviewed(errors=[1e-12, 2e-12, 3e-12, 4e-12, 5e-12, 6e-12])
        self.assertTrue(all(row["error_behavior"] == "inflate"
                            for row in result["level_rows"][1:]))

    def test_error_ranking_and_shares(self):
        data = list(fixtures())
        data[3][0][0]["reported_error"] = data[3][0][0]["elist"][0] = 8e-16
        data[2][0]["reported_error"] = math.fsum(p["reported_error"] for p in data[3][0])
        result = r.review_records(*data)
        row = result["error_rows"][0]
        self.assertEqual(row["dominant_interval_ordinal"], 0)
        self.assertGreater(float(row["top1_error_share"]), 0.4)

    def test_widths_private_in_public_package(self):
        result = self.reviewed()
        public = r.public_package(result, True, "0" * 64)
        text = r.canonical(public["terminal_subdivision_summary.json"]).decode()
        self.assertNotIn('"minimum"', text)
        self.assertNotIn('"maximum"', text)
        self.assertIn("private/hash-bound", text)

    def test_warning_source_mismatch_prevents_specific_c(self):
        result = self.reviewed(errors=[1e-16] * 6)
        result["facts"]["reference_within"] = True
        result["facts"]["terminal_error_above_request"] = False
        public = r.public_package(result, False, "0" * 64)
        self.assertNotEqual(public["classification"], "C")

    def test_classification_g_integrity(self):
        self.assertEqual(r.classify({}, integrity_valid=False),
                         ("G", 4, "evidence_integrity_failure"))

    def test_classification_e_multiple_independent(self):
        facts = self.reviewed()["facts"]
        facts["drift"] = True
        self.assertEqual(r.classify(facts)[0], "E")

    def test_classification_d_drift(self):
        facts = self.reviewed()["facts"]
        facts.update(drift=True, roundoff_reported=False)
        self.assertEqual(r.classify(facts)[0], "D")

    def test_classification_c_roundoff(self):
        self.assertEqual(r.classify(self.reviewed()["facts"])[0], "C")

    def test_classification_b_stable_unsatisfied(self):
        facts = self.reviewed()["facts"]
        facts.update(roundoff_reported=False, reference_within=False)
        self.assertEqual(r.classify(facts)[0], "B")

    def test_classification_a_requires_accuracy(self):
        facts = self.reviewed()["facts"]
        facts.update(roundoff_reported=False, terminal_error_above_request=False,
                     reference_within=True)
        self.assertEqual(r.classify(facts),
                         ("A", 1, "stable_and_independently_within_existing_gate"))

    def test_classification_f_unavailable(self):
        facts = self.reviewed()["facts"]
        facts.update(stable=False, drift=False, roundoff_reported=False,
                     terminal_error_above_request=False, reference_within=False)
        self.assertEqual(r.classify(facts)[0], "F")

    def test_missing_evidence_fixed_precedence(self):
        facts = self.reviewed()["facts"]
        self.assertEqual(r.missing_item(facts)["item"],
                         "independently_bounded_warning_interval_reference")
        facts["warning_level_sum_available"] = False
        self.assertEqual(r.missing_item(facts)["item"],
                         "warning_level_returned_component")

    def test_atomic_create_once_and_marker_collision(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "attempt.marker"
            r.atomic(path, {"session": "14ap"})
            with self.assertRaises(FileExistsError):
                r.atomic(path, {"session": "14ap"})

    def test_csv_has_lf_and_frozen_schema(self):
        public = r.public_package(self.reviewed(), True, "0" * 64)
        data = public["level_summary.csv"]
        self.assertNotIn(b"\r", data)
        reader = csv.DictReader(io.StringIO(data.decode()))
        self.assertEqual(tuple(reader.fieldnames), r.LEVEL_FIELDS)
        self.assertEqual(len(list(reader)), 6)

    def test_public_package_contains_no_exact_values(self):
        public = r.public_package(self.reviewed(), True, "0" * 64)
        for name in r.PUBLIC_FILES[:-1]:
            value = public[name]
            data = value if isinstance(value, bytes) else r.canonical(value)
            self.assertNotIn(b'"estimate":', data)
            self.assertNotIn(b'"reported_error":', data)
            self.assertNotIn(b'"widths":', data)

    def test_valid_persisted_package(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            _, expected = self.write_package(folder)
            self.assertTrue(r.validate_public(folder, expected))

    def test_missing_persisted_output_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            _, expected = self.write_package(folder)
            (folder / "warning_semantics.json").unlink()
            with self.assertRaises(FileNotFoundError):
                r.validate_public(folder, expected)

    def test_changed_persisted_hash_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            _, expected = self.write_package(folder)
            (folder / "level_summary.csv").write_bytes(b"changed\n")
            with self.assertRaisesRegex(ValueError, "output_hash"):
                r.validate_public(folder, expected)

    def test_false_classification_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            _, expected = self.write_package(folder)
            forged = {**expected["qc.json"], "classification": "A"}
            (folder / "qc.json").write_bytes(r.canonical(forged))
            manifest = r.strict_load(folder / "manifest.json")
            manifest["outputs"]["qc.json"] = r.sha(folder / "qc.json")
            (folder / "manifest.json").write_bytes(r.canonical(manifest))
            with self.assertRaisesRegex(ValueError, "classification"):
                r.validate_public(folder, expected)

    def test_runner_has_no_numerical_or_geometry_route(self):
        root = Path(__file__).resolve().parents[1]
        path = root / "scripts/session_14ap_terminal_error_evidence_review.py"
        tree = ast.parse(path.read_text())
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        self.assertFalse(any(name.startswith(("numpy", "scipy.integrate",
                                              "defensive_network_disruption.geometry"))
                             for name in imports))
        text = path.read_text()
        self.assertNotIn("quad(", text)
        self.assertNotIn("individual_values", text)
        self.assertIn('local / "failure.json"', text)


if __name__ == "__main__":
    unittest.main()
