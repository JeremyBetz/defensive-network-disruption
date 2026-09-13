"""Internal Session 14ah diagnostics and diagnostic-event publication adapter."""
from __future__ import annotations

import hashlib
import json
import math
import struct
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from ..data.boundary_review import View, finite_point, identifier
from ..data.representation_projection import ALIASES, CANONICAL_KEYS, DEVELOPMENT
from ..geometry.occlusion_fields import CarrierOriginField, validate_geometry
from ..geometry.root_partition_determinism import certify_switch, deterministic_directional_onsets
from ..geometry.verification_audit import controlled_vector, scalar_oracle
from ..geometry.verification_repair import VerificationError, find_verified_envelope
from ..geometry.integration_review import values_for_components
from .projection_exposure import replay_exposure
from .r5_persistence import CANDIDATES, LifecycleError, digest, read_journal


DIAGNOSTIC_STAGES = (
    "geometry", "joint_simpson", "envelope", "routing", "strict_piecewise",
    "repeat_piecewise", "onset_adaptive", "direct_simpson", "accepted",
)
BASE_EVENTS = {
    "initialized", "access_authorized", "state_discovered", "projection_attempt",
    "projection_not_materialized", "projection_materialized", "state_prepared",
    "state_evaluation_started", "field_started", "field_completed", "edge_completed",
    "state_completed", "failure", "blocked", "success", "failure_evidence",
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def float_bits(value: float) -> str:
    return struct.pack(">d", float(value)).hex()


def _array_item(view: View, span: tuple[int, int], ordinal: int) -> Any:
    if isinstance(ordinal, bool) or not isinstance(ordinal, int) or ordinal < 0:
        raise ValueError("receiver_ordinal")
    for index, item in enumerate(view.items(span)):
        if index == ordinal:
            return view.read(item)
    raise ValueError("receiver_ordinal")


def project_prepared_edge(text: str, ordinal: int) -> dict[str, Any]:
    """Decode one prepared receiver while lexically skipping every other receiver."""
    view = View(text); fields = view.fields()
    if set(fields) != {"alias", "carrier", "receivers", "defenders"}:
        raise ValueError("prepared_schema")
    alias = identifier(view.get(fields, "alias"))
    if alias not in ALIASES:
        raise PermissionError("development_only")
    carrier = finite_point(view.get(fields, "carrier"))
    receiver = finite_point(_array_item(view, fields["receivers"], ordinal))
    defenders = tuple(finite_point(view.read(item)) for item in view.items(fields["defenders"]))
    validate_geometry(carrier, defenders)
    return {"alias": alias, "carrier": carrier, "receiver": receiver, "defenders": defenders}


def project_canonical_edge(text: str, ordinal: int) -> dict[str, Any]:
    """Decode only the corresponding canonical geometry and no target value."""
    view = View(text); fields = view.fields()
    if set(fields) != CANONICAL_KEYS:
        raise ValueError("canonical_schema")
    match = identifier(view.get(fields, "match_id"))
    if match not in DEVELOPMENT:
        raise PermissionError("development_only")
    carrier = finite_point(view.get(fields, "carrier_xy"))
    receiver = finite_point(_array_item(view, fields["candidate_xy"], ordinal))
    defenders = tuple(finite_point(view.read(item)) for item in view.items(fields["defender_xy"]))
    validate_geometry(carrier, defenders)
    return {"alias": ALIASES[DEVELOPMENT.index(match)], "carrier": carrier,
            "receiver": receiver, "defenders": defenders}


def selective_bytes(row: Mapping[str, Any]) -> bytes:
    return (json.dumps(row, sort_keys=True, allow_nan=False, separators=(",", ":")) + "\n").encode()


def _validate_diagnostic(payload: Mapping[str, Any], active: tuple[str, str, str] | None) -> None:
    if set(payload) != {"state", "edge", "candidate", "detail"}:
        raise LifecycleError("numerical_stage_payload")
    state, edge, candidate = payload["state"], payload["edge"], payload["candidate"]
    if not isinstance(state, (str, int)) or not isinstance(edge, (str, int)) or candidate not in CANDIDATES:
        raise LifecycleError("numerical_stage_context_type")
    if (str(state), str(edge), candidate) != active:
        raise LifecycleError("numerical_stage_context")
    detail = payload["detail"]
    if not isinstance(detail, dict) or "stage" not in detail or set(detail) - {"stage", "pieces", "bounded", "quadrature"}:
        raise LifecycleError("numerical_stage_detail")
    if detail["stage"] not in DIAGNOSTIC_STAGES:
        raise LifecycleError("numerical_stage_value")
    for key in ("pieces", "bounded", "quadrature"):
        if key in detail and (isinstance(detail[key], bool) or not isinstance(detail[key], int) or detail[key] < 0):
            raise LifecycleError("numerical_stage_count")
    if all(key in detail for key in ("pieces", "bounded", "quadrature")):
        if detail["bounded"] + detail["quadrature"] != detail["pieces"]:
            raise LifecycleError("numerical_stage_routing")


def replay_with_diagnostics(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Validate diagnostic events, then replay unchanged lifecycle semantics."""
    filtered = []
    active: tuple[str, str, str] | None = None
    diagnostics = []
    for record in records:
        action = record.get("action"); payload = record.get("payload")
        if action == "diagnostic_started":
            if active is not None or set(payload) != {"state", "edge", "candidate"}:
                raise LifecycleError("diagnostic_start")
            active = (str(payload.get("state")), str(payload.get("edge")), payload.get("candidate"))
            if active[2] not in CANDIDATES:
                raise LifecycleError("diagnostic_start")
            continue
        if action == "field_started":
            active = (str(payload.get("state")), str(payload.get("edge")), payload.get("candidate"))
        elif action == "field_completed":
            if active != (str(payload.get("state")), str(payload.get("edge")), payload.get("candidate")):
                raise LifecycleError("diagnostic_active_context")
            active = None
        if action == "numerical_stage":
            _validate_diagnostic(payload, active)
            diagnostics.append({"state": str(payload["state"]), "edge": str(payload["edge"]),
                                "candidate": payload["candidate"], **payload["detail"]})
        elif action == "diagnostic_stopped":
            if set(payload) != {"state", "edge", "candidate"} or active != (
                    str(payload.get("state")), str(payload.get("edge")), payload.get("candidate")):
                raise LifecycleError("diagnostic_stop")
            active = None
        elif action in BASE_EVENTS:
            filtered.append(record)
        else:
            raise LifecycleError("unknown_diagnostic_event")
    snapshot = replay_exposure(filtered)
    return {"snapshot": snapshot, "diagnostic_count": len(diagnostics),
            "diagnostic_stages": [item["stage"] for item in diagnostics],
            "journal_record_count": len(records)}


def replay_journal_with_diagnostics(path: Path, *, expected_head: str | None = None) -> dict[str, Any]:
    records, head = read_journal(path, expected_head=expected_head)
    result = replay_with_diagnostics(records)
    return {**result, "journal_sha256": head, "snapshot_sha256": digest(result["snapshot"])}


def _owners(row: np.ndarray) -> tuple[int, ...]:
    high = float(np.max(row))
    return () if high == 0.0 else tuple(i for i, value in enumerate(row) if high - float(value) <= 1e-12)


def diagnose_switch(origin, receiver, defenders) -> dict[str, Any]:
    """Capture the unchanged detector/certifier disagreement without repairing it."""
    b, ds, _ = validate_geometry(origin, defenders)
    end = np.asarray(receiver, dtype=np.float64)
    field = CarrierOriginField("constant_width")
    function = lambda t: field.individual_values(b, ds, b[None, :] + t[:, None] * (end - b)[None, :])
    onsets = deterministic_directional_onsets(b, end, ds)
    envelope = find_verified_envelope(function, extra_partitions=tuple(x.raw_scalar_result for x in onsets))
    failure = None; switch = None
    for item in envelope.switches:
        try:
            certify_switch(function, item)
        except VerificationError as error:
            failure = str(error); switch = item; break
    if failure != "switch_owner_semantics_changed" or switch is None:
        raise VerificationError("historical_failure_not_reproduced")

    import defensive_network_disruption.geometry.root_partition_determinism as roots
    lower, upper = roots._switch_witnesses(function, switch)
    pair = switch.crossing_pairs[0]
    grid = 1.0 / 65536.0
    partitions = envelope.partitions
    prior = max((x for x in partitions if x < switch.location), default=0.0)
    later = min((x for x in partitions if x > switch.location), default=1.0)
    probe = min(1e-7, (switch.location - prior) / 4.0, (later - switch.location) / 4.0)
    detector_points = (switch.location - probe, switch.location, switch.location + probe)
    points = {lower, upper, switch.location, *detector_points}
    cursor = switch.location
    for _ in range(2):
        cursor = float(np.nextafter(cursor, -math.inf)); points.add(cursor)
    cursor = switch.location
    for _ in range(2):
        cursor = float(np.nextafter(cursor, math.inf)); points.add(cursor)
    rows = []
    for point in sorted(points, key=lambda x: struct.unpack(">Q", struct.pack(">d", x))[0]):
        values = np.asarray(function(np.array([point]))[0], dtype=np.float64)
        query = b + point * (end - b)
        oracle = np.array([scalar_oracle("constant_width", b, defender, query) for defender in ds])
        rows.append({"point": point, "bits": float_bits(point), "values": values.tolist(),
                     "value_bits": [float_bits(x) for x in values], "owners": _owners(values),
                     "maximum": float(np.max(values)),
                     "oracle_match": bool(np.allclose(values, oracle, rtol=1e-12, atol=1e-12))})
    intervals, estimates, change = controlled_vector(lambda n: values_for_components(field, b, end, ds, n))
    onset_distances = [(item.branch, item.canonical, abs(item.canonical-switch.location)) for item in onsets]
    return {
        "failure": failure, "switch": switch, "pair": pair, "witnesses": (lower, upper),
        "detector_probe": probe, "detector_points": detector_points, "rows": rows,
        "onsets": onsets, "onset_distances": onset_distances, "ties": envelope.tie_intervals,
        "partitions": partitions, "joint": {"intervals": intervals, "change": change,
                                             "finite": all(math.isfinite(x) for x in estimates.values())},
        "owner_match_before": _owners(function(np.array([lower]))[0]) == switch.owners_before,
        "owner_match_after": _owners(function(np.array([upper]))[0]) == switch.owners_after,
    }


__all__ = ["DIAGNOSTIC_STAGES", "diagnose_switch", "float_bits", "project_canonical_edge",
           "project_prepared_edge", "replay_journal_with_diagnostics", "replay_with_diagnostics",
           "selective_bytes", "sha256_bytes"]
