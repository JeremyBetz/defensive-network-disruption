#!/usr/bin/env python3
"""One R9J diagnosis. Dependency imports occur inside the failure boundary."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/continuous_occlusion_r9i_blocker_diagnosis"
OLD = ROOT / "outputs/continuous_occlusion_empirical_retry_r9i/local"
PROTOCOL = "docs/protocols/phase_14r9j_r9i_blocker_diagnosis.md"
PREPARED_HASH = "15a809060f0ba4a8cb3790011dab8008db3dad6e931c287ccb395f61ef1530b0"
JOURNAL_HASH = "6f1c2110d20fc0edbfe9d337f231e829a73df9d90eb47f65f6afb2366054ef3c"
FAILURE_HASH = "7644e3cb9686e89bed1b0101366c7d09f6aeb440975f3b4055f30a3f2469efef"
EMERGENCY_HASH = "959e79b871e05eae4b7c937eda26cd5fa3ba58e7a366ad8a4d922ebb4f70f479"


def bootstrap_write(path, value):
    """Independent create-once preservation even if the package cannot import."""
    path = Path(path)
    if any(p.is_symlink() for p in (path, *path.parents)): raise PermissionError("symlink")
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)+"\n").encode()
    temp = path.with_name("."+path.name+".pending")
    with temp.open("xb") as f:
        f.write(raw); f.flush(); os.fsync(f.fileno())
    os.link(temp, path); temp.unlink()
    fd = os.open(path.parent, os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)


def entry(folder, work):
    folder = Path(folder); local = folder/"local"
    bootstrap_write(local/"diagnosis.marker", {"schema_version": 1, "reserved": True, "authorizes_access": False})
    try:
        return work(folder)
    except BaseException as error:
        try:
            bootstrap_write(local/"outer_emergency.json", {"schema_version": 1,
                "exception": type(error).__name__, "message": str(error),
                "traceback": "".join(traceback.format_exception(error)), "status": "invalid"})
        except BaseException:
            # Do not replace the original exception with failed emergency I/O.
            pass
        raise


def git(*args):
    return subprocess.check_output(("git", *args), cwd=ROOT, text=True).strip()


def preflight():
    from defensive_network_disruption.validation import r9j_evidence as e
    if git("status", "--porcelain"): raise RuntimeError("dirty_tree")
    git("merge-base", "--is-ancestor", e.START, "HEAD")
    if git("rev-parse", "v0.1.0^{}") != e.TAG: raise RuntimeError("release_changed")
    if Path(sys.prefix).resolve() != (ROOT/".venv").resolve(): raise RuntimeError("locked_project_environment")
    protocol = (ROOT/PROTOCOL).read_text()
    bindings = json.loads(protocol.split("```json\n", 1)[1].split("\n```", 1)[0])
    for path, expected in bindings.items():
        if e.sha(ROOT/path) != expected: raise RuntimeError("historical_authority_changed:"+path)
    sources = git("ls-files", "scripts/*14r9j*", "src/**/r9j*", "tests/*14r9j*", PROTOCOL).splitlines()
    if len(sources) < 8: raise RuntimeError("incomplete_committed_implementation")
    for path in sources:
        if subprocess.check_output(("git", "show", "HEAD:"+path), cwd=ROOT) != (ROOT/path).read_bytes():
            raise RuntimeError("implementation_not_committed")
    return {"implementation": git("rev-parse", "HEAD"), "protocol_sha256": e.sha(ROOT/PROTOCOL),
            "lock_sha256": e.sha(ROOT/"uv.lock"), "python": sys.version.split()[0],
            "packages": {name: importlib.metadata.version(name) for name in ("numpy", "scipy", "defensive-network-disruption")},
            "source_hashes": {p: e.sha(ROOT/p) for p in sources}, "historical_hashes": bindings}


class Evidence:
    def __init__(self, local):
        self.local = local; self.serial = 0; self.io = 0.
    def save(self, label, value):
        from defensive_network_disruption.validation import r9j_evidence as e
        start = time.perf_counter()
        name = f"{self.serial:06d}_{label}.json"; self.serial += 1
        e.put(self.local/name, value); self.io += time.perf_counter()-start
        return name


def selected_edge(prepared, receipt):
    from defensive_network_disruption.validation.empirical_switch_diagnosis import project_prepared_edge
    if receipt is None or receipt["state"] != "4" or "7" not in receipt["edges"]:
        raise PermissionError("missing_selected_materialization")
    with prepared.open("rb") as f:
        for ordinal, raw in enumerate(f):
            if ordinal == 4:
                return project_prepared_edge(raw.decode(), 7)
    raise ValueError("selected_row_unavailable")


def numerical(local, evidence, public, rows, authority, qc):
    from fractions import Fraction as F
    from defensive_network_disruption.validation import r9j_evidence as e
    from defensive_network_disruption.geometry import r9j_diagnosis as d, r9j_reference as ref
    budget = d.Budget()
    e.put(local/"numerical.marker", {"schema_version": 1, "reserved": True, "authorizes_access": False})
    if e.sha(OLD/"prepared.jsonl") != PREPARED_HASH: raise RuntimeError("prepared_hash")
    if authority.selected_receipt is None: raise PermissionError("selected_receipt_unavailable")
    e.put(local/"access_attempt.json", {"state": 4, "edge": 7, "prepared_sha256": PREPARED_HASH})
    qc["exposure_uncertain"] = True
    row = selected_edge(OLD/"prepared.jsonl", authority.selected_receipt)
    e.put(local/"access_materialized.json", {"state": 4, "edge": 7, "selected_sha256": e.digest(row)})
    qc.update(states_reopened=1, edges_reopened=1, exposure_uncertain=False)
    evidence.save("selected_geometry", row)
    reproduced, observed, failure = d.reproduce("constant_width", row, ROOT, evidence.save, budget)
    controlled = observed.saved.get("controlled")
    warnings = sum(len(x["warnings"]) for x in observed.pieces)
    certified = sum(x["result"] is not None and x["result"].branch == "independent_certificate" for x in observed.pieces)
    e.record(public, "numerical_reproduction.json", flags={"reproduced": reproduced,
        "production_converged": controlled is not None and controlled[0] is not None,
        "gate_inputs_captured": bool(observed.gates), "warning_evidence_captured": True},
        counts={"accepted_resolution": None if controlled is None else controlled[0], "adaptive_calls": len(observed.quad),
                "warnings": warnings, "certified_pieces": certified})
    rows["candidate_path_comparison.csv"].append(dict(candidate="constant_width",status="failed" if failure else "passed",gate=failure or "accepted",
        converged=controlled is not None and controlled[0] is not None,accepted_resolution="" if controlled is None else controlled[0],reason="provisional_if_failed"))
    if not reproduced: return "NF", "exact_failure_not_reproduced", time.monotonic()-budget.started
    evidence.save('point_estimate_differences',d.pairwise_differences({
        'production':controlled[1]['maximum'],
        'piecewise':observed.saved['strict_piecewise'][1]['production_estimate'],
        'onset_only':observed.saved['onset_adaptive'][1]['production_estimate']}))
    with budget.limit(): audit = d.audit(observed, row)
    e.record(public, "partition_diagnosis.json", flags={"valid":audit["passed"],"onsets_present":audit["checks"]["onsets_present"],
        "switches_present":audit["checks"]["switches_present"],"ties_preserved":audit["checks"]["tie_endpoints_preserved"],
        "witnesses_valid":audit["checks"]["witnesses_valid"],"routing_valid":audit["routing_valid"]},
        counts={"pieces":audit["pieces"],"onsets":audit["onset_count"],"switches":audit["switch_count"],"ties":audit["tie_count"],"bounded_pieces":audit["bounded"]})
    if not audit["passed"]: return "NC", "partition_audit_failed", time.monotonic()-budget.started
    cuts = sorted({0., 1., *observed.saved["structure"][2], *(x.canonical for x in observed.saved["structure"][0])})
    with budget.limit():
        fields = ref.from_geometry(tuple(map(float,row["carrier"])), tuple(map(float,row["receiver"])),
                                   tuple(tuple(map(float,x)) for x in row["defenders"]))
        bound = ref.enclose(fields, [F.from_float(x) for x in cuts], deadline=min(budget.deadline,time.monotonic()+600))
    private = {k:d.primitive(v) for k,v in bound.items() if k not in ("bound","groups")}
    private.update(bound=d.primitive({"lower":bound["bound"].lo,"upper":bound["bound"].hi}),
                   groups=[d.primitive({"lower":x.lo,"upper":x.hi}) for x in bound["groups"]],cuts=cuts)
    evidence.save("independent_reference", private)
    e.record(public,"independent_reference.json", flags={"eligible":bound["eligible"],"scalar_oracle":audit["scalar_oracle"]},
             counts={"leaves":bound["leaves"],"smooth_leaves":bound["smooth_leaves"]},timings={"seconds":bound["seconds"]},reason=bound["reason"])
    decision="NF"
    if bound["eligible"]:
        strict=observed.saved["strict_piecewise"][0]; onset=observed.saved["onset_adaptive"][0]
        production=controlled[1]["maximum"]
        comparisons={"production":ref.compare((production,production),bound["bound"],1e-6),
                     "piecewise":ref.compare((strict.lower,strict.upper),bound["bound"],1e-10),
                     "onset":ref.compare((onset.lower,onset.upper),bound["bound"],1e-10)}
        evidence.save("reference_comparisons",d.primitive(comparisons))
        # Exact differences remain private, including interval-aware gate distances.
        evidence.save("pairwise_comparisons", {"production_piecewise":max(0.,strict.lower-production,production-strict.upper),
            "production_onset":max(0.,onset.lower-production,production-onset.upper),
            "piecewise_onset":max(0.,strict.lower-onset.upper,onset.lower-strict.upper),
            "production":production,"strict":d.primitive(strict),"onset":d.primitive(onset)})
        e.record(public,"independent_reference.json", flags={"production_accurate":comparisons["production"]["accurate"],
            "piecewise_accurate":comparisons["piecewise"]["accurate"],"piecewise_inaccurate":comparisons["piecewise"]["inaccurate"],"onset_accurate":comparisons["onset"]["accurate"],
            "onset_inaccurate":comparisons["onset"]["inaccurate"]})
        if comparisons["production"]["accurate"] and comparisons["piecewise"]["accurate"] and comparisons["onset"]["inaccurate"]: decision="NA"
        elif comparisons["production"]["accurate"] and comparisons["piecewise"]["inaccurate"] and comparisons["onset"]["accurate"]: decision="NB"
        for integral in observed.integrals:
            if integral["stage"] not in ("strict_piecewise","onset_adaptive"): continue
            for ordinal,(a,b,piece) in enumerate(zip(integral["partitions"],integral["partitions"][1:],integral["pieces"])):
                subset=[bound["groups"][i] for i in range(len(cuts)-1) if a<=cuts[i] and cuts[i+1]<=b]
                cell=ref.Bounds(sum((x.lo for x in subset),F(0)),sum((x.hi for x in subset),F(0)))
                comp=ref.compare((piece.lower,piece.upper),cell,1e-10)
                evidence.save("localized_interval",d.primitive({"stage":integral["stage"],"ordinal":ordinal,"a":a,"b":b,"piece":piece,"reference_lower":cell.lo,"reference_upper":cell.hi,"comparison":comp}))
                rows["interval_localization.csv"].append(dict(ordinal=ordinal,kind=integral["stage"],status="available",
                    accurate=comp["accurate"],inaccurate=comp["inaccurate"],reason="exact_values_private"))
    elif bound["reason"] == "deadline":
        return "NF","reference_deadline",time.monotonic()-budget.started
    for candidate in ("isotropic","expanding"):
        _,other,failed=d.reproduce(candidate,row,ROOT,evidence.save,budget)
        vector=other.saved.get("controlled")
        rows["candidate_path_comparison.csv"].append(dict(candidate=candidate,status="failed" if failed else "passed",gate=failed or "accepted",
            converged=vector is not None and vector[0] is not None,accepted_resolution="" if vector is None else vector[0],reason="no_independent_accuracy_claim"))
    return decision,"completed_diagnosis",time.monotonic()-budget.started


def governed(folder):
    from defensive_network_disruption.validation import r9j_evidence as e
    from defensive_network_disruption.validation import r9j_linear_publication as linear
    start=time.perf_counter();local=folder/"local";evidence=Evidence(local)
    public=e.empty_public();rows={n:[] for n in e.CSV_SCHEMAS};environment={}
    qc=dict(status="partial",execution_valid=True,numerical="NF",publication="PD",readiness=4,
            states_reopened=0,edges_reopened=0,exposure_uncertain=False)
    stage="preflight";publication_wall=numerical_wall=publication_io=numerical_io=0.
    try:
        environment=preflight();evidence.save("environment",environment)
        e.record(public,"authority.json",flags={"committed_authority":True,"environment":True})
        stage="publication_controls";pstart=time.perf_counter();pio=evidence.io
        equivalence=linear.acceptance(local/"synthetic_controls")
        evidence.save("equivalence",equivalence)
        e.record(public,"validator_equivalence.json",flags=equivalence["flags"],counts=equivalence["counts"])
        complexity=linear.complexity_probe()
        evidence.save("complexity",complexity)
        e.record(public,"publication_complexity.json",flags=complexity["flags"],counts=complexity["counts"])
        enabled=True
        for nominal in (1000,2000,4000,8000):
            result=linear.benchmark(nominal,old_enabled=enabled,seconds=60)
            evidence.save("benchmark",result)
            rows["replay_benchmarks.csv"].append(result)
            if result["old_status"]=="timeout":enabled=False
        stage="retained_journal"
        e.put(local/"retained_review.marker",{"schema_version":1,"single_pass":True})
        for name,expected in (("original_failure.json",FAILURE_HASH),("emergency_failure.json",EMERGENCY_HASH)):
            if e.sha(OLD/name)!=expected:raise RuntimeError("retained_failure_authority")
            evidence.save("retained_"+name.removesuffix('.json'),e.load(OLD/name))
        t=time.perf_counter();authority=linear.review(OLD/"journal.jsonl",expected_sha256=JOURNAL_HASH,select=("4","7"))
        elapsed=time.perf_counter()-t
        evidence.save("retained_review",authority.record())
        checks=linear.check_r9i(authority)
        if not all(checks.values()):raise RuntimeError("retained_authority_mismatch")
        c=authority.legacy["snapshot"]["snapshot"]["counters"]
        e.record(public,"retained_journal_review.json",flags={**checks,"historical_complete_snapshot_available":False},
            counts={"records":authority.records,"states_opened":authority.exposure["states_opened"],"edges_opened":c["edges_opened"],
                "states_completed":c["states_completed"],"edges_completed":c["edges_completed"],"field_started":c["field_evaluations_started"],
                "field_completed":c["field_evaluations_completed"],"unresolved_edges":c["unresolved_exposed_edges"]},timings={"seconds":elapsed})
        publication_wall=time.perf_counter()-pstart
        publication_io=evidence.io-pio
        qc.update(publication="PA",readiness=3)
        e.record(public,"authority.json",flags={"retained_inputs":True})
        stage="numerical"
        try:
            nstart=time.perf_counter();nio=evidence.io
            decision,reason,numerical_wall=numerical(local,evidence,public,rows,authority,qc)
            qc["numerical"]=decision
            if reason=="completed_diagnosis":qc["status"]="complete"
            evidence.save("numerical_closure",{"decision":decision,"reason":reason})
            numerical_wall=time.perf_counter()-nstart
            numerical_io=evidence.io-nio
        except BaseException as error:
            numerical_wall=time.perf_counter()-nstart
            numerical_io=evidence.io-nio
            e.emergency(local/"numerical_emergency.json",error,stage)
            from defensive_network_disruption.geometry.r9j_diagnosis import DiagnosticTimeout
            if not isinstance(error,DiagnosticTimeout):qc.update(status="invalid",execution_valid=False)
    except BaseException as error:
        e.emergency(local/"diagnostic_emergency.json",error,stage)
        qc.update(status="invalid",execution_valid=False)
    wall=time.perf_counter()-start
    e.record(public,"runtime_summary.json",flags={"exclusive_accounting":True,"no_overlapping_sum":True},
        timings={"governed_wall":wall,"numerical_wall":numerical_wall,"publication_wall":publication_wall,
                 "numerical_exclusive":max(0.,numerical_wall-numerical_io),"publication_exclusive":max(0.,publication_wall-publication_io),
                 "io":evidence.io,"unattributed":max(0.,wall-publication_wall-numerical_wall+publication_io+numerical_io-evidence.io)},
        reason="through_preclosure; exclusive means branch wall excluding measured evidence I/O; inclusive branch timers are not additive with I/O")
    stage="publication"
    return e.close(folder,public,rows,qc,environment)


def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument("command",choices=("preflight","diagnose","publication-check"))
    args=parser.parse_args(argv)
    if args.command=="diagnose":result=entry(OUT,governed)
    elif args.command=="preflight":result=preflight()
    else:
        from defensive_network_disruption.validation.r9j_evidence import publication_check
        result=publication_check(OUT)
    # No exact empirical values or exception messages are printed.
    print(json.dumps({"command":args.command,"status":"passed"},sort_keys=True))
    return result


if __name__=="__main__":main()
