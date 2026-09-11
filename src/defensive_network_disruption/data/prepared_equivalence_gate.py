"""Strict historical-byte gate for an explicitly supplied prepared record."""
from __future__ import annotations

from typing import Any

from .row_equivalence import historical_json_bytes


def require_historical_prepared_bytes(row: Any, preserved_line: bytes) -> bytes:
    """Return reproduced bytes only when they exactly equal the preserved line."""

    if not isinstance(preserved_line, bytes):
        raise TypeError("preserved_line must be bytes")
    reproduced = historical_json_bytes(row)
    if reproduced != preserved_line:
        raise ValueError("prepared_historical_bytes_mismatch")
    return reproduced
