#!/usr/bin/env python3
"""Synthetic-only Session 14c maximum-envelope switching review."""
from __future__ import annotations

import argparse
import ast
import csv
from datetime import datetime, timezone
import hashlib
import importlib.util
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
from defensive_network_disruption.geometry.integration_review import (
    directional_breakpoints, values_for_components,
)
from defensive_network_disruption.geometry.maximum_envelope import (
    DIRECT_FINE_AGREEMENT, PIECEWISE_REPEAT_AGREEMENT, SPLIT_SIMPSON_AGREEMENT,
    UNSPLIT_AGREEMENT, EnvelopeError, find_envelope_switches,
    integrate_maximum_piecewise, split_simpson_maximum, switch_slopes,
)
from defensive_network_disruption.geometry.occlusion_fields import CANDIDATES, CarrierOriginField
from defensive_network_disruption.validation.json_scalars import json_native


START = "0918fc7425078269e6d39117af95965971b31561"
TAG_TARGET = "f00690c05d8c1c6db308a65bd311c43f9a8ef2fa"
PROTOCOL = Path("docs/protocols/phase_14c_maximum_envelope_switching_review.md")
OUT = Path("outputs/continuous_occlusion_max_switching")
SESSION14 = Path("scripts/session_14_occlusion_fields.py")
REFERENCE = Path("outputs/continuous_occlusion_numerics_14b/reference_summary.json")
PUBLIC = ("switch_summary.csv", "unresolved_case_comparison.csv",
          "control_case_comparison.csv", "convergence_by_switch_count.csv",
          "method_summary.json", "qc.json")
IMPLEMENTATION = (
    "src/defensive_network_disruption/geometry/maximum_envelope.py",
    "scripts/session_14c_maximum_switching.py",
    "tests/test_session14c_switching.py",
)
HISTORICAL_HASHES = {
    "scripts/session_14_occlusion_fields.py": "921842723974083431e6deee44c18ad6eda8c1de722e15e79e65612ee83b26ee",
    "src/defensive_network_disruption/geometry/occlusion_fields.py": "d7fd23bc131d0db2686ef27475a128fdca78aea88616c4494609962c165533aa",
    "src/defensive_network_disruption/geometry/integration_review.py": "152f688fe6b217dec0c6ede667e611d9d411c43762c0de1ff8d1143919b50f0d",
    "outputs/continuous_occlusion_hypotheses/manifest.json": "249c4fcb42c472290305356140066383097428432385951aea4803aa39d9e459",
    "outputs/continuous_occlusion_numerics/manifest.json": "4581de83a6d5bec7c39418578b5ea80e2eed26d0739804f69cc93195666a2859",
    "outputs/continuous_occlusion_numerics_14b/manifest.json": "8858b4bfd2717dae1d250e1647742cc467813170cd2bba9c5b47d407de0990a3",
    "outputs/continuous_occlusion_numerics_14b/reference_summary.json": "734af21c5ea22bd8e3b472b1a21bfd1de8e27dfb2ecbb4d915103362e5c976ac",
}
EXPECTED_CASES = 108
EXPECTED_UNRESOLVED = {
    ("equal_minimum_three", "expanding"),
    ("equal_minimum_three", "constant_width"),
    ("star_edge_1", "expanding"),
    ("star_edge_3", "expanding"),
}


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT).decode().strip()


def safe(relative: Path | str) -> Path:
    relative = Path(relative)
    path = ROOT / relative
    if not path.resolve().is_relative_to(ROOT.resolve()) or any(
            item.is_symlink() for item in (path, *path.parents)):
        raise PermissionError("unsafe_path")
    return path


def digest(relative: Path | str) -> str:
    return hashlib.sha256(safe(relative).read_bytes()).hexdigest()


def load_json(relative: Path | str):
    return json.loads(safe(relative).read_text(), parse_constant=lambda _:
                      (_ for _ in ()).throw(ValueError("nonfinite_json")))


def encoded(value) -> str:
    return json.dumps(json_native(value), sort_keys=True, indent=2, allow_nan=False) + "\n"


def atomic_json(relative: Path | str, value) -> None:
    path = safe(relative)
    if path.exists():
        raise FileExistsError("artifact_exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name("." + path.name + ".tmp")
    with temporary.open("x", newline="\n") as handle:
        handle.write(encoded(value))
    temporary.replace(path)


def atomic_csv(relative: Path | str, fieldnames: list[str], rows: list[dict]) -> None:
    path = safe(relative)
    if path.exists():
        raise FileExistsError("artifact_exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name("." + path.name + ".tmp")
    with temporary.open("x", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    temporary.replace(path)


def committed(relative: Path | str) -> None:
    content = subprocess.check_output(["git", "show", "HEAD:" + str(relative)], cwd=ROOT)
    if hashlib.sha256(content).hexdigest() != digest(relative):
        raise ValueError("required_file_not_committed")


def verify_history() -> None:
    git("merge-base", "--is-ancestor", START, "HEAD")
    if git("rev-parse", "v0.1.0^{}") != TAG_TARGET:
        raise ValueError("release_tag_changed")
    for path, expected in HISTORICAL_HASHES.items():
        if digest(path) != expected:
            raise ValueError("historical_authority_changed")


def implementation_hashes() -> dict[str, str]:
    return {path: digest(path) for path in IMPLEMENTATION}


def environment() -> dict:
    return {"python": platform.python_version(), "numpy": np.__version__,
            "scipy": scipy.__version__, "uv_lock_sha256": digest("uv.lock")}


def load_session14():
    spec = importlib.util.spec_from_file_location("closed_session14_for_14c", safe(SESSION14))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def fixture_rows():
    return tuple(load_session14().fixtures())


def maximum_records() -> dict[tuple[str, str], dict]:
    records = {(row["fixture"], row["candidate"]): row for row in load_json(REFERENCE)["records"]
               if row["component"] == "maximum"}
    if len(records) != EXPECTED_CASES:
        raise ValueError("maximum_case_count_changed")
    unavailable = {key for key, row in records.items() if not row["available"]}
    if unavailable != EXPECTED_UNRESOLVED:
        raise ValueError("historical_unresolved_set_changed")
    return records


def values_function(candidate: str, origin, receiver, defenders):
    field = CarrierOriginField(candidate)
    b = np.asarray(origin, dtype=np.float64)
    end = np.asarray(receiver, dtype=np.float64)
    ds = np.asarray(defenders, dtype=np.float64)

    def evaluate(t_values):
        t = np.asarray(t_values, dtype=np.float64)
        queries = b[None, :] + t[:, None] * (end-b)[None, :]
        return field.individual_values(b, ds, queries)
    return evaluate


def mapped_signature(result, defender_count: int, reverse: bool = False) -> tuple:
    count = defender_count
    convert = (lambda value: count - 1 - value) if reverse else (lambda value: value)
    return tuple((item.location,
                  tuple(sorted(convert(value) for value in item.owners_before)),
                  tuple(sorted(convert(value) for value in item.owners_at)),
                  tuple(sorted(convert(value) for value in item.owners_after)),
                  item.endpoint, item.multiway)
                 for item in result.switches)


def ledger(stage: str, status: str) -> None:
    path = safe(OUT / "local" / "execution.jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", newline="\n") as handle:
        handle.write(json.dumps({"time": datetime.now(timezone.utc).isoformat(),
                                 "stage": stage, "status": status,
                                 "head": git("rev-parse", "HEAD"),
                                 "synthetic_only": True}, sort_keys=True) + "\n")


def route_guard() -> None:
    imports = set(); calls = set(); source = ""
    for relative in IMPLEMENTATION[:2]:
        text = safe(relative).read_text(); source += text
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import): imports.update(item.name for item in node.names)
            elif isinstance(node, ast.ImportFrom): imports.add(node.module or "")
            elif isinstance(node, ast.Call):
                calls.add(node.func.id if isinstance(node.func, ast.Name) else
                          node.func.attr if isinstance(node.func, ast.Attribute) else "")
    if ({name.split(".")[0] for name in imports} & {"requests", "urllib"} or
            any(name.startswith("defensive_network_disruption.models") for name in imports) or
            calls & {"evaluate_options", "minimize", "urlopen"} or
            any(token in source for token in ("population" + ".jsonl", "player_" + "targeted_id"))):
        raise ValueError("forbidden_route_present")


def preflight() -> None:
    verify_history(); committed(PROTOCOL)
    for path in IMPLEMENTATION: committed(path)
    if not git("check-ignore", "--", str(OUT / "local" / "probe")):
        raise ValueError("local_storage_not_ignored")
    route_guard(); maximum_records()
    if len(fixture_rows()) != 36 or tuple(CANDIDATES) != ("isotropic", "expanding", "constant_width"):
        raise ValueError("fixture_authority_changed")
    print("Session 14c preflight passed; synthetic maximum envelopes only")


def _grid_distance(location: float, intervals: int) -> float:
    return abs(location*intervals - round(location*intervals)) / intervals


def _minimum_switch_spacing(locations: list[float]) -> float | None:
    points = sorted({0.0, 1.0, *locations})
    return min((right-left for left, right in zip(points[:-1], points[1:], strict=True)),
               default=None)


def _controlled_contract(candidate: str, origin, receiver, defenders,
                         reference: float) -> tuple[int | None, float | None]:
    previous = None
    for intervals in (256, 512, 1024, 2048, 4096, 8192, 16384):
        value = values_for_components(CarrierOriginField(candidate), origin, receiver,
                                      defenders, intervals)["maximum"]
        if previous is not None and abs(value-previous) <= 1e-7:
            return intervals, abs(value-reference)
        previous = value
    return None, None


def review() -> None:
    preflight()
    if any(safe(OUT / name).exists() for name in (*PUBLIC, "manifest.json")):
        raise FileExistsError("review_outputs_exist")
    marker = safe(OUT / "local" / "review.marker"); marker.parent.mkdir(parents=True, exist_ok=True)
    with marker.open("x", newline="\n") as handle: handle.write(git("rev-parse", "HEAD") + "\n")
    ledger("review", "started")
    historical = maximum_records()
    case_rows = []; switch_rows = []
    deterministic = True; permutation_stable = True
    for fixture, origin, receiver, defenders in fixture_rows():
        for candidate in CANDIDATES:
            key = (fixture, candidate); old = historical[key]
            extra = (() if candidate == "isotropic" else
                     directional_breakpoints(origin, receiver, defenders))
            function = values_function(candidate, origin, receiver, defenders)
            detected = find_envelope_switches(function, extra_partitions=extra)
            repeated = find_envelope_switches(function, extra_partitions=extra)
            if detected != repeated: deterministic = False
            reversed_defenders = tuple(reversed(defenders))
            reversed_result = find_envelope_switches(
                values_function(candidate, origin, receiver, reversed_defenders),
                extra_partitions=extra)
            if mapped_signature(detected, len(defenders)) != mapped_signature(
                    reversed_result, len(defenders), reverse=True):
                permutation_stable = False
            piecewise = integrate_maximum_piecewise(function, detected, extra_partitions=extra)
            partitions = piecewise.partitions
            split32, intervals32, evaluations32 = split_simpson_maximum(function, partitions, 32768)
            split65, intervals65, evaluations65 = split_simpson_maximum(function, partitions, 65536)
            direct65 = float(old["fine_65536"])
            piece_repeat_delta = abs(piecewise.value-piecewise.repeat_value)
            unsplit_delta = abs(piecewise.value-float(old["reference"]))
            direct_delta = abs(piecewise.value-direct65)
            split_delta = abs(split65-split32)
            slopes = switch_slopes(function, detected, partitions)
            continuous = all(item["continuous"] for item in slopes)
            available = (piece_repeat_delta <= PIECEWISE_REPEAT_AGREEMENT and
                         unsplit_delta <= UNSPLIT_AGREEMENT and
                         direct_delta <= DIRECT_FINE_AGREEMENT and not piecewise.warnings and continuous and
                         (key not in EXPECTED_UNRESOLVED or split_delta <= SPLIT_SIMPSON_AGREEMENT))
            locations = [item.location for item in detected.switches]
            controlled_intervals, controlled_error = _controlled_contract(
                candidate, origin, receiver, defenders, piecewise.value)
            case = {
                "fixture": fixture, "candidate": candidate,
                "historical_status": "unresolved" if key in EXPECTED_UNRESOLVED else "control",
                "switch_count": len(detected.switches),
                "interior_switch_count": sum(not item.endpoint for item in detected.switches),
                "endpoint_switch_count": sum(item.endpoint for item in detected.switches),
                "maximizing_defender_count": len(detected.maximizing_defenders),
                "tie_interval_count": len(detected.tie_intervals),
                "multiway_switch_count": sum(item.multiway for item in detected.switches),
                "minimum_switch_spacing": _minimum_switch_spacing(locations),
                "piecewise_reference": piecewise.value,
                "piecewise_repeat": piecewise.repeat_value,
                "piecewise_repeat_difference": piece_repeat_delta,
                "unsplit_adaptive": old["reference"], "unsplit_difference": unsplit_delta,
                "direct_simpson_65536": direct65, "direct_difference": direct_delta,
                "historical_direct_32768_65536_difference": abs(float(old["fine_65536"])-float(old["fine_32768"])),
                "split_simpson_32768": split32, "split_simpson_65536": split65,
                "split_simpson_difference": split_delta,
                "split_32768_intervals": intervals32, "split_32768_evaluations": evaluations32,
                "split_65536_intervals": intervals65, "split_65536_evaluations": evaluations65,
                "controlled_intervals": controlled_intervals,
                "controlled_reference_error": controlled_error,
                "available": available,
            }
            case_rows.append(case)
            slope_by_location = {item["location"]: item for item in slopes}
            for ordinal, item in enumerate(detected.switches, 1):
                slope = slope_by_location.get(item.location)
                switch_rows.append({
                    "fixture": fixture, "candidate": candidate, "switch_ordinal": ordinal,
                    "location": item.location, "endpoint": item.endpoint,
                    "owners_before": len(item.owners_before), "owners_at": len(item.owners_at),
                    "owners_after": len(item.owners_after), "multiway": item.multiway,
                    "envelope_value": item.envelope_value,
                    "minimum_grid_distance_32768": _grid_distance(item.location, 32768),
                    "minimum_grid_distance_65536": _grid_distance(item.location, 65536),
                    "slope_probe_step": None if slope is None else slope["step"],
                    "left_slope": None if slope is None else slope["left_slope"],
                    "right_slope": None if slope is None else slope["right_slope"],
                    "slope_change": None if slope is None else slope["slope_change"],
                    "continuous": None if slope is None else slope["continuous"],
                })

    unresolved = [row for row in case_rows if row["historical_status"] == "unresolved"]
    controls = [row for row in case_rows if row["historical_status"] == "control"]
    all_available = all(row["available"] for row in case_rows)
    all_unresolved_switch = all(row["interior_switch_count"] > 0 for row in unresolved)
    all_unresolved_split = all(row["split_simpson_difference"] <= SPLIT_SIMPSON_AGREEMENT for row in unresolved)
    all_continuous = all(row["continuous"] is not False for row in switch_rows)
    if all_available and all_unresolved_switch and all_unresolved_split and deterministic and permutation_stable:
        classification = "A — SWITCHING POINTS EXPLAIN THE MAXIMUM-ENVELOPE REFERENCE FAILURES"
    elif any(row["available"] and row["interior_switch_count"] > 0 for row in unresolved):
        classification = "B — SWITCHING POINTS CONTRIBUTE BUT DO NOT FULLY EXPLAIN FAILURES"
    elif all_available:
        classification = "C — MAXIMUM ENVELOPE IS NUMERICALLY VALID BUT DISPROPORTIONATELY COMPLEX"
    elif not all_continuous or not deterministic or not permutation_stable:
        classification = "D — MAXIMUM-ENVELOPE REPRESENTATION / IMPLEMENTATION HAS A DEEPER NUMERICAL PROBLEM"
    else:
        classification = "F — UNRESOLVED"
    maximum_decision = ("1 — RETAIN MAXIMUM WITH THE PIECEWISE CONTRACT" if all_available and deterministic and
                        permutation_stable else "3 — RETIRE MAXIMUM FROM FUTURE EMPIRICAL WORK")
    controlled_all = all(row["controlled_intervals"] is not None and
                         row["controlled_reference_error"] is not None and
                         row["controlled_reference_error"] <= 1e-6 for row in case_rows)
    if classification.startswith("A") and maximum_decision.startswith("1") and controlled_all:
        readiness = "1 — READY FOR A SEPARATELY FROZEN SESSION 14 RETRY"
    elif maximum_decision.startswith("3") and all_continuous:
        readiness = "2 — READY ONLY WITH MAXIMUM RETIRED"
    elif not all_continuous:
        readiness = "4 — DEEPER CONTINUOUS-FIELD DEFECT"
    else:
        readiness = "3 — PARTIAL OR COMPLEX NUMERICAL EVIDENCE"

    grouped = []
    for status in ("unresolved", "control"):
        subset = [row for row in case_rows if row["historical_status"] == status]
        for candidate in CANDIDATES:
            candidate_rows = [row for row in subset if row["candidate"] == candidate]
            for switch_count in sorted({row["switch_count"] for row in candidate_rows}):
                rows = [row for row in candidate_rows if row["switch_count"] == switch_count]
                grouped.append({"historical_status": status, "candidate": candidate,
                                "switch_count": switch_count, "case_count": len(rows),
                                "available_count": sum(row["available"] for row in rows),
                                "maximum_piecewise_direct_difference": max(row["direct_difference"] for row in rows),
                                "maximum_split_difference": max(row["split_simpson_difference"] for row in rows),
                                "maximum_historical_direct_change": max(
                                    row["historical_direct_32768_65536_difference"] for row in rows)})

    fields = list(case_rows[0])
    atomic_csv(OUT / "switch_summary.csv", list(switch_rows[0]) if switch_rows else
               ["fixture", "candidate", "switch_ordinal"], switch_rows)
    atomic_csv(OUT / "unresolved_case_comparison.csv", fields, unresolved)
    atomic_csv(OUT / "control_case_comparison.csv", fields, controls)
    atomic_csv(OUT / "convergence_by_switch_count.csv", list(grouped[0]), grouped)
    method = {
        "schema_version": 1, "status": "closed", "synthetic_only": True,
        "case_count": len(case_rows), "unresolved_case_count": len(unresolved),
        "control_case_count": len(controls), "switch_count": len(switch_rows),
        "deterministic": deterministic, "permutation_stable": permutation_stable,
        "all_piecewise_cases_available": all_available,
        "all_unresolved_cases_have_true_interior_switches": all_unresolved_switch,
        "all_unresolved_split_simpson_pass": all_unresolved_split,
        "all_switches_continuous": all_continuous,
        "controlled_simpson_verified_for_all_108_maximum_cases": controlled_all,
        "classification": classification, "maximum_decision": maximum_decision,
        "session_14_retry_readiness": readiness,
        "future_integration_contract": ({"maximum_reference": "partition at onsets and verified envelope switches; scalar quad on each piece",
                                         "strict_tolerance": 1e-13, "repeat_tolerance": 1e-11,
                                         "piecewise_repeat_agreement": PIECEWISE_REPEAT_AGREEMENT,
                                         "unsplit_agreement": UNSPLIT_AGREEMENT,
                                         "direct_65536_agreement": DIRECT_FINE_AGREEMENT,
                                         "failure": "block without tolerance widening"}
                                        if maximum_decision.startswith("1") else None),
        "recommended_next_action": ("freeze one separate Session 14 retry using the verified numerical contract"
                                    if readiness.startswith("1") else
                                    "freeze a Session 14 retry that retires maximum and retains individual/union fields"
                                    if readiness.startswith("2") else
                                    "conduct a bounded follow-up numerical integrity review"),
    }
    atomic_json(OUT / "method_summary.json", method)
    qc = {"schema_version": 1, "status": "closed", "synthetic_only": True,
          "empirical_states_read": 0, "models_loaded": 0, "targets_read": 0,
          "case_count": len(case_rows), "switch_row_count": len(switch_rows),
          "unresolved_count": len(unresolved), "control_count": len(controls),
          "available_count": sum(row["available"] for row in case_rows),
          "classification": classification, "maximum_decision": maximum_decision,
          "retry_readiness": readiness, "deterministic": deterministic,
          "permutation_stable": permutation_stable}
    atomic_json(OUT / "qc.json", qc)
    outputs = {name: digest(OUT / name) for name in PUBLIC}
    atomic_json(OUT / "manifest.json", {
        "schema_version": 1, "status": "closed", "start": START,
        "protocol_sha256": digest(PROTOCOL), "implementation_sha256": implementation_hashes(),
        "historical_authority_sha256": HISTORICAL_HASHES, "environment": environment(),
        "outputs_sha256": outputs, "synthetic_only": True,
    })
    ledger("review", "closed")
    print(classification); print(maximum_decision); print(readiness)


def publication_check() -> None:
    verify_history(); committed(PROTOCOL)
    for path in IMPLEMENTATION: committed(path)
    manifest = load_json(OUT / "manifest.json"); qc = load_json(OUT / "qc.json")
    expected_manifest = {"schema_version", "status", "start", "protocol_sha256",
                         "implementation_sha256", "historical_authority_sha256",
                         "environment", "outputs_sha256", "synthetic_only"}
    if set(manifest) != expected_manifest or manifest["status"] != "closed" or not manifest["synthetic_only"]:
        raise ValueError("manifest_schema")
    if manifest["implementation_sha256"] != implementation_hashes() or manifest["environment"] != environment():
        raise ValueError("implementation_authority_mismatch")
    if manifest["protocol_sha256"] != digest(PROTOCOL) or manifest["historical_authority_sha256"] != HISTORICAL_HASHES:
        raise ValueError("historical_authority_mismatch")
    if set(manifest["outputs_sha256"]) != set(PUBLIC): raise ValueError("output_allowlist")
    for name, expected in manifest["outputs_sha256"].items():
        if digest(OUT / name) != expected: raise ValueError("output_hash_mismatch")
    if qc["case_count"] != EXPECTED_CASES or qc["unresolved_count"] != 4 or qc["control_count"] != 104:
        raise ValueError("qc_counts")
    for name in (*PUBLIC, "manifest.json"):
        text = safe(OUT / name).read_text()
        if any(token in text for token in ("/Users/", "player_id", "event_id", "token=", "https://")):
            raise ValueError("publication_content")
    print("Session 14c publication checks passed; existing hashes were not rebound")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "review", "publication-check"))
    arguments = parser.parse_args()
    result = {"preflight": preflight, "review": review,
              "publication-check": publication_check}[arguments.command]()
    return 0 if result is None else int(result)


if __name__ == "__main__":
    sys.exit(main())
