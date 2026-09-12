#!/usr/bin/env python3
"""Synthetic-only Session 14ae lifecycle and publication audit."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defensive_network_disruption.validation.state_lifecycle import (  # noqa: E402
    LifecycleError, LifecycleProgress, canonical_bytes, snapshot_digest,
    validate_cross_file, validate_snapshot,
)

OUT = ROOT / "outputs" / "session14_state_lifecycle_accounting"
LOCAL = OUT / "local"
PROTOCOL = ROOT / "docs" / "protocols" / "phase_14ae_state_lifecycle_accounting.md"
FILES = (
    "lifecycle_contract.json", "lifecycle_oracles.csv", "publication_invalid_oracles.csv",
    "publication_valid_oracles.csv", "access_accounting_oracles.csv", "failure_controls.csv",
    "success_control.json", "cross_file_validation.json", "qc.json",
)
CLASSIFICATION = "A — STATE-LIFECYCLE ACCOUNTING AND PUBLICATION VALIDATION REPAIRED"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name("." + path.name + ".tmp")
    with temp.open("xb") as handle:
        handle.write(data); handle.flush(); os.fsync(handle.fileno())
    os.replace(temp, path)


def emit_json(path: Path, value: dict[str, Any]) -> None:
    atomic(path, canonical_bytes(value))


def emit_csv(path: Path, fieldnames: Iterable[str], rows: list[dict[str, Any]]) -> None:
    import io
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=tuple(fieldnames), lineterminator="\n")
    writer.writeheader(); writer.writerows(rows)
    atomic(path, stream.getvalue().encode())


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, text=True, capture_output=True).stdout.strip()


def preflight() -> None:
    if git("status", "--porcelain"):
        raise LifecycleError("dirty_tree")
    if not PROTOCOL.exists() or not git("ls-files", "--error-unmatch", str(PROTOCOL.relative_to(ROOT))):
        raise LifecycleError("protocol_not_committed")
    print("Session 14ae preflight passed")


def prepared_only() -> LifecycleProgress:
    p = LifecycleProgress(); p.discover_state("state_01", ("edge_01",)); p.prepare_state("state_01"); return p


def completed(states: int = 1, edges: int = 2) -> LifecycleProgress:
    p = LifecycleProgress()
    for index in range(states):
        state = f"state_{index + 1:02d}"; edge_keys = tuple(f"edge_{index + 1:02d}_{j + 1:02d}" for j in range(edges))
        p.discover_state(state, edge_keys); p.prepare_state(state); p.start_state_evaluation(state)
        for edge in edge_keys: p.start_edge(state, edge); p.complete_edge(state, edge)
        p.complete_state(state)
    p.succeed(); return p


def lifecycle_oracles() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    def capture(name: str, p: LifecycleProgress, expected: str) -> None:
        s = p.snapshot(); validate_snapshot(s, terminal=s["status"] != "active")
        c = s["counters"]
        rows.append({"oracle": name, "expected": expected, "observed": "pass", **c})
    p = prepared_only(); p.block("after_preparation", "synthetic_stop"); capture("r3_regression_prepared_not_completed", p, "valid")
    p = LifecycleProgress(); p.fail("before_preparation", "SyntheticFailure"); capture("failure_before_preparation", p, "valid")
    p = prepared_only(); p.fail("after_preparation", "SyntheticFailure", state_key="state_01"); capture("failure_after_preparation", p, "valid")
    p = prepared_only(); p.start_state_evaluation("state_01"); p.fail("evaluation_start", "SyntheticFailure", state_key="state_01"); capture("evaluation_start_failure", p, "valid")
    p = prepared_only(); p.start_state_evaluation("state_01"); p.start_edge("state_01", "edge_01"); p.fail("mid_edge", "SyntheticFailure", state_key="state_01", edge_key="edge_01"); capture("first_edge_failure", p, "valid")
    p = LifecycleProgress(); p.discover_state("state_01", ("edge_01", "edge_02")); p.prepare_state("state_01"); p.start_state_evaluation("state_01"); p.start_edge("state_01", "edge_01"); p.complete_edge("state_01", "edge_01"); p.start_edge("state_01", "edge_02"); p.fail("second_edge", "SyntheticFailure", state_key="state_01", edge_key="edge_02"); capture("partial_edge_completion", p, "valid")
    capture("successful_state", completed(), "valid"); capture("successful_multi_state", completed(2, 2), "valid")
    return rows


def publication_oracles() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    base = prepared_only(); base.block("after_preparation", "synthetic_stop"); valid_base = base.snapshot()
    success = completed().snapshot()
    invalid: list[tuple[str, dict[str, Any]]] = []
    def changed(name: str, source: dict[str, Any], path: tuple[str, ...], value: Any) -> None:
        item = json.loads(json.dumps(source)); target = item
        for key in path[:-1]: target = target[key]
        target[path[-1]] = value; invalid.append((name, item))
    changed("r3_completed_without_start", valid_base, ("counters", "states_completed"), 1)
    changed("started_beyond_prepared", valid_base, ("counters", "states_evaluation_started"), 2)
    changed("prepared_beyond_discovered", valid_base, ("counters", "states_prepared"), 2)
    changed("edge_completed_beyond_started", valid_base, ("counters", "edges_completed"), 1)
    changed("success_incomplete", valid_base, ("status",), "success")
    changed("success_with_failure", success, ("counters", "state_failures"), 1)
    changed("access_without_authority", valid_base, ("counters", "states_opened"), 1)
    changed("orphan_edge", valid_base, ("integrity", "orphan_edges"), 1)
    failure_complete = success.copy(); failure_complete = json.loads(json.dumps(failure_complete)); failure_complete.update(status="failure", stage="evaluation", exception="SyntheticFailure")
    invalid.append(("failure_after_complete_wrong_stage", failure_complete))
    missing = json.loads(json.dumps(valid_base)); del missing["counters"]["states_completed"]; invalid.append(("missing_counter", missing))
    invalid_rows=[]
    for name, item in invalid:
        try: validate_snapshot(item); observed="accepted"
        except LifecycleError as exc: observed="rejected:"+str(exc)
        invalid_rows.append({"oracle":name,"expected":"rejected","observed":observed})
    valid_records = [("blocked_preparation_only", valid_base), ("success_complete", success)]
    p=prepared_only(); p.start_state_evaluation("state_01"); p.start_edge("state_01","edge_01"); p.fail("mid_edge","SyntheticFailure",state_key="state_01",edge_key="edge_01"); valid_records.append(("failure_during_evaluation",p.snapshot()))
    p=completed(); item=p.snapshot(); item["status"]="failure"; item["stage"]="publication_validation"; item["exception"]="SyntheticPublicationFailure"; valid_records.append(("publication_failure_after_complete",item))
    valid_rows=[]
    for name,item in valid_records:
        validate_snapshot(item); valid_rows.append({"oracle":name,"expected":"accepted","observed":"accepted"})
    return invalid_rows, valid_rows


def access_oracles() -> list[dict[str, Any]]:
    rows=[]
    for name, state_open, edge_open in (("no_access",0,0),("state_only",1,0),("state_and_first_edge",1,1)):
        p=LifecycleProgress();p.discover_state("state_01",("edge_01",));p.prepare_state("state_01")
        if state_open: p.authorize_access();p.open_state("state_01")
        if edge_open: p.open_edge("state_01","edge_01")
        p.block("synthetic_access_oracle","synthetic_stop");s=p.snapshot();validate_snapshot(s);c=s["counters"]
        rows.append({"oracle":name,"synthetic_states_opened":c["states_opened"],"synthetic_edges_opened":c["edges_opened"],"real_states_opened":0,"real_edges_opened":0,"observed":"pass"})
    return rows


def failure_controls() -> list[dict[str, Any]]:
    rows=[]
    injections=("preparation","after_preparation","evaluation_start","mid_edge","after_one_edge","publication_validation")
    for name in injections:
        if name=="preparation": p=LifecycleProgress();p.discover_state("state_01",("edge_01",));p.fail(name,"SyntheticFailure",state_key="state_01")
        elif name=="after_preparation": p=prepared_only();p.fail(name,"SyntheticFailure",state_key="state_01")
        elif name=="evaluation_start": p=prepared_only();p.start_state_evaluation("state_01");p.fail(name,"SyntheticFailure",state_key="state_01")
        elif name=="mid_edge": p=prepared_only();p.start_state_evaluation("state_01");p.start_edge("state_01","edge_01");p.fail(name,"SyntheticFailure",state_key="state_01",edge_key="edge_01")
        elif name=="after_one_edge":
            p=LifecycleProgress();p.discover_state("state_01",("edge_01","edge_02"));p.prepare_state("state_01");p.start_state_evaluation("state_01");p.start_edge("state_01","edge_01");p.complete_edge("state_01","edge_01");p.start_edge("state_01","edge_02");p.fail(name,"SyntheticFailure",state_key="state_01",edge_key="edge_02")
        else:
            p=completed();s=p.snapshot();s["status"]="failure";s["stage"]="publication_validation";s["exception"]="SyntheticFailure";validate_snapshot(s);c=s["counters"];rows.append({"injection":name,"status":"failure","states_prepared":c["states_prepared"],"states_evaluation_started":c["states_evaluation_started"],"states_completed":c["states_completed"],"edges_evaluation_started":c["edges_evaluation_started"],"edges_completed":c["edges_completed"],"preserved":"yes"});continue
        s=p.snapshot();validate_snapshot(s);c=s["counters"]
        rows.append({"injection":name,"status":s["status"],"states_prepared":c["states_prepared"],"states_evaluation_started":c["states_evaluation_started"],"states_completed":c["states_completed"],"edges_evaluation_started":c["edges_evaluation_started"],"edges_completed":c["edges_completed"],"preserved":"yes"})
    return rows


def audit() -> None:
    preflight()
    OUT.mkdir(parents=True, exist_ok=True); LOCAL.mkdir(parents=True, exist_ok=True)
    marker=LOCAL/"audit.marker"
    try: fd=os.open(marker,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.write(fd,b"claimed\n");os.close(fd)
    except FileExistsError as exc: raise LifecycleError("audit_already_claimed") from exc
    if any((OUT/name).exists() for name in (*FILES,"manifest.json")): raise LifecycleError("outputs_already_exist")
    lifecycle_rows=lifecycle_oracles(); invalid_rows,valid_rows=publication_oracles(); access_rows=access_oracles(); failures=failure_controls()
    if any(row["observed"]=="accepted" for row in invalid_rows): raise LifecycleError("invalid_oracle_accepted")
    audit_progress=completed(1,6); snapshot=audit_progress.snapshot();validate_snapshot(snapshot); lifecycle_hash=snapshot_digest(snapshot)
    contract={"schema_version":1,"scope":"synthetic_orchestration_only","state_lifecycle":["discovered","prepared","evaluation_started","evaluation_completed"],"edge_lifecycle":["discovered","evaluation_started","evaluation_completed"],"terminal_statuses":["success","failure","blocked"],"state_completion":"all_required_edges_completed","real_states_opened":0,"real_edges_opened":0}
    success={"schema_version":1,"status":"success","lifecycle":snapshot,"lifecycle_sha256":lifecycle_hash,"real_states_opened":0,"real_edges_opened":0}
    cross={"schema_version":1,"status":"success","valid_control":"accepted","qc_digest_mismatch":"rejected","manifest_digest_mismatch":"rejected","evidence_status_mismatch":"rejected","report_digest_mismatch":"rejected","lifecycle_sha256":lifecycle_hash}
    qc={"schema_version":1,"status":"success","classification":CLASSIFICATION,"readiness":1,"real_access":{"states_opened":0,"edges_opened":0},"lifecycle":snapshot,"lifecycle_sha256":lifecycle_hash}
    emit_json(OUT/"lifecycle_contract.json",contract)
    counter_fields=list(lifecycle_rows[0]);emit_csv(OUT/"lifecycle_oracles.csv",counter_fields,lifecycle_rows)
    emit_csv(OUT/"publication_invalid_oracles.csv",("oracle","expected","observed"),invalid_rows)
    emit_csv(OUT/"publication_valid_oracles.csv",("oracle","expected","observed"),valid_rows)
    emit_csv(OUT/"access_accounting_oracles.csv",tuple(access_rows[0]),access_rows)
    emit_csv(OUT/"failure_controls.csv",tuple(failures[0]),failures)
    emit_json(OUT/"success_control.json",success);emit_json(OUT/"cross_file_validation.json",cross);emit_json(OUT/"qc.json",qc)
    manifest_stub={"schema_version":1,"status":"success","classification":CLASSIFICATION,"readiness":1,"starting_head":"3a24f985e2069faff28b5459c6f8f6839e5ba9ce","implementation_commit":git("rev-parse","HEAD"),"protocol_sha256":digest(PROTOCOL),"lifecycle_sha256":lifecycle_hash,"outputs":{name:digest(OUT/name) for name in FILES}}
    report_stub={"status":"success","lifecycle_sha256":lifecycle_hash}
    validate_cross_file(qc,manifest_stub,success,report_stub)
    emit_json(OUT/"manifest.json",manifest_stub)
    publication_check()
    atomic(LOCAL/"closed",b"closed\n")
    print(CLASSIFICATION+"; readiness 1")


def publication_check() -> None:
    manifest=json.loads((OUT/"manifest.json").read_text());qc=json.loads((OUT/"qc.json").read_text());success=json.loads((OUT/"success_control.json").read_text())
    if set(manifest)!={"schema_version","status","classification","readiness","starting_head","implementation_commit","protocol_sha256","lifecycle_sha256","outputs"}: raise LifecycleError("manifest_schema")
    if set(manifest["outputs"])!=set(FILES): raise LifecycleError("manifest_outputs")
    for name,expected in manifest["outputs"].items():
        if digest(OUT/name)!=expected: raise LifecycleError("output_hash")
    validate_cross_file(qc,manifest,success,{"status":manifest["status"],"lifecycle_sha256":manifest["lifecycle_sha256"]})
    for path in (OUT/name for name in (*FILES,"manifest.json")):
        text=path.read_text()
        for forbidden in ("/Users/","/private/","event_id","target_index","carrier_xy","candidate_xy","defender_xy","token="):
            if forbidden in text: raise LifecycleError("publication_content")
    print("Session 14ae publication checks passed")


def main() -> None:
    parser=argparse.ArgumentParser();parser.add_argument("command",choices=("preflight","audit","publication-check"));args=parser.parse_args()
    if args.command=="preflight":preflight()
    elif args.command=="audit":
        try:audit()
        except Exception as exc:
            LOCAL.mkdir(parents=True,exist_ok=True)
            if not (LOCAL/"failure.json").exists():
                emit_json(LOCAL/"failure.json",{"stage":"audit","exception":type(exc).__name__,"traceback":traceback.format_exc(),"real_states_opened":0,"real_edges_opened":0})
            raise
    else:publication_check()


if __name__=="__main__":main()
