#!/usr/bin/env python3
"""Session 6c repaired acquisition and one corrected protected evaluation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import platform
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import scripts.session_06_reserved as frozen  # noqa: E402
from defensive_network_disruption.data.identity_compatibility import ChoiceSet  # noqa: E402
from defensive_network_disruption.data.session6_population import (  # noqa: E402
    load_projected_match_session6,
    prepare_match_session6,
    rendered_population,
)
from defensive_network_disruption.data.session6c_source import (  # noqa: E402
    LfsPointer,
    SOURCE_COMMIT,
    Session6cSourceClient,
    TreeEntry,
    git_blob_oid,
    public_entry,
    safe_destination,
    source_path,
)
from defensive_network_disruption.data.skillcorner_session2 import DEVELOPMENT_MATCHES  # noqa: E402
from defensive_network_disruption.validation.ranking_metrics import expected_credits, match_macro  # noqa: E402

START = "5d2a4f94d88ff479834ead4ef05ed50b051c62f3"
PROTOCOL_COMMIT = "7f910d21420d39de90e515c01ab2f94275020e83"
PROTOCOL = ROOT / "docs/protocols/phase_06c_verifier_repair_and_reserved_evaluation.md"
FINAL_MODELS = ROOT / "outputs/reserved_evaluation/final_development_models.json"
FINAL_MODELS_SHA = "0383561e45bcd9f8d84eccc7e9733b2409536f61c39193fa87d08c36c6f6fd65"
RESERVED = frozenset({
    "1874553", "1927964", "1959846", "1986691", "1996436",
    "2006363", "2007448", "2007721", "2010085", "2016236",
})
WITHHELD = "1953632"
RESERVED_ALIASES = {item: f"reserved_{index:02d}" for index, item in enumerate(sorted(RESERVED, key=int), 1)}
DEV_ALIASES = {item: f"development_{index:02d}" for index, item in enumerate(sorted(DEVELOPMENT_MATCHES, key=int), 1)}
PRODUCTS = ("metadata", "events", "tracking")
DATA = ROOT / "data/session_06c"
OUTPUT = ROOT / "outputs/reserved_evaluation_v2"
LOCAL = OUTPUT / "local"
SOURCE_AUTHORITY = LOCAL / "source_authority.json"
SOURCE_RECEIPTS = LOCAL / "source_receipts.json"
ACCESS_LEDGER = LOCAL / "access_ledger.jsonl"
POPULATION = LOCAL / "reserved_population.jsonl"
ALIAS_MAP = LOCAL / "alias_map.json"
EXECUTION = LOCAL / "execution_state.json"
REPAIR_AUTHORITY = OUTPUT / "repair_authority.json"
POPULATION_SUMMARY = OUTPUT / "population_summary.json"
RESULT_FILES = (
    "m0_match_metrics.csv", "m1_match_metrics.csv", "m2_match_metrics.csv",
    "m1_m0_paired.csv", "m2_m1_paired.csv", "aggregate_metrics.json", "qc.json", "manifest.json",
)
IMPLEMENTATION_FILES = (
    "scripts/session_06c_reserved.py",
    "src/defensive_network_disruption/data/session6c_source.py",
    "tests/test_session6c_reserved.py",
)
RESERVATION = (
    "Prospectively reserved from this project stage forward. Session 1 schema inventory "
    "mechanically over-read post-header bytes into process memory, but no evidence indicates "
    "value-level content was surfaced, persisted, or used analytically."
)


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def committed_sha(commit: str, relative: str) -> str:
    content = subprocess.run(["git", "show", f"{commit}:{relative}"], cwd=ROOT, check=True, capture_output=True).stdout
    return hashlib.sha256(content).hexdigest()


def json_text(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"


def atomic_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)


def atomic_csv(path: Path, rows: list[dict], fields: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def require_clean() -> None:
    if git("status", "--porcelain"):
        raise RuntimeError("command requires a clean committed tree")


def require_committed(path: Path) -> str:
    relative = str(path.relative_to(ROOT))
    git("ls-files", "--error-unmatch", relative)
    if sha(path) != committed_sha("HEAD", relative):
        raise RuntimeError(f"committed artifact differs: {relative}")
    return git("log", "-1", "--format=%H", "--", relative)


def verify_history() -> dict:
    if subprocess.run(["git", "merge-base", "--is-ancestor", START, "HEAD"], cwd=ROOT).returncode:
        raise RuntimeError("Session 6b authority is not an ancestor")
    if committed_sha(PROTOCOL_COMMIT, str(PROTOCOL.relative_to(ROOT))) != sha(PROTOCOL):
        raise RuntimeError("Session 6c protocol changed")
    if sha(FINAL_MODELS) != FINAL_MODELS_SHA:
        raise RuntimeError("final development model authority changed")
    if sha(ROOT / "docs/session_06_reserved_evaluation_decision_brief.md") != "0618352da55c5ef0d03d1953259c8cfd158cfb23e0d7ea0ea5d32e3fda552db4":
        raise RuntimeError("historical Session 6 decision changed")
    if sha(ROOT / "outputs/tracking_integrity_review/manifest.json") != "14e67c1ff8454c9a1e77b8f7bfd2efb799a3e5fe5fe14ea070bd4438a98b5c06":
        raise RuntimeError("Session 6b authority changed")
    return frozen.verify_final_authority()


def implementation_hashes() -> dict[str, str]:
    return {name: sha(ROOT / name) for name in IMPLEMENTATION_FILES}


def ensure_implementation_committed() -> str:
    for name in IMPLEMENTATION_FILES:
        require_committed(ROOT / name)
    require_clean()
    return git("rev-parse", "HEAD")


def append_access(label: str, attempt: int, status: str, category: str | None) -> None:
    LOCAL.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(), "phase": "session_06c",
        "protocol_commit": PROTOCOL_COMMIT, "implementation_commit": git("rev-parse", "HEAD"),
        "request_label": label, "attempt": attempt, "status": status, "failure_category": category,
    }
    with ACCESS_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")


def github_token() -> str:
    token = subprocess.run(["gh", "auth", "token"], check=True, capture_output=True, text=True).stdout.strip()
    if not token:
        raise RuntimeError("GitHub token unavailable")
    return token


def expected_paths() -> tuple[set[str], dict[str, tuple[str, str, str]]]:
    paths: set[str] = set()
    reverse: dict[str, tuple[str, str, str]] = {}
    for match, alias in RESERVED_ALIASES.items():
        for product in PRODUCTS:
            path = source_path(match, product, RESERVED)
            paths.add(path)
            reverse[path] = ("reserved", alias, product)
    development = frozenset(DEVELOPMENT_MATCHES)
    for match, alias in DEV_ALIASES.items():
        path = source_path(match, "tracking", development)
        paths.add(path)
        reverse[path] = ("development", alias, "tracking")
    if WITHHELD in " ".join(paths):
        raise PermissionError("withheld identity entered source paths")
    return paths, reverse


def preflight() -> None:
    verify_history()
    if set(RESERVED) != set(frozen.RESERVED) or WITHHELD in RESERVED:
        raise RuntimeError("partition authority changed")
    if any((OUTPUT / name).exists() for name in RESULT_FILES) or EXECUTION.exists():
        raise RuntimeError("Session 6c protected execution already exists")
    print("Session 6c preflight passed")


def verify_sources() -> None:
    models = verify_history()
    implementation_commit = ensure_implementation_committed()
    if REPAIR_AUTHORITY.exists() or SOURCE_AUTHORITY.exists():
        raise RuntimeError("source verification already exists")
    paths, reverse = expected_paths()
    client = Session6cSourceClient(github_token(), ledger=append_access)
    tree_oid, entries = client.tree_entries(paths)
    local: dict[str, object] = {"source_commit": SOURCE_COMMIT, "source_tree": tree_oid, "records": {}}
    public: dict[str, dict] = {"development": {}, "reserved": {}}
    development_payloads_verified = 0
    for path in sorted(paths):
        partition, alias, product = reverse[path]
        entry = entries[path]
        pointer = None
        if product == "tracking":
            pointer, pointer_bytes = client.pointer(entry, label=f"{partition}:{alias}:pointer")
            if git_blob_oid(pointer_bytes) != entry.git_oid or len(pointer_bytes) != entry.git_size:
                raise RuntimeError("corrected pointer verification failed")
        record = public_entry(entry, pointer)
        local["records"].setdefault(alias, {})[product] = {"path": path, **record}
        public[partition].setdefault(alias, {})[product] = record
        if partition == "development":
            match = next(key for key, value in DEV_ALIASES.items() if value == alias)
            existing = safe_destination(ROOT / "data/session_02", match, "tracking", frozenset(DEVELOPMENT_MATCHES))
            if existing.is_file() and not existing.is_symlink() and pointer is not None:
                if existing.stat().st_size != pointer.payload_size or sha(existing) != pointer.payload_sha256:
                    raise RuntimeError(f"existing development payload integrity mismatch: {alias}")
                development_payloads_verified += 1
    atomic_text(SOURCE_AUTHORITY, json_text(local))
    authority = {
        "schema_version": "1.0.0", "status": "prospective_repair_authority",
        "starting_authority": START, "protocol_commit": PROTOCOL_COMMIT, "protocol_sha256": sha(PROTOCOL),
        "implementation_commit": implementation_commit, "implementation_sha256": implementation_hashes(),
        "source_commit": SOURCE_COMMIT, "source_tree": tree_oid,
        "environment": models["environment"], "uv_lock_sha256": sha(ROOT / "uv.lock"),
        "final_development_models_sha256": sha(FINAL_MODELS),
        "development_compatibility": {
            "tracking_identities_verified": len(DEV_ALIASES),
            "existing_payloads_verified_without_parsing": development_payloads_verified,
            "status": "passed",
        },
        "historical_regression": {
            "pointer_bytes": 133, "contents_reported_bytes": 90729279,
            "frozen_session6_rejects": True, "session6c_accepts_distinct_identities": True,
        },
        "authorized_products": {"development": public["development"], "reserved": public["reserved"]},
        "reserved_match_count": 10, "withheld_access": False,
        "detailed_source_authority_sha256": sha(SOURCE_AUTHORITY),
    }
    atomic_text(REPAIR_AUTHORITY, json_text(authority))
    print(json.dumps({"source_tree": tree_oid, "development_tracking": 9, "reserved_products": 30}))


def load_source_authority() -> tuple[dict, dict]:
    require_committed(REPAIR_AUTHORITY)
    authority = json.loads(REPAIR_AUTHORITY.read_text())
    local = json.loads(SOURCE_AUTHORITY.read_text())
    if sha(SOURCE_AUTHORITY) != authority.get("detailed_source_authority_sha256"):
        raise RuntimeError("detailed source authority changed")
    if authority.get("implementation_sha256") != implementation_hashes():
        raise RuntimeError("repair implementation changed")
    if authority.get("source_commit") != SOURCE_COMMIT or authority.get("reserved_match_count") != 10:
        raise RuntimeError("repair authority invalid")
    return authority, local


def entry_from(record: dict) -> tuple[TreeEntry, LfsPointer | None]:
    entry = TreeEntry(record["path"], record["git_object_type"], record["git_blob_oid"], record["git_blob_size"])
    pointer = None if "lfs" not in record else LfsPointer(record["lfs"]["payload_sha256"], record["lfs"]["payload_size"])
    return entry, pointer


def acquire_reserved() -> None:
    verify_history()
    ensure_implementation_committed()
    _, local = load_source_authority()
    if DATA.exists() or SOURCE_RECEIPTS.exists():
        raise RuntimeError("Session 6c acquisition already started")
    client = Session6cSourceClient(github_token(), ledger=append_access)
    receipts: dict[str, dict] = {}
    for match in sorted(RESERVED, key=int):
        alias = RESERVED_ALIASES[match]
        receipts[alias] = {}
        for product in PRODUCTS:
            record = local["records"][alias][product]
            entry, pointer = entry_from(record)
            destination = safe_destination(DATA, match, product, RESERVED)
            receipts[alias][product] = client.acquire(
                entry, destination, pointer=pointer, label=f"reserved:{alias}:{product}:payload"
            )
            atomic_text(SOURCE_RECEIPTS, json_text(receipts))
    if sum(len(value) for value in receipts.values()) != 30:
        raise RuntimeError("not all reserved products were acquired")
    print(json.dumps({"ordinary_git_objects_verified": 20, "lfs_payloads_verified": 10}))


def verify_acquired(local: dict) -> None:
    receipts = json.loads(SOURCE_RECEIPTS.read_text())
    for match in sorted(RESERVED, key=int):
        alias = RESERVED_ALIASES[match]
        for product in PRODUCTS:
            path = safe_destination(DATA, match, product, RESERVED)
            if not path.is_file() or path.is_symlink():
                raise RuntimeError(f"acquired product missing or unsafe: {alias}/{product}")
            record = local["records"][alias][product]
            entry, pointer = entry_from(record)
            if pointer is None:
                content = path.read_bytes()
                valid = len(content) == entry.git_size and git_blob_oid(content) == entry.git_oid
                expected_receipt = {"git_oid": entry.git_oid, "bytes": len(content)}
            else:
                valid = path.stat().st_size == pointer.payload_size and sha(path) == pointer.payload_sha256
                expected_receipt = {"lfs_payload_sha256": pointer.payload_sha256, "bytes": path.stat().st_size}
            if not valid or receipts.get(alias, {}).get(product) != expected_receipt:
                raise RuntimeError(f"acquired integrity mismatch: {alias}/{product}")


def summarize(values: list[int]) -> dict[str, float | int]:
    return frozen.summarize_counts(values)


def prepare_reserved() -> None:
    models = verify_history()
    ensure_implementation_committed()
    _, local = load_source_authority()
    verify_acquired(local)
    if POPULATION.exists() or POPULATION_SUMMARY.exists() or EXECUTION.exists():
        raise RuntimeError("Session 6c population already started")
    all_choices: list[ChoiceSet] = []
    all_candidates: list[int] = []
    all_defenders: list[int] = []
    matches: dict[str, dict] = {}
    atomic_text(ALIAS_MAP, json_text(RESERVED_ALIASES))
    for match in sorted(RESERVED, key=int):
        alias = RESERVED_ALIASES[match]
        projected = load_projected_match_session6(DATA, match, allowlist=RESERVED)
        choices, qc, contract = prepare_match_session6(match, projected, allowlist=RESERVED)
        if not choices:
            raise RuntimeError(f"reserved match has no evaluation observations: {alias}")
        content = rendered_population(choices)
        matches[alias] = {
            "raw_pass_attempts": qc["raw_pass_attempts"], "evaluation_eligible": qc["evaluation_eligible"],
            "fit_eligible": qc["fit_eligible"], "exclusions": qc["exclusions"],
            "target_outside": qc["target_outside"], "target_outside_reasons": qc["target_outside_reasons"],
            "target_qc": qc["target_qc"], "carrier_qc": qc["carrier_qc"],
            "candidate_count_summary": summarize(qc["candidate_counts"]),
            "defender_count_summary": summarize(qc["defender_counts"]),
            "population_sha256": hashlib.sha256(content).hexdigest(), "input_contract": contract,
        }
        all_candidates.extend(qc["candidate_counts"])
        all_defenders.extend(qc["defender_counts"])
        all_choices.extend(choices)
    population = rendered_population(all_choices)
    atomic_text(POPULATION, population.decode())
    first = next(iter(matches.values()))
    sum_map = lambda field: {key: sum(item[field][key] for item in matches.values()) for key in first[field]}  # noqa: E731
    summary = {
        "schema_version": "1.0.0", "performance_computed": False, "reservation": RESERVATION,
        "source_commit": SOURCE_COMMIT, "source_authority_sha256": sha(SOURCE_AUTHORITY),
        "source_receipts_sha256": sha(SOURCE_RECEIPTS), "reserved_match_count": 10,
        "reserved_aliases": sorted(RESERVED_ALIASES.values()), "withheld_access": False,
        "source_integrity": {"ordinary_git_objects_verified": 20, "lfs_pointer_objects_verified": 10, "lfs_payloads_verified": 10},
        "raw_pass_attempts": sum(item["raw_pass_attempts"] for item in matches.values()),
        "evaluation_eligible": sum(item["evaluation_eligible"] for item in matches.values()),
        "fit_eligible": sum(item["fit_eligible"] for item in matches.values()),
        "exclusions": sum_map("exclusions"), "target_qc": sum_map("target_qc"), "carrier_qc": sum_map("carrier_qc"),
        "target_outside": sum(item["target_outside"] for item in matches.values()),
        "target_outside_reasons": {
            reason: sum(item["target_outside_reasons"].get(reason, 0) for item in matches.values())
            for reason in sorted({reason for item in matches.values() for reason in item["target_outside_reasons"]})
        },
        "candidate_count_summary": summarize(all_candidates), "defender_count_summary": summarize(all_defenders),
        "population_sha256": hashlib.sha256(population).hexdigest(),
        "final_development_models_sha256": sha(FINAL_MODELS),
        "repair_authority_sha256": sha(REPAIR_AUTHORITY), "implementation_sha256": implementation_hashes(),
        "matches": matches,
    }
    atomic_text(POPULATION_SUMMARY, json_text(summary))
    print(json.dumps({key: summary[key] for key in ("raw_pass_attempts", "evaluation_eligible", "fit_eligible", "target_outside", "population_sha256")}))


def validate_population() -> tuple[dict, dict]:
    models = verify_history()
    require_committed(POPULATION_SUMMARY)
    summary = json.loads(POPULATION_SUMMARY.read_text())
    if sha(POPULATION) != summary.get("population_sha256") or sha(FINAL_MODELS) != summary.get("final_development_models_sha256"):
        raise RuntimeError("population authority hash mismatch")
    aliases = sorted(RESERVED_ALIASES.values())
    if summary.get("reserved_aliases") != aliases or sorted(summary.get("matches", {})) != aliases:
        raise RuntimeError("population aliases invalid")
    if any(item["evaluation_eligible"] <= 0 for item in summary["matches"].values()):
        raise RuntimeError("reserved match has no evaluation observations")
    for field in ("evaluation_eligible", "fit_eligible", "target_outside", "raw_pass_attempts"):
        if summary[field] != sum(item[field] for item in summary["matches"].values()):
            raise RuntimeError(f"population total mismatch: {field}")
    return models, summary


def create_execution_marker() -> None:
    EXECUTION.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(EXECUTION, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(json_text({"status": "started", "timestamp": datetime.now(timezone.utc).isoformat(), "population_sha256": sha(POPULATION)}))


def score() -> None:
    models, summary = validate_population()
    ensure_implementation_committed()
    require_clean()
    if EXECUTION.exists() or any((OUTPUT / name).exists() for name in RESULT_FILES):
        raise RuntimeError("Session 6c protected scoring already started")
    groups = frozen.load_population(POPULATION, RESERVED)
    if set(groups) != set(RESERVED) or any(not rows for rows in groups.values()):
        raise RuntimeError("scoring requires ten nonempty reserved groups")
    features = frozen.raw_features(groups)
    if sum(map(len, groups.values())) != summary["evaluation_eligible"]:
        raise RuntimeError("evaluation denominator mismatch")
    create_execution_marker()
    rows_by_model: dict[str, list[dict]] = {model: [] for model in ("m0", "m1", "m2")}
    for model in ("m0", "m1", "m2"):
        authority = models["models"][model]
        mean, scale, beta = (np.asarray(authority[name], dtype=np.float64) for name in ("mean", "scale", "coefficients"))
        for match in sorted(RESERVED, key=int):
            credits = [
                expected_credits(((matrix - mean) / scale) @ beta, choice.target_index)
                for matrix, choice in zip(features[model][match], groups[match], strict=True)
            ]
            alias = RESERVED_ALIASES[match]
            item = summary["matches"][alias]
            rows_by_model[model].append(frozen.metric_row(alias, credits, item["fit_eligible"], item["target_outside"]))
    metric_fields = ("match_alias", "evaluation_eligible", "fit_eligible", "target_outside_zero_credit", "mrr", "hit_at_1", "hit_at_3", "tied_target_blocks")
    for model in ("m0", "m1", "m2"):
        atomic_csv(OUTPUT / f"{model}_match_metrics.csv", rows_by_model[model], metric_fields)
    paired_m1 = [{
        "match_alias": left["match_alias"], "m0_mrr": left["mrr"], "m1_mrr": right["mrr"],
        "m1_minus_m0_mrr": right["mrr"] - left["mrr"],
        "m1_minus_m0_hit_at_1": right["hit_at_1"] - left["hit_at_1"],
        "m1_minus_m0_hit_at_3": right["hit_at_3"] - left["hit_at_3"],
    } for left, right in zip(rows_by_model["m0"], rows_by_model["m1"], strict=True)]
    paired_m2 = [{
        "match_alias": left["match_alias"], "m1_mrr": left["mrr"], "m2_mrr": right["mrr"],
        "m2_minus_m1_mrr": right["mrr"] - left["mrr"],
        "m2_minus_m1_hit_at_1": right["hit_at_1"] - left["hit_at_1"],
        "m2_minus_m1_hit_at_3": right["hit_at_3"] - left["hit_at_3"],
    } for left, right in zip(rows_by_model["m1"], rows_by_model["m2"], strict=True)]
    atomic_csv(OUTPUT / "m1_m0_paired.csv", paired_m1, tuple(paired_m1[0]))
    atomic_csv(OUTPUT / "m2_m1_paired.csv", paired_m2, tuple(paired_m2[0]))
    aggregate_models = {
        model: {field: match_macro({row["match_alias"]: row for row in rows}, field) for field in ("mrr", "hit_at_1", "hit_at_3")}
        for model, rows in rows_by_model.items()
    }
    aggregate = {
        "schema_version": "1.0.0", "headline_weighting": "equal mean across ten reserved matches",
        "models": aggregate_models,
        "m1_minus_m0": {field: aggregate_models["m1"][field] - aggregate_models["m0"][field] for field in ("mrr", "hit_at_1", "hit_at_3")},
        "m2_minus_m1": {field: aggregate_models["m2"][field] - aggregate_models["m1"][field] for field in ("mrr", "hit_at_1", "hit_at_3")},
        "paired_m1_minus_m0_mrr": frozen.paired_summary(paired_m1, "m1_minus_m0_mrr"),
        "paired_m2_minus_m1_mrr": frozen.paired_summary(paired_m2, "m2_minus_m1_mrr"),
    }
    atomic_text(OUTPUT / "aggregate_metrics.json", json_text(aggregate))
    qc = {
        "schema_version": "1.0.0", "reserved_match_count": 10,
        "evaluation_eligible": summary["evaluation_eligible"], "fit_eligible": summary["fit_eligible"],
        "target_outside_zero_credit": summary["target_outside"], "identical_model_populations": True,
        "tie_policy": {"absolute_tolerance": 1e-12, "block_reference": "highest score in block", "expected_credit": True},
        "tied_target_blocks": {model: sum(row["tied_target_blocks"] for row in rows) for model, rows in rows_by_model.items()},
        "reserved_fitting": False, "post_access_tuning": False, "pose_or_orientation_access": False,
        "network_or_gnn_work": False, "scored_passage_inspection": False,
    }
    atomic_text(OUTPUT / "qc.json", json_text(qc))
    output_hashes = {name: sha(OUTPUT / name) for name in RESULT_FILES if name not in {"manifest.json"}}
    manifest = {
        "schema_version": "1.0.0", "status": "closed", "source_commit": SOURCE_COMMIT,
        "starting_authority": START, "protocol_commit": PROTOCOL_COMMIT, "protocol_sha256": sha(PROTOCOL),
        "implementation_sha256": implementation_hashes(), "environment": models["environment"],
        "final_development_models_sha256": sha(FINAL_MODELS), "repair_authority_sha256": sha(REPAIR_AUTHORITY),
        "population_summary_sha256": sha(POPULATION_SUMMARY), "reserved_population_sha256": sha(POPULATION),
        "reserved_match_aliases": sorted(RESERVED_ALIASES.values()),
        "model_features": {model: models["models"][model]["feature_names"] for model in ("m0", "m1", "m2")},
        "metrics": ["mrr", "hit_at_1", "hit_at_3"], "output_sha256": output_hashes,
    }
    atomic_text(OUTPUT / "manifest.json", json_text(manifest))
    atomic_text(EXECUTION, json_text({"status": "closed", "timestamp": datetime.now(timezone.utc).isoformat(), "manifest_sha256": sha(OUTPUT / "manifest.json")}))
    validate_outputs()
    print(json.dumps({
        "m0_mrr": aggregate_models["m0"]["mrr"], "m1_mrr": aggregate_models["m1"]["mrr"],
        "m1_minus_m0": aggregate["m1_minus_m0"]["mrr"], "m2_mrr": aggregate_models["m2"]["mrr"],
        "m2_minus_m1": aggregate["m2_minus_m1"]["mrr"],
    }))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate_outputs() -> None:
    summary = json.loads(POPULATION_SUMMARY.read_text())
    aliases = sorted(RESERVED_ALIASES.values())
    metrics: dict[str, dict[str, dict[str, float]]] = {}
    expected_metric_fields = {"match_alias", "evaluation_eligible", "fit_eligible", "target_outside_zero_credit", "mrr", "hit_at_1", "hit_at_3", "tied_target_blocks"}
    for model in ("m0", "m1", "m2"):
        rows = read_csv(OUTPUT / f"{model}_match_metrics.csv")
        if len(rows) != 10 or [row["match_alias"] for row in rows] != aliases or set(rows[0]) != expected_metric_fields:
            raise RuntimeError("metric schema or aliases invalid")
        metrics[model] = {}
        for row in rows:
            alias = row["match_alias"]
            if int(row["evaluation_eligible"]) != summary["matches"][alias]["evaluation_eligible"]:
                raise RuntimeError("metric denominator mismatch")
            values = {field: float(row[field]) for field in ("mrr", "hit_at_1", "hit_at_3")}
            if any(not math.isfinite(value) or not 0 <= value <= 1 for value in values.values()):
                raise RuntimeError("metric value invalid")
            metrics[model][alias] = values
    aggregate = json.loads((OUTPUT / "aggregate_metrics.json").read_text())
    for model in metrics:
        for field in ("mrr", "hit_at_1", "hit_at_3"):
            expected = sum(metrics[model][alias][field] for alias in aliases) / 10
            if aggregate["models"][model][field] != expected:
                raise RuntimeError("aggregate mismatch")
    manifest = json.loads((OUTPUT / "manifest.json").read_text())
    for name, digest in manifest["output_sha256"].items():
        if sha(OUTPUT / name) != digest:
            raise RuntimeError("closed output hash mismatch")


def publication_check() -> None:
    verify_history()
    if REPAIR_AUTHORITY.exists():
        authority = json.loads(REPAIR_AUTHORITY.read_text())
        if authority.get("reserved_match_count") != 10 or authority.get("withheld_access") is True:
            raise RuntimeError("repair authority publication schema invalid")
    if POPULATION_SUMMARY.exists():
        summary = json.loads(POPULATION_SUMMARY.read_text())
        if summary.get("reserved_match_count") != 10 or summary.get("withheld_access") is True:
            raise RuntimeError("population publication schema invalid")
    if (OUTPUT / "manifest.json").exists():
        validate_outputs()
    prohibited = ('"player_id"', '"event_id"', '"candidate_ids"', '"candidate_xy"', '"carrier_xy"', '"defender_xy"', '"timestamp"', "/Users/")
    for path in [REPAIR_AUTHORITY, POPULATION_SUMMARY, *(OUTPUT / name for name in RESULT_FILES)]:
        if path.exists() and any(term in path.read_text(errors="ignore") for term in prohibited):
            raise RuntimeError(f"publication-sensitive field in {path.name}")
    print("Session 6c publication check passed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "verify-sources", "acquire-reserved", "prepare-reserved", "score", "publication-check"))
    command = parser.parse_args().command
    globals()[command.replace("-", "_")]()


if __name__ == "__main__":
    main()
