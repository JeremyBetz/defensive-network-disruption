#!/usr/bin/env python3
"""Metadata-only R9X evidence-retention review."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
START = "1263402fcb37f9d1a090b305f67c156c12a76af2"
TAG = "f00690c05d8c1c6db308a65bd311c43f9a8ef2fa"
PROTOCOL = ROOT / "docs/protocols/phase_14r9x_terminal_cell_evidence_retention_review.md"
OUT = ROOT / "outputs/continuous_occlusion_terminal_cell_evidence_retention"
R9V = ROOT / "outputs/continuous_occlusion_tie_boundary_publication_diagnosis"
EXPECTED = {
    "docs/protocols/phase_14r9v_tie_boundary_and_publication_diagnosis.md": "20710c4420dd988c5aafa68d16f487f90d7341cc86f1278ba2937f134c5302d5",
    "docs/session_14r9v_tie_boundary_and_publication_diagnosis.md": "cded89e4cb5dd074e1f2e47e03aef620f7134faaac75f0b599e1c2e679332ebf",
    "outputs/continuous_occlusion_tie_boundary_publication_diagnosis/manifest.json": "2d1424ae401dfb83a38aea4af2539c394fff024188a6348df072d997340301b8",
    "src/defensive_network_disruption/geometry/r9v_tie_diagnosis.py": "07697bfa5329193cb5f6cc1f632f1128654a04115fa48c2a8fcfc5656553168f",
    "src/defensive_network_disruption/geometry/r9r_localization.py": "9768323ec258c18949faa1798781d6f67b635ad34c7d08d698ff67c8f8c11070",
    "src/defensive_network_disruption/validation/r9v_publication_ownership.py": "fe7b011b0e311e03045e5a2dec1985e29b6350d45895075058249b7a7832e66f",
}
PRIVATE_INDEX_SHA256 = "2abe5f916265275a94c157bd1a93c55f96d352863cbdce618a40418af3a2ebc6"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(*args):
    return subprocess.check_output(("git", *args), cwd=ROOT, text=True).strip()


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def put(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_name("." + path.name + ".pending")
    with pending.open("xb") as handle:
        handle.write(canonical(value)); handle.flush(); os.fsync(handle.fileno())
    os.link(pending, path); pending.unlink()
    descriptor = os.open(path.parent, os.O_RDONLY)
    try: os.fsync(descriptor)
    finally: os.close(descriptor)


def preflight(folder=OUT):
    if git("status", "--porcelain"):
        raise RuntimeError("dirty_tree")
    head = git("rev-parse", "HEAD")
    if head != git("rev-parse", "origin/main"):
        raise RuntimeError("tracking_mismatch")
    git("merge-base", "--is-ancestor", START, head)
    if git("rev-parse", "v0.1.0^{}") != TAG:
        raise RuntimeError("release_target")
    for name, expected in EXPECTED.items():
        if sha(ROOT / name) != expected:
            raise RuntimeError("inherited_authority_hash")
    if sha(R9V / "local/private_index.json") != PRIVATE_INDEX_SHA256:
        raise RuntimeError("private_index_hash")
    tracked = git("ls-files", "*r9x*", str(PROTOCOL.relative_to(ROOT))).splitlines()
    for name in tracked:
        if subprocess.check_output(("git", "show", "HEAD:" + name), cwd=ROOT) != (ROOT / name).read_bytes():
            raise RuntimeError("implementation_freshness")
    if (Path(folder) / "local/review.marker").exists():
        raise FileExistsError("governed_review_exists")
    return {"head": head, "release": TAG, "protocol_sha256": sha(PROTOCOL),
            "runner_sha256": sha(Path(__file__))}


def _metadata_review():
    index_path = R9V / "local/private_index.json"
    index = json.loads(index_path.read_text())
    if set(index) != {"schema_version", "files"} or index["schema_version"] != 1:
        raise ValueError("r9v_private_index_schema")
    files = index["files"]
    required = {"boundary_capture.json", "selected_edge.json", "reference_result.json"}
    if not required.issubset(files):
        raise ValueError("r9v_required_record")
    cells = sorted(name for name in files if name.startswith("reference_reference_cell_"))
    if len(cells) != 81:
        raise ValueError("r9v_cell_count")
    rows = []
    for name in cells:
        path = R9V / "local" / name
        if sha(path) != files[name]:
            raise ValueError("r9v_cell_hash")
        row = json.loads(path.read_text())
        if set(row) != {"ordinal", "depth", "pair_status", "maximum_status"}:
            raise ValueError("r9v_cell_schema")
        if type(row["ordinal"]) is not int or type(row["depth"]) is not int:
            raise ValueError("r9v_cell_type")
        rows.append(row)
    rows.sort(key=lambda item: item["ordinal"])
    if [row["ordinal"] for row in rows] != list(range(81)):
        raise ValueError("r9v_cell_ordinals")
    counts = {status: sum(row["maximum_status"] == status for row in rows)
              for status in ("maximum", "dominated", "unresolved")}
    if counts != {"maximum": 36, "dominated": 44, "unresolved": 1}:
        raise ValueError("r9v_cell_outcomes")
    source = (ROOT / "src/defensive_network_disruption/geometry/r9v_tie_diagnosis.py").read_text()
    required_source = ("class Cell:", "left: F", "right: F", "fields = tuple(FieldAuthority.from_geometry",
                       "difference, _ = pair_authority.bounds", 'sink("reference_cell"',
                       '"pair_status": cell.pair_status', '"maximum_status": cell.maximum_status')
    if not all(token in source for token in required_source):
        raise ValueError("source_trace_changed")
    partition = [{"ordinal": row["ordinal"], "depth": row["depth"]} for row in rows]
    return {
        "cells": len(rows), "counts": counts,
        "ordered_partition_sha256": hashlib.sha256(canonical(partition)).hexdigest(),
        "boundary_capture_sha256": files["boundary_capture.json"],
        "selected_edge_sha256": files["selected_edge.json"],
        "source_trace_valid": True,
    }


def _loss_entries():
    return [
        {"datum": "cell_lower_bound", "in_memory": True, "retained": False, "loss_boundary": "reference_cell_sink", "future_source": "ordered_partition_derivation"},
        {"datum": "cell_upper_bound", "in_memory": True, "retained": False, "loss_boundary": "reference_cell_sink", "future_source": "ordered_partition_derivation"},
        {"datum": "function_coefficients", "in_memory": True, "retained": False, "loss_boundary": "reference_result_serialization", "future_source": "selected_edge_coefficient_derivation"},
        {"datum": "pair_authority", "in_memory": True, "retained": False, "loss_boundary": "reference_result_serialization", "future_source": "coefficient_hash_references"},
        {"datum": "competitor_authority", "in_memory": True, "retained": False, "loss_boundary": "reference_result_serialization", "future_source": "coefficient_hash_references"},
        {"datum": "branch_onset_state", "in_memory": True, "retained": False, "loss_boundary": "field_bounds_return", "future_source": "derive_from_coefficients_and_bounds"},
        {"datum": "pair_value_enclosure", "in_memory": True, "retained": False, "loss_boundary": "status_reduction", "future_source": "derive_from_coefficients_and_bounds"},
        {"datum": "pair_competitor_enclosure", "in_memory": True, "retained": False, "loss_boundary": "status_reduction", "future_source": "derive_from_coefficients_and_bounds"},
        {"datum": "derivative_enclosure", "in_memory": True, "retained": False, "loss_boundary": "discarded_bounds_component", "future_source": "derive_from_coefficients_and_bounds"},
        {"datum": "refinement_provenance", "in_memory": True, "retained": False, "loss_boundary": "reference_cell_sink", "future_source": "ordered_partition_and_cell_authority"},
    ]


def _field_rows():
    rows = [
        ("cell_ordinal_depth", "REQUIRED", "identifies the unresolved leaf within the retained partition"),
        ("exact_cell_bounds", "REQUIRED", "defines the only permitted refinement domain"),
        ("candidate_formula_authority", "REQUIRED", "fixes mathematical semantics"),
        ("q_dot_cross2_coefficients", "REQUIRED", "reconstructs constant-width functions without geometry"),
        ("pair_coefficient_references", "REQUIRED", "identifies the exact tied mathematical functions"),
        ("all_unique_competitor_references", "REQUIRED", "supports global maximality against every function"),
        ("source_and_implementation_hashes", "REQUIRED", "binds provenance and derivation"),
        ("schema_and_provenance_hash", "REQUIRED", "enforces canonical immutable evidence"),
        ("rho_alpha_beta2", "DERIVABLE", "computed exactly from retained coefficients"),
        ("branch_onset_state", "DERIVABLE", "computed from coefficients and cell bounds"),
        ("value_difference_derivative_bounds", "DERIVABLE", "recomputed by the independent interval route"),
        ("previous_enclosures", "REDUNDANT", "not needed to reproduce a stronger independent bound"),
        ("parent_cell_contents", "REDUNDANT", "lineage hashes and exact leaf bounds suffice"),
        ("production_owner_decisions", "REDUNDANT", "not independent mathematical authority"),
        ("raw_identity_and_geometry", "TOO_EMPIRICAL", "derived coefficient authority is sufficient"),
        ("provider_tracking_rows", "TOO_EMPIRICAL", "outside the bounded retained authority"),
    ]
    return [{"field": field, "disposition": disposition, "reason": reason}
            for field, disposition, reason in rows]


def review(folder=OUT):
    environment = preflight(folder)
    local = Path(folder) / "local"
    put(local / "review.marker", {"reserved": True})
    metadata = _metadata_review()
    put(local / "metadata_review.json", metadata)
    from defensive_network_disruption.geometry.r9x_terminal_authority import (
        FORMULA_SHA256, SOURCE_KEYS, synthetic_sufficiency)
    synthetic = synthetic_sufficiency()
    for row in synthetic:
        put(local / ("synthetic_" + row["fixture"] + ".json"), row)
    all_pass = all(row["passed"] for row in synthetic)
    negative_pass = all(row["passed"] for row in synthetic if row["expected"] == "blocked")
    entries = _loss_entries()
    required = [row["field"] for row in _field_rows() if row["disposition"] == "REQUIRED"]
    derivable = [row["field"] for row in _field_rows() if row["disposition"] == "DERIVABLE"]
    redundant = [row["field"] for row in _field_rows() if row["disposition"] == "REDUNDANT"]
    prohibited = [row["field"] for row in _field_rows() if row["disposition"] == "TOO_EMPIRICAL"]
    records = {
        "retention_contract.json": {
            "schema_version": 1, "status": "complete",
            "flags": {"metadata_only": True, "zero_empirical_access": True,
                      "no_reconstruction": True, "historical_outcomes_preserved": True,
                      "single_writer_preserved": True},
            "counts": {"retained_cells": metadata["cells"], "unresolved_cells": 1,
                       "new_states": 0, "new_edges": 0},
            "authority": {**environment, "r9v_private_index_sha256": PRIVATE_INDEX_SHA256},
        },
        "evidence_loss_trace.json": {"schema_version": 1, "status": "complete",
                                     "entries": entries},
        "minimum_schema.json": {
            "schema_version": 1, "status": "complete", "required": required,
            "derivable": derivable, "redundant": redundant, "prohibited": prohibited,
            "field_schema": {"version": 1, "candidate": "constant_width",
                             "coefficient_fields": ["q", "dot", "cross2"],
                             "source_hash_fields": list(SOURCE_KEYS),
                             "formula_authority_sha256": FORMULA_SHA256},
        },
        "prospective_acquisition.json": {
            "schema_version": 1, "status": "complete",
            "flags": {"selected_copy_only": True, "prepared_population_forbidden": True,
                      "provider_data_forbidden": True, "field_evaluation_forbidden": True,
                      "refinement_forbidden": True, "repair_forbidden": True,
                      "scope_exact": True},
            "counts": {"previously_exposed_states_reopened": 1,
                       "previously_exposed_edges_reopened": 1,
                       "new_population_states": 0, "new_population_edges": 0,
                       "authority_objects": 1},
            "steps": ["validate_r9v_authority", "read_retained_selected_copy",
                      "derive_constant_width_coefficients", "derive_leaf_bounds",
                      "persist_and_validate_one_authority", "stop_before_refinement"],
            "recommendation": "govern_bounded_terminal_cell_authority_acquisition",
        },
    }
    classification = "A" if all_pass and negative_pass and metadata["source_trace_valid"] else "D"
    readiness = 1 if classification == "A" else 4
    qc = {"status": "complete" if classification == "A" else "invalid",
          "execution_valid": classification == "A", "classification": classification,
          "readiness": readiness, "states_accessed": 0, "edges_accessed": 0,
          "empirical_computation": False}
    put(local / "review_result.json", {"classification": classification,
                                        "readiness": readiness, "metadata": metadata,
                                        "synthetic_passed": sum(row["passed"] for row in synthetic)})
    from defensive_network_disruption.validation.r9x_evidence import close
    return close(folder, environment, records, _field_rows(), synthetic, qc)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "review", "publication-check"))
    args = parser.parse_args()
    if args.command == "preflight": result = preflight()
    elif args.command == "review": result = review()
    else:
        from defensive_network_disruption.validation.r9x_evidence import publication_check
        result = publication_check(OUT)
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
