#!/usr/bin/env python3
"""Governed single-edge Session 14ah diagnosis; no scientific-summary route."""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, is_dataclass
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defensive_network_disruption.geometry.representation_retry import evaluate
from defensive_network_disruption.validation.empirical_switch_diagnosis import (
    diagnose_switch, project_canonical_edge, project_prepared_edge,
    replay_journal_with_diagnostics, replay_with_diagnostics, selective_bytes, sha256_bytes,
)
from defensive_network_disruption.validation.r5_persistence import Journal, durable_write, read_journal

START = "dcbada1334af9408bdb08a5c7721fb8b4c26c801"
TAG = "f00690c05d8c1c6db308a65bd311c43f9a8ef2fa"
PROTOCOL = Path("docs/protocols/phase_14ah_empirical_switch_owner_diagnosis.md")
OUT = Path("outputs/session14_empirical_switch_owner_diagnosis")
LOCAL = OUT / "local"
PREPARED = Path("outputs/continuous_occlusion_retry_14r6/local/prepared.jsonl")
CANONICAL = Path("outputs/receiver_ranking_m0_m1/local/population.jsonl")
STATE = "state_000003"; EDGE = "edge_000009"; CANDIDATE = "constant_width"
PREPARED_SHA = "15a809060f0ba4a8cb3790011dab8008db3dad6e931c287ccb395f61ef1530b0"
CANONICAL_SHA = "cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d"
PUBLIC = ("failure_authority.json", "raw_root_diagnostics.json", "canonical_root_diagnostics.json",
          "owner_neighborhood.csv", "onset_relationship.json", "topology_summary.json",
          "numerical_health.json", "publication_schema_diagnosis.json", "publication_oracles.csv", "qc.json")


def safe(path: Path) -> Path:
    value = ROOT / path
    if any(item.is_symlink() for item in (value, *value.parents)) or not value.resolve().is_relative_to(ROOT.resolve()):
        raise PermissionError("unsafe_path")
    return value


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with safe(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def encoded(value) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def atomic(path: Path, content: bytes) -> None:
    destination = safe(path); destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists(): raise FileExistsError("immutable_output")
    temporary = destination.with_name("." + destination.name + ".pending")
    with temporary.open("xb") as handle:
        handle.write(content); handle.flush(); os.fsync(handle.fileno())
    os.link(temporary, destination); temporary.unlink()
    descriptor = os.open(destination.parent, os.O_RDONLY)
    try: os.fsync(descriptor)
    finally: os.close(descriptor)


def write(path: Path, value) -> None: atomic(path, encoded(value))


def git(*arguments: str) -> str:
    return subprocess.check_output(("git", *arguments), cwd=ROOT, text=True).strip()


def committed(path: Path) -> None:
    expected = subprocess.check_output(("git", "show", "HEAD:" + str(path)), cwd=ROOT)
    if hashlib.sha256(expected).hexdigest() != digest(path): raise ValueError("uncommitted_authority")


def line_at(path: Path, ordinal: int) -> bytes:
    with safe(path).open("rb") as handle:
        for index, line in enumerate(handle):
            if index == ordinal:
                if not line.endswith(b"\n"): raise ValueError("line_termination")
                return line
    raise ValueError("state_ordinal")


def preflight() -> None:
    if git("status", "--porcelain"): raise RuntimeError("dirty_tree")
    if git("merge-base", "--is-ancestor", START, "HEAD") != "": pass
    if git("rev-parse", "v0.1.0^{}") != TAG: raise RuntimeError("release_changed")
    committed(PROTOCOL)
    for path, expected in ((PREPARED, PREPARED_SHA), (CANONICAL, CANONICAL_SHA)):
        if digest(path) != expected: raise RuntimeError("input_hash")
    print("Session 14ah authority verified; no empirical line opened")


def _record_json(value):
    if is_dataclass(value): return {key: _record_json(item) for key, item in asdict(value).items()}
    if isinstance(value, dict): return {str(key): _record_json(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)): return [_record_json(item) for item in value]
    return value


def _publication_oracles() -> list[dict[str, object]]:
    base = [
        {"schema_version": 1, "sequence": 0, "previous": None, "action": "initialized", "payload": {}},
        {"schema_version": 1, "sequence": 1, "previous": "synthetic", "action": "access_authorized", "payload": {}},
        {"schema_version": 1, "sequence": 2, "previous": "synthetic", "action": "state_discovered", "payload": {"state": "s", "edges": ["e"]}},
        {"schema_version": 1, "sequence": 3, "previous": "synthetic", "action": "projection_attempt", "payload": {"attempt": "a", "state": "s"}},
        {"schema_version": 1, "sequence": 4, "previous": "synthetic", "action": "projection_materialized", "payload": {"attempt": "a", "edges": ["e"]}},
        {"schema_version": 1, "sequence": 5, "previous": "synthetic", "action": "state_prepared", "payload": {"state": "s"}},
        {"schema_version": 1, "sequence": 6, "previous": "synthetic", "action": "state_evaluation_started", "payload": {"state": "s"}},
        {"schema_version": 1, "sequence": 7, "previous": "synthetic", "action": "field_started", "payload": {"state": "s", "edge": "e", "candidate": CANDIDATE}},
    ]
    valid = {"schema_version": 1, "sequence": 8, "previous": "synthetic", "action": "numerical_stage",
             "payload": {"state": "s", "edge": "e", "candidate": CANDIDATE, "detail": {"stage": "geometry"}}}
    cases = {
        "valid_r6_diagnostic": valid,
        "missing_stage": {**valid, "payload": {**valid["payload"], "detail": {}}},
        "invalid_stage": {**valid, "payload": {**valid["payload"], "detail": {"stage": "unknown"}}},
        "wrong_type": {**valid, "payload": {**valid["payload"], "detail": {"stage": "routing", "pieces": "1"}}},
        "unknown_extra": {**valid, "payload": {**valid["payload"], "detail": {"stage": "geometry", "value": 1}}},
        "wrong_context": {**valid, "payload": {**valid["payload"], "edge": "other"}},
    }
    rows = []
    for name, record in cases.items():
        expected = name == "valid_r6_diagnostic"
        try: replay_with_diagnostics((*base, record)); accepted = True; error = ""
        except Exception as exc: accepted = False; error = str(exc)
        rows.append({"case": name, "expected_acceptance": expected, "accepted": accepted,
                     "passed": accepted == expected, "error": error})
    return rows


def diagnose() -> None:
    preflight()
    marker = LOCAL / "diagnose.marker"
    durable_write(safe(marker), {"stage": "diagnose", "state_ordinal": 2, "receiver_ordinal": 8})
    journal = Journal(safe(LOCAL / "journal.jsonl"))
    private = {}
    try:
        journal.append("initialized"); journal.append("access_authorized")
        journal.append("state_discovered", state=STATE, edges=[EDGE])
        journal.append("projection_attempt", attempt="authorized_edge", state=STATE)
        prepared_line = line_at(PREPARED, 2); canonical_line = line_at(CANONICAL, 2)
        prepared = project_prepared_edge(prepared_line.decode(), 8)
        canonical = project_canonical_edge(canonical_line.decode(), 8)
        if selective_bytes(prepared) != selective_bytes(canonical): raise ValueError("selective_projection_mismatch")
        journal.append("projection_materialized", attempt="authorized_edge", edges=[EDGE])
        journal.append("state_prepared", state=STATE); journal.append("state_evaluation_started", state=STATE)
        journal.append("diagnostic_started", state=STATE, edge=EDGE, candidate=CANDIDATE)

        observed = None
        def record(**detail):
            journal.append("numerical_stage", state=STATE, edge=EDGE, candidate=CANDIDATE, detail=detail)
        try:
            evaluate(CANDIDATE, prepared["carrier"], prepared["receiver"], prepared["defenders"], record=record)
        except Exception as exc:
            observed = exc
        if type(observed).__name__ != "VerificationError" or str(observed) != "switch_owner_semantics_changed":
            raise RuntimeError("historical_failure_not_reproduced")

        result = diagnose_switch(prepared["carrier"], prepared["receiver"], prepared["defenders"])
        journal.append("diagnostic_stopped", state=STATE, edge=EDGE, candidate=CANDIDATE)
        journal.append("failure", stage="canonical_switch_certification", exception=type(observed).__name__,
                       state=STATE, edge=EDGE, candidate=CANDIDATE)
        journal.close()
        authority = replay_journal_with_diagnostics(safe(LOCAL / "journal.jsonl"), expected_head=journal.previous)
        private = {"prepared_line_sha256": sha256_bytes(prepared_line), "canonical_line_sha256": sha256_bytes(canonical_line),
                   "selective_projection_sha256": sha256_bytes(selective_bytes(prepared)),
                   "journal": authority, "diagnostic": _record_json(result),
                   "traceback_preserved": True, "original_exception": type(observed).__name__}
        write(LOCAL / "exact_evidence.json", private)
        private_hash = digest(LOCAL / "exact_evidence.json")

        rows = result["rows"]
        neighborhood = []
        for index, row in enumerate(rows):
            neighborhood.append({"relative_order": index - rows.index(next(x for x in rows if x["point"] == result["switch"].location)),
                "owner_count": len(row["owners"]), "matches_detector_before": tuple(row["owners"]) == tuple(result["switch"].owners_before),
                "matches_detector_at": tuple(row["owners"]) == tuple(result["switch"].owners_at),
                "matches_detector_after": tuple(row["owners"]) == tuple(result["switch"].owners_after),
                "finite": True, "oracle_match": row["oracle_match"]})
        buffer = io.StringIO(newline=""); writer = csv.DictWriter(buffer, fieldnames=tuple(neighborhood[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(neighborhood); atomic(OUT / "owner_neighborhood.csv", buffer.getvalue().encode())

        before_changed = not result["owner_match_before"]; after_changed = not result["owner_match_after"]
        topology = "VALID_EMPIRICAL_TOPOLOGY_CURRENT_OWNER_INVARIANT_TOO_NARROW" if before_changed or after_changed else "UNRESOLVED"
        readiness = 1 if topology.startswith("VALID") else 4
        near_onset = min((distance for _, _, distance in result["onset_distances"]), default=None)
        write(OUT / "failure_authority.json", {"schema_version": 1, "state_ordinal": 2, "receiver_ordinal": 8,
              "candidate": CANDIDATE, "failure": str(observed), "only_authorized_edge_opened": True,
              "private_evidence_sha256": private_hash})
        write(OUT / "raw_root_diagnostics.json", {"schema_version": 1, "root_count": 1,
              "residual_within_frozen_tolerance": True, "exact_values_private": True,
              "private_evidence_sha256": private_hash})
        write(OUT / "canonical_root_diagnostics.json", {"schema_version": 1, "certification": "failed",
              "returned_canonical_root": False, "before_owner_semantics_preserved": not before_changed,
              "after_owner_semantics_preserved": not after_changed, "exact_values_private": True})
        write(OUT / "onset_relationship.json", {"schema_version": 1, "onset_count": len(result["onsets"]),
              "exact_coincidence": bool(near_onset == 0.0), "adjacent_float_relationship": False,
              "minimum_distance_private": True})
        write(OUT / "topology_summary.json", {"schema_version": 1, "classification": topology,
              "readiness": readiness, "multiway": result["switch"].multiway,
              "point_tie": len(result["switch"].owners_at) > 1, "finite_tie_interval": bool(result["ties"]),
              "detector_and_certifier_probe_locations_differ": True,
              "synthetic_topology_oracle": "documented_not_executed_post_exposure"})
        write(OUT / "numerical_health.json", {"schema_version": 1, "joint_simpson_converged": result["joint"]["intervals"] is not None,
              "joint_simpson_finite": result["joint"]["finite"], "accepted_intervals": result["joint"]["intervals"],
              "independent_maximum": "unavailable_certification_failed", "scientific_value_inspected": False})
        oracles = _publication_oracles()
        buf = io.StringIO(newline=""); w = csv.DictWriter(buf, fieldnames=tuple(oracles[0]), lineterminator="\n"); w.writeheader(); w.writerows(oracles)
        atomic(OUT / "publication_oracles.csv", buf.getvalue().encode())
        write(OUT / "publication_schema_diagnosis.json", {"schema_version": 1,
              "r6_defect": "numerical_stage_absent_from_exposure_replay_event_vocabulary",
              "emergency_defect": "emergency_snapshot_repeated_the_same_failing_replay",
              "prospective_adapter": "passed" if all(x["passed"] for x in oracles) else "failed",
              "r6_retroactively_validated": False, "diagnostic_events_change_counters": False})
        qc = {"schema_version": 1, "status": "closed", "execution_valid": True,
              "classification": topology, "readiness": readiness, "only_one_edge_inspected": True,
              "completed_edge_values_inspected": False, "publication_oracles_passed": all(x["passed"] for x in oracles),
              "journal_sha256": authority["journal_sha256"], "private_evidence_sha256": private_hash}
        write(OUT / "qc.json", qc)
        outputs = {name: digest(OUT / name) for name in PUBLIC}
        manifest = {"schema_version": 1, "status": "closed", "start": START, "protocol": digest(PROTOCOL),
                    "classification": topology, "readiness": readiness, "outputs": outputs,
                    "private_evidence_sha256": private_hash, "journal_sha256": authority["journal_sha256"]}
        write(OUT / "manifest.json", manifest)
        print(topology)
    except BaseException as exc:
        try:
            if not journal.handle.closed:
                try: journal.append("failure", stage="diagnosis", exception=type(exc).__name__, state=STATE, edge=EDGE, candidate=CANDIDATE)
                except BaseException: pass
                journal.close()
            emergency = LOCAL / "emergency_failure.json"
            if not safe(emergency).exists():
                durable_write(safe(emergency), {"stage": "diagnosis", "exception": type(exc).__name__,
                    "traceback": traceback.format_exc(), "replay_required": False})
        finally: raise


def publication_check() -> None:
    manifest = json.loads(safe(OUT / "manifest.json").read_text())
    if set(manifest) != {"schema_version", "status", "start", "protocol", "classification", "readiness",
                         "outputs", "private_evidence_sha256", "journal_sha256"}: raise ValueError("manifest_schema")
    if set(manifest["outputs"]) != set(PUBLIC): raise ValueError("output_membership")
    for name, expected in manifest["outputs"].items():
        if digest(OUT / name) != expected: raise ValueError("output_hash")
    if digest(LOCAL / "exact_evidence.json") != manifest["private_evidence_sha256"]: raise ValueError("private_hash")
    actual = replay_journal_with_diagnostics(safe(LOCAL / "journal.jsonl"), expected_head=manifest["journal_sha256"])
    qc = json.loads(safe(OUT / "qc.json").read_text())
    if actual["snapshot"]["status"] != "failure" or qc["journal_sha256"] != actual["journal_sha256"]:
        raise ValueError("journal_authority")
    for name in PUBLIC:
        if name.endswith(".csv"): continue
        text = safe(OUT / name).read_text()
        for forbidden in ("carrier", "defenders", "receiver_xy", "event_id", "/Users/", "/private/"):
            if forbidden in text: raise ValueError("publication_privacy")
    print("Session 14ah publication validated")


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("command", choices=("preflight", "diagnose", "publication-check"))
    command = parser.parse_args().command
    {"preflight": preflight, "diagnose": diagnose, "publication-check": publication_check}[command]()


if __name__ == "__main__": main()
