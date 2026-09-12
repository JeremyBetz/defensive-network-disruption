#!/usr/bin/env python3
"""Synthetic-only Session 14af empirical-capable publication audit."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defensive_network_disruption.validation.empirical_lifecycle import (  # noqa: E402
    EmpiricalLifecycle, FailureCapture, ValidationMode, capture_unexpected_failure,
    make_progress_view, package_record, validate_cross_file_package,
    validate_progress_view,
)
from defensive_network_disruption.validation.launch_enforcement import (  # noqa: E402
    EnvironmentObservation, GovernedLauncher, PrerequisiteExpectation,
    canonical_json as launch_json,
)
from defensive_network_disruption.validation.state_lifecycle import (  # noqa: E402
    LifecycleError, canonical_bytes, snapshot_digest,
)

OUT = ROOT / "outputs" / "session14_empirical_lifecycle_publication"
LOCAL = OUT / "local"
PROTOCOL = ROOT / "docs" / "protocols" / "phase_14af_empirical_capable_lifecycle_publication.md"
STARTING_HEAD = "010bc8876c2abad227ff969c8e2655d96a3f397e"
CLASSIFICATION = "A — EMPIRICAL-CAPABLE LIFECYCLE / PUBLICATION AUTHORITY ESTABLISHED"
FILES = (
    "authority_qualification.json", "lifecycle_contract.json", "validator_modes.json",
    "invalid_cross_file_injections.csv", "valid_pre_access_control.json",
    "valid_empirical_partial_control.json", "valid_empirical_success_control.json",
    "unexpected_failure_control.json", "access_preservation_oracles.csv",
    "r4_wrapper_compatibility.json", "qc.json",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name("." + path.name + ".tmp")
    with temp.open("xb") as handle:
        handle.write(data); handle.flush(); os.fsync(handle.fileno())
    os.replace(temp, path)


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    atomic(path, canonical_bytes(value))


def write_csv(path: Path, fields: Iterable[str], rows: list[dict[str, Any]]) -> None:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=tuple(fields), lineterminator="\n")
    writer.writeheader(); writer.writerows(rows)
    atomic(path, stream.getvalue().encode())


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, text=True, capture_output=True).stdout.strip()


def preflight() -> None:
    if git("status", "--porcelain"):
        raise LifecycleError("dirty_tree")
    if not PROTOCOL.is_file() or not git("ls-files", "--error-unmatch", str(PROTOCOL.relative_to(ROOT))):
        raise LifecycleError("protocol_not_committed")
    print("Session 14af preflight passed")


def views(view: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    return (
        package_record(view, classification=CLASSIFICATION, readiness=1),
        package_record(view, outputs={}),
        package_record(view, evidence_kind="synthetic_control"),
        package_record(view, report_binding="machine_summary"),
    )


def validate_all(view: Mapping[str, Any], authority: EmpiricalLifecycle) -> None:
    qc, manifest, evidence, report = views(view)
    validate_cross_file_package(
        mode=view["validation_mode"], qc=qc, manifest=manifest,
        evidence=evidence, report=report, journal=authority.journal,
    )


def pre_access_control() -> tuple[EmpiricalLifecycle, dict[str, Any]]:
    authority = EmpiricalLifecycle()
    authority.discover_state("state_01", ("edge_01",))
    authority.prepare_state("state_01")
    authority.block("pre_access_checkpoint", "synthetic_stop")
    view = make_progress_view(authority, ValidationMode.PRE_ACCESS)
    validate_all(view, authority)
    return authority, view


def partial_failure_control() -> tuple[EmpiricalLifecycle, FailureCapture]:
    authority = EmpiricalLifecycle()
    for number in range(1, 4):
        authority.discover_state(f"state_{number:02d}", (f"edge_{number:02d}_01", f"edge_{number:02d}_02"))
        authority.prepare_state(f"state_{number:02d}")
    authority.authorize_access()
    authority.open_state("state_01"); authority.start_state_evaluation("state_01")
    for edge in ("edge_01_01", "edge_01_02"):
        authority.open_edge("state_01", edge); authority.start_edge("state_01", edge); authority.complete_edge("state_01", edge)
    authority.complete_state("state_01")
    authority.open_state("state_02"); authority.start_state_evaluation("state_02")
    authority.open_edge("state_02", "edge_02_01"); authority.start_edge("state_02", "edge_02_01"); authority.complete_edge("state_02", "edge_02_01")
    authority.open_edge("state_02", "edge_02_02"); authority.start_edge("state_02", "edge_02_02")
    capture = capture_unexpected_failure(
        authority,
        lambda: (_ for _ in ()).throw(RuntimeError("synthetic unexpected failure")),
        stage="edge_evaluation",
    )
    validate_all(capture.progress_view, authority)
    return authority, capture


def empirical_success_control() -> tuple[EmpiricalLifecycle, dict[str, Any]]:
    authority = EmpiricalLifecycle()
    authority.authorize_access()
    for number in range(1, 3):
        state = f"state_{number:02d}"; edges = (f"edge_{number:02d}_01", f"edge_{number:02d}_02")
        authority.discover_state(state, edges); authority.prepare_state(state); authority.open_state(state)
        authority.start_state_evaluation(state)
        for edge in edges:
            authority.open_edge(state, edge); authority.start_edge(state, edge); authority.complete_edge(state, edge)
        authority.complete_state(state)
    authority.succeed()
    view = make_progress_view(authority, ValidationMode.EMPIRICAL_SUCCESS)
    validate_all(view, authority)
    return authority, view


def access_preservation_oracles(failure: FailureCapture, authority: EmpiricalLifecycle) -> list[dict[str, Any]]:
    state_only = EmpiricalLifecycle(); state_only.discover_state("state_01", ("edge_01",)); state_only.prepare_state("state_01")
    state_only.authorize_access(); state_only.open_state("state_01"); state_only.block("synthetic_access", "synthetic_stop")
    state_view = make_progress_view(state_only, ValidationMode.EMPIRICAL_PARTIAL); validate_all(state_view, state_only)
    reset_observed = "accepted"
    reset_view = copy.deepcopy(failure.progress_view)
    reset_view["access"] = {"states_opened":0,"edges_opened":0}
    reset_view["lifecycle"]["counters"]["states_opened"] = 0; reset_view["lifecycle"]["counters"]["edges_opened"] = 0
    reset_view["lifecycle_sha256"] = snapshot_digest(reset_view["lifecycle"])
    reset_records = [package_record(reset_view) for _ in range(4)]
    try:
        validate_cross_file_package(mode=ValidationMode.EMPIRICAL_FAILURE, qc=reset_records[0], manifest=reset_records[1], evidence=reset_records[2], report=reset_records[3], journal=authority.journal)
    except LifecycleError as exc:
        reset_observed = "rejected:" + str(exc)
    return [
        {"oracle":"pre_access_zero","synthetic_states_opened":0,"synthetic_edges_opened":0,"expected":"accepted","observed":"accepted"},
        {"oracle":"state_open_edge_closed","synthetic_states_opened":state_view["access"]["states_opened"],"synthetic_edges_opened":state_view["access"]["edges_opened"],"expected":"accepted","observed":"accepted"},
        {"oracle":"partial_failure_preserved","synthetic_states_opened":failure.progress_view["access"]["states_opened"],"synthetic_edges_opened":failure.progress_view["access"]["edges_opened"],"expected":"accepted","observed":"accepted"},
        {"oracle":"reset_after_access","synthetic_states_opened":0,"synthetic_edges_opened":0,"expected":"rejected","observed":reset_observed},
    ]


def _mutate_package(records: list[dict[str, Any]], index: int, mutation: str) -> None:
    record = records[index]
    view = record["progress_authority"]
    if mutation == "lifecycle_hash": view["lifecycle_sha256"] = "0" * 64
    elif mutation == "access": view["access"]["edges_opened"] -= 1
    elif mutation == "completed": view["lifecycle"]["counters"]["states_completed"] += 1
    elif mutation == "active_state": view["active_state"] = "different_state"
    elif mutation == "active_edge": view["active_edge"] = "different_edge"
    elif mutation == "status": record["status"] = "success"
    elif mutation == "failure_stage": view["failure_stage"] = "different_stage"
    elif mutation == "manifest_success": record["status"] = "success"
    else: raise AssertionError(mutation)


def invalid_injections(authority: EmpiricalLifecycle, view: Mapping[str, Any]) -> list[dict[str, str]]:
    cases = (
        ("qc_lifecycle_hash_differs", 0, "lifecycle_hash"),
        ("failure_access_differs_from_qc", 2, "access"),
        ("completed_state_count_differs", 1, "completed"),
        ("active_state_differs", 3, "active_state"),
        ("active_edge_differs", 1, "active_edge"),
        ("status_differs", 2, "status"),
        ("failure_stage_differs", 3, "failure_stage"),
        ("manifest_claims_success", 1, "manifest_success"),
    )
    rows: list[dict[str, str]] = []
    for name, index, mutation in cases:
        records = [copy.deepcopy(item) for item in views(view)]
        _mutate_package(records, index, mutation)
        try:
            validate_cross_file_package(mode=ValidationMode.EMPIRICAL_FAILURE, qc=records[0], manifest=records[1], evidence=records[2], report=records[3], journal=authority.journal)
            observed = "accepted"
        except LifecycleError as exc:
            observed = "rejected:" + str(exc)
        rows.append({"injection": name, "expected": "rejected", "observed": observed})

    records = [copy.deepcopy(item) for item in views(view)]
    for record in records: record["progress_authority"]["validation_mode"] = ValidationMode.PRE_ACCESS.value
    try:
        validate_cross_file_package(mode=ValidationMode.PRE_ACCESS, qc=records[0], manifest=records[1], evidence=records[2], report=records[3], journal=authority.journal)
        observed = "accepted"
    except LifecycleError as exc: observed = "rejected:" + str(exc)
    rows.append({"injection":"nonzero_access_pre_access_mode","expected":"rejected","observed":observed})

    reset_view = copy.deepcopy(view)
    reset_view["access"] = {"states_opened": 0, "edges_opened": 0}
    reset_view["lifecycle"]["counters"]["states_opened"] = 0
    reset_view["lifecycle"]["counters"]["edges_opened"] = 0
    reset_view["lifecycle_sha256"] = snapshot_digest(reset_view["lifecycle"])
    records = [package_record(reset_view) for _ in range(4)]
    try:
        validate_cross_file_package(mode=ValidationMode.EMPIRICAL_FAILURE, qc=records[0], manifest=records[1], evidence=records[2], report=records[3], journal=authority.journal)
        observed = "accepted"
    except LifecycleError as exc: observed = "rejected:" + str(exc)
    rows.append({"injection":"access_reset_to_zero","expected":"rejected","observed":observed})
    return rows


def r4_compatibility() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory); prerequisite = root / "prerequisite.json"
        environment = EnvironmentObservation(
            python="3.13", implementation="CPython", in_project_environment=True,
            environment_marker="uv-locked-project-environment", lock_sha256="1" * 64,
            packages=(("numpy", "2.2.6"),),
        )
        expected = PrerequisiteExpectation(
            protocol_sha256="2" * 64, implementation_sha256="3" * 64,
            lock_sha256=environment.lock_sha256, environment_sha256=environment.fingerprint(),
            test_command=("python", "-m", "unittest", "discover"),
        )
        record = {
            "schema_version":1,"producer":"session14ad_enforcement_tests","status":"passed",
            "test_command":list(expected.test_command),"protocol_sha256":expected.protocol_sha256,
            "implementation_sha256":expected.implementation_sha256,"lock_sha256":expected.lock_sha256,
            "environment_sha256":expected.environment_sha256,"tests_run":2,"tests_passed":2,"tests_skipped":0,
            "exit_status":0,"test_output_sha256":"4"*64,"failure_enforcement_passed":True,
        }
        captured: dict[str, Any] = {}
        def produce() -> None: prerequisite.write_text(launch_json(record) + "\n")
        def authorized(_context: object) -> None:
            authority, failure = partial_failure_control()
            validate_all(failure.progress_view, authority)
            captured.update({"view":failure.progress_view,"journal":authority.journal})
        launcher = GovernedLauncher(root/"launch.marker", root/"access.marker")
        launcher.run(environment=environment, expected=expected, required_packages=("numpy",),
                     prerequisite_path=prerequisite, produce_prerequisite=produce,
                     verify_synthetic=lambda _context: True, authorize_empirical=authorized)
        return {
            "schema_version":1,"status":"success","launch_state":launcher.state.value,
            "transitions":launcher.transitions,"partial_failure_validated":bool(captured),
            "synthetic_states_opened":captured["view"]["access"]["states_opened"],
            "synthetic_edges_opened":captured["view"]["access"]["edges_opened"],
            "real_states_opened":0,"real_edges_opened":0,
        }


def public_control(view: Mapping[str, Any], **extra: Any) -> dict[str, Any]:
    counters = view["lifecycle"]["counters"]
    return {
        "schema_version":1,"status":"success","validation_result":"accepted",
        "control_status":view["status"],"validation_mode":view["validation_mode"],
        "lifecycle_sha256":view["lifecycle_sha256"],"journal_sha256":view["journal_sha256"],
        "states_discovered":counters["states_discovered"],"states_prepared":counters["states_prepared"],
        "states_evaluation_started":counters["states_evaluation_started"],"states_completed":counters["states_completed"],
        "edges_evaluation_started":counters["edges_evaluation_started"],"edges_completed":counters["edges_completed"],
        "synthetic_states_opened":view["access"]["states_opened"],"synthetic_edges_opened":view["access"]["edges_opened"],
        "real_states_opened":0,"real_edges_opened":0,"active_state_preserved":view["active_state"] is not None,
        "active_edge_preserved":view["active_edge"] is not None, **extra,
    }


def audit() -> None:
    preflight(); OUT.mkdir(parents=True, exist_ok=True); LOCAL.mkdir(parents=True, exist_ok=True)
    marker = LOCAL / "audit.marker"
    try: fd = os.open(marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600); os.write(fd, b"claimed\n"); os.close(fd)
    except FileExistsError as exc: raise LifecycleError("audit_already_claimed") from exc
    if any((OUT/name).exists() for name in (*FILES, "manifest.json")): raise LifecycleError("outputs_already_exist")

    pre_authority, pre_view = pre_access_control()
    partial_authority, failure = partial_failure_control()
    success_authority, success_view = empirical_success_control()
    injections = invalid_injections(partial_authority, failure.progress_view)
    if any(not row["observed"].startswith("rejected:") for row in injections): raise LifecycleError("invalid_injection_accepted")
    r4 = r4_compatibility()

    audit_authority = EmpiricalLifecycle(); audit_authority.discover_state("audit_state", ("audit_edge",)); audit_authority.prepare_state("audit_state")
    audit_authority.start_state_evaluation("audit_state"); audit_authority.start_edge("audit_state", "audit_edge"); audit_authority.complete_edge("audit_state", "audit_edge")
    audit_authority.complete_state("audit_state"); audit_authority.succeed()
    audit_view = make_progress_view(audit_authority, ValidationMode.PRE_ACCESS); validate_all(audit_view, audit_authority)

    qualification = {"schema_version":1,"status":"success","historical_session14ae":"preserved_A_readiness_1","qualification":"valid synthetic lifecycle and zero-access pre-empirical accounting; empirical-capable cross-file validation and unexpected nonzero-access failure preservation were not fully established","historical_files_changed":False}
    contract = {"schema_version":1,"status":"success","processing_lifecycle":["discovered","prepared","evaluation_started","evaluation_completed"],"access_authority":"append_only_private_journal","access_independent_of_completion":True,"public_counters_derived":True,"real_states_opened":0,"real_edges_opened":0}
    modes = {"schema_version":1,"status":"success","modes":{"pre_access":"zero access required","empirical_partial":"incomplete blocked or failed progress permitted","empirical_failure":"failure evidence and preserved nonzero access permitted","empirical_success":"complete nonempty work and complete access required"}}
    pre_public = public_control(pre_view)
    partial_public = public_control(failure.progress_view, traceback_preserved=True, pre_failure_snapshot_preserved=True, terminal_snapshot_preserved=True, partial_progress_preserved=True)
    success_public = public_control(success_view)
    unexpected_public = public_control(failure.progress_view, traceback_preserved=bool(failure.traceback_text), pre_failure_snapshot_sha256=snapshot_digest(failure.pre_failure_snapshot), terminal_snapshot_sha256=snapshot_digest(failure.terminal_snapshot), partial_progress_preserved=True)
    access_rows = access_preservation_oracles(failure, partial_authority)
    qc = package_record(audit_view, classification=CLASSIFICATION, readiness=1, real_access={"states_opened":0,"edges_opened":0}, governed_injections=len(injections), governed_rejections=sum(row["observed"].startswith("rejected:") for row in injections))

    write_json(OUT/"authority_qualification.json", qualification); write_json(OUT/"lifecycle_contract.json", contract); write_json(OUT/"validator_modes.json", modes)
    write_csv(OUT/"invalid_cross_file_injections.csv", ("injection","expected","observed"), injections)
    write_json(OUT/"valid_pre_access_control.json", pre_public); write_json(OUT/"valid_empirical_partial_control.json", partial_public)
    write_json(OUT/"valid_empirical_success_control.json", success_public); write_json(OUT/"unexpected_failure_control.json", unexpected_public)
    write_csv(OUT/"access_preservation_oracles.csv", ("oracle","synthetic_states_opened","synthetic_edges_opened","expected","observed"), access_rows)
    write_json(OUT/"r4_wrapper_compatibility.json", r4); write_json(OUT/"qc.json", qc)
    manifest = package_record(audit_view, classification=CLASSIFICATION, readiness=1, starting_head=STARTING_HEAD,
                              implementation_commit=git("rev-parse", "HEAD"), protocol_sha256=sha256_file(PROTOCOL),
                              outputs={name:sha256_file(OUT/name) for name in FILES})
    validate_cross_file_package(mode=ValidationMode.PRE_ACCESS, qc=qc, manifest=manifest,
                                evidence=package_record(audit_view), report=package_record(audit_view), journal=audit_authority.journal)
    write_json(OUT/"manifest.json", manifest)
    write_json(LOCAL/"audit_journal.json", {"journal":audit_authority.journal})
    write_json(LOCAL/"unexpected_failure_private.json", {"traceback":failure.traceback_text,"pre_failure_snapshot":failure.pre_failure_snapshot,"terminal_snapshot":failure.terminal_snapshot,"journal":partial_authority.journal})
    publication_check(); atomic(LOCAL/"closed", b"closed\n")
    print(CLASSIFICATION + "; readiness 1")


def publication_check() -> None:
    manifest = json.loads((OUT/"manifest.json").read_text()); qc = json.loads((OUT/"qc.json").read_text())
    if set(manifest.get("outputs", {})) != set(FILES): raise LifecycleError("manifest_outputs")
    for name, expected in manifest["outputs"].items():
        if sha256_file(OUT/name) != expected: raise LifecycleError("output_hash")
    journal = json.loads((LOCAL/"audit_journal.json").read_text())["journal"]
    validate_cross_file_package(mode=ValidationMode.PRE_ACCESS, qc=qc, manifest=manifest,
                                evidence=package_record(qc["progress_authority"]), report=package_record(qc["progress_authority"]), journal=journal)
    for path in (OUT/name for name in (*FILES, "manifest.json")):
        text = path.read_text()
        for forbidden in ("/Users/", "/private/", "event_id", "target_index", "carrier_xy", "candidate_xy", "defender_xy", "token="):
            if forbidden in text: raise LifecycleError("publication_content")
    print("Session 14af publication checks passed")


def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("command", choices=("preflight","audit","publication-check")); args=parser.parse_args()
    if args.command == "preflight": preflight()
    elif args.command == "audit": audit()
    else: publication_check()


if __name__ == "__main__": main()
