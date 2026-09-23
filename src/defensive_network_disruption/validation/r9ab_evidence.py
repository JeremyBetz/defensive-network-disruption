"""Strict seven-file R9AB public evidence contract."""
from __future__ import annotations

from pathlib import Path

from .r9j_evidence import finite, load, put, sha
from .r9v_publication_ownership import validate_persisted

NAMES = ("acquisition_contract.json", "lineage_validation.json",
         "authority_capture.json", "pair_authority_validation.json",
         "sufficiency_validation.json", "qc.json", "manifest.json")


def close(folder, records, qc, authority, descriptor):
    folder = Path(folder); local = folder / "local"
    validate_persisted(descriptor, authority)
    private = {path.relative_to(local).as_posix(): sha(path)
               for path in sorted(local.rglob("*"))
               if path.is_file() and path.name != "private_index.json"}
    put(local / "private_index.json", {"schema_version": 1, "files": private})
    index_hash = sha(local / "private_index.json")
    for name, value in records.items():
        put(folder / name, {**value, "evidence_sha256": index_hash,
                            "closure_authority_sha256": descriptor.sha256})
    put(folder / "qc.json", {**qc, "schema_version": 1,
        "private_index_sha256": index_hash,
        "closure_authority_sha256": descriptor.sha256})
    put(folder / "manifest.json", {"schema_version": 1,
        "private_index_sha256": index_hash,
        "closure_authority_sha256": descriptor.sha256,
        "outputs": {name: sha(folder / name) for name in NAMES if name != "manifest.json"}})
    return publication_check(folder, authority=authority, descriptor=descriptor)


def publication_check(folder, *, authority=None, descriptor=None):
    folder = Path(folder)
    if {item.name for item in folder.iterdir() if item.is_file()} != set(NAMES):
        raise ValueError("inventory")
    manifest = load(folder / "manifest.json")
    if set(manifest) != {"schema_version", "private_index_sha256",
                         "closure_authority_sha256", "outputs"} or manifest["schema_version"] != 1:
        raise ValueError("manifest_schema")
    if set(manifest["outputs"]) != set(NAMES) - {"manifest.json"}:
        raise ValueError("manifest_outputs")
    if any(sha(folder / name) != value for name, value in manifest["outputs"].items()):
        raise ValueError("public_hash")
    local = folder / "local"; index = load(local / "private_index.json")
    if sha(local / "private_index.json") != manifest["private_index_sha256"]:
        raise ValueError("private_index")
    for name, value in index["files"].items():
        path = Path(name)
        if path.is_absolute() or ".." in path.parts or sha(local / path) != value:
            raise ValueError("private_hash")
    if authority is not None:
        if descriptor is None or validate_persisted(descriptor, authority)["status"] not in ("success", "failure"):
            raise ValueError("closure_authority")
        if descriptor.sha256 != manifest["closure_authority_sha256"]:
            raise ValueError("closure_authority_hash")
    for name in NAMES[:-2]:
        value = load(folder / name); finite(value)
        if set(value) != {"schema_version", "status", "flags", "counts",
                         "evidence_sha256", "closure_authority_sha256"}:
            raise ValueError("record_schema")
        if value["schema_version"] != 1 or value["status"] not in ("complete", "blocked", "invalid"):
            raise ValueError("record_status")
        if value["evidence_sha256"] != manifest["private_index_sha256"]:
            raise ValueError("record_evidence")
    qc = load(folder / "qc.json"); finite(qc)
    required = {"schema_version", "status", "execution_valid", "classification", "readiness",
                "authority_schema_version", "ordered_pair_refs_distinct", "competitors_complete",
                "interval_relation_lineage_valid", "canonical_round_trip", "states_reopened",
                "edges_reopened", "new_population_states", "new_population_edges",
                "candidate_evaluations", "field_evaluations", "refinements",
                "maximality_classifications", "exposure_uncertain", "private_index_sha256",
                "closure_authority_sha256"}
    if set(qc) != required or qc["classification"] not in "ABCD" or qc["readiness"] not in (1,2,3,4):
        raise ValueError("qc_schema")
    if qc["classification"] == "A" and not (
            qc["execution_valid"] and qc["readiness"] == 1 and
            qc["authority_schema_version"] == 2 and qc["ordered_pair_refs_distinct"] and
            qc["competitors_complete"] and qc["interval_relation_lineage_valid"] and
            qc["canonical_round_trip"] and qc["states_reopened"] == 1 and
            qc["edges_reopened"] == 1 and qc["new_population_states"] == 0 and
            qc["new_population_edges"] == 0 and not qc["exposure_uncertain"] and
            qc["candidate_evaluations"] == qc["field_evaluations"] == qc["refinements"] ==
            qc["maximality_classifications"] == 0):
        raise ValueError("false_acceptance")
    prohibited = ("/Users/", '"numerator"', '"denominator"', '"q"', '"dot"',
                  '"cross2"', '"carrier"', '"receiver"', '"defenders"',
                  "common_inactive_branch", '"ordinal"')
    for name in NAMES:
        text = (folder / name).read_text()
        if any(token in text for token in prohibited):
            raise ValueError("privacy")
    return {"valid": True, "files": 7, "classification": qc["classification"],
            "readiness": qc["readiness"]}


__all__ = ["NAMES", "close", "publication_check"]
