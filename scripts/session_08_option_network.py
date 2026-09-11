#!/usr/bin/env python3
"""Session 8 one-shot, development-only option distribution analysis."""
from __future__ import annotations
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np
from defensive_network_disruption.networks.options import (
    OptionState, FrozenOptionModel, evaluate_options, compare_options, SUMMARY_KEYS)
from defensive_network_disruption.validation.construct_diagnostics import distribution
from defensive_network_disruption.visualization.option_svg import synthetic_options_svg

START = "54b56a9900b96a1be0e9e51087a978ffeef6d4f1"
POP_SHA = "cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d"
MODEL_SHA = "0383561e45bcd9f8d84eccc7e9733b2409536f61c39193fa87d08c36c6f6fd65"
DEV = ("1886347","1899585","1925299","1996435","2006229","2011166","2013725","2015213","2017461")
COUNTS = (885,801,952,877,861,629,764,734,724)
ALIASES = tuple(f"development_{i:02d}" for i in range(1,10))
POP = Path("outputs/receiver_ranking_m0_m1/local/population.jsonl")
MODEL = Path("outputs/reserved_evaluation/final_development_models.json")
PROTOCOL = Path("docs/protocols/phase_08_attacking_option_network.md")
OUT = Path("outputs/attacking_option_network")
IMPL = ("scripts/session_08_option_network.py",
        "src/defensive_network_disruption/networks/options.py",
        "src/defensive_network_disruption/data/option_adapter.py",
        "src/defensive_network_disruption/visualization/option_svg.py",
        "tests/test_session8_options.py")
INHERITED = ("src/defensive_network_disruption/validation/ranking_features.py",
             "src/defensive_network_disruption/validation/construct_diagnostics.py",
             "src/defensive_network_disruption/validation/ranking_metrics.py",
             "src/defensive_network_disruption/geometry/segment.py")
CHANGE_KEYS = (*SUMMARY_KEYS, "top_set_changed", "strict_reversal", "tie_created", "tie_removed", "ordering_changed")
RESULTS = ("network_summary.json", "m0_m1_network_comparison.csv", "qc.json")
CANONICAL = {"match_id","event_id","candidate_ids","candidate_xy","defender_xy","carrier_xy","target_index","target_outside"}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT).decode().strip()


def safe(path):
    path = ROOT / path
    if any(p.is_symlink() for p in (path,*path.parents)) or not path.resolve().is_relative_to(ROOT.resolve()):
        raise PermissionError("unsafe path")
    return path


def digest(path):
    h = hashlib.sha256()
    with safe(path).open("rb") as f:
        for block in iter(lambda: f.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()


def load(path):
    return json.loads(safe(path).read_text(), parse_constant=lambda x: (_ for _ in ()).throw(ValueError("nonfinite JSON")))


def text_json(value):
    return json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"


def atomic(path, text):
    if not Path(path).is_relative_to(OUT):
        raise PermissionError("output namespace required")
    dest = safe(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    temp = safe(Path(path).with_name("." + Path(path).name + ".tmp"))
    with temp.open("x") as f:
        f.write(text)
    temp.replace(dest)


def ledger(stage, status):
    p = safe(OUT / "local/access.jsonl")
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a") as f:
        f.write(json.dumps({"stage":stage,"status":status,"time":datetime.now(timezone.utc).isoformat(),
                            "protocol_sha256":digest(PROTOCOL),"implementation":git("rev-parse","HEAD")})+"\n")


def marker():
    p = safe(OUT / "local/analyze.marker")
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("x") as f:
        f.write(git("rev-parse","HEAD")+"\n")


def committed(path):
    data = subprocess.check_output(["git","show","HEAD:"+str(path)], cwd=ROOT)
    if hashlib.sha256(data).hexdigest() != digest(path):
        raise ValueError("uncommitted authority")


def environment():
    from importlib.metadata import version
    return {"python":platform.python_version(),"platform":platform.platform(),
            "numpy":np.__version__,"scipy":version("scipy"),"uv_lock_sha256":digest("uv.lock")}


def historical():
    git("merge-base","--is-ancestor",START,"HEAD")
    old = set(git("ls-tree","-r","--name-only",START).splitlines())
    changed = set(git("diff","--name-only",START).splitlines())
    for name in old & changed:
        if name not in ("docs/research_log.md","references/library_review.md"):
            raise ValueError("historical tracked artifact changed")
        original = subprocess.check_output(["git","show",START+":"+name],cwd=ROOT)
        if not safe(name).read_bytes().startswith(original):
            raise ValueError("append-only history violated")


def authorities(require_clean=False):
    historical()
    if require_clean and git("status","--porcelain"):
        raise ValueError("clean implementation commit required")
    for p in (PROTOCOL, OUT/"software_contract.json", OUT/"implementation_authority.json"):
        committed(p)
    a = load(OUT/"implementation_authority.json")
    if set(a) != {"schema_version","protocol_sha256","contract_sha256","implementation_sha256","inherited_sha256","environment","starting_commit"}:
        raise ValueError("implementation authority schema")
    if a["starting_commit"] != START or a["protocol_sha256"] != digest(PROTOCOL) or a["contract_sha256"] != digest(OUT/"software_contract.json"):
        raise ValueError("protocol binding mismatch")
    for key, names in (("implementation_sha256",IMPL),("inherited_sha256",INHERITED)):
        if set(a[key]) != set(names):
            raise ValueError("implementation list mismatch")
        for p in names:
            committed(p)
            if a[key][p] != digest(p):
                raise ValueError("implementation hash mismatch")
    if digest(MODEL) != MODEL_SHA or environment() != a["environment"]:
        raise ValueError("model/environment mismatch")
    raw = load(MODEL)
    if raw["environment"] != a["environment"]:
        raise ValueError("historical environment mismatch")
    models = {name:FrozenOptionModel.from_mapping(name,raw["models"][name]) for name in ("m0","m1")}
    if models["m0"].mean != models["m1"].mean[:3] or models["m0"].scale != models["m1"].scale[:3]:
        raise ValueError("frozen preprocessing nesting mismatch")
    return models


def preflight():
    authorities()
    safe(POP)
    if not safe(POP).is_file():
        raise ValueError("canonical population missing")
    if not git("check-ignore","--",str(OUT/"local/probe")):
        raise ValueError("local storage must be ignored")
    print("Session 8 preflight passed; no population parsed")


def projected_row(raw):
    """Targets never enter the returned analytical object."""
    if set(raw) != CANONICAL or raw["match_id"] not in DEV:
        raise PermissionError("population schema or membership violation")
    if not isinstance(raw["event_id"],str) or not raw["event_id"] or raw["event_id"].strip()!=raw["event_id"]:
        raise ValueError("invalid event identity")
    state=OptionState(raw["carrier_xy"],raw["candidate_ids"],raw["candidate_xy"],raw["defender_xy"])
    return ALIASES[DEV.index(raw["match_id"])], raw["event_id"], state


def population():
    ledger("population_hash","started")
    if digest(POP) != POP_SHA:
        raise ValueError("population hash mismatch")
    ledger("population_hash","passed")
    counts=Counter();seen=set();rows=[]
    ledger("population_projection","started")
    with safe(POP).open() as f:
        for line in f:
            alias, event, state = projected_row(json.loads(line))
            if (alias,event) in seen:
                raise ValueError("duplicate event")
            seen.add((alias,event));counts[alias]+=1
            rows.append((alias,state))
    if tuple(counts[a] for a in ALIASES) != COUNTS or len(rows)!=7227:
        raise ValueError("population counts mismatch")
    ledger("population_projection","passed")
    return rows


def pearson(x,y):
    x=np.asarray(x,dtype=float);y=np.asarray(y,dtype=float)
    x=x-x.mean();y=y-y.mean()
    if not np.any(x) or not np.any(y):
        return None
    r=float(np.dot(x,y)/math.sqrt(float(np.dot(x,x))*float(np.dot(y,y))))
    return max(-1.0,min(1.0,r))


def summarize_rows(rows, models):
    """Label-free kernel used in synthetic rehearsal and the single live run."""
    detail=[]
    for alias,state in rows:
        left=evaluate_options(state,model=models["m0"])
        right=evaluate_options(state,model=models["m1"])
        detail.append((alias,dict(left.summary),dict(right.summary),compare_options(left,right)))
    aliases=sorted({r[0] for r in detail})
    counts=Counter(r[0] for r in detail)
    def group_stats(group):
        selected=detail if group=="match_macro" else [r for r in detail if r[0]==group]
        out={}
        for i,name,keys in ((1,"m0",SUMMARY_KEYS),(2,"m1",SUMMARY_KEYS),(3,"change",CHANGE_KEYS)):
            out[name]={}
            for key in keys:
                valid=[r for r in selected if r[i][key] is not None]
                represented={r[0] for r in valid}
                valid_counts=Counter(r[0] for r in valid)
                weights=[1/len(represented)/valid_counts[r[0]] for r in valid]
                out[name][key]=distribution([r[i][key] for r in valid],weights)
        return {"states":len(selected),"models":out}
    groups={a:group_stats(a) for a in (*aliases,"match_macro")}
    correlations={}
    for alias in aliases:
        selected=[r for r in detail if r[0]==alias]
        correlations[alias]={name:{k:pearson([r[i]["effective_option_count"] for r in selected],
                                            [r[i][k] for r in selected])
                                  for k in ("top_one_share","top_two_share","utility_range")}
                             for i,name in ((1,"m0"),(2,"m1"))}
    return {"schema_version":"1","scope":"label_free_in_sample_development_description",
            "states":len(detail),"counts":dict(sorted(counts.items())),
            "groups":groups,"correlations":correlations}


def csv_text(summary):
    rows=[]
    for a in (*sorted(summary["counts"]),"match_macro"):
        g=summary["groups"][a];row={"match_alias":a,"states":g["states"]}
        for name in ("m0","m1","change"):
            keys=SUMMARY_KEYS if name!="change" else CHANGE_KEYS
            for k in keys:
                row[name+"_"+k]=g["models"][name][k]["mean"]
        rows.append(row)
    f=io.StringIO(newline="")
    writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n")
    writer.writeheader();writer.writerows(rows)
    return f.getvalue()


def check_distribution(d):
    if set(d)!={"count","mean","minimum","maximum","quantiles"}:
        raise ValueError("distribution schema")
    if d["count"]==0:
        if any(d[k] is not None for k in ("mean","minimum","maximum","quantiles")):
            raise ValueError("empty distribution semantics")
    elif not isinstance(d["count"],int) or d["count"]<0 or set(d["quantiles"])!={"q05","q25","q50","q75","q95"}:
        raise ValueError("distribution count/quantiles")
    else:
        tolerance=64*np.finfo(float).eps*max(1,abs(d["minimum"]),abs(d["maximum"]))
        if not d["minimum"]-tolerance<=d["mean"]<=d["maximum"]+tolerance:
            raise ValueError("distribution range")
        qs=list(d["quantiles"].values())
        if qs!=sorted(qs) or qs[0]<d["minimum"] or qs[-1]>d["maximum"]:
            raise ValueError("quantile order")


def validate_summary(s, expected_counts):
    if set(s)!={"schema_version","scope","states","counts","groups","correlations"} or s["schema_version"]!="1":
        raise ValueError("summary schema")
    if s["scope"]!="label_free_in_sample_development_description" or s["counts"]!=expected_counts or s["states"]!=sum(expected_counts.values()):
        raise ValueError("summary population")
    if set(s["groups"])!=set(expected_counts)|{"match_macro"} or set(s["correlations"])!=set(expected_counts):
        raise ValueError("summary aliases")
    for a,g in s["groups"].items():
        if set(g)!={"states","models"} or g["states"]!=(s["states"] if a=="match_macro" else expected_counts[a]) or set(g["models"])!={"m0","m1","change"}:
            raise ValueError("group schema")
        for name,v in g["models"].items():
            if set(v)!=set(SUMMARY_KEYS if name!="change" else CHANGE_KEYS):
                raise ValueError("metric schema")
            for d in v.values():
                check_distribution(d)
                if d["count"]>g["states"]:
                    raise ValueError("denominator mismatch")
    for c in s["correlations"].values():
        if set(c)!={"m0","m1"}:
            raise ValueError("correlation models")
        for v in c.values():
            if set(v)!={"top_one_share","top_two_share","utility_range"} or any(x is not None and not -1<=x<=1 for x in v.values()):
                raise ValueError("correlation schema")
    text_json(s)  # reject nonfinite anywhere


def bind_manifest(status, files):
    manifest={"schema_version":"1","status":status,"starting_commit":START,
              "implementation_commit":git("log","-1","--format=%H","--",str(OUT/"implementation_authority.json")),
              "protocol_sha256":digest(PROTOCOL),"model_sha256":MODEL_SHA,"population_sha256":POP_SHA,
              "implementation_authority_sha256":digest(OUT/"implementation_authority.json"),
              "output_sha256":{p:digest(OUT/p) for p in files}}
    atomic(OUT/"manifest.json",text_json(manifest))


def analyze():
    models=authorities(require_clean=True)
    for name in (*RESULTS,"manifest.json"):
        if safe(OUT/name).exists():
            raise ValueError("existing results; no rerun")
    marker()
    try:
        ledger("analyze","started")
        result=summarize_rows(population(),models)
        validate_summary(result,dict(zip(ALIASES,COUNTS)))
        atomic(OUT/"network_summary.json",text_json(result))
        atomic(OUT/"m0_m1_network_comparison.csv",csv_text(result))
        qc={"schema_version":"1","status":"validated","states":sum(COUNTS),"matches":len(ALIASES),
            "models":["m0","m1"],"fitting":False,"target_analysis":False,
            "reserved_detail_access":False,"withheld_access":False,"pose_access":False,
            "population_sha256":POP_SHA,"model_sha256":MODEL_SHA}
        atomic(OUT/"qc.json",text_json(qc))
        validate_results()
        bind_manifest("aggregates_closed",RESULTS)
        atomic(OUT/"local/aggregate_closure.json",text_json({"manifest_sha256":digest(OUT/"manifest.json")}))
        ledger("analyze","closed")
        print("Session 8 aggregates closed; no per-state results displayed")
    except Exception as error:
        atomic(OUT/"local/failure.json",text_json({"stage":"analyze","category":type(error).__name__}))
        ledger("analyze","failed")
        raise RuntimeError("Session 8 stopped; preserved failure") from None


def validate_results():
    s=load(OUT/"network_summary.json")
    validate_summary(s,dict(zip(ALIASES,COUNTS)))
    if safe(OUT/"m0_m1_network_comparison.csv").read_bytes()!=csv_text(s).encode():
        raise ValueError("CSV cross-file mismatch")
    q=load(OUT/"qc.json")
    expected={"schema_version":"1","status":"validated","states":sum(COUNTS),"matches":len(ALIASES),
              "models":["m0","m1"],"fitting":False,"target_analysis":False,
              "reserved_detail_access":False,"withheld_access":False,"pose_access":False,
              "population_sha256":POP_SHA,"model_sha256":MODEL_SHA}
    if q!=expected:
        raise ValueError("QC schema/values")


def publication_check():
    authorities()
    if safe(OUT/"local/failure.json").exists():
        raise RuntimeError("preserved failed execution")
    validate_results()
    m=load(OUT/"manifest.json")
    keys={"schema_version","status","starting_commit","implementation_commit","protocol_sha256",
          "model_sha256","population_sha256","implementation_authority_sha256","output_sha256"}
    if set(m)!=keys or m["schema_version"]!="1" or m["status"] not in ("aggregates_closed","closed"):
        raise ValueError("manifest schema")
    expected=set(RESULTS)|({"synthetic_options.svg"} if m["status"]=="closed" else set())
    if set(m["output_sha256"])!=expected:
        raise ValueError("manifest file schema")
    for name,h in m["output_sha256"].items():
        if digest(OUT/name)!=h:
            raise ValueError("result hash mismatch")
    if (m["protocol_sha256"],m["model_sha256"],m["population_sha256"],m["implementation_authority_sha256"],m["starting_commit"])!=(digest(PROTOCOL),MODEL_SHA,POP_SHA,digest(OUT/"implementation_authority.json"),START):
        raise ValueError("manifest binding")
    print("Session 8 publication schemas, hashes and authority passed")


def render_synthetic():
    publication_check()
    if safe(OUT/"synthetic_options.svg").exists():
        raise ValueError("synthetic illustration already rendered")
    models=authorities()
    svg=synthetic_options_svg(models)
    atomic(OUT/"synthetic_options.svg",svg)
    bind_manifest("closed",(*RESULTS,"synthetic_options.svg"))
    publication_check()
    print("Synthetic illustration rendered; no empirical geometry loaded")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=("preflight","analyze","render-synthetic","publication-check"))
    args=parser.parse_args()
    {"preflight":preflight,"analyze":analyze,"render-synthetic":render_synthetic,
     "publication-check":publication_check}[args.command]()
