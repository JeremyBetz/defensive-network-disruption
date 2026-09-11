#!/usr/bin/env python3
"""Synthetic-only cross-platform historical-vector diagnostic."""
from __future__ import annotations

import argparse, ast, base64, csv, hashlib, io, json, math, os, platform, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np
import scipy

from defensive_network_disruption.geometry.integration_review import directional_breakpoints, values_for_components
from defensive_network_disruption.geometry.occlusion_fields import CANDIDATES, CarrierOriginField
from defensive_network_disruption.geometry.verification_audit import COUNTS
from defensive_network_disruption.geometry.verification_repair import find_verified_envelope
from defensive_network_disruption.geometry.production_verification import certified_partitions
from defensive_network_disruption.geometry.micro_interval_verifier import GLOBAL_RESIDUAL_BUDGET
from defensive_network_disruption.geometry.vector_reproducibility import component_record, extract_log_envelope

START = "749dcd2856e846d87e7f4f74e9f6b7f97bfd72c7"
TAG = "f00690c05d8c1c6db308a65bd311c43f9a8ef2fa"
PROTOCOL = Path("docs/protocols/phase_14x_cross_platform_vector_reproducibility.md")
OUT = Path("outputs/cross_platform_vector_reproducibility")
LOCAL = OUT / "local"
HISTORICAL = Path("outputs/continuous_occlusion_production_acceptance/reference_comparison.csv")
FIXTURES = Path("scripts/session_14_occlusion_fields.py")
CODE = (Path("scripts/session_14x_cross_platform_vector_reproducibility.py"),
        Path("src/defensive_network_disruption/geometry/vector_reproducibility.py"),
        Path("tests/test_session14x_vector_reproducibility.py"),
        Path(".github/workflows/session14x-diagnostic.yml"))
HISTORICAL_SHA = "c0f7935a4b728598126f0b5701ad36dedf0981ab20c73b6d5879d9ee38981e56"

def git(*args): return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
def safe(path):
    path = Path(path)
    if path.is_absolute() or ".." in path.parts: raise ValueError("unsafe_path")
    result = ROOT / path
    if any(item.is_symlink() for item in (result, *result.parents)): raise ValueError("symlink_rejected")
    return result
def digest(path): return hashlib.sha256(safe(path).read_bytes()).hexdigest()
def committed(path):
    if safe(path).read_bytes() != subprocess.check_output(["git","show",f"HEAD:{path}"],cwd=ROOT):
        raise ValueError("uncommitted_authority")
def encoded(value): return (json.dumps(value, sort_keys=True, separators=(",",":"), allow_nan=False)+"\n").encode()
def write_once(path, data):
    target=safe(path); target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists(): raise FileExistsError("output_exists")
    temp=target.with_name("."+target.name+".tmp"); temp.write_bytes(data); temp.replace(target)

def fixtures():
    node=next(x for x in ast.parse(safe(FIXTURES).read_text()).body if isinstance(x,ast.FunctionDef) and x.name=="fixtures")
    namespace={}; exec(compile(ast.Module(body=[node],type_ignores=[]),"<frozen fixtures>","exec"),namespace)
    rows=tuple(namespace["fixtures"]())
    if len(rows)!=36: raise ValueError("fixture_count")
    return rows

def historical_vectors():
    with safe(HISTORICAL).open(newline="") as stream: rows=list(csv.DictReader(stream))
    vectors={}
    for row in rows:
        key=(row["fixture"],row["candidate"])
        item=vectors.setdefault(key,{"intervals":int(row["intervals"]),"estimates":{}})
        if item["intervals"]!=int(row["intervals"]): raise ValueError("mixed_intervals")
        item["estimates"][row["component"]]=float(row["estimate"])
    if len(rows)!=366 or len(vectors)!=108: raise ValueError("historical_shape")
    return vectors

def environment():
    config=np.__config__.show(mode="dicts")
    build=config.get("Build Dependencies",{})
    def library(name):
        value=build.get(name,{})
        return {"name":str(value.get("name","unavailable")),"version":str(value.get("version","unavailable"))}
    return {"os":platform.system(),"platform":platform.platform(),"architecture":platform.machine(),
            "python":platform.python_version(),"python_build":" ".join(platform.python_build()),
            "implementation":platform.python_implementation(),"libc":" ".join(platform.libc_ver()),
            "numpy":np.__version__,"scipy":scipy.__version__,"blas":library("blas"),"lapack":library("lapack"),
            "uv_lock_sha256":digest("uv.lock"),"installation":"uv-sync-editable"}

def route(candidate, origin, receiver, defenders):
    field=CarrierOriginField(candidate); base=np.asarray(origin,dtype=np.float64); edge=np.asarray(receiver,dtype=np.float64)-base
    def function(t):
        query=base[None,:]+t[:,None]*edge[None,:]
        return field.individual_values(origin,defenders,query)
    onset=() if candidate=="isotropic" else directional_breakpoints(origin,receiver,defenders)
    envelope=find_verified_envelope(function,extra_partitions=onset)
    parts=certified_partitions(function,envelope,onset)
    widths=[b-a for a,b in zip(parts[:-1],parts[1:],strict=True)]
    threshold=GLOBAL_RESIDUAL_BUDGET/len(widths)
    bounded=[width for width in widths if width<=threshold]
    def boundary(value):
        if value is None:return None
        return [value.outside,value.inside,value.direction,list(value.owners)]
    return {"partitions":list(parts),"switches":[[x.location,list(x.left_owners),list(x.right_owners)] for x in envelope.switches],
            "tie_enclosures":[[boundary(x.start),boundary(x.end),list(x.owners)] for x in envelope.tie_intervals],
            "threshold":threshold,"piece_widths":widths,"bounded_widths":bounded,
            "bounded_count":len(bounded),"quadrature_count":len(widths)-len(bounded),
            "residual_bound":math.fsum(bounded)}

def diagnostic():
    expected=historical_vectors(); records=[]
    for label,origin,receiver,defenders in fixtures():
        for candidate in CANDIDATES:
            key=(label,candidate); field=CarrierOriginField(candidate); ladder=[]; previous=None; accepted=None
            for count in COUNTS:
                values=values_for_components(field,origin,receiver,defenders,count)
                change=None if previous is None else max(abs(values[k]-previous[k]) for k in values)
                ladder.append({"intervals":count,"values":values,"maximum_change":change})
                if accepted is None and change is not None and change<=1e-7: accepted={"intervals":count,"values":values,"maximum_change":change}
                previous=values
            if accepted is None: raise ValueError("controlled_nonconvergence")
            comparison=[component_record(name,expected[key]["estimates"][name],value) for name,value in accepted["values"].items()]
            records.append({"fixture":label,"candidate":candidate,"historical":expected[key],"accepted":accepted,
                            "ladder":ladder,"comparison":comparison,"routing":route(candidate,origin,receiver,defenders)})
    if len(records)!=108 or sum(len(x["comparison"]) for x in records)!=366: raise ValueError("diagnostic_shape")
    return {"schema_version":1,"authority":{"historical_sha256":digest(HISTORICAL),"fixture_sha256":digest(FIXTURES),
            "component_order":"individual_1..n,union,maximum","vector_count":108,"component_count":366},
            "environment":environment(),"records":records}

def preflight():
    if git("status","--porcelain"): raise ValueError("clean_tree_required")
    if git("rev-parse","v0.1.0^{}")!=TAG or digest(HISTORICAL)!=HISTORICAL_SHA: raise ValueError("authority_changed")
    for path in (PROTOCOL,*CODE): committed(path)
    print("Session 14x preflight passed; synthetic diagnostic only")

def local_diagnostic():
    preflight(); raw=encoded(diagnostic()); write_once(LOCAL/"diagnostic.json",raw)
    sha=hashlib.sha256(raw).hexdigest(); print(f"SESSION14X_DIAGNOSTIC_BEGIN {sha} {base64.b64encode(raw).decode()}")
    print("SESSION14X_DIAGNOSTIC_END")

def compare(ci_log):
    preflight(); local=json.loads(safe(LOCAL/"diagnostic.json").read_text())
    raw=extract_log_envelope(Path(ci_log).read_text()); ci=json.loads(raw); write_once(LOCAL/"ci_diagnostic.json",raw)
    local_by={(x["fixture"],x["candidate"]):x for x in local["records"]}; ci_by={(x["fixture"],x["candidate"]):x for x in ci["records"]}
    vector_rows=[]; resolution_rows=[]; differing=[]
    for key,item in local_by.items():
        other=ci_by[key]
        for lrow,crow in zip(item["comparison"],other["comparison"],strict=True):
            row=component_record(lrow["component"],lrow["actual"],crow["actual"])
            row={"fixture":key[0],"candidate":key[1],**row}; vector_rows.append(row)
            if not row["bitwise_equal"]: differing.append(row)
        for left,right in zip(item["ladder"],other["ladder"],strict=True):
            differences=[abs(left["values"][k]-right["values"][k]) for k in left["values"]]
            resolution_rows.append({"fixture":key[0],"candidate":key[1],"intervals":left["intervals"],
                "local_maximum_change":left["maximum_change"],"ci_maximum_change":right["maximum_change"],
                "maximum_absolute_platform_difference":max(differences),"bitwise_equal":all(
                    component_record(k,left["values"][k],right["values"][k])["bitwise_equal"] for k in left["values"])})
    routes_equal=all(local_by[k]["routing"]==ci_by[k]["routing"] for k in local_by)
    resolutions_equal=all(local_by[k]["accepted"]["intervals"]==ci_by[k]["accepted"]["intervals"] for k in local_by)
    numeric_ok=all((row["absolute_difference"] or 0)<=1e-6 for row in vector_rows)
    classification="C" if differing and routes_equal and resolutions_equal and numeric_ok else "A" if not differing else "E" if not routes_equal or not resolutions_equal else "F"
    readiness=1 if classification in ("A","B","C") else 3
    def csv_bytes(rows,fields):
        stream=io.StringIO(newline=""); writer=csv.DictWriter(stream,fieldnames=fields,lineterminator="\n"); writer.writeheader(); writer.writerows(rows); return stream.getvalue().encode()
    vector_fields=("fixture","candidate","component","expected","actual","expected_bits","actual_bits","expected_signed_zero","actual_signed_zero","absolute_difference","relative_difference","ulp_distance","finite","python_equal","bitwise_equal")
    resolution_fields=("fixture","candidate","intervals","local_maximum_change","ci_maximum_change","maximum_absolute_platform_difference","bitwise_equal")
    write_once(OUT/"vector_comparison.csv",csv_bytes(vector_rows,vector_fields)); write_once(OUT/"resolution_comparison.csv",csv_bytes(resolution_rows,resolution_fields))
    write_once(OUT/"environment_comparison.json",encoded({"local":local["environment"],"ci":ci["environment"],"same_dependencies":local["environment"]["numpy"]==ci["environment"]["numpy"] and local["environment"]["scipy"]==ci["environment"]["scipy"]}))
    write_once(OUT/"routing_comparison.json",encoded({"all_108_equal":routes_equal,"different_vectors":[list(k) for k in local_by if local_by[k]["routing"]!=ci_by[k]["routing"]]}))
    first=next((row for row in resolution_rows if not row["bitwise_equal"]),None)
    review={"classification":classification,"readiness":readiness,"historical_python_equality":"accepted interval integer and estimates dictionary exact equality",
            "algorithmically_reproducible":routes_equal and resolutions_equal,"numerically_reproducible_within_existing_1e_6_authority":numeric_ok,
            "bitwise_reproducible":not differing,"differing_components":len(differing),
            "maximum_absolute_difference":max((x["absolute_difference"] or 0 for x in vector_rows),default=0),
            "maximum_relative_difference":max((x["relative_difference"] or 0 for x in vector_rows),default=0),
            "maximum_ulp_distance":max((x["ulp_distance"] or 0 for x in vector_rows),default=0),
            "first_divergent_resolution":None if first is None else first["intervals"],"replacement_tolerance_selected":False}
    write_once(OUT/"equality_contract_review.json",encoded(review))
    write_once(OUT/"qc.json",encoded({"schema_version":1,"status":"closed","classification":classification,"readiness":readiness,"vector_count":108,"component_count":366,"ci_record_sha256":hashlib.sha256(raw).hexdigest(),"empirical_access":False,"session14r_partial_outputs_accessed":False}))
    public=("environment_comparison.json","vector_comparison.csv","resolution_comparison.csv","routing_comparison.json","equality_contract_review.json","qc.json")
    manifest={"schema_version":1,"status":"closed","start":START,"protocol_sha256":digest(PROTOCOL),"historical_sha256":digest(HISTORICAL),"ci_record_sha256":hashlib.sha256(raw).hexdigest(),"implementation":{str(x):digest(x) for x in CODE},"outputs":{x:digest(OUT/x) for x in public}}
    write_once(OUT/"manifest.json",encoded(manifest)); print(json.dumps(review,sort_keys=True))

def publication_check():
    manifest=json.loads(safe(OUT/"manifest.json").read_text())
    for name,sha in manifest["outputs"].items():
        if digest(OUT/name)!=sha: raise ValueError("output_hash_changed")
    for name in (*manifest["outputs"],"manifest.json"):
        text=safe(OUT/name).read_text()
        if any(x in text for x in ("/Users/","/home/runner/","event_id","target_id","X-Amz-Signature")): raise ValueError("publication_boundary")
    print("Session 14x publication checks passed")

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("command",choices=("preflight","local-diagnostic","compare","publication-check")); parser.add_argument("--ci-log")
    args=parser.parse_args()
    if args.command=="compare":
        if not args.ci_log: raise ValueError("ci_log_required")
        compare(args.ci_log)
    else: {"preflight":preflight,"local-diagnostic":local_diagnostic,"publication-check":publication_check}[args.command]()
if __name__=="__main__": main()
