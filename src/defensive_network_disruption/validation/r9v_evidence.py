"""Strict R9V persisted evidence and eleven-file public package."""
from __future__ import annotations

import csv
import io
from pathlib import Path

from .r9j_evidence import canonical, finite, hash_string, load, put, put_bytes, sha

NAMES = ("authority.json", "numerical_reproduction.json", "tie_invariant.json",
         "tie_maximality.json", "independent_reference.json",
         "synthetic_tie_controls.csv", "publication_collision.json",
         "publication_controls.csv", "publication_repair.json", "qc.json", "manifest.json")

SCHEMAS = {
    "authority.json": (("bindings_valid", "journal_valid", "terminal_match",
                         "traceback_match", "receipt_match"), ("journal_records",), ()),
    "numerical_reproduction.json": (("reproduced", "unchanged_route", "frame_captured",
                                      "original_preserved"), ("boundary_frames",), ("seconds",)),
    "tie_invariant.json": (("exact_pair_tie", "pair_in_global_owner_block",
                            "positive_global_maximum", "tolerance_distinct"),
                           ("pair_members", "global_owners"), ()),
    "tie_maximality.json": (("pair_equal", "globally_maximal", "third_defender_dominance",
                              "extension_available", "complete"),
                             ("cells", "dominated_cells", "unresolved_cells"), ()),
    "independent_reference.json": (("exact_inputs", "outward_bounds", "symbolic_identity",
                                     "complete"), ("cells", "subdivisions", "max_depth"), ("seconds",)),
    "publication_collision.json": (("reproduced", "first_write_valid", "second_write_blocked",
                                     "original_failure_preserved"), ("authority_writers",), ()),
    "publication_repair.json": (("single_writer", "descriptor_bound", "validators_read_only",
                                  "one_linear_review", "legacy_replay_unreachable",
                                  "original_failures_preserved", "negative_controls"),
                                 ("controls", "controls_passed"), ("seconds",)),
}

TIE_COLUMNS = ("fixture", "expected", "observed", "passed", "evidence_sha256")
PUB_COLUMNS = ("fixture", "reviews", "passed", "evidence_sha256")


def record(flags, counts, timings, *, status="unavailable", reason="not_executed"):
    return {"schema_version": 1, "status": status, "reason": reason,
            "flags": flags, "counts": counts, "timings": timings,
            "evidence_sha256": None}


def empty():
    return {name: record(dict.fromkeys(flags), dict.fromkeys(counts), dict.fromkeys(timings))
            for name, (flags, counts, timings) in SCHEMAS.items()}


def fill(records, name, *, status="complete", reason, flags=None, counts=None, timings=None):
    item = records[name]
    item.update(status=status, reason=reason)
    for key, values in (("flags", flags), ("counts", counts), ("timings", timings)):
        if values:
            if set(values) - set(item[key]):
                raise ValueError("unknown_record_field")
            item[key].update(values)


def validate_record(name, value):
    if set(value) != {"schema_version", "status", "reason", "flags", "counts", "timings", "evidence_sha256"}:
        raise ValueError("record_schema")
    if value["schema_version"] != 1 or value["status"] not in ("complete", "partial", "invalid", "unavailable"):
        raise ValueError("record_status")
    if not isinstance(value["reason"], str) or not value["reason"]:
        raise ValueError("record_reason")
    for kind, keys, expected in zip(("flags", "counts", "timings"), SCHEMAS[name],
                                    (bool, int, (int, float))):
        if set(value[kind]) != set(keys):
            raise ValueError("record_fields")
        for item in value[kind].values():
            if item is None:
                continue
            if (type(item) not in expected if isinstance(expected, tuple) else type(item) is not expected):
                raise ValueError("record_type")
            if kind != "flags" and item < 0:
                raise ValueError("record_negative")
    if not hash_string(value["evidence_sha256"]):
        raise ValueError("record_hash")
    finite(value)


def csv_bytes(rows, columns):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        if set(row) != set(columns) - {"evidence_sha256"}:
            raise ValueError("csv_row_schema")
        writer.writerow({**row, "passed": str(row["passed"]).lower(), "evidence_sha256": "{INDEX}"})
    return stream.getvalue().encode()


def close(folder, authority, records, tie_rows, publication_rows, qc):
    folder = Path(folder); local = folder / "local"
    private = {p.relative_to(local).as_posix(): sha(p) for p in sorted(local.rglob("*"))
               if p.is_file() and p.name != "private_index.json"}
    put(local / "private_index.json", {"schema_version": 1, "files": private})
    index_hash = sha(local / "private_index.json")
    for name, value in records.items():
        value["evidence_sha256"] = index_hash
        validate_record(name, value)
        put(folder / name, value)
    for name, rows, columns in (("synthetic_tie_controls.csv", tie_rows, TIE_COLUMNS),
                                ("publication_controls.csv", publication_rows, PUB_COLUMNS)):
        put_bytes(folder / name, csv_bytes(rows, columns).replace(b"{INDEX}", index_hash.encode()))
    put(folder / "qc.json", {**qc, "schema_version": 1, "private_index_sha256": index_hash})
    put(folder / "manifest.json", {"schema_version": 1, "authority": authority,
        "private_index_sha256": index_hash,
        "outputs": {name: sha(folder / name) for name in NAMES if name != "manifest.json"}})
    return publication_check(folder)


def publication_check(folder):
    folder = Path(folder); local = folder / "local"
    if {p.name for p in folder.iterdir() if p.is_file()} != set(NAMES):
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
        if Path(name).is_absolute() or ".." in Path(name).parts or sha(local / name) != expected:
            raise ValueError("private_hash")
    for name in SCHEMAS:
        value = load(folder / name); validate_record(name, value)
        if value["evidence_sha256"] != manifest["private_index_sha256"]:
            raise ValueError("record_binding")
    for name, columns in (("synthetic_tie_controls.csv", TIE_COLUMNS),
                          ("publication_controls.csv", PUB_COLUMNS)):
        raw = (folder / name).read_bytes()
        if b"\r" in raw:
            raise ValueError("csv_line_endings")
        reader = csv.DictReader(io.StringIO(raw.decode()))
        if tuple(reader.fieldnames or ()) != columns:
            raise ValueError("csv_schema")
        for row in reader:
            if None in row or row["evidence_sha256"] != manifest["private_index_sha256"]:
                raise ValueError("csv_binding")
    qc = load(folder / "qc.json")
    expected_qc = {"schema_version", "status", "execution_valid", "numerical", "publication",
                   "readiness", "states_reopened", "edges_reopened", "exposure_uncertain",
                   "private_index_sha256"}
    if set(qc) != expected_qc or qc["schema_version"] != 1:
        raise ValueError("qc_schema")
    if qc["numerical"] not in ("NA", "NB", "NC", "ND", "NE", "NF") or qc["publication"] not in ("PA", "PB", "PC", "PD"):
        raise ValueError("classification")
    if qc["readiness"] not in (1, 2, 3, 4) or type(qc["execution_valid"]) is not bool:
        raise ValueError("qc_values")
    if qc["publication"] == "PA" and not all(load(folder / "publication_repair.json")["flags"].values()):
        raise ValueError("false_publication_acceptance")
    if qc["numerical"] != "NF" and not load(folder / "numerical_reproduction.json")["flags"]["reproduced"]:
        raise ValueError("false_numerical_classification")
    attempt = local / "access_attempt.json"; receipt = local / "access_materialized.json"
    if qc["edges_reopened"] != int(receipt.exists()) or qc["states_reopened"] != int(receipt.exists()):
        raise ValueError("access_count")
    if qc["exposure_uncertain"] != (attempt.exists() and not receipt.exists()):
        raise ValueError("exposure_uncertainty")
    for name in NAMES:
        text = (folder / name).read_text()
        if any(token in text for token in ("/Users/", "/private/", '"carrier"', '"defenders"', '"traceback"')):
            raise ValueError("public_privacy")
    return {"valid": True, "files": len(NAMES), "numerical": qc["numerical"],
            "publication": qc["publication"], "readiness": qc["readiness"]}
