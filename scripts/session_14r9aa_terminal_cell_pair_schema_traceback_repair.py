#!/usr/bin/env python3
"""Run the synthetic-only Session 14R9AA governed acceptance."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "outputs/continuous_occlusion_terminal_cell_pair_schema_repair"
PROTOCOL = ROOT / "docs/protocols/phase_14r9aa_terminal_cell_pair_schema_traceback_repair.md"
TAG = "f00690c05d8c1c6db308a65bd311c43f9a8ef2fa"

HISTORICAL = {
    "docs/protocols/phase_14r9v_tie_boundary_and_publication_diagnosis.md": "20710c4420dd988c5aafa68d16f487f90d7341cc86f1278ba2937f134c5302d5",
    "docs/session_14r9v_tie_boundary_and_publication_diagnosis.md": "cded89e4cb5dd074e1f2e47e03aef620f7134faaac75f0b599e1c2e679332ebf",
    "outputs/continuous_occlusion_tie_boundary_publication_diagnosis/manifest.json": "2d1424ae401dfb83a38aea4af2539c394fff024188a6348df072d997340301b8",
    "docs/protocols/phase_14r9x_terminal_cell_evidence_retention_review.md": "5cf0461d9ec16d75f3b763a100e21aede23387a0f8242d159b4761d61f1d47c0",
    "docs/session_14r9x_terminal_cell_evidence_retention_review.md": "aa6d414ca316a0eff2ccc1f1609eef79ed88539a2a29a99192b3566bf87051c6",
    "outputs/continuous_occlusion_terminal_cell_evidence_retention/manifest.json": "9c87d0217a0152a535890c573c5aa22498295f20dc922c0044c0d3e570fae567",
    "docs/protocols/phase_14r9y_terminal_cell_authority_acquisition.md": "342b45dc6c8382e780b4b6fdcb4dc3fd7759e9bec59d5f4fceecc5fa14d116ed",
    "docs/session_14r9y_terminal_cell_authority_acquisition.md": "77d7ae2b1aa2f1c508146ed5cb528bb854f751dfa3feebc3f4d3742598084b78",
    "outputs/continuous_occlusion_terminal_cell_authority_acquisition/manifest.json": "d0254407d973eca7a5b2fbe1bf34c15a9ef0529c190672947bb2130f92c985a0",
    "docs/protocols/phase_14r9z_pair_authority_failure_evidence_diagnosis.md": "c3ab50099536267d82538d444bb0814c80d8cc7e0847f18998e0e9622cb76d88",
    "docs/session_14r9z_pair_authority_failure_evidence_diagnosis.md": "352d53864bf9c2e0b4aee9d1bcef2e8d44cadb98fb5e6be3900003b1460a4cdf",
    "outputs/continuous_occlusion_pair_authority_diagnosis/manifest.json": "3bc702538cae9a28cf739f5fa0a9e9d307fa9e45ee6fccea4c46e8ee6d19c456",
    "src/defensive_network_disruption/geometry/r9x_terminal_authority.py": "ab272ec304602ab0931fd23b4ecf74cf7479f8ee076d60b954824090525ae097",
    "scripts/session_14r9y_terminal_cell_authority_acquisition.py": "06af99c3de890e72deaa2f501a04d014048cfaaaa7e74bb5ddb39537c3d36af1",
    "src/defensive_network_disruption/validation/checkpoint_ci_authority.py": "d66328abab8f0aa059fc84c405a409f5d6b621b8276561f127cc8789b0e1068b",
    "src/defensive_network_disruption/validation/r9j_linear_publication.py": "a242cb0921d1fd390cd2b74c9d15a0fdff3e2b82e46000dc8be0cbbba6d6c139",
}


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=ROOT, text=True).strip()


def put(path: Path, value: object) -> None:
    from defensive_network_disruption.validation.r9j_evidence import put as write
    write(path, value)


def expectation():
    from defensive_network_disruption.validation.checkpoint_ci_authority import CIExpectation
    return CIExpectation(git("rev-parse", "HEAD"), sha(PROTOCOL), sha(Path(__file__)),
                         sha(ROOT / "uv.lock"), sha(ROOT / ".github/workflows/ci.yml"))


def preflight(folder: Path = OUT) -> dict:
    if git("status", "--porcelain"):
        raise RuntimeError("dirty_tree")
    if git("rev-parse", "HEAD") != git("rev-parse", "origin/main"):
        raise RuntimeError("tracking_mismatch")
    if git("rev-parse", "v0.1.0^{}") != TAG:
        raise RuntimeError("release_tag")
    local = Path(folder) / "local"
    if (local / "audit.marker").exists() or (local / "closure.marker").exists():
        raise FileExistsError("governed_audit_exists")
    if any(sha(ROOT / name) != value for name, value in HISTORICAL.items()):
        raise RuntimeError("historical_authority")
    from defensive_network_disruption.validation.checkpoint_ci_authority import validate_receipt
    receipt = local / "checkpoint_ci.json"
    sidecar = local / "checkpoint_ci.json.sha256"
    authority = validate_receipt(receipt, expectation(), expected_sha256=sidecar.read_text().strip())
    return {"head": git("rev-parse", "HEAD"), "ci_receipt_sha256": authority.receipt_sha256}


def audit() -> dict:
    environment = preflight()
    local = OUT / "local"
    put(local / "audit.marker", {"reserved": True, "empirical_access": False})
    from defensive_network_disruption.validation import r9aa_acceptance as acceptance
    from defensive_network_disruption.validation import r9aa_evidence as evidence
    schema_rows, details = acceptance.schema_controls()
    failure_rows, failure_private = acceptance.failure_controls(local / "failure_controls")
    compatibility = acceptance.compatibility_matrix()
    history = acceptance.historical_hashes(ROOT, HISTORICAL)
    put(local / "schema_details.json", details)
    put(local / "failure_details.json", failure_private)
    put(local / "authority_bindings.json", {"schema_version": 1, "files": HISTORICAL})
    schema_valid = all(row["passed"] for row in schema_rows)
    traceback_valid = all(row["passed"] for row in failure_rows)
    preservation_valid = all(history.values()) and details["v1_bytes_preserved"]
    valid = schema_valid and traceback_valid and preservation_valid
    records = {
        "repair_contract.json": {"schema_version": 1, "status": "complete",
            "flags": {"synthetic_only": True, "v1_unchanged": True,
                      "distinct_pair_authority": True, "capture_precedes_callbacks": True,
                      "historical_r9y_traceback_unavailable": True},
            "counts": {"states_reopened": 0, "edges_reopened": 0,
                       "field_evaluations": 0, "acquisitions": 0,
                       "refinements": 0, "maximality_classifications": 0}},
        "schema_v2.json": {"schema_version": 1, "status": "complete",
            "authority_schema_version": 2, "serialization": "canonical-json-v2",
            "relations": ["symbolic_identity", "common_inactive_branch", "tolerance_certified"],
            "flags": {"ordered_pair_references": True, "tie_authority_hash_closed": True,
                      "independent_pair_bounds": True, "all_competitors_compared": True,
                      "tie_relation_provenance_only": True}},
        "historical_preservation.json": {"schema_version": 1, "status": "complete",
            "flags": {"all_bound_hashes_match": all(history.values()),
                      "historical_v1_preserved": details["v1_bytes_preserved"],
                      "historical_r9y_traceback_available": False,
                      "public_api_changed": False, "dependency_changed": False},
            "counts": {"bound_files": len(history)}},
    }
    qc = {"status": "complete" if valid else "invalid", "execution_valid": valid,
          "classification": "A" if valid else "D", "readiness": 1 if valid else 4,
          "schema_repair_valid": schema_valid, "traceback_repair_valid": traceback_valid,
          "historical_v1_preserved": preservation_valid,
          "historical_r9y_traceback_available": False,
          "states_reopened": 0, "edges_reopened": 0, "empirical_computations": 0}
    put(local / "closure.marker", {"status": qc["status"]})
    result = evidence.close(OUT, records,
        {"compatibility_matrix.csv": compatibility,
         "synthetic_pair_controls.csv": schema_rows,
         "traceback_controls.csv": failure_rows}, qc)
    return {**result, "environment": environment}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "audit", "publication-check"))
    args = parser.parse_args()
    if args.command == "preflight":
        result = preflight()
    elif args.command == "audit":
        result = audit()
    else:
        from defensive_network_disruption.validation.r9aa_evidence import publication_check
        result = publication_check(OUT)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
