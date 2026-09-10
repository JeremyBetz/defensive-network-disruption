"""Metadata-only Git and Git LFS identity diagnostics."""

from __future__ import annotations

import base64
import hashlib
import json
import re
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any, Callable

POINTER_LIMIT = 1024
JSON_LIMIT = 2_000_000
LFS_VERSION = "version https://git-lfs.github.com/spec/v1"
OID_PATTERN = re.compile(r"[0-9a-f]{64}")


class IntegrityError(RuntimeError):
    """A specifically classified source-identity failure."""


@dataclass(frozen=True)
class LfsPointer:
    version: str
    payload_sha256: str
    payload_size: int


def git_blob_oid(content: bytes) -> str:
    header = b"blob " + str(len(content)).encode("ascii") + b"\0"
    return hashlib.sha1(header + content).hexdigest()  # noqa: S324 - Git object identity


def parse_lfs_pointer(content: bytes, *, limit: int = POINTER_LIMIT) -> LfsPointer:
    if len(content) > limit:
        raise IntegrityError("pointer_oversized")
    try:
        lines = content.decode("ascii").splitlines()
    except UnicodeDecodeError as exc:
        raise IntegrityError("pointer_non_ascii") from exc
    if len(lines) != 3 or lines[0] != LFS_VERSION:
        raise IntegrityError("pointer_malformed")
    if not lines[1].startswith("oid sha256:") or not lines[2].startswith("size "):
        raise IntegrityError("pointer_malformed")
    oid = lines[1].removeprefix("oid sha256:")
    if OID_PATTERN.fullmatch(oid) is None:
        raise IntegrityError("pointer_oid_malformed")
    try:
        size = int(lines[2].removeprefix("size "))
    except ValueError as exc:
        raise IntegrityError("pointer_size_malformed") from exc
    if size <= 0:
        raise IntegrityError("pointer_size_malformed")
    return LfsPointer(LFS_VERSION, oid, size)


def assess_identity(
    *,
    expected_path: str,
    observed_path: str,
    expected_blob_oid: str,
    expected_pointer_size: int,
    contents_blob_oid: str,
    contents_reported_size: int,
    envelope_blob_oid: str,
    envelope_reported_size: int,
    decoded_blob: bytes,
    expected_lfs_oid: str | None = None,
    expected_lfs_size: int | None = None,
) -> dict[str, Any]:
    """Assess every Git/pointer/payload identity dimension independently."""
    pointer = parse_lfs_pointer(decoded_blob)
    actual_oid = git_blob_oid(decoded_blob)
    checks = {
        "path_matches": observed_path == expected_path,
        "tree_vs_contents_blob_oid": expected_blob_oid == contents_blob_oid,
        "tree_vs_envelope_blob_oid": expected_blob_oid == envelope_blob_oid,
        "decoded_blob_oid_matches": expected_blob_oid == actual_oid,
        "tree_pointer_size_matches_decoded": expected_pointer_size == len(decoded_blob),
        "envelope_size_matches_decoded": envelope_reported_size == len(decoded_blob),
        "contents_size_matches_decoded": contents_reported_size == len(decoded_blob),
        "contents_size_matches_payload": contents_reported_size == pointer.payload_size,
        "recorded_lfs_oid_matches_pointer": (
            None if expected_lfs_oid is None else expected_lfs_oid == pointer.payload_sha256
        ),
        "recorded_lfs_size_matches_pointer": (
            None if expected_lfs_size is None else expected_lfs_size == pointer.payload_size
        ),
    }
    return {
        "git_blob_oid": actual_oid,
        "git_pointer_size": len(decoded_blob),
        "contents_reported_size": contents_reported_size,
        "blob_envelope_reported_size": envelope_reported_size,
        "pointer": asdict(pointer),
        "checks": checks,
        "frozen_session6_hash_check": checks["decoded_blob_oid_matches"],
        "frozen_session6_size_check": checks["contents_size_matches_decoded"],
        "frozen_session6_combined_check": (
            checks["decoded_blob_oid_matches"] and checks["contents_size_matches_decoded"]
        ),
    }


def project_json_value(text: str, key: str, *, start: int = 0) -> tuple[Any, int]:
    """Decode only the JSON value immediately following a selected object key."""
    marker = json.dumps(key) + ":"
    index = text.find(marker, start)
    if index < 0:
        marker = json.dumps(key) + ": "
        index = text.find(marker, start)
    if index < 0:
        raise IntegrityError(f"projected_key_missing:{key}")
    value_start = index + len(marker)
    while value_start < len(text) and text[value_start].isspace():
        value_start += 1
    value, consumed = json.JSONDecoder().raw_decode(text[value_start:])
    return value, value_start + consumed


class _RejectRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise PermissionError("redirect_prohibited")


class GitHubMetadataClient:
    """Bounded GitHub API client with no raw/media/LFS download capability."""

    def __init__(self, token: str, *, hook: Callable[[str, str], None] | None = None, opener=None):
        self._token = token
        self._hook = hook
        self._opener = opener or urllib.request.build_opener(_RejectRedirects())

    def _json(self, endpoint: str, *, label: str) -> Any:
        if not endpoint.startswith("/") or ".." in endpoint:
            raise PermissionError("unsafe_api_endpoint")
        url = "https://api.github.com" + endpoint
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https" or parsed.hostname != "api.github.com":
            raise PermissionError("api_host_prohibited")
        request = urllib.request.Request(url, headers={
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "defensive-network-disruption-session-6b",
        })
        if self._hook:
            self._hook(label, "started")
        try:
            with self._opener.open(request, timeout=120) as response:
                if response.geturl() != url:
                    raise PermissionError("response_url_changed")
                declared = response.headers.get("Content-Length")
                if declared is not None and int(declared) > JSON_LIMIT:
                    raise IntegrityError("api_response_oversized")
                raw = response.read(JSON_LIMIT + 1)
            if len(raw) > JSON_LIMIT:
                raise IntegrityError("api_response_oversized")
            result = json.loads(raw)
        except Exception:
            if self._hook:
                self._hook(label, "failed")
            raise
        if self._hook:
            self._hook(label, "completed")
        return result

    def commit_tree(self, owner_repo: str, commit: str) -> str:
        document = self._json(f"/repos/{owner_repo}/git/commits/{commit}", label="commit")
        if document.get("sha") != commit or not isinstance(document.get("tree"), dict):
            raise IntegrityError("commit_identity_mismatch")
        tree = document["tree"].get("sha")
        if not isinstance(tree, str) or len(tree) != 40:
            raise IntegrityError("tree_identity_missing")
        return tree

    def contents_metadata(self, owner_repo: str, commit: str, path: str, *, label: str) -> dict[str, Any]:
        quoted = urllib.parse.quote(path, safe="/")
        document = self._json(
            f"/repos/{owner_repo}/contents/{quoted}?ref={commit}", label=label
        )
        if document.get("path") != path or document.get("type") != "file":
            raise IntegrityError("path_object_mismatch")
        return {"path": path, "blob_oid": document.get("sha"), "reported_size": document.get("size")}

    def blob(self, owner_repo: str, oid: str, *, label: str, decoded_limit: int) -> tuple[bytes, dict[str, Any]]:
        document = self._json(f"/repos/{owner_repo}/git/blobs/{oid}", label=label)
        if document.get("sha") != oid or document.get("encoding") != "base64":
            raise IntegrityError("blob_envelope_mismatch")
        encoded = "".join(str(document.get("content", "")).split())
        maximum_encoded = ((decoded_limit + 2) // 3) * 4 + 4
        if len(encoded) > maximum_encoded:
            raise IntegrityError("decoded_blob_oversized")
        try:
            content = base64.b64decode(encoded, validate=True)
        except ValueError as exc:
            raise IntegrityError("blob_base64_malformed") from exc
        if len(content) > decoded_limit:
            raise IntegrityError("decoded_blob_oversized")
        return content, {"blob_oid": oid, "reported_size": document.get("size")}
