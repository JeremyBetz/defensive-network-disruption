"""Read-only Session 14ap reduction of retained terminal quadrature evidence."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import statistics
from typing import Any, Mapping, Sequence

GATE = 1e-10
LEVEL_NUMBERS = (22, 42, 62, 82, 102, 122)
TOLERANCES = (1e-13, 5e-14, 2e-14, 1e-14, 5e-15, 2e-15)
LEVEL_FIELDS = (
    "level", "tolerance", "status", "estimate_available", "aggregate_kind",
    "estimate_equal_previous", "estimate_delta_within_gate", "error_available",
    "error_equal_previous", "error_behavior", "reported_bounds_met", "neval",
    "terminal_intervals", "subdivision_operations", "warning", "termination",
    "trace_nodes_equal_previous", "trace_values_equal_previous",
    "piece_hashes_equal_previous", "terminal_arrays_equal_previous",
    "trace_hash", "evidence_sha256",
)
ERROR_FIELDS = (
    "level", "status", "active_intervals", "ranking_available",
    "dominant_interval_ordinal", "maximum_error_tie_count", "top1_error_share",
    "top3_error_share", "onset_adjacent_intervals", "onset_error_share_available",
    "evidence_sha256",
)
PUBLIC_FILES = (
    "level_summary.csv", "terminal_subdivision_summary.json",
    "error_contribution_summary.csv", "warning_semantics.json",
    "missing_evidence.json", "qc.json",
)


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True, allow_nan=False) + "\n").encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1_048_576), b""):
            h.update(chunk)
    return h.hexdigest()


def strict_load(path: Path) -> Any:
    def pairs(items: Sequence[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate_key")
            result[key] = value
        return result

    value = json.loads(path.read_bytes(), object_pairs_hook=pairs,
                       parse_constant=lambda _: (_ for _ in ()).throw(
                           ValueError("nonfinite")))
    canonical(value)
    return value


def atomic(path: Path, value: Any, *, raw: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise FileExistsError(path)
    data = value if raw else canonical(value)
    temporary = path.with_name("." + path.name + ".pending")
    with temporary.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.link(temporary, path)
    finally:
        temporary.unlink()
    descriptor = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def csv_bytes(rows: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def finite(value: Any) -> bool:
    return type(value) in (int, float) and not isinstance(value, bool) and math.isfinite(value)


def selected_names() -> tuple[str, ...]:
    names = ["000001_reference.json", "000003_onsets.json"]
    for level_number in LEVEL_NUMBERS:
        names.extend(f"{number:06d}_piece.json"
                     for number in range(level_number - 17, level_number, 2))
        names.append(f"{level_number:06d}_level.json")
        names.append(f"{level_number + 1:06d}_comparison.json")
    return tuple(names)


def validate_piece(piece: Mapping[str, Any]) -> dict[str, Any]:
    required = {
        "a", "b", "callback_count", "trace_sha256", "trace", "warnings",
        "exception", "message", "normal", "exhausted", "estimate",
        "reported_error", "neval", "last", "alist", "blist", "rlist",
        "elist", "tolerance", "limit", "seconds",
    }
    if set(piece) != required:
        raise ValueError("piece_schema")
    if not all(finite(piece[key]) for key in ("a", "b", "tolerance", "limit", "seconds")):
        raise ValueError("piece_scalar")
    if piece["b"] <= piece["a"] or piece["limit"] != 1000:
        raise ValueError("piece_bounds")
    if type(piece["last"]) is not int or type(piece["neval"]) is not int:
        raise ValueError("piece_counts")
    if type(piece["callback_count"]) is not int or piece["callback_count"] != piece["neval"]:
        raise ValueError("callback_count")
    if piece["last"] < 1 or piece["last"] > piece["limit"]:
        raise ValueError("last")
    arrays = tuple(piece[key] for key in ("alist", "blist", "rlist", "elist"))
    if any(type(array) is not list or len(array) != piece["last"] for array in arrays):
        raise ValueError("initialized_array_length")
    if not all(finite(item) for array in arrays for item in array):
        raise ValueError("terminal_nonfinite")
    if type(piece["trace"]) is not list or len(piece["trace"]) != piece["neval"]:
        raise ValueError("trace_length")
    for pair in piece["trace"]:
        if type(pair) is not list or len(pair) != 2 or not all(finite(x) for x in pair):
            raise ValueError("trace_item")
    if digest(piece["trace"]) != piece["trace_sha256"]:
        raise ValueError("trace_hash")
    if not finite(piece["estimate"]) or not finite(piece["reported_error"]):
        raise ValueError("terminal_value")
    if any(right <= left for left, right in zip(piece["alist"], piece["blist"])):
        raise ValueError("terminal_width")
    if any(left < piece["a"] or right > piece["b"]
           for left, right in zip(piece["alist"], piece["blist"])):
        raise ValueError("terminal_outside_piece")
    ordered = sorted(zip(piece["alist"], piece["blist"]), key=lambda item: item[0])
    if ordered[0][0] != piece["a"] or ordered[-1][1] != piece["b"] or any(
            left[1] != right[0] for left, right in zip(ordered, ordered[1:])):
        raise ValueError("terminal_coverage")
    if math.fsum(piece["rlist"]) != piece["estimate"]:
        raise ValueError("terminal_estimate_sum")
    if math.fsum(piece["elist"]) != piece["reported_error"]:
        raise ValueError("terminal_error_sum")
    if type(piece["warnings"]) is not list or any(
            type(item) is not dict or set(item) != {"category", "message"}
            or not all(type(item[key]) is str for key in item)
            for item in piece["warnings"]):
        raise ValueError("warning_schema")
    if any(type(piece[key]) is not bool for key in ("normal", "exhausted")):
        raise ValueError("piece_boolean")
    if piece["normal"] != (not piece["warnings"] and piece["message"] is None
                            and piece["exception"] is None):
        raise ValueError("normal_semantics")
    return dict(piece)


def validate_level(level: Mapping[str, Any], pieces: Sequence[Mapping[str, Any]],
                   tolerance: float) -> None:
    required = {
        "tolerance", "complete", "normal", "warnings", "exhausted", "neval",
        "terminal_panels", "subdivisions", "onset_adjacent_panels",
        "onset_error_fraction", "estimate", "reported_error",
        "reported_bounds_met", "seconds", "trace_sha256", "pieces_attempted",
        "pieces_required",
    }
    if set(level) != required or level["tolerance"] != tolerance:
        raise ValueError("level_schema")
    if level["pieces_attempted"] != 9 or level["pieces_required"] != 9 or len(pieces) != 9:
        raise ValueError("piece_count")
    if level["neval"] != sum(piece["callback_count"] for piece in pieces):
        raise ValueError("level_neval")
    if level["terminal_panels"] != sum(piece["last"] for piece in pieces):
        raise ValueError("level_panels")
    if level["subdivisions"] != sum(piece["last"] - 1 for piece in pieces):
        raise ValueError("level_subdivisions")
    if level["trace_sha256"] != digest([piece["trace_sha256"] for piece in pieces]):
        raise ValueError("level_trace_hash")
    complete = all(piece["normal"] and not piece["exhausted"] for piece in pieces)
    if level["complete"] is not complete or level["normal"] is not complete:
        raise ValueError("level_completion")
    if level["warnings"] is not any(piece["warnings"] for piece in pieces):
        raise ValueError("level_warning")
    if complete:
        estimate = math.fsum(piece["estimate"] for piece in pieces)
        if level["estimate"] != estimate:
            raise ValueError("level_estimate")
    elif level["estimate"] is not None:
        raise ValueError("incomplete_historical_estimate")
    error = math.fsum(piece["reported_error"] for piece in pieces)
    if level["reported_error"] != error:
        raise ValueError("level_error")


def behavior(current: float, previous: float | None) -> str:
    if previous is None:
        return "anchor"
    if current == previous:
        return "plateau"
    return "shrink" if current < previous else "inflate"


def review_records(reference: Mapping[str, Any], onsets: Mapping[str, Any],
                   levels: Sequence[Mapping[str, Any]],
                   pieces_by_level: Sequence[Sequence[Mapping[str, Any]]],
                   evidence_hashes: Sequence[str]) -> dict[str, Any]:
    if set(reference) != {"anchor", "bounds", "reference"}:
        raise ValueError("reference_schema")
    if set(onsets) != {"partitions"} or type(onsets["partitions"]) is not list:
        raise ValueError("onset_schema")
    partitions = onsets["partitions"]
    if len(partitions) != 10 or partitions[0] != 0.0 or partitions[-1] != 1.0:
        raise ValueError("onset_count")
    if not all(finite(x) for x in partitions) or any(b <= a for a, b in zip(partitions, partitions[1:])):
        raise ValueError("onset_order")
    checked: list[list[dict[str, Any]]] = []
    for index, (level, pieces, tolerance) in enumerate(zip(levels, pieces_by_level, TOLERANCES)):
        validated = [validate_piece(piece) for piece in pieces]
        validate_level(level, validated, tolerance)
        checked.append(validated)
        if index < 5 and not level["complete"]:
            raise ValueError("completed_prefix")
        if index == 5 and (level["complete"] or not level["warnings"]):
            raise ValueError("warning_level")

    exact_estimates = [level["estimate"] for level in levels[:5]]
    warning_sum = math.fsum(piece["estimate"] for piece in checked[5])
    aggregate_estimates = [*exact_estimates, warning_sum]
    errors = [level["reported_error"] for level in levels]
    reference_value = reference["reference"]
    level_rows: list[dict[str, Any]] = []
    error_rows: list[dict[str, Any]] = []
    private_levels: list[dict[str, Any]] = []
    onsets_set = set(partitions[1:-1])

    for index, (level, pieces, estimate, error, source_hash) in enumerate(
            zip(levels, checked, aggregate_estimates, errors, evidence_hashes)):
        previous_estimate = aggregate_estimates[index - 1] if index else None
        previous_error = errors[index - 1] if index else None
        previous_pieces = checked[index - 1] if index else None
        nodes_equal = None if previous_pieces is None else all(
            [pair[0] for pair in piece["trace"]] ==
            [pair[0] for pair in prior["trace"]]
            for piece, prior in zip(pieces, previous_pieces))
        values_equal = None if previous_pieces is None else all(
            [pair[1] for pair in piece["trace"]] ==
            [pair[1] for pair in prior["trace"]]
            for piece, prior in zip(pieces, previous_pieces))
        piece_hashes_equal = None if previous_pieces is None else [
            piece["trace_sha256"] for piece in pieces] == [
                piece["trace_sha256"] for piece in previous_pieces]
        arrays_equal = None if previous_pieces is None else all(
            all(piece[key] == prior[key] for key in ("alist", "blist", "rlist", "elist"))
            for piece, prior in zip(pieces, previous_pieces))
        interval_errors: list[tuple[int, float, float, bool]] = []
        ordinal = 0
        for piece in pieces:
            for left, right, local_error in zip(piece["alist"], piece["blist"], piece["elist"]):
                interval_errors.append((ordinal, local_error, right - left,
                                        left in onsets_set or right in onsets_set))
                ordinal += 1
        ranked = sorted(interval_errors, key=lambda item: (-item[1], item[0]))
        total_error = math.fsum(item[1] for item in interval_errors)
        top1 = ranked[0][1] / total_error if total_error else None
        top3 = math.fsum(item[1] for item in ranked[:3]) / total_error if total_error else None
        max_ties = sum(item[1] == ranked[0][1] for item in ranked) if ranked else 0
        onset_adjacent = sum(item[3] for item in interval_errors)
        onset_error = math.fsum(item[1] for item in interval_errors if item[3])
        onset_fraction = onset_error / total_error if total_error else None
        if onset_adjacent != level["onset_adjacent_panels"] or onset_fraction != level["onset_error_fraction"]:
            raise ValueError("onset_summary")
        level_rows.append({
            "level": index, "tolerance": tolerance,
            "status": "complete" if level["complete"] else "warning_partial",
            "estimate_available": True,
            "aggregate_kind": "historical_level" if level["complete"] else "reviewer_derived_piece_return_sum",
            "estimate_equal_previous": "" if index == 0 else estimate == previous_estimate,
            "estimate_delta_within_gate": "" if index == 0 else abs(estimate - previous_estimate) <= GATE,
            "error_available": True,
            "error_equal_previous": "" if index == 0 else error == previous_error,
            "error_behavior": behavior(error, previous_error),
            "reported_bounds_met": level["reported_bounds_met"],
            "neval": level["neval"], "terminal_intervals": level["terminal_panels"],
            "subdivision_operations": level["subdivisions"], "warning": level["warnings"],
            "termination": "normal" if level["complete"] else "roundoff_warning",
            "trace_nodes_equal_previous": "" if index == 0 else nodes_equal,
            "trace_values_equal_previous": "" if index == 0 else values_equal,
            "piece_hashes_equal_previous": "" if index == 0 else piece_hashes_equal,
            "terminal_arrays_equal_previous": "" if index == 0 else arrays_equal,
            "trace_hash": level["trace_sha256"], "evidence_sha256": source_hash,
        })
        error_rows.append({
            "level": index, "status": "complete" if level["complete"] else "warning_partial",
            "active_intervals": len(interval_errors), "ranking_available": bool(ranked),
            "dominant_interval_ordinal": ranked[0][0] if ranked else "",
            "maximum_error_tie_count": max_ties,
            "top1_error_share": "" if top1 is None else top1,
            "top3_error_share": "" if top3 is None else top3,
            "onset_adjacent_intervals": onset_adjacent,
            "onset_error_share_available": total_error > 0,
            "evidence_sha256": source_hash,
        })
        private_levels.append({
            "level": index, "estimate": estimate,
            "aggregate_kind": level_rows[-1]["aggregate_kind"], "reported_error": error,
            "estimate_delta": None if previous_estimate is None else estimate - previous_estimate,
            "error_delta": None if previous_error is None else error - previous_error,
            "reference_difference": abs(estimate - reference_value),
            "widths": [item[2] for item in interval_errors],
            "ranked_local_errors": [[item[0], item[1]] for item in ranked],
            "top1_error_share": top1, "top3_error_share": top3,
            "onset_error_share": level["onset_error_fraction"],
        })

    warning_piece = next((piece for piece in checked[5] if piece["warnings"]), None)
    if warning_piece is None or len(warning_piece["warnings"]) != 1:
        raise ValueError("warning_piece")
    warning = warning_piece["warnings"][0]
    drift = any(abs(b - a) > GATE for a, b in zip(aggregate_estimates, aggregate_estimates[1:]))
    stable = not drift
    reference_within = all(abs(value - reference_value) <= GATE for value in aggregate_estimates)
    roundoff = warning["category"] == "IntegrationWarning" and "roundoff error" in warning["message"]
    terminal_above = warning_piece["reported_error"] > max(
        TOLERANCES[-1], TOLERANCES[-1] * abs(warning_piece["estimate"]))
    return {
        "level_rows": level_rows, "error_rows": error_rows,
        "private": {"levels": private_levels, "warning_piece": warning_piece,
                    "reference": dict(reference)},
        "facts": {
            "stable": stable, "drift": drift, "reference_within": reference_within,
            "roundoff_reported": roundoff, "terminal_error_above_request": terminal_above,
            "all_trace_nodes_equal": all(row["trace_nodes_equal_previous"] is True for row in level_rows[1:]),
            "all_trace_values_equal": all(row["trace_values_equal_previous"] is True for row in level_rows[1:]),
            "all_piece_hashes_equal": all(row["piece_hashes_equal_previous"] is True for row in level_rows[1:]),
            "all_terminal_arrays_equal": all(row["terminal_arrays_equal_previous"] is True for row in level_rows[1:]),
            "warning_level_sum_available": True,
            "warning_local_error_vector_available": True,
            "termination_metadata_available": True,
            "independent_warning_interval_bound_available": False,
        },
        "warning": warning,
        "width_summary": {
            "final_success": _width_summary(private_levels[4]["widths"]),
            "warning": _width_summary(private_levels[5]["widths"]),
        },
    }


def _width_summary(widths: Sequence[float]) -> dict[str, Any]:
    return {"count": len(widths), "minimum": min(widths),
            "median": statistics.median(widths), "maximum": max(widths),
            "sha256": digest(list(widths))}


def classify(facts: Mapping[str, Any], *, integrity_valid: bool = True) -> tuple[str, int, str]:
    if not integrity_valid:
        return "G", 4, "evidence_integrity_failure"
    drift = facts["drift"] is True
    roundoff = facts["roundoff_reported"] is True
    if drift and roundoff:
        return "E", 3, "independent_drift_and_reported_roundoff"
    if drift:
        return "D", 3, "estimate_drift_exceeds_existing_gate"
    if roundoff and facts["termination_metadata_available"] is True:
        return "C", 2, "integrator_reported_roundoff_limitation"
    if facts["stable"] is True and (facts["terminal_error_above_request"] is True
                                     or facts["reference_within"] is False):
        return "B", 2, "stable_estimate_with_unsatisfied_error_or_agreement_condition"
    if facts["stable"] is True and facts["reference_within"] is True:
        return "A", 1, "stable_and_independently_within_existing_gate"
    return "F", 4, "retained_evidence_insufficient"


def missing_item(facts: Mapping[str, Any]) -> dict[str, Any]:
    choices = (
        ("warning_level_returned_component", facts["warning_level_sum_available"]),
        ("warning_level_local_error_vector_and_termination", facts["warning_local_error_vector_available"]
         and facts["termination_metadata_available"]),
        ("independently_bounded_warning_interval_reference", facts["independent_warning_interval_bound_available"]),
        ("unchanged_method_next_level_with_additional_work", False),
    )
    item = next(name for name, available in choices if not available)
    return {"item": item, "available_in_retained_evidence": False,
            "requires_separate_authority": True}


def public_package(review: Mapping[str, Any], source_match: bool,
                   source_sha256: str) -> dict[str, Any]:
    facts = dict(review["facts"])
    facts["termination_metadata_available"] = facts["termination_metadata_available"] and source_match
    classification, readiness, rationale = classify(facts)
    missing = missing_item(facts)
    width = review["width_summary"]
    terminal = {
        "schema_version": 1,
        "final_success_level": 4,
        "warning_level": 5,
        "final_success_active_intervals": width["final_success"]["count"],
        "warning_active_intervals": width["warning"]["count"],
        "final_success_subdivision_operations": review["level_rows"][4]["subdivision_operations"],
        "warning_subdivision_operations": review["level_rows"][5]["subdivision_operations"],
        "deepest_refinement": "none_within_onset_pieces" if review["level_rows"][5]["subdivision_operations"] == 0 else "private",
        "width_values": "private/hash-bound",
        "final_success_width_sha256": width["final_success"]["sha256"],
        "warning_width_sha256": width["warning"]["sha256"],
        "partition_topology_equal": review["facts"]["all_terminal_arrays_equal"],
        "repeated_target_region": review["facts"]["all_terminal_arrays_equal"],
        "switch_adjacency": "unavailable_not_retained",
    }
    semantics = {
        "schema_version": 1,
        "category": review["warning"]["category"],
        "message": review["warning"]["message"],
        "locked_source_sha256": source_sha256,
        "locked_source_match": source_match,
        "documented_condition": "roundoff_detected_requested_tolerance_not_achieved_error_may_be_underestimated" if source_match else "unavailable",
        "interpretation_limit": "integrator_reported_condition_not_independent_true_error_proof",
    }
    missing_record = {
        "schema_version": 1,
        "classification": classification,
        "readiness": readiness,
        "rationale": rationale,
        "estimate_stability": "stable" if facts["stable"] else "not_stable",
        "reported_error_behavior": "plateau" if all(row["error_behavior"] in ("anchor", "plateau") for row in review["level_rows"]) else "changed",
        "certification": "failed_warning_and_reference_agreement",
        "decision_sufficient_for_warning_mechanism": classification in ("C", "E"),
        "decision_sufficient_for_numerical_accuracy": facts["reference_within"] is True,
        "next_evidence": missing,
        "recommendation": recommendation(classification, missing["item"]),
    }
    return {
        "level_summary.csv": csv_bytes(review["level_rows"], LEVEL_FIELDS),
        "terminal_subdivision_summary.json": terminal,
        "error_contribution_summary.csv": csv_bytes(review["error_rows"], ERROR_FIELDS),
        "warning_semantics.json": semantics,
        "missing_evidence.json": missing_record,
        "classification": classification,
        "readiness": readiness,
    }


def recommendation(classification: str, item: str) -> str:
    if classification == "A":
        return "Separately govern a bounded verifier-evidence contract repair using the retained stable estimate and independent accuracy authority."
    if classification in ("B", "C", "F"):
        return ("Separately govern acquisition of one independently bounded reference for the sanitized "
                "warning-producing terminal interval; do not rerun the full edge or alter the comparator automatically.")
    if classification in ("D", "E"):
        return "Separately govern a production numerical-method review focused on the retained estimate instability; do not resume the representation study."
    return "Resolve the retained-evidence integrity failure before any numerical or scientific work."


def validate_public(folder: Path, expected: Mapping[str, Any]) -> bool:
    manifest = strict_load(folder / "manifest.json")
    qc = strict_load(folder / "qc.json")
    if set(manifest) != {"schema_version", "status", "outputs", "authority", "private_index_sha256"}:
        raise ValueError("manifest_schema")
    if set(manifest["outputs"]) != set(PUBLIC_FILES):
        raise ValueError("manifest_outputs")
    if set(qc) != {"schema_version", "status", "execution_valid", "classification", "readiness",
                   "retained_records", "new_numerical_evaluations", "empirical_records_opened",
                   "exact_values_public", "private_index_sha256"}:
        raise ValueError("qc_schema")
    if qc["status"] != "closed" or not qc["execution_valid"]:
        raise ValueError("qc_status")
    if qc["new_numerical_evaluations"] != 0 or qc["empirical_records_opened"] != 0 or qc["exact_values_public"]:
        raise ValueError("scope")
    decision = expected["missing_evidence.json"]
    if qc["classification"] != decision["classification"] or qc["readiness"] != decision["readiness"]:
        raise ValueError("classification")
    if qc["private_index_sha256"] != manifest["private_index_sha256"] or sha(folder / "local/private_index.json") != qc["private_index_sha256"]:
        raise ValueError("private_index")
    for name, expected_hash in manifest["outputs"].items():
        if sha(folder / name) != expected_hash:
            raise ValueError("output_hash")
    for name, expected_value in expected.items():
        if name.endswith(".csv"):
            if (folder / name).read_bytes() != expected_value:
                raise ValueError("csv_reduction")
        elif name.endswith(".json") and strict_load(folder / name) != expected_value:
            raise ValueError("json_reduction")
    for name in PUBLIC_FILES:
        text = (folder / name).read_text()
        if any(token in text for token in ("/Users/", '"estimate":', '"reported_error":',
                                           '"widths":', '"trace":', '"a":', '"b":')):
            raise ValueError("private_value_leak")
    return True
