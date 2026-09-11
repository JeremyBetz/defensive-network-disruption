#!/usr/bin/env python3
"""Synthetic Session 14z artifact transport and cross-platform comparison."""
from __future__ import annotations

import argparse, csv, hashlib, importlib.util, io, json, math, platform, shutil, subprocess, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from defensive_network_disruption.geometry.diagnostic_artifact_transport import (
    ARTIFACT_FILENAME, ARTIFACT_NAME, diagnostic_bytes, read_verified_diagnostic,
    sha256_bytes, write_diagnostic,
)
from defensive_network_disruption.geometry.vector_reproducibility import component_record

START = "938683d6f13e5299128ce30aa1d05e6bdddc6c96"
TAG = "f00690c05d8c1c6db308a65bd311c43f9a8ef2fa"
PROTOCOL = Path("docs/protocols/phase_14z_ci_artifact_transport_and_reproducibility.md")
HISTORICAL = Path("outputs/continuous_occlusion_production_acceptance/reference_comparison.csv")
SESSION14Y_LOCAL = Path("outputs/cross_platform_vector_reproducibility_14y/local_diagnostic.json")
OUT = Path("outputs/cross_platform_vector_reproducibility_14z")
LOCAL_PRIVATE = OUT / "local"
WORKFLOW = Path(".github/workflows/session14z-diagnostic.yml")
CODE = (Path("scripts/session_14z_ci_artifact_transport_and_reproducibility.py"),
        Path("src/defensive_network_disruption/geometry/diagnostic_artifact_transport.py"),
        Path("tests/test_session14z_artifact_transport.py"), WORKFLOW)

def safe(path):
    path=Path(path)
    if path.is_absolute() or ".." in path.parts: raise ValueError("unsafe_path")
    result=ROOT/path
    if any(x.is_symlink() for x in (result,*result.parents)): raise ValueError("symlink_rejected")
    return result
def digest(path): return hashlib.sha256(safe(path).read_bytes()).hexdigest()
def git(*args): return subprocess.check_output(["git",*args],cwd=ROOT,text=True).strip()
def committed(path):
    if safe(path).read_bytes()!=subprocess.check_output(["git","show",f"HEAD:{path}"],cwd=ROOT): raise ValueError("uncommitted_authority")
def encoded(value): return (json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n").encode()
def write_once(path,data):
    target=safe(path); target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists(): raise FileExistsError("output_exists")
    temp=target.with_name("."+target.name+".tmp"); temp.write_bytes(data); temp.replace(target)
def load_14y():
    path=safe("scripts/session_14y_switch_projection_repair_and_reproducibility.py")
    spec=importlib.util.spec_from_file_location("session14y_frozen",path); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

def validate_record(record):
    if record.get("schema_version")!=1 or record.get("authority",{}).get("vector_count")!=108 or record["authority"].get("component_count")!=366: raise ValueError("diagnostic_schema")
    if len(record.get("records",[]))!=108 or sum(len(x.get("comparison",[])) for x in record["records"])!=366: raise ValueError("diagnostic_shape")
    if any(tuple(x["ladder"][i]["intervals"] for i in range(len(x["ladder"])))!=(256,512,1024,2048,4096,8192,16384) for x in record["records"]): raise ValueError("ladder_shape")

def preflight():
    if git("status","--porcelain"): raise ValueError("clean_tree_required")
    if git("rev-parse","v0.1.0^{}")!=TAG: raise ValueError("release_tag_changed")
    for path in (PROTOCOL,*CODE): committed(path)
    print("Session 14z preflight passed; synthetic evidence only")

def compute_record():
    record=load_14y().diagnostic(); validate_record(record); return record

def local_diagnostic():
    preflight(); record=compute_record(); raw=diagnostic_bytes(record)
    historical=safe(SESSION14Y_LOCAL).read_bytes()
    if raw!=historical: raise ValueError("session14y_local_authority_changed")
    counts=Counter(x["accepted"]["intervals"] for x in record["records"])
    if counts!={512:55,1024:13,2048:30,4096:8,8192:2}: raise ValueError("accepted_resolution_authority")
    write_once(LOCAL_PRIVATE/"local_diagnostic.json",raw)
    print(json.dumps({"schema_version":1,"bytes":len(raw),"sha256":sha256_bytes(raw),"vectors":108,"components":366,"accepted_resolutions":dict(sorted(counts.items()))},sort_keys=True))

def ci_diagnostic(output):
    preflight(); target=Path(output)
    if target.is_absolute() or target.name!=ARTIFACT_FILENAME: raise ValueError("ci_output_path")
    size,sha=write_diagnostic(ROOT/target,compute_record())
    print(f"SESSION14Z_DIAGNOSTIC schema=1 bytes={size} sha256={sha} artifact={ARTIFACT_NAME} file={ARTIFACT_FILENAME}")

def csv_bytes(rows,fields):
    stream=io.StringIO(newline=""); writer=csv.DictWriter(stream,fieldnames=fields,lineterminator="\n"); writer.writeheader(); writer.writerows(rows); return stream.getvalue().encode()

def compare(ci_file,declared_sha,run_id):
    preflight(); local_raw=safe(LOCAL_PRIVATE/"local_diagnostic.json").read_bytes(); local=json.loads(local_raw); validate_record(local)
    ci,ci_raw=read_verified_diagnostic(Path(ci_file),declared_sha); validate_record(ci)
    local_by={(x["fixture"],x["candidate"]):x for x in local["records"]}; ci_by={(x["fixture"],x["candidate"]):x for x in ci["records"]}
    if tuple(local_by)!=tuple(ci_by): raise ValueError("vector_order_changed")
    vector_rows=[]; resolution_rows=[]; differing=[]; signed_zero_differences=0
    routes_equal=True; resolutions_equal=True
    for key,item in local_by.items():
        other=ci_by[key]
        if item["routing"]!=other["routing"]: routes_equal=False
        if item["accepted"]["intervals"]!=other["accepted"]["intervals"]: resolutions_equal=False
        if tuple(x["component"] for x in item["comparison"])!=tuple(x["component"] for x in other["comparison"]): raise ValueError("component_order_changed")
        for historical,lrow,crow in zip(item["comparison"],item["comparison"],other["comparison"],strict=True):
            row=component_record(lrow["component"],lrow["actual"],crow["actual"])
            row={"fixture":key[0],"candidate":key[1],"historical":historical["expected"],"local":row.pop("expected"),"ci":row.pop("actual"),**{k:v for k,v in row.items() if k!="component"}}
            vector_rows.append(row)
            if not row["bitwise_equal"]: differing.append(row)
            if row["expected_signed_zero"]!=row["actual_signed_zero"]: signed_zero_differences+=1
        for left,right in zip(item["ladder"],other["ladder"],strict=True):
            if left["intervals"]!=right["intervals"] or tuple(left["values"])!=tuple(right["values"]): raise ValueError("ladder_order_changed")
            comps=[component_record(k,left["values"][k],right["values"][k]) for k in left["values"]]
            resolution_rows.append({"fixture":key[0],"candidate":key[1],"intervals":left["intervals"],"differing_components":sum(not x["bitwise_equal"] for x in comps),"maximum_absolute_difference":max(x["absolute_difference"] for x in comps),"accepted_local":left["intervals"]==item["accepted"]["intervals"],"accepted_ci":right["intervals"]==other["accepted"]["intervals"]})
    numeric_ok=all(row["absolute_difference"]<=1e-6 for row in vector_rows)
    algorithmic=routes_equal and resolutions_equal
    if not algorithmic: classification="E"
    elif not numeric_ok: classification="F"
    elif differing: classification="C"
    else: classification="A"
    readiness=1 if classification in ("A","B","C") else 3
    first=next((r["intervals"] for r in resolution_rows if r["differing_components"]),None)
    max_rel=max((r["relative_difference"] for r in vector_rows if r["relative_difference"] is not None),default=0.0)
    review={"classification":classification,"readiness":readiness,"algorithmically_reproducible":algorithmic,"bitwise_reproducible":not differing,"numerically_reproducible_within_existing_authority":numeric_ok,"historical_exact_equality_overstrict":classification=="C","differing_components":len(differing),"maximum_absolute_difference":max((r["absolute_difference"] for r in vector_rows),default=0.0),"maximum_relative_difference":max_rel,"maximum_ulp_distance":max((r["ulp_distance"] for r in vector_rows if r["ulp_distance"] is not None),default=0),"signed_zero_differences":signed_zero_differences,"first_divergent_resolution":first,"replacement_tolerance_selected":False}
    vector_fields=("fixture","candidate","historical","local","ci","expected_bits","actual_bits","expected_signed_zero","actual_signed_zero","absolute_difference","relative_difference","ulp_distance","finite","python_equal","bitwise_equal")
    resolution_fields=("fixture","candidate","intervals","differing_components","maximum_absolute_difference","accepted_local","accepted_ci")
    write_once(OUT/"transport_contract.json",encoded({"schema_version":1,"artifact_name":ARTIFACT_NAME,"filename":ARTIFACT_FILENAME,"transport":"github-actions-artifact","stdout_payload":False,"ci_run_id":str(run_id),"declared_sha256":declared_sha,"downloaded_sha256":sha256_bytes(ci_raw),"hash_verified":True}))
    write_once(OUT/"local_diagnostic.json",local_raw); write_once(OUT/"ci_diagnostic.json",ci_raw)
    write_once(OUT/"environment_comparison.json",encoded({"local":local["environment"],"ci":ci["environment"],"same_numpy":local["environment"]["numpy"]==ci["environment"]["numpy"],"same_scipy":local["environment"]["scipy"]==ci["environment"]["scipy"]}))
    write_once(OUT/"vector_comparison.csv",csv_bytes(vector_rows,vector_fields)); write_once(OUT/"resolution_comparison.csv",csv_bytes(resolution_rows,resolution_fields))
    write_once(OUT/"routing_comparison.json",encoded({"all_108_equal":routes_equal,"accepted_resolutions_equal":resolutions_equal,"local_counts":dict(sorted(Counter(x["accepted"]["intervals"] for x in local["records"]).items())),"ci_counts":dict(sorted(Counter(x["accepted"]["intervals"] for x in ci["records"]).items()))}))
    write_once(OUT/"equality_contract_review.json",encoded(review))
    write_once(OUT/"qc.json",encoded({"schema_version":1,"status":"closed","classification":classification,"readiness":readiness,"vector_count":108,"component_count":366,"empirical_access":False,"session14r_partial_outputs_accessed":False,"governed_ci_dispatches":1,"artifact_retrievals":1}))
    names=("transport_contract.json","local_diagnostic.json","ci_diagnostic.json","environment_comparison.json","vector_comparison.csv","resolution_comparison.csv","routing_comparison.json","equality_contract_review.json","qc.json")
    manifest={"schema_version":1,"status":"closed","start":START,"protocol_sha256":digest(PROTOCOL),"historical_sha256":digest(HISTORICAL),"session14y_local_sha256":digest(SESSION14Y_LOCAL),"ci_run_id":str(run_id),"artifact_name":ARTIFACT_NAME,"declared_ci_sha256":declared_sha,"downloaded_artifact_sha256":sha256_bytes(ci_raw),"implementation":{str(x):digest(x) for x in CODE},"outputs":{x:digest(OUT/x) for x in names}}
    write_once(OUT/"manifest.json",encoded(manifest)); print(json.dumps(review,sort_keys=True))

def publication_check():
    manifest=json.loads(safe(OUT/"manifest.json").read_text())
    for name,sha in manifest["outputs"].items():
        if digest(OUT/name)!=sha: raise ValueError("output_hash_changed")
    for name in (*manifest["outputs"],"manifest.json"):
        text=safe(OUT/name).read_text()
        if any(x in text for x in ("/Users/","/home/runner/","event_id","target_id","X-Amz-Signature")): raise ValueError("publication_boundary")
    print("Session 14z publication checks passed")

def main():
    p=argparse.ArgumentParser(); p.add_argument("command",choices=("preflight","local-diagnostic","ci-diagnostic","compare","publication-check")); p.add_argument("--output",default=ARTIFACT_FILENAME); p.add_argument("--ci-file"); p.add_argument("--declared-sha256"); p.add_argument("--run-id")
    a=p.parse_args()
    if a.command=="preflight": preflight()
    elif a.command=="local-diagnostic": local_diagnostic()
    elif a.command=="ci-diagnostic": ci_diagnostic(a.output)
    elif a.command=="compare":
        if not all((a.ci_file,a.declared_sha256,a.run_id)): raise ValueError("comparison_arguments_required")
        compare(a.ci_file,a.declared_sha256,a.run_id)
    else: publication_check()
if __name__=="__main__": main()
