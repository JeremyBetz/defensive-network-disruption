#!/usr/bin/env python3
"""One-shot Session 14ak comparator and publication-replay diagnosis."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import platform
import resource
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np

from defensive_network_disruption.geometry.comparator_diagnosis import (
    DiagnosticTimeout, audit_partitions, sanitize_curve, split_simpson_curve,
    timed, uniform_simpson_curve,
)
from defensive_network_disruption.geometry.integration_review import values_for_components
from defensive_network_disruption.geometry.micro_interval_verifier import (
    bounded_adaptive_maximum, point_interval_distance,
)
from defensive_network_disruption.geometry.occlusion_fields import CarrierOriginField
from defensive_network_disruption.geometry.production_verification import adaptive_maximum, require
from defensive_network_disruption.geometry.representation_retry import canonical_geometry
from defensive_network_disruption.geometry.verification_audit import controlled_vector, scalar_oracle
from defensive_network_disruption.validation.empirical_switch_diagnosis import (
    project_canonical_edge, project_prepared_edge, selective_bytes,
)
from defensive_network_disruption.validation.numerical_failure_publication import replay
from defensive_network_disruption.validation.r5_persistence import durable_write, read_journal

START = "0ace3b79d18cdfa9b2f3dd26a7bf1d201cdbfa1f"
TAG = "f00690c05d8c1c6db308a65bd311c43f9a8ef2fa"
PROTOCOL = Path("docs/protocols/phase_14ak_constant_width_comparator_diagnosis.md")
OUT = Path("outputs/session14_constant_width_comparator_diagnosis")
LOCAL = OUT / "local"
PREPARED = Path("outputs/continuous_occlusion_retry_14r8/local/prepared.jsonl")
CANONICAL = Path("outputs/receiver_ranking_m0_m1/local/population.jsonl")
R8_JOURNAL = Path("outputs/continuous_occlusion_retry_14r8/local/journal.jsonl")
R8_ORIGINAL = Path("outputs/continuous_occlusion_retry_14r8/local/original_failure.json")
R8_EMERGENCY = Path("outputs/continuous_occlusion_retry_14r8/local/emergency_failure.json")
PREPARED_SHA = "15a809060f0ba4a8cb3790011dab8008db3dad6e931c287ccb395f61ef1530b0"
CANONICAL_SHA = "cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d"
ORIGINAL_SHA = "ef1e465ab78318f42e1fb10a3e173a4e342649c3f3ea529144934d117b47550a"
EMERGENCY_SHA = "39d8061948ff04975812380eddcb1fca796f19d07fbfb20b5a0eaa57927be3d0"
JOURNAL_SHA = "10b5aa8769458c8695f74028e4cb278aad9edf5740e35c978695758cef54446e"
STATE = 4
RECEIVER = 7
CANDIDATE = "constant_width"
LADDER = (256, 512, 1024, 2048, 4096, 8192, 16384)
OPERATION_LIMIT = 600.0
TOTAL_LIMIT = 3600.0
PUBLIC = (
    "failure_authority.json", "topology_summary.json", "piecewise_convergence.csv",
    "unsplit_convergence.csv", "production_numerical_health.json", "onset_neighborhood.csv",
    "piece_contributions.csv", "runtime_breakdown.json", "agreement_gate_diagnosis.json",
    "synthetic_reproduction.json", "publication_replay_diagnosis.json",
    "publication_scalability_options.json", "qc.json",
)


def safe(path: Path | str) -> Path:
    value = Path(path)
    if not value.is_absolute():
        value = ROOT / value
    if not value.resolve().is_relative_to(ROOT.resolve()) or any(p.is_symlink() for p in (value, *value.parents)):
        raise PermissionError("unsafe_path")
    return value


def sha(path: Path | str) -> str:
    digest = hashlib.sha256()
    with safe(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=ROOT, text=True).strip()


def plain(value):
    if isinstance(value, dict):
        return {str(key): plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [plain(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def write(path: Path | str, value) -> None:
    destination = safe(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError("output_exists")
    durable_write(destination, plain(value))


def write_csv(path: Path | str, rows: list[dict], fields: tuple[str, ...]) -> None:
    destination = safe(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError("output_exists")
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    temporary = destination.with_name("." + destination.name + ".pending")
    with temporary.open("x", newline="") as handle:
        handle.write(buffer.getvalue())
        handle.flush()
        os.fsync(handle.fileno())
    os.link(temporary, destination)
    temporary.unlink()


def line_at(path: Path, ordinal: int) -> bytes:
    with safe(path).open("rb") as handle:
        for index, line in enumerate(handle):
            if index == ordinal:
                return line
    raise ValueError("state_ordinal")


def preflight() -> dict:
    if git("status", "--porcelain"):
        raise RuntimeError("dirty_tree")
    git("merge-base", "--is-ancestor", START, "HEAD")
    if git("rev-parse", "v0.1.0^{}") != TAG:
        raise RuntimeError("release_changed")
    if Path(sys.prefix).resolve() != (ROOT / ".venv").resolve():
        raise RuntimeError("project_environment_required")
    bindings = {
        PREPARED: PREPARED_SHA, CANONICAL: CANONICAL_SHA, R8_JOURNAL: JOURNAL_SHA,
        R8_ORIGINAL: ORIGINAL_SHA, R8_EMERGENCY: EMERGENCY_SHA,
    }
    for path, expected in bindings.items():
        if sha(path) != expected:
            raise RuntimeError("retained_authority_changed")
    for path in (PROTOCOL, Path(__file__).relative_to(ROOT),
                 Path("src/defensive_network_disruption/geometry/comparator_diagnosis.py")):
        committed = subprocess.check_output(("git", "show", "HEAD:" + str(path)), cwd=ROOT)
        if hashlib.sha256(committed).hexdigest() != sha(path):
            raise RuntimeError("uncommitted_authority")
    return {"python": platform.python_version(), "numpy": np.__version__,
            "lock_sha256": sha("uv.lock"), "bindings": {str(k): v for k, v in bindings.items()}}


def synthetic_records(states: int) -> list[dict]:
    records = []
    sequence = 0

    def add(action, **payload):
        nonlocal sequence
        records.append({"schema_version": 1, "sequence": sequence,
                        "previous": "synthetic", "action": action, "payload": payload})
        sequence += 1

    add("initialized")
    add("access_authorized")
    for state_index in range(states):
        state = f"s{state_index}"
        edges = [f"e{edge}" for edge in range(10)]
        add("state_discovered", state=state, edges=edges)
        add("projection_attempt", state=state, attempt=f"p{state_index}")
        add("projection_materialized", attempt=f"p{state_index}", edges=edges)
        add("state_prepared", state=state)
    return records


def replay_scaling() -> tuple[list[dict], dict]:
    rows = []
    for states in (16, 32, 64, 128, 256, 512, 1024):
        records = synthetic_records(states)
        started = time.perf_counter()
        try:
            with __import__("defensive_network_disruption.geometry.comparator_diagnosis", fromlist=["wall_limit"]).wall_limit(OPERATION_LIMIT):
                replay(records)
            status = "completed"
        except DiagnosticTimeout:
            status = "timeout"
        rows.append({"states": states, "records": len(records),
                     "encoded_bytes": len(json.dumps(records, sort_keys=True)),
                     "seconds": time.perf_counter() - started, "status": status})
        if status == "timeout":
            break
    historical_records, head = read_journal(safe(R8_JOURNAL))
    counts = Counter(record["action"] for record in historical_records)
    return rows, {"records": len(historical_records), "bytes": safe(R8_JOURNAL).stat().st_size,
                  "head": head, "event_counts": dict(sorted(counts.items()))}


def diagnose() -> None:
    marker = LOCAL / "diagnose.marker"
    write(marker, {"session": "14ak", "state": STATE, "receiver": RECEIVER, "candidate": CANDIDATE})
    environment = preflight()
    total_started = time.perf_counter()
    stage_times = {}
    private = {}
    try:
        prepared_line = line_at(PREPARED, STATE)
        canonical_line = line_at(CANONICAL, STATE)
        prepared = project_prepared_edge(prepared_line.decode(), RECEIVER)
        canonical = project_canonical_edge(canonical_line.decode(), RECEIVER)
        require(selective_bytes(prepared) == selective_bytes(canonical), "selective_projection_mismatch")
        private["line_hashes"] = {"prepared": hashlib.sha256(prepared_line).hexdigest(),
                                  "canonical": hashlib.sha256(canonical_line).hexdigest(),
                                  "projection": hashlib.sha256(selective_bytes(prepared)).hexdigest()}

        origin = np.asarray(prepared["carrier"], dtype=np.float64)
        receiver = np.asarray(prepared["receiver"], dtype=np.float64)
        defenders = np.asarray(prepared["defenders"], dtype=np.float64)
        field = CarrierOriginField(CANDIDATE)
        function = lambda t: field.individual_values(origin, defenders,
            origin[None, :] + np.asarray(t, dtype=np.float64)[:, None] * (receiver - origin)[None, :])

        (joint, seconds) = timed(lambda: controlled_vector(
            lambda intervals: values_for_components(field, origin, receiver, defenders, intervals)),
            limit_seconds=OPERATION_LIMIT)
        stage_times["production_joint_simpson"] = seconds
        intervals, estimates, change = joint
        require(intervals is not None, "production_nonconvergence")

        ((onsets, envelope, partitions, switches), seconds) = timed(
            lambda: canonical_geometry(CANDIDATE, origin, receiver, defenders, function),
            limit_seconds=OPERATION_LIMIT)
        stage_times["canonical_structure"] = seconds
        onset_points = tuple(onset.canonical for onset in onsets)
        topology = audit_partitions(partitions, onset_points)
        topology.update({"switch_count": len(switches), "tie_interval_count": len(envelope.tie_intervals),
                         "bounded_piece_count": sum((b - a) <= 1e-12 / (len(partitions) - 1)
                                                    for a, b in zip(partitions[:-1], partitions[1:]))})

        (strict, seconds) = timed(lambda: bounded_adaptive_maximum(function, partitions, 1e-13),
                                  limit_seconds=OPERATION_LIMIT)
        stage_times["strict_piecewise"] = seconds
        (repeat, seconds) = timed(lambda: bounded_adaptive_maximum(function, partitions, 1e-11),
                                  limit_seconds=OPERATION_LIMIT)
        stage_times["repeat_piecewise"] = seconds
        onset_partitions = tuple(sorted({0.0, 1.0, *onset_points}))
        (unsplit, seconds) = timed(lambda: adaptive_maximum(function, onset_partitions, 1e-13),
                                   limit_seconds=OPERATION_LIMIT)
        stage_times["onset_only_adaptive"] = seconds
        disagreement = point_interval_distance(unsplit, strict)
        reproduced = disagreement > 1e-10
        require(reproduced, "historical_failure_not_reproduced")

        (uniform, seconds) = timed(lambda: uniform_simpson_curve(function, LADDER), limit_seconds=OPERATION_LIMIT)
        stage_times["uniform_simpson_ladder"] = seconds
        (piecewise, seconds) = timed(lambda: split_simpson_curve(function, partitions, LADDER), limit_seconds=OPERATION_LIMIT)
        stage_times["piecewise_simpson_ladder"] = seconds

        piece_rows = []
        piece_private = []
        for index, (lower, upper) in enumerate(zip(partitions[:-1], partitions[1:])):
            interval, elapsed = timed(lambda lo=lower, hi=upper:
                bounded_adaptive_maximum(function, (lo, hi), 1e-13), limit_seconds=OPERATION_LIMIT)
            piece_private.append({"piece": index, "lower": lower, "upper": upper,
                                  "integral": plain(interval), "seconds": elapsed})
            piece_rows.append({"piece": index, "bounded_residual": (upper-lower) <= 1e-12/(len(partitions)-1),
                               "finite": math.isfinite(interval.lower) and math.isfinite(interval.upper),
                               "seconds": elapsed})

        neighborhood_private = []
        neighborhood_public = []
        for onset_index, onset in enumerate(onset_points):
            for label, point in (("predecessor", np.nextafter(onset, -math.inf)),
                                 ("onset", onset), ("successor", np.nextafter(onset, math.inf))):
                values = function(np.array([point]))[0]
                q = origin + point * (receiver-origin)
                oracle = np.array([scalar_oracle(CANDIDATE, origin, defender, q) for defender in defenders])
                neighborhood_private.append({"onset": onset_index, "position": label, "t": point,
                                             "values": values.tolist(), "oracle": oracle.tolist(),
                                             "owners": np.flatnonzero(values >= np.max(values)-1e-12).tolist()})
                neighborhood_public.append({"onset": onset_index, "position": label,
                                            "finite": bool(np.isfinite(values).all()),
                                            "oracle_agrees": bool(np.allclose(values, oracle, atol=1e-12, rtol=1e-12))})

        replay_rows, historical_journal = replay_scaling()
        stage_times["total_before_closure"] = time.perf_counter() - total_started
        if stage_times["total_before_closure"] > TOTAL_LIMIT:
            raise DiagnosticTimeout("total_timeout")

        private.update({"production": {"intervals": intervals, "estimates": estimates, "change": change},
                        "strict": plain(strict), "repeat": plain(repeat), "unsplit": unsplit,
                        "disagreement": disagreement, "partitions": partitions,
                        "onsets": plain(onsets), "switches": plain(switches),
                        "envelope": plain(envelope), "piece_contributions": piece_private,
                        "onset_neighborhood": neighborhood_private,
                        "uniform_curve": uniform, "piecewise_curve": piecewise})
        write(LOCAL / "exact_evidence.json", private)
        private_hash = sha(LOCAL / "exact_evidence.json")

        write(OUT / "failure_authority.json", {"schema_version": 1, "retained_state_ordinal": STATE,
              "retained_receiver_ordinal": RECEIVER, "candidate": CANDIDATE, "gate": "piecewise_unsplit",
              "historical_values_available": False, "diagnostic_reproduced": True,
              "r8_original_failure_sha256": ORIGINAL_SHA, "r8_emergency_sha256": EMERGENCY_SHA,
              "r8_journal_sha256": JOURNAL_SHA, "private_evidence_sha256": private_hash})
        write(OUT / "topology_summary.json", {"schema_version": 1, **{k: v for k, v in topology.items()
              if k not in ("minimum_width", "maximum_width")}, "onset_only": len(switches) == 0 and not envelope.tie_intervals,
              "exact_values_private": True})
        write_csv(OUT / "unsplit_convergence.csv", sanitize_curve(uniform),
                  ("intervals", "evaluations", "successive_abs_delta", "highest_abs_delta", "seconds"))
        write_csv(OUT / "piecewise_convergence.csv", sanitize_curve(piecewise),
                  ("intervals", "evaluations", "successive_abs_delta", "highest_abs_delta", "seconds"))
        production_healthy = (point_interval_distance(estimates["maximum"], strict) <= 1e-6 and
                              point_interval_distance(float(uniform[-1]["estimate"]), strict) <= 1e-9)
        write(OUT / "production_numerical_health.json", {"schema_version": 1,
              "joint_simpson_converged": True, "accepted_intervals": intervals,
              "joint_maximum_piecewise_agreement": point_interval_distance(estimates["maximum"], strict) <= 1e-6,
              "direct_simpson_piecewise_agreement": point_interval_distance(float(uniform[-1]["estimate"]), strict) <= 1e-9,
              "strict_repeat_agreement": __import__("defensive_network_disruption.geometry.micro_interval_verifier", fromlist=["interval_distance"]).interval_distance(strict, repeat) <= 1e-10,
              "production_healthy": production_healthy, "exact_values_private": True})
        write_csv(OUT / "onset_neighborhood.csv", neighborhood_public,
                  ("onset", "position", "finite", "oracle_agrees"))
        write_csv(OUT / "piece_contributions.csv", piece_rows,
                  ("piece", "bounded_residual", "finite", "seconds"))
        write(OUT / "runtime_breakdown.json", {"schema_version": 1, "diagnostic_seconds": stage_times,
              "historical_55_minute_attribution": "unavailable", "operation_limit_seconds": OPERATION_LIMIT,
              "total_limit_seconds": TOTAL_LIMIT})

        numerical = ("A" if production_healthy and float(uniform[-1]["highest_abs_delta"] if "highest_abs_delta" in uniform[-1] else 0) == 0
                     else "G")
        write(OUT / "agreement_gate_diagnosis.json", {"schema_version": 1, "gate": "piecewise_unsplit",
              "absolute_tolerance": 1e-10, "failure_reproduced": True,
              "disagreement_exceeds_gate": disagreement > 1e-10, "same_integrand": True,
              "same_quadrature_family_for_adaptive_paths": True, "different_structural_partitions": True,
              "classification": numerical, "readiness": 1 if numerical in ("A", "B", "E") else 4,
              "exact_disagreement_private": True})
        write(OUT / "synthetic_reproduction.json", {"schema_version": 1, "status": "documented_not_executed",
              "reason": "post_diagnostic_topology_fixture_deferred_to_separate_authority"})

        completed = [row for row in replay_rows if row["status"] == "completed"]
        ratios = []
        for left, right in zip(completed[:-1], completed[1:], strict=False):
            if left["seconds"] > 0:
                ratios.append(right["seconds"] / left["seconds"])
        publication_class = "P1" if ratios and max(ratios[-3:]) >= 3.0 else "P2"
        write(OUT / "publication_replay_diagnosis.json", {"schema_version": 1,
              "historical_journal": historical_journal, "synthetic_scaling": replay_rows,
              "source_prefix_replay": True, "duplicate_failure_handling": True,
              "complexity": "quadratic_prefix_reduction", "classification": publication_class,
              "emergency_preserved_original": True, "emergency_normal_authority": False})
        write(OUT / "publication_scalability_options.json", {"schema_version": 1, "selected_for_future":
              "single_pass_streaming_replay_with_authenticated_checkpoints",
              "implemented": False, "requirements": ["complete_hash_chain", "exact_event_order",
              "prefix_checkpoint_binding", "suffix_replay", "historical_small_journal_compatibility",
              "independent_emergency_preservation"]})
        qc = {"schema_version": 1, "status": "closed", "execution_valid": True,
              "numerical_classification": numerical, "readiness": 1 if numerical in ("A", "B", "E") else 4,
              "publication_classification": publication_class, "only_authorized_edge_inspected": True,
              "scientific_summaries_inspected": False, "private_evidence_sha256": private_hash,
              "environment": environment}
        write(OUT / "qc.json", qc)
        outputs = {name: sha(OUT / name) for name in PUBLIC}
        write(OUT / "manifest.json", {"schema_version": 1, "status": "closed", "start": START,
              "protocol_sha256": sha(PROTOCOL), "implementation_commit": git("rev-parse", "HEAD"),
              "outputs": outputs, "private_evidence_sha256": private_hash})
        publication_check()
        print(json.dumps({"numerical": numerical, "readiness": qc["readiness"],
                          "publication": publication_class}, sort_keys=True))
    except BaseException as error:
        emergency = LOCAL / "emergency_failure.json"
        if not safe(emergency).exists():
            write(emergency, {"schema_version": 1, "exception": type(error).__name__,
                  "traceback": traceback.format_exc(), "state": STATE, "receiver": RECEIVER,
                  "candidate": CANDIDATE, "elapsed_seconds": time.perf_counter() - total_started})
        raise


def publication_check() -> None:
    manifest = json.loads(safe(OUT / "manifest.json").read_text())
    if set(manifest) != {"schema_version", "status", "start", "protocol_sha256",
                         "implementation_commit", "outputs", "private_evidence_sha256"}:
        raise ValueError("manifest_schema")
    if set(manifest["outputs"]) != set(PUBLIC):
        raise ValueError("manifest_members")
    for name, expected in manifest["outputs"].items():
        if sha(OUT / name) != expected:
            raise ValueError("output_hash")
    if sha(LOCAL / "exact_evidence.json") != manifest["private_evidence_sha256"]:
        raise ValueError("private_hash")
    public_text = "".join(safe(OUT / name).read_text() for name in (*PUBLIC, "manifest.json"))
    for forbidden in ("/Users/", "/private/", '"carrier"', '"receiver_xy"', '"defenders"'):
        if forbidden in public_text:
            raise ValueError("publication_privacy")
    print("Session 14ak publication package verified")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "diagnose", "publication-check"))
    args = parser.parse_args()
    if args.command == "preflight":
        print(json.dumps(preflight(), sort_keys=True))
    elif args.command == "diagnose":
        diagnose()
    else:
        publication_check()


if __name__ == "__main__":
    main()
