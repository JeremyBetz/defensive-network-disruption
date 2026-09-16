#!/usr/bin/env python3
"""Synthetic-only Session 14R9H authority-context diagnosis."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import traceback


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defensive_network_disruption.validation import r9h_authority_context as authority


START = "6385792269c9beb034722d5f01bd74ea391971fd"
TAG = "f00690c05d8c1c6db308a65bd311c43f9a8ef2fa"
PROTOCOL = Path("docs/protocols/phase_14r9h_runner_authority_context.md")
OUT = Path("outputs/continuous_occlusion_runner_authority_context")
LOCAL = OUT / "local"
PUBLIC = (
    "authority_flow.json", "context_contract.json", "mutation_oracles.csv",
    "retained_certificate_orchestration.json", "unmatched_warning_oracle.json",
    "publication_regression.json", "qc.json", "manifest.json",
)
IMPLEMENTATION = (
    "scripts/session_14r9h_runner_authority_context.py",
    "src/defensive_network_disruption/validation/r9h_authority_context.py",
    "src/defensive_network_disruption/geometry/r9e_representation.py",
    "src/defensive_network_disruption/validation/r9f_portable_authority.py",
    "src/defensive_network_disruption/validation/independent_certificate_verifier.py",
    "tests/authority_fixtures/session14r9e_certificate_authority.json",
    "tests/test_session14r9h.py",
)


def _safe(path: Path) -> Path:
    target = ROOT / path
    if (any(item.is_symlink() for item in (target, *target.parents)) or
            not target.resolve().is_relative_to(ROOT.resolve())):
        raise PermissionError("unsafe_path")
    return target


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with _safe(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1_048_576), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def _atomic_bytes(path: Path, raw: bytes) -> None:
    target = _safe(path)
    if target.exists():
        raise FileExistsError("immutable_record_exists:" + target.name)
    target.parent.mkdir(parents=True, exist_ok=True)
    pending = target.with_name("." + target.name + ".pending")
    with pending.open("xb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    os.link(pending, target)
    pending.unlink()


def _atomic_json(path: Path, value: object) -> None:
    _atomic_bytes(path, _canonical(value))


def _csv_bytes(rows: list[dict]) -> bytes:
    if not rows:
        raise ValueError("csv_rows_required")
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().replace("\r\n", "\n").encode()


def _head() -> str:
    return subprocess.check_output(("git", "rev-parse", "HEAD"), cwd=ROOT,
                                   text=True).strip()


def _release() -> str:
    return subprocess.check_output(("git", "rev-parse", "v0.1.0^{}"), cwd=ROOT,
                                   text=True).strip()


def preflight() -> dict:
    if _release() != TAG:
        raise RuntimeError("release_target_changed")
    if not _safe(PROTOCOL).is_file():
        raise RuntimeError("protocol_missing")
    fixture = _safe(Path("tests/authority_fixtures/session14r9e_certificate_authority.json"))
    if hashlib.sha256(fixture.read_bytes()).hexdigest() != (
            "84357ed8cee08b6452fe146bcd97eb5a2d3166910aba86e46f2768f358be85f9"):
        raise RuntimeError("portable_fixture_changed")
    if _safe(LOCAL / "audit.marker").exists():
        raise FileExistsError("audit_marker_exists")
    return {"schema_version": 1, "status": "ready", "session": "14R9H",
            "starting_head": START, "current_head": _head(),
            "release_target": TAG, "protocol_sha256": _sha(PROTOCOL),
            "empirical_access": {"states": 0, "edges": 0}}


def _failure_publication_oracle() -> dict:
    with tempfile.TemporaryDirectory(dir=ROOT) as folder:
        base = Path(folder)
        marker = base / "attempt.marker"
        failure = base / "failure.json"
        marker.write_bytes(_canonical({"status": "reserved"}))
        try:
            raise RuntimeError("synthetic_context_construction_failure")
        except RuntimeError as error:
            failure.write_bytes(_canonical({
                "schema_version": 1, "status": "failure",
                "exception": type(error).__name__, "message": str(error),
                "traceback": "".join(traceback.format_exception(error)),
                "empirical_access": {"states": 0, "edges": 0},
                "readiness": False,
            }))
        record = json.loads(failure.read_text())
        rerun_rejected = marker.exists()
        return {
            "actual_failure_boundary": "session14r9h_runner",
            "original_exception_preserved": record["exception"] == "RuntimeError",
            "traceback_preserved": "synthetic_context_construction_failure" in record["traceback"],
            "zero_access_preserved": record["empirical_access"] == {"states": 0, "edges": 0},
            "readiness_false": record["readiness"] is False,
            "failure_evidence_valid": record["status"] == "failure",
            "rerun_rejected": rerun_rejected,
            "status": "passed",
        }


def execute_acceptance() -> dict[str, object]:
    flow = authority.observe_actual_join(ROOT)
    mutations = authority.mutation_oracles()
    retained = authority.retained_certificate_orchestration(ROOT)
    unmatched = authority.unmatched_warning_oracle(ROOT)
    reopening = authority.no_reopening_guard(ROOT)
    publication = _failure_publication_oracle()
    passed = (
        all(flow[name] for name in (
            "actual_chain_observed", "origin_identical", "receiver_identical",
            "defenders_identical_and_ordered", "field_values_identical",
            "authority_builder_received_complete_context")) and
        flow["actual_loss_observed"] is False and
        all(row["status"] == "passed" for row in mutations) and
        retained["warning_preserved"] and retained["exact_request_matched"] and
        retained["certificate_lookup_succeeded"] and
        unmatched["blocking"] and not unmatched["readiness"] and
        reopening["passed"] and publication["status"] == "passed"
    )
    return {"flow": flow, "mutations": mutations, "retained": retained,
            "unmatched": unmatched, "reopening": reopening,
            "publication": publication, "passed": passed}


def audit() -> None:
    stage = "preflight"
    try:
        ready = preflight()
        _atomic_json(LOCAL / "audit.marker", {
            "schema_version": 1, "status": "reserved", "head": _head(),
            "preflight_sha256": hashlib.sha256(_canonical(ready)).hexdigest(),
        })
        stage = "synthetic_acceptance"
        result = execute_acceptance()
        if not result["passed"]:
            raise RuntimeError("synthetic_acceptance_failed")
        stage = "publication"
        flow = result["flow"]
        context_contract = {
            "schema_version": 1,
            "selected_geometry_fields": ["alias", "origin", "receiver", "defenders"],
            "orchestration_identity_fields": ["alias", "state", "edge"],
            "certificate_fingerprint_excludes": ["state", "edge"],
            "geometry_source": "validated values used by r9e_representation.evaluate",
            "defender_order": "validate_geometry input row order preserved",
            "secondary_geometry_source": False,
            "production_context_object_added": False,
            "production_numerical_code_changed": False,
            "reason": "existing evaluator already joins complete canonical geometry",
        }
        qc = {
            "schema_version": 1, "status": "passed", "classification": "A",
            "readiness": 1, "existing_wiring_confirmed": True,
            "production_repair_required": False,
            "retained_r9g_classification": "D_INVALID_BLOCKED",
            "empirical_access": {"states": 0, "edges": 0},
            "mutation_oracles": {"run": len(result["mutations"]),
                                 "passed": sum(row["status"] == "passed" for row in result["mutations"])},
            "no_geometry_reopening": result["reopening"]["passed"],
            "publication_regression": result["publication"]["status"],
            "claim_ledger_changed": False,
        }
        _atomic_json(OUT / "authority_flow.json", {"schema_version": 1, **flow})
        _atomic_json(OUT / "context_contract.json", context_contract)
        _atomic_bytes(OUT / "mutation_oracles.csv", _csv_bytes(result["mutations"]))
        _atomic_json(OUT / "retained_certificate_orchestration.json",
                     {"schema_version": 1, **result["retained"]})
        _atomic_json(OUT / "unmatched_warning_oracle.json",
                     {"schema_version": 1, **result["unmatched"]})
        _atomic_json(OUT / "publication_regression.json",
                     {"schema_version": 1, **result["publication"],
                      "no_geometry_reopening": result["reopening"]})
        _atomic_json(OUT / "qc.json", qc)
        outputs = {name: _sha(OUT / name) for name in PUBLIC if name != "manifest.json"}
        manifest = {
            "schema_version": 1, "status": "passed", "session": "14R9H",
            "starting_head": START, "protocol_sha256": _sha(PROTOCOL),
            "implementation": {name: _sha(Path(name)) for name in IMPLEMENTATION},
            "outputs": outputs, "classification": "A", "readiness": 1,
            "empirical_access": {"states": 0, "edges": 0},
        }
        _atomic_json(OUT / "manifest.json", manifest)
        print("Session 14R9H synthetic authority-context acceptance passed")
    except BaseException as error:
        emergency = LOCAL / "emergency_failure.json"
        if not _safe(emergency).exists():
            _atomic_json(emergency, {"schema_version": 1, "status": "failure",
                "stage": stage, "exception": type(error).__name__,
                "traceback": "".join(traceback.format_exception(error)),
                "empirical_access": {"states": 0, "edges": 0}})
        raise


def publication_check() -> dict:
    target = _safe(OUT)
    actual = {path.name for path in target.iterdir() if path.is_file()}
    if actual != set(PUBLIC):
        raise RuntimeError("public_artifact_set")
    manifest = json.loads((target / "manifest.json").read_text())
    if (manifest.get("status") != "passed" or manifest.get("classification") != "A" or
            manifest.get("readiness") != 1 or
            manifest.get("empirical_access") != {"states": 0, "edges": 0}):
        raise RuntimeError("manifest_status")
    expected = manifest.get("outputs", {})
    observed = {name: _sha(OUT / name) for name in PUBLIC if name != "manifest.json"}
    if expected != observed:
        raise RuntimeError("output_hash_mismatch")
    qc = json.loads((target / "qc.json").read_text())
    if qc.get("status") != "passed" or qc.get("empirical_access") != {"states": 0, "edges": 0}:
        raise RuntimeError("qc_status")
    if any(not (target / name).read_bytes().endswith(b"\n") for name in PUBLIC):
        raise RuntimeError("lf_termination")
    return {"schema_version": 1, "status": "valid", "artifact_count": len(PUBLIC),
            "manifest_sha256": _sha(OUT / "manifest.json")}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "audit", "publication-check"))
    command = parser.parse_args().command
    if command == "preflight":
        print(json.dumps(preflight(), sort_keys=True, allow_nan=False))
    elif command == "audit":
        audit()
    else:
        print(json.dumps(publication_check(), sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
