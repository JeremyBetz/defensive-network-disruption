"""Session 6c Git/LFS verification and bounded opaque acquisition."""

from __future__ import annotations

import base64
import hashlib
import http.client
import json
import os
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

SOURCE_COMMIT = "02a396ffd09b283c9f092fdedeff11da6d535b66"
OWNER_REPO = "SkillCorner/opendata"
POINTER_LIMIT = 1024
API_LIMIT = 4_000_000
TRANSIENT_HTTP = frozenset({500, 502, 503, 504})
PRODUCT_SUFFIX = {
    "metadata": "match.json",
    "events": "dynamic_events.csv",
    "tracking": "tracking_extrapolated.jsonl",
}
LFS_VERSION = "version https://git-lfs.github.com/spec/v1"
OID64 = re.compile(r"[0-9a-f]{64}")


class IntegrityError(RuntimeError):
    """A non-retryable identity or integrity failure."""


class TransportError(RuntimeError):
    """A retryable transport failure after attempts are exhausted."""


class _RejectRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise IntegrityError("redirect_or_substitution")


@dataclass(frozen=True)
class TreeEntry:
    path: str
    object_type: str
    git_oid: str
    git_size: int


@dataclass(frozen=True)
class LfsPointer:
    payload_sha256: str
    payload_size: int


def source_path(match_id: str, product: str, allowlist: frozenset[str]) -> str:
    if match_id not in allowlist or not match_id.isdigit():
        raise PermissionError("match outside exact partition allowlist")
    if product not in PRODUCT_SUFFIX:
        raise PermissionError("product outside exact allowlist")
    return f"data/matches/{match_id}/{match_id}_{PRODUCT_SUFFIX[product]}"


def safe_destination(root: Path, match_id: str, product: str, allowlist: frozenset[str]) -> Path:
    if root.is_symlink():
        raise PermissionError("destination root is a symlink")
    relative = Path(source_path(match_id, product, allowlist))
    destination = root / relative
    root_resolved = root.resolve()
    if not destination.resolve(strict=False).is_relative_to(root_resolved):
        raise PermissionError("destination escaped ignored root")
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise PermissionError("destination contains a symlink")
    return destination


def git_blob_oid(content: bytes) -> str:
    header = b"blob " + str(len(content)).encode("ascii") + b"\0"
    return hashlib.sha1(header + content).hexdigest()  # noqa: S324 - Git identity


def parse_lfs_pointer(content: bytes) -> LfsPointer:
    if len(content) > POINTER_LIMIT:
        raise IntegrityError("pointer_oversized")
    try:
        lines = content.decode("ascii").splitlines()
    except UnicodeDecodeError as exc:
        raise IntegrityError("pointer_non_ascii") from exc
    while lines and not lines[-1].strip():
        lines.pop()
    if len(lines) != 3 or lines[0] != LFS_VERSION:
        raise IntegrityError("pointer_malformed")
    if not lines[1].startswith("oid sha256:") or not lines[2].startswith("size "):
        raise IntegrityError("pointer_malformed")
    digest = lines[1][len("oid sha256:"):]
    size_text = lines[2][len("size "):]
    if OID64.fullmatch(digest) is None:
        raise IntegrityError("pointer_oid_malformed")
    if not size_text or not size_text.isascii() or not size_text.isdecimal():
        raise IntegrityError("pointer_size_malformed")
    return LfsPointer(digest, int(size_text))


def verify_blob(entry: TreeEntry, envelope: dict[str, Any], *, decoded_limit: int) -> bytes:
    if entry.object_type != "blob":
        raise IntegrityError("unexpected_object_type")
    if envelope.get("sha") != entry.git_oid or envelope.get("encoding") != "base64":
        raise IntegrityError("blob_envelope_identity_mismatch")
    if envelope.get("size") != entry.git_size:
        raise IntegrityError("blob_envelope_size_mismatch")
    encoded = envelope.get("content")
    if not isinstance(encoded, str):
        raise IntegrityError("blob_content_missing")
    try:
        content = base64.b64decode("".join(encoded.split()), validate=True)
    except Exception as exc:
        raise IntegrityError("blob_base64_invalid") from exc
    if len(content) > decoded_limit:
        raise IntegrityError("decoded_blob_oversized")
    if len(content) != entry.git_size:
        raise IntegrityError("decoded_blob_size_mismatch")
    if git_blob_oid(content) != entry.git_oid:
        raise IntegrityError("decoded_blob_oid_mismatch")
    return content


def _transport_category(exc: BaseException) -> str | None:
    if isinstance(exc, urllib.error.HTTPError):
        return f"http_{exc.code}" if exc.code in TRANSIENT_HTTP else None
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return "timeout"
    if isinstance(exc, (ConnectionResetError, ConnectionAbortedError, BrokenPipeError)):
        return "connection_dropped"
    if isinstance(exc, http.client.IncompleteRead):
        return "interrupted_stream"
    if isinstance(exc, urllib.error.URLError):
        reason = exc.reason
        if isinstance(reason, (TimeoutError, socket.timeout)):
            return "timeout"
        if isinstance(reason, (ConnectionResetError, ConnectionAbortedError, BrokenPipeError)):
            return "connection_dropped"
    return None


class Session6cSourceClient:
    """Pinned Git metadata and opaque product client with frozen retries."""

    def __init__(
        self,
        token: str,
        *,
        ledger: Callable[[str, int, str, str | None], None] | None = None,
        opener=None,
        sleeper: Callable[[float], None] = time.sleep,
    ):
        self._token = token
        self._ledger = ledger
        self._opener = opener or urllib.request.build_opener(_RejectRedirects())
        self._sleep = sleeper

    def _request(self, url: str, *, label: str, maximum: int) -> bytes:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https" or parsed.hostname not in {
            "api.github.com", "raw.githubusercontent.com", "media.githubusercontent.com"
        }:
            raise PermissionError("request host prohibited")
        headers = {"Authorization": f"Bearer {self._token}", "User-Agent": "defensive-network-disruption-session-6c"}
        if parsed.hostname == "api.github.com":
            headers.update({"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
        request = urllib.request.Request(url, headers=headers)
        for attempt in range(1, 4):
            if self._ledger:
                self._ledger(label, attempt, "started", None)
            try:
                with self._opener.open(request, timeout=240) as response:
                    if response.geturl() != url:
                        raise IntegrityError("redirect_or_substitution")
                    declared = response.headers.get("Content-Length")
                    if declared is not None and int(declared) > maximum:
                        raise IntegrityError("response_oversized")
                    data = response.read(maximum + 1)
                if len(data) > maximum:
                    raise IntegrityError("response_oversized")
                if declared is not None and len(data) != int(declared):
                    raise IntegrityError("completed_response_size_mismatch")
            except BaseException as exc:
                category = _transport_category(exc)
                if self._ledger:
                    self._ledger(label, attempt, "failed", category or type(exc).__name__)
                if category is None or attempt == 3:
                    if category is not None:
                        raise TransportError(f"transport_retries_exhausted:{category}") from exc
                    raise
                self._sleep(float(attempt))
                continue
            if self._ledger:
                self._ledger(label, attempt, "completed", None)
            return data
        raise AssertionError("unreachable")

    def _json(self, endpoint: str, *, label: str) -> Any:
        if not endpoint.startswith("/") or ".." in endpoint:
            raise PermissionError("unsafe_api_endpoint")
        raw = self._request("https://api.github.com" + endpoint, label=label, maximum=API_LIMIT)
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise IntegrityError("api_json_invalid") from exc

    def tree_entries(self, paths: set[str]) -> tuple[str, dict[str, TreeEntry]]:
        commit = self._json(f"/repos/{OWNER_REPO}/git/commits/{SOURCE_COMMIT}", label="source_commit")
        if commit.get("sha") != SOURCE_COMMIT or not isinstance(commit.get("tree"), dict):
            raise IntegrityError("commit_identity_mismatch")
        tree_oid = commit["tree"].get("sha")
        tree = self._json(f"/repos/{OWNER_REPO}/git/trees/{tree_oid}?recursive=1", label="source_tree")
        if tree.get("sha") != tree_oid or tree.get("truncated") is True:
            raise IntegrityError("tree_identity_or_completeness_failure")
        selected: dict[str, TreeEntry] = {}
        for item in tree.get("tree", []):
            path = item.get("path")
            if path not in paths:
                continue
            if item.get("type") != "blob" or not isinstance(item.get("sha"), str) or not isinstance(item.get("size"), int):
                raise IntegrityError("unexpected_object_type")
            selected[path] = TreeEntry(path, item["type"], item["sha"], item["size"])
        if set(selected) != paths:
            raise IntegrityError("authorized_path_missing_from_tree")
        return tree_oid, selected

    def pointer(self, entry: TreeEntry, *, label: str) -> tuple[LfsPointer, bytes]:
        envelope = self._json(f"/repos/{OWNER_REPO}/git/blobs/{entry.git_oid}", label=label)
        content = verify_blob(entry, envelope, decoded_limit=POINTER_LIMIT)
        return parse_lfs_pointer(content), content

    def acquire(self, entry: TreeEntry, destination: Path, *, pointer: LfsPointer | None, label: str) -> dict[str, Any]:
        if destination.exists():
            raise FileExistsError("verified product already exists; automatic redownload prohibited")
        if pointer is None:
            url = f"https://raw.githubusercontent.com/{OWNER_REPO}/{SOURCE_COMMIT}/{entry.path}"
            maximum = entry.git_size
        else:
            url = f"https://media.githubusercontent.com/media/{OWNER_REPO}/{SOURCE_COMMIT}/{entry.path}"
            maximum = pointer.payload_size
        destination.parent.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(url, headers={
            "Authorization": f"Bearer {self._token}",
            "User-Agent": "defensive-network-disruption-session-6c",
        })
        for attempt in range(1, 4):
            temporary = destination.with_name(f".{destination.name}.{os.getpid()}.{attempt}.tmp")
            if self._ledger:
                self._ledger(label, attempt, "started", None)
            count = 0
            digest = hashlib.sha256()
            git_digest = hashlib.sha1()  # noqa: S324 - Git identity
            git_digest.update(b"blob " + str(entry.git_size).encode("ascii") + b"\0")
            try:
                with self._opener.open(request, timeout=240) as response:
                    if response.geturl() != url:
                        raise IntegrityError("redirect_or_substitution")
                    declared = response.headers.get("Content-Length")
                    if declared is not None and int(declared) > maximum:
                        raise IntegrityError("response_oversized")
                    with temporary.open("xb") as handle:
                        while True:
                            chunk = response.read(min(1024 * 1024, maximum + 1 - count))
                            if not chunk:
                                break
                            count += len(chunk)
                            if count > maximum:
                                raise IntegrityError("response_oversized")
                            handle.write(chunk)
                            digest.update(chunk)
                            git_digest.update(chunk)
                        handle.flush()
                        os.fsync(handle.fileno())
                if declared is not None and count != int(declared):
                    raise IntegrityError("completed_response_size_mismatch")
                if pointer is None:
                    if count != entry.git_size or git_digest.hexdigest() != entry.git_oid:
                        raise IntegrityError("ordinary_blob_integrity_mismatch")
                    identity = {"git_oid": entry.git_oid, "bytes": count}
                else:
                    if count != pointer.payload_size:
                        raise IntegrityError("payload_size_mismatch")
                    if digest.hexdigest() != pointer.payload_sha256:
                        raise IntegrityError("payload_sha256_mismatch")
                    identity = {"lfs_payload_sha256": digest.hexdigest(), "bytes": count}
                os.replace(temporary, destination)
            except BaseException as exc:
                temporary.unlink(missing_ok=True)
                category = _transport_category(exc)
                if self._ledger:
                    self._ledger(label, attempt, "failed", category or type(exc).__name__)
                if category is None or attempt == 3:
                    if category is not None:
                        raise TransportError(f"transport_retries_exhausted:{category}") from exc
                    raise
                self._sleep(float(attempt))
                continue
            if self._ledger:
                self._ledger(label, attempt, "completed", None)
            return identity
        raise AssertionError("unreachable")


def public_entry(entry: TreeEntry, pointer: LfsPointer | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "git_object_type": entry.object_type,
        "git_blob_oid": entry.git_oid,
        "git_blob_size": entry.git_size,
    }
    if pointer is not None:
        result["lfs"] = asdict(pointer)
    return result
