"""Strict public evidence contract for Session 14R9K."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import traceback

START = "1dabec1b1c953004e3e662370c0a4973e1e1ba06"
TAG = "f00690c05d8c1c6db308a65bd311c43f9a8ef2fa"
NAMES = (
    "repair_contract.json", "synthetic_acceptance.csv", "negative_controls.csv",
    "retained_edge_replay.json", "candidate_regression.csv", "performance.json",
    "publication_validation.json", "qc.json", "manifest.json",
)
JSON_SCHEMAS = {
    "repair_contract.json": {
        "flags": ("independent_route", "certified_boundaries_only", "production_unchanged",
                  "piecewise_unchanged", "tolerances_unchanged", "certificate_semantics_unchanged"),
        "counts": ("agreement_tolerance_power", "synthetic_families"),
        "timings": (),
    },
    "retained_edge_replay.json": {
        "flags": ("receipt_valid", "production_unchanged", "piecewise_unchanged",
                  "constant_width_passed", "isotropic_passed", "expanding_passed",
                  "no_certificate_special_case", "warnings_absent", "authority_exact"),
        "counts": ("states_reopened", "edges_reopened", "candidates_run"),
        "timings": ("seconds",),
    },
    "performance.json": {
        "flags": ("linear_piece_work", "one_call_per_ordinary_piece", "within_budget"),
        "counts": ("fixtures", "structural_pieces", "adaptive_calls", "micro_pieces"),
        "timings": ("historical_seconds", "repaired_seconds", "overhead_ratio"),
    },
    "publication_validation.json": {
        "flags": ("pa_unchanged", "single_retained_replay", "raw_hash", "chain_valid",
                  "counts_match", "failure_match", "success_package", "failure_package"),
        "counts": ("records", "states_opened", "edges_opened", "states_completed",
                   "edges_completed", "field_started", "field_completed", "unresolved_edges"),
        "timings": ("seconds",),
    },
}
CSV_SCHEMAS = {
    "synthetic_acceptance.csv": (
        "fixture", "candidate", "family", "status", "reference_kind", "within_gate",
        "production_preserved", "piecewise_preserved", "boundaries_exact", "components",
        "permutations", "reason", "evidence_sha256"),
    "negative_controls.csv": (
        "fixture", "expected_failure", "blocked", "reason", "evidence_sha256"),
    "candidate_regression.csv": (
        "candidate", "status", "accepted_resolution", "production_preserved",
        "piecewise_preserved", "comparator_passed", "certificate_count", "warning_count",
        "reason", "evidence_sha256"),
}


def finite(value):
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("nonfinite_evidence")
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str): raise ValueError("string_keys_required")
            finite(item)
    elif isinstance(value, (list, tuple)):
        for item in value: finite(item)


def canonical(value):
    finite(value)
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def safe(path):
    path = Path(path)
    if any(item.is_symlink() for item in (path, *path.parents)):
        raise PermissionError("symlink_rejected")
    return path


def sha(path):
    result = hashlib.sha256()
    with safe(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def put_bytes(path, raw):
    path = safe(path); path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists(): raise FileExistsError("immutable_evidence_exists")
    pending = path.with_name("." + path.name + ".pending")
    with pending.open("xb") as handle:
        handle.write(raw); handle.flush(); os.fsync(handle.fileno())
    os.link(pending, path); pending.unlink()
    descriptor = os.open(path.parent, os.O_RDONLY)
    try: os.fsync(descriptor)
    finally: os.close(descriptor)


def put(path, value):
    put_bytes(path, canonical(value))


def load(path):
    def pairs(items):
        output = {}
        for key, value in items:
            if key in output: raise ValueError("duplicate_key")
            output[key] = value
        return output
    result = json.loads(safe(path).read_bytes(), object_pairs_hook=pairs,
                        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite_json")))
    finite(result); return result


def emergency(path, error, stage):
    put(path, {"schema_version": 1, "status": "invalid", "stage": stage,
               "exception": type(error).__name__, "message": str(error),
               "traceback": "".join(traceback.format_exception(error))})


def hash_string(value):
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def empty_public():
    return {name: {"schema_version": 1, "status": "unavailable", "reason": "not_executed",
                   "flags": dict.fromkeys(schema["flags"]),
                   "counts": dict.fromkeys(schema["counts"]),
                   "timings": dict.fromkeys(schema["timings"]),
                   "evidence_sha256": None}
            for name, schema in JSON_SCHEMAS.items()}


def record(public, name, *, flags=None, counts=None, timings=None, reason=None):
    item = public[name]
    for kind, values in (("flags", flags), ("counts", counts), ("timings", timings)):
        if values:
            if set(values) - set(item[kind]): raise ValueError("unexpected_public_field")
            item[kind].update(values)
    item.update(status="available", reason=reason)


def validate_record(name, item):
    if set(item) != {"schema_version", "status", "reason", "flags", "counts",
                     "timings", "evidence_sha256"}:
        raise ValueError("public_record_schema")
    if item["schema_version"] != 1 or item["status"] not in ("available", "unavailable"):
        raise ValueError("public_record_status")
    if item["status"] == "unavailable" and not item["reason"]: raise ValueError("unavailable_reason")
    schema = JSON_SCHEMAS[name]
    for kind, expected in (("flags", bool), ("counts", int), ("timings", (int, float))):
        if set(item[kind]) != set(schema[kind]): raise ValueError("public_fields")
        for value in item[kind].values():
            if value is None: continue
            if (type(value) not in expected if isinstance(expected, tuple) else type(value) is not expected):
                raise ValueError("public_value_type")
            if kind != "flags" and value < 0: raise ValueError("negative_public_value")
    if not hash_string(item["evidence_sha256"]): raise ValueError("evidence_hash")
    finite(item)


def close(folder, public, rows, qc, authority):
    folder = Path(folder); local = folder / "local"
    private = {path.relative_to(local).as_posix(): sha(path)
               for path in sorted(local.rglob("*"))
               if path.is_file() and path.name != "private_index.json"}
    put(local / "private_index.json", {"schema_version": 1, "files": private})
    index_hash = sha(local / "private_index.json")
    for name, item in public.items():
        item["evidence_sha256"] = index_hash
        validate_record(name, item); put(folder / name, item)
    for name, columns in CSV_SCHEMAS.items():
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows.get(name, ()):
            writer.writerow({**row, "evidence_sha256": index_hash})
        put_bytes(folder / name, stream.getvalue().encode())
    payload = {**qc, "schema_version": 1, "private_index_sha256": index_hash}
    put(folder / "qc.json", payload)
    put(folder / "manifest.json", {
        "schema_version": 1, "status": payload["status"], "start": START,
        "authority": authority, "private_index_sha256": index_hash,
        "outputs": {name: sha(folder / name) for name in NAMES if name != "manifest.json"},
    })
    return publication_check(folder)


def publication_check(folder):
    folder = Path(folder); manifest = load(folder / "manifest.json"); qc = load(folder / "qc.json")
    if set(manifest) != {"schema_version", "status", "start", "authority",
                        "private_index_sha256", "outputs"}: raise ValueError("manifest_schema")
    if set(qc) != {"schema_version", "status", "execution_valid", "classification", "readiness",
                  "states_reopened", "edges_reopened", "exposure_uncertain", "private_index_sha256"}:
        raise ValueError("qc_schema")
    if manifest["start"] != START or manifest["status"] != qc["status"]: raise ValueError("authority_status")
    if qc["status"] not in ("complete", "blocked", "invalid"): raise ValueError("status")
    if type(qc["execution_valid"]) is not bool or qc["execution_valid"] != (qc["status"] != "invalid"):
        raise ValueError("execution_validity")
    if qc["classification"] not in tuple("ABCDE") or qc["readiness"] not in (1, 2, 3, 4):
        raise ValueError("decision")
    if qc["classification"] == "A" and qc["readiness"] != 1: raise ValueError("false_readiness")
    if any(type(qc[key]) is not int or qc[key] not in (0, 1)
           for key in ("states_reopened", "edges_reopened")): raise ValueError("access_count")
    if qc["states_reopened"] != qc["edges_reopened"]: raise ValueError("access_units")
    if type(qc["exposure_uncertain"]) is not bool: raise ValueError("exposure_type")
    if set(manifest["outputs"]) != set(NAMES) - {"manifest.json"}: raise ValueError("artifact_set")
    if {item.name for item in folder.iterdir() if item.is_file()} != set(NAMES): raise ValueError("extra_artifact")
    for name, expected in manifest["outputs"].items():
        if not hash_string(expected) or sha(folder / name) != expected: raise ValueError("artifact_hash")
    index = folder / "local/private_index.json"
    if sha(index) != qc["private_index_sha256"] or manifest["private_index_sha256"] != qc["private_index_sha256"]:
        raise ValueError("private_index_hash")
    for name, expected in load(index)["files"].items():
        if Path(name).is_absolute() or ".." in Path(name).parts or sha(folder / "local" / name) != expected:
            raise ValueError("private_file_hash")
    for name in JSON_SCHEMAS:
        item = load(folder / name); validate_record(name, item)
        if item["evidence_sha256"] != qc["private_index_sha256"]: raise ValueError("record_binding")
    for name, columns in CSV_SCHEMAS.items():
        raw = (folder / name).read_bytes()
        if b"\r" in raw: raise ValueError("csv_line_endings")
        reader = csv.DictReader(io.StringIO(raw.decode()))
        if reader.fieldnames != list(columns): raise ValueError("csv_schema")
        for row in reader:
            if None in row or row["evidence_sha256"] != qc["private_index_sha256"]:
                raise ValueError("csv_binding")
    contract = load(folder / "repair_contract.json")["flags"]
    retained = load(folder / "retained_edge_replay.json")["flags"]
    publication = load(folder / "publication_validation.json")["flags"]
    if qc["classification"] == "A":
        if not all(contract.values()) or not all(retained.values()) or not all(publication.values()):
            raise ValueError("false_A")
        for name in ("synthetic_acceptance.csv", "negative_controls.csv", "candidate_regression.csv"):
            for row in csv.DictReader(io.StringIO((folder / name).read_text())):
                if row["status"] != "passed" if "status" in row else row["blocked"] != "True":
                    raise ValueError("false_acceptance")
    attempt = folder / "local/access_attempt.json"; receipt = folder / "local/access_materialized.json"
    if qc["edges_reopened"] != int(receipt.exists()) or qc["exposure_uncertain"] != (attempt.exists() and not receipt.exists()):
        raise ValueError("access_receipt_mismatch")
    for name in NAMES:
        text = (folder / name).read_text()
        if any(token in text for token in ("/Users/", "/private/", '"carrier"', '"defenders"', '"traceback"')):
            raise ValueError("public_privacy")
    return {"status": "valid", "artifacts": len(NAMES), "historical_journal_replayed": False}
