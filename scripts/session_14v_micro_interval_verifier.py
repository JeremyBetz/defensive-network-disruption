#!/usr/bin/env python3
"""Session 14v bounded micro-interval verifier and single-edge regression."""
from __future__ import annotations

import argparse
import ast
import csv
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import traceback
import warnings

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import scipy

from defensive_network_disruption.data.prepared_equivalence_gate import require_historical_prepared_bytes
from defensive_network_disruption.data.representation_projection import project_line
from defensive_network_disruption.geometry import micro_interval_verifier as repaired
from defensive_network_disruption.geometry import production_verification as historical
from defensive_network_disruption.geometry.max_warning_diagnosis import (
    controlled_diagnostic, maximum_function,
)
from defensive_network_disruption.geometry.occlusion_fields import CANDIDATES


START = "cc8cb1a7c5c6706ef9db6e0c74d41c32f7fe54d5"
TAG = "f00690c05d8c1c6db308a65bd311c43f9a8ef2fa"
PROTOCOL = Path("docs/protocols/phase_14v_micro_interval_verifier.md")
OUT = Path("outputs/continuous_occlusion_micro_interval_verifier")
LOCAL = OUT / "local"
POPULATION = Path("outputs/receiver_ranking_m0_m1/local/population.jsonl")
PREPARED = Path("outputs/continuous_occlusion_retry/local/prepared.jsonl")
REFERENCE = Path("outputs/continuous_occlusion_numerics_14b/reference_summary.json")
UNRESOLVED = Path("outputs/continuous_occlusion_max_switching/unresolved_case_comparison.csv")
HISTORICAL = Path("outputs/continuous_occlusion_production_acceptance/reference_comparison.csv")
SOURCE_FIXTURES = Path("scripts/session_14_occlusion_fields.py")
R14I = Path("outputs/continuous_occlusion_production_acceptance/manifest.json")
R14R = Path("outputs/continuous_occlusion_retry/manifest.json")
R14U = Path("outputs/continuous_occlusion_warning_diagnosis_resumed/manifest.json")
EXPECTED = {
    str(R14I): "1c65769260cc6e1b8a79b69129b3b5a227d4a0a41aec93be4533168a042ace88",
    str(R14R): "8a639f7a2b29a6aec026e176d80d8901b28839b0d2091dd0256751d77b6f70ed",
    str(R14U): "fbcef2b81b9adea67cccd68e9db26990ff3e2825f77ce98a4e37b047b488896d",
    str(POPULATION): "cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d",
    str(PREPARED): "15a809060f0ba4a8cb3790011dab8008db3dad6e931c287ccb395f61ef1530b0",
}
CODE = (
    Path("scripts/session_14v_micro_interval_verifier.py"),
    Path("src/defensive_network_disruption/geometry/micro_interval_verifier.py"),
    Path("tests/test_session14v_micro_interval.py"),
)
PUBLIC = (
    "contract.json", "synthetic_micro_interval_oracles.csv",
    "synthetic_reference_regression.csv", "failing_edge_regression.json",
    "residual_summary.json", "qc.json",
)
REFERENCE_COLUMNS = (
    "fixture", "candidate", "component", "intervals", "estimate", "reference",
    "absolute_error", "reference_interval_lower", "reference_interval_upper",
    "point_to_interval_distance", "passed",
)
ORACLE_COLUMNS = (
    "fixture", "structural_pieces", "bounded_pieces", "quadrature_pieces",
    "residual_bound", "exact_integral", "interval_lower", "interval_upper", "contained",
)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def safe(relative: Path | str) -> Path:
    relative = Path(relative)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("unsafe_path")
    path = ROOT / relative
    if any(item.is_symlink() for item in (path, *path.parents)):
        raise ValueError("symlink_rejected")
    if not path.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError("path_escape")
    return path


def digest(relative: Path | str) -> str:
    handle = hashlib.sha256()
    with safe(relative).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            handle.update(block)
    return handle.hexdigest()


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def read_json(relative: Path | str):
    return json.loads(safe(relative).read_text(), object_pairs_hook=no_duplicates,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite_json")))


def committed(relative: Path | str) -> None:
    if safe(relative).read_bytes() != subprocess.check_output(
            ["git", "show", f"HEAD:{relative}"], cwd=ROOT):
        raise ValueError("uncommitted_authority")


def atomic_text(relative: Path | str, value: str) -> None:
    destination = safe(relative)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError("output_exists")
    temporary = destination.with_name("." + destination.name + ".tmp")
    with temporary.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(value)
    temporary.replace(destination)


def atomic_json(name: str, value, *, private=False) -> None:
    base = LOCAL if private else OUT
    atomic_text(base / name, json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")


def environment() -> dict[str, str]:
    return {"python": platform.python_version(), "numpy": np.__version__,
            "scipy": scipy.__version__, "lock_sha256": digest("uv.lock")}


def source_hashes() -> dict[str, str]:
    return {name: digest(name) for name in EXPECTED}


def preservation() -> None:
    git("merge-base", "--is-ancestor", START, "HEAD")
    if git("rev-parse", "v0.1.0^{}") != TAG:
        raise ValueError("release_tag_changed")
    changes = set(git("diff", "--name-only", START).splitlines())
    allowed = {str(PROTOCOL), *map(str, CODE),
               "docs/session_14v_micro_interval_verifier.md", "docs/research_log.md"}
    if any(path not in allowed and not path.startswith(str(OUT) + "/") for path in changes):
        raise ValueError("historical_file_changed")
    old_log = subprocess.check_output(["git", "show", f"{START}:docs/research_log.md"], cwd=ROOT)
    if not safe("docs/research_log.md").read_bytes().startswith(old_log):
        raise ValueError("research_log_rewritten")


def preflight() -> None:
    if git("status", "--porcelain"):
        raise ValueError("clean_tree_required")
    for path in (PROTOCOL, *CODE):
        committed(path)
    preservation()
    if source_hashes() != EXPECTED:
        raise ValueError("source_authority_changed")
    if subprocess.run(["git", "check-ignore", "-q", str(LOCAL / "probe")], cwd=ROOT).returncode:
        raise ValueError("local_storage_not_ignored")
    print("Session 14v preflight passed; no numerical execution or authorized edge access")


def fixture_rows():
    source = safe(SOURCE_FIXTURES).read_text()
    function = next(node for node in ast.parse(source).body
                    if isinstance(node, ast.FunctionDef) and node.name == "fixtures")
    namespace = {}
    exec(compile(ast.Module(body=[function], type_ignores=[]),
                 "<frozen synthetic fixtures>", "exec"), namespace)
    rows = tuple(namespace["fixtures"]())
    historical.require(len(rows) == 36, "fixture_count")
    return rows


def authority_cases():
    rows = read_json(REFERENCE)["records"]
    references = {(row["fixture"], row["candidate"], row["component"]): row["reference"]
                  for row in rows if row["available"]}
    missing = {(row["fixture"], row["candidate"], row["component"])
               for row in rows if not row["available"]}
    with safe(UNRESOLVED).open(newline="") as stream:
        replacements = list(csv.DictReader(stream))
    historical.require(len(references) == 362 and len(rows) == 366 and len(replacements) == 4,
                       "reference_counts")
    historical.require({(row["fixture"], row["candidate"], "maximum")
                        for row in replacements} == missing, "reference_keys")
    for row in replacements:
        historical.require(row["available"] == "True", "replacement_unavailable")
        references[row["fixture"], row["candidate"], "maximum"] = float(row["piecewise_reference"])
    with safe(HISTORICAL).open(newline="") as stream:
        historical_rows = list(csv.DictReader(stream))
    vectors = {}
    for row in historical_rows:
        item = vectors.setdefault((row["fixture"], row["candidate"]),
                                  {"intervals": int(row["intervals"]), "estimates": {}})
        item["estimates"][row["component"]] = float(row["estimate"])
    for label, origin, receiver, defenders in fixture_rows():
        for candidate in CANDIDATES:
            yield label, {
                "candidate": candidate, "origin": origin, "receiver": receiver,
                "defenders": defenders,
                "references": {key[2]: value for key, value in references.items()
                               if key[:2] == (label, candidate)},
                "historical_vector": vectors[label, candidate],
                "historical_failure": (label, candidate, "maximum") in missing,
            }


def run_synthetic_acceptance():
    cases = []
    comparison = []
    for label, case in authority_cases():
        result = repaired.verify_case(**case)
        cases.append(result)
        maximum_interval = result["maximum"]["piecewise"]
        for component, estimate in result["estimates"].items():
            reference = case["references"][component]
            if component == "maximum":
                lower, upper = maximum_interval.lower, maximum_interval.upper
                interval_error = repaired.point_interval_distance(reference, maximum_interval)
            else:
                lower = upper = reference
                interval_error = abs(estimate - reference)
            comparison.append({
                "fixture": label, "candidate": case["candidate"], "component": component,
                "intervals": result["intervals"], "estimate": estimate, "reference": reference,
                "absolute_error": result["errors"][component],
                "reference_interval_lower": lower, "reference_interval_upper": upper,
                "point_to_interval_distance": interval_error, "passed": True,
            })
    historical.require(len(cases) == 108 and len(comparison) == 366, "acceptance_counts")
    historical.require(sum(row["permutations"] for row in cases) == 399, "permutation_count")
    return cases, comparison


def micro_oracles():
    budget = repaired.GLOBAL_RESIDUAL_BUDGET
    threshold = budget / 2
    below = float(np.nextafter(threshold, 0.0))
    above = float(np.nextafter(threshold, math.inf))
    definitions = (
        ("ordinary", (0.0, .25, 1.0), .4),
        ("onset_adjacent", (0.0, .5, float(np.nextafter(.5, 1.0)), 1.0), .7),
        ("switch_adjacent", (0.0, float(np.nextafter(.5, 0.0)), .5, 1.0), .3),
        ("endpoint_adjacent", (0.0, float(np.nextafter(0.0, 1.0)), 1.0), 1.0),
        ("multiple", (0.0, 1e-14, 2e-14, .5, 1.0), .8),
        ("threshold_below", (0.0, below, 1.0), .5),
        ("threshold_above", (0.0, above, 1.0), .5),
        ("zero", (0.0, 1e-14, 1.0), 0.0),
        ("field_one", (0.0, 1e-14, 1.0), 1.0),
    )
    rows = []
    for name, partitions, value in definitions:
        function = lambda t, value=value: np.full((len(t), 1), value, dtype=np.float64)
        result = repaired.bounded_adaptive_maximum(function, partitions, 1e-13)
        exact = value
        contained = result.lower <= exact <= result.upper
        historical.require(contained, "oracle_not_contained")
        rows.append({
            "fixture": name, "structural_pieces": result.structural_piece_count,
            "bounded_pieces": result.bounded_piece_count,
            "quadrature_pieces": result.quadrature_piece_count,
            "residual_bound": result.residual_bound, "exact_integral": exact,
            "interval_lower": result.lower, "interval_upper": result.upper,
            "contained": contained,
        })
    historical.require(next(row for row in rows if row["fixture"] == "threshold_below")["bounded_pieces"] == 1,
                       "below_threshold_not_bounded")
    historical.require(next(row for row in rows if row["fixture"] == "threshold_above")["bounded_pieces"] == 0,
                       "above_threshold_bounded")
    return rows


def one_line(relative: Path, ordinal: int) -> str:
    if ordinal != 1:
        raise PermissionError("only_ordinal_1_authorized")
    with safe(relative).open(encoding="utf-8") as stream:
        for index, line in enumerate(stream):
            if index == ordinal:
                return line
    raise ValueError("ordinal_1_unavailable")


def authorized_edge():
    canonical = one_line(POPULATION, 1)
    preserved = one_line(PREPARED, 1).encode("utf-8")
    _, reconstructed = project_line(canonical)
    require_historical_prepared_bytes(reconstructed, preserved)
    row = json.loads(preserved, object_pairs_hook=no_duplicates)
    return row, row["receivers"][7]


def edge_regression():
    row, receiver = authorized_edge()
    field, _, _, defenders, individual, onset, envelope, partitions = maximum_function(
        "constant_width", row["carrier"], receiver, row["defenders"])
    widths = [upper - lower for lower, upper in zip(partitions[:-1], partitions[1:], strict=True)]
    historical.require(len(widths) == 12 and len(envelope.switches) == 1 and
                       len(envelope.tie_intervals) == 0, "edge_structure_changed")
    micro_width = 3.3306690738754696e-15
    historical.require(micro_width in widths, "known_micro_piece_missing")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        checked = repaired.maximum_checks(individual, envelope, onset, False)
    integration_warnings = [item for item in caught
                            if item.category.__name__ == "IntegrationWarning"]
    historical.require(not integration_warnings, "integration_warning_remains")
    controlled, estimates = controlled_diagnostic(field, row["carrier"], receiver, row["defenders"])
    historical.require(controlled["converged"] and controlled["finite"] and
                       controlled["deterministic"] and controlled["intervals"] == 2048,
                       "joint_simpson_changed")
    interval = checked["piecewise"]
    historical.require(interval.structural_piece_count == 12 and
                       interval.bounded_piece_count == 1 and
                       interval.quadrature_piece_count == 11, "micro_routing_changed")
    prior = read_json("outputs/continuous_occlusion_warning_diagnosis_resumed/method_comparison.json")
    for name, value, tolerance in (
        ("unsplit", prior["methods"]["unsplit_adaptive"], 1e-10),
        ("direct", prior["methods"]["direct_simpson_65536"], 1e-9),
        ("split32", prior["methods"]["split_simpson_32768"], 1e-10),
        ("split65", prior["methods"]["split_simpson_65536"], 1e-10),
        ("joint", estimates["maximum"], 1e-6),
    ):
        historical.require(repaired.point_interval_distance(value, interval) <= tolerance,
                           f"edge_{name}_agreement")
    return {
        "schema_version": 1, "zero_based_row_ordinal": 1,
        "candidate": "constant_width", "receiver_ordinal": 7,
        "structural_piece_count": 12, "switch_count": 1, "tie_interval_count": 0,
        "certified_enclosure_endpoint_count": 0,
        "known_micro_width": micro_width, "bounded_piece_count": interval.bounded_piece_count,
        "quadrature_piece_count": interval.quadrature_piece_count,
        "residual_bound": interval.residual_bound,
        "reference_interval": [interval.lower, interval.upper],
        "integration_warning_count": len(integration_warnings),
        "joint_simpson_intervals": controlled["intervals"],
        "joint_simpson_maximum": estimates["maximum"],
        "joint_point_to_interval_distance": repaired.point_interval_distance(
            estimates["maximum"], interval),
        "additional_states_opened": 0, "additional_edges_opened": 0,
    }


def ledger(status: str) -> None:
    path = safe(LOCAL / "access.jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps({"time": datetime.now(timezone.utc).isoformat(),
                                 "stage": "audit", "status": status,
                                 "head": git("rev-parse", "HEAD")}) + "\n")


def begin() -> None:
    if any(safe(OUT / name).exists() for name in (*PUBLIC, "manifest.json")):
        raise FileExistsError("closed_no_rerun")
    historical.claim_execution(safe(LOCAL / "audit.marker"))
    ledger("started")


def write_csv(name: str, columns, rows) -> None:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader(); writer.writerows(rows)
    atomic_text(OUT / name, stream.getvalue())


def close_manifest(status: str) -> None:
    existing = [name for name in PUBLIC if safe(OUT / name).exists()]
    atomic_json("manifest.json", {
        "schema_version": 1, "status": status, "start": START,
        "protocol_sha256": digest(PROTOCOL),
        "implementation": {str(path): digest(path) for path in CODE},
        "environment": environment(), "sources": EXPECTED,
        "outputs": {name: digest(OUT / name) for name in existing},
        "unavailable": [name for name in PUBLIC if name not in existing],
    })


def audit() -> None:
    preflight(); begin()
    try:
        oracle_rows = micro_oracles()
        cases, reference_rows = run_synthetic_acceptance()
        edge = edge_regression()
        residuals = [case["maximum"]["piecewise"].residual_bound for case in cases]
        bounded_counts = [case["maximum"]["piecewise"].bounded_piece_count for case in cases]
        contract = {
            "schema_version": 1, "field_bounds": [0.0, 1.0],
            "global_residual_budget": repaired.GLOBAL_RESIDUAL_BUDGET,
            "allocation": "global_budget / positive_structural_piece_count",
            "eligibility": "upper_bound * realized_float64_width <= allocation",
            "eligible_piece_interval": "[0, upper_bound * width]",
            "structural_partitions_preserved": True, "interval_merging": False,
            "joint_simpson_changed": False,
        }
        write_json = atomic_json
        write_json("contract.json", contract)
        write_csv("synthetic_micro_interval_oracles.csv", ORACLE_COLUMNS, oracle_rows)
        write_csv("synthetic_reference_regression.csv", REFERENCE_COLUMNS, reference_rows)
        write_json("failing_edge_regression.json", edge)
        write_json("residual_summary.json", {
            "schema_version": 1, "synthetic_cases": len(cases),
            "synthetic_references": len(reference_rows),
            "synthetic_permutations": sum(case["permutations"] for case in cases),
            "cases_with_bounded_pieces": sum(count > 0 for count in bounded_counts),
            "total_bounded_pieces": sum(bounded_counts),
            "maximum_case_residual_bound": max(residuals),
            "global_residual_budget": repaired.GLOBAL_RESIDUAL_BUDGET,
            "failing_edge_residual_bound": edge["residual_bound"],
        })
        write_json("qc.json", {
            "schema_version": 1, "status": "closed", "classification": "A",
            "classification_text": "Bounded-residual verifier repair succeeds",
            "retry_readiness": 1, "synthetic_cases_passed": len(cases),
            "references_passed": len(reference_rows),
            "permutations_passed": sum(case["permutations"] for case in cases),
            "empirical_states_opened": 1, "empirical_edges_opened": 1,
            "additional_states_opened": 0, "additional_edges_opened": 0,
            "integration_warnings": edge["integration_warning_count"],
            "joint_simpson_changed": False,
            "targets_outcomes_models_shares_accessed": False,
            "protected_or_withheld_access": False, "failure": None,
        })
        close_manifest("closed"); ledger("closed")
        print("Session 14v audit closed: A, readiness 1")
    except Exception as error:
        atomic_json("failure.json", {"type": type(error).__name__, "message": str(error),
                                     "traceback": traceback.format_exc()}, private=True)
        if not safe(OUT / "qc.json").exists():
            atomic_json("qc.json", {"schema_version": 1, "status": "invalid",
                "classification": "F", "classification_text": "Invalid",
                "retry_readiness": 4, "synthetic_cases_passed": 0,
                "references_passed": 0, "permutations_passed": 0,
                "empirical_states_opened": 0, "empirical_edges_opened": 0,
                "additional_states_opened": 0, "additional_edges_opened": 0,
                "integration_warnings": 0, "joint_simpson_changed": False,
                "targets_outcomes_models_shares_accessed": False,
                "protected_or_withheld_access": False, "failure": type(error).__name__})
        close_manifest("invalid"); ledger("failed")
        raise


def finite(value) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("nonfinite_public_value")
    if isinstance(value, dict):
        for item in value.values(): finite(item)
    elif isinstance(value, list):
        for item in value: finite(item)


def publication_check() -> None:
    preservation()
    if source_hashes() != EXPECTED:
        raise ValueError("source_authority_changed")
    for path in (PROTOCOL, *CODE): committed(path)
    manifest = read_json(OUT / "manifest.json")
    required = {"schema_version", "status", "start", "protocol_sha256", "implementation",
                "environment", "sources", "outputs", "unavailable"}
    if set(manifest) != required or manifest["protocol_sha256"] != digest(PROTOCOL):
        raise ValueError("manifest_authority")
    if manifest["implementation"] != {str(path): digest(path) for path in CODE}:
        raise ValueError("implementation_binding")
    if manifest["sources"] != EXPECTED or set(manifest["outputs"]) != set(PUBLIC):
        raise ValueError("source_or_output_membership")
    for name, expected in manifest["outputs"].items():
        if digest(OUT / name) != expected:
            raise ValueError("output_hash_changed")
        text = safe(OUT / name).read_text()
        for forbidden in ("/Users/", "/private/", "event_id", "carrier_xy", "candidate_xy",
                          "defender_xy", "target_index", "access_token", "X-Amz-Signature"):
            if forbidden in text:
                raise ValueError("publication_boundary")
        if name.endswith(".json"): finite(read_json(OUT / name))
        elif b"\r" in safe(OUT / name).read_bytes(): raise ValueError("csv_newline")
    qc = read_json(OUT / "qc.json")
    if qc["status"] == "closed":
        if not (qc["classification"] == "A" and qc["retry_readiness"] == 1 and
                qc["synthetic_cases_passed"] == 108 and qc["references_passed"] == 366 and
                qc["permutations_passed"] == 399 and qc["integration_warnings"] == 0):
            raise ValueError("success_schema")
    print(f"Session 14v publication checks passed: {manifest['status']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "audit", "publication-check"))
    command = parser.parse_args().command
    {"preflight": preflight, "audit": audit,
     "publication-check": publication_check}[command]()


if __name__ == "__main__":
    main()
