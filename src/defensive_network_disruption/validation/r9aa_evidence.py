"""Strict eight-file R9AA public evidence contract."""
from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

from .r9j_evidence import finite, load, put, put_bytes, sha

NAMES = ("repair_contract.json", "schema_v2.json", "compatibility_matrix.csv",
         "synthetic_pair_controls.csv", "traceback_controls.csv",
         "historical_preservation.json", "qc.json", "manifest.json")


def csv_bytes(rows):
    rows = list(rows); output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=list(rows[0]))
    writer.writeheader(); writer.writerows(rows)
    return output.getvalue().encode()


def close(folder, records, csv_records, qc):
    folder = Path(folder); local = folder / "local"
    private = {path.relative_to(local).as_posix(): sha(path)
               for path in sorted(local.rglob("*"))
               if path.is_file() and path.name != "private_index.json"}
    put(local / "private_index.json", {"schema_version": 1, "files": private})
    index_hash = sha(local / "private_index.json")
    for name, value in records.items():
        put(folder / name, {**value, "evidence_sha256": index_hash})
    for name, rows in csv_records.items():
        put_bytes(folder / name, csv_bytes(rows))
    put(folder / "qc.json", {**qc, "schema_version": 1,
                              "private_index_sha256": index_hash})
    put(folder / "manifest.json", {"schema_version": 1,
        "private_index_sha256": index_hash,
        "outputs": {name: sha(folder / name) for name in NAMES if name != "manifest.json"}})
    return publication_check(folder)


def publication_check(folder):
    folder = Path(folder)
    if {item.name for item in folder.iterdir() if item.is_file()} != set(NAMES):
        raise ValueError("inventory")
    manifest = load(folder / "manifest.json")
    if set(manifest) != {"schema_version", "private_index_sha256", "outputs"} or manifest["schema_version"] != 1:
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
    for name in ("repair_contract.json", "schema_v2.json", "historical_preservation.json"):
        value = load(folder / name)
        if value.get("schema_version") != 1 or value.get("status") != "complete" or value.get("evidence_sha256") != manifest["private_index_sha256"]:
            raise ValueError("record_schema")
        finite(value)
    qc = load(folder / "qc.json")
    required = {"schema_version", "status", "execution_valid", "classification",
                "readiness", "schema_repair_valid", "traceback_repair_valid",
                "historical_v1_preserved", "historical_r9y_traceback_available",
                "states_reopened", "edges_reopened", "empirical_computations",
                "private_index_sha256"}
    if set(qc) != required or qc["classification"] not in "ABCD" or qc["readiness"] not in (1, 2, 3, 4):
        raise ValueError("qc_schema")
    if qc["classification"] == "A" and not (
            qc["execution_valid"] and qc["readiness"] == 1 and
            qc["schema_repair_valid"] and qc["traceback_repair_valid"] and
            qc["historical_v1_preserved"] and
            qc["historical_r9y_traceback_available"] is False and
            qc["states_reopened"] == qc["edges_reopened"] == qc["empirical_computations"] == 0):
        raise ValueError("false_acceptance")
    prohibited = ("/Users/", "selected_edge", "boundary_capture", "coordinates",
                  "carrier", "receiver", "defenders", "numerator", "denominator")
    for name in NAMES:
        text = (folder / name).read_text()
        if any(token in text for token in prohibited):
            raise ValueError("privacy")
    return {"valid": True, "files": 8, "classification": qc["classification"],
            "readiness": qc["readiness"]}


__all__ = ["NAMES", "close", "publication_check"]
