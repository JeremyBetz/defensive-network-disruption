import csv
import io
import importlib
import math
from pathlib import Path
import tempfile
import unittest

from defensive_network_disruption.validation import terminal_error_publication_validator as validator
from defensive_network_disruption.validation import terminal_error_revalidation as reviewer


def piece(tolerance, value=0.1, error=1e-16, warning=False, *, left=0.0, right=1.0):
    trace = [[(left + right) / 2, value]]
    message = "The occurrence of roundoff error is detected, which prevents the requested tolerance from being achieved. The error may be underestimated."
    return {
        "a": left, "b": right, "callback_count": 1,
        "trace_sha256": reviewer.digest(trace), "trace": trace,
        "warnings": [{"category": "IntegrationWarning", "message": message}] if warning else [],
        "exception": None, "message": message if warning else None,
        "normal": not warning, "exhausted": False, "estimate": value,
        "reported_error": error, "neval": 1, "last": 1,
        "alist": [left], "blist": [right], "rlist": [value], "elist": [error],
        "tolerance": tolerance, "limit": 1000, "seconds": 0.001,
    }


def records():
    levels, pieces = [], []
    for index, tolerance in enumerate(reviewer.TOLERANCES):
        warning = index == 5
        rows = [piece(tolerance, value=0.1 / 9, error=1e-16 / 9,
                      warning=warning and j == 8, left=j / 9, right=(j + 1) / 9)
                for j in range(9)]
        pieces.append(rows)
        levels.append({
            "tolerance": tolerance, "complete": not warning, "normal": not warning,
            "warnings": warning, "exhausted": False, "neval": 9,
            "terminal_panels": 9, "subdivisions": 0,
            "onset_adjacent_panels": 9, "onset_error_fraction": 1.0,
            "estimate": None if warning else math.fsum(row["estimate"] for row in rows),
            "reported_error": math.fsum(row["reported_error"] for row in rows),
            "reported_bounds_met": not warning, "seconds": 0.01,
            "trace_sha256": reviewer.digest([row["trace_sha256"] for row in rows]),
            "pieces_attempted": 9, "pieces_required": 9,
        })
    return levels, pieces


class Session14aqTests(unittest.TestCase):
    def test_per_level_tolerance_is_explicit(self):
        levels, pieces = records()
        review = reviewer.review_records(
            {"anchor": 0.1, "bounds": [0.1, 0.1], "reference": 0.2},
            {"partitions": [i / 9 for i in range(10)]}, levels, pieces,
            [f"hash-{i}" for i in range(6)],
        )
        self.assertEqual([row["tolerance"] for row in review["level_rows"]], list(reviewer.TOLERANCES))

    def test_missing_retained_tolerance_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing_retained_tolerance"):
            reviewer.reviewed_level_row({}, {"tolerance": 2e-15})

    def test_independent_expected_rows(self):
        levels, pieces = records()
        rows = validator.expected_level_rows(levels, pieces, [f"hash-{i}" for i in range(6)])
        self.assertEqual([row["tolerance"] for row in rows], [str(x) for x in reviewer.TOLERANCES])
        self.assertEqual(rows[5]["status"], "warning_partial")

    def test_historical_stale_variable_rejected_with_rows(self):
        levels, pieces = records()
        expected = validator.expected_level_rows(levels, pieces, [f"hash-{i}" for i in range(6)])
        stale = [dict(row, tolerance="2e-15") for row in expected]
        failures = validator.compare_level_rows(stale, expected)
        self.assertEqual(sorted({item["row"] for item in failures}), [0, 1, 2, 3, 4])

    def test_corruptions_are_detected(self):
        levels, pieces = records()
        expected = validator.expected_level_rows(levels, pieces, [f"hash-{i}" for i in range(6)])
        cases = []
        swapped = [dict(row) for row in expected]
        swapped[0]["tolerance"], swapped[1]["tolerance"] = swapped[1]["tolerance"], swapped[0]["tolerance"]
        cases.append(swapped)
        cases.append(expected[:-1])
        shifted = [dict(row, level=str(index + 1)) for index, row in enumerate(expected)]
        cases.append(shifted)
        warning = [dict(row) for row in expected]
        warning[4]["warning"] = "True"
        cases.append(warning)
        estimate = [dict(row) for row in expected]
        estimate[1]["estimate_equal_previous"] = "False"
        cases.append(estimate)
        error = [dict(row) for row in expected]
        error[1]["error_behavior"] = "shrink"
        cases.append(error)
        unavailable = [dict(row) for row in expected]
        unavailable[0]["estimate_equal_previous"] = "unavailable"
        cases.append(unavailable)
        for rows in cases:
            self.assertTrue(validator.compare_level_rows(rows, expected))

    def test_level_csv_rejects_reordered_schema(self):
        data = b"tolerance,level\n1e-13,0\n"
        with self.assertRaisesRegex(ValueError, "level_fields"):
            validator.parse_level_csv(data)

    def test_modules_do_not_import_numerical_or_geometry_routes(self):
        for module in (reviewer, validator):
            source = Path(module.__file__).read_text()
            self.assertNotIn("import numpy", source)
            self.assertNotIn("import scipy", source)
            self.assertNotIn("geometry", source)
            self.assertNotIn("quad(", source)

    def test_deterministic_csv(self):
        levels, pieces = records()
        rows = validator.expected_level_rows(levels, pieces, [f"hash-{i}" for i in range(6)])
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=validator.LEVEL_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        self.assertEqual(stream.getvalue().encode(), stream.getvalue().encode())


if __name__ == "__main__":
    unittest.main()
