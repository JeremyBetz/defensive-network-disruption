"""Strict six-file public evidence contract for R9Y."""
from pathlib import Path
from .r9j_evidence import finite, hash_string, load, put, sha

NAMES = ("acquisition_contract.json", "lineage_validation.json",
         "authority_capture.json", "sufficiency_validation.json", "qc.json", "manifest.json")

def close(folder, records, qc):
    folder=Path(folder); local=folder/"local"
    private={p.relative_to(local).as_posix():sha(p) for p in sorted(local.rglob("*"))
             if p.is_file() and p.name != "private_index.json"}
    put(local/"private_index.json", {"schema_version":1,"files":private})
    index_hash=sha(local/"private_index.json")
    for name,value in records.items(): put(folder/name,{**value,"evidence_sha256":index_hash})
    put(folder/"qc.json",{**qc,"schema_version":1,"private_index_sha256":index_hash})
    put(folder/"manifest.json",{"schema_version":1,"private_index_sha256":index_hash,
        "outputs":{name:sha(folder/name) for name in NAMES if name!="manifest.json"}})
    return publication_check(folder)

def publication_check(folder):
    folder=Path(folder)
    if {p.name for p in folder.iterdir() if p.is_file()} != set(NAMES): raise ValueError("inventory")
    manifest=load(folder/"manifest.json")
    if set(manifest)!={"schema_version","private_index_sha256","outputs"} or manifest["schema_version"]!=1: raise ValueError("manifest")
    if set(manifest["outputs"])!=set(NAMES)-{"manifest.json"}: raise ValueError("outputs")
    for name,value in manifest["outputs"].items():
        if not hash_string(value) or sha(folder/name)!=value: raise ValueError("public_hash")
    local=folder/"local"; index=load(local/"private_index.json")
    if sha(local/"private_index.json")!=manifest["private_index_sha256"]: raise ValueError("private_index")
    for name,value in index["files"].items():
        if Path(name).is_absolute() or ".." in Path(name).parts or sha(local/name)!=value: raise ValueError("private_hash")
    for name in NAMES[:-2]:
        value=load(folder/name)
        if value.get("schema_version")!=1 or value.get("status") not in ("complete","partial","blocked","invalid") or value.get("evidence_sha256")!=manifest["private_index_sha256"]: raise ValueError("record")
        finite(value)
    qc=load(folder/"qc.json")
    expected={"schema_version","status","execution_valid","classification","readiness",
              "previously_exposed_states_reopened","previously_exposed_edges_reopened",
              "new_population_states","new_population_edges","field_evaluations",
              "refinement_performed","classification_performed","private_index_sha256"}
    if set(qc)!=expected or qc["classification"] not in "ABCD" or qc["readiness"] not in (1,2,3,4): raise ValueError("qc")
    if qc["classification"]=="A" and not (qc["execution_valid"] and qc["readiness"]==1 and
       qc["previously_exposed_states_reopened"]==qc["previously_exposed_edges_reopened"]==1 and
       qc["new_population_states"]==qc["new_population_edges"]==qc["field_evaluations"]==0 and
       not qc["refinement_performed"] and not qc["classification_performed"]): raise ValueError("false_acceptance")
    prohibited=("/Users/","coordinates","carrier","receiver","defenders","alias","numerator","denominator")
    for name in NAMES:
        text=(folder/name).read_text()
        if any(token in text for token in prohibited): raise ValueError("privacy")
    return {"valid":True,"files":6,"classification":qc["classification"],"readiness":qc["readiness"]}
