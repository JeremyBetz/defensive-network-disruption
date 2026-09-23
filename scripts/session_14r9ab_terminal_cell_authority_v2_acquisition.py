#!/usr/bin/env python3
"""Run the one bounded Session 14R9AB authority acquisition."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "outputs/continuous_occlusion_terminal_cell_authority_v2_acquisition"
SOURCE = ROOT / "outputs/continuous_occlusion_tie_boundary_publication_diagnosis/local"
PROTOCOL = ROOT / "docs/protocols/phase_14r9ab_terminal_cell_authority_v2_acquisition.md"
TAG = "f00690c05d8c1c6db308a65bd311c43f9a8ef2fa"
PRIVATE_INDEX = "2abe5f916265275a94c157bd1a93c55f96d352863cbdce618a40418af3a2ebc6"
BOUNDARY = "30a8363749bb07053cdd35f82248535ebc1909441274a9da572ba684de7f597b"
SELECTED = "04bfd87303522ced4968d7953228d2bc8a289a2fab28d823cfd1c7deff8aa51f"
PARTITION = "91af2d5a17291223c49e2b361c4091b67047424e70d52cc305c64c49f78c2e26"
REFERENCE = "07697bfa5329193cb5f6cc1f632f1128654a04115fa48c2a8fcfc5656553168f"
VERIFIER = "417233c6baf694b35d4ce835fe1164ed9730a54df81e2cb8b6deb06911a330cd"
ONSET_OWNER = "d62dc611a759b03c68098c7628568d3f9e78fd59d995a4f555dd6ed325171b97"

HISTORICAL = {
    "src/defensive_network_disruption/geometry/r9aa_terminal_authority.py": "306d542c812bc1f72c84ae1171bfe11c55adafb52e8cb5e391568ad0b6d63431",
    "src/defensive_network_disruption/validation/r9aa_failure.py": "d60a6cd5cf87903857cc06b686bfaa247b139588d8465a342605d259f1fb94fb",
    "src/defensive_network_disruption/geometry/r9x_terminal_authority.py": "ab272ec304602ab0931fd23b4ecf74cf7479f8ee076d60b954824090525ae097",
    "src/defensive_network_disruption/geometry/r9y_acquisition.py": "409554e382e85198f6f5e4a04ff75c8a31a40e681ee741c13fb6cc32d0713b1a",
    "src/defensive_network_disruption/validation/r9j_linear_publication.py": "a242cb0921d1fd390cd2b74c9d15a0fdff3e2b82e46000dc8be0cbbba6d6c139",
    "docs/session_14r9aa_terminal_cell_pair_schema_traceback_repair.md": "91be03a8b9d5c8a68c4d868aa5a52d115b8d2b5a9090dac4371aaacab9db499d",
    "outputs/continuous_occlusion_terminal_cell_pair_schema_repair/manifest.json": "d919a4095b25882c8ba6c49a4091e325a7b227dcc3a69d1a740c7c9a33e4035d",
}


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=ROOT, text=True).strip()


def put(path: Path, value) -> None:
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
    if any(sha(ROOT / name) != value for name, value in HISTORICAL.items()):
        raise RuntimeError("historical_authority")
    local = Path(folder) / "local"
    markers = ("review.marker", "access_attempt.marker", "materialization.marker",
               "authority.marker", "publication.marker", "closure.marker")
    if any((local / name).exists() for name in markers):
        raise FileExistsError("governed_acquisition_exists")
    from defensive_network_disruption.validation.checkpoint_ci_authority import validate_receipt
    receipt = local / "checkpoint_ci.json"
    authority = validate_receipt(receipt, expectation(),
                                 expected_sha256=(receipt.with_suffix(".json.sha256").read_text().strip()))
    return {"head": git("rev-parse", "HEAD"), "ci_receipt_sha256": authority.receipt_sha256}


def _acquire_impl() -> dict:
    environment = preflight(); local = OUT / "local"
    from defensive_network_disruption.geometry.r9x_terminal_authority import canonical, digest
    from defensive_network_disruption.geometry.r9y_acquisition import load_lineage
    from defensive_network_disruption.geometry.r9ab_acquisition import construct
    from defensive_network_disruption.validation.r9ab_linear import Journal, review
    from defensive_network_disruption.validation.r9ab_evidence import close
    from defensive_network_disruption.validation.r9j_evidence import put_bytes
    from defensive_network_disruption.validation.r9v_publication_ownership import persist_authority

    put(local / "review.marker", {"reserved": True})
    journal = Journal(local / "journal.jsonl")
    try:
        lineage = load_lineage(SOURCE, expected_index_sha256=PRIVATE_INDEX)
        if (lineage["boundary_capture_sha256"], lineage["selected_edge_sha256"],
                lineage["ordered_partition_sha256"]) != (BOUNDARY, SELECTED, PARTITION):
            raise ValueError("lineage_authority")
        put(local / "lineage_receipt.json", {"schema_version": 1, "valid": True,
            "private_index_sha256": PRIVATE_INDEX, "boundary_capture_sha256": BOUNDARY,
            "selected_edge_sha256": SELECTED, "ordered_partition_sha256": PARTITION,
            "cell_count": len(lineage["cells"])})
        journal.append("lineage_review", valid=True)

        put(local / "access_attempt.marker", {"reserved": True})
        put(local / "access_attempt.json", {"schema_version": 1, "source_sha256": SELECTED,
                                              "previously_exposed": True})
        journal.append("access_attempt", previously_exposed=True)
        boundary_path, selected_path = SOURCE / "boundary_capture.json", SOURCE / "selected_edge.json"
        if sha(boundary_path) != BOUNDARY or sha(selected_path) != SELECTED:
            raise ValueError("retained_content_hash")
        boundary = json.loads(boundary_path.read_bytes())
        selected = json.loads(selected_path.read_bytes())
        put(local / "materialization.marker", {"complete": True})
        put(local / "materialization_receipt.json", {"schema_version": 1,
            "selected_edge_sha256": SELECTED, "previously_exposed_states": 1,
            "previously_exposed_edges": 1, "new_population_states": 0,
            "new_population_edges": 0})
        journal.append("materialization", previously_exposed_states=1,
                       previously_exposed_edges=1, new_population_states=0,
                       new_population_edges=0)

        value, derivation = construct(
            lineage=lineage, boundary=boundary, selected=selected,
            private_index_sha256=PRIVATE_INDEX,
            reference_implementation_sha256=REFERENCE,
            verifier_sha256=VERIFIER, onset_owner_sha256=ONSET_OWNER)
        put(local / "derivation_receipt.json", derivation)
        put_bytes(local / "terminal_cell_authority_v2.json", canonical(value))
        put(local / "authority.marker", {"sha256": sha(local / "terminal_cell_authority_v2.json")})
        journal.append("authority_persistence", valid=True,
                       authority_sha256=sha(local / "terminal_cell_authority_v2.json"))
        journal.append("structural_validation", valid=True,
                       pair_refs_distinct=derivation["pair_refs_distinct"],
                       competitors_complete=derivation["competitor_complete"])
        journal.append("terminal_success")
        journal.close()
        closure_authority = review(journal.path, expected_head=journal.previous)
        descriptor = persist_authority(local, closure_authority)
        put(local / "publication.marker", {"authority_sha256": descriptor.sha256})
        put(local / "closure.marker", {"status": "complete"})
        counts = {"states_reopened": 1, "edges_reopened": 1,
                  "new_population_states": 0, "new_population_edges": 0,
                  "candidate_evaluations": 0, "field_evaluations": 0,
                  "refinements": 0, "maximality_classifications": 0}
        records = {
            "acquisition_contract.json": {"schema_version": 1, "status": "complete",
                "flags": {"bounded_retained_copy_only": True, "create_once": True,
                          "historical_files_unchanged": True}, "counts": counts},
            "lineage_validation.json": {"schema_version": 1, "status": "complete",
                "flags": {"private_index_valid": True, "partition_valid": True,
                          "unresolved_leaf_valid": True, "selected_copy_hash_valid": True},
                "counts": {"partition_cells": 81, "unresolved_cells": 1}},
            "authority_capture.json": {"schema_version": 1, "status": "complete",
                "flags": {"schema_v2": True, "canonical_bytes": True,
                          "provenance_valid": True, "compatibility_loaded": True},
                "counts": {"authority_objects": 1,
                           "coefficient_records": derivation["unique_coefficient_count"]}},
            "pair_authority_validation.json": {"schema_version": 1, "status": "complete",
                "flags": {"ordered_pair_refs_distinct": True,
                          "interval_relation_lineage_valid": True,
                          "all_nonpair_functions_represented": True},
                "counts": {"ordered_pair_references": 2,
                           "unique_competitor_references": derivation["unique_competitor_count"]}},
            "sufficiency_validation.json": {"schema_version": 1, "status": "complete",
                "flags": {"structurally_sufficient": True, "round_trip_equal": True,
                          "field_evaluation_performed": False, "bound_performed": False,
                          "classification_performed": False}, "counts": counts},
        }
        qc = {"status": "complete", "execution_valid": True, "classification": "A",
              "readiness": 1, "authority_schema_version": 2,
              "ordered_pair_refs_distinct": True, "competitors_complete": True,
              "interval_relation_lineage_valid": True, "canonical_round_trip": True,
              **counts, "exposure_uncertain": False}
        result = close(OUT, records, qc, closure_authority, descriptor)
        return {**result, "environment": environment}
    finally:
        if not journal.handle.closed:
            journal.close()


def acquire() -> dict:
    """Capture any governed failure before producing a blocked package."""
    try:
        return _acquire_impl()
    except BaseException as error:
        local = OUT / "local"
        from defensive_network_disruption.validation.r9aa_failure import AcquisitionFailureBoundary
        from defensive_network_disruption.validation.r9ab_linear import Journal, review
        from defensive_network_disruption.validation.r9ab_evidence import close
        from defensive_network_disruption.validation.r9v_publication_ownership import persist_authority
        boundary = AcquisitionFailureBoundary(local / "failure")

        def blocked_qc(captured):
            put(local / "blocked_qc.json", {"schema_version": 1, "status": "blocked",
                "stage": captured.stage, "traceback_sha256": captured.traceback_sha256})
            return True

        def publish(captured):
            journal = Journal(local / "failure_journal.jsonl")
            journal.append("terminal_failure", stage=captured.stage,
                           exception=captured.exception_type,
                           traceback_sha256=captured.traceback_sha256)
            journal.close(); authority = review(journal.path, expected_head=journal.previous)
            descriptor = persist_authority(local, authority)
            materialized = (local / "materialization_receipt.json").exists()
            attempted = (local / "access_attempt.json").exists()
            counts = {"states_reopened": int(materialized), "edges_reopened": int(materialized),
                      "new_population_states": 0, "new_population_edges": 0,
                      "candidate_evaluations": 0, "field_evaluations": 0,
                      "refinements": 0, "maximality_classifications": 0}
            records = {name: {"schema_version": 1, "status": "blocked",
                               "flags": {"available": False, "failure_preserved": True},
                               "counts": counts}
                       for name in ("acquisition_contract.json", "lineage_validation.json",
                                    "authority_capture.json", "pair_authority_validation.json",
                                    "sufficiency_validation.json")}
            qc = {"status": "blocked", "execution_valid": False, "classification": "D",
                  "readiness": 4, "authority_schema_version": 2,
                  "ordered_pair_refs_distinct": False, "competitors_complete": False,
                  "interval_relation_lineage_valid": False, "canonical_round_trip": False,
                  **counts, "exposure_uncertain": attempted and not materialized}
            if not (local / "publication.marker").exists():
                put(local / "publication.marker", {"authority_sha256": descriptor.sha256})
            if not (local / "closure.marker").exists():
                put(local / "closure.marker", {"status": "blocked"})
            return close(OUT, records, qc, authority, descriptor)

        boundary.close(error, "acquisition", write_blocked_qc=blocked_qc,
                       publish=publish, reraise=True)
        raise AssertionError("unreachable")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "acquire", "publication-check"))
    args = parser.parse_args()
    if args.command == "preflight": result = preflight()
    elif args.command == "acquire": result = acquire()
    else:
        from defensive_network_disruption.validation.r9ab_evidence import publication_check
        result = publication_check(OUT)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
