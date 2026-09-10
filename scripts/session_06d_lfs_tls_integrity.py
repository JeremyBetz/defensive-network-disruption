#!/usr/bin/env python3
"""Session 6d transport diagnostics; never downloads football payloads."""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import ssl
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from defensive_network_disruption.data.session6d_tls import (  # noqa: E402
    DOCS, TUPLES, environment_presence, failure, identity, origin, redact,
)

START = "72908fe5cab983e6c30f99fc63fea7fa3bb61589"
PROTOCOL = "docs/protocols/phase_06d_lfs_tls_integrity_review.md"
FILES = (
    "scripts/session_06d_lfs_tls_integrity.py",
    "src/defensive_network_disruption/data/session6d_tls.py",
    "tests/test_session6d_tls.py",
)
OUTPUT = ROOT / "outputs/lfs_tls_integrity_review"
LOCAL = OUTPUT / "local"
LEDGER = LOCAL / "ledger.jsonl"
COMMAND = ""
PUBLIC_FILES = ("environment_summary.json", "endpoint_summary.json", "transport_comparison.json")
CHILD = (
    "import sys,json;sys.path.insert(0,sys.argv[1]);"
    "from defensive_network_disruption.data.session6d_tls import worker;"
    "print(json.dumps(worker(json.load(sys.stdin)),allow_nan=False))"
)


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name("." + path.name + ".tmp")
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")
    os.replace(temporary, path)


def hashes():
    return {name: digest(ROOT / name) for name in FILES}


def protocol_commit():
    return git("log", "--diff-filter=A", "-1", "--format=%H", "--", PROTOCOL)


def immutable_history():
    # Every tracked historical file remains byte-identical; research log is append-only.
    original = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", START], cwd=ROOT, text=True).splitlines()
    log_old = subprocess.check_output(["git", "show", START + ":docs/research_log.md"], cwd=ROOT)
    if not (ROOT / "docs/research_log.md").read_bytes().startswith(log_old):
        raise RuntimeError("historical_log_changed")
    for name in original:
        if name == "docs/research_log.md":
            continue
        expected = subprocess.check_output(["git", "show", START + ":" + name], cwd=ROOT)
        if not (ROOT / name).is_file() or (ROOT / name).read_bytes() != expected:
            raise RuntimeError("historical_tracked_authority_changed:" + name)
    ledgers = {
        "session6": ("outputs/reserved_evaluation/local/access_ledger.jsonl", "03472df87bbc77e93b7d08bd7a1b646a325a4fcb05f11c89cbaed01230db8329"),
        "session6c": ("outputs/reserved_evaluation_v2/local/access_ledger.jsonl", "809aae47bc9d04bcdcd17415815bb09ae5d39afc44c6be6b887399638fe9575d"),
    }
    statuses = {}
    for label, (name, expected) in ledgers.items():
        path = ROOT / name
        if not path.is_file() or path.is_symlink() or digest(path) != expected:
            raise RuntimeError("governed_historical_ledger_changed:" + label)
        statuses[label] = "matches_committed_hash"
    statuses["session6b"] = "not_assigned_new_retrospective_byte_authority"
    return statuses


def preflight():
    if git("status", "--porcelain"):
        raise RuntimeError("clean_tree_required")
    git("merge-base", "--is-ancestor", START, "HEAD")
    pcommit = protocol_commit()
    for name in (PROTOCOL, *FILES):
        expected = subprocess.check_output(["git", "show", (pcommit if name == PROTOCOL else "HEAD") + ":" + name], cwd=ROOT)
        if (ROOT / name).read_bytes() != expected:
            raise RuntimeError("uncommitted_audit_authority")
    immutable_history()
    authority = json.loads((ROOT / "outputs/reserved_evaluation_v2/repair_authority.json").read_text())
    for alias, value in TUPLES.items():
        item = authority["authorized_products"]["reserved" if alias.startswith("reserved") else "development"][alias]["tracking"]
        if (value["pointer"], value["oid"], value["size"]) != (item["git_blob_oid"], item["lfs"]["payload_sha256"], item["lfs"]["payload_size"]):
            raise RuntimeError("frozen_tuple_differs")
    for parent in (OUTPUT, LOCAL):
        if parent.is_symlink():
            raise RuntimeError("symlink_output")
    print("Session 6d preflight passed")


def ledger(label, state, weight=0, result=None):
    LOCAL.mkdir(parents=True, exist_ok=True)
    record = {
        "time": datetime.now(timezone.utc).isoformat(), "session": "6d", "command": COMMAND,
        "probe": label, "state": state, "request_budget": weight,
        "protocol_commit": protocol_commit(), "implementation_commit": git("rev-parse", "HEAD"),
    }
    if result is not None:
        record["result"] = result
    with LEDGER.open("a") as handle:
        handle.write(json.dumps(record, sort_keys=True, allow_nan=False) + "\n")


def budget_used():
    if not LEDGER.exists():
        return 0
    return sum(json.loads(line).get("request_budget", 0) for line in LEDGER.read_text().splitlines())


def begin_command(name):
    preflight()
    LOCAL.mkdir(parents=True, exist_ok=True)
    with (LOCAL / (name + ".started")).open("x") as handle:
        handle.write(git("rev-parse", "HEAD") + "\n")


def network(label, invoke, weight=1):
    if budget_used() + weight > 24:
        raise RuntimeError("diagnostic_budget_exhausted")
    ledger(label, "started", weight)
    try:
        result = invoke()
    except Exception as exc:
        result = failure(exc)
    public_result = {key: value for key, value in result.items() if key not in {"_private_url", "text"}}
    ledger(label, "completed", result=public_result)
    return result


def child(python, payload):
    try:
        result = subprocess.run([python, "-c", CHILD, str(ROOT / "src")], input=json.dumps(payload), text=True, capture_output=True, timeout=30)
    except subprocess.TimeoutExpired:
        return {"status": "failed", "category": "overall_timeout", "retryable": False}
    if result.returncode:
        return {"status": "unavailable", "category": "child_failed", "message": redact(result.stderr)}
    try:
        return json.loads(result.stdout)
    except ValueError:
        return {"status": "failed", "category": "child_protocol_error"}


def tool(args):
    try:
        completed = subprocess.run(args, capture_output=True, text=True, timeout=15)
        return {"available": completed.returncode == 0, "version": redact(completed.stdout.splitlines()[0] if completed.stdout else completed.stderr.splitlines()[0] if completed.stderr else "unavailable")}
    except (OSError, subprocess.TimeoutExpired):
        return {"available": False, "version": "unavailable"}


def python_state(python):
    code = "import json,sys,ssl; p=ssl.get_default_verify_paths(); print(json.dumps({'python':sys.version.split()[0],'ssl':ssl.OPENSSL_VERSION,'default_cafile_present':bool(p.cafile),'default_capath_present':bool(p.capath),'runtime_default_ca':True}))"
    try:
        return json.loads(subprocess.check_output([python, "-c", code], text=True, timeout=15))
    except (OSError, ValueError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return {"status": "unavailable"}


def inspect_environment():
    begin_command("inspect-environment")
    available_lfs = []
    for candidate in (shutil.which("git-lfs"), "/opt/homebrew/bin/git-lfs", "/usr/local/bin/git-lfs"):
        if candidate and os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            available_lfs.append(tool([candidate, "version"]))
    gitcfg = subprocess.run(["git", "config", "--get-regexp", r"^(http\..*|url\..*\.insteadof)$"], cwd=ROOT, capture_output=True, text=True)
    categories = {"proxy": 0, "ssl": 0, "url_rewrite": 0, "other_http": 0}
    insecure = False
    for line in gitcfg.stdout.splitlines():
        key, _, value = line.partition(" ")
        key = key.lower()
        if "proxy" in key:
            categories["proxy"] += 1
        elif "ssl" in key:
            categories["ssl"] += 1
            insecure |= key.endswith("sslverify") and value.lower() == "false"
        elif key.startswith("url."):
            categories["url_rewrite"] += 1
        else:
            categories["other_http"] += 1
    try:
        certifi = {"installed": True, "version": importlib.metadata.version("certifi"), "applies_to_urllib": False}
    except importlib.metadata.PackageNotFoundError:
        certifi = {"installed": False, "version": "unavailable", "applies_to_urllib": False}
    overrides = 0
    hosts = Path("/etc/hosts")
    if hosts.is_file():
        for line in hosts.read_text().splitlines():
            names = line.partition("#")[0].split()[1:]
            overrides += sum(name in {"github.com", "media.githubusercontent.com", "raw.githubusercontent.com"} for name in names)
    result = {
        "schema_version": "1", "venv_python": python_state(sys.executable), "system_python": python_state("/usr/bin/python3"),
        "actual_historical_stack": "urllib.request with Python default SSL context",
        "certifi": certifi, "git": tool(["git", "--version"]), "git_tls_backend": "not_exposed_by_version",
        "curl": tool(["/usr/bin/curl", "--version"]),
        "curl_tls_backend": "SecureTransport (reported by installed curl)",
        "git_lfs": available_lfs[0] if available_lfs else {"available": False, "version": "unavailable"},
        "environment": environment_presence(os.environ), "git_config_categories": categories,
        "git_insecure_override_observed": insecure, "relevant_hosts_overrides": overrides,
        "system_ca_source": "system_trust_store_for_SecureTransport; Python_runtime_defaults_for_SSL",
        "private_ca_paths_published": False, "proxy_presence_proves_interception": False,
        "trust_roots_equivalence": "not_established_by_path_categories_alone",
    }
    ledger("environment_projection", "completed", result={"secrets_retained": False})
    write(OUTPUT / "environment_summary.json", result)
    print(json.dumps(result))


def curl_head(url):
    # -q prevents implicit ~/.curlrc options; no redirects or insecure switches.
    args = ["/usr/bin/curl", "-q", "--head", "--silent", "--show-error", "--proto", "=https", "--connect-timeout", "15", "--max-time", "30", "--max-redirs", "0", url]
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return {"status": "failed", "category": "overall_timeout"}
    if len(result.stdout.encode()) > 65536:
        return {"status": "failed", "category": "headers_oversized"}
    statuses = [line for line in result.stdout.splitlines() if line.startswith("HTTP/")]
    return {"status": "verified" if result.returncode == 0 else "failed", "exit_code": result.returncode, "http_status_lines": statuses[:3], "message": redact(result.stderr), "body_read": False, "redirect_followed": False}


def git_probe():
    args = ["git", "-c", "http.sslVerify=true", "-c", "http.followRedirects=false", "-c", "http.connectTimeout=15", "ls-remote", "https://github.com/SkillCorner/opendata.git", "HEAD"]
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return {"status": "failed", "category": "overall_timeout", "scope": "git_host_only"}
    return {"status": "verified" if result.returncode == 0 else "failed", "message": redact(result.stderr), "scope": "git_host_only", "payload_downloaded": False}


def inspect_endpoint():
    begin_command("inspect-endpoint")
    if not (OUTPUT / "environment_summary.json").exists():
        raise RuntimeError("environment_inspection_required")
    result = {"schema_version": "1", "evidence_category": "current_reproduction", "historical_url_source": "locally_constructed_without_LFS_batch", "historical_host": "media.githubusercontent.com", "probes": {}}
    for alias, value in TUPLES.items():
        url = "https://media.githubusercontent.com/media/SkillCorner/opendata/" + value["revision"] + "/" + value["path"]
        result["probes"][alias] = {}
        for name, python in (("venv_python", sys.executable), ("system_python", "/usr/bin/python3")):
            result["probes"][alias][name] = network(alias + ":" + name + ":HEAD", lambda p=python, u=url: child(p, {"kind": "head", "url": u}))
        result["probes"][alias]["curl"] = network(alias + ":curl:HEAD", lambda u=url: curl_head(u))
    result["verified_certificate_probe"] = network("media:direct_verified_TLS", lambda: child(sys.executable, {"kind": "tls", "host": "media.githubusercontent.com"}))
    result["git_host_comparison"] = network("github:git_ref_advertisement", git_probe, 2)
    write(OUTPUT / "endpoint_summary.json", result)
    print(json.dumps(result))


def compare_git_lfs():
    begin_command("compare-git-lfs")
    environment = json.loads((OUTPUT / "environment_summary.json").read_text())
    endpoint = json.loads((OUTPUT / "endpoint_summary.json").read_text())
    docs = []
    for index, url in enumerate(DOCS):
        item = network("official_documentation_" + str(index + 1), lambda u=url: child(sys.executable, {"kind": "documentation", "url": u}), 0)
        if "text" in item:
            write(LOCAL / ("documentation_" + str(index + 1) + ".json"), item)
            docs.append({"url": url, "sha256": item["sha256"], "status": "retrieved"})
        else:
            docs.append({"url": url, **item})
    batches = {}
    for alias in TUPLES:
        batches[alias] = network(alias + ":batch_metadata", lambda a=alias: child(sys.executable, {"kind": "batch", "alias": a}))
        private_url = batches[alias].pop("_private_url", None)
        if private_url:
            for kind in ("delivery_tls", "delivery_head"):
                batches[alias][kind] = network(alias + ":" + kind, lambda k=kind, u=private_url, o=batches[alias]["delivery_origin"]: child(sys.executable, {"kind": k, "url": u, "official_origin": o}))
    secure = all(value.get("identity_matches") is True and value.get("delivery_tls", {}).get("status") == "verified" for value in batches.values())
    result = {
        "schema_version": "1", "evidence_category": "current_official_protocol_comparison",
        "documentation": docs, "batch_flow": batches, "git_lfs": environment["git_lfs"],
        "git_lfs_live_delivery": "untested" if environment["git_lfs"]["available"] else "unavailable",
        "classification": "B" if secure else "D",
        "classification_basis": "secure_official_batch_origins_and_exact_object_agreement" if secure else "secure_official_delivery_not_established",
        "normal_tls_preserved": True, "exact_object_identity_enforceable": True,
        "independent_payload_hash_and_size_required": True, "protected_rerun_authorized": False,
        "tracking_payload_downloaded": False, "request_budget_used": budget_used(),
        "retained_query_secrets": False, "certificate_failures_retryable": False,
        "python_specific_cause": "not_established", "environment_repair_required": "not_established",
        "historical_cause_limit": "current reproduction cannot identify historical certificate SAN without retained evidence",
    }
    write(OUTPUT / "transport_comparison.json", result)
    close_manifest()
    print(json.dumps(result))


def close_manifest():
    manifest = {
        "schema_version": "1", "status": "closed", "starting_authority": START,
        "protocol_commit": protocol_commit(), "protocol_sha256": digest(ROOT / PROTOCOL),
        "implementation_commit": git("rev-parse", "HEAD"), "implementation_sha256": hashes(),
        "output_sha256": {name: digest(OUTPUT / name) for name in PUBLIC_FILES},
        "ledger_sha256": digest(LEDGER), "historical_ledger_status": immutable_history(),
        "reserved_payload_downloaded_or_parsed": False, "population_prepared": False,
        "empirical_model_fitted_or_scored": False, "probe_budget_reserved": budget_used(),
    }
    write(OUTPUT / "manifest.json", manifest)


def publication_check():
    immutable_history()
    expected_fields = {
        "environment_summary.json": {"schema_version", "venv_python", "system_python", "actual_historical_stack", "certifi", "git", "git_tls_backend", "curl", "curl_tls_backend", "git_lfs", "environment", "git_config_categories", "git_insecure_override_observed", "relevant_hosts_overrides", "system_ca_source", "private_ca_paths_published", "proxy_presence_proves_interception", "trust_roots_equivalence"},
        "endpoint_summary.json": {"schema_version", "evidence_category", "historical_url_source", "historical_host", "probes", "verified_certificate_probe", "git_host_comparison"},
        "transport_comparison.json": {"schema_version", "evidence_category", "documentation", "batch_flow", "git_lfs", "git_lfs_live_delivery", "classification", "classification_basis", "normal_tls_preserved", "exact_object_identity_enforceable", "independent_payload_hash_and_size_required", "protected_rerun_authorized", "tracking_payload_downloaded", "request_budget_used", "retained_query_secrets", "certificate_failures_retryable", "python_specific_cause", "environment_repair_required", "historical_cause_limit"},
    }
    manifest = json.loads((OUTPUT / "manifest.json").read_text())
    if hashes() != manifest["implementation_sha256"] or digest(LEDGER) != manifest["ledger_sha256"]:
        raise RuntimeError("closed_audit_authority_changed")
    for name, fields in expected_fields.items():
        raw = (OUTPUT / name).read_text()
        data = json.loads(raw)
        if set(data) != fields or digest(OUTPUT / name) != manifest["output_sha256"][name]:
            raise RuntimeError("output_schema_or_hash_mismatch:" + name)
        for forbidden in ("/Users/", "?X-Amz", "?token", '"Authorization"', '"Cookie"', '"href"', '"player_id"', '"event_id"'):
            if forbidden in raw:
                raise RuntimeError("publication_secret_or_provider_field:" + name)
    if budget_used() > 24:
        raise RuntimeError("probe_budget_exceeded")
    print("Session 6d publication, authority, and hash checks passed")


def main():
    global COMMAND
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "inspect-environment", "inspect-endpoint", "compare-git-lfs", "publication-check"))
    COMMAND = parser.parse_args().command
    globals()[COMMAND.replace("-", "_")]()


if __name__ == "__main__":
    main()
