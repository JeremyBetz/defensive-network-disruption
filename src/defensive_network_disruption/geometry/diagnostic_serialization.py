"""Explicit JSON projection for internal continuous-field diagnostic evidence."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import traceback
from typing import Any, Mapping

import numpy as np

from .micro_interval_verifier import IntegralInterval
from .root_partition_determinism import CertifiedOnset, CertifiedRootTransition
from .verification_repair import (
    CertifiedBoundary,
    CertifiedTieInterval,
    VerifiedEnvelope,
    VerifiedSwitch,
)


class DiagnosticSerializationError(TypeError):
    """Diagnostic evidence is outside the frozen JSON projection contract."""


def _finite(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, np.integer, np.floating)):
        raise DiagnosticSerializationError(f"{field}_must_be_float")
    result = float(value)
    if not math.isfinite(result):
        raise DiagnosticSerializationError(f"{field}_nonfinite")
    return result


def _integer(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
        raise DiagnosticSerializationError(f"{field}_must_be_int")
    return int(value)


def _owners(value: Any, field: str) -> list[int]:
    if not isinstance(value, tuple):
        raise DiagnosticSerializationError(f"{field}_must_be_tuple")
    projected = [_integer(item, field) for item in value]
    if any(item < 0 for item in projected) or len(projected) != len(set(projected)):
        raise DiagnosticSerializationError(f"{field}_malformed")
    return sorted(projected)


def _pairs(value: Any, field: str) -> list[list[int]]:
    if not isinstance(value, tuple):
        raise DiagnosticSerializationError(f"{field}_must_be_tuple")
    projected: list[tuple[int, int]] = []
    for pair in value:
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise DiagnosticSerializationError(f"{field}_malformed")
        first, second = (_integer(item, field) for item in pair)
        if first < 0 or second < 0 or first == second:
            raise DiagnosticSerializationError(f"{field}_malformed")
        projected.append(tuple(sorted((first, second))))
    if len(projected) != len(set(projected)):
        raise DiagnosticSerializationError(f"{field}_malformed")
    return [list(pair) for pair in sorted(projected)]


def project_boundary(value: CertifiedBoundary | None) -> dict[str, Any] | None:
    if value is None:
        return None
    if type(value) is not CertifiedBoundary or value.direction not in ("entry", "exit"):
        raise DiagnosticSerializationError("certified_boundary_invalid")
    return {
        "direction": value.direction,
        "inside": _finite(value.inside, "boundary_inside"),
        "outside": _finite(value.outside, "boundary_outside"),
        "owners": _owners(value.owners, "boundary_owners"),
        "pair": _pairs((value.pair,), "boundary_pair")[0],
    }


def project_tie_interval(value: CertifiedTieInterval) -> dict[str, Any]:
    if type(value) is not CertifiedTieInterval:
        raise DiagnosticSerializationError("tie_interval_invalid")
    return {
        "end": project_boundary(value.end),
        "owners": _owners(value.owners, "tie_owners"),
        "pairs": _pairs(value.pairs, "tie_pairs"),
        "start": project_boundary(value.start),
    }


def project_switch(value: VerifiedSwitch) -> dict[str, Any]:
    if type(value) is not VerifiedSwitch or type(value.endpoint) is not bool or type(value.multiway) is not bool:
        raise DiagnosticSerializationError("verified_switch_invalid")
    return {
        "crossing_pairs": _pairs(value.crossing_pairs, "switch_pairs"),
        "endpoint": value.endpoint,
        "envelope_value": _finite(value.envelope_value, "envelope_value"),
        "location": _finite(value.location, "switch_location"),
        "multiway": value.multiway,
        "owners_after": _owners(value.owners_after, "owners_after"),
        "owners_at": _owners(value.owners_at, "owners_at"),
        "owners_before": _owners(value.owners_before, "owners_before"),
    }


def project_verified_envelope(value: VerifiedEnvelope) -> dict[str, Any]:
    """Project one envelope without arbitrary dataclass recursion."""
    if type(value) is not VerifiedEnvelope:
        raise DiagnosticSerializationError("verified_envelope_required")
    if not isinstance(value.switches, tuple) or not isinstance(value.tie_intervals, tuple):
        raise DiagnosticSerializationError("envelope_sequences_must_be_tuple")
    partitions = [_finite(item, "partition") for item in value.partitions]
    if not partitions or any(right < left for left, right in zip(partitions, partitions[1:])):
        raise DiagnosticSerializationError("partitions_malformed")
    return {
        "grid_intervals": _integer(value.grid_intervals, "grid_intervals"),
        "maximizing_defenders": _owners(value.maximizing_defenders, "maximizing_defenders"),
        "partitions": partitions,
        "schema_version": 1,
        "switches": [project_switch(item) for item in value.switches],
        "tie_intervals": [project_tie_interval(item) for item in value.tie_intervals],
        "type": "verified_envelope",
    }


def _project_onset(value: CertifiedOnset) -> dict[str, Any]:
    return {
        "branch": _integer(value.branch, "onset_branch"),
        "defender_index": _integer(value.defender_index, "onset_defender"),
        "first_post_branch": _finite(value.first_post_branch, "first_post_branch"),
        "last_pre_branch": _finite(value.last_pre_branch, "last_pre_branch"),
        "raw_scalar_result": _finite(value.raw_scalar_result, "raw_scalar_result"),
        "type": "certified_onset",
    }


def _project_transition(value: CertifiedRootTransition) -> dict[str, Any]:
    return {
        "crossing_pairs": _pairs(value.crossing_pairs, "transition_pairs"),
        "exact_zero_end": None if value.exact_zero_end is None else _finite(value.exact_zero_end, "zero_end"),
        "exact_zero_start": None if value.exact_zero_start is None else _finite(value.exact_zero_start, "zero_start"),
        "first_post_switch": _finite(value.first_post_switch, "first_post_switch"),
        "last_pre_switch": _finite(value.last_pre_switch, "last_pre_switch"),
        "owners_after": _owners(value.owners_after, "transition_owners_after"),
        "owners_at": _owners(value.owners_at, "transition_owners_at"),
        "owners_before": _owners(value.owners_before, "transition_owners_before"),
        "raw_solver_result": _finite(value.raw_solver_result, "raw_solver_result"),
        "type": "certified_root_transition",
    }


def _project_interval(value: IntegralInterval) -> dict[str, Any]:
    return {
        "bounded_piece_count": _integer(value.bounded_piece_count, "bounded_piece_count"),
        "lower": _finite(value.lower, "interval_lower"),
        "quadrature_piece_count": _integer(value.quadrature_piece_count, "quadrature_piece_count"),
        "residual_bound": _finite(value.residual_bound, "residual_bound"),
        "structural_piece_count": _integer(value.structural_piece_count, "structural_piece_count"),
        "type": "integral_interval",
        "upper": _finite(value.upper, "interval_upper"),
    }


def project_evidence(value: Any) -> Any:
    """Recursively project only explicitly approved diagnostic values."""
    if value is None or type(value) in (str, bool):
        return value
    if isinstance(value, (int, np.integer)) and not isinstance(value, bool):
        return int(value)
    if isinstance(value, (float, np.floating)):
        return _finite(value, "evidence_float")
    if type(value) is VerifiedEnvelope:
        return project_verified_envelope(value)
    if type(value) is VerifiedSwitch:
        return project_switch(value)
    if type(value) is CertifiedTieInterval:
        return project_tie_interval(value)
    if type(value) is CertifiedBoundary:
        return project_boundary(value)
    if type(value) is CertifiedOnset:
        return _project_onset(value)
    if type(value) is CertifiedRootTransition:
        return _project_transition(value)
    if type(value) is IntegralInterval:
        return _project_interval(value)
    if isinstance(value, Mapping):
        if type(value) is not dict or not all(type(key) is str for key in value):
            raise DiagnosticSerializationError("mapping_must_be_plain_string_dict")
        return {key: project_evidence(item) for key, item in value.items()}
    if type(value) in (list, tuple):
        return [project_evidence(item) for item in value]
    if isinstance(value, (set, frozenset)):
        raise DiagnosticSerializationError("unordered_container_unsupported")
    raise DiagnosticSerializationError(f"unsupported_type:{type(value).__name__}")


def canonical_bytes(value: Any) -> bytes:
    projected = project_evidence(value)
    return (json.dumps(projected, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8")


def evidence_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def semantic_envelope_equal(value: VerifiedEnvelope, projected: Mapping[str, Any]) -> bool:
    return project_verified_envelope(value) == dict(projected)


def emergency_write(path: Path, primary: BaseException, *, stage: str) -> None:
    """Write independent minimal failure evidence without projecting the payload."""
    record = {
        "exception": type(primary).__name__,
        "message": str(primary),
        "schema_version": 1,
        "stage": stage,
        "traceback": "".join(traceback.format_exception(primary)),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(record))


__all__ = [
    "DiagnosticSerializationError", "canonical_bytes", "emergency_write",
    "evidence_sha256", "project_boundary", "project_evidence", "project_switch",
    "project_tie_interval", "project_verified_envelope", "semantic_envelope_equal",
]
