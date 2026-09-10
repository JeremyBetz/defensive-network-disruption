#!/usr/bin/env python3
"""Development-only Session 6a identity compatibility audit."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defensive_network_disruption.data.identity_compatibility import (
    canonical_lines, load_projected_match, restricted_prepare_match, verify_products,
)
from defensive_network_disruption.data.skillcorner_session2 import DEVELOPMENT_MATCHES, SOURCE_COMMIT

START_AUTHORITY = "3cd72c1509bf2ca08d6b41a236b80e065156668d"
SOURCE = "02a396ffd09b283c9f092fdedeff11da6d535b66"
POPULATION_SHA = "cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d"
PROTOCOL = ROOT / "docs/protocols/phase_06a_identity_compatibility.md"
DATA_ROOT = ROOT / "data/session_02"
SOURCE_MANIFEST = ROOT / "data/manifests/skillcorner_opendata_02a396f.local.json"
AUTHORITY_ROOT = ROOT / "outputs/receiver_ranking_m0_m1"
AUTHORITY_POPULATION = AUTHORITY_ROOT / "local/population.jsonl"
OUTPUT_ROOT = ROOT / "outputs/identity_compatibility"
LOCAL_ROOT = OUTPUT_ROOT / "local"
REPLAY = LOCAL_ROOT / "population_replay.jsonl"
DETAILS = LOCAL_ROOT / "audit_details.json"
ACCESS_LEDGER = LOCAL_ROOT / "access_ledger.jsonl"
SUMMARY = OUTPUT_ROOT / "summary.json"
MANIFEST = OUTPUT_ROOT / "manifest.json"
ALIASES = {item: f"development_{index:02d}" for index, item in enumerate(sorted(DEVELOPMENT_MATCHES, key=int), 1)}
EXPECTED = {"evaluation_eligible": 7227, "fit_eligible": 7227}
IMPLEMENTATION_FILES = (
    "scripts/session_06a_identity.py",
    "src/defensive_network_disruption/data/identity_compatibility.py",
    "src/defensive_network_disruption/data/receiver_choices.py",
    "tests/test_session6a_identity_compatibility.py",
)


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def json_text(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def committed_sha(commit: str, relative: str) -> str:
    content = subprocess.run(["git", "show", f"{commit}:{relative}"], cwd=ROOT, check=True, capture_output=True).stdout
    return hashlib.sha256(content).hexdigest()


def safe_authoritative_population() -> Path:
    root = (AUTHORITY_ROOT / "local").resolve()
    if AUTHORITY_POPULATION.is_symlink() or not AUTHORITY_POPULATION.is_file():
        raise RuntimeError("authoritative population is missing or unsafe")
    if not AUTHORITY_POPULATION.resolve().is_relative_to(root) or sha(AUTHORITY_POPULATION) != POPULATION_SHA:
        raise RuntimeError("authoritative population identity mismatch")
    return AUTHORITY_POPULATION


def authority() -> tuple[dict, dict]:
    if subprocess.run(["git", "merge-base", "--is-ancestor", START_AUTHORITY, "HEAD"], cwd=ROOT).returncode:
        raise RuntimeError("Session 5 authority is not an ancestor")
    if SOURCE_COMMIT != SOURCE:
        raise RuntimeError("SkillCorner source revision changed")
    git("ls-files", "--error-unmatch", str(PROTOCOL.relative_to(ROOT)))
    if sha(PROTOCOL) != committed_sha("HEAD", str(PROTOCOL.relative_to(ROOT))):
        raise RuntimeError("Phase 6a protocol is not intact and committed")
    freeze = json.loads((AUTHORITY_ROOT / "population_freeze.json").read_text())
    if freeze["source_commit"] != SOURCE or freeze["population_sha256"] != POPULATION_SHA:
        raise RuntimeError("Session 3 freeze authority mismatch")
    if freeze["evaluation_eligible"] != EXPECTED["evaluation_eligible"] or freeze["fit_eligible"] != EXPECTED["fit_eligible"]:
        raise RuntimeError("authoritative eligibility counts changed")
    session3_manifest = json.loads((AUTHORITY_ROOT / "manifest.json").read_text())
    for name, digest in session3_manifest["output_sha256"].items():
        if sha(AUTHORITY_ROOT / name) != digest:
            raise RuntimeError(f"closed Session 3 artifact changed: {name}")
    safe_authoritative_population()
    return freeze, session3_manifest


def selected_source_authority() -> dict:
    if SOURCE_MANIFEST.is_symlink() or not SOURCE_MANIFEST.is_file():
        raise RuntimeError("source identity manifest is missing or unsafe")
    document = json.loads(SOURCE_MANIFEST.read_text())
    if document.get("source", {}).get("commit") != SOURCE:
        raise RuntimeError("source identity manifest revision mismatch")
    matches = document.get("matches") or {}
    return {match_id: matches[match_id] for match_id in DEVELOPMENT_MATCHES}


def preflight() -> None:
    authority()
    if set(DEVELOPMENT_MATCHES) != {
        "1886347", "1899585", "1925299", "1996435", "2006229", "2011166",
        "2013725", "2015213", "2017461",
    }:
        raise RuntimeError("development allowlist changed")
    selected_source_authority()
    print("Session 6a preflight passed")


def run_audit(write_replay: bool) -> tuple[dict, bytes]:
    freeze, _ = authority()
    source = selected_source_authority()
    per_match, combined_lines, product_identities = {}, [], {}
    access_rows = []
    for match_id in sorted(DEVELOPMENT_MATCHES, key=int):
        alias = ALIASES[match_id]
        product_identities[alias] = verify_products(DATA_ROOT, match_id, source[match_id])
        access_rows.append({"match_alias": alias, "products": ["metadata", "events", "tracking"], "purpose": "identity_compatibility"})
        projected = load_projected_match(DATA_ROOT, match_id)
        choices, qc, audit = restricted_prepare_match(match_id, projected)
        lines = canonical_lines(choices)
        combined_lines.extend(lines)
        expected = freeze["matches"][alias]
        replay_hash = hashlib.sha256(("\n".join(lines) + "\n").encode()).hexdigest()
        comparisons = {
            "evaluation_eligible": qc["evaluation_eligible"] == expected["evaluation_eligible"],
            "fit_eligible": qc["fit_eligible"] == expected["fit_eligible"],
            "exclusions": qc["exclusions"] == expected["exclusions"],
            "target_outside": qc["target_outside"] == expected["target_outside"],
            "target_outside_reasons": qc["target_outside_reasons"] == expected["target_outside_reasons"],
            "population_sha256": replay_hash == expected["population_sha256"],
        }
        per_match[alias] = {
            "raw_pass_attempts": qc["raw_pass_attempts"],
            "evaluation_eligible": qc["evaluation_eligible"],
            "fit_eligible": qc["fit_eligible"],
            "exclusions": qc["exclusions"],
            "target_outside": qc["target_outside"],
            "target_outside_reasons": qc["target_outside_reasons"],
            "population_sha256": replay_hash,
            "authority_match": comparisons,
            "identity_audit": audit,
        }
    replay_bytes = (("\n".join(combined_lines) + "\n").encode())
    totals = {
        "raw_pass_attempts": sum(item["raw_pass_attempts"] for item in per_match.values()),
        "evaluation_eligible": sum(item["evaluation_eligible"] for item in per_match.values()),
        "fit_eligible": sum(item["fit_eligible"] for item in per_match.values()),
    }
    replay_hash = hashlib.sha256(replay_bytes).hexdigest()
    exact_per_match = all(all(item["authority_match"].values()) for item in per_match.values())
    byte_equal = replay_bytes == safe_authoritative_population().read_bytes()
    result = {
        "schema_version": "1.0.0", "source_commit": SOURCE,
        "authority_commit": START_AUTHORITY, "development_match_count": 9,
        "totals": totals, "combined_population_sha256": replay_hash,
        "expected_population_sha256": POPULATION_SHA,
        "exact_per_match_authority": exact_per_match,
        "byte_equal_authoritative_population": byte_equal,
        "per_match": per_match, "product_identities": product_identities,
    }
    if write_replay:
        atomic(REPLAY, replay_bytes.decode())
        atomic(DETAILS, json_text(result))
        ACCESS_LEDGER.parent.mkdir(parents=True, exist_ok=True)
        with ACCESS_LEDGER.open("a", encoding="utf-8") as handle:
            for row in access_rows:
                handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    return result, replay_bytes


def aggregate_forms(per_match: dict) -> dict:
    categories = next(iter(per_match.values()))["identity_audit"]["identity_forms"]
    return {
        scope: {form: sum(item["identity_audit"]["identity_forms"][scope][form] for item in per_match.values()) for form in values}
        for scope, values in categories.items()
    }


def audit() -> None:
    preflight()
    result, _ = run_audit(write_replay=False)
    print(json.dumps({"totals": result["totals"], "identity_forms": aggregate_forms(result["per_match"])}, sort_keys=True))


def replay() -> None:
    preflight()
    result, _ = run_audit(write_replay=True)
    pass_conditions = (
        result["totals"]["evaluation_eligible"] == EXPECTED["evaluation_eligible"]
        and result["totals"]["fit_eligible"] == EXPECTED["fit_eligible"]
        and result["combined_population_sha256"] == POPULATION_SHA
        and result["exact_per_match_authority"]
        and result["byte_equal_authoritative_population"]
    )
    decision = "PASS — Identity contract compatible" if pass_conditions else "FAIL — Replay mismatch"
    compact_matches = {}
    for alias, item in result["per_match"].items():
        compact_matches[alias] = {
            "raw_pass_attempts": item["raw_pass_attempts"],
            "evaluation_eligible": item["evaluation_eligible"],
            "fit_eligible": item["fit_eligible"],
            "exclusions": item["exclusions"], "target_outside": item["target_outside"],
            "authority_match": item["authority_match"],
            "identity_audit": item["identity_audit"],
        }
    summary = {
        "schema_version": "1.0.0", "decision": decision,
        "source_commit": SOURCE, "authority_commit": START_AUTHORITY,
        "development_match_count": 9, "totals": result["totals"],
        "evaluation_and_fit_are_separate": True,
        "combined_population_sha256": result["combined_population_sha256"],
        "byte_equal_authoritative_population": result["byte_equal_authoritative_population"],
        "exact_per_match_authority": result["exact_per_match_authority"],
        "matches": compact_matches,
    }
    atomic(SUMMARY, json_text(summary))
    manifest = {
        "schema_version": "1.0.0", "decision": decision,
        "source_commit": SOURCE, "authority_commit": START_AUTHORITY,
        "protocol_commit": git("log", "-1", "--format=%H", "--", str(PROTOCOL.relative_to(ROOT))),
        "protocol_sha256": sha(PROTOCOL),
        "implementation_sha256": {name: sha(ROOT / name) for name in IMPLEMENTATION_FILES},
        "environment": {
            "python": platform.python_version(), "platform": platform.platform(),
            "uv_lock_sha256": sha(ROOT / "uv.lock"),
        },
        "development_match_aliases": sorted(ALIASES.values()),
        "population_authority_sha256": POPULATION_SHA,
        "population_replay_sha256": sha(REPLAY),
        "output_sha256": {"summary.json": sha(SUMMARY)},
    }
    atomic(MANIFEST, json_text(manifest))
    print(json.dumps({"decision": decision, "totals": result["totals"], "population_sha256": result["combined_population_sha256"]}))
    if not pass_conditions:
        raise RuntimeError(decision)


def publication_check() -> None:
    authority()
    if not SUMMARY.is_file() or not MANIFEST.is_file():
        raise RuntimeError("public Session 6a outputs are missing")
    summary = json.loads(SUMMARY.read_text())
    manifest = json.loads(MANIFEST.read_text())
    if summary.get("schema_version") != "1.0.0" or manifest.get("schema_version") != "1.0.0":
        raise RuntimeError("unexpected public output schema")
    if summary.get("decision") != "PASS — Identity contract compatible" or manifest.get("decision") != summary["decision"]:
        raise RuntimeError("public decision mismatch")
    if summary.get("totals") != {"raw_pass_attempts": 7292, "evaluation_eligible": 7227, "fit_eligible": 7227}:
        raise RuntimeError("public eligibility totals mismatch")
    if set(summary.get("matches", {})) != set(ALIASES.values()):
        raise RuntimeError("public match alias coverage mismatch")
    if not summary.get("byte_equal_authoritative_population") or not summary.get("exact_per_match_authority"):
        raise RuntimeError("public replay authority did not pass")
    if manifest.get("population_replay_sha256") != POPULATION_SHA or sha(REPLAY) != POPULATION_SHA:
        raise RuntimeError("ignored replay hash mismatch")
    if manifest["output_sha256"]["summary.json"] != sha(SUMMARY):
        raise RuntimeError("public summary hash mismatch")
    # Field-class labels such as ``event_id`` are allowed because the summary
    # reports only counts. Actual provider IDs, row fields, paths, and geometry
    # remain prohibited.
    prohibited = re.compile(
        r"(?i)(candidate_ids|candidate_xy|defender_xy|carrier_xy|timestamp\s*[:=]|"
        r"/users/|data/session_02|\b\d{7}\b)"
    )
    for path in (SUMMARY, MANIFEST):
        if prohibited.search(path.read_text()):
            raise RuntimeError(f"publication guard rejected {path.name}")
    if git("status", "--porcelain", "--", "data/session_02", "outputs/receiver_ranking_m0_m1/local"):
        raise RuntimeError("governed raw or authoritative population material changed")
    print("Session 6a publication check passed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "audit", "replay", "publication-check"))
    command = parser.parse_args().command
    {"preflight": preflight, "audit": audit, "replay": replay, "publication-check": publication_check}[command]()


if __name__ == "__main__":
    main()
