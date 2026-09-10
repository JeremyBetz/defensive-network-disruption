#!/usr/bin/env python3
"""Metadata-only Session 6b Git/LFS identity review."""

from __future__ import annotations

import argparse
import ast
import fnmatch
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defensive_network_disruption.data.git_lfs_integrity import (  # noqa: E402
    GitHubMetadataClient,
    IntegrityError,
    assess_identity,
    git_blob_oid,
    parse_lfs_pointer,
    project_json_value,
)

START = "045d24ab014a2962d9da046bf0b2efc3eb805664"
PROTOCOL_COMMIT = "bdae204fd294493f83b2bff075dcff533a56291b"
SOURCE_COMMIT = "02a396ffd09b283c9f092fdedeff11da6d535b66"
SOURCE_TREE = "44fd5081d0e6a441dbafadd12c51d6ffca8ab98b"
OWNER_REPO = "SkillCorner/opendata"
PROTOCOL = ROOT / "docs/protocols/phase_06b_tracking_integrity_review.md"
SESSION1_MANIFEST = ROOT / "data/manifests/skillcorner_opendata_02a396f.local.json"
SESSION1_CODE = ROOT / "docs/provenance/session_01/schema_inventory_reader.original.py.txt"
SESSION2_LEDGER = ROOT / "outputs/development_compatibility/local/access_ledger.jsonl"
SESSION6A_DETAILS = ROOT / "outputs/identity_compatibility/local/audit_details.json"
SESSION6_LEDGER = ROOT / "outputs/reserved_evaluation/local/access_ledger.jsonl"
SESSION6_SOURCE = ROOT / "src/defensive_network_disruption/data/session6_source.py"
OUTPUT = ROOT / "outputs/tracking_integrity_review"
LOCAL = OUTPUT / "local"
ACCESS_LEDGER = LOCAL / "access_ledger.jsonl"
IDENTITY_OUTPUT = OUTPUT / "identity_comparison.json"
DIAGNOSTICS_OUTPUT = OUTPUT / "verifier_diagnostics.json"
MANIFEST_OUTPUT = OUTPUT / "manifest.json"
FILES = {
    "reserved_01": {
        "match_id": "1874553",
        "path": "data/matches/1874553/1874553_tracking_extrapolated.jsonl",
    },
    "development_01": {
        "match_id": "1886347",
        "path": "data/matches/1886347/1886347_tracking_extrapolated.jsonl",
    },
}
IMPLEMENTATION_FILES = (
    "scripts/session_06b_tracking_integrity.py",
    "src/defensive_network_disruption/data/git_lfs_integrity.py",
    "tests/test_session6b_tracking_integrity.py",
)


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_text(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"


def atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)


def committed_sha(commit: str, relative: str) -> str:
    content = subprocess.run(
        ["git", "show", f"{commit}:{relative}"], cwd=ROOT, check=True, capture_output=True
    ).stdout
    return hashlib.sha256(content).hexdigest()


def verify_closed_manifest(directory: Path) -> None:
    manifest = json.loads((directory / "manifest.json").read_text())
    for name, digest in manifest["output_sha256"].items():
        if sha(directory / name) != digest:
            raise RuntimeError(f"closed artifact changed: {directory.name}/{name}")


def verify_authority() -> None:
    if git("rev-parse", "HEAD") == START:
        raise RuntimeError("Phase 6b protocol and implementation are not committed")
    if subprocess.run(["git", "merge-base", "--is-ancestor", START, "HEAD"], cwd=ROOT).returncode:
        raise RuntimeError("Session 6 closing authority is not an ancestor")
    if git("rev-parse", PROTOCOL_COMMIT) != PROTOCOL_COMMIT:
        raise RuntimeError("Phase 6b protocol commit is unavailable")
    if sha(PROTOCOL) != committed_sha(PROTOCOL_COMMIT, str(PROTOCOL.relative_to(ROOT))):
        raise RuntimeError("Phase 6b protocol changed")
    if SOURCE_COMMIT != "02a396ffd09b283c9f092fdedeff11da6d535b66":
        raise RuntimeError("source revision changed")
    for directory in (
        ROOT / "outputs/receiver_ranking_m0_m1",
        ROOT / "outputs/m1_failure_mode_audit",
        ROOT / "outputs/receiver_ranking_m2",
        ROOT / "outputs/identity_compatibility",
    ):
        verify_closed_manifest(directory)
    if sha(ROOT / "outputs/reserved_evaluation/final_development_models.json") != "0383561e45bcd9f8d84eccc7e9733b2409536f61c39193fa87d08c36c6f6fd65":
        raise RuntimeError("Session 6 final development model authority changed")
    if sha(ROOT / "docs/session_06_reserved_evaluation_decision_brief.md") != "0618352da55c5ef0d03d1953259c8cfd158cfb23e0d7ea0ea5d32e3fda552db4":
        raise RuntimeError("Session 6 invalid decision record changed")
    if sha(SESSION6_LEDGER) != "03472df87bbc77e93b7d08bd7a1b646a325a4fcb05f11c89cbaed01230db8329":
        raise RuntimeError("Session 6 access ledger changed")


def implementation_hashes() -> dict[str, str]:
    return {name: sha(ROOT / name) for name in IMPLEMENTATION_FILES}


def ensure_implementation_committed() -> str:
    for name in IMPLEMENTATION_FILES:
        git("ls-files", "--error-unmatch", name)
        if sha(ROOT / name) != committed_sha("HEAD", name):
            raise RuntimeError(f"implementation is not committed and intact: {name}")
    if git("status", "--porcelain"):
        raise RuntimeError("metadata review requires a clean tree")
    return git("rev-parse", "HEAD")


def forbidden_imports() -> list[str]:
    prohibited = {
        "session6_population", "receiver_choices", "ranking_metrics", "choice_model",
        "ranking_features", "session5", "numpy", "scipy", "pandas", "kloppy",
    }
    found: list[str] = []
    for name in IMPLEMENTATION_FILES[:2]:
        tree = ast.parse((ROOT / name).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = [item.name for item in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = [node.module or ""]
            else:
                continue
            for module in modules:
                if any(part in prohibited for part in module.split(".")):
                    found.append(f"{name}:{module}")
    return found


def preflight() -> None:
    verify_authority()
    if forbidden_imports():
        raise RuntimeError("prohibited scientific or parsing import")
    if set(FILES) != {"reserved_01", "development_01"}:
        raise RuntimeError("identity-review alias allowlist changed")
    if any(path.exists() for path in (IDENTITY_OUTPUT, DIAGNOSTICS_OUTPUT, MANIFEST_OUTPUT)):
        raise RuntimeError("integrity-review outputs already exist")
    for path in (SESSION1_MANIFEST, SESSION1_CODE, SESSION2_LEDGER, SESSION6A_DETAILS, SESSION6_LEDGER):
        if path.is_symlink() or not path.is_file():
            raise RuntimeError(f"required local evidence is missing or unsafe: {path.name}")
    print("Session 6b preflight passed")


def manifest_tracking_claim(match_id: str) -> dict:
    text = SESSION1_MANIFEST.read_text()
    match_position = text.find(json.dumps(match_id) + ":")
    if match_position < 0:
        raise IntegrityError("session1_match_claim_missing")
    tracking, _ = project_json_value(text, "tracking_extrapolated.jsonl", start=match_position)
    if not isinstance(tracking, dict):
        raise IntegrityError("session1_tracking_claim_missing")
    permitted = {
        "path", "git_object_sha", "git_object_size", "lfs_payload_sha256",
        "lfs_declared_payload_size", "payload_integrity", "payload_schema",
    }
    if not set(tracking).issubset(permitted):
        raise IntegrityError("session1_tracking_claim_unexpected_field")
    return {key: tracking.get(key) for key in sorted(permitted)}


def project_session2_tracking(match_id: str) -> dict:
    text = SESSION2_LEDGER.read_text()
    marker = f'"match_id": "{match_id}"'
    position = 0
    while True:
        position = text.find(marker, position)
        if position < 0:
            raise IntegrityError("session2_tracking_record_missing")
        start = text.rfind("{", 0, position)
        record, _ = json.JSONDecoder().raw_decode(text[start:])
        if record.get("product") == "tracking":
            return {key: record.get(key) for key in ("bytes", "path", "sha256")}
        position += len(marker)


def project_session6a_tracking(alias: str) -> dict:
    text = SESSION6A_DETAILS.read_text()
    section_position = text.find(json.dumps("product_identities") + ":")
    alias_position = text.find(json.dumps(alias) + ":", section_position)
    if section_position < 0 or alias_position < 0:
        raise IntegrityError("session6a_identity_section_missing")
    record, _ = project_json_value(text, "tracking", start=alias_position)
    if not isinstance(record, dict):
        raise IntegrityError("session6a_tracking_record_missing")
    return {key: record.get(key) for key in (
        "git_pointer_object_sha", "lfs_payload_sha256", "payload_size"
    )}


def project_session6_failure() -> dict:
    records = [json.loads(line) for line in SESSION6_LEDGER.read_text().splitlines()]
    tracking = [item for item in records if item.get("match_alias") == "reserved_01" and item.get("product") == "tracking"]
    return {
        "started": sum(item.get("status") == "started" for item in tracking),
        "failed": sum(item.get("status") == "failed" for item in tracking),
        "completed": sum(item.get("status") == "completed" for item in tracking),
        "retained_comparison_components": False,
    }


def append_access(label: str, status: str) -> None:
    LOCAL.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(), "phase": "session_06b",
        "command": "review", "protocol_commit": PROTOCOL_COMMIT,
        "implementation_commit": git("rev-parse", "HEAD"), "request_label": label,
        "status": status, "tracking_payload_requested": False,
    }
    with ACCESS_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True, separators=(",", ":")) + "\n")


def github_token() -> str:
    token = subprocess.run(["gh", "auth", "token"], check=True, capture_output=True, text=True).stdout.strip()
    if not token:
        raise RuntimeError("GitHub token unavailable")
    return token


def source_checkout_status() -> dict:
    candidates = (
        ROOT / "vendor/skillcorner-opendata",
        ROOT / ".cache/skillcorner-opendata",
        ROOT.parent / "opendata",
    )
    present = [str(path) for path in candidates if path.exists()]
    return {
        "documented_checkout_found": False,
        "checked_candidate_count": len(candidates),
        "undocumented_candidate_present": bool(present),
        "checkout_object_review": "not_evaluated_no_documented_checkout",
    }


def upstream_identity(client: GitHubMetadataClient, alias: str, claim: dict) -> dict:
    path = FILES[alias]["path"]
    contents = client.contents_metadata(OWNER_REPO, SOURCE_COMMIT, path, label=f"{alias}_contents")
    blob, envelope = client.blob(
        OWNER_REPO, contents["blob_oid"], label=f"{alias}_blob", decoded_limit=1024
    )
    result = assess_identity(
        expected_path=path, observed_path=contents["path"],
        expected_blob_oid=claim["git_object_sha"],
        expected_pointer_size=claim["git_object_size"],
        contents_blob_oid=contents["blob_oid"],
        contents_reported_size=contents["reported_size"],
        envelope_blob_oid=envelope["blob_oid"],
        envelope_reported_size=envelope["reported_size"], decoded_blob=blob,
        expected_lfs_oid=claim["lfs_payload_sha256"],
        expected_lfs_size=claim["lfs_declared_payload_size"],
    )
    result["pointer_lines"] = {
        "version": result["pointer"]["version"],
        "oid_sha256": result["pointer"]["payload_sha256"],
        "size": result["pointer"]["payload_size"],
    }
    del result["pointer"]
    return result


def lfs_attribute_applies(lines: list[str], path: str) -> bool:
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        fields = stripped.split()
        if len(fields) >= 5 and fnmatch.fnmatchcase(path, fields[0]):
            attributes = set(fields[1:])
            if {"filter=lfs", "diff=lfs", "merge=lfs", "-text"}.issubset(attributes):
                return True
    return False


def review() -> None:
    preflight()
    implementation_commit = ensure_implementation_committed()
    claims = {alias: manifest_tracking_claim(item["match_id"]) for alias, item in FILES.items()}
    existing = {
        "reserved_01": {
            "session_01": claims["reserved_01"],
            "session_06_failure": project_session6_failure(),
        },
        "development_01": {
            "session_01": claims["development_01"],
            "session_02": project_session2_tracking(FILES["development_01"]["match_id"]),
            "session_06a": project_session6a_tracking("development_01"),
        },
    }
    client = GitHubMetadataClient(github_token(), hook=append_access)
    upstream_tree = client.commit_tree(OWNER_REPO, SOURCE_COMMIT)
    if upstream_tree != SOURCE_TREE:
        raise IntegrityError("pinned_commit_tree_mismatch")
    upstream = {alias: upstream_identity(client, alias, claims[alias]) for alias in FILES}

    attributes_meta = client.contents_metadata(
        OWNER_REPO, SOURCE_COMMIT, ".gitattributes", label="gitattributes_contents"
    )
    attributes_blob, attributes_envelope = client.blob(
        OWNER_REPO, attributes_meta["blob_oid"], label="gitattributes_blob", decoded_limit=16_384
    )
    if git_blob_oid(attributes_blob) != attributes_meta["blob_oid"] or attributes_envelope["reported_size"] != len(attributes_blob):
        raise IntegrityError("gitattributes_blob_mismatch")
    try:
        attribute_lines = attributes_blob.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise IntegrityError("gitattributes_non_utf8") from exc
    lfs_rule = all(lfs_attribute_applies(attribute_lines, item["path"]) for item in FILES.values())

    unique = all(
        result["checks"]["path_matches"]
        and result["checks"]["tree_vs_contents_blob_oid"]
        and result["checks"]["tree_vs_envelope_blob_oid"]
        and result["checks"]["decoded_blob_oid_matches"]
        and result["checks"]["tree_pointer_size_matches_decoded"]
        and result["checks"]["envelope_size_matches_decoded"]
        and result["checks"]["recorded_lfs_oid_matches_pointer"]
        and result["checks"]["recorded_lfs_size_matches_pointer"]
        for result in upstream.values()
    )
    systematic_size_semantics = all(
        not result["checks"]["contents_size_matches_decoded"]
        and result["checks"]["contents_size_matches_payload"]
        and result["frozen_session6_hash_check"]
        for result in upstream.values()
    )
    classification = (
        "B — PROVENANCE BUG RECOVERABLE WITH BOUNDED REPAIR"
        if unique and systematic_size_semantics and lfs_rule
        else "D — PAYLOAD IDENTITY AMBIGUOUS — DO NOT RERUN"
    )
    comparison = {
        "schema_version": "1.0.0", "source_commit": SOURCE_COMMIT,
        "source_tree": SOURCE_TREE, "upstream_tree_verified": upstream_tree == SOURCE_TREE,
        "aliases": {
            alias: {
                "git_blob_oid": upstream[alias]["git_blob_oid"],
                "git_pointer_size": upstream[alias]["git_pointer_size"],
                "contents_reported_size": upstream[alias]["contents_reported_size"],
                "blob_envelope_reported_size": upstream[alias]["blob_envelope_reported_size"],
                "lfs_payload_sha256": upstream[alias]["pointer_lines"]["oid_sha256"],
                "lfs_declared_payload_size": upstream[alias]["pointer_lines"]["size"],
                "identity_unique_at_pin": unique,
            }
            for alias in sorted(upstream)
        },
        "evidence_sources": {
            "session_01_manifest": "contemporaneous",
            "session_02_development_acquisition": "contemporaneous",
            "session_06a_development_verification": "contemporaneous",
            "session_06_failure_components": "unavailable",
            "upstream_pinned_metadata": "reconstructed",
            "local_source_checkout": source_checkout_status()["checkout_object_review"],
        },
    }
    diagnostics = {
        "schema_version": "1.0.0", "classification": classification,
        "cause": "contents_api_payload_size_compared_with_decoded_lfs_pointer_size",
        "aliases": {
            alias: {
                "checks": upstream[alias]["checks"],
                "frozen_session6_hash_check": upstream[alias]["frozen_session6_hash_check"],
                "frozen_session6_size_check": upstream[alias]["frozen_session6_size_check"],
                "frozen_session6_combined_check": upstream[alias]["frozen_session6_combined_check"],
            }
            for alias in sorted(upstream)
        },
        "git_lfs_rule_verified": lfs_rule,
        "session_01_tree_identity_correct": unique,
        "pointer_payload_semantics_conflated": systematic_size_semantics,
        "issue_scope": "verifier_wide_for_tested_tracking_paths" if systematic_size_semantics else "unresolved",
        "historical_failure_components": existing["reserved_01"]["session_06_failure"],
        "local_checkout": source_checkout_status(),
        "tracking_payload_requested": False,
        "tracking_payload_integrity": "unverified_not_downloaded",
        "population_prepared": False, "models_fitted_or_scored": False,
        "passages_inspected": False,
    }
    atomic(IDENTITY_OUTPUT, json_text(comparison))
    atomic(DIAGNOSTICS_OUTPUT, json_text(diagnostics))
    manifest = {
        "schema_version": "1.0.0", "status": "closed",
        "starting_authority": START, "protocol_commit": PROTOCOL_COMMIT,
        "protocol_sha256": sha(PROTOCOL), "implementation_commit": implementation_commit,
        "implementation_sha256": implementation_hashes(),
        "source_commit": SOURCE_COMMIT, "source_tree": SOURCE_TREE,
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "output_sha256": {
            "identity_comparison.json": sha(IDENTITY_OUTPUT),
            "verifier_diagnostics.json": sha(DIAGNOSTICS_OUTPUT),
        },
    }
    atomic(MANIFEST_OUTPUT, json_text(manifest))
    publication_check()
    print(json.dumps({"classification": classification, "cause": diagnostics["cause"]}))


def publication_check() -> None:
    verify_authority()
    if not all(path.is_file() for path in (IDENTITY_OUTPUT, DIAGNOSTICS_OUTPUT, MANIFEST_OUTPUT)):
        raise RuntimeError("integrity-review output package is incomplete")
    identity = json.loads(IDENTITY_OUTPUT.read_text())
    diagnostics = json.loads(DIAGNOSTICS_OUTPUT.read_text())
    manifest = json.loads(MANIFEST_OUTPUT.read_text())
    if set(identity) != {"schema_version", "source_commit", "source_tree", "upstream_tree_verified", "aliases", "evidence_sources"}:
        raise RuntimeError("identity comparison schema invalid")
    if set(identity["aliases"]) != set(FILES) or set(diagnostics["aliases"]) != set(FILES):
        raise RuntimeError("alias coverage invalid")
    if diagnostics["tracking_payload_requested"] is not False or diagnostics["population_prepared"] is not False or diagnostics["models_fitted_or_scored"] is not False:
        raise RuntimeError("scope firewall failed")
    if manifest.get("status") != "closed" or manifest.get("source_commit") != SOURCE_COMMIT:
        raise RuntimeError("manifest authority invalid")
    for name, digest in manifest["output_sha256"].items():
        if sha(OUTPUT / name) != digest:
            raise RuntimeError(f"output hash mismatch: {name}")
    prohibited = re.compile(
        r"(?i)(/users/|candidate|coordinate|timestamp|player_id|event_id|mrr|hit_at|"
        r"media\.githubusercontent|git-lfs.*objects/batch|tracking_extrapolated\.jsonl)"
    )
    for path in (IDENTITY_OUTPUT, DIAGNOSTICS_OUTPUT, MANIFEST_OUTPUT):
        if prohibited.search(path.read_text()):
            raise RuntimeError(f"publication guard rejected {path.name}")
    print("Session 6b publication check passed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "review", "publication-check"))
    command = parser.parse_args().command
    {"preflight": preflight, "review": review, "publication-check": publication_check}[command]()


if __name__ == "__main__":
    main()
