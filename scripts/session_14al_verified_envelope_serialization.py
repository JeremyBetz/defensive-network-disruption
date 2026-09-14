#!/usr/bin/env python3
"""One-shot synthetic Session 14al diagnostic-serialization audit."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np

from defensive_network_disruption.geometry.diagnostic_serialization import (
    DiagnosticSerializationError, canonical_bytes, emergency_write,
    project_evidence, project_verified_envelope, semantic_envelope_equal,
)
from defensive_network_disruption.geometry.micro_interval_verifier import IntegralInterval
from defensive_network_disruption.geometry.root_partition_determinism import CertifiedOnset, CertifiedRootTransition
from defensive_network_disruption.geometry.verification_repair import (
    CertifiedBoundary, CertifiedTieInterval, VerifiedEnvelope, VerifiedSwitch,
)

START = "05070c7dde5114840e4f4678a5db20cf395cbbb6"
TAG = "f00690c05d8c1c6db308a65bd311c43f9a8ef2fa"
PROTOCOL = Path("docs/protocols/phase_14al_verified_envelope_serialization.md")
IMPLEMENTATION = Path("src/defensive_network_disruption/geometry/diagnostic_serialization.py")
SCRIPT = Path("scripts/session_14al_verified_envelope_serialization.py")
OUT = Path("outputs/session14_verified_envelope_serialization")
LOCAL = OUT / "local"
PUBLIC = (
    "failure_reproduction.json", "verified_envelope_schema.json",
    "nested_type_inventory.csv", "deterministic_serialization.json",
    "payload_regression.json", "negative_controls.csv",
    "emergency_record_regression.json", "numerical_invariance.json", "qc.json",
)
NUMERICAL_HASHES = {
    "src/defensive_network_disruption/geometry/occlusion_fields.py": "d7fd23bc131d0db2686ef27475a128fdca78aea88616c4494609962c165533aa",
    "src/defensive_network_disruption/geometry/verification_repair.py": "417233c6baf694b35d4ce835fe1164ed9730a54df81e2cb8b6deb06911a330cd",
    "src/defensive_network_disruption/geometry/root_partition_determinism.py": "8709706de798277c172d5f4a874856fad1ebb4321caf1f004be9e24ba622f0af",
    "src/defensive_network_disruption/geometry/onset_owner_certification.py": "d62dc611a759b03c68098c7628568d3f9e78fd59d995a4f555dd6ed325171b97",
    "src/defensive_network_disruption/geometry/micro_interval_verifier.py": "55389fd78d7c546bb1b4c830cdb434932fce6f67dcc8042a2427e44dc77c2b0e",
    "src/defensive_network_disruption/geometry/production_verification.py": "6d4eeddf0c7537ecbea027e1c308e4f573b2cf0f4bb71a0b3b839e2382f75a6c",
    "src/defensive_network_disruption/geometry/representation_retry.py": "96dbdfe6030582e69f837a1343fb1e68952ed34992c957f243507bdc5b2c2f99",
    "scripts/session_14ak_constant_width_comparator_diagnosis.py": "48eb9ff8c1637cbdcd148f65403614d1314a36302862135c9b088c22ec066f04",
    "outputs/session14_constant_width_comparator_diagnosis/manifest.json": "5352fa30bf8e4c0ac67aee8cecb1e5fdbbf2f703e79bca9d2f8c9a01e9c03896",
    "outputs/session14_constant_width_comparator_diagnosis/local/emergency_failure.json": "fda86bc1e35557ee313d47ffe1c54a44f7fa9893434dc1732fb43c92926b91c8",
}


def safe(path: Path | str) -> Path:
    value = Path(path)
    if not value.is_absolute():
        value = ROOT / value
    resolved = value.resolve()
    if not resolved.is_relative_to(ROOT.resolve()) or any(item.is_symlink() for item in (value, *value.parents)):
        raise PermissionError("unsafe_path")
    return value


def sha(path: Path | str) -> str:
    return hashlib.sha256(safe(path).read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=ROOT, text=True).strip()


def committed(path: Path) -> bool:
    stored = subprocess.check_output(("git", "show", "HEAD:" + str(path)), cwd=ROOT)
    return hashlib.sha256(stored).hexdigest() == sha(path)


def write_once(path: Path | str, value) -> None:
    destination = safe(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError("output_exists")
    pending = destination.with_name("." + destination.name + ".pending")
    with pending.open("xb") as handle:
        handle.write(canonical_bytes(value)); handle.flush(); os.fsync(handle.fileno())
    os.link(pending, destination); pending.unlink()


def write_csv(path: Path | str, rows: list[dict], fields: tuple[str, ...]) -> None:
    destination = safe(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError("output_exists")
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader(); writer.writerows(rows)
    pending = destination.with_name("." + destination.name + ".pending")
    with pending.open("x", newline="") as handle:
        handle.write(buffer.getvalue()); handle.flush(); os.fsync(handle.fileno())
    os.link(pending, destination); pending.unlink()


def fixture() -> VerifiedEnvelope:
    start = CertifiedBoundary(0.24, float(np.nextafter(0.24, 1.0)), "entry", (1, 0), (1, 0))
    end = CertifiedBoundary(0.76, float(np.nextafter(0.76, 0.0)), "exit", (0, 1), (0, 1))
    tie = CertifiedTieInterval(start, end, (1, 0), ((1, 0),))
    switch = VerifiedSwitch(0.5, (0,), (1, 0), (1,), ((1, 0),), False, False, 0.75)
    return VerifiedEnvelope((switch,), (tie,), (1, 0), (0.0, 0.5, 1.0), 65536)


def payload() -> dict:
    interval = IntegralInterval(0.2, 0.2000000000001, 1e-13, 3, 2, 1)
    onset = CertifiedOnset(0, 1, 0.25, float(np.nextafter(0.25, 0.0)), 0.25)
    transition = CertifiedRootTransition(0.5, float(np.nextafter(0.5, 0.0)), None, None,
                                         0.5, (0,), (0, 1), (1,), ((0, 1),))
    return {
        "production": {"intervals": 512, "estimates": {"maximum": np.float64(0.2)}, "change": 1e-8},
        "strict": interval, "repeat": interval, "unsplit": 0.2, "disagreement": 0.0,
        "partitions": (0.0, 0.5, 1.0), "onsets": (onset,), "switches": (transition,),
        "envelope": fixture(), "piece_contributions": [{"piece": 0, "integral": interval}],
        "onset_neighborhood": [{"owners": [0, 1], "finite": True}],
        "uniform_curve": [{"intervals": 256, "estimate": 0.2}],
        "piecewise_curve": [{"intervals": 256, "estimate": 0.2}],
    }


def historical_plain(value):
    if isinstance(value, dict): return {str(key): historical_plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)): return [historical_plain(item) for item in value]
    if isinstance(value, np.generic): return value.item()
    return value


def preflight() -> dict:
    if git("status", "--porcelain"):
        raise RuntimeError("dirty_tree")
    git("merge-base", "--is-ancestor", START, "HEAD")
    if git("rev-parse", "v0.1.0^{}") != TAG:
        raise RuntimeError("release_changed")
    if Path(sys.prefix).resolve() != (ROOT / ".venv").resolve():
        raise RuntimeError("project_environment_required")
    for path in (PROTOCOL, IMPLEMENTATION, SCRIPT):
        if not committed(path): raise RuntimeError("uncommitted_authority")
    return {"python": platform.python_version(), "numpy": np.__version__, "lock_sha256": sha("uv.lock")}


def run_audit() -> None:
    marker = LOCAL / "audit.marker"
    write_once(marker, {"schema_version": 1, "session": "14al"})
    environment = preflight()

    failure = None
    try:
        json.dumps(historical_plain({"envelope": fixture()}), allow_nan=False)
    except TypeError as error:
        failure = error
    if failure is None or "VerifiedEnvelope" not in str(failure) or "JSON serializable" not in str(failure):
        raise RuntimeError("historical_failure_not_reproduced")

    envelope_projection = project_verified_envelope(fixture())
    full = payload()
    projected = project_evidence(full)
    first = canonical_bytes(full); second = canonical_bytes(full)
    if first != second or not semantic_envelope_equal(fixture(), envelope_projection):
        raise RuntimeError("determinism_or_equivalence")

    private_path = LOCAL / "synthetic_payload.json"
    write_once(private_path, full)
    private_hash = sha(private_path)

    controls = []
    for name, value in (
        ("unsupported_object", object()), ("unordered_set", {1, 2}),
        ("nonfinite_nan", math.nan), ("nonfinite_positive_infinity", math.inf),
        ("nonfinite_negative_infinity", -math.inf), ("unsupported_array", np.array([1.0])),
        ("non_string_mapping_key", {1: "bad"}),
    ):
        try:
            canonical_bytes({"value": value}); blocked = False; category = "none"
        except DiagnosticSerializationError as error:
            blocked = True; category = str(error).split(":", 1)[0]
        controls.append({"fixture": name, "blocked": blocked, "category": category})
    malformed = VerifiedEnvelope((), (), (0, 0), (0.0, 1.0), 2)
    try:
        project_verified_envelope(malformed); malformed_blocked = False
    except DiagnosticSerializationError:
        malformed_blocked = True
    controls.append({"fixture": "malformed_owner_set", "blocked": malformed_blocked,
                     "category": "maximizing_defenders_malformed"})
    if not all(row["blocked"] for row in controls): raise RuntimeError("negative_control_failed")

    with tempfile.TemporaryDirectory(dir=LOCAL) as directory:
        root = Path(directory)
        try:
            canonical_bytes({"supported": envelope_projection, "later_bad": object()})
        except DiagnosticSerializationError as error:
            emergency_write(root / "emergency.json", error, stage="synthetic_publication")
        emergency = json.loads((root / "emergency.json").read_text())
        emergency_ok = (emergency["exception"] == "DiagnosticSerializationError" and
                        "unsupported_type" in emergency["traceback"] and
                        not (root / "manifest.json").exists())
    if not emergency_ok: raise RuntimeError("emergency_regression")

    invariance = {name: {"expected_sha256": expected, "actual_sha256": sha(name),
                          "unchanged": sha(name) == expected}
                  for name, expected in NUMERICAL_HASHES.items()}
    if not all(item["unchanged"] for item in invariance.values()):
        raise RuntimeError("numerical_authority_changed")

    write_once(OUT / "failure_reproduction.json", {
        "schema_version": 1, "reproduced": True, "exception": "TypeError",
        "root_type": "VerifiedEnvelope", "message_category": "not_json_serializable",
        "empirical_source_used": False,
    })
    write_once(OUT / "verified_envelope_schema.json", {
        "schema_version": 1, "projection_type": "verified_envelope",
        "required_fields": sorted(envelope_projection), "json_primitive_only": True,
        "semantic_equivalence": True, "round_trip_reconstruction_required": False,
    })
    inventory = [
        {"type": "VerifiedEnvelope", "classification": "A", "projection": "canonical_structure"},
        {"type": "VerifiedSwitch", "classification": "A", "projection": "canonical_structure"},
        {"type": "CertifiedTieInterval", "classification": "A", "projection": "canonical_structure"},
        {"type": "CertifiedBoundary", "classification": "A", "projection": "canonical_structure"},
        {"type": "CertifiedOnset", "classification": "A", "projection": "canonical_structure"},
        {"type": "CertifiedRootTransition", "classification": "A/B", "projection": "canonical_plus_raw_provenance"},
        {"type": "IntegralInterval", "classification": "A", "projection": "bounded_integral_authority"},
        {"type": "raw_solver_result", "classification": "B", "projection": "diagnostic_only_not_canonical_equality"},
        {"type": "derived_counts", "classification": "C", "projection": "retained_where_14ak_payload_requires"},
        {"type": "empirical_values", "classification": "D", "projection": "not_accessed_or_published"},
    ]
    write_csv(OUT / "nested_type_inventory.csv", inventory, ("type", "classification", "projection"))
    write_once(OUT / "deterministic_serialization.json", {
        "schema_version": 1, "byte_identical": first == second,
        "sha256_identical": hashlib.sha256(first).digest() == hashlib.sha256(second).digest(),
        "payload_sha256": hashlib.sha256(first).hexdigest(), "owner_order": "ascending_integer",
        "key_order": "lexicographic", "float_rule": "finite_exact_no_rounding",
    })
    write_once(OUT / "payload_regression.json", {
        "schema_version": 1, "full_14ak_shape_serialized": True,
        "embedded_envelope_projected": projected["envelope"]["type"] == "verified_envelope",
        "nested_types_projected": True, "private_payload_sha256": private_hash,
        "manifest_closure_exercised": True,
    })
    write_csv(OUT / "negative_controls.csv", controls, ("fixture", "blocked", "category"))
    write_once(OUT / "emergency_record_regression.json", {
        "schema_version": 1, "primary_exception_preserved": emergency_ok,
        "traceback_preserved": emergency_ok, "emergency_written": emergency_ok,
        "false_success_manifest_absent": emergency_ok,
    })
    write_once(OUT / "numerical_invariance.json", {
        "schema_version": 1, "all_unchanged": True, "files": invariance,
        "field_or_integration_execution": False,
    })
    qc = {
        "schema_version": 1, "status": "closed", "classification": "A",
        "readiness": 1, "pre_repair_failure_reproduced": True,
        "standalone_projection_passed": True, "full_payload_passed": True,
        "deterministic": True, "negative_controls_passed": True,
        "emergency_regression_passed": True, "numerical_invariance_passed": True,
        "empirical_data_accessed": False, "session14ak_unchanged": True,
        "environment": environment,
    }
    write_once(OUT / "qc.json", qc)
    output_hashes = {name: sha(OUT / name) for name in PUBLIC}
    write_once(OUT / "manifest.json", {
        "schema_version": 1, "status": "closed", "start": START,
        "protocol_sha256": sha(PROTOCOL), "implementation_commit": git("rev-parse", "HEAD"),
        "outputs": output_hashes, "private_payload_sha256": private_hash,
    })
    publication_check()
    print(json.dumps({"classification": "A", "readiness": 1}, sort_keys=True))


def publication_check() -> None:
    manifest = json.loads(safe(OUT / "manifest.json").read_text())
    required = {"schema_version", "status", "start", "protocol_sha256", "implementation_commit",
                "outputs", "private_payload_sha256"}
    if set(manifest) != required or set(manifest["outputs"]) != set(PUBLIC):
        raise ValueError("manifest_schema")
    for name, expected in manifest["outputs"].items():
        if sha(OUT / name) != expected: raise ValueError("output_hash")
    if sha(LOCAL / "synthetic_payload.json") != manifest["private_payload_sha256"]:
        raise ValueError("private_hash")
    qc = json.loads(safe(OUT / "qc.json").read_text())
    if qc["classification"] != "A" or qc["readiness"] != 1 or qc["empirical_data_accessed"]:
        raise ValueError("qc_gate")
    public = "".join(safe(OUT / name).read_text() for name in (*PUBLIC, "manifest.json"))
    for forbidden in ("/Users/", "/private/", '"carrier"', '"receiver_xy"', '"defenders"'):
        if forbidden in public: raise ValueError("publication_privacy")
    print("Session 14al publication package verified")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "audit", "publication-check"))
    command = parser.parse_args().command
    if command == "preflight": print(json.dumps(preflight(), sort_keys=True))
    elif command == "audit": run_audit()
    else: publication_check()


if __name__ == "__main__":
    main()
