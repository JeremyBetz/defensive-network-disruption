#!/usr/bin/env python3
"""Governed Session 2 acquisition and validation entry point."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defensive_network_disruption.data.skillcorner_session2 import (  # noqa: E402
    DEVELOPMENT_MATCHES,
    SOURCE_COMMIT,
    safe_destination,
    source_path,
)

CHECKPOINT = "292506548728069c88a8e2dcc4835cce743cee1b"
PROTOCOL = ROOT / "docs/protocols/phase_02_development_compatibility.md"
MANIFEST = ROOT / "data/manifests/skillcorner_opendata_02a396f.local.json"
DATA_ROOT = ROOT / "data/session_02"
LOCAL_ROOT = ROOT / "outputs/development_compatibility/local"
LEDGER = LOCAL_ROOT / "access_ledger.jsonl"
OWNER_REPO = "SkillCorner/opendata"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def preflight() -> dict:
    if git("rev-parse", "HEAD") != CHECKPOINT:
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", CHECKPOINT, "HEAD"], cwd=ROOT
        )
        if ancestor.returncode != 0:
            raise RuntimeError("Session 1 checkpoint is not an ancestor of HEAD")
    if not PROTOCOL.is_file() or not MANIFEST.is_file():
        raise RuntimeError("protocol or ignored Session 1 manifest is missing")
    if subprocess.run(["git", "check-ignore", "-q", str(MANIFEST)], cwd=ROOT).returncode != 0:
        raise RuntimeError("detailed manifest is not ignored")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest["source"]["commit"] != SOURCE_COMMIT:
        raise RuntimeError("source revision mismatch")
    if set(manifest["matches"]) != DEVELOPMENT_MATCHES | {
        "1874553", "1927964", "1959846", "1986691", "1996436",
        "2006363", "2007448", "2007721", "2010085", "2016236", "1953632",
    }:
        raise RuntimeError("manifest inventory changed")
    return manifest


def token() -> str:
    return subprocess.run(["gh", "auth", "token"], check=True, capture_output=True, text=True).stdout.strip()


def append_ledger(entry: dict) -> None:
    LOCAL_ROOT.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def download_blob(path: str, destination: Path, expected_sha: str, auth: str) -> dict:
    url = f"https://api.github.com/repos/{OWNER_REPO}/git/blobs/{expected_sha}"
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {auth}", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=60) as response:
        envelope = json.load(response)
    payload = base64.b64decode(envelope["content"])
    actual = hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()
    if actual != expected_sha or envelope["sha"] != expected_sha:
        raise RuntimeError(f"Git blob integrity failure: {path}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)
    return {"git_sha": actual, "bytes": len(payload)}


def download_tracking(path: str, destination: Path, expected_sha256: str, expected_size: int, auth: str) -> dict:
    url = f"https://media.githubusercontent.com/media/{OWNER_REPO}/{SOURCE_COMMIT}/{path}"
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {auth}", "User-Agent": "session-2-development-only"})
    digest = hashlib.sha256()
    size = 0
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(request, timeout=120) as response, destination.open("wb") as handle:
        while block := response.read(1024 * 1024):
            digest.update(block)
            size += len(block)
            handle.write(block)
    if digest.hexdigest() != expected_sha256 or size != expected_size:
        destination.unlink(missing_ok=True)
        raise RuntimeError(f"tracking integrity failure: {path}")
    return {"sha256": digest.hexdigest(), "bytes": size}


def acquire_schema() -> None:
    manifest = preflight()
    auth = token()
    acquired = []
    for match_id in sorted(DEVELOPMENT_MATCHES, key=int):
        for product in ("metadata", "events", "tracking"):
            path = source_path(match_id, product)
            destination = safe_destination(DATA_ROOT, match_id, product)
            record = manifest["matches"][match_id][{
                "metadata": "match.json", "events": "dynamic_events.csv",
                "tracking": "tracking_extrapolated.jsonl",
            }[product]]
            if destination.exists():
                if product == "tracking":
                    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
                    if digest != record["lfs_payload_sha256"] or destination.stat().st_size != record["lfs_declared_payload_size"]:
                        raise RuntimeError(f"existing tracking file failed integrity: {path}")
                    result = {"sha256": digest, "bytes": destination.stat().st_size}
                else:
                    payload = destination.read_bytes()
                    actual = hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()
                    if actual != record["git_object_sha"]:
                        raise RuntimeError(f"existing Git blob failed integrity: {path}")
                    result = {"git_sha": actual, "bytes": len(payload)}
            elif product == "tracking":
                result = download_tracking(path, destination, record["lfs_payload_sha256"], record["lfs_declared_payload_size"], auth)
            else:
                result = download_blob(path, destination, record["git_object_sha"], auth)
            acquired.append({"match_id": match_id, "product": product, "path": path, **result})
    append_ledger({
        "timestamp": datetime.now(timezone.utc).isoformat(), "command": "acquire-schema",
        "source": SOURCE_COMMIT, "protocol_sha256": hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
        "files": acquired,
    })
    print(json.dumps({"status": "ok", "development_matches": 9, "products": 27}))


def main() -> None:
    command = argparse.ArgumentParser()
    command.add_argument("command", choices=("preflight", "acquire-schema", "validate", "publication-check"))
    args = command.parse_args()
    if args.command == "preflight":
        preflight()
        print(json.dumps({"status": "ok", "checkpoint": CHECKPOINT, "development_matches": 9}))
    elif args.command == "acquire-schema":
        acquire_schema()
    else:
        raise SystemExit(f"{args.command} becomes available after the prospective Stage S2B mapping amendment")


if __name__ == "__main__":
    main()
