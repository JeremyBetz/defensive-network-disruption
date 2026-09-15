"""Independent Session 14aq publication validation.

This module deliberately does not import the Session 14aq reviewer or call any
public-row construction helper.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

LEVEL_FIELDS = (
    "level", "tolerance", "status", "estimate_available", "aggregate_kind",
    "estimate_equal_previous", "estimate_delta_within_gate", "error_available",
    "error_equal_previous", "error_behavior", "reported_bounds_met", "neval",
    "terminal_intervals", "subdivision_operations", "warning", "termination",
    "trace_nodes_equal_previous", "trace_values_equal_previous",
    "piece_hashes_equal_previous", "terminal_arrays_equal_previous",
    "trace_hash", "evidence_sha256",
)
TOLERANCES = (1e-13, 5e-14, 2e-14, 1e-14, 5e-15, 2e-15)
GATE = 1e-10


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True, allow_nan=False) + "\n").encode()


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1_048_576), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _strict_load(path: Path) -> Any:
    def pairs(items: Sequence[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in items:
            if key in value:
                raise ValueError("duplicate_key")
            value[key] = item
        return value
    value = json.loads(path.read_bytes(), object_pairs_hook=pairs,
                       parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite")))
    _canonical(value)
    return value


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value)
    return str(value)


def _behavior(current: float, previous: float | None) -> str:
    if previous is None:
        return "anchor"
    if current == previous:
        return "plateau"
    return "shrink" if current < previous else "inflate"


def expected_level_rows(levels: Sequence[Mapping[str, Any]],
                        pieces_by_level: Sequence[Sequence[Mapping[str, Any]]],
                        evidence_hashes: Sequence[str]) -> list[dict[str, str]]:
    """Derive expected rows directly from raw records, independently."""
    if len(levels) != 6 or len(pieces_by_level) != 6 or len(evidence_hashes) != 6:
        raise ValueError("level_count")
    aggregates: list[float] = []
    errors: list[float] = []
    for index, (level, pieces) in enumerate(zip(levels, pieces_by_level)):
        if level.get("tolerance") != TOLERANCES[index] or len(pieces) != 9:
            raise ValueError("retained_level")
        if index < 5:
            estimate = level.get("estimate")
            if type(estimate) is not float or not math.isfinite(estimate):
                raise ValueError("completed_estimate")
        else:
            if level.get("estimate") is not None:
                raise ValueError("warning_estimate")
            values = [piece.get("estimate") for piece in pieces]
            if any(type(value) is not float or not math.isfinite(value) for value in values):
                raise ValueError("piece_estimate")
            estimate = math.fsum(values)
        error = level.get("reported_error")
        if type(error) is not float or not math.isfinite(error):
            raise ValueError("reported_error")
        aggregates.append(estimate)
        errors.append(error)

    expected: list[dict[str, str]] = []
    for index, (level, pieces, source_hash) in enumerate(
            zip(levels, pieces_by_level, evidence_hashes)):
        previous_pieces = pieces_by_level[index - 1] if index else None
        nodes_equal = None if previous_pieces is None else all(
            [pair[0] for pair in piece["trace"]] == [pair[0] for pair in prior["trace"]]
            for piece, prior in zip(pieces, previous_pieces)
        )
        values_equal = None if previous_pieces is None else all(
            [pair[1] for pair in piece["trace"]] == [pair[1] for pair in prior["trace"]]
            for piece, prior in zip(pieces, previous_pieces)
        )
        hashes_equal = None if previous_pieces is None else (
            [piece["trace_sha256"] for piece in pieces]
            == [piece["trace_sha256"] for piece in previous_pieces]
        )
        arrays_equal = None if previous_pieces is None else all(
            all(piece[key] == prior[key] for key in ("alist", "blist", "rlist", "elist"))
            for piece, prior in zip(pieces, previous_pieces)
        )
        previous_estimate = aggregates[index - 1] if index else None
        previous_error = errors[index - 1] if index else None
        row = {
            "level": str(index),
            "tolerance": str(level["tolerance"]),
            "status": "complete" if level["complete"] else "warning_partial",
            "estimate_available": "True",
            "aggregate_kind": "historical_level" if level["complete"] else "reviewer_derived_piece_return_sum",
            "estimate_equal_previous": "" if index == 0 else str(aggregates[index] == previous_estimate),
            "estimate_delta_within_gate": "" if index == 0 else str(abs(aggregates[index] - previous_estimate) <= GATE),
            "error_available": "True",
            "error_equal_previous": "" if index == 0 else str(errors[index] == previous_error),
            "error_behavior": _behavior(errors[index], previous_error),
            "reported_bounds_met": str(level["reported_bounds_met"]),
            "neval": str(level["neval"]),
            "terminal_intervals": str(level["terminal_panels"]),
            "subdivision_operations": str(level["subdivisions"]),
            "warning": str(level["warnings"]),
            "termination": "normal" if level["complete"] else "roundoff_warning",
            "trace_nodes_equal_previous": "" if index == 0 else str(nodes_equal),
            "trace_values_equal_previous": "" if index == 0 else str(values_equal),
            "piece_hashes_equal_previous": "" if index == 0 else str(hashes_equal),
            "terminal_arrays_equal_previous": "" if index == 0 else str(arrays_equal),
            "trace_hash": str(level["trace_sha256"]),
            "evidence_sha256": source_hash,
        }
        expected.append(row)
    return expected


def parse_level_csv(data: bytes) -> list[dict[str, str]]:
    text = data.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if tuple(reader.fieldnames or ()) != LEVEL_FIELDS:
        raise ValueError("level_fields")
    return [dict(row) for row in reader]


def compare_level_rows(actual: Sequence[Mapping[str, str]],
                       expected: Sequence[Mapping[str, str]]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    if len(actual) != len(expected):
        failures.append({"row": None, "field": "row_count", "expected": len(expected), "actual": len(actual)})
    for index in range(max(len(actual), len(expected))):
        if index >= len(actual):
            failures.append({"row": index, "field": "row", "expected": "present", "actual": "missing"})
            continue
        if index >= len(expected):
            failures.append({"row": index, "field": "row", "expected": "absent", "actual": "extra"})
            continue
        for field in LEVEL_FIELDS:
            if actual[index].get(field) != expected[index].get(field):
                failures.append({"row": index, "field": field,
                                 "expected": expected[index].get(field),
                                 "actual": actual[index].get(field)})
    return failures


def validate_package(folder: Path, levels: Sequence[Mapping[str, Any]],
                     pieces_by_level: Sequence[Sequence[Mapping[str, Any]]],
                     evidence_hashes: Sequence[str]) -> dict[str, Any]:
    expected = expected_level_rows(levels, pieces_by_level, evidence_hashes)
    actual = parse_level_csv((folder / "level_summary.csv").read_bytes())
    failures = compare_level_rows(actual, expected)
    manifest = _strict_load(folder / "manifest.json")
    qc = _strict_load(folder / "qc.json")
    required = {
        "level_summary.csv", "terminal_subdivision_summary.json",
        "error_contribution_summary.csv", "warning_semantics.json",
        "missing_evidence.json", "publication_validation.json", "qc.json",
    }
    if set(manifest.get("outputs", {})) != required:
        failures.append({"row": None, "field": "manifest_outputs", "expected": "exact", "actual": "mismatch"})
    for name, expected_hash in manifest.get("outputs", {}).items():
        if not (folder / name).is_file() or _sha(folder / name) != expected_hash:
            failures.append({"row": None, "field": "output_hash", "expected": name, "actual": "mismatch"})
    validation = _strict_load(folder / "publication_validation.json")
    if validation.get("accepted") is not True or validation.get("failure_count") != 0:
        failures.append({"row": None, "field": "publication_validation", "expected": "accepted", "actual": "failed"})
    if qc.get("status") != "closed" or qc.get("execution_valid") is not True:
        failures.append({"row": None, "field": "qc", "expected": "closed", "actual": "invalid"})
    if qc.get("new_numerical_evaluations") != 0 or qc.get("empirical_records_opened") != 0:
        failures.append({"row": None, "field": "scope", "expected": "zero", "actual": "nonzero"})
    if failures:
        raise ValueError(json.dumps(failures, sort_keys=True, separators=(",", ":")))
    return {"accepted": True, "failure_count": 0, "validated_levels": 6,
            "validator_path": "independent_raw_record_mapping"}
