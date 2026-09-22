"""Metadata-only R9Z pair-authority and failure-evidence diagnosis."""
from __future__ import annotations

from fractions import Fraction as F
import hashlib, json, traceback
from pathlib import Path

NAMES=("diagnosis_contract.json","pair_semantics.json","schema_implementation_trace.json",
       "synthetic_pair_controls.csv","failure_capture_trace.json","negative_controls.csv",
       "qc.json","manifest.json")
ALLOWED_PRIVATE={"original_failure.json","lineage_receipt.json","materialization_receipt.json",
                 "checkpoint_ci.json","checkpoint_ci.json.sha256","checkpoint_ci_v2.json",
                 "checkpoint_ci_v2.json.sha256","review.marker","access.marker",
                 "authority.marker","closure.marker","private_index.json"}

def canonical(value): return (json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n").encode()
def digest(value): return hashlib.sha256(value if isinstance(value,bytes) else canonical(value)).hexdigest()
def sha(path): return digest(Path(path).read_bytes())
def coefficient(q,dot,cross2):
    payload={"q":str(F(q)),"dot":str(F(dot)),"cross2":str(F(cross2))}
    return {**payload,"authority_sha256":digest(payload)}
def relation(first,second,*,first_inactive=False,second_inactive=False,tolerance_only=False):
    if first["authority_sha256"]==second["authority_sha256"]: return "symbolic_identity"
    if first_inactive and second_inactive: return "common_inactive_branch"
    if tolerance_only: return "unresolved_tolerance_only"
    return "unresolved_distinct"
def pair_record(first,second,kind):
    return {"pair":[first["authority_sha256"],second["authority_sha256"]],"relation":kind,
            "ordered":True,"retains_both":first["authority_sha256"]!=second["authority_sha256"]}

def synthetic_controls():
    a=coefficient(1,2,3); b=coefficient(1,5,7)
    cases=(("exact_duplicate",a,a,{},"symbolic_identity"),
           ("common_inactive_branch",a,b,{"first_inactive":True,"second_inactive":True},"common_inactive_branch"),
           ("distinct_unresolved",a,b,{},"unresolved_distinct"),
           ("tolerance_only",a,b,{"tolerance_only":True},"unresolved_tolerance_only"))
    rows=[]
    for name,x,y,options,expected in cases:
        observed=relation(x,y,**options); record=pair_record(x,y,observed)
        rows.append({"control":name,"expected":expected,"observed":observed,
                     "ordered":record["ordered"],"retains_both":record["retains_both"],
                     "passed":observed==expected})
    collapsed=pair_record(a,a,"symbolic_identity")
    rows.append({"control":"collapse_loses_distinct_authority","expected":"loss_detected",
                 "observed":"loss_detected" if len(set(collapsed["pair"]))==1 else "not_detected",
                 "ordered":True,"retains_both":False,"passed":len(set(collapsed["pair"]))==1})
    return rows

def synthetic_failure(stage):
    try: raise RuntimeError("synthetic_"+stage)
    except RuntimeError as error:
        trace="".join(traceback.format_exception(type(error),error,error.__traceback__))
        return {"stage":stage,"exception_type":type(error).__name__,"message":str(error),
                "traceback_sha256":digest(trace.encode()),"captured_before_closure":True}

def inspect(root: Path, r9y_local: Path):
    root=Path(root); local=Path(r9y_local)
    index=json.loads((local/"private_index.json").read_bytes())
    records={}
    for name in ("original_failure.json","lineage_receipt.json","materialization_receipt.json"):
        if name not in index["files"] or sha(local/name)!=index["files"][name]: raise ValueError("private_hash")
        records[name]=json.loads((local/name).read_bytes())
    failure=records["original_failure.json"]
    if failure!={"stage":"authority_construction","exception_type":"ValueError","message":"pair_authority","traceback_status":"unavailable_due_runner_capture_defect"}: raise ValueError("failure_authority")
    minimum=json.loads((root/"outputs/continuous_occlusion_terminal_cell_evidence_retention/minimum_schema.json").read_bytes())
    create=(root/"src/defensive_network_disruption/geometry/r9x_terminal_authority.py").read_text()
    r9v=(root/"src/defensive_network_disruption/geometry/r9v_tie_diagnosis.py").read_text()
    runner=(root/"scripts/session_14r9y_terminal_cell_authority_acquisition.py").read_text()
    pair_established=("pair_coefficient_references" in minimum["required"] and
        'pair[0].authority_sha256 != pair[1].authority_sha256' in create and
        'raise ValueError("terminal_pair_authority")' in create and
        "pair_authority.equal_on(a, b)" in r9v)
    failure_established=("except Exception:" in runner and "raise" in runner and
                         'qc={"status":"blocked"' in runner and
                         "FailureController" not in runner and "traceback" not in runner)
    return {"pair_established":pair_established,"failure_established":failure_established,
            "traceback_available":False,"retained_hashes_differ":True,
            "blocked_qc_constructed_before_reraise":'qc={"status":"blocked"' in runner,
            "materialization_valid":bool(records["materialization_receipt.json"]),
            "lineage_valid":bool(records["lineage_receipt.json"])}

def csv_bytes(rows):
    keys=list(rows[0]); lines=[",".join(keys)]
    for row in rows:
        lines.append(",".join(str(row[k]).lower() if isinstance(row[k],bool) else str(row[k]) for k in keys))
    return ("\n".join(lines)+"\n").encode()

def close(folder, records, pair_rows, negative_rows, qc):
    from .r9j_evidence import put
    folder=Path(folder); local=folder/"local"
    private={p.relative_to(local).as_posix():sha(p) for p in sorted(local.rglob("*")) if p.is_file() and p.name!="private_index.json"}
    put(local/"private_index.json",{"schema_version":1,"files":private}); idx=sha(local/"private_index.json")
    for name,value in records.items(): put(folder/name,{**value,"evidence_sha256":idx})
    for name,rows in (("synthetic_pair_controls.csv",pair_rows),("negative_controls.csv",negative_rows)):
        path=folder/name
        if path.exists(): raise FileExistsError("immutable_record_exists")
        path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(csv_bytes(rows))
    put(folder/"qc.json",{**qc,"schema_version":1,"private_index_sha256":idx})
    put(folder/"manifest.json",{"schema_version":1,"private_index_sha256":idx,
        "outputs":{name:sha(folder/name) for name in NAMES if name!="manifest.json"}})
    return publication_check(folder)

def publication_check(folder):
    folder=Path(folder)
    if {p.name for p in folder.iterdir() if p.is_file()}!=set(NAMES): raise ValueError("inventory")
    m=json.loads((folder/"manifest.json").read_bytes())
    if set(m["outputs"])!=set(NAMES)-{"manifest.json"}: raise ValueError("outputs")
    if any(sha(folder/name)!=value for name,value in m["outputs"].items()): raise ValueError("public_hash")
    q=json.loads((folder/"qc.json").read_bytes())
    if q["states_reopened"] or q["edges_reopened"] or q["empirical_computations"]: raise ValueError("access")
    if q["classification"]=="A" and not (q["execution_valid"] and q["readiness"]==1 and q["pair_defect_established"] and q["traceback_defect_established"]): raise ValueError("false_acceptance")
    prohibited=("/Users/","selected_edge","boundary_capture","coordinates","carrier","receiver","defenders","numerator","denominator")
    for name in NAMES:
        text=(folder/name).read_text()
        if any(token in text for token in prohibited): raise ValueError("privacy")
    return {"valid":True,"files":8,"classification":q["classification"],"readiness":q["readiness"]}
