#!/usr/bin/env python3
"""One bounded R9Y retained terminal-cell authority acquisition."""
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/"docs/protocols/phase_14r9y_terminal_cell_authority_acquisition.md"
OUT=ROOT/"outputs/continuous_occlusion_terminal_cell_authority_acquisition"
R9V=ROOT/"outputs/continuous_occlusion_tie_boundary_publication_diagnosis/local"
START="c12f86a3b3441f0845fae5a0e9989d00b73e141a"
TAG="f00690c05d8c1c6db308a65bd311c43f9a8ef2fa"
INDEX_HASH="2abe5f916265275a94c157bd1a93c55f96d352863cbdce618a40418af3a2ebc6"

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1048576),b""): h.update(block)
    return h.hexdigest()
def git(*args): return subprocess.check_output(("git",*args),cwd=ROOT,text=True).strip()
def expectation():
    from defensive_network_disruption.validation.checkpoint_ci_authority import CIExpectation
    return CIExpectation(git("rev-parse","HEAD"),sha(PROTOCOL),sha(Path(__file__)),sha(ROOT/"uv.lock"),sha(ROOT/".github/workflows/ci.yml"))
def put(path,value):
    from defensive_network_disruption.validation.r9j_evidence import put
    put(path,value)

def preflight(folder=OUT):
    if git("status","--porcelain"): raise RuntimeError("dirty_tree")
    if git("rev-parse","HEAD")!=git("rev-parse","origin/main"): raise RuntimeError("tracking_mismatch")
    git("merge-base","--is-ancestor",START,"HEAD")
    if git("rev-parse","v0.1.0^{}")!=TAG: raise RuntimeError("release_tag")
    if Path(sys.prefix).resolve()!=(ROOT/".venv").resolve(): raise RuntimeError("environment")
    local=Path(folder)/"local"
    for name in ("review.marker","access.marker","authority.marker","closure.marker"):
        if (local/name).exists(): raise FileExistsError("governed_attempt_exists")
    from defensive_network_disruption.validation.checkpoint_ci_authority import validate_receipt
    # The generic capture tool appends ``.sha256`` to the complete receipt
    # filename.  Use a new create-once name so the superseded checkpoint
    # receipt remains immutable after a corrected implementation commit.
    receipt=local/"checkpoint_ci_v2.json"; sidecar=local/"checkpoint_ci_v2.json.sha256"
    ci=validate_receipt(receipt,expectation(),expected_sha256=sidecar.read_text().strip())
    return {"head":git("rev-parse","HEAD"),"protocol_sha256":sha(PROTOCOL),
            "runner_sha256":sha(Path(__file__)),"ci_receipt_sha256":ci.receipt_sha256}

def acquire(folder=OUT):
    folder=Path(folder); local=folder/"local"; env=preflight(folder)
    from defensive_network_disruption.geometry import r9y_acquisition as a
    from defensive_network_disruption.validation import r9y_evidence as e
    records={}; exposure=False
    try:
        put(local/"review.marker",{"reserved":True,"authorizes_access":False})
        lineage=a.load_lineage(R9V,expected_index_sha256=INDEX_HASH)
        put(local/"lineage_receipt.json",{"private_index_sha256":INDEX_HASH,
            "ordered_partition_sha256":lineage["ordered_partition_sha256"],"cells":81})
        records["lineage_validation.json"]={"schema_version":1,"status":"complete",
            "flags":{"private_index":True,"boundary":True,"partition":True,"selected_copy":True,
                     "unresolved_identity":True,"reference_implementation":True},
            "counts":{"cells":81,"unresolved":1}}
        put(local/"access.marker",{"reserved":True,"authorizes_access":True})
        put(local/"access_attempt.json",{"lineage_receipt_sha256":sha(local/"lineage_receipt.json")})
        boundary_path=R9V/"boundary_capture.json"; selected_path=R9V/"selected_edge.json"
        if sha(boundary_path)!=lineage["boundary_capture_sha256"] or sha(selected_path)!=lineage["selected_edge_sha256"]: raise ValueError("retained_hash")
        boundary=json.loads(boundary_path.read_bytes()); selected=json.loads(selected_path.read_bytes())
        put(local/"materialization_receipt.json",{"attempt_sha256":sha(local/"access_attempt.json"),
            "selected_edge_sha256":lineage["selected_edge_sha256"]})
        exposure=True
        put(local/"authority.marker",{"reserved":True})
        reference_hash=sha(ROOT/"src/defensive_network_disruption/geometry/r9v_tie_diagnosis.py")
        authority=a.acquire(lineage=lineage,boundary=boundary,selected=selected,
            private_index_sha256=INDEX_HASH,reference_implementation_sha256=reference_hash)
        put(local/"terminal_cell_authority.json",authority)
        from defensive_network_disruption.geometry.r9x_terminal_authority import load_authority,canonical
        loaded=load_authority(json.loads((local/"terminal_cell_authority.json").read_bytes()))
        if canonical(authority)!=(local/"terminal_cell_authority.json").read_bytes(): raise ValueError("authority_bytes")
        coefficient_count=len(authority["coefficients"])
        records.update({
          "acquisition_contract.json":{"schema_version":1,"status":"complete","flags":{"scope_exact":True,"field_evaluation_forbidden":True,"refinement_forbidden":True,"classification_forbidden":True},"counts":{"authorities":1}},
          "authority_capture.json":{"schema_version":1,"status":"complete","flags":{"created_once":True,"bounds_derived":True,"coefficients_complete":True,"references_complete":True},"counts":{"authorities":1,"coefficient_records":coefficient_count,"pair_references":2,"competitor_references":len(authority["competitors"])},"authority_sha256":sha(local/"terminal_cell_authority.json"),"provenance_sha256":authority["provenance_sha256"]},
          "sufficiency_validation.json":{"schema_version":1,"status":"complete","flags":{"loader_accepted":True,"canonical_bytes":True,"round_trip":True,"provenance":True,"no_bounds_evaluated":True,"no_refinement":True,"no_classification":True},"counts":{"loaded_pairs":len(loaded[1]),"loaded_competitors":len(loaded[2])}},
        })
        qc={"status":"complete","execution_valid":True,"classification":"A","readiness":1,
            "previously_exposed_states_reopened":1,"previously_exposed_edges_reopened":1,
            "new_population_states":0,"new_population_edges":0,"field_evaluations":0,
            "refinement_performed":False,"classification_performed":False}
    except Exception:
        qc={"status":"blocked","execution_valid":False,"classification":"D","readiness":4,
            "previously_exposed_states_reopened":int(exposure),"previously_exposed_edges_reopened":int(exposure),
            "new_population_states":0,"new_population_edges":0,"field_evaluations":0,
            "refinement_performed":False,"classification_performed":False}
        raise
    put(local/"closure.marker",{"status":"complete"})
    result=e.close(folder,records,qc); return {**result,"environment":env}

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("command",choices=("preflight","acquire","publication-check")); args=parser.parse_args()
    if args.command=="preflight": result=preflight()
    elif args.command=="acquire": result=acquire()
    else:
        from defensive_network_disruption.validation.r9y_evidence import publication_check
        result=publication_check(OUT)
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__": main()
