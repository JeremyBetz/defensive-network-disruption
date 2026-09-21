"""Strict R9X evidence package; eight public files and no empirical payloads."""
from __future__ import annotations

import csv
import io
from pathlib import Path

from .r9j_evidence import finite, hash_string, load, put, put_bytes, sha

NAMES = (
    "retention_contract.json", "evidence_loss_trace.json", "minimum_schema.json",
    "field_necessity.csv", "synthetic_sufficiency.csv",
    "prospective_acquisition.json", "qc.json", "manifest.json",
)
FIELD_COLUMNS = ("field", "disposition", "reason", "evidence_sha256")
SYNTHETIC_COLUMNS = (
    "fixture", "expected", "observed", "source_discarded", "passed",
    "evidence_sha256",
)


def _csv(rows, columns):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        if set(row) != set(columns) - {"evidence_sha256"}:
            raise ValueError("csv_row_schema")
        formatted = dict(row)
        for key in ("source_discarded", "passed"):
            if key in formatted:
                formatted[key] = str(formatted[key]).lower()
        writer.writerow({**formatted, "evidence_sha256": "{INDEX}"})
    return stream.getvalue().encode()


def _validate_json(name, value):
    schemas = {
        "retention_contract.json": {"schema_version", "status", "flags", "counts", "authority", "evidence_sha256"},
        "evidence_loss_trace.json": {"schema_version", "status", "entries", "evidence_sha256"},
        "minimum_schema.json": {"schema_version", "status", "required", "derivable", "redundant", "prohibited", "field_schema", "evidence_sha256"},
        "prospective_acquisition.json": {"schema_version", "status", "flags", "counts", "steps", "recommendation", "evidence_sha256"},
    }
    if set(value) != schemas[name] or value["schema_version"] != 1:
        raise ValueError("public_record_schema")
    if value["status"] != "complete" or not hash_string(value["evidence_sha256"]):
        raise ValueError("public_record_status")
    finite(value)


def close(folder, authority, records, field_rows, synthetic_rows, qc):
    folder = Path(folder); local = folder / "local"
    private = {path.relative_to(local).as_posix(): sha(path)
               for path in sorted(local.rglob("*"))
               if path.is_file() and path.name != "private_index.json"}
    put(local / "private_index.json", {"schema_version": 1, "files": private})
    index_hash = sha(local / "private_index.json")
    for name, value in records.items():
        value = {**value, "evidence_sha256": index_hash}
        _validate_json(name, value)
        put(folder / name, value)
    put_bytes(folder / "field_necessity.csv",
              _csv(field_rows, FIELD_COLUMNS).replace(b"{INDEX}", index_hash.encode()))
    put_bytes(folder / "synthetic_sufficiency.csv",
              _csv(synthetic_rows, SYNTHETIC_COLUMNS).replace(b"{INDEX}", index_hash.encode()))
    put(folder / "qc.json", {**qc, "schema_version": 1,
                              "private_index_sha256": index_hash})
    put(folder / "manifest.json", {
        "schema_version": 1, "authority": authority,
        "private_index_sha256": index_hash,
        "outputs": {name: sha(folder / name) for name in NAMES if name != "manifest.json"},
    })
    return publication_check(folder)


def publication_check(folder):
    folder = Path(folder); local = folder / "local"
    if {path.name for path in folder.iterdir() if path.is_file()} != set(NAMES):
        raise ValueError("public_inventory")
    manifest = load(folder / "manifest.json")
    if set(manifest) != {"schema_version", "authority", "private_index_sha256", "outputs"} or manifest["schema_version"] != 1:
        raise ValueError("manifest_schema")
    if set(manifest["outputs"]) != set(NAMES) - {"manifest.json"}:
        raise ValueError("manifest_inventory")
    for name, expected in manifest["outputs"].items():
        if not hash_string(expected) or sha(folder / name) != expected:
            raise ValueError("public_hash")
    index = load(local / "private_index.json")
    if sha(local / "private_index.json") != manifest["private_index_sha256"]:
        raise ValueError("private_index_hash")
    if set(index) != {"schema_version", "files"} or index["schema_version"] != 1:
        raise ValueError("private_index_schema")
    for name, expected in index["files"].items():
        if Path(name).is_absolute() or ".." in Path(name).parts or not hash_string(expected) or sha(local / name) != expected:
            raise ValueError("private_hash")
    for name in ("retention_contract.json", "evidence_loss_trace.json",
                 "minimum_schema.json", "prospective_acquisition.json"):
        value = load(folder / name); _validate_json(name, value)
        if value["evidence_sha256"] != manifest["private_index_sha256"]:
            raise ValueError("record_binding")
    for name, columns in (("field_necessity.csv", FIELD_COLUMNS),
                          ("synthetic_sufficiency.csv", SYNTHETIC_COLUMNS)):
        raw = (folder / name).read_bytes()
        if b"\r" in raw:
            raise ValueError("csv_line_endings")
        reader = csv.DictReader(io.StringIO(raw.decode()))
        if tuple(reader.fieldnames or ()) != columns:
            raise ValueError("csv_schema")
        rows = list(reader)
        if not rows or any(None in row or row["evidence_sha256"] != manifest["private_index_sha256"] for row in rows):
            raise ValueError("csv_binding")
    qc = load(folder / "qc.json")
    expected = {"schema_version", "status", "execution_valid", "classification",
                "readiness", "states_accessed", "edges_accessed",
                "empirical_computation", "private_index_sha256"}
    if set(qc) != expected or qc["schema_version"] != 1:
        raise ValueError("qc_schema")
    if qc["classification"] not in ("A", "B", "C", "D") or qc["readiness"] not in (1, 2, 3, 4):
        raise ValueError("qc_classification")
    if type(qc["execution_valid"]) is not bool or type(qc["empirical_computation"]) is not bool:
        raise ValueError("qc_types")
    if qc["states_accessed"] != 0 or qc["edges_accessed"] != 0 or qc["empirical_computation"]:
        raise ValueError("empirical_access")
    synthetic = list(csv.DictReader(io.StringIO((folder / "synthetic_sufficiency.csv").read_text())))
    all_synthetic = all(row["passed"] == "true" for row in synthetic)
    acquisition = load(folder / "prospective_acquisition.json")
    if qc["classification"] == "A" and not (all_synthetic and all(acquisition["flags"].values())):
        raise ValueError("false_acceptance")
    prohibited = ("/Users/", "/private/", '"carrier"', '"receiver"',
                  '"defenders"', '"coordinates"', '"alias"')
    for name in NAMES:
        text = (folder / name).read_text()
        if any(token in text for token in prohibited):
            raise ValueError("public_privacy")
    return {"valid": True, "files": len(NAMES),
            "classification": qc["classification"], "readiness": qc["readiness"]}
