"""R9E persisted-evidence validator for the reconciled nineteen-file package."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping

from . import numerical_failure_publication as numerical
from .r7_execution import exposure_summary, read_journal
from .r9a_publication import MANIFEST_MEMBERS, PUBLIC_ARTIFACTS, sha256_file


class R9EPublicationError(ValueError):
    pass


def _digest(value: object) -> str:
    raw = (json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False) + "\n").encode()
    return hashlib.sha256(raw).hexdigest()


def _load(path: Path) -> Any:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise R9EPublicationError("duplicate_key")
            result[key] = value
        return result
    return json.loads(path.read_text(), object_pairs_hook=pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(R9EPublicationError("nonfinite_json")))


def _finite(value: Any) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise R9EPublicationError("nonfinite_value")
    if isinstance(value, Mapping):
        for item in value.values():
            _finite(item)
    elif isinstance(value, list):
        for item in value:
            _finite(item)


def derive_progress(journal: Path, *, expected_head: str | None, mode: str) -> dict:
    records, head = read_journal(journal, expected_head=expected_head)
    if not records:
        if mode != "pre_access":
            raise R9EPublicationError("empty_empirical_journal")
        return {"schema_version": 3, "mode": mode, "journal_sha256": head,
                "snapshot_sha256": None, "snapshot": None,
                "exposure": exposure_summary(journal, expected_head=head)}
    authority = numerical.authority(journal, head)
    snapshot = authority["snapshot"]["snapshot"]
    exposure = exposure_summary(journal, expected_head=head)
    expected_status = {"empirical_success": "success", "empirical_failure": "failure"}.get(mode)
    if mode not in ("empirical_partial", "empirical_success", "empirical_failure"):
        raise R9EPublicationError("mode")
    if expected_status is not None and snapshot["status"] != expected_status:
        raise R9EPublicationError("mode_status")
    if mode == "empirical_partial" and snapshot["status"] not in ("failure", "blocked"):
        raise R9EPublicationError("partial_status")
    return {"schema_version": 3, "mode": mode, "journal_sha256": head,
            "snapshot_sha256": authority["snapshot_sha256"], "snapshot": snapshot,
            "exposure": exposure}


def _validate_success(authority: Mapping[str, Any]) -> None:
    snapshot = authority["snapshot"]
    exposure = authority["exposure"]
    counters = snapshot["counters"]
    candidates = snapshot["field_work_by_candidate"]
    if not snapshot["access_authorized"] or snapshot["status"] != "success":
        raise R9EPublicationError("success_authorization")
    if snapshot["active"] != {"state": None, "edge": None, "candidate": None}:
        raise R9EPublicationError("success_active_context")
    if snapshot["failure_stage"] is not None or snapshot["exception"] is not None:
        raise R9EPublicationError("success_failure_state")
    if counters["states_discovered"] != 7227 or not (
            counters["states_discovered"] == counters["states_prepared"] ==
            counters["states_evaluation_started"] == counters["states_completed"]):
        raise R9EPublicationError("success_state_completion")
    if not counters["edges_discovered"] or not (
            counters["edges_discovered"] == counters["edges_opened"] ==
            counters["edges_evaluation_started"] == counters["edges_completed"]):
        raise R9EPublicationError("success_edge_completion")
    if counters["unresolved_exposed_edges"] or counters["unresolved_projection_attempts"]:
        raise R9EPublicationError("success_unresolved_exposure")
    if counters["state_failures"]:
        raise R9EPublicationError("success_failures")
    if exposure["states_opened"] != 7227 or exposure["edges_opened"] != counters["edges_completed"]:
        raise R9EPublicationError("success_access_counts")
    if exposure["field_evaluations_completed"] != 3 * counters["edges_completed"]:
        raise R9EPublicationError("success_candidate_total")
    for item in candidates.values():
        if item["started"] != item["completed"] or item["completed"] != counters["edges_completed"]:
            raise R9EPublicationError("success_candidate_family")


def validate_private(private_dir: Path, journal: Path, *, expected_head: str | None,
                     mode: str) -> dict:
    names = ("qc.json", "manifest.json", "evidence.json", "progress_authority.json")
    records = {name: _load(private_dir / name) for name in names}
    actual = derive_progress(journal, expected_head=expected_head, mode=mode)
    if records["progress_authority.json"] != actual:
        raise R9EPublicationError("private_progress_mismatch")
    base = {"schema_version", "status", "progress_authority"}
    schemas = {
        "qc.json": base | {"stage", "exception", "scientific_comparisons_available"},
        "evidence.json": base,
        "manifest.json": base | {"outputs"},
    }
    for name, keys in schemas.items():
        if set(records[name]) != keys or records[name]["schema_version"] != 1:
            raise R9EPublicationError("private_schema:" + name)
        if records[name]["progress_authority"] != actual:
            raise R9EPublicationError("private_cross_file:" + name)
    status = records["qc.json"]["status"]
    if status not in ("success", "failure", "blocked"):
        raise R9EPublicationError("private_status")
    if any(records[name]["status"] != status for name in ("manifest.json", "evidence.json")):
        raise R9EPublicationError("private_status_mismatch")
    if status == "success":
        _validate_success(actual)
        if records["qc.json"]["exception"] is not None or not records["qc.json"]["scientific_comparisons_available"]:
            raise R9EPublicationError("invalid_private_success")
    elif records["qc.json"]["scientific_comparisons_available"]:
        raise R9EPublicationError("failure_science_available")
    for name, expected in records["manifest.json"]["outputs"].items():
        if Path(name).name != name or name == "manifest.json":
            raise R9EPublicationError("private_manifest_path")
        if sha256_file(private_dir / name) != expected:
            raise R9EPublicationError("private_hash")
    numerical.validate_persisted(private_dir / "numerical_publication", journal,
        actual["journal_sha256"], traceback_path=journal.parent / "numerical_traceback.txt")
    return actual


def validate_public(directory: Path, *, private_dir: Path, journal: Path,
                    expected_head: str | None, mode: str) -> dict:
    directory = Path(directory)
    manifest = _load(directory / "manifest.json")
    keys = {"schema_version", "status", "progress_authority", "start", "protocol",
            "implementation", "environment", "outputs", "unavailable",
            "private_evidence_sha256", "private_manifest_sha256"}
    if set(manifest) != keys or manifest["schema_version"] != 1:
        raise R9EPublicationError("manifest_schema")
    outputs, unavailable = manifest["outputs"], manifest["unavailable"]
    if set(outputs) | set(unavailable) != set(MANIFEST_MEMBERS) or set(outputs) & set(unavailable):
        raise R9EPublicationError("nineteen_file_schema")
    if len(PUBLIC_ARTIFACTS) != 19:
        raise R9EPublicationError("schema_count")
    for name, expected in outputs.items():
        path = directory / name
        if not path.is_file() or sha256_file(path) != expected:
            raise R9EPublicationError("public_hash:" + name)
        if name.endswith(".json"):
            _finite(_load(path))
    actual = validate_private(private_dir, journal, expected_head=expected_head, mode=mode)
    qc = _load(directory / "qc.json")
    if set(qc) != {"schema_version", "status", "progress_authority", "stage",
                   "exception", "scientific_comparisons_available"}:
        raise R9EPublicationError("qc_schema")
    if qc["progress_authority"] != actual or manifest["progress_authority"] != actual:
        raise R9EPublicationError("public_progress_mismatch")
    if qc["status"] != manifest["status"]:
        raise R9EPublicationError("public_status_mismatch")
    if manifest["status"] == "success":
        _validate_success(actual)
        if unavailable or not qc["scientific_comparisons_available"] or qc["exception"] is not None:
            raise R9EPublicationError("invalid_public_success")
    elif qc["scientific_comparisons_available"]:
        raise R9EPublicationError("failure_public_science")
    if sha256_file(private_dir / "evidence.json") != manifest["private_evidence_sha256"]:
        raise R9EPublicationError("private_evidence_binding")
    if sha256_file(private_dir / "manifest.json") != manifest["private_manifest_sha256"]:
        raise R9EPublicationError("private_manifest_binding")
    return {"schema_version": 1, "status": "valid", "artifact_count": 19,
            "lifecycle_source": "qc.json.progress_authority",
            "journal_replayed": True, "snapshot_hash_recomputed": True,
            "states_opened": actual["exposure"]["states_opened"],
            "progress_sha256": _digest(actual)}


__all__ = ["R9EPublicationError", "derive_progress", "validate_private", "validate_public"]
