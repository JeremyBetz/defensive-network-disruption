#!/usr/bin/env python3
"""Session 6e repaired acquisition and one corrected protected evaluation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import platform
import re
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
from defensive_network_disruption.data.session6e_transport import (  # noqa: E402
    LfsPointer,
    SOURCE_COMMIT,
    OfficialLfsClient,
    TreeEntry,



    source_path,
)
from defensive_network_disruption.data.session6c_source import public_entry, git_blob_oid, safe_destination
from defensive_network_disruption.data.session6e_transport import safe_local
from defensive_network_disruption.data.skillcorner_session2 import DEVELOPMENT_MATCHES  # noqa: E402
from defensive_network_disruption.validation.ranking_metrics import expected_credits, match_macro  # noqa: E402

START = "aecdb860f6a3b354c4eb9631aff54b694fefe88f"
PROTOCOL_COMMIT = "d8112ad"
PROTOCOL = ROOT / "docs/protocols/phase_06e_official_lfs_transport_and_reserved_evaluation.md"
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
DATA = ROOT / "data/session_06e"
OUTPUT = ROOT / "outputs/reserved_evaluation_v3"
LOCAL = OUTPUT / "local"
SOURCE_AUTHORITY = LOCAL / "source_authority.json"
SOURCE_RECEIPTS = LOCAL / "source_receipts.json"
ACCESS_LEDGER = LOCAL / "access_ledger.jsonl"
POPULATION = LOCAL / "reserved_population.jsonl"
ALIAS_MAP = LOCAL / "alias_map.json"
EXECUTION = LOCAL / "execution_state.json"
TRANSPORT_AUTHORITY = OUTPUT / "transport_authority.json"
POPULATION_SUMMARY = OUTPUT / "population_summary.json"
RESULT_FILES = (
    "m0_match_metrics.csv", "m1_match_metrics.csv", "m2_match_metrics.csv",
    "m1_m0_paired.csv", "m2_m1_paired.csv", "aggregate_metrics.json", "qc.json", "manifest.json",
)
IMPLEMENTATION_FILES = (
    "scripts/session_06e_reserved.py",
    "src/defensive_network_disruption/data/session6e_transport.py",
    "tests/test_session6e_reserved.py",
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
    safe_local(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)


def atomic_csv(path: Path, rows: list[dict], fields: tuple[str, ...]) -> None:
    safe_local(path)
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
        raise RuntimeError("starting authority is not an ancestor")
    if committed_sha(PROTOCOL_COMMIT, str(PROTOCOL.relative_to(ROOT))) != sha(PROTOCOL):
        raise RuntimeError("Session 6e protocol changed")
    # Preserve all historical tracked bytes, apart from explicitly append-only log.
    for name in git("ls-tree", "-r", "--name-only", START).splitlines():
        if name == "docs/research_log.md":
            original = subprocess.run(["git","show",f"{START}:{name}"],cwd=ROOT,check=True,capture_output=True).stdout
            if not (ROOT/name).read_bytes().startswith(original):
                raise RuntimeError("historical research log rewritten")
        elif not (ROOT/name).is_file() or sha(ROOT/name) != committed_sha(START,name):
            raise RuntimeError("historical artifact changed")
    if sha(FINAL_MODELS) != FINAL_MODELS_SHA:
        raise RuntimeError("final models changed")
    models = json.loads(FINAL_MODELS.read_text())
    actual = {"python":platform.python_version(),"platform":platform.platform(),"numpy":np.__version__,"scipy":scipy.__version__,"uv_lock_sha256":sha(ROOT/"uv.lock")}
    if models["environment"] != actual:
        raise RuntimeError("governed numerical environment mismatch")
    return models


def implementation_hashes() -> dict[str, str]:
    return {name: sha(ROOT / name) for name in IMPLEMENTATION_FILES}


def ensure_implementation_committed() -> str:
    for name in IMPLEMENTATION_FILES:
        require_committed(ROOT / name)
    require_clean()
    return git("rev-parse", "HEAD")


def append_access(label: str, attempt: int, status: str, category: str | None) -> None:
    safe_local(ACCESS_LEDGER)
    LOCAL.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(), "phase": "session_06e",
        "protocol_commit": PROTOCOL_COMMIT, "implementation_commit": git("rev-parse", "HEAD"),
        "request_label": label, "attempt": attempt, "status": status, "failure_category": category,
        "protocol_sha256":sha(PROTOCOL),"implementation_sha256":implementation_hashes(),
    }
    with ACCESS_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")


def github_token() -> str:
    token = subprocess.run(["gh", "auth", "token"], check=True, capture_output=True, text=True).stdout.strip()
    if not token:
        raise RuntimeError("GitHub token unavailable")
    return token


def expected_paths() -> tuple[set[str], dict]:
    paths, reverse = set(), {}
    for match, alias in RESERVED_ALIASES.items():
        for product in PRODUCTS:
            path = source_path(match,product,RESERVED)
            paths.add(path)
            reverse[path] = ("reserved",alias,product)
    return paths,reverse


def preflight() -> None:
    verify_history()
    for path in (DATA,LOCAL):
        safe_local(path)
        relative = str((path/"ignore_check").relative_to(ROOT))
        if not git("check-ignore","--",relative):
            raise RuntimeError("storage is not ignored")
    if set(RESERVED) != set(frozen.RESERVED) or WITHHELD in RESERVED:
        raise RuntimeError("partition authority changed")
    if any((OUTPUT / name).exists() for name in RESULT_FILES) or EXECUTION.exists():
        raise RuntimeError("Session 6e protected execution already exists")
    print("Session 6e preflight passed")


def verify_sources() -> None:
    models = verify_history()
    implementation_commit = ensure_implementation_committed()
    if any((LOCAL/name).exists() for name in ("acquisition_state.json","preparation_state.json","execution_state.json")):
        raise RuntimeError("source verification cannot follow acquisition")
    if TRANSPORT_AUTHORITY.exists() or SOURCE_AUTHORITY.exists():
        raise RuntimeError("source verification already exists")
    previous = ROOT / "outputs/reserved_evaluation_v2/local/source_authority.json"
    safe_local(previous)
    if sha(previous) != "6d5f4f6f64216b826b2405e2099569d03e7d1ffc368617d552ba70072cb6a87b":
        raise RuntimeError("identity-only source authority mismatch")
    recorded = json.loads(previous.read_text())
    paths, reverse = expected_paths()
    client = OfficialLfsClient(github_token(), ledger=append_access)
    tree_oid, entries = client.tree_entries(paths)
    if tree_oid != recorded["source_tree"]:
        raise RuntimeError("source tree changed")
    local = {"source_commit":SOURCE_COMMIT,"source_tree":tree_oid,"records":{}}
    public = {}
    for path in sorted(paths):
        _,alias,product = reverse[path]
        entry = entries[path]
        pointer = client.pointer(entry,label=f"reserved:{alias}:pointer")[0] if product == "tracking" else None
        record = {"path":path,**public_entry(entry,pointer)}
        if record != recorded["records"][alias][product]:
            raise RuntimeError("pinned source identity differs from authority")
        local["records"].setdefault(alias,{})[product] = record
        public.setdefault(alias,{})[product] = public_entry(entry,pointer)
    atomic_text(SOURCE_AUTHORITY,json_text(local))
    authority = {
        "schema_version":"1.0.0","status":"prospective_transport_authority",
        "starting_authority":START,"protocol_commit":git("rev-parse",PROTOCOL_COMMIT),"protocol_sha256":sha(PROTOCOL),
        "implementation_commit":implementation_commit,"implementation_sha256":implementation_hashes(),
        "source_commit":SOURCE_COMMIT,"source_tree":tree_oid,"environment":models["environment"],
        "uv_lock_sha256":sha(ROOT/"uv.lock"),"final_development_models_sha256":sha(FINAL_MODELS),
        "session6d_manifest_sha256":sha(ROOT/"outputs/lfs_tls_integrity_review/manifest.json"),
        "session6c_repair_authority_sha256":sha(ROOT/"outputs/reserved_evaluation_v2/repair_authority.json"),
        "corrected_verifier_sha256":sha(ROOT/"src/defensive_network_disruption/data/session6c_source.py"),
        "authorized_products":public,"reserved_match_count":10,"withheld_access":False,
        "detailed_source_authority_sha256":sha(SOURCE_AUTHORITY),
        "transport":"official LFS basic batch download; normal TLS; no redirects",
        "test_evidence_sha256":sha(LOCAL/"preaccess_tests.json"),
    }
    atomic_text(TRANSPORT_AUTHORITY,json_text(authority))
    print("Thirty pinned source identities verified; no product payload acquired")


def load_source_authority() -> tuple[dict, dict]:
    require_committed(TRANSPORT_AUTHORITY)
    authority = json.loads(TRANSPORT_AUTHORITY.read_text())
    safe_local(SOURCE_AUTHORITY)
    if sha(SOURCE_AUTHORITY) != authority.get("detailed_source_authority_sha256"):
        raise RuntimeError("detailed source authority changed")
    local = json.loads(SOURCE_AUTHORITY.read_text())
    if authority.get("protocol_sha256") != sha(PROTOCOL) or authority.get("final_development_models_sha256") != sha(FINAL_MODELS) or authority.get("environment") != verify_history()["environment"]:
        raise RuntimeError("transport authority binding changed")
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
    if DATA.exists() or SOURCE_RECEIPTS.exists() or (LOCAL/"acquisition_state.json").exists():
        raise RuntimeError("Session 6e acquisition already started")
    stage_marker("acquisition")
    client = OfficialLfsClient(ledger=append_access)
    receipts: dict[str, dict] = {}
    for match in sorted(RESERVED, key=int):
        alias = RESERVED_ALIASES[match]
        receipts[alias] = {}
        for product in PRODUCTS:
            record = local["records"][alias][product]
            entry, pointer = entry_from(record)
            destination = safe_destination(DATA, match, product, RESERVED)
            if record["path"] != source_path(match,product,RESERVED):
                raise RuntimeError("source path association mismatch")
            receipts[alias][product] = client.acquire(
                entry, destination, pointer=pointer, label=f"reserved:{alias}:{product}:payload"
            )
            atomic_text(SOURCE_RECEIPTS, json_text(receipts))
    if sum(len(value) for value in receipts.values()) != 30:
        raise RuntimeError("not all reserved products were acquired")
    atomic_text(LOCAL/"acquisition_state.json",json_text({"status":"verified","source_receipts_sha256":sha(SOURCE_RECEIPTS)}))
    print(json.dumps({"ordinary_git_objects_verified": 20, "lfs_payloads_verified": 10}))


def verify_acquired(local: dict) -> None:
    safe_local(SOURCE_RECEIPTS)
    receipts = json.loads(SOURCE_RECEIPTS.read_text())
    if set(receipts) != set(RESERVED_ALIASES.values()) or any(set(v) != set(PRODUCTS) for v in receipts.values()):
        raise RuntimeError("thirty verified receipts required")
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
        raise RuntimeError("Session 6e population already started")
    stage_marker("preparation")
    all_choices: list[ChoiceSet] = []
    all_candidates: list[int] = []
    all_defenders: list[int] = []
    matches: dict[str, dict] = {}
    atomic_text(ALIAS_MAP, json_text(RESERVED_ALIASES))
    for match in sorted(RESERVED, key=int):
        alias = RESERVED_ALIASES[match]
        append_access(f"reserved:{alias}:projected_values",1,"started",None)
        projected = load_projected_match_session6(DATA, match, allowlist=RESERVED)
        choices, qc, contract = prepare_match_session6(match, projected, allowlist=RESERVED)
        append_access(f"reserved:{alias}:projected_values",1,"completed",None)
        if not choices:
            raise RuntimeError(f"reserved match has no evaluation observations: {alias}")
        content = rendered_population(choices)
        matches[alias] = {
            "raw_pass_attempts": qc["raw_pass_attempts"], "evaluation_eligible": qc["evaluation_eligible"],
            "fit_eligible": qc["fit_eligible"], "exclusions": qc["exclusions"],
            "target_outside": qc["target_outside"], "target_outside_reasons": qc["target_outside_reasons"],
            "target_qc": qc["target_qc"], "carrier_qc": qc["carrier_qc"],
            "target_completeness":{"denominator_raw_attempts":qc["raw_pass_attempts"],"missing":qc["target_qc"]["missing"],"present":qc["raw_pass_attempts"]-qc["target_qc"]["missing"],"unusable_self_or_unresolved":qc["target_qc"]["self"]+qc["target_qc"]["unresolved"],"usable_reference":qc["raw_pass_attempts"]-qc["target_qc"]["missing"]-qc["target_qc"]["self"]-qc["target_qc"]["unresolved"]},
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
        "source_integrity": {"ordinary_git_objects_verified": 20, "lfs_pointer_objects_verified": 10, "lfs_payloads_verified": 10,
            "tracking": {alias:{"expected_sha256":local["records"][alias]["tracking"]["lfs"]["payload_sha256"],"actual_sha256":json.loads(SOURCE_RECEIPTS.read_text())[alias]["tracking"]["lfs_payload_sha256"],"expected_bytes":local["records"][alias]["tracking"]["lfs"]["payload_size"],"actual_bytes":json.loads(SOURCE_RECEIPTS.read_text())[alias]["tracking"]["bytes"],"status":"verified"} for alias in sorted(RESERVED_ALIASES.values())}},
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
        "transport_authority_sha256": sha(TRANSPORT_AUTHORITY), "implementation_sha256": implementation_hashes(),
        "matches": matches,
    }
    validate_structural_summary(summary)
    atomic_text(POPULATION_SUMMARY, json_text(summary))
    print(json.dumps({key: summary[key] for key in ("raw_pass_attempts", "evaluation_eligible", "fit_eligible", "target_outside", "population_sha256")}))


def validate_structural_summary(summary):
    expected = {"schema_version","performance_computed","reservation","source_commit","source_authority_sha256","source_receipts_sha256","reserved_match_count","reserved_aliases","withheld_access","source_integrity","raw_pass_attempts","evaluation_eligible","fit_eligible","exclusions","target_qc","carrier_qc","target_outside","target_outside_reasons","candidate_count_summary","defender_count_summary","population_sha256","final_development_models_sha256","transport_authority_sha256","implementation_sha256","matches"}
    if set(summary) != expected or summary["performance_computed"] is not False or summary["withheld_access"] is not False or summary["source_commit"] != SOURCE_COMMIT:
        raise RuntimeError("structural summary schema mismatch")
    aliases = sorted(RESERVED_ALIASES.values())
    if summary["reserved_aliases"] != aliases or sorted(summary["matches"]) != aliases or summary["reserved_match_count"] != 10:
        raise RuntimeError("structural alias mismatch")
    match_fields = {"raw_pass_attempts","evaluation_eligible","fit_eligible","exclusions","target_outside","target_outside_reasons","target_qc","carrier_qc","target_completeness","candidate_count_summary","defender_count_summary","population_sha256","input_contract"}
    for item in summary["matches"].values():
        if set(item) != match_fields:
            raise RuntimeError("structural match schema mismatch")
        for field in ("raw_pass_attempts","evaluation_eligible","fit_eligible","target_outside"):
            if type(item[field]) is not int or item[field] < 0:
                raise RuntimeError("structural count invalid")
        if item["evaluation_eligible"] <= 0 or item["evaluation_eligible"] != item["fit_eligible"]+item["target_outside"] or item["raw_pass_attempts"] != item["evaluation_eligible"]+sum(item["exclusions"].values()):
            raise RuntimeError("structural population reconciliation failed")
        tc=item["target_completeness"]
        if set(tc) != {"denominator_raw_attempts","missing","present","unusable_self_or_unresolved","usable_reference"} or tc["denominator_raw_attempts"] != item["raw_pass_attempts"] or tc["present"]+tc["missing"] != item["raw_pass_attempts"] or tc["usable_reference"]+tc["unusable_self_or_unresolved"] != tc["present"]:
            raise RuntimeError("target completeness denominator mismatch")
    for field in ("raw_pass_attempts","evaluation_eligible","fit_eligible","target_outside"):
        if summary[field] != sum(item[field] for item in summary["matches"].values()):
            raise RuntimeError("structural total mismatch")
    tracking=summary["source_integrity"]["tracking"]
    if sorted(tracking) != aliases:
        raise RuntimeError("tracking verification aliases mismatch")
    for item in tracking.values():
        if set(item) != {"expected_sha256","actual_sha256","expected_bytes","actual_bytes","status"} or item["expected_sha256"] != item["actual_sha256"] or item["expected_bytes"] != item["actual_bytes"] or item["status"] != "verified":
            raise RuntimeError("tracking verification mismatch")


def validate_population() -> tuple[dict, dict]:
    models = verify_history()
    load_source_authority()
    require_committed(POPULATION_SUMMARY)
    summary = json.loads(POPULATION_SUMMARY.read_text())
    safe_local(POPULATION)
    safe_local(SOURCE_RECEIPTS)
    if summary.get("implementation_sha256") != implementation_hashes() or summary.get("transport_authority_sha256") != sha(TRANSPORT_AUTHORITY) or summary.get("source_receipts_sha256") != sha(SOURCE_RECEIPTS) or summary.get("source_authority_sha256") != sha(SOURCE_AUTHORITY):
        raise RuntimeError("population source and implementation binding mismatch")
    if sha(POPULATION) != summary.get("population_sha256") or sha(FINAL_MODELS) != summary.get("final_development_models_sha256"):
        raise RuntimeError("population authority hash mismatch")
    validate_structural_summary(summary)
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
    safe_local(EXECUTION)
    descriptor = os.open(EXECUTION, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(json_text({"status": "started", "timestamp": datetime.now(timezone.utc).isoformat(), "population_sha256": sha(POPULATION)}))


def score() -> None:
    models, summary = validate_population()
    ensure_implementation_committed()
    require_clean()
    if EXECUTION.exists() or any((OUTPUT / name).exists() for name in RESULT_FILES):
        raise RuntimeError("Session 6e protected scoring already started")
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
    validate_outputs(check_manifest=False)
    output_hashes = {name: sha(OUTPUT / name) for name in RESULT_FILES if name not in {"manifest.json"}}
    manifest = {
        "schema_version": "1.0.0", "status": "closed", "source_commit": SOURCE_COMMIT,
        "starting_authority": START, "protocol_commit": PROTOCOL_COMMIT, "protocol_sha256": sha(PROTOCOL),
        "implementation_sha256": implementation_hashes(), "environment": models["environment"],
        "final_development_models_sha256": sha(FINAL_MODELS), "transport_authority_sha256": sha(TRANSPORT_AUTHORITY),
        "population_summary_sha256": sha(POPULATION_SUMMARY), "reserved_population_sha256": sha(POPULATION),
        "population_authority_commit":require_committed(POPULATION_SUMMARY),"transport_authority_commit":require_committed(TRANSPORT_AUTHORITY),"source_receipts_sha256":sha(SOURCE_RECEIPTS),"access_ledger_sha256":sha(ACCESS_LEDGER),
        "reserved_match_aliases": sorted(RESERVED_ALIASES.values()),
        "model_features": {model: models["models"][model]["feature_names"] for model in ("m0", "m1", "m2")},
        "metrics": ["mrr", "hit_at_1", "hit_at_3"], "output_sha256": output_hashes,
    }
    atomic_text(OUTPUT / "manifest.json", json_text(manifest))
    validate_outputs()
    atomic_text(EXECUTION, json_text({"status": "closed", "timestamp": datetime.now(timezone.utc).isoformat(), "manifest_sha256": sha(OUTPUT / "manifest.json")}))
    print(json.dumps({
        "m0_mrr": aggregate_models["m0"]["mrr"], "m1_mrr": aggregate_models["m1"]["mrr"],
        "m1_minus_m0": aggregate["m1_minus_m0"]["mrr"], "m2_mrr": aggregate_models["m2"]["mrr"],
        "m2_minus_m1": aggregate["m2_minus_m1"]["mrr"],
    }))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate_outputs(check_manifest=True) -> None:
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
            item = summary["matches"][alias]
            for field,source in (("fit_eligible","fit_eligible"),("target_outside_zero_credit","target_outside")):
                if int(row[field]) != item[source]:
                    raise RuntimeError("metric count mismatch")
            if int(row["tied_target_blocks"]) < 0 or int(row["tied_target_blocks"]) > int(row["evaluation_eligible"]):
                raise RuntimeError("tie count invalid")
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
    # Strict paired-file and secondary-metric consistency, not just headline MRR.
    for left,right in (("m0","m1"),("m1","m2")):
        prefix = f"{right}_minus_{left}"
        rows = read_csv(OUTPUT/f"{right}_{left}_paired.csv")
        fields = {"match_alias",f"{left}_mrr",f"{right}_mrr",f"{prefix}_mrr",f"{prefix}_hit_at_1",f"{prefix}_hit_at_3"}
        if len(rows) != 10 or [r["match_alias"] for r in rows] != aliases or any(set(r) != fields for r in rows):
            raise RuntimeError("paired schema mismatch")
        typed = []
        for row in rows:
            alias = row["match_alias"]
            for model in (left,right):
                if float(row[f"{model}_mrr"]) != metrics[model][alias]["mrr"]:
                    raise RuntimeError("paired model mismatch")
            for field in ("mrr","hit_at_1","hit_at_3"):
                if float(row[f"{prefix}_{field}"]) != metrics[right][alias][field]-metrics[left][alias][field]:
                    raise RuntimeError("paired difference mismatch")
                if aggregate[prefix][field] != aggregate["models"][right][field]-aggregate["models"][left][field]:
                    raise RuntimeError("aggregate difference mismatch")
            typed.append({k:float(v) if k != "match_alias" else v for k,v in row.items()})
        if aggregate[f"paired_{prefix}_mrr"] != frozen.paired_summary(typed,f"{prefix}_mrr"):
            raise RuntimeError("paired summary mismatch")
    qc = json.loads((OUTPUT/"qc.json").read_text())
    expected_qc = {"schema_version","reserved_match_count","evaluation_eligible","fit_eligible","target_outside_zero_credit","identical_model_populations","tie_policy","tied_target_blocks","reserved_fitting","post_access_tuning","pose_or_orientation_access","network_or_gnn_work","scored_passage_inspection"}
    if set(qc) != expected_qc or qc["reserved_match_count"] != 10 or qc["identical_model_populations"] is not True:
        raise RuntimeError("QC schema invalid")
    for field,source in (("evaluation_eligible","evaluation_eligible"),("fit_eligible","fit_eligible"),("target_outside_zero_credit","target_outside")):
        if qc[field] != summary[source]:
            raise RuntimeError("QC denominator mismatch")
    for model in metrics:
        if qc["tied_target_blocks"][model] != sum(int(r["tied_target_blocks"]) for r in read_csv(OUTPUT/f"{model}_match_metrics.csv")):
            raise RuntimeError("QC tie mismatch")
    expected_aggregate = {"schema_version","headline_weighting","models","m1_minus_m0","m2_minus_m1","paired_m1_minus_m0_mrr","paired_m2_minus_m1_mrr"}
    if set(aggregate) != expected_aggregate or set(aggregate["models"]) != {"m0","m1","m2"}:
        raise RuntimeError("aggregate schema mismatch")
    if check_manifest:
        manifest = json.loads((OUTPUT / "manifest.json").read_text())
        if manifest.get("status") != "closed" or set(manifest["output_sha256"]) != set(RESULT_FILES)-{"manifest.json"}:
            raise RuntimeError("manifest closure invalid")
        for name, digest in manifest["output_sha256"].items():
            if sha(OUTPUT / name) != digest:
                raise RuntimeError("closed output hash mismatch")


def publication_check() -> None:
    verify_history()
    if TRANSPORT_AUTHORITY.exists():
        authority = json.loads(TRANSPORT_AUTHORITY.read_text())
        if authority.get("reserved_match_count") != 10 or authority.get("withheld_access") is True:
            raise RuntimeError("repair authority publication schema invalid")
    if POPULATION_SUMMARY.exists():
        summary = json.loads(POPULATION_SUMMARY.read_text())
        validate_structural_summary(summary)
        if summary.get("reserved_match_count") != 10 or summary.get("withheld_access") is True:
            raise RuntimeError("population publication schema invalid")
    if (OUTPUT / "manifest.json").exists():
        manifest = json.loads((OUTPUT/"manifest.json").read_text())
        if manifest.get("status") == "invalid":
            validate_failure(manifest)
        else:
            validate_outputs()
    prohibited = ('"player_id"', '"event_id"', '"candidate_ids"', '"candidate_xy"', '"carrier_xy"', '"defender_xy"', '"timestamp"', "/Users/", "X-Amz-", "Authorization", "https://github-cloud", "candidate_rows")
    for path in [TRANSPORT_AUTHORITY, POPULATION_SUMMARY, *(OUTPUT / name for name in RESULT_FILES)]:
        if path.exists() and any(term in path.read_text(errors="ignore") for term in prohibited):
            raise RuntimeError(f"publication-sensitive field in {path.name}")
    print("Session 6e publication check passed")


def stage_marker(stage):
    LOCAL.mkdir(parents=True,exist_ok=True)
    path = LOCAL/f"{stage}_state.json"
    safe_local(path)
    fd = os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,"w") as handle:
        handle.write(json_text({"status":"started","protocol_sha256":sha(PROTOCOL),"implementation_sha256":implementation_hashes()}))


def validate_failure(manifest):
    fields = {"schema_version","status","failed_command","failure_category","failure_reason","primary","secondary","source_commit","protocol_sha256","implementation_sha256","starting_authority","final_development_models_sha256","verified_products","structural_access_started","scoring_started","output_sha256","unavailable","access_ledger_sha256"}
    if set(manifest) != fields or manifest["status"] != "invalid" or manifest["primary"] != "D" or manifest["secondary"] != "4":
        raise RuntimeError("failure manifest schema invalid")
    if manifest["failed_command"] not in {"verify-sources","acquire-reserved","prepare-reserved","score"} or type(manifest["verified_products"]) is not int or not 0 <= manifest["verified_products"] <= 30:
        raise RuntimeError("failure stage invalid")
    allowed = set(RESULT_FILES)-{"manifest.json"} | {"transport_authority.json","population_summary.json"}
    if not set(manifest["output_sha256"]).issubset(allowed) or set(manifest["unavailable"]) != allowed-set(manifest["output_sha256"]):
        raise RuntimeError("failure artifact inventory invalid")
    for name,digest in manifest["output_sha256"].items():
        if sha(OUTPUT/name) != digest:
            raise RuntimeError("failure output hash mismatch")


def close_failure(command,exc):
    # Exception text is admitted only for controlled structural errors; transport text
    # never carries signed URLs and only its class/category is published.
    from defensive_network_disruption.data.session6_population import Session6ContractError
    reason = str(exc) if isinstance(exc,Session6ContractError) or (type(exc).__name__ == "IntegrityError" and re.fullmatch(r"[a-z_]+",str(exc))) else type(exc).__name__
    if any(token in reason for token in ("http", "/Users/", "Authorization")):
        reason = type(exc).__name__
    append_access(command,1,"stopped",type(exc).__name__)
    receipts = json.loads(SOURCE_RECEIPTS.read_text()) if SOURCE_RECEIPTS.exists() else {}
    allowed = set(RESULT_FILES)-{"manifest.json"} | {"transport_authority.json","population_summary.json"}
    hashes = {name:sha(OUTPUT/name) for name in sorted(allowed) if (OUTPUT/name).exists()}
    manifest = {
        "schema_version":"1.0.0","status":"invalid","failed_command":command,
        "failure_category":type(exc).__name__,"failure_reason":reason,"primary":"D","secondary":"4",
        "source_commit":SOURCE_COMMIT,"protocol_sha256":sha(PROTOCOL),"implementation_sha256":implementation_hashes(),
        "starting_authority":START,"final_development_models_sha256":sha(FINAL_MODELS),
        "verified_products":sum(len(v) for v in receipts.values()),
        "structural_access_started":(LOCAL/"preparation_state.json").exists(),"scoring_started":EXECUTION.exists(),
        "output_sha256":hashes,"unavailable":sorted(allowed-set(hashes)),"access_ledger_sha256":sha(ACCESS_LEDGER),
    }
    validate_failure(manifest)
    atomic_text(OUTPUT/"manifest.json",json_text(manifest))
    print(json.dumps({"status":"invalid","stage":command,"category":type(exc).__name__}))


def dispatch(command):
    if command != "publication-check" and (OUTPUT/"manifest.json").exists():
        raise RuntimeError("closed or failed execution cannot be rerun")
    existing_stage = any((LOCAL/name).exists() for name in ("acquisition_state.json","preparation_state.json","execution_state.json"))
    if command == "acquire-reserved" and existing_stage:
        raise RuntimeError("acquisition cannot restart")
    if command == "prepare-reserved" and (LOCAL/"preparation_state.json").exists():
        raise RuntimeError("preparation cannot restart")
    if command == "score" and EXECUTION.exists():
        raise RuntimeError("scoring cannot restart")
    try:
        globals()[command.replace("-","_")]()
    except Exception as exc:
        if isinstance(exc, FileExistsError):
            raise SystemExit("Session 6e refused concurrent or repeated execution") from None
        if command in {"verify-sources","acquire-reserved","prepare-reserved","score"} and ACCESS_LEDGER.exists() and (not (OUTPUT/"manifest.json").exists() or command == "score"):
            close_failure(command,exc)
        raise SystemExit(f"Session 6e stopped: {type(exc).__name__}") from None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "verify-sources", "acquire-reserved", "prepare-reserved", "score", "publication-check"))
    command = parser.parse_args().command
    dispatch(command)


if __name__ == "__main__":
    main()
