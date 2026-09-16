"""Prospective R9 public-package validator; standard library and no data route."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping


SCHEMA_ID = "session14r9_public_artifacts_v1"
PUBLIC_ARTIFACTS = (
    "preaccess_contract.json",
    "retained_observation_certificate_gate.json",
    "runner_failure_oracles.json",
    "runner_success_oracle.json",
    "synthetic_acceptance.json",
    "evidence_type_summary.json",
    "visual_qa.json",
    "candidate_summary.json",
    "structural_correspondence.csv",
    "candidate_pair_comparison.csv",
    "receiver_corridor_ordering.csv",
    "union_vs_max.csv",
    "overlap_redundancy.csv",
    "multi_edge_summary.csv",
    "match_summary.csv",
    "synthetic_stress_summary.json",
    "qc.json",
    "manifest.json",
    "synthetic_field_comparison.svg",
)
MANIFEST_MEMBERS = tuple(name for name in PUBLIC_ARTIFACTS if name != "manifest.json")
CANDIDATES = ("isotropic", "expanding", "constant_width")
COUNTERS = (
    "states_discovered", "states_prepared", "states_evaluation_started",
    "states_completed", "edges_discovered", "edges_opened",
    "edges_evaluation_started", "edges_completed", "unresolved_exposed_edges",
    "projection_attempts", "unresolved_projection_attempts",
    "field_evaluations_started", "field_evaluations_completed", "state_failures",
)


class PublicationContractError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        if key in result:
            raise PublicationContractError("duplicate_key")
        result[key] = value
    return result


def load_json(path: Path) -> Any:
    return json.loads(
        Path(path).read_text(),
        object_pairs_hook=_pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(PublicationContractError("nonfinite_json")),
    )


def _finite(value: Any) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise PublicationContractError("nonfinite_value")
    if isinstance(value, Mapping):
        for item in value.values():
            _finite(item)
    elif isinstance(value, list):
        for item in value:
            _finite(item)


def validate_progress_authority(authority: Mapping[str, Any]) -> dict[str, Any]:
    expected = {"schema_version", "mode", "journal_sha256", "snapshot_sha256", "snapshot"}
    if not isinstance(authority, Mapping) or set(authority) != expected or authority["schema_version"] != 2:
        raise PublicationContractError("progress_authority_schema")
    mode = authority["mode"]
    if mode not in ("pre_access", "empirical_partial", "empirical_failure", "empirical_success"):
        raise PublicationContractError("progress_authority_mode")
    if mode == "pre_access":
        if any(authority[key] is not None for key in ("journal_sha256", "snapshot_sha256", "snapshot")):
            raise PublicationContractError("pre_access_authority")
        return {
            "mode": mode,
            "lifecycle_initialized": False,
            "access_authorized": False,
            "confirmed_zero_exposure": True,
            "status": "pre_access",
        }
    for key in ("journal_sha256", "snapshot_sha256"):
        if not isinstance(authority[key], str) or len(authority[key]) != 64:
            raise PublicationContractError("authority_hash")
    snapshot = authority["snapshot"]
    snapshot_keys = {
        "schema_version", "status", "access_authorized", "counters",
        "field_work_by_candidate", "active", "failure_stage", "exception",
        "confirmed_zero_exposure",
    }
    if not isinstance(snapshot, Mapping) or set(snapshot) != snapshot_keys or snapshot["schema_version"] != 1:
        raise PublicationContractError("lifecycle_snapshot_schema")
    counters = snapshot["counters"]
    if not isinstance(counters, Mapping) or set(counters) != set(COUNTERS):
        raise PublicationContractError("lifecycle_counter_schema")
    if any(type(counters[name]) is not int or counters[name] < 0 for name in COUNTERS):
        raise PublicationContractError("lifecycle_counter_type")
    if not (counters["states_completed"] <= counters["states_evaluation_started"] <= counters["states_prepared"] <= counters["states_discovered"]):
        raise PublicationContractError("state_counter_order")
    if not (counters["edges_completed"] <= counters["edges_evaluation_started"] <= counters["edges_opened"] <= counters["edges_discovered"]):
        raise PublicationContractError("edge_counter_order")
    if counters["unresolved_exposed_edges"] != counters["edges_opened"] - counters["edges_completed"]:
        raise PublicationContractError("unresolved_edge_count")
    work = snapshot["field_work_by_candidate"]
    if not isinstance(work, Mapping) or set(work) != set(CANDIDATES):
        raise PublicationContractError("candidate_work_schema")
    for item in work.values():
        if not isinstance(item, Mapping) or set(item) != {"started", "completed"}:
            raise PublicationContractError("candidate_work_fields")
        if any(type(item[key]) is not int or item[key] < 0 for key in item) or item["completed"] > item["started"]:
            raise PublicationContractError("candidate_work_count")
    if sum(item["started"] for item in work.values()) != counters["field_evaluations_started"]:
        raise PublicationContractError("candidate_started_total")
    if sum(item["completed"] for item in work.values()) != counters["field_evaluations_completed"]:
        raise PublicationContractError("candidate_completed_total")
    active = snapshot["active"]
    if not isinstance(active, Mapping) or set(active) != {"state", "edge", "candidate"}:
        raise PublicationContractError("active_context_schema")
    expected_status = {"empirical_success": "success", "empirical_failure": "failure"}.get(mode)
    if expected_status and snapshot["status"] != expected_status:
        raise PublicationContractError("mode_status")
    if mode == "empirical_partial" and snapshot["status"] not in ("blocked", "failure"):
        raise PublicationContractError("partial_status")
    return {
        "mode": mode,
        "lifecycle_initialized": True,
        "access_authorized": snapshot["access_authorized"],
        "confirmed_zero_exposure": snapshot["confirmed_zero_exposure"],
        "status": snapshot["status"],
        "counters": dict(counters),
        "field_work_by_candidate": {key: dict(value) for key, value in work.items()},
        "active": dict(active),
        "failure_stage": snapshot["failure_stage"],
        "exception": snapshot["exception"],
    }


@dataclass(frozen=True)
class ValidationReceipt:
    schema_version: int
    schema_id: str
    lifecycle_representation_source: str
    artifact_count: int
    package_status: str
    result: str
    optional_legacy_lifecycle_checked: bool


def validate_public_package(
    directory: Path,
    *,
    optional_legacy_lifecycle: Mapping[str, Any] | None = None,
) -> ValidationReceipt:
    directory = Path(directory)
    manifest = load_json(directory / "manifest.json")
    manifest_keys = {
        "schema_version", "status", "progress_authority", "start", "protocol",
        "implementation", "environment", "outputs", "unavailable",
        "private_evidence_sha256", "private_manifest_sha256",
    }
    if not isinstance(manifest, Mapping) or set(manifest) != manifest_keys or manifest["schema_version"] != 1:
        raise PublicationContractError("manifest_schema")
    status = manifest["status"]
    if status not in ("success", "failure", "blocked"):
        raise PublicationContractError("status")
    outputs, unavailable = manifest["outputs"], manifest["unavailable"]
    if not isinstance(outputs, Mapping) or not isinstance(unavailable, list):
        raise PublicationContractError("manifest_members")
    if set(outputs) | set(unavailable) != set(MANIFEST_MEMBERS) or set(outputs) & set(unavailable):
        raise PublicationContractError("frozen_schema_membership")
    for name, expected_hash in outputs.items():
        if name not in MANIFEST_MEMBERS or not isinstance(expected_hash, str) or len(expected_hash) != 64:
            raise PublicationContractError("output_authority")
        path = directory / name
        if not path.is_file() or sha256_file(path) != expected_hash:
            raise PublicationContractError("output_hash")
        if name.endswith(".json"):
            _finite(load_json(path))
    if "qc.json" not in outputs:
        raise PublicationContractError("qc_required")
    qc = load_json(directory / "qc.json")
    qc_keys = {
        "schema_version", "status", "progress_authority", "stage", "exception",
        "scientific_comparisons_available",
    }
    if not isinstance(qc, Mapping) or set(qc) != qc_keys or qc["schema_version"] != 1:
        raise PublicationContractError("qc_schema")
    if qc["status"] != status or qc["progress_authority"] != manifest["progress_authority"]:
        raise PublicationContractError("qc_manifest_mismatch")
    if type(qc["scientific_comparisons_available"]) is not bool:
        raise PublicationContractError("scientific_availability_type")
    if status == "success":
        if unavailable or not qc["scientific_comparisons_available"] or qc["exception"] is not None:
            raise PublicationContractError("invalid_success")
    elif qc["scientific_comparisons_available"]:
        raise PublicationContractError("failure_science_available")
    validate_progress_authority(qc["progress_authority"])
    checked = optional_legacy_lifecycle is not None
    if checked and optional_legacy_lifecycle != qc["progress_authority"]:
        raise PublicationContractError("legacy_lifecycle_conflict")
    for key in ("private_evidence_sha256", "private_manifest_sha256", "protocol"):
        if not isinstance(manifest[key], str) or len(manifest[key]) != 64:
            raise PublicationContractError("manifest_hash_authority")
    if not isinstance(manifest["implementation"], Mapping) or not manifest["implementation"]:
        raise PublicationContractError("implementation_authority")
    return ValidationReceipt(
        schema_version=1,
        schema_id=SCHEMA_ID,
        lifecycle_representation_source="qc.json.progress_authority",
        artifact_count=len(PUBLIC_ARTIFACTS),
        package_status=status,
        result="valid",
        optional_legacy_lifecycle_checked=checked,
    )


__all__ = [
    "COUNTERS", "MANIFEST_MEMBERS", "PUBLIC_ARTIFACTS", "PublicationContractError",
    "SCHEMA_ID", "ValidationReceipt", "load_json", "sha256_file",
    "validate_progress_authority", "validate_public_package",
]
