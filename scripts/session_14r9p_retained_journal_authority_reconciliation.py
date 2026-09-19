#!/usr/bin/env python3
"""Single-use, metadata-only Session 14R9P reconciliation runner."""
from __future__ import annotations

import argparse
import csv
from dataclasses import replace
import hashlib
import io
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import traceback


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/continuous_occlusion_retained_journal_authority"
PROTOCOL = "docs/protocols/phase_14r9p_retained_journal_authority_reconciliation.md"
START = "88e9e2d2d0d95f7da8574dd23b21ac015251e74d"
RELEASE = "f00690c05d8c1c6db308a65bd311c43f9a8ef2fa"
R9I_LOCAL = ROOT / "outputs/continuous_occlusion_empirical_retry_r9i/local"
R9N_LOCAL = ROOT / "outputs/continuous_occlusion_empirical_retry_r9n/local"
NAMES = (
    "reconciliation_contract.json",
    "count_provenance.json",
    "journal_structure_delta.csv",
    "r9n_validation.json",
    "r9i_regression.json",
    "negative_controls.csv",
    "qc.json",
    "manifest.json",
)


def canonical(value) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_once(path: Path, raw: bytes) -> None:
    path = Path(path)
    if any(item.is_symlink() for item in (path, *path.parents)):
        raise PermissionError("symlink_rejected")
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_name("." + path.name + ".pending")
    with pending.open("xb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    os.link(pending, path)
    pending.unlink()
    directory = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def put(path: Path, value) -> None:
    write_once(path, canonical(value))


def git(*arguments: str) -> str:
    return subprocess.check_output(("git", *arguments), cwd=ROOT, text=True).strip()


def bindings() -> dict[str, str]:
    text = (ROOT / PROTOCOL).read_text()
    return json.loads(text.split("```json\n", 1)[1].split("\n```", 1)[0])


def preflight(folder: Path = OUT) -> dict:
    if git("status", "--porcelain"):
        raise RuntimeError("dirty_tree")
    git("merge-base", "--is-ancestor", START, "HEAD")
    if git("rev-parse", "v0.1.0^{}") != RELEASE:
        raise RuntimeError("release_target")
    if Path(sys.prefix).resolve() != (ROOT / ".venv").resolve():
        raise RuntimeError("project_environment")
    for path, expected in bindings().items():
        if sha(ROOT / path) != expected:
            raise RuntimeError("inherited_authority_hash")
    sources = git("ls-files", "*r9p*", PROTOCOL).splitlines()
    for path in sources:
        if subprocess.check_output(("git", "show", "HEAD:" + path), cwd=ROOT) != (ROOT / path).read_bytes():
            raise RuntimeError("uncommitted_implementation")
    if (Path(folder) / "local/reconcile.marker").exists():
        raise FileExistsError("reconciliation_already_reserved")
    return {
        "head": git("rev-parse", "HEAD"),
        "protocol_sha256": sha(ROOT / PROTOCOL),
        "implementation": {path: sha(ROOT / path) for path in sources},
        "release": RELEASE,
    }


def _synthetic_descriptor(folder: Path):
    from defensive_network_disruption.validation import r9j_linear_publication as linear
    from defensive_network_disruption.validation.r9p_retained_authority import RetainedJournalDescriptor

    rows = linear.fixture("failure")
    journal = folder / "journal.jsonl"
    trace = folder / "traceback.txt"
    linear.write_records(journal, rows)
    trace.write_bytes(linear.TRACE)
    descriptor = RetainedJournalDescriptor(
        "synthetic_negative_control",
        sha(journal),
        hashlib.sha256(linear.TRACE).hexdigest(),
        ("0", "1", "constant_width", "onset_adaptive", "GateFailure"),
        "0",
        "0",
    )
    return rows, journal, trace, descriptor


def negative_controls() -> list[dict]:
    from defensive_network_disruption.validation import r9p_retained_authority as retained
    from defensive_network_disruption.validation.state_lifecycle import canonical_bytes

    rows = []
    fixtures = (
        "correct_count_wrong_hash",
        "tampered_record",
        "truncated_journal",
        "appended_record",
        "broken_chain",
        "wrong_terminal_failure",
        "wrong_traceback",
        "missing_receipt",
        "supplied_count_override",
    )
    for fixture in fixtures:
        with tempfile.TemporaryDirectory() as name:
            records, journal, trace, descriptor = _synthetic_descriptor(Path(name).resolve())
            if fixture == "correct_count_wrong_hash":
                descriptor = replace(descriptor, raw_sha256="0" * 64)
            elif fixture == "tampered_record":
                lines = journal.read_bytes().splitlines(keepends=True)
                record = json.loads(lines[0]); record["payload"]["synthetic"] = True
                lines[0] = canonical_bytes(record); journal.write_bytes(b"".join(lines))
            elif fixture == "truncated_journal":
                journal.write_bytes(b"".join(journal.read_bytes().splitlines(keepends=True)[:-1]))
                descriptor = replace(descriptor, raw_sha256=sha(journal))
            elif fixture == "appended_record":
                lines = journal.read_bytes().splitlines(keepends=True); journal.write_bytes(b"".join(lines) + lines[-1])
                descriptor = replace(descriptor, raw_sha256=sha(journal))
            elif fixture == "broken_chain":
                lines = journal.read_bytes().splitlines(keepends=True)
                record = json.loads(lines[1]); record["previous"] = "0" * 64
                lines[1] = canonical_bytes(record); journal.write_bytes(b"".join(lines))
                descriptor = replace(descriptor, raw_sha256=sha(journal))
            elif fixture == "wrong_terminal_failure":
                descriptor = replace(descriptor, terminal=("0", "1", "constant_width", "routing", "GateFailure"))
            elif fixture == "wrong_traceback":
                descriptor = replace(descriptor, traceback_sha256="0" * 64)
            elif fixture == "missing_receipt":
                descriptor = replace(descriptor, selected_edge="missing")
            retained.REGISTRY[descriptor.authority_id] = descriptor
            try:
                if fixture == "supplied_count_override":
                    retained.review_registered(journal, trace, descriptor, expected_count=len(records))
                else:
                    retained.review_registered(journal, trace, descriptor)
            except BaseException as error:
                rows.append({"fixture": fixture, "status": "blocked", "blocked": True, "reason": type(error).__name__})
            else:
                rows.append({"fixture": fixture, "status": "accepted", "blocked": False, "reason": "not_blocked"})
            finally:
                retained.REGISTRY.pop(descriptor.authority_id, None)
    return rows


def _provenance() -> dict:
    r9i_report = subprocess.check_output(("git", "show", "137b7cc2109fc18f1efe203c715484a547a287c6:docs/session_14r9i_empirical_execution.md"), cwd=ROOT, text=True)
    r9j_protocol = subprocess.check_output(("git", "show", "cd2775b7d098e6aca231bf7962e16b2e51d80e29:docs/protocols/phase_14r9j_r9i_blocker_diagnosis.md"), cwd=ROOT, text=True)
    r9o_protocol = subprocess.check_output(("git", "show", "49eaa2deec3b15df946361a2d395679a8c1fc464:docs/protocols/phase_14r9o_switch_equality_failure_diagnosis.md"), cwd=ROOT, text=True)
    r9n_protocol = (ROOT / "docs/protocols/phase_14r9n_empirical_representation_retry.md").read_text()
    r9n_report = (ROOT / "docs/session_14r9n_empirical_representation_retry.md").read_text()
    return {
        "schema_version": 1,
        "count_30881": {
            "origin": "R9I_RETAINED_JOURNAL",
            "source_file": "docs/session_14r9i_empirical_execution.md",
            "source_commit": "137b7cc2109fc18f1efe203c715484a547a287c6",
            "r9i_report_asserted": "30,881" in r9i_report,
            "r9j_protocol_bound": "30,881" in r9j_protocol,
            "copied_to_r9o_protocol": "30,881" in r9o_protocol,
            "asserted_by_r9n_protocol": "30,881" in r9n_protocol,
            "asserted_by_r9n_report": "30,881" in r9n_report,
        },
        "count_31161": {
            "origin": "DERIVED_FROM_HASH_VERIFIED_R9N_JOURNAL",
            "prior_observation_commit": "88e9e2d2d0d95f7da8574dd23b21ac015251e74d",
            "r9n_report_binds_raw_hash": "ab5600ba8eea54092996bb2f4c613c76a5ba331c25c2c9d2b7bb65fa6e9555db" in r9n_report,
        },
    }


def _public_validation(authority) -> dict:
    value = authority.record()
    counters = value["counters"]
    return {
        "schema_version": 1,
        "status": "valid",
        "flags": {
            "raw_hash_valid": True,
            "canonical_encoding_valid": value["canonical_encoding_valid"],
            "sequence_valid": value["sequence_valid"],
            "chain_valid": value["chain_valid"],
            "terminal_failure_context_valid": True,
            "traceback_binding_valid": value["traceback_valid"],
            "selected_receipt_valid": True,
            "lifecycle_valid": True,
        },
        "counts": {
            "derived_records": value["derived_record_count"],
            "states_opened": counters["states_discovered"],
            "edges_opened": counters["edges_opened"],
            "states_completed": counters["states_completed"],
            "edges_completed": counters["edges_completed"],
            "candidate_starts": counters["field_evaluations_started"],
            "candidate_completions": counters["field_evaluations_completed"],
        },
        "raw_sha256": value["raw_sha256"],
        "chain_head_sha256": value["chain_head_sha256"],
        "authority_receipt_sha256": authority.sha256,
        "count_role": value["count_role"],
    }


def _csv_bytes(rows: list[dict], fields: list[str]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: str(value).lower() if isinstance(value, bool) else value for key, value in row.items()})
    return output.getvalue().encode()


def _close(folder: Path, public: dict, delta: list[dict], controls: list[dict], private_hashes: dict, environment: dict) -> None:
    local = folder / "local"
    put(local / "private_index.json", private_hashes)
    public["journal_structure_delta.csv"] = _csv_bytes(delta, ["action", "r9i_count", "r9n_count", "delta", "explanation"])
    public["negative_controls.csv"] = _csv_bytes(controls, ["fixture", "status", "blocked", "reason"])
    for name in NAMES:
        if name == "manifest.json":
            continue
        value = public[name]
        if isinstance(value, bytes):
            write_once(folder / name, value)
        else:
            put(folder / name, value)
    outputs = {name: sha(folder / name) for name in NAMES if name != "manifest.json"}
    manifest = {
        "schema_version": 1,
        "protocol_sha256": environment["protocol_sha256"],
        "implementation": environment["implementation"],
        "outputs": outputs,
        "private_index_sha256": sha(local / "private_index.json"),
    }
    put(folder / "manifest.json", manifest)


def reconcile(folder: Path = OUT) -> dict:
    environment = preflight(folder)
    folder = Path(folder); local = folder / "local"
    put(local / "reconcile.marker", {"reserved": True, "authorizes_empirical_access": False})
    private_hashes = {"reconcile.marker": sha(local / "reconcile.marker")}
    public = {}
    delta_rows: list[dict] = []
    controls: list[dict] = []
    try:
        from defensive_network_disruption.validation.r9p_retained_authority import (
            R9I, R9N, action_delta, review_registered, validate_expected_delta,
        )
        r9i = review_registered(R9I_LOCAL / "journal.jsonl", R9I_LOCAL / "numerical_traceback.txt", R9I)
        r9n = review_registered(R9N_LOCAL / "journal.jsonl", R9N_LOCAL / "numerical_traceback.txt", R9N)
        put(local / "r9i_authority.json", r9i.record()); private_hashes["r9i_authority.json"] = sha(local / "r9i_authority.json")
        put(local / "r9n_authority.json", r9n.record()); private_hashes["r9n_authority.json"] = sha(local / "r9n_authority.json")
        delta_rows = action_delta(r9i, r9n)
        validate_expected_delta(delta_rows)
        explanations = {
            "numerical_stage": "additional_completed_evaluation_work",
            "field_started": "additional_candidate_work",
            "field_completed": "additional_candidate_work",
            "edge_completed": "additional_completed_work",
            "state_completed": "additional_completed_work",
            "state_evaluation_started": "additional_started_work",
        }
        for row in delta_rows:
            row["explanation"] = explanations.get(row["action"], "unchanged_lifecycle_structure")
        controls = negative_controls()
        if not all(row["blocked"] for row in controls):
            raise RuntimeError("negative_control_failure")
        provenance = _provenance()
        if not (
            provenance["count_30881"]["r9i_report_asserted"]
            and provenance["count_30881"]["r9j_protocol_bound"]
            and provenance["count_30881"]["copied_to_r9o_protocol"]
            and not provenance["count_30881"]["asserted_by_r9n_protocol"]
            and not provenance["count_30881"]["asserted_by_r9n_report"]
            and provenance["count_31161"]["r9n_report_binds_raw_hash"]
        ):
            raise RuntimeError("count_provenance")
        public = {
            "reconciliation_contract.json": {
                "schema_version": 1, "status": "valid",
                "authority_semantics": "EXACT_RAW_HASH_CHAIN_TERMINAL_TRACEBACK_AND_RECEIPT",
                "count_role": "CB_DERIVED_CONSISTENCY_FACT",
                "r9o_historical_status": "NF_PD_READINESS_4",
                "empirical_access": {"states": 0, "edges": 0},
            },
            "count_provenance.json": provenance,
            "r9n_validation.json": _public_validation(r9n),
            "r9i_regression.json": _public_validation(r9i),
            "qc.json": {
                "schema_version": 1, "status": "success", "execution_valid": True,
                "r9o_mismatch_classification": "A", "classification": "A", "readiness": 1,
                "states_opened": 0, "edges_opened": 0, "scientific_computation": False,
                "numerical_computation": False, "negative_controls_passed": len(controls),
                "record_delta": r9n.derived_record_count - r9i.derived_record_count,
            },
        }
    except BaseException as error:
        raw = traceback.format_exc().encode()
        write_once(local / "failure_traceback.txt", raw); private_hashes["failure_traceback.txt"] = sha(local / "failure_traceback.txt")
        put(local / "failure.json", {"exception": type(error).__name__, "message": str(error), "traceback_sha256": private_hashes["failure_traceback.txt"]})
        private_hashes["failure.json"] = sha(local / "failure.json")
        public = {
            "reconciliation_contract.json": {"schema_version": 1, "status": "invalid", "authority_semantics": "unavailable", "count_role": "CB_DERIVED_CONSISTENCY_FACT", "r9o_historical_status": "NF_PD_READINESS_4", "empirical_access": {"states": 0, "edges": 0}},
            "count_provenance.json": {"schema_version": 1, "status": "unavailable", "reason": "governed_failure"},
            "r9n_validation.json": {"schema_version": 1, "status": "invalid", "reason": "governed_failure"},
            "r9i_regression.json": {"schema_version": 1, "status": "invalid", "reason": "governed_failure"},
            "qc.json": {"schema_version": 1, "status": "failure", "execution_valid": False, "r9o_mismatch_classification": "E", "classification": "D", "readiness": 4, "states_opened": 0, "edges_opened": 0, "scientific_computation": False, "numerical_computation": False, "negative_controls_passed": sum(row.get("blocked", False) for row in controls), "record_delta": 0},
        }
    _close(folder, public, delta_rows, controls, private_hashes, environment)
    return publication_check(folder)


def publication_check(folder: Path = OUT) -> dict:
    folder = Path(folder)
    if {path.name for path in folder.iterdir() if path.is_file()} != set(NAMES):
        raise ValueError("public_inventory")
    manifest = json.loads((folder / "manifest.json").read_text())
    if set(manifest) != {"schema_version", "protocol_sha256", "implementation", "outputs", "private_index_sha256"} or manifest["schema_version"] != 1:
        raise ValueError("manifest_schema")
    if set(manifest["outputs"]) != set(NAMES) - {"manifest.json"}:
        raise ValueError("manifest_inventory")
    for name, expected in manifest["outputs"].items():
        if sha(folder / name) != expected:
            raise ValueError("public_hash")
        if name.endswith(".json"):
            json.loads((folder / name).read_text(), parse_constant=lambda value: (_ for _ in ()).throw(ValueError("nonfinite_json")))
    private_index = folder / "local/private_index.json"
    if sha(private_index) != manifest["private_index_sha256"]:
        raise ValueError("private_index_hash")
    for name, expected in json.loads(private_index.read_text()).items():
        if Path(name).name != name or sha(folder / "local" / name) != expected:
            raise ValueError("private_evidence_hash")
    with (folder / "negative_controls.csv").open(newline="") as handle:
        negative = list(csv.DictReader(handle))
    with (folder / "journal_structure_delta.csv").open(newline="") as handle:
        delta = list(csv.DictReader(handle))
    qc = json.loads((folder / "qc.json").read_text())
    if qc["status"] == "success":
        if qc["classification"] != "A" or qc["readiness"] != 1 or qc["r9o_mismatch_classification"] != "A":
            raise ValueError("false_classification")
        if not negative or not all(row["blocked"] == "true" for row in negative):
            raise ValueError("negative_controls")
        if sum(int(row["delta"]) for row in delta) != 280 or qc["record_delta"] != 280:
            raise ValueError("record_delta")
        if qc["states_opened"] or qc["edges_opened"] or qc["scientific_computation"] or qc["numerical_computation"]:
            raise ValueError("scope_violation")
    return {"valid": True, "status": qc["status"], "classification": qc["classification"], "readiness": qc["readiness"], "files": len(NAMES)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "reconcile", "publication-check"))
    arguments = parser.parse_args()
    if arguments.command == "preflight":
        result = preflight()
    elif arguments.command == "reconcile":
        result = reconcile()
    else:
        result = publication_check()
    print(json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False))


if __name__ == "__main__":
    main()
