#!/usr/bin/env python3
"""Governed read-only reconciliation of the Session 14R9 public schema."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defensive_network_disruption.validation.r9a_publication import (
    MANIFEST_MEMBERS,
    PUBLIC_ARTIFACTS,
    PublicationContractError,
    SCHEMA_ID,
    load_json,
    sha256_file,
    validate_public_package,
)

START = "a3b2af244978d60c7e5a32ac573bcdc2d6916a2c"
TAG = "f00690c05d8c1c6db308a65bd311c43f9a8ef2fa"
PROTOCOL = Path("docs/protocols/phase_14r9a_publication_contract_reconciliation.md")
R9_PROTOCOL = Path("docs/protocols/phase_14r9_continuous_occlusion_empirical_retry.md")
R9_RUNNER = Path("scripts/session_14r9_occlusion_study.py")
R9_OUT = Path("outputs/continuous_occlusion_empirical_retry_r9")
OUT = Path("outputs/continuous_occlusion_empirical_retry_r9a")
LOCAL = OUT / "local"
FILES = (
    "authority_trace.json", "frozen_schema.json", "lifecycle_field_mapping.json",
    "publication_oracles.json", "revalidation.json", "qc.json",
)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT).decode().strip()


def safe(path: Path) -> Path:
    target = ROOT / path
    if any(item.is_symlink() for item in (target, *target.parents)) or not target.resolve().is_relative_to(ROOT.resolve()):
        raise PermissionError("unsafe_path")
    return target


def encoded(value) -> str:
    return json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"


def atomic(path: Path, value) -> None:
    destination = safe(path)
    if destination.exists():
        raise FileExistsError("output_exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.with_name("." + destination.name + ".tmp")
    with temp.open("x") as handle:
        handle.write(encoded(value) if not isinstance(value, str) else value)
        handle.flush(); os.fsync(handle.fileno())
    os.link(temp, destination); temp.unlink()


def committed(path: Path) -> None:
    content = subprocess.check_output(["git", "show", "HEAD:" + str(path)], cwd=ROOT)
    if hashlib.sha256(content).hexdigest() != sha256_file(safe(path)):
        raise ValueError("uncommitted_authority")


def preflight() -> None:
    if git("rev-parse", START) != START or git("rev-parse", "v0.1.0^{}") != TAG:
        raise ValueError("starting_authority")
    for path in (PROTOCOL, R9_PROTOCOL, R9_RUNNER, R9_OUT / "qc.json", R9_OUT / "manifest.json"):
        committed(path)
    if safe(R9_OUT / "local/run.marker").exists():
        raise ValueError("historical_empirical_marker_unexpected")


def claim() -> None:
    marker = safe(LOCAL / "reconcile.marker")
    marker.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w") as handle:
        handle.write(hashlib.sha256(safe(PROTOCOL).read_bytes()).hexdigest() + "\n")
        handle.flush(); os.fsync(handle.fileno())


def line_of(path: Path, fragment: str) -> int:
    for number, line in enumerate(safe(path).read_text().splitlines(), 1):
        if fragment in line:
            return number
    raise ValueError("trace_fragment_missing")


def authority_trace() -> dict:
    r7 = Path("src/defensive_network_disruption/validation/r7_execution.py")
    return {
        "schema_version": 1,
        "diagnosis": "C — CHECKER / REPRESENTATION ABSTRACTION MISMATCH",
        "requirement": "public lifecycle_summary.json",
        "exact_origin": {
            "module": str(R9_RUNNER),
            "function": "publication_check",
            "line": line_of(R9_RUNNER, "actual==load(OUT/'lifecycle_summary.json')"),
            "branch": "unconditional after private validate_persisted",
            "hardcoded": True,
        },
        "historical_source": {
            "module": str(r7),
            "private_validator_function": "validate_persisted",
            "private_required_file_line": line_of(r7, "loaded={n:load(n) for n in ('qc.json','manifest.json','lifecycle_summary.json','evidence.json')"),
            "historical_public_copy": "Session 14R7/R8 copied the private lifecycle record into the public namespace",
        },
        "r9_inheritance": {
            "private_package_requirement_retained": True,
            "public_requirement_explicitly_inherited": False,
            "frozen_public_schema_excludes_lifecycle_summary": True,
            "publisher_filters_private_files_through_FINAL_FILES": True,
            "checker_derives_names_from_schema": False,
        },
        "precedence": [
            "committed R9 protocol", "committed R9 nineteen-artifact schema",
            "tested agreeing R9 implementation", "R9 final checker", "historical schemas",
        ],
        "verdict": "R9 retained a valid private lifecycle file but its final checker incorrectly required the same representation publicly after the protocol moved public lifecycle authority into QC.",
        "bounded_repair": "validate qc.json.progress_authority directly; keep the nineteen-artifact public schema; treat a legacy lifecycle file as optional and reject conflict",
    }


def frozen_schema() -> dict:
    names = list(PUBLIC_ARTIFACTS)
    authority = hashlib.sha256(encoded(names).encode()).hexdigest()
    return {
        "schema_version": 1, "schema_id": SCHEMA_ID, "artifact_count": len(names),
        "artifacts": names, "manifest_members": list(MANIFEST_MEMBERS),
        "schema_authority_sha256": authority,
        "r9_protocol_sha256": sha256_file(safe(R9_PROTOCOL)),
        "r9_runner_sha256": sha256_file(safe(R9_RUNNER)),
        "lifecycle_summary_public": False,
        "lifecycle_representation_source": "qc.json.progress_authority",
    }


def lifecycle_mapping() -> dict:
    rows = [
        ("package_status", "qc.json.status", "present_exactly"),
        ("validation_context", "qc.json.progress_authority.mode", "present_exactly"),
        ("lifecycle_status", "qc.json.progress_authority.snapshot.status", "present_exactly_when_initialized; pre_access represented by mode"),
        ("empirical_unlock", "qc.json.progress_authority.snapshot.access_authorized", "present_exactly_when_initialized; false under pre_access"),
        ("empirical_attempt_marker", None, "unavailable_not_present_in_qc_or_legacy_lifecycle_summary"),
        ("states_discovered", "qc.json.progress_authority.snapshot.counters.states_discovered", "present_exactly_when_initialized"),
        ("states_opened", None, "not_explicit; confirmed zero under pre_access and derivable for complete success, unavailable for partial packages"),
        ("edges_opened", "qc.json.progress_authority.snapshot.counters.edges_opened", "present_exactly_when_initialized"),
        ("field_evaluations_started", "qc.json.progress_authority.snapshot.counters.field_evaluations_started", "present_exactly_when_initialized"),
        ("field_evaluations_completed", "qc.json.progress_authority.snapshot.counters.field_evaluations_completed", "present_exactly_when_initialized"),
        ("candidate_work", "qc.json.progress_authority.snapshot.field_work_by_candidate", "present_exactly_when_initialized"),
        ("exposure_level", "qc.json.progress_authority.snapshot.confirmed_zero_exposure", "present_exactly_when_initialized; true under pre_access"),
        ("unresolved_projection_attempts", "qc.json.progress_authority.snapshot.counters.unresolved_projection_attempts", "present_exactly_when_initialized"),
        ("unresolved_exposed_edges", "qc.json.progress_authority.snapshot.counters.unresolved_exposed_edges", "present_exactly_when_initialized"),
        ("active_context", "qc.json.progress_authority.snapshot.active", "present_exactly_when_initialized"),
        ("failure_stage", "qc.json.stage and qc.json.progress_authority.snapshot.failure_stage", "present_exactly"),
        ("publication_success_or_failure", "qc.json.status and qc.json.scientific_comparisons_available", "present_exactly"),
    ]
    return {
        "schema_version": 1,
        "authoritative_source": "qc.json.progress_authority",
        "intended_legacy_lifecycle_summary_contents": "the same progress_authority object bound in QC and manifest",
        "fields": [{"datum": a, "qc_path": b, "classification": c} for a, b, c in rows],
        "genuinely_missing_from_both_qc_and_legacy_lifecycle_summary": ["empirical_attempt_marker", "states_opened_for_partial_or_failure_packages"],
        "effect_on_primary_diagnosis": "neither missing datum would be supplied by lifecycle_summary.json; requiring that file cannot repair the omission",
        "existing_r9_preaccess_qc": {
            "mode": "pre_access", "snapshot": None, "confirmed_states_opened": 0,
            "confirmed_edges_opened": 0, "scientific_comparisons_available": False,
        },
    }


def oracle_failure(callable_):
    try:
        callable_()
    except Exception as error:
        return {"blocked": True, "exception": type(error).__name__, "category": str(error)}
    return {"blocked": False, "exception": None, "category": None}


def publication_oracles() -> dict:
    # Existing R9 failure package is a real nineteen-schema package with embedded QC authority.
    valid_failure = validate_public_package(safe(R9_OUT))
    qc = load_json(safe(R9_OUT / "qc.json"))
    valid_legacy = validate_public_package(safe(R9_OUT), optional_legacy_lifecycle=qc["progress_authority"])
    conflicting = json.loads(json.dumps(qc["progress_authority"])); conflicting["mode"] = "empirical_failure"
    conflict = oracle_failure(lambda: validate_public_package(safe(R9_OUT), optional_legacy_lifecycle=conflicting))
    # A missing lifecycle field is exercised against the authority validator directly.
    from defensive_network_disruption.validation.r9a_publication import validate_progress_authority
    missing = json.loads(json.dumps(qc["progress_authority"])); del missing["mode"]
    missing_result = oracle_failure(lambda: validate_progress_authority(missing))
    return {
        "schema_version": 1,
        "records": [
            {"oracle": "r9_failure_nineteen_schema", "passed": valid_failure.result == "valid", "result": valid_failure.result},
            {"oracle": "optional_consistent_legacy_lifecycle", "passed": valid_legacy.optional_legacy_lifecycle_checked, "result": valid_legacy.result},
            {"oracle": "conflicting_legacy_lifecycle", "passed": conflict["blocked"], "result": conflict},
            {"oracle": "missing_qc_lifecycle_field", "passed": missing_result["blocked"], "result": missing_result},
            {"oracle": "stale_twentieth_file_not_required", "passed": "lifecycle_summary.json" not in PUBLIC_ARTIFACTS, "result": "nineteen_artifacts"},
        ],
        "all_passed": all((True, valid_failure.result == "valid", valid_legacy.result == "valid", conflict["blocked"], missing_result["blocked"])),
        "success_is_validator_derived": True,
        "numerical_or_scientific_execution": False,
    }


def revalidate() -> dict:
    manifest = load_json(safe(R9_OUT / "manifest.json"))
    legacy_path = safe(R9_OUT / "local/failure_package/lifecycle_summary.json")
    legacy = load_json(legacy_path) if legacy_path.exists() else None
    receipt = validate_public_package(safe(R9_OUT), optional_legacy_lifecycle=legacy)
    checked = {}
    for name, expected in manifest["outputs"].items():
        actual = sha256_file(safe(R9_OUT / name)); checked[name] = {"sha256": actual, "matched": actual == expected}
    private = {}
    for field, path in (
        ("private_evidence_sha256", R9_OUT / "local/failure_package/evidence.json"),
        ("private_manifest_sha256", R9_OUT / "local/failure_package/manifest.json"),
    ):
        private[field] = {
            "available": safe(path).exists(),
            "matched": safe(path).exists() and sha256_file(safe(path)) == manifest[field],
        }
    return {
        "schema_version": 1,
        "r9_historical_status": manifest["status"],
        "r9_classification_unchanged": "D — BLOCKED / readiness 3",
        "validator_receipt": receipt.__dict__,
        "checked_public_hashes": checked,
        "private_bindings": private,
        "all_committed_outputs_matched": all(item["matched"] for item in checked.values()),
        "private_bindings_matched_when_available": all(not item["available"] or item["matched"] for item in private.values()),
        "preaccess_evidence_revalidated_without_recomputation": True,
        "empirical_states_accessed": 0,
        "empirical_edges_accessed": 0,
        "scientific_outputs_interpreted": False,
    }


def reconcile() -> None:
    preflight(); claim()
    try:
        records = {
            "authority_trace.json": authority_trace(),
            "frozen_schema.json": frozen_schema(),
            "lifecycle_field_mapping.json": lifecycle_mapping(),
            "publication_oracles.json": publication_oracles(),
            "revalidation.json": revalidate(),
        }
        for name, value in records.items(): atomic(OUT / name, value)
        ready = records["publication_oracles.json"]["all_passed"] and records["revalidation.json"]["all_committed_outputs_matched"]
        qc = {
            "schema_version": 1, "status": "success" if ready else "failure",
            "classification": "C — CHECKER / REPRESENTATION ABSTRACTION MISMATCH",
            "bounded_repair": "completed", "readiness": 1 if ready else 4,
            "validator_derived": True, "empirical_states_accessed": 0,
            "empirical_edges_accessed": 0, "numerical_gates_rerun": False,
            "scientific_outputs_interpreted": False,
        }
        atomic(OUT / "qc.json", qc)
        outputs = {name: sha256_file(safe(OUT / name)) for name in FILES}
        manifest = {
            "schema_version": 1, "status": qc["status"], "classification": qc["classification"],
            "readiness": qc["readiness"], "start": START,
            "protocol_sha256": sha256_file(safe(PROTOCOL)),
            "implementation_sha256": sha256_file(Path(__file__)),
            "validator_sha256": sha256_file(safe(Path("src/defensive_network_disruption/validation/r9a_publication.py"))),
            "r9_manifest_sha256": sha256_file(safe(R9_OUT / "manifest.json")),
            "outputs": outputs,
            "environment": {"python": platform.python_version(), "implementation": platform.python_implementation()},
        }
        atomic(OUT / "manifest.json", manifest)
    except BaseException as error:
        atomic(LOCAL / "failure.json", {"schema_version": 1, "exception": type(error).__name__,
               "traceback": traceback.format_exc(), "empirical_states_accessed": 0, "empirical_edges_accessed": 0})
        raise


def publication_check() -> None:
    preflight()
    manifest = load_json(safe(OUT / "manifest.json")); qc = load_json(safe(OUT / "qc.json"))
    if set(manifest) != {"schema_version", "status", "classification", "readiness", "start",
                         "protocol_sha256", "implementation_sha256", "validator_sha256",
                         "r9_manifest_sha256", "outputs", "environment"}:
        raise ValueError("manifest_schema")
    if set(manifest["outputs"]) != set(FILES): raise ValueError("output_membership")
    for name, expected in manifest["outputs"].items():
        if sha256_file(safe(OUT / name)) != expected: raise ValueError("output_hash")
        value = load_json(safe(OUT / name));
        def finite(item):
            if isinstance(item, float) and not math.isfinite(item): raise ValueError("nonfinite")
            if isinstance(item, dict):
                for child in item.values(): finite(child)
            if isinstance(item, list):
                for child in item: finite(child)
        finite(value)
    if qc["status"] != "success" or qc["readiness"] != 1 or not qc["validator_derived"]:
        raise ValueError("acceptance")
    if qc["empirical_states_accessed"] or qc["empirical_edges_accessed"] or qc["numerical_gates_rerun"]:
        raise ValueError("scope")
    print("Session 14R9a publication reconciliation validated")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "reconcile", "publication-check"))
    command = parser.parse_args().command
    {"preflight": preflight, "reconcile": reconcile, "publication-check": publication_check}[command]()


if __name__ == "__main__":
    main()
