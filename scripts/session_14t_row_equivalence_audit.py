#!/usr/bin/env python3
"""Governed one-row representation audit for Session 14R preparation."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np

from defensive_network_disruption.data.representation_projection import project_line
from defensive_network_disruption.data.row_equivalence import (
    compare_exact, historical_json_bytes, public_difference_rows,
    schema_fingerprint, semantic_flags, sha256_bytes, type_category,
)


START = "a337e26b9d4f297d626e13c77366dcd81b097d84"
TAG = "f00690c05d8c1c6db308a65bd311c43f9a8ef2fa"
PROTOCOL = Path("docs/protocols/phase_14t_row_equivalence_audit.md")
OUT = Path("outputs/continuous_occlusion_row_equivalence")
LOCAL = OUT / "local"
R14R = Path("outputs/continuous_occlusion_retry")
R14S = Path("outputs/continuous_occlusion_max_warning_diagnosis")
POPULATION = Path("outputs/receiver_ranking_m0_m1/local/population.jsonl")
PREPARED = R14R / "local/prepared.jsonl"
EXPECTED = {
    "session14r_manifest": "8a639f7a2b29a6aec026e176d80d8901b28839b0d2091dd0256751d77b6f70ed",
    "session14s_manifest": "9bdb96a97e447f834068ca941453d537082a91fcb9653fef1c428ddadc78a61b",
    "canonical_population": "cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d",
    "prepared_population": "15a809060f0ba4a8cb3790011dab8008db3dad6e931c287ccb395f61ef1530b0",
}
CODE = (
    Path("scripts/session_14t_row_equivalence_audit.py"),
    Path("src/defensive_network_disruption/data/row_equivalence.py"),
    Path("tests/test_session14t_equivalence.py"),
)
JSON_PUBLIC = ("authority_summary.json", "schema_comparison.json",
               "environment_comparison.json", "qc.json")
CSV_PUBLIC = ("field_comparison.csv", "pipeline_stage_fingerprints.csv")
PUBLIC = (*JSON_PUBLIC, *CSV_PUBLIC)
CSV_FIELDS = {
    "field_comparison.csv": ("path", "category", "left_type", "right_type", "count",
                             "all_float64_bits_equal", "all_signed_zero_equal",
                             "maximum_numeric_absolute_difference"),
    "pipeline_stage_fingerprints.csv": ("stage", "representation", "sha256",
                                        "byte_count", "matches_preserved_prepared_bytes"),
}


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def safe(relative: Path | str) -> Path:
    relative = Path(relative)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("unsafe_path")
    path = ROOT / relative
    if any(item.is_symlink() for item in (path, *path.parents)):
        raise ValueError("symlink_rejected")
    if not path.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError("path_escape")
    return path


def digest(relative: Path | str) -> str:
    handle = hashlib.sha256()
    with safe(relative).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            handle.update(block)
    return handle.hexdigest()


def no_duplicates(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate_json_key")
        value[key] = item
    return value


def read_json(relative: Path | str):
    return json.loads(safe(relative).read_text(), object_pairs_hook=no_duplicates,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite_json")))


def encoded(value) -> str:
    return json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"


def atomic_text(relative: Path | str, content: str) -> None:
    destination = safe(relative)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError("output_exists")
    temporary = destination.with_name("." + destination.name + ".tmp")
    with temporary.open("x", encoding="utf-8", newline="") as stream:
        stream.write(content)
    temporary.replace(destination)


def write_json(name: str, value) -> None:
    atomic_text(OUT / name, encoded(value))


def write_csv(name: str, rows: list[dict]) -> None:
    destination = safe(OUT / name)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError("output_exists")
    temporary = destination.with_name("." + destination.name + ".tmp")
    with temporary.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS[name], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(destination)


def write_private(name: str, value) -> None:
    atomic_text(LOCAL / name, encoded(value))


def committed(relative: Path | str) -> None:
    if safe(relative).read_bytes() != subprocess.check_output(
            ["git", "show", f"HEAD:{relative}"], cwd=ROOT):
        raise ValueError("uncommitted_authority")


def one_line(relative: Path | str, ordinal: int) -> str:
    if ordinal != 1:
        raise PermissionError("only_ordinal_1_authorized")
    found = None
    with safe(relative).open(encoding="utf-8") as stream:
        for index, line in enumerate(stream):
            if index == ordinal:
                found = line
                break
    if found is None:
        raise ValueError("ordinal_1_unavailable")
    return found


def input_hashes() -> dict[str, str]:
    return {
        "session14r_manifest": digest(R14R / "manifest.json"),
        "session14s_manifest": digest(R14S / "manifest.json"),
        "canonical_population": digest(POPULATION),
        "prepared_population": digest(PREPARED),
    }


def verify_inputs() -> None:
    if input_hashes() != EXPECTED:
        raise ValueError("input_authority_changed")
    if read_json(R14S / "qc.json")["failure"] != "ValueError":
        raise ValueError("session14s_failure_changed")


def preservation() -> None:
    git("merge-base", "--is-ancestor", START, "HEAD")
    if git("rev-parse", "v0.1.0^{}") != TAG:
        raise ValueError("release_tag_changed")
    changed = set(git("diff", "--name-only", START).splitlines())
    allowed = {str(PROTOCOL), *map(str, CODE),
               "docs/session_14t_row_equivalence_audit.md", "docs/research_log.md"}
    if any(path not in allowed and not path.startswith(str(OUT) + "/") for path in changed):
        raise ValueError("historical_file_changed")
    original = subprocess.check_output(["git", "show", f"{START}:docs/research_log.md"], cwd=ROOT)
    if not safe("docs/research_log.md").read_bytes().startswith(original):
        raise ValueError("research_log_rewritten")


def code_hashes() -> dict[str, str]:
    return {str(path): digest(path) for path in CODE}


def preflight() -> None:
    if git("status", "--porcelain"):
        raise ValueError("clean_tree_required")
    committed(PROTOCOL)
    for path in CODE:
        committed(path)
    if subprocess.run(["git", "check-ignore", "-q", str(LOCAL / "probe")], cwd=ROOT).returncode:
        raise ValueError("local_storage_not_ignored")
    preservation()
    verify_inputs()
    print("Session 14t preflight passed; ordinal 1 not opened")


def ledger(status: str) -> None:
    path = safe(LOCAL / "access.jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps({"time": datetime.now(timezone.utc).isoformat(),
                                 "stage": "audit", "status": status,
                                 "head": git("rev-parse", "HEAD")}) + "\n")


def claim_marker() -> None:
    marker = safe(LOCAL / "audit.marker")
    marker.parent.mkdir(parents=True, exist_ok=True)
    with marker.open("x", encoding="utf-8") as stream:
        stream.write(git("rev-parse", "HEAD") + "\n")


def private_difference(item) -> dict:
    return {
        "path": item.path, "category": item.category,
        "left_type": item.left_type, "right_type": item.right_type,
        "left_value": item.left_value, "right_value": item.right_value,
        "absolute_difference": item.absolute_difference,
        "bit_equal": item.bit_equal, "signed_zero_equal": item.signed_zero_equal,
    }


def environment_record() -> dict:
    recorded = read_json(R14R / "manifest.json")["environment"]
    current = {"python": platform.python_version(), "numpy": np.__version__,
               "lock": digest("uv.lock")}
    synthetic = {"python_tuple_list_unequal": {"x": (1.0,)} != {"x": [1.0]},
                 "historical_serialization_equal": historical_json_bytes(
                     {"x": (1.0,)}) == historical_json_bytes({"x": [1.0]})}
    return {
        "schema_version": 1, "current": current,
        "session14r_recorded": {key: recorded[key] for key in ("python", "numpy", "lock")},
        "exact_environment_match": current == {key: recorded[key] for key in current},
        "synthetic_equivalent_behavior": synthetic,
        "environment_sensitivity_detected": not all(synthetic.values()),
        "dependency_changes": False,
    }


def classify(flags: dict, serialized_equal: bool, environment_sensitive: bool) -> tuple[str, int]:
    if environment_sensitive:
        return "F", 4
    if (not flags["python_equality"] and flags["container_or_order_difference_count"] > 0
            and flags["structural_identity"] and flags["numerical_identity"]
            and serialized_equal):
        return "B", 1
    if (not serialized_equal and flags["structural_identity"] and flags["numerical_identity"]
            and flags["container_or_order_difference_count"] == 0):
        return "A", 1
    if not flags["numerical_identity"]:
        return "C", 2
    if not flags["structural_identity"]:
        return "D", 2
    return "H", 4


def close_manifest(status: str) -> None:
    existing = [name for name in PUBLIC if safe(OUT / name).exists()]
    manifest = {
        "schema_version": 1, "status": status, "start": START,
        "protocol_sha256": digest(PROTOCOL), "implementation": code_hashes(),
        "sources": EXPECTED, "outputs": {name: digest(OUT / name) for name in existing},
        "unavailable": [name for name in PUBLIC if name not in existing],
    }
    write_json("manifest.json", manifest)


def audit() -> None:
    preflight()
    if safe(OUT / "manifest.json").exists():
        raise FileExistsError("closed_no_rerun")
    claim_marker()
    ledger("started")
    try:
        canonical_text = one_line(POPULATION, 1)
        prepared_text = one_line(PREPARED, 1)
        key, reconstructed = project_line(canonical_text)
        decoded = json.loads(prepared_text, object_pairs_hook=no_duplicates,
                             parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite_json")))
        if not isinstance(decoded, dict) or not isinstance(reconstructed, dict):
            raise ValueError("prepared_row_not_mapping")
        alias, event_key = key
        neutral_state = f"{alias}_state_{2:06d}"
        private_key_hash = sha256_bytes((alias + "\0" + event_key).encode())
        historical_equal = reconstructed == decoded
        reproduction_bytes = historical_json_bytes(reconstructed)
        preserved_bytes = prepared_text.encode("utf-8")
        serialized_equal = reproduction_bytes == preserved_bytes
        differences = compare_exact(reconstructed, decoded)
        flags = semantic_flags(reconstructed, decoded, serialized_equal)
        environment = environment_record()

        stages = [
            ("canonical_raw_line", "json_bytes", canonical_text.encode()),
            ("restricted_projection", "historical_sorted_json", historical_json_bytes(reconstructed)),
            ("python_prepared_object", "schema", schema_fingerprint(reconstructed).encode()),
            ("session14r_sorted_json", "json_bytes", reproduction_bytes),
            ("preserved_prepared_line", "json_bytes", preserved_bytes),
            ("json_decoded_comparison_object", "historical_sorted_json", historical_json_bytes(decoded)),
        ]
        fingerprints = [{
            "stage": name, "representation": representation,
            "sha256": sha256_bytes(payload), "byte_count": len(payload),
            "matches_preserved_prepared_bytes": payload == preserved_bytes,
        } for name, representation, payload in stages]
        category, readiness = classify(flags, serialized_equal,
                                       environment["environment_sensitivity_detected"])

        write_private("exact_comparison.json", {
            "neutral_state": neutral_state, "integrity_key_sha256": private_key_hash,
            "canonical_raw_sha256": sha256_bytes(canonical_text.encode()),
            "preserved_raw_sha256": sha256_bytes(preserved_bytes),
            "canonical_key": list(key), "reconstructed": reconstructed, "decoded": decoded,
            "differences": [private_difference(item) for item in differences],
            "historical_python_equality": historical_equal,
            "historical_serialization_bytes_equal": serialized_equal,
        })
        write_json("authority_summary.json", {
            "schema_version": 1, "status": "closed", "zero_based_row_ordinal": 1,
            "neutral_state_key": neutral_state, "integrity_key_sha256": private_key_hash,
            "sources": EXPECTED, "canonical_line_sha256": sha256_bytes(canonical_text.encode()),
            "preserved_line_sha256": sha256_bytes(preserved_bytes),
            "historical_python_dictionary_equality": historical_equal,
            "historical_serialization_bytes_equal": serialized_equal,
            "classification": category, "readiness": readiness,
        })
        write_json("schema_comparison.json", {
            "schema_version": 1, "left_schema_sha256": schema_fingerprint(reconstructed),
            "right_schema_sha256": schema_fingerprint(decoded),
            "first_divergence_path": (public_difference_rows(differences)[0]["path"]
                                      if differences else None),
            "mapping_field_names_equal": set(reconstructed) == set(decoded),
            "mapping_order_equal": tuple(reconstructed) == tuple(decoded),
            "missing_or_optional_key_difference_count": sum(
                item.category == "mapping_keys" for item in differences),
            "difference_count": len(differences), **flags,
        })
        write_csv("field_comparison.csv", public_difference_rows(differences))
        write_csv("pipeline_stage_fingerprints.csv", fingerprints)
        write_json("environment_comparison.json", environment)
        write_json("qc.json", {
            "schema_version": 1, "status": "closed", "empirical_rows_opened": 1,
            "additional_rows_opened": 0, "field_evaluations": 0, "integration_calls": 0,
            "models_loaded": False, "targets_or_outcomes_decoded": False,
            "prohibited_access": False, "evidence_hash_closed_before_interpretation": True,
            "classification": category, "readiness": readiness, "failure": None,
        })
        close_manifest("closed")
        ledger("closed")
        print(f"Session 14t evidence closed: classification {category}, readiness {readiness}")
    except Exception as error:
        write_private("failure.json", {"type": type(error).__name__, "message": str(error),
                                        "traceback": traceback.format_exc()})
        if not safe(OUT / "qc.json").exists():
            write_json("qc.json", {"schema_version": 1, "status": "unresolved",
                "empirical_rows_opened": 1, "additional_rows_opened": 0,
                "field_evaluations": 0, "integration_calls": 0, "models_loaded": False,
                "targets_or_outcomes_decoded": False, "prohibited_access": False,
                "evidence_hash_closed_before_interpretation": True,
                "classification": "H", "readiness": 4, "failure": type(error).__name__})
        close_manifest("unresolved")
        ledger("failed")
        raise


def finite(value) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("nonfinite_public_value")
    if isinstance(value, dict):
        for item in value.values():
            finite(item)
    elif isinstance(value, list):
        for item in value:
            finite(item)


def publication_check() -> None:
    preservation()
    verify_inputs()
    for path in (PROTOCOL, *CODE):
        committed(path)
    manifest = read_json(OUT / "manifest.json")
    required = {"schema_version", "status", "start", "protocol_sha256",
                "implementation", "sources", "outputs", "unavailable"}
    if set(manifest) != required or manifest["protocol_sha256"] != digest(PROTOCOL):
        raise ValueError("manifest_authority")
    if manifest["implementation"] != code_hashes() or manifest["sources"] != EXPECTED:
        raise ValueError("manifest_binding")
    if set(manifest["outputs"]) | set(manifest["unavailable"]) != set(PUBLIC):
        raise ValueError("manifest_membership")
    for name, expected in manifest["outputs"].items():
        if digest(OUT / name) != expected:
            raise ValueError("output_hash_changed")
        text = safe(OUT / name).read_text()
        for forbidden in ("/Users/", "/private/", "event_id", "carrier_xy", "candidate_xy",
                          "defender_xy", "target_index", "access_token", "X-Amz-Signature"):
            if forbidden in text:
                raise ValueError("publication_boundary")
        if name.endswith(".json"):
            finite(read_json(OUT / name))
        else:
            with safe(OUT / name).open(newline="") as stream:
                reader = csv.DictReader(stream)
                if tuple(reader.fieldnames or ()) != CSV_FIELDS[name]:
                    raise ValueError("csv_schema")
                list(reader)
    qc = read_json(OUT / "qc.json")
    if qc["empirical_rows_opened"] != 1 or qc["additional_rows_opened"] != 0:
        raise ValueError("row_scope")
    print(f"Session 14t publication checks passed: {manifest['status']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "audit", "publication-check"))
    command = parser.parse_args().command
    {"preflight": preflight, "audit": audit,
     "publication-check": publication_check}[command]()


if __name__ == "__main__":
    main()
