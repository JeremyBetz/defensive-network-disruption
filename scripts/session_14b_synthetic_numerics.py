#!/usr/bin/env python3
"""Serialization-repaired exact Session 14b synthetic numerical rerun."""
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
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import scipy
from defensive_network_disruption.geometry.integration_review import (
    FINE_INTERVALS, ORDINARY_INTERVALS, RELATIVE_ERROR_FLOOR,
    adaptive_reference, components, directional_breakpoints, historical_failure,
    polynomial_oracles, values_for_components)
from defensive_network_disruption.geometry.occlusion_fields import CANDIDATES, CarrierOriginField
from defensive_network_disruption.validation.json_scalars import json_native

START = "d7151243ec10ea2d455977c5432d0dcc74f33dea"
TAG_TARGET = "f00690c05d8c1c6db308a65bd311c43f9a8ef2fa"
PROTOCOL = Path("docs/protocols/phase_14b_serialization_repair_and_rerun.md")
OUT = Path("outputs/continuous_occlusion_numerics_14b")
SESSION14 = Path("scripts/session_14_occlusion_fields.py")
HISTORICAL_HASHES = {
    "scripts/session_14_occlusion_fields.py": "921842723974083431e6deee44c18ad6eda8c1de722e15e79e65612ee83b26ee",
    "src/defensive_network_disruption/geometry/occlusion_fields.py": "d7fd23bc131d0db2686ef27475a128fdca78aea88616c4494609962c165533aa",
    "tests/test_session14_fields.py": "a3a3e9530b45e8dec4391dc8cdf76ac07c8f2216118c0d4dcf367a7b661c49dd",
    "outputs/continuous_occlusion_hypotheses/manifest.json": "249c4fcb42c472290305356140066383097428432385951aea4803aa39d9e459",
    "outputs/continuous_occlusion_numerics/convergence.csv": "fab91419fca9731430baef5f372c6e7eb30e1291b1e06d636520e09b91fff49f",
    "outputs/continuous_occlusion_numerics/qc.json": "5c9a6bec7319a61d227f9d94f638eeae489f19348f83f4b98b7fb56c42db1166",
    "outputs/continuous_occlusion_numerics/manifest.json": "4581de83a6d5bec7c39418578b5ea80e2eed26d0739804f69cc93195666a2859",
}
IMPLEMENTATION = (
    "src/defensive_network_disruption/geometry/integration_review.py",
    "src/defensive_network_disruption/validation/json_scalars.py",
    "scripts/session_14b_synthetic_numerics.py",
    "tests/test_session14b_serialization.py",
)
PUBLIC = ("convergence.csv", "reference_summary.json", "failing_fixture_diagnostic.csv",
          "method_summary.json", "qc.json")
EXPECTED_FAILURE = {
    "coarse_intervals": 80, "fine_intervals": 160,
    "coarse_value": 0.5423405961267106, "fine_value": 0.5424947427905844,
    "absolute_difference": 0.00015414666387381093,
}


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT).decode().strip()


def safe(relative: Path | str) -> Path:
    relative = Path(relative)
    target = ROOT / relative
    if not target.resolve().is_relative_to(ROOT.resolve()) or any(item.is_symlink() for item in (target, *target.parents)):
        raise PermissionError("unsafe_path")
    return target


def digest(relative: Path | str) -> str:
    return hashlib.sha256(safe(relative).read_bytes()).hexdigest()


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
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def load_json(relative: Path | str):
    return json.loads(safe(relative).read_text(), parse_constant=lambda _:
                      (_ for _ in ()).throw(ValueError("nonfinite_json")))


def load_session14():
    spec = importlib.util.spec_from_file_location("closed_session14", safe(SESSION14))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture_rows():
    return tuple(load_session14().fixtures())


def ledger(stage: str, status: str) -> None:
    path = safe(OUT / "local" / "execution.jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", newline="\n") as handle:
        handle.write(json.dumps({"time": datetime.now(timezone.utc).isoformat(), "stage": stage,
                                 "status": status, "head": git("rev-parse", "HEAD"),
                                 "empirical_access": False}, sort_keys=True) + "\n")


def verify_history() -> None:
    git("merge-base", "--is-ancestor", START, "HEAD")
    if git("rev-parse", "v0.1.0^{}") != TAG_TARGET:
        raise ValueError("release_tag_changed")
    for path, expected in HISTORICAL_HASHES.items():
        if digest(path) != expected:
            raise ValueError("historical_authority_changed")


def committed(relative: Path | str) -> None:
    content = subprocess.check_output(["git", "show", "HEAD:" + str(relative)], cwd=ROOT)
    if hashlib.sha256(content).hexdigest() != digest(relative):
        raise ValueError("required_file_not_committed")


def implementation_hashes() -> dict[str, str]:
    return {path: digest(path) for path in IMPLEMENTATION}


def preflight() -> None:
    verify_history()
    committed(PROTOCOL)
    for path in IMPLEMENTATION:
        committed(path)
    if not git("check-ignore", "--", str(OUT / "local" / "probe")):
        raise ValueError("local_storage_not_ignored")
    source_paths = (Path(__file__).relative_to(ROOT), Path(IMPLEMENTATION[0]))
    imported = set()
    called = set()
    raw_source = ""
    for source_path in source_paths:
        source = safe(source_path).read_text()
        raw_source += source
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add(node.module or "")
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    called.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    called.add(node.func.attr)
    forbidden_import_roots = {"requests", "urllib"}
    forbidden_import_prefixes = ("defensive_network_disruption.models",
                                 "defensive_network_disruption.modeling")
    forbidden_calls = {"evaluate_options", "minimize", "urlopen", "open_provider_product"}
    forbidden_literals = ("population" + ".jsonl", "player_" + "targeted_id")
    if ({name.split(".")[0] for name in imported} & forbidden_import_roots or
            any(name.startswith(forbidden_import_prefixes) for name in imported) or
            called & forbidden_calls or any(token in raw_source for token in forbidden_literals)):
        raise ValueError("forbidden_route_present")
    print("Session 14b preflight passed; serialization-repaired synthetic rerun only")


def _component_values(field, origin, receiver, defenders, t_values):
    b = np.asarray(origin, dtype=np.float64)
    end = np.asarray(receiver, dtype=np.float64)
    queries = b[None, :] + np.asarray(t_values)[:, None] * (end - b)[None, :]
    return field.individual_values(origin, defenders, queries)


def failing_diagnostic() -> tuple[list[dict], dict]:
    origin = np.array((0.0, 0.0)); receiver = np.array((20.0, 0.0)); defender = np.array((5.0, 1.0))
    field = CarrierOriginField("expanding")
    radius = math.hypot(*defender); unit = defender / radius
    breakpoints = directional_breakpoints(origin, receiver, (defender,))
    grid = set(float(value) for value in np.linspace(0.0, 1.0, 257))
    for boundary in breakpoints:
        grid.add(boundary)
        for displacement in (1e-1, 1e-2, 1e-3, 1e-4):
            offset = displacement / 20.0
            if 0.0 <= boundary - offset <= 1.0: grid.add(boundary - offset)
            if 0.0 <= boundary + offset <= 1.0: grid.add(boundary + offset)
    rows = []
    for t in sorted(grid):
        query = origin + t * (receiver - origin)
        diff = query - defender
        ell = float(np.dot(diff, unit))
        h = abs(float(diff[0] * unit[1] - diff[1] * unit[0]))
        gate_t = min(1.0, max(0.0, ell))
        gate = gate_t * gate_t * (3.0 - 2.0 * gate_t)
        width = 2.0 + max(ell, 0.0) * math.tan(math.radians(10.0))
        value = float(field.individual_values(origin, (defender,), (query,))[0, 0])
        rows.append({"t": t, "field_value": value, "ell": ell, "h": h, "gate": gate, "width": width})
    peak = max(rows, key=lambda row: row["field_value"])
    probes = []
    for boundary_name, boundary in zip(("ell_zero", "ell_one"), breakpoints, strict=True):
        center = float(field.individual_values(origin, (defender,), ((origin + boundary * (receiver-origin)),))[0, 0])
        for displacement in (1e-1, 1e-2, 1e-3, 1e-4):
            dt = displacement / 20.0
            left = float(field.individual_values(origin, (defender,), ((origin + (boundary-dt)*(receiver-origin)),))[0, 0])
            right = float(field.individual_values(origin, (defender,), ((origin + (boundary+dt)*(receiver-origin)),))[0, 0])
            probes.append({"location": boundary_name, "displacement_metres": displacement,
                           "left_delta": left-center, "right_delta": right-center,
                           "left_right_difference": right-left})
    summary = {"breakpoints_t": list(breakpoints), "onset_width_t": breakpoints[1]-breakpoints[0],
               "sampled_peak_t": peak["t"], "sampled_peak_value": peak["field_value"],
               "boundary_probes": probes,
               "continuity_verdict": "continuous; smoothstep is C1 but changes higher derivatives at piece boundaries"}
    return rows, summary


def review() -> None:
    preflight()
    if any(safe(OUT / name).exists() for name in (*PUBLIC, "manifest.json")):
        raise FileExistsError("review_outputs_exist")
    marker = safe(OUT / "local" / "review.marker")
    marker.parent.mkdir(parents=True, exist_ok=True)
    with marker.open("x", newline="\n") as handle:
        handle.write(git("rev-parse", "HEAD") + "\n")
    ledger("review", "started")

    reproduced = historical_failure()
    if reproduced != EXPECTED_FAILURE:
        ledger("review", "authority_reproduction_failed")
        raise RuntimeError("historical_failure_not_reproduced")
    oracle_records = polynomial_oracles()
    if not all(record["passed"] for record in oracle_records):
        ledger("review", "simpson_oracle_failed")
        raise RuntimeError("simpson_oracle_failed")

    convergence_rows = []
    references = []
    edge_records = []
    started = time.perf_counter()
    for fixture, origin, receiver, defenders in fixture_rows():
        for candidate in CANDIDATES:
            field = CarrierOriginField(candidate)
            all_estimates = {count: values_for_components(field, origin, receiver, defenders, count)
                             for count in (*ORDINARY_INTERVALS, *FINE_INTERVALS, 80, 160)}
            reference_map = {}
            for component in components(len(defenders)):
                reference = adaptive_reference(field, origin, receiver, defenders, component, all_estimates)
                reference_map[component.name] = reference
                references.append({"fixture": fixture, "candidate": candidate, "component": component.name,
                                   "reference": reference.value, "adaptive_error_estimate": reference.estimated_error,
                                   "repeat_reference": reference.repeat_value,
                                   "fine_32768": reference.fine_32768, "fine_65536": reference.fine_65536,
                                   "available": reference.available, "unavailable_reason": reference.reason})
                previous = None
                for count in ORDINARY_INTERVALS:
                    estimate = all_estimates[count][component.name]
                    absolute_error = abs(estimate-reference.value) if reference.available else None
                    relative_error = (absolute_error/abs(reference.value)
                                      if absolute_error is not None and abs(reference.value)>RELATIVE_ERROR_FLOOR else None)
                    convergence_rows.append({"fixture": fixture, "candidate": candidate,
                                             "component": component.name, "intervals": count,
                                             "estimate": estimate,
                                             "previous_difference": None if previous is None else abs(estimate-previous),
                                             "absolute_reference_error": absolute_error,
                                             "relative_reference_error": relative_error,
                                             "reference_available": reference.available})
                    previous = estimate
            errors_160 = [abs(all_estimates[160][name]-ref.value) for name,ref in reference_map.items() if ref.available]
            gate_delta = max(abs(all_estimates[160][name]-all_estimates[80][name]) for name in reference_map)
            controlled = None
            for count in (512,1024,2048,4096,8192,16384):
                prior = count//2
                if max(abs(all_estimates[count][name]-all_estimates[prior][name]) for name in reference_map) <= 1e-7:
                    controlled = count
                    break
            edge_records.append({"fixture":fixture,"candidate":candidate,
                                 "maximum_80_160_difference":gate_delta,
                                 "maximum_160_reference_error":max(errors_160) if errors_160 else None,
                                 "controlled_intervals":controlled,
                                 "controlled_maximum_reference_error":None if controlled is None else max(
                                     abs(all_estimates[controlled][name]-ref.value)
                                     for name,ref in reference_map.items() if ref.available)})
    elapsed = time.perf_counter()-started
    diagnostic_rows, localization = failing_diagnostic()

    unavailable = [row for row in references if not row["available"]]
    max_160_error = max(row["maximum_160_reference_error"] for row in edge_records
                        if row["maximum_160_reference_error"] is not None)
    controlled_complete = all(row["controlled_intervals"] is not None for row in edge_records)
    controlled_max_error = max((row["controlled_maximum_reference_error"] or 0.0) for row in edge_records)
    if unavailable:
        classification, readiness = "F — UNRESOLVED", "4 — NOT READY / ABANDON CANDIDATE"
    elif max_160_error > 1e-6:
        classification = "B — FIELD IS SOUND BUT REQUIRES HIGHER/CONTROLLED RESOLUTION"
        readiness = ("1 — READY FOR A SEPARATELY GOVERNED SESSION 14 RETRY WITH A NEW FROZEN NUMERICAL CONTRACT"
                     if controlled_complete and controlled_max_error <= 1e-6 else
                     "2 — READY AFTER SMALL IMPLEMENTATION REPAIR")
    else:
        classification = "A — CURRENT FIELD IS NUMERICALLY SOUND; ORIGINAL GATE WAS INAPPROPRIATE"
        readiness = "1 — READY FOR A SEPARATELY GOVERNED SESSION 14 RETRY WITH A NEW FROZEN NUMERICAL CONTRACT"

    per_resolution = []
    for count in ORDINARY_INTERVALS:
        rows = [row for row in convergence_rows if row["intervals"]==count and row["reference_available"]]
        per_resolution.append({"intervals":count,"maximum_absolute_reference_error":max(row["absolute_reference_error"] for row in rows),
                               "evaluations_per_component":count+1})
    recommendation = None
    if controlled_complete and controlled_max_error <= 1e-6:
        recommendation = {"method":"convergence-controlled composite Simpson",
                          "start_intervals":256,"refinement":"double intervals",
                          "acceptance":"maximum absolute successive-estimate difference <= 1e-7 across all individual, union and maximum components",
                          "maximum_intervals":16384,"accepted_value":"finer estimate",
                          "failure":"block the edge and the governed execution",
                          "demonstrated_maximum_synthetic_reference_error":controlled_max_error}

    method_summary = {
        "schema_version":1,"status":"closed","historical_failure":reproduced,
        "simpson_oracles":{"count":len(oracle_records),"passed":sum(bool(r["passed"]) for r in oracle_records),
                           "maximum_absolute_error":max(r["absolute_error"] for r in oracle_records)},
        "reference_method":{"library":"SciPy","version":scipy.__version__,"method":"integrate.quad",
                            "strict_tolerances":1e-13,"repeat_tolerances":1e-11,"limit":1000,
                            "analytical_directional_breakpoints":True},
        "ordinary_resolution_summary":per_resolution,"edge_candidate_count":len(edge_records),
        "reference_component_count":len(references),"unavailable_reference_count":len(unavailable),
        "maximum_160_interval_reference_error":max_160_error,
        "historical_gate_verdict":"poorly specified: successive-estimate disagreement is not actual reference error, although it correctly blocked an inaccurate 160-interval estimate",
        "field_smoothness":localization["continuity_verdict"],"classification":classification,
        "retry_readiness":readiness,"recommended_future_contract":recommendation,
        "approximate_review_runtime_seconds":elapsed,
        "planning_probe_prior_exposure":True,
        "next_direction":"separately govern a Session 14 retry under the recommended integration contract" if recommendation else
                         "resolve the numerical reference failure before any Session 14 retry"}
    reference_summary = {"schema_version":1,"records":references,"edge_candidate_diagnostics":edge_records,
                         "failing_fixture_localization":localization,"polynomial_oracles":oracle_records}
    qc = {"schema_version":1,"status":"closed","synthetic_only":True,"empirical_states_read":0,
          "models_loaded":0,"targets_read":0,"historical_session14_modified":False,
          "fixture_count":len(fixture_rows()),"candidate_count":len(CANDIDATES),
          "convergence_row_count":len(convergence_rows),"reference_record_count":len(references),
          "historical_failure_reproduced":True,"oracle_failures":0,"reference_failures":len(unavailable),
          "classification":classification,"retry_readiness":readiness}

    atomic_csv(OUT/"convergence.csv", list(convergence_rows[0]), convergence_rows)
    atomic_json(OUT/"reference_summary.json", reference_summary)
    atomic_csv(OUT/"failing_fixture_diagnostic.csv", list(diagnostic_rows[0]), diagnostic_rows)
    atomic_json(OUT/"method_summary.json", method_summary)
    atomic_json(OUT/"qc.json", qc)
    output_hashes = {name:digest(OUT/name) for name in PUBLIC}
    manifest = {"schema_version":1,"status":"closed","starting_authority":START,
                "protocol_sha256":digest(PROTOCOL),"implementation_sha256":implementation_hashes(),
                "historical_authority_sha256":HISTORICAL_HASHES,"environment":{"python":platform.python_version(),
                "numpy":np.__version__,"scipy":scipy.__version__,"uv_lock_sha256":digest("uv.lock")},
                "outputs_sha256":output_hashes,"empirical_access":False}
    atomic_json(OUT/"manifest.json",manifest)
    ledger("review", "closed")
    print(classification)
    print(readiness)


def publication_check() -> None:
    verify_history(); committed(PROTOCOL)
    manifest = load_json(OUT/"manifest.json")
    if manifest["protocol_sha256"] != digest(PROTOCOL) or manifest["implementation_sha256"] != implementation_hashes():
        raise ValueError("authority_mismatch")
    for name, expected in manifest["outputs_sha256"].items():
        if digest(OUT/name) != expected:
            raise ValueError("closed_output_mismatch")
    qc = load_json(OUT/"qc.json")
    if any(qc[key] for key in ("empirical_states_read","models_loaded","targets_read","oracle_failures")):
        raise ValueError("qc_failure")
    references = load_json(OUT/"reference_summary.json")["records"]
    unavailable = sum(not row["available"] for row in references)
    if unavailable != qc["reference_failures"]:
        raise ValueError("reference_availability_count_mismatch")
    if unavailable and not qc["classification"].startswith("F —"):
        raise ValueError("unavailable_reference_classification_mismatch")
    forbidden = ("player_id", "event_id", "timestamp", "provider_id", "signed_url", "/Users/")
    for name in (*PUBLIC,"manifest.json"):
        text = safe(OUT/name).read_text()
        if any(token in text for token in forbidden):
            raise ValueError("publication_forbidden_content")
    print("Session 14b publication check passed")


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight","review","publication-check"))
    command=parser.parse_args().command
    {"preflight":preflight,"review":review,"publication-check":publication_check}[command]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
