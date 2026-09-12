#!/usr/bin/env python3
"""Synthetic-only Session 14ab canonical comparison audit."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defensive_network_disruption.geometry.canonical_comparison import compare_raw_provenance, compare_records
from defensive_network_disruption.geometry.diagnostic_artifact_transport import diagnostic_bytes

START = "69b0ef4749cbb151f0f0dad5825165e911dc8bcb"
TAG = "f00690c05d8c1c6db308a65bd311c43f9a8ef2fa"
PROTOCOL = Path("docs/protocols/phase_14ab_canonical_comparison_contract.md")
OUT = Path("outputs/cross_platform_canonical_comparison")
LOCAL = OUT / "local"
ARTIFACT_NAME = "session14ab-python313-canonical-diagnostic"
ARTIFACT_FILENAME = "session14ab_ci_diagnostic.json"
WORKFLOW = Path(".github/workflows/session14ab-canonical-diagnostic.yml")
CODE = (Path("scripts/session_14ab_canonical_comparison_contract.py"),
        Path("src/defensive_network_disruption/geometry/canonical_comparison.py"),
        Path("tests/test_session14ab_canonical_comparison.py"), WORKFLOW)


def safe(path):
    path = Path(path)
    if path.is_absolute() or ".." in path.parts: raise ValueError("unsafe_path")
    result = ROOT / path
    if any(item.is_symlink() for item in (result, *result.parents)): raise ValueError("symlink_rejected")
    return result


def digest(path): return hashlib.sha256(safe(path).read_bytes()).hexdigest()
def git(*args): return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
def committed(path):
    if safe(path).read_bytes() != subprocess.check_output(["git", "show", f"HEAD:{path}"], cwd=ROOT): raise ValueError("uncommitted_authority")
def encoded(value): return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
def write_once(path, data):
    target = safe(path); target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists(): raise FileExistsError("output_exists")
    temporary = target.with_name("." + target.name + ".tmp"); temporary.write_bytes(data); temporary.replace(target)


def load_14aa():
    path = safe("scripts/session_14aa_cross_platform_root_determinism.py")
    spec = importlib.util.spec_from_file_location("session14aa_frozen", path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def validate(record):
    if record.get("schema_version") != 2 or len(record.get("records", ())) != 108: raise ValueError("diagnostic_schema")
    if sum(len(row.get("comparison", ())) for row in record["records"]) != 366: raise ValueError("diagnostic_shape")


def preflight():
    if git("status", "--porcelain"): raise ValueError("clean_tree_required")
    if git("rev-parse", "v0.1.0^{}") != TAG: raise ValueError("release_tag_changed")
    for path in (PROTOCOL, *CODE): committed(path)
    print("Session 14ab preflight passed; synthetic comparison only")


def diagnostic_bytes_now():
    record = load_14aa().diagnostic(); validate(record); return diagnostic_bytes(record)


def local_diagnostic():
    preflight(); raw = diagnostic_bytes_now(); write_once(LOCAL / "local_diagnostic.json", raw)
    print(json.dumps({"vectors": 108, "components": 366, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}, sort_keys=True))


def ci_diagnostic(output):
    preflight(); target = Path(output)
    if target.is_absolute() or target.name != ARTIFACT_FILENAME or (ROOT / target).exists(): raise ValueError("ci_output_path")
    raw = diagnostic_bytes_now(); (ROOT / target).write_bytes(raw)
    print(f"SESSION14AB_DIAGNOSTIC schema=2 bytes={len(raw)} sha256={hashlib.sha256(raw).hexdigest()} artifact={ARTIFACT_NAME} file={ARTIFACT_FILENAME}")


def read_ci(path, claimed):
    path = Path(path)
    if path.name != ARTIFACT_FILENAME or path.is_symlink() or not path.is_file(): raise ValueError("invalid_artifact")
    raw = path.read_bytes()
    if len(raw) > 2_000_000 or hashlib.sha256(raw).hexdigest() != claimed: raise ValueError("artifact_hash")
    record = json.loads(raw); validate(record)
    if diagnostic_bytes(record) != raw: raise ValueError("noncanonical_artifact")
    return record, raw


def compare(ci_file, claimed, run_id):
    preflight(); local_raw = safe(LOCAL / "local_diagnostic.json").read_bytes(); local = json.loads(local_raw); validate(local)
    ci, ci_raw = read_ci(ci_file, claimed)
    canonical = compare_records(local, ci); provenance = compare_raw_provenance(local, ci)
    canonical_record = {name: getattr(canonical, name) for name in canonical.__dataclass_fields__}
    if canonical.canonical_structural_equal and canonical.final_components_bitwise_equal:
        classification, readiness = "A", 2
    elif canonical.canonical_structural_equal: classification, readiness = "B", 3
    else: classification, readiness = "C", 3
    contract = {"schema_version": 1, "canonical_fields": ["onsets", "certified_switches", "owners", "tie_enclosures", "partitions", "routing", "residual_bounds", "accepted_resolution", "component_order", "component_bits"],
                "diagnostic_fields": ["raw_solver_result", "raw_solver_bits", "environment"],
                "raw_provenance_excluded_from_canonical_equality": True}
    historical = {"tests": ["test_session14v_micro_interval.Session14vMicroIntervalTests.test_complete_historical_synthetic_acceptance", "test_session14w_failure_evidence.Session14wMicroIntervalTests.test_complete_historical_synthetic_acceptance"],
                  "cause": "exact comparison of current controlled-Simpson estimates against stale platform-specific historical expected floats",
                  "uses_raw_root": False, "repair_performed": False, "ordinary_ci_expected_to_remain_blocked": True}
    qc = {"schema_version": 1, "status": "closed", "classification": classification, "readiness": readiness,
          **canonical_record, "raw_solver_provenance_equal": provenance["raw_solver_provenance_equal"],
          "raw_solver_differences": len(provenance["differences"]), "maximum_raw_solver_ulp": max((x["ulp_distance"] for x in provenance["differences"]), default=0),
          "vectors": 108, "components": 366, "governed_ci_run_id": str(run_id), "governed_dispatches": 1, "artifact_retrievals": 1,
          "empirical_access": False, "session14r_partial_outputs_accessed": False}
    write_once(OUT / "comparison_contract.json", encoded(contract)); write_once(OUT / "local_diagnostic.json", local_raw); write_once(OUT / "ci_diagnostic.json", ci_raw)
    write_once(OUT / "canonical_comparison.json", encoded(canonical_record)); write_once(OUT / "provenance_comparison.json", encoded(provenance)); write_once(OUT / "historical_test_review.json", encoded(historical)); write_once(OUT / "qc.json", encoded(qc))
    names = ("comparison_contract.json", "local_diagnostic.json", "ci_diagnostic.json", "canonical_comparison.json", "provenance_comparison.json", "historical_test_review.json", "qc.json")
    manifest = {"schema_version": 1, "status": "closed", "start": START, "release_tag_target": TAG, "protocol_sha256": digest(PROTOCOL),
                "implementation": {str(path): digest(path) for path in CODE}, "ci_run_id": str(run_id), "artifact_name": ARTIFACT_NAME,
                "declared_ci_sha256": claimed, "downloaded_ci_sha256": hashlib.sha256(ci_raw).hexdigest(), "outputs": {name: digest(OUT / name) for name in names}}
    write_once(OUT / "manifest.json", encoded(manifest)); print(json.dumps(qc, sort_keys=True))


def publication_check():
    manifest = json.loads(safe(OUT / "manifest.json").read_text())
    for name, expected in manifest["outputs"].items():
        if digest(OUT / name) != expected: raise ValueError("output_hash_changed")
    for name in (*manifest["outputs"], "manifest.json"):
        text = safe(OUT / name).read_text()
        if any(token in text for token in ("/Users/", "/home/runner/", "event_id", "target_id", "X-Amz-Signature")): raise ValueError("publication_boundary")
    print("Session 14ab publication checks passed")


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("command", choices=("preflight", "local-diagnostic", "ci-diagnostic", "compare", "publication-check")); parser.add_argument("--output", default=ARTIFACT_FILENAME); parser.add_argument("--ci-file"); parser.add_argument("--declared-sha256"); parser.add_argument("--run-id")
    args = parser.parse_args()
    if args.command == "preflight": preflight()
    elif args.command == "local-diagnostic": local_diagnostic()
    elif args.command == "ci-diagnostic": ci_diagnostic(args.output)
    elif args.command == "compare":
        if not all((args.ci_file, args.declared_sha256, args.run_id)): raise ValueError("comparison_arguments_required")
        compare(args.ci_file, args.declared_sha256, args.run_id)
    else: publication_check()


if __name__ == "__main__": main()
