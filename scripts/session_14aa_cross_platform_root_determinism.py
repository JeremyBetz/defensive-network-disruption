#!/usr/bin/env python3
"""Synthetic-only Session 14aa deterministic-boundary diagnostic."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import json
import math
import platform
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np
import scipy

from defensive_network_disruption.geometry.diagnostic_artifact_transport import diagnostic_bytes
from defensive_network_disruption.geometry.occlusion_fields import CANDIDATES, CarrierOriginField
from defensive_network_disruption.geometry.root_partition_determinism import (
    deterministic_directional_onsets,
    deterministic_partitions,
)
from defensive_network_disruption.geometry.vector_reproducibility import component_record, float_bits
from defensive_network_disruption.geometry.verification_repair import find_verified_envelope
from defensive_network_disruption.geometry.micro_interval_verifier import GLOBAL_RESIDUAL_BUDGET

START = "79f327072bce3381e79e2ff68b9d2e35d7ad0112"
TAG = "f00690c05d8c1c6db308a65bd311c43f9a8ef2fa"
PROTOCOL = Path("docs/protocols/phase_14aa_cross_platform_root_determinism.md")
OUT = Path("outputs/cross_platform_root_determinism")
LOCAL = OUT / "local"
HIST_LOCAL = Path("outputs/cross_platform_vector_reproducibility_14z/local_diagnostic.json")
HIST_CI = Path("outputs/cross_platform_vector_reproducibility_14z/ci_diagnostic.json")
HIST_MANIFEST = Path("outputs/cross_platform_vector_reproducibility_14z/manifest.json")
ARTIFACT_NAME = "session14aa-python313-root-diagnostic"
ARTIFACT_FILENAME = "session14aa_ci_diagnostic.json"
WORKFLOW = Path(".github/workflows/session14aa-root-diagnostic.yml")
CODE = (
    Path("scripts/session_14aa_cross_platform_root_determinism.py"),
    Path("src/defensive_network_disruption/geometry/root_partition_determinism.py"),
    Path("tests/test_session14aa_root_determinism.py"),
    WORKFLOW,
)


def safe(path):
    path = Path(path)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("unsafe_path")
    result = ROOT / path
    if any(item.is_symlink() for item in (result, *result.parents)):
        raise ValueError("symlink_rejected")
    return result


def digest(path):
    return hashlib.sha256(safe(path).read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def committed(path):
    if safe(path).read_bytes() != subprocess.check_output(["git", "show", f"HEAD:{path}"], cwd=ROOT):
        raise ValueError("uncommitted_authority")


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def write_once(path, data):
    target = safe(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError("output_exists")
    temporary = target.with_name("." + target.name + ".tmp")
    temporary.write_bytes(data)
    temporary.replace(target)


def read_verified_ci(path, declared_sha):
    path = Path(path)
    if path.name != ARTIFACT_FILENAME or path.is_symlink() or not path.is_file():
        raise ValueError("invalid_diagnostic_artifact")
    raw = path.read_bytes()
    if len(raw) > 2_000_000 or hashlib.sha256(raw).hexdigest() != declared_sha:
        raise ValueError("diagnostic_artifact_hash")
    record = json.loads(raw)
    if diagnostic_bytes(record) != raw:
        raise ValueError("diagnostic_artifact_noncanonical")
    return record, raw


def load_14y():
    path = safe("scripts/session_14y_switch_projection_repair_and_reproducibility.py")
    spec = importlib.util.spec_from_file_location("session14y_frozen", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def environment():
    config = np.__config__.show(mode="dicts").get("Build Dependencies", {})
    def library(name):
        value = config.get(name, {})
        return {"name": str(value.get("name", "unavailable")), "version": str(value.get("version", "unavailable"))}
    return {
        "os": platform.system(), "platform": platform.platform(), "architecture": platform.machine(),
        "python": platform.python_version(), "implementation": platform.python_implementation(),
        "numpy": np.__version__, "scipy": scipy.__version__, "blas": library("blas"), "lapack": library("lapack"),
        "uv_lock_sha256": digest("uv.lock"), "installation": "uv-sync-editable",
    }


def route(candidate, origin, receiver, defenders):
    field = CarrierOriginField(candidate)
    base = np.asarray(origin, dtype=np.float64)
    edge = np.asarray(receiver, dtype=np.float64) - base
    def function(t):
        query = base[None, :] + t[:, None] * edge[None, :]
        return field.individual_values(origin, defenders, query)
    onsets = () if candidate == "isotropic" else deterministic_directional_onsets(origin, receiver, defenders)
    raw_onsets = tuple(item.raw_scalar_result for item in onsets)
    envelope = find_verified_envelope(function, extra_partitions=raw_onsets)
    partitions, switches = deterministic_partitions(function, envelope, onsets)
    widths = [upper - lower for lower, upper in zip(partitions[:-1], partitions[1:], strict=True)]
    threshold = GLOBAL_RESIDUAL_BUDGET / len(widths)
    bounded = [width for width in widths if width <= threshold]
    def boundary(value):
        return None if value is None else [value.outside, value.inside, value.direction, list(value.owners)]
    return {
        "partitions": list(partitions),
        "partition_bits": [float_bits(value) for value in partitions],
        "onsets": [{"defender": item.defender_index, "branch": item.branch,
                    "raw": item.raw_scalar_result, "last_pre": item.last_pre_branch,
                    "canonical": item.canonical, "canonical_bits": float_bits(item.canonical)} for item in onsets],
        "switches": [{"raw": item.raw_solver_result, "last_pre": item.last_pre_switch,
                      "zero_start": item.exact_zero_start, "zero_end": item.exact_zero_end,
                      "canonical": item.canonical, "canonical_bits": float_bits(item.canonical),
                      "owners_before": list(item.owners_before), "owners_at": list(item.owners_at),
                      "owners_after": list(item.owners_after), "crossing_pairs": [list(pair) for pair in item.crossing_pairs]}
                     for item in switches],
        "tie_enclosures": [[boundary(item.start), boundary(item.end), list(item.owners)] for item in envelope.tie_intervals],
        "piece_widths": widths, "bounded_widths": bounded, "bounded_count": len(bounded),
        "quadrature_count": len(widths) - len(bounded), "residual_bound": math.fsum(bounded),
    }


def diagnostic():
    frozen = load_14y()
    record = frozen.diagnostic()
    fixtures = frozen.fixtures()
    expected_order = [(label, candidate) for label, _, _, _ in fixtures for candidate in CANDIDATES]
    if [(item["fixture"], item["candidate"]) for item in record["records"]] != expected_order:
        raise ValueError("vector_order_changed")
    for item, (label, origin, receiver, defenders), candidate in zip(
            record["records"], (fixture for fixture in fixtures for _ in CANDIDATES),
            (candidate for _ in fixtures for candidate in CANDIDATES), strict=True):
        if item["fixture"] != label or item["candidate"] != candidate:
            raise ValueError("vector_alignment")
        item["routing"] = route(candidate, origin, receiver, defenders)
    record["schema_version"] = 2
    record["environment"] = environment()
    record["authority"]["boundary_contract"] = "certified-first-post-float"
    return record


def validate_record(record):
    if record.get("schema_version") != 2 or len(record.get("records", [])) != 108:
        raise ValueError("diagnostic_schema")
    if sum(len(item.get("comparison", [])) for item in record["records"]) != 366:
        raise ValueError("diagnostic_shape")


def preflight():
    if git("status", "--porcelain"):
        raise ValueError("clean_tree_required")
    if git("rev-parse", "v0.1.0^{}") != TAG:
        raise ValueError("release_tag_changed")
    for path in (PROTOCOL, HIST_LOCAL, HIST_CI, HIST_MANIFEST, *CODE):
        committed(path)
    print("Session 14aa preflight passed; synthetic evidence only")


def local_diagnostic():
    preflight()
    raw = diagnostic_bytes(diagnostic())
    write_once(LOCAL / "local_diagnostic.json", raw)
    record = json.loads(raw)
    counts = Counter(item["accepted"]["intervals"] for item in record["records"])
    if counts != {512: 55, 1024: 13, 2048: 30, 4096: 8, 8192: 2}:
        raise ValueError("accepted_resolution_authority")
    print(json.dumps({"vectors": 108, "components": 366, "bytes": len(raw),
                      "sha256": hashlib.sha256(raw).hexdigest(), "accepted_resolutions": dict(sorted(counts.items()))}, sort_keys=True))


def ci_diagnostic(output):
    preflight()
    target = Path(output)
    if target.is_absolute() or target.name != ARTIFACT_FILENAME:
        raise ValueError("ci_output_path")
    raw = diagnostic_bytes(diagnostic())
    destination = ROOT / target
    if destination.exists():
        raise FileExistsError("diagnostic_output_exists")
    destination.write_bytes(raw)
    print(f"SESSION14AA_DIAGNOSTIC schema=2 bytes={len(raw)} sha256={hashlib.sha256(raw).hexdigest()} artifact={ARTIFACT_NAME} file={ARTIFACT_FILENAME}")


def csv_bytes(rows, fields):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader(); writer.writerows(rows)
    return stream.getvalue().encode()


def compare(ci_file, declared_sha, run_id):
    preflight()
    local_raw = safe(LOCAL / "local_diagnostic.json").read_bytes()
    local = json.loads(local_raw); validate_record(local)
    ci, ci_raw = read_verified_ci(Path(ci_file), declared_sha); validate_record(ci)
    local_by = {(item["fixture"], item["candidate"]): item for item in local["records"]}
    ci_by = {(item["fixture"], item["candidate"]): item for item in ci["records"]}
    if tuple(local_by) != tuple(ci_by):
        raise ValueError("vector_order_changed")
    partition_rows, vector_rows = [], []
    structure_equal = True; resolutions_equal = True
    for key, left in local_by.items():
        right = ci_by[key]
        same_route = left["routing"] == right["routing"]
        structure_equal &= same_route
        resolutions_equal &= left["accepted"]["intervals"] == right["accepted"]["intervals"]
        partition_rows.append({"fixture": key[0], "candidate": key[1], "bitwise_equal": same_route,
                               "local_partition_count": len(left["routing"]["partitions"]),
                               "ci_partition_count": len(right["routing"]["partitions"])})
        for lrow, rrow in zip(left["comparison"], right["comparison"], strict=True):
            comparison = component_record(lrow["component"], lrow["actual"], rrow["actual"])
            vector_rows.append({"fixture": key[0], "candidate": key[1], **comparison})
    numeric_ok = all(row["absolute_difference"] <= 1e-6 for row in vector_rows)
    bitwise = all(row["bitwise_equal"] for row in vector_rows)
    if structure_equal and resolutions_equal and bitwise:
        classification, readiness = "A", 1
    elif structure_equal and resolutions_equal and numeric_ok:
        classification, readiness = "B", 2
    elif not structure_equal:
        classification, readiness = "D", 3
    elif not numeric_ok:
        classification, readiness = "E", 3
    else:
        classification, readiness = "G", 4
    authority = {
        "schema_version": 1, "session14z_local_sha256": digest(HIST_LOCAL),
        "session14z_ci_sha256": digest(HIST_CI), "session14z_manifest_sha256": digest(HIST_MANIFEST),
        "frozen_divergent_vectors": 7, "governed_ci_run_id": str(run_id),
        "artifact_name": ARTIFACT_NAME, "declared_ci_sha256": declared_sha,
        "downloaded_ci_sha256": hashlib.sha256(ci_raw).hexdigest(),
    }
    oracle_rows = []
    for item in local["records"]:
        for onset in item["routing"]["onsets"]:
            oracle_rows.append({"fixture": item["fixture"], "candidate": item["candidate"], "kind": "onset",
                                "raw": onset["raw"], "canonical": onset["canonical"], "canonical_bits": onset["canonical_bits"]})
        for switch in item["routing"]["switches"]:
            oracle_rows.append({"fixture": item["fixture"], "candidate": item["candidate"], "kind": "switch",
                                "raw": switch["raw"], "canonical": switch["canonical"], "canonical_bits": switch["canonical_bits"]})
    write_once(OUT / "divergent_root_authority.json", encoded(authority))
    write_once(OUT / "canonicalization_oracles.csv", csv_bytes(oracle_rows, ("fixture", "candidate", "kind", "raw", "canonical", "canonical_bits")))
    write_once(OUT / "local_diagnostic.json", local_raw); write_once(OUT / "ci_diagnostic.json", ci_raw)
    write_once(OUT / "partition_comparison.csv", csv_bytes(partition_rows, ("fixture", "candidate", "bitwise_equal", "local_partition_count", "ci_partition_count")))
    vector_fields = ("fixture", "candidate", "component", "expected", "actual", "expected_bits", "actual_bits", "expected_signed_zero", "actual_signed_zero", "absolute_difference", "relative_difference", "ulp_distance", "finite", "python_equal", "bitwise_equal")
    write_once(OUT / "vector_comparison.csv", csv_bytes(vector_rows, vector_fields))
    write_once(OUT / "environment_comparison.json", encoded({"local": local["environment"], "ci": ci["environment"], "same_numpy": local["environment"]["numpy"] == ci["environment"]["numpy"], "same_scipy": local["environment"]["scipy"] == ci["environment"]["scipy"]}))
    qc = {"schema_version": 1, "status": "closed", "classification": classification, "readiness": readiness,
          "canonical_partitions_bitwise_equal": structure_equal, "accepted_resolutions_equal": resolutions_equal,
          "final_vectors_bitwise_equal": bitwise, "numerically_within_existing_authority": numeric_ok,
          "differing_components": sum(not row["bitwise_equal"] for row in vector_rows),
          "maximum_absolute_difference": max(row["absolute_difference"] for row in vector_rows),
          "maximum_ulp_distance": max(row["ulp_distance"] for row in vector_rows if row["ulp_distance"] is not None),
          "vectors": 108, "components": 366, "permutations_regressed": 399,
          "empirical_access": False, "session14r_partial_outputs_accessed": False,
          "governed_ci_dispatches": 1, "artifact_retrievals": 1}
    write_once(OUT / "qc.json", encoded(qc))
    names = ("divergent_root_authority.json", "canonicalization_oracles.csv", "local_diagnostic.json", "ci_diagnostic.json", "partition_comparison.csv", "vector_comparison.csv", "environment_comparison.json", "qc.json")
    manifest = {"schema_version": 1, "status": "closed", "start": START, "release_tag_target": TAG,
                "protocol_sha256": digest(PROTOCOL), "implementation": {str(path): digest(path) for path in CODE},
                "outputs": {name: digest(OUT / name) for name in names}}
    write_once(OUT / "manifest.json", encoded(manifest))
    print(json.dumps(qc, sort_keys=True))


def publication_check():
    manifest = json.loads(safe(OUT / "manifest.json").read_text())
    for name, expected in manifest["outputs"].items():
        if digest(OUT / name) != expected:
            raise ValueError("output_hash_changed")
    for name in (*manifest["outputs"], "manifest.json"):
        text = safe(OUT / name).read_text()
        if any(token in text for token in ("/Users/", "/home/runner/", "event_id", "target_id", "X-Amz-Signature")):
            raise ValueError("publication_boundary")
    print("Session 14aa publication checks passed")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "local-diagnostic", "ci-diagnostic", "compare", "publication-check"))
    parser.add_argument("--output", default=ARTIFACT_FILENAME)
    parser.add_argument("--ci-file"); parser.add_argument("--declared-sha256"); parser.add_argument("--run-id")
    args = parser.parse_args()
    if args.command == "preflight": preflight()
    elif args.command == "local-diagnostic": local_diagnostic()
    elif args.command == "ci-diagnostic": ci_diagnostic(args.output)
    elif args.command == "compare":
        if not all((args.ci_file, args.declared_sha256, args.run_id)):
            raise ValueError("comparison_arguments_required")
        compare(args.ci_file, args.declared_sha256, args.run_id)
    else: publication_check()


if __name__ == "__main__":
    main()
