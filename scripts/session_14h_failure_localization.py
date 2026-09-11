#!/usr/bin/env python3
"""Session 14h synthetic-only governed failure-localization runner."""
from __future__ import annotations

import argparse
import ast
import csv
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np
import scipy

from defensive_network_disruption.geometry.failure_diagnostics import (
    FIXTURE_ORDER,
    DiagnosticFailure,
    run_engineering_diagnostic,
    sanitize_traceback,
)

START = "661f1beaac7eea9d47500747ddd9f2f36b3e8ed5"
TAG = "f00690c05d8c1c6db308a65bd311c43f9a8ef2fa"
PROTOCOL = "docs/protocols/phase_14h_failure_localization.md"
OUT = Path("outputs/continuous_occlusion_failure_localization")
CODE = (
    "scripts/session_14h_failure_localization.py",
    "src/defensive_network_disruption/geometry/failure_diagnostics.py",
    "tests/test_session14h_diagnostics.py",
)
HISTORICAL = (
    "src/defensive_network_disruption/geometry/production_verification.py",
    "src/defensive_network_disruption/geometry/verification_repair.py",
    "scripts/session_14g_production_verification.py",
    "tests/test_session14g_production.py",
    "outputs/continuous_occlusion_production_verification/manifest.json",
    "outputs/continuous_occlusion_production_verification/qc.json",
    "outputs/continuous_occlusion_production_verification/wiring_checks.json",
    "docs/protocols/phase_14g_production_verification_wiring.md",
    "docs/session_14g_production_verification_wiring.md",
    "uv.lock",
)
FILES = (
    "diagnostic_contract.json",
    "engineering_progress.csv",
    "failure_summary.json",
    "qc.json",
)
CSV_FIELDS = (
    "check_index",
    "fixture",
    "passed",
    "reason",
    "permutations_checked",
    "partition_count",
)
LOCALIZED = "LOCALIZED — EXACT TYPEERROR SOURCE ESTABLISHED"
UNRESOLVED = "UNRESOLVED — HISTORICAL FAILURE NOT SUFFICIENTLY LOCALIZED"
INVALID = "INVALID — LOCALIZATION EXECUTION FAILURE"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def safe(relative: str | Path) -> Path:
    relative = Path(relative)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("unsafe_path")
    path = ROOT / relative
    if not path.resolve().is_relative_to(ROOT.resolve()) or any(
        item.is_symlink() for item in (path, *path.parents)
    ):
        raise ValueError("unsafe_path")
    return path


def digest(relative: str | Path) -> str:
    return hashlib.sha256(safe(relative).read_bytes()).hexdigest()


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def read_json(relative: str | Path):
    return json.loads(
        safe(relative).read_text(),
        object_pairs_hook=no_duplicates,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite_json")),
    )


def environment() -> dict:
    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "uv_lock_sha256": digest("uv.lock"),
    }


def atomic_text(relative: str | Path, text: str) -> None:
    path = safe(relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError("artifact_exists")
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    temporary.replace(path)


def write_json(name: str, value) -> None:
    atomic_text(OUT / name, json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def append_jsonl(relative: str | Path, value) -> None:
    path = safe(relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(value, sort_keys=True, allow_nan=False) + "\n")
        handle.flush()


def append_progress(index: int, row: dict) -> None:
    append_jsonl(
        OUT / "local/engineering_progress.jsonl",
        {
            "check_index": index,
            "fixture": row["fixture"],
            "passed": row["passed"],
            "reason": row["reason"],
            "permutations_checked": row["permutations_checked"],
            "partition_count": row["partition_count"],
        },
    )


def ledger(stage: str, status: str) -> None:
    append_jsonl(
        OUT / "local/access.jsonl",
        {
            "time": datetime.now(timezone.utc).isoformat(),
            "stage": stage,
            "status": status,
            "commit": git("rev-parse", "HEAD"),
            "synthetic_only": True,
        },
    )


def historical_preservation() -> None:
    changed = git("diff", "--name-only", START).splitlines()
    allowed = {
        PROTOCOL,
        *CODE,
        "docs/session_14h_failure_localization.md",
        "docs/research_log.md",
    }
    if any(path not in allowed and not path.startswith(str(OUT) + "/") for path in changed):
        raise ValueError("historical_change")
    for path in HISTORICAL:
        prior = subprocess.check_output(["git", "show", f"{START}:{path}"], cwd=ROOT)
        if safe(path).read_bytes() != prior:
            raise ValueError("historical_authority_changed")
    previous_log = subprocess.check_output(
        ["git", "show", f"{START}:docs/research_log.md"], cwd=ROOT
    )
    if not safe("docs/research_log.md").read_bytes().startswith(previous_log):
        raise ValueError("research_log_rewritten")


def route_guard() -> None:
    forbidden = (
        "receiver_ranking",
        "option_network",
        "modeling",
        "acquisition",
        "tracking",
        "requests",
        "urllib",
        "socket",
        "kloppy",
    )
    for path in CODE[:2]:
        tree = ast.parse(safe(path).read_text())
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = (
                    [node.module or ""]
                    if isinstance(node, ast.ImportFrom)
                    else [item.name for item in node.names]
                )
                if any(any(word in name.lower() for word in forbidden) for name in names):
                    raise ValueError("forbidden_import")


def preflight() -> None:
    if git("status", "--porcelain"):
        raise ValueError("unclean_tree")
    if git("rev-parse", "v0.1.0^{}") != TAG:
        raise ValueError("release_tag_changed")
    git("merge-base", "--is-ancestor", START, "HEAD")
    for path in (PROTOCOL, *CODE):
        committed = subprocess.check_output(["git", "show", f"HEAD:{path}"], cwd=ROOT)
        if safe(path).read_bytes() != committed:
            raise ValueError("uncommitted_authority")
    if subprocess.run(
        ["git", "check-ignore", "-q", str(OUT / "local/probe")], cwd=ROOT
    ).returncode:
        raise ValueError("local_storage_not_ignored")
    historical_preservation()
    route_guard()


def begin() -> None:
    if any(safe(OUT / name).exists() for name in (*FILES, "manifest.json")):
        raise FileExistsError("governed_outputs_exist")
    marker = safe(OUT / "local/execution.marker")
    marker.parent.mkdir(parents=True, exist_ok=True)
    with marker.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(git("rev-parse", "HEAD") + "\n")
    ledger("reproduction", "started")


def public_progress(rows: list[dict]) -> None:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for index, row in enumerate(rows, start=1):
        writer.writerow(
            {
                "check_index": index,
                "fixture": row["fixture"],
                "passed": row["passed"],
                "reason": row["reason"],
                "permutations_checked": row["permutations_checked"],
                "partition_count": row["partition_count"],
            }
        )
    atomic_text(OUT / "engineering_progress.csv", stream.getvalue())


def relevant_frame(frames: list[dict]) -> dict | None:
    for frame in reversed(frames):
        if frame["file"].startswith("<REPOSITORY>/"):
            return frame
    return frames[-1] if frames else None


def classify_cause(failure: DiagnosticFailure, frame: dict | None) -> tuple[str, str, str]:
    stage = failure.active["stage"]
    function = failure.active["function"]
    if stage in ("signature_construction", "permutation_signature_comparison"):
        defect = "B — TYPE NORMALIZATION / CONTAINER DEFECT"
        expected = "mapped_signature must return order-comparable tuple records"
    elif stage in ("enclosure_validation", "partition_construction"):
        defect = "D — SWITCH / PARTITION INTERFACE DEFECT"
        expected = "certified_partitions must accept the detector's VerifiedEnvelope record"
    elif stage in ("fixture_load", "input_shape_probe"):
        defect = "C — FIXTURE / RECORD SHAPE DEFECT"
        expected = "fixture functions must return a two-dimensional numeric array"
    elif stage in ("switch_detection", "permutation_switch_detection", "field_evaluation"):
        defect = "A — API / ARGUMENT CONTRACT DEFECT"
        expected = "the detector and fixture callable must exchange a one-dimensional float64 grid"
    elif stage == "progress_persistence":
        defect = "E — SERIALIZATION / PUBLICATION DEFECT"
        expected = "a bounded completed-row record must serialize to the append-only ledger"
    else:
        defect = "F — OTHER BOUNDED SOFTWARE DEFECT"
        expected = "the frozen engineering path must complete the active operation"
    location = "unavailable" if frame is None else f"{frame['file']}:{frame['line']} in {frame['function']}"
    return defect, expected, location


def sanitize_message(message: str) -> str:
    return message.replace(str(ROOT.resolve()), "<REPOSITORY>").replace(
        str(Path.home().resolve()), "<HOME>"
    )


def reproduce() -> int:
    preflight()
    begin()
    rows: list[dict] = []
    counter = 0

    def persist(row: dict) -> None:
        nonlocal counter
        counter += 1
        append_progress(counter, row)

    rows, failure = run_engineering_diagnostic(persist)
    if failure is not None:
        local_failure = {
            "exception_class": failure.exception_class,
            "exception_message": failure.exception_message,
            "full_traceback": failure.full_traceback,
            "active": failure.active,
            "completed_rows": list(failure.completed_rows),
            "marker_state": "present",
        }
        atomic_text(
            OUT / "local/failure_full.json",
            json.dumps(local_failure, indent=2, sort_keys=True, allow_nan=False) + "\n",
        )
        sanitized_traceback, frames = sanitize_traceback(failure.full_traceback, ROOT)
        frame = relevant_frame(frames)
        localized = (
            failure.exception_class == "TypeError"
            and failure.active["fixture"] in FIXTURE_ORDER
            and frame is not None
            and bool(failure.active["function"])
        )
        classification = LOCALIZED if localized else INVALID
        defect, expected, location = classify_cause(failure, frame)
        summary = {
            "schema_version": 1,
            "classification": classification,
            "typeerror_reproduced": failure.exception_class == "TypeError",
            "exception_class": failure.exception_class,
            "exception_message": sanitize_message(failure.exception_message),
            "active": failure.active,
            "traceback_frames": frames,
            "sanitized_traceback": sanitized_traceback,
            "failing_location": location,
            "defect_classification": defect if localized else None,
            "expected_contract": expected if localized else None,
            "observed_input": failure.active["input_summary"],
            "completed_checks": len(rows),
            "marker_state": "present",
        }
    else:
        classification = UNRESOLVED
        summary = {
            "schema_version": 1,
            "classification": classification,
            "typeerror_reproduced": False,
            "exception_class": None,
            "exception_message": None,
            "active": None,
            "traceback_frames": [],
            "sanitized_traceback": None,
            "failing_location": None,
            "defect_classification": None,
            "expected_contract": None,
            "observed_input": None,
            "completed_checks": len(rows),
            "marker_state": "present",
        }
    public_progress(rows)
    contract = {
        "schema_version": 1,
        "starting_head": START,
        "protocol_commit": git("log", "-1", "--format=%H", "--", PROTOCOL),
        "execution_commit": git("rev-parse", "HEAD"),
        "fixture_order": list(FIXTURE_ORDER),
        "stages": [
            "fixture_load",
            "field_evaluation",
            "switch_detection",
            "enclosure_validation",
            "partition_construction",
            "input_shape_probe",
            "signature_construction",
            "permutation_switch_detection",
            "permutation_signature_comparison",
            "progress_persistence",
        ],
        "historical_hashes": {path: digest(path) for path in HISTORICAL},
        "implementation_hashes": {path: digest(path) for path in CODE},
        "protocol_sha256": digest(PROTOCOL),
        "environment": environment(),
    }
    write_json("diagnostic_contract.json", contract)
    write_json("failure_summary.json", summary)
    write_json(
        "qc.json",
        {
            "schema_version": 1,
            "status": "closed",
            "classification": classification,
            "completed_checks": len(rows),
            "expected_checks": len(FIXTURE_ORDER),
            "typeerror_reproduced": summary["typeerror_reproduced"],
            "readiness_claimed": False,
            "acceptance_cases_executed": 0,
            "references_executed": 0,
            "acceptance_permutations_executed": 0,
            "empirical_access": False,
        },
    )
    write_json(
        "manifest.json",
        {
            "schema_version": 1,
            "status": "closed",
            "classification": classification,
            "outputs_sha256": {name: digest(OUT / name) for name in FILES},
        },
    )
    validate()
    ledger("reproduction", "closed")
    atomic_text(OUT / "local/closed.marker", digest(OUT / "manifest.json") + "\n")
    print(classification)
    return 0 if classification in (LOCALIZED, UNRESOLVED) else 2


def finite_tree(value) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("nonfinite_value")
    if isinstance(value, dict):
        for item in value.values():
            finite_tree(item)
    elif isinstance(value, list):
        for item in value:
            finite_tree(item)


def exact_keys(value, keys) -> None:
    if type(value) is not dict or set(value) != set(keys):
        raise ValueError("schema_keys")


def validate() -> str:
    contract = read_json(OUT / "diagnostic_contract.json")
    summary = read_json(OUT / "failure_summary.json")
    qc = read_json(OUT / "qc.json")
    manifest = read_json(OUT / "manifest.json")
    for value in (contract, summary, qc, manifest):
        finite_tree(value)
        if value["schema_version"] != 1:
            raise ValueError("schema_version")
    exact_keys(
        contract,
        {
            "schema_version",
            "starting_head",
            "protocol_commit",
            "execution_commit",
            "fixture_order",
            "stages",
            "historical_hashes",
            "implementation_hashes",
            "protocol_sha256",
            "environment",
        },
    )
    exact_keys(
        summary,
        {
            "schema_version",
            "classification",
            "typeerror_reproduced",
            "exception_class",
            "exception_message",
            "active",
            "traceback_frames",
            "sanitized_traceback",
            "failing_location",
            "defect_classification",
            "expected_contract",
            "observed_input",
            "completed_checks",
            "marker_state",
        },
    )
    exact_keys(
        qc,
        {
            "schema_version",
            "status",
            "classification",
            "completed_checks",
            "expected_checks",
            "typeerror_reproduced",
            "readiness_claimed",
            "acceptance_cases_executed",
            "references_executed",
            "acceptance_permutations_executed",
            "empirical_access",
        },
    )
    exact_keys(manifest, {"schema_version", "status", "classification", "outputs_sha256"})
    classification = summary["classification"]
    if classification not in (LOCALIZED, UNRESOLVED, INVALID):
        raise ValueError("classification")
    if qc["classification"] != classification or manifest["classification"] != classification:
        raise ValueError("classification_mismatch")
    if qc["status"] != "closed" or manifest["status"] != "closed":
        raise ValueError("not_closed")
    if qc["readiness_claimed"] is not False or qc["empirical_access"] is not False:
        raise ValueError("scope_mismatch")
    if any(qc[key] != 0 for key in (
        "acceptance_cases_executed",
        "references_executed",
        "acceptance_permutations_executed",
    )):
        raise ValueError("acceptance_work_executed")
    if contract["fixture_order"] != list(FIXTURE_ORDER):
        raise ValueError("fixture_order")
    for path, expected in contract["historical_hashes"].items():
        if path not in HISTORICAL or digest(path) != expected:
            raise ValueError("historical_hash")
    for path, expected in contract["implementation_hashes"].items():
        if path not in CODE or digest(path) != expected:
            raise ValueError("implementation_hash")
    if set(contract["historical_hashes"]) != set(HISTORICAL):
        raise ValueError("historical_authority")
    if set(contract["implementation_hashes"]) != set(CODE):
        raise ValueError("implementation_authority")
    if contract["protocol_sha256"] != digest(PROTOCOL):
        raise ValueError("protocol_hash")
    with safe(OUT / "engineering_progress.csv").open(newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != CSV_FIELDS:
            raise ValueError("progress_fields")
        rows = list(reader)
    if b"\r" in safe(OUT / "engineering_progress.csv").read_bytes():
        raise ValueError("progress_newlines")
    if len(rows) != qc["completed_checks"] or len(rows) != summary["completed_checks"]:
        raise ValueError("progress_count")
    expected_names = list(FIXTURE_ORDER[: len(rows)])
    if [row["fixture"] for row in rows] != expected_names:
        raise ValueError("progress_order")
    if classification == LOCALIZED:
        if not summary["typeerror_reproduced"] or summary["exception_class"] != "TypeError":
            raise ValueError("localization_evidence")
        if summary["active"] is None or summary["failing_location"] in (None, "unavailable"):
            raise ValueError("localization_location")
        if summary["active"]["completed_checks"] != len(rows):
            raise ValueError("active_progress")
    if set(manifest["outputs_sha256"]) != set(FILES):
        raise ValueError("manifest_membership")
    for name, expected in manifest["outputs_sha256"].items():
        if digest(OUT / name) != expected:
            raise ValueError("output_hash")
    for name in (*FILES, "manifest.json"):
        text = safe(OUT / name).read_text()
        if any(item in text for item in (
            str(ROOT.resolve()),
            str(Path.home().resolve()),
            "player_id",
            "event_id",
            "target_id",
            "signed_url",
        )):
            raise ValueError("publication_content")
    return classification


def publication_check() -> None:
    historical_preservation()
    route_guard()
    print(validate())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preflight", "reproduce", "publication-check"))
    command = parser.parse_args().command
    if command == "preflight":
        preflight()
        print("preflight passed")
        return 0
    if command == "reproduce":
        return reproduce()
    publication_check()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
