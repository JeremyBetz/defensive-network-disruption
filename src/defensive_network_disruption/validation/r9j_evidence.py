"""Standard-library R9J persistence and exact publication schemas."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import traceback

START = "137b7cc2109fc18f1efe203c715484a547a287c6"
TAG = "f00690c05d8c1c6db308a65bd311c43f9a8ef2fa"
PROTOCOL = "docs/protocols/phase_14r9j_r9i_blocker_diagnosis.md"
NAMES = ("authority.json", "numerical_reproduction.json", "partition_diagnosis.json",
         "interval_localization.csv", "independent_reference.json", "candidate_path_comparison.csv",
         "publication_complexity.json", "replay_benchmarks.csv", "validator_equivalence.json",
         "retained_journal_review.json", "runtime_summary.json", "qc.json", "manifest.json")
SCHEMAS = {
    "authority.json": (("committed_authority", "environment", "retained_inputs"), (), ()),
    "numerical_reproduction.json": (("reproduced", "production_converged", "gate_inputs_captured", "warning_evidence_captured"),
                                    ("accepted_resolution", "adaptive_calls", "warnings", "certified_pieces"), ()),
    "partition_diagnosis.json": (("valid", "onsets_present", "switches_present", "ties_preserved", "witnesses_valid", "routing_valid"),
                                ("pieces", "onsets", "switches", "ties", "bounded_pieces"), ()),
    "independent_reference.json": (("eligible", "production_accurate", "piecewise_accurate", "piecewise_inaccurate", "onset_accurate", "onset_inaccurate", "scalar_oracle"),
                                  ("leaves", "smooth_leaves"), ("seconds",)),
    "publication_complexity.json": (("prefix_replay", "attempt_rescan", "cubic_preparation_work", "linear_replacement", "no_runtime_extrapolation"),
                                    ("small_probe_records", "measured_prefix_visits", "predicted_prefix_visits", "measured_attempt_scans", "predicted_attempt_scans"), ()),
    "validator_equivalence.json": (("complete_objects_equal", "prefixes_equal", "negative_controls", "persisted_packages", "legacy_hash_meaning"),
                                  ("controls", "prefixes", "rejections"), ()),
    "retained_journal_review.json": (("raw_hash", "chain_valid", "counts_match", "selected_receipt", "failure_match", "historical_complete_snapshot_available"),
                                    ("records", "states_opened", "edges_opened", "states_completed", "edges_completed", "field_started", "field_completed", "unresolved_edges"),
                                    ("seconds",)),
    "runtime_summary.json": (("exclusive_accounting", "no_overlapping_sum"), (),
                            ("governed_wall", "numerical_wall", "publication_wall", "numerical_exclusive", "publication_exclusive", "io", "unattributed")),
}
CSV_SCHEMAS = {
    "interval_localization.csv": ("ordinal", "kind", "status", "accurate", "inaccurate", "reason", "evidence_sha256"),
    "candidate_path_comparison.csv": ("candidate", "status", "gate", "converged", "accepted_resolution", "reason", "evidence_sha256"),
    "replay_benchmarks.csv": ("nominal_records", "actual_records", "states", "old_status", "old_seconds", "new_seconds", "equal", "prefix_visits", "attempt_scans", "reason", "evidence_sha256"),
}


def finite(value):
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("nonfinite_evidence")
    if isinstance(value, dict):
        for k, v in value.items():
            if not isinstance(k, str): raise ValueError("string_keys_required")
            finite(v)
    elif isinstance(value, (list, tuple)):
        for v in value: finite(v)


def canonical(value):
    finite(value)
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)+"\n").encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def safe(path):
    path = Path(path)
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise PermissionError("symlink_rejected")
    return path


def sha(path):
    h = hashlib.sha256()
    with safe(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


def put_bytes(path, raw):
    path = safe(path); path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name("."+path.name+".pending")
    if path.exists(): raise FileExistsError("immutable_evidence_exists")
    with temp.open("xb") as f:
        f.write(raw); f.flush(); os.fsync(f.fileno())
    os.link(temp, path); temp.unlink()
    fd = os.open(path.parent, os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)


def put(path, value):
    put_bytes(path, canonical(value))


def load(path):
    def pairs(items):
        out = {}
        for k, v in items:
            if k in out: raise ValueError("duplicate_key")
            out[k] = v
        return out
    result = json.loads(safe(path).read_bytes(), object_pairs_hook=pairs,
                        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite_json")))
    finite(result)
    return result


def emergency(path, error, stage, context=None):
    put(path, {"schema_version": 1, "exception": type(error).__name__,
               "message": str(error), "traceback": "".join(traceback.format_exception(error)),
               "stage": stage, "context": context})


def empty_public():
    return {name: {"schema_version": 1, "status": "unavailable", "reason": "not_executed",
                   "flags": dict.fromkeys(flags), "counts": dict.fromkeys(counts),
                   "timings": dict.fromkeys(timings), "evidence_sha256": None}
            for name, (flags, counts, timings) in SCHEMAS.items()}


def record(public, name, *, flags=None, counts=None, timings=None, reason=None):
    item = public[name]
    for key, values in (("flags", flags), ("counts", counts), ("timings", timings)):
        if values:
            if set(values)-set(item[key]): raise ValueError("unexpected_public_field")
            item[key].update(values)
    item.update(status="available", reason=reason)


def hash_string(value):
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def validate_record(name, item):
    if set(item) != {"schema_version", "status", "reason", "flags", "counts", "timings", "evidence_sha256"}:
        raise ValueError("public_record_schema")
    if item["schema_version"] != 1 or item["status"] not in ("available", "unavailable"):
        raise ValueError("public_record_status")
    if item["reason"] is not None and not isinstance(item["reason"], str): raise ValueError("reason_type")
    if item["status"] == "unavailable" and not item["reason"]: raise ValueError("unavailable_reason")
    for kind, keys, expected in zip(("flags", "counts", "timings"), SCHEMAS[name], (bool, int, (int, float))):
        if set(item[kind]) != set(keys): raise ValueError("public_fields")
        for value in item[kind].values():
            if value is not None:
                if (type(value) not in expected if isinstance(expected, tuple) else type(value) is not expected):
                    raise ValueError("public_value_type")
                if kind != "flags" and value < 0: raise ValueError("negative_count_time")
    if not hash_string(item["evidence_sha256"]): raise ValueError("evidence_hash")
    finite(item)


def close(folder, public, csv_rows, qc, authority):
    folder = Path(folder)
    private = {p.relative_to(folder/"local").as_posix(): sha(p) for p in sorted((folder/"local").rglob("*")) if p.is_file() and p.name != "private_index.json"}
    put(folder/"local/private_index.json", {"schema_version": 1, "files": private})
    index_hash = sha(folder/"local/private_index.json")
    for name, item in public.items():
        item["evidence_sha256"] = index_hash
        validate_record(name, item); put(folder/name, item)
    for name, columns in CSV_SCHEMAS.items():
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in csv_rows.get(name, []):
            writer.writerow({**row, "evidence_sha256": index_hash})
        put_bytes(folder/name, stream.getvalue().encode())
    qc = {**qc, "schema_version": 1, "private_index_sha256": index_hash}
    put(folder/"qc.json", qc)
    put(folder/"manifest.json", {"schema_version": 1, "status": qc["status"], "start": START,
        "authority": authority, "private_index_sha256": index_hash,
        "outputs": {n: sha(folder/n) for n in NAMES if n != "manifest.json"}})
    return publication_check(folder)


def publication_check(folder):
    folder = Path(folder); m = load(folder/"manifest.json"); q = load(folder/"qc.json")
    if set(m) != {"schema_version", "status", "start", "authority", "private_index_sha256", "outputs"}:
        raise ValueError("manifest_schema")
    if set(q) != {"schema_version", "status", "execution_valid", "numerical", "publication", "readiness",
                  "states_reopened", "edges_reopened", "exposure_uncertain", "private_index_sha256"}:
        raise ValueError("qc_schema")
    if m["schema_version"] != 1 or q["schema_version"] != 1 or m["start"] != START: raise ValueError("schema_version")
    if q["status"] not in ("complete", "partial", "invalid") or m["status"] != q["status"]: raise ValueError("status")
    if type(q["execution_valid"]) is not bool or type(q["exposure_uncertain"]) is not bool: raise ValueError("qc_boolean")
    if q["execution_valid"] != (q["status"] != "invalid"): raise ValueError("execution_validity")
    if q["numerical"] not in ("NA", "NB", "NC", "ND", "NE", "NF") or q["publication"] not in ("PA", "PB", "PC", "PD"):
        raise ValueError("classification")
    if type(q["readiness"]) is not int or q["readiness"] not in (1, 2, 3, 4): raise ValueError("readiness")
    if q["readiness"] != (3 if q["publication"] == "PA" else 4): raise ValueError("unrepaired_numerical_contract")
    if any(type(q[k]) is not int or q[k] not in (0, 1) for k in ("states_reopened", "edges_reopened")) or q["states_reopened"] != q["edges_reopened"]:
        raise ValueError("access_count")
    if set(m["outputs"]) != set(NAMES)-{"manifest.json"}: raise ValueError("artifact_set")
    if {p.name for p in folder.iterdir() if p.is_file()} != set(NAMES): raise ValueError("extra_artifact")
    for name, expected in m["outputs"].items():
        if not hash_string(expected) or sha(folder/name) != expected: raise ValueError("artifact_hash")
    index = folder/"local/private_index.json"
    if sha(index) != q["private_index_sha256"] or m["private_index_sha256"] != q["private_index_sha256"]:
        raise ValueError("private_index_hash")
    indexed = load(index)
    if set(indexed) != {"schema_version", "files"} or indexed["schema_version"] != 1: raise ValueError("index_schema")
    for name, expected in indexed["files"].items():
        if Path(name).is_absolute() or ".." in Path(name).parts or sha(folder/"local"/name) != expected: raise ValueError("private_file_hash")
    for name in SCHEMAS:
        value = load(folder/name); validate_record(name, value)
        if value["evidence_sha256"] != q["private_index_sha256"]: raise ValueError("record_binding")
    for name, columns in CSV_SCHEMAS.items():
        raw = (folder/name).read_bytes()
        if b"\r" in raw: raise ValueError("csv_line_endings")
        reader = csv.DictReader(io.StringIO(raw.decode()))
        if reader.fieldnames != list(columns): raise ValueError("csv_schema")
        for row in reader:
            if None in row or row["evidence_sha256"] != q["private_index_sha256"]: raise ValueError("csv_binding")
    retained = load(folder/"retained_journal_review.json")["flags"]
    equivalence = load(folder/"validator_equivalence.json")["flags"]
    if q["publication"] == "PA" and (not all(equivalence.values()) or not all(retained[k] for k in retained if k != "historical_complete_snapshot_available")):
        raise ValueError("false_publication_acceptance")
    ref = load(folder/"independent_reference.json")["flags"]
    if q["numerical"] in ("NA", "NB"):
        if not load(folder/"numerical_reproduction.json")["flags"]["reproduced"] or not ref["eligible"] or not ref["production_accurate"]:
            raise ValueError("false_numerical_accuracy")
        if q["numerical"] == "NA" and not (ref["piecewise_accurate"] and ref["onset_inaccurate"]):
            raise ValueError("false_NA")
        if q["numerical"] == "NB" and not (ref["piecewise_inaccurate"] and ref["onset_accurate"]):
            raise ValueError("false_NB")
    attempt = folder/"local/access_attempt.json"; receipt = folder/"local/access_materialized.json"
    if q["edges_reopened"] != int(receipt.exists()) or q["exposure_uncertain"] != (attempt.exists() and not receipt.exists()):
        raise ValueError("access_receipt_mismatch")
    for name in NAMES:
        raw = (folder/name).read_text()
        if any(token in raw for token in ('/Users/', '/private/', '"defenders"', '"carrier"', '"traceback"')):
            raise ValueError("public_privacy")
    return {"status": "valid", "artifacts": len(NAMES), "historical_journal_replayed": False}
