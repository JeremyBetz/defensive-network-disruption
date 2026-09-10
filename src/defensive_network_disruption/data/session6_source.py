"""Pinned GitHub acquisition for authorized Session 6 products."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable

SOURCE_COMMIT = "02a396ffd09b283c9f092fdedeff11da6d535b66"
OWNER_REPO = "SkillCorner/opendata"
PRODUCT_SUFFIXES = {
    "metadata": "match.json",
    "events": "dynamic_events.csv",
    "tracking": "tracking_extrapolated.jsonl",
}


class _SameHostRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urllib.parse.urlparse(newurl).hostname != urllib.parse.urlparse(req.full_url).hostname:
            raise PermissionError("cross-host redirect is prohibited")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def source_path(match_id: str, product: str, allowlist: frozenset[str]) -> str:
    match_id = str(match_id)
    if match_id not in allowlist:
        raise PermissionError("match outside explicit Session 6 partition allowlist")
    try:
        suffix = PRODUCT_SUFFIXES[product]
    except KeyError as exc:
        raise PermissionError("product outside Session 6 allowlist") from exc
    return f"data/matches/{match_id}/{match_id}_{suffix}"


def safe_destination(root: Path, match_id: str, product: str, allowlist: frozenset[str]) -> Path:
    relative = source_path(match_id, product, allowlist)
    root = root.resolve()
    cursor = root
    for part in Path(relative).parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise PermissionError("symlink path is prohibited")
    resolved = cursor.resolve(strict=False)
    if not resolved.is_relative_to(root):
        raise PermissionError("destination escapes governed root")
    return resolved


def git_blob_sha1(content: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()  # noqa: S324


def parse_lfs_pointer(content: bytes) -> tuple[str, int]:
    try:
        lines = content.decode("ascii").splitlines()
    except UnicodeDecodeError as exc:
        raise RuntimeError("tracking Git object is not an LFS pointer") from exc
    if len(lines) != 3 or lines[0] != "version https://git-lfs.github.com/spec/v1":
        raise RuntimeError("unexpected LFS pointer format")
    if not lines[1].startswith("oid sha256:") or not lines[2].startswith("size "):
        raise RuntimeError("incomplete LFS pointer")
    digest = lines[1].removeprefix("oid sha256:")
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise RuntimeError("invalid LFS payload identity")
    try:
        size = int(lines[2].removeprefix("size "))
    except ValueError as exc:
        raise RuntimeError("invalid LFS payload size") from exc
    if size <= 0:
        raise RuntimeError("invalid LFS payload size")
    return digest, size


def _json_request(url: str, token: str, opener=None) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "defensive-network-disruption-session-6",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    opener = opener or urllib.request.build_opener(_SameHostRedirect())
    with opener.open(request, timeout=120) as response:
        if urllib.parse.urlparse(response.geturl()).hostname != "api.github.com":
            raise PermissionError("GitHub API host changed")
        return json.load(response)


def _blob(path: str, token: str, opener=None) -> tuple[bytes, dict[str, Any]]:
    quoted = urllib.parse.quote(path, safe="/")
    metadata = _json_request(
        f"https://api.github.com/repos/{OWNER_REPO}/contents/{quoted}?ref={SOURCE_COMMIT}",
        token,
        opener,
    )
    if metadata.get("path") != path or metadata.get("type") != "file":
        raise RuntimeError("source path did not resolve to the requested file")
    sha = metadata.get("sha")
    envelope = _json_request(
        f"https://api.github.com/repos/{OWNER_REPO}/git/blobs/{sha}", token, opener
    )
    if envelope.get("sha") != sha or envelope.get("encoding") != "base64":
        raise RuntimeError("Git blob envelope identity mismatch")
    encoded = "".join(str(envelope["content"]).split())
    content = base64.b64decode(encoded, validate=True)
    if git_blob_sha1(content) != sha or len(content) != metadata.get("size"):
        raise RuntimeError("Git blob hash or size mismatch")
    return content, {"path": path, "git_object_sha": sha, "git_object_size": len(content)}


def _tracking_payload(path: str, pointer: bytes, token: str, opener=None) -> tuple[bytes, dict[str, Any]]:
    payload_sha, payload_size = parse_lfs_pointer(pointer)
    url = f"https://media.githubusercontent.com/media/{OWNER_REPO}/{SOURCE_COMMIT}/{path}"
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}", "User-Agent": "defensive-network-disruption-session-6"},
    )
    opener = opener or urllib.request.build_opener(_SameHostRedirect())
    with opener.open(request, timeout=240) as response:
        if urllib.parse.urlparse(response.geturl()).hostname != "media.githubusercontent.com":
            raise PermissionError("tracking media host changed")
        payload = response.read()
    if len(payload) != payload_size or hashlib.sha256(payload).hexdigest() != payload_sha:
        raise RuntimeError("LFS payload hash or size mismatch")
    return payload, {"lfs_payload_sha256": payload_sha, "lfs_payload_size": payload_size}


def acquire_product(
    root: Path,
    match_id: str,
    product: str,
    allowlist: frozenset[str],
    token: str,
    *,
    opener=None,
    access_hook: Callable[[str, str, str], None] | None = None,
) -> dict[str, Any]:
    """Acquire one pinned product atomically after path and object verification."""
    path = source_path(match_id, product, allowlist)
    destination = safe_destination(root, match_id, product, allowlist)
    if destination.exists():
        raise FileExistsError("Session 6 acquisition destination already exists")
    if access_hook:
        access_hook(str(match_id), product, "started")
    try:
        git_content, identity = _blob(path, token, opener)
        content = git_content
        if product == "tracking":
            content, payload_identity = _tracking_payload(path, git_content, token, opener)
            identity.update(payload_identity)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(f".{destination.name}.tmp")
        temporary.write_bytes(content)
        os.replace(temporary, destination)
        identity["stored_size"] = len(content)
        if access_hook:
            access_hook(str(match_id), product, "completed")
        return identity
    except Exception:
        if access_hook:
            access_hook(str(match_id), product, "failed")
        raise
