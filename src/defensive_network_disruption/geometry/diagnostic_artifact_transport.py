"""File transport for bounded synthetic cross-platform diagnostics."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ARTIFACT_NAME = "session14z-python313-vector-diagnostic"
ARTIFACT_FILENAME = "session14z_ci_diagnostic.json"
MAX_BYTES = 2_000_000


def diagnostic_bytes(record: dict) -> bytes:
    """Return the canonical bytes used by the historical diagnostic."""
    return (json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def write_diagnostic(path: Path, record: dict) -> tuple[int, str]:
    """Write one canonical diagnostic file atomically and return size/hash."""
    path = Path(path)
    if path.name != ARTIFACT_FILENAME or path.is_symlink() or path.exists():
        raise ValueError("unsafe_or_existing_artifact_path")
    raw = diagnostic_bytes(record)
    if len(raw) > MAX_BYTES:
        raise ValueError("diagnostic_artifact_oversized")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name("." + path.name + ".tmp")
    temporary.write_bytes(raw)
    temporary.replace(path)
    return len(raw), sha256_bytes(raw)


def read_verified_diagnostic(path: Path, declared_sha256: str) -> tuple[dict, bytes]:
    """Read one safe diagnostic artifact and require its declared hash."""
    path = Path(path)
    if path.name != ARTIFACT_FILENAME or path.is_symlink() or not path.is_file():
        raise ValueError("invalid_diagnostic_artifact")
    raw = path.read_bytes()
    if len(raw) > MAX_BYTES or sha256_bytes(raw) != declared_sha256:
        raise ValueError("diagnostic_artifact_hash")
    record = json.loads(raw)
    if diagnostic_bytes(record) != raw:
        raise ValueError("diagnostic_artifact_noncanonical")
    return record, raw
