"""Bounded schema-only readers for provenance-controlled inventory work.

These helpers operate on already-open binary streams. They never initiate network
access. A caller remains responsible for ensuring that its transport does not
prefetch provider content beyond bytes delivered through ``read``.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Mapping
from typing import Any, BinaryIO


class SchemaReadError(ValueError):
    """Raised when content cannot be inspected within the schema-only contract."""


def read_csv_header(stream: BinaryIO, *, max_bytes: int = 64_000) -> tuple[list[str], bytes]:
    """Read exactly one physical CSV header line from ``stream``.

    The helper asks the supplied stream for one byte per call and stops immediately
    after LF. Bytes following LF are neither requested nor returned. This contract
    governs application-level reads; an OS, TLS stack, or buffered transport may
    still prefetch bytes internally.
    """
    if max_bytes < 1:
        raise ValueError("max_bytes must be positive")

    header = bytearray()
    while len(header) < max_bytes:
        byte = stream.read(1)
        if byte == b"":
            raise SchemaReadError("CSV header has no terminating LF")
        if len(byte) != 1:
            raise SchemaReadError("stream violated the one-byte read contract")
        header.extend(byte)
        if byte == b"\n":
            break
    else:
        raise SchemaReadError("CSV header exceeds the configured byte limit")

    raw_header = bytes(header)
    text = raw_header.decode("utf-8-sig")
    if "\n" in text[:-1] or "\r" in text.rstrip("\r\n"):
        raise SchemaReadError("multiline CSV headers are not permitted")
    try:
        rows = list(csv.reader(io.StringIO(text), strict=True))
    except csv.Error as exc:
        raise SchemaReadError("malformed CSV header") from exc
    if len(rows) != 1 or not rows[0] or any(column == "" for column in rows[0]):
        raise SchemaReadError("CSV header must contain one non-empty record")
    if len(rows[0]) != len(set(rows[0])):
        raise SchemaReadError("CSV header contains duplicate columns")
    return rows[0], raw_header


def json_schema(value: Any, path: str = "$") -> dict[str, tuple[str, ...]]:
    """Return JSON paths and types without returning scalar values."""
    found: dict[str, set[str]] = {}

    def visit(current: Any, current_path: str) -> None:
        if current is None:
            kind = "null"
        elif isinstance(current, bool):
            kind = "boolean"
        elif isinstance(current, int):
            kind = "integer"
        elif isinstance(current, float):
            kind = "number"
        elif isinstance(current, str):
            kind = "string"
        elif isinstance(current, list):
            kind = "array"
        elif isinstance(current, Mapping):
            kind = "object"
        else:
            raise TypeError(f"unsupported JSON value type: {type(current).__name__}")
        found.setdefault(current_path, set()).add(kind)
        if isinstance(current, Mapping):
            for key, child in current.items():
                visit(child, f"{current_path}.{key}")
        elif isinstance(current, list):
            for child in current:
                visit(child, f"{current_path}[]")

    visit(value, path)
    return {key: tuple(sorted(types)) for key, types in sorted(found.items())}
