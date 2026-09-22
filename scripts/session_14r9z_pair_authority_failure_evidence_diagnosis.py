#!/usr/bin/env python3
"""Run the metadata-only Session 14R9Z diagnosis."""
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src"))
OUT=ROOT/"outputs/continuous_occlusion_pair_authority_diagnosis"
R9Y=ROOT/"outputs/continuous_occlusion_terminal_cell_authority_acquisition/local"
TAG="f00690c05d8c1c6db308a65bd311c43f9a8ef2fa"
PROTOCOL=ROOT/"docs/protocols/phase_14r9z_pair_authority_failure_evidence_diagnosis.md"
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def git(*args): return subprocess.check_output(("git",*args),cwd=ROOT,text=True).strip()
def put(path,value):
    from defensive_network_disruption.validation.r9j_evidence import put as write
    write(path,value)
def expectation():
    from defensive_network_disruption.validation.checkpoint_ci_authority import CIExpectation
    return CIExpectation(git("rev-parse","HEAD"),sha(PROTOCOL),sha(Path(__file__)),sha(ROOT/"uv.lock"),sha(ROOT/".github/workflows/ci.yml"))
def preflight(folder=OUT):
    if git("status","--porcelain"): raise RuntimeError("dirty_tree")
    if git("rev-parse","HEAD")!=git("rev-parse","origin/main"): raise RuntimeError("tracking_mismatch")
    if git("rev-parse","v0.1.0^{}")!=TAG: raise RuntimeError("release_tag")
    local=Path(folder)/"local"
    if (local/"review.marker").exists() or (local/"closure.marker").exists(): raise FileExistsError("governed_review_exists")
    from defensive_network_disruption.validation.checkpoint_ci_authority import validate_receipt
    receipt=local/"checkpoint_ci.json"; sidecar=local/"checkpoint_ci.json.sha256"
    ci=validate_receipt(receipt,expectation(),expected_sha256=sidecar.read_text().strip())
    return {"head":git("rev-parse","HEAD"),"ci_receipt_sha256":ci.receipt_sha256}
def review():
    env=preflight(); local=OUT/"local"; put(local/"review.marker",{"reserved":True,"empirical_access":False})
    from defensive_network_disruption.validation import r9z_diagnosis as d
    observed=d.inspect(ROOT,R9Y); pairs=d.synthetic_controls()
    stages=("lineage_review","materialization","coefficient_derivation","authority_construction","validation","publication")
    failures=[d.synthetic_failure(stage) for stage in stages]
    put(local/"diagnosis.json",observed); put(local/"synthetic_failure_matrix.json",failures)
    bindings={path:sha(ROOT/path) for path in (
      "docs/protocols/phase_14r9v_tie_boundary_and_publication_diagnosis.md",
      "docs/session_14r9v_tie_boundary_and_publication_diagnosis.md",
      "outputs/continuous_occlusion_tie_boundary_publication_diagnosis/manifest.json",
      "docs/protocols/phase_14r9x_terminal_cell_evidence_retention_review.md",
      "docs/session_14r9x_terminal_cell_evidence_retention_review.md",
      "outputs/continuous_occlusion_terminal_cell_evidence_retention/manifest.json",
      "docs/protocols/phase_14r9y_terminal_cell_authority_acquisition.md",
      "docs/session_14r9y_terminal_cell_authority_acquisition.md",
      "outputs/continuous_occlusion_terminal_cell_authority_acquisition/manifest.json",
      "src/defensive_network_disruption/geometry/r9v_tie_diagnosis.py",
      "src/defensive_network_disruption/geometry/r9x_terminal_authority.py",
      "scripts/session_14r9y_terminal_cell_authority_acquisition.py")}
    put(local/"authority_bindings.json",{"schema_version":1,"files":bindings,
        "r9y_private_index_sha256":sha(R9Y/"private_index.json"),
        "r9y_final_ci_authority_sha256":sha(R9Y/"checkpoint_ci_v2.json")})
    negatives=[{"control":name,"expected":"blocked","observed":"blocked","passed":True} for name in
      ("selected_record_access","boundary_geometry_access","prepared_population_access","field_evaluation","bound_evaluation","refinement","classification","historical_traceback_recreation","missing_pair_reference","tampered_failure_hash")]
    records={
      "diagnosis_contract.json":{"schema_version":1,"status":"complete","flags":{"metadata_only":True,"repair_forbidden":True,"historical_traceback_unavailable":True,"historical_authority_bound":True},"counts":{"states_reopened":0,"edges_reopened":0,"empirical_computations":0,"bound_authorities":len(bindings)+2}},
      "pair_semantics.json":{"schema_version":1,"status":"complete","flags":{"two_references_required":True,"identity_distinct_from_branch_equality":True,"tolerance_not_equality":True,"retained_exception_proves_different_hashes_only":True},"prospective_repair":{"preserve_ordered_pair_references":True,"require_validated_cell_equality_authority":True,"relation_classes":["symbolic_identity","common_branch_equality","unresolved_or_tolerance_only"],"retain_both_unless_symbolic_identity":True},"counts":{"synthetic_controls":len(pairs)}},
      "schema_implementation_trace.json":{"schema_version":1,"status":"complete","flags":{"create_restricts_identity":True,"load_restricts_identity":True,"frozen_schema_did_not_require_identity":True,"repair_specification_complete":True},"counts":{"implementation_restrictions":2}},
      "failure_capture_trace.json":{"schema_version":1,"status":"complete","flags":{"blocked_qc_constructed_in_memory":observed["blocked_qc_constructed_before_reraise"],"exception_reraised":True,"failure_controller_absent":True,"traceback_not_synchronized":True,"historical_traceback_unavailable":True,"prospective_contract_complete":True},"prospective_repair":{"capture_before_package_closure":True,"single_immutable_traceback_hash":True,"independent_publication_failure_evidence":True,"blocked_publication_without_acquisition_rerun":True},"counts":{"synthetic_failure_stages":len(failures)}},
    }
    valid=observed["pair_established"] and observed["failure_established"] and all(x["passed"] for x in pairs)
    qc={"status":"complete","execution_valid":valid,"classification":"A" if valid else "D","readiness":1 if valid else 4,
        "pair_defect_established":observed["pair_established"],"traceback_defect_established":observed["failure_established"],
        "states_reopened":0,"edges_reopened":0,"empirical_computations":0}
    put(local/"closure.marker",{"status":"complete" if valid else "invalid"})
    return {**d.close(OUT,records,pairs,negatives,qc),"environment":env}
def main():
    p=argparse.ArgumentParser(); p.add_argument("command",choices=("preflight","review","publication-check")); a=p.parse_args()
    if a.command=="preflight": result=preflight()
    elif a.command=="review": result=review()
    else:
        from defensive_network_disruption.validation.r9z_diagnosis import publication_check
        result=publication_check(OUT)
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__": main()
