"""Exact representation comparisons for prepared geometry records."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import struct
from typing import Any

import numpy as np


@dataclass(frozen=True)
class Difference:
    """One exact structural or scalar difference at a private object path."""

    path: str
    category: str
    left_type: str
    right_type: str
    left_value: Any = None
    right_value: Any = None
    absolute_difference: float | None = None
    bit_equal: bool | None = None
    signed_zero_equal: bool | None = None


def historical_json_bytes(value: Any) -> bytes:
    """Serialize with the exact Session 14R JSON expression and UTF-8 encoding."""

    return (json.dumps(value, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    """Return a lowercase SHA-256 fingerprint."""

    return hashlib.sha256(value).hexdigest()


def type_category(value: Any) -> str:
    """Return a stable public type category without values or identities."""

    if isinstance(value, np.generic):
        return f"numpy_{value.dtype.name}"
    if isinstance(value, dict):
        return "mapping"
    if isinstance(value, tuple):
        return "tuple"
    if isinstance(value, list):
        return "list"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "float"
    if value is None:
        return "null"
    if isinstance(value, str):
        return "string"
    return type(value).__name__


def float64_bits(value: Any) -> str:
    """Return the exact big-endian IEEE-754 binary64 bits of a real scalar."""

    if isinstance(value, bool) or not isinstance(value, (int, float, np.number)):
        raise TypeError("value must be a real numeric scalar")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("value must be finite")
    return struct.pack(">d", number).hex()


def _record(path: str, category: str, left: Any, right: Any, **extra: Any) -> Difference:
    return Difference(path, category, type_category(left), type_category(right),
                      left, right, **extra)


def compare_exact(left: Any, right: Any, path: str = "$", differences: list[Difference] | None = None) -> list[Difference]:
    """Compare nested values without coercion, normalization, sorting, or tolerance."""

    result = differences if differences is not None else []
    left_mapping, right_mapping = isinstance(left, dict), isinstance(right, dict)
    if left_mapping or right_mapping:
        if not (left_mapping and right_mapping):
            result.append(_record(path, "container_type", left, right))
            return result
        left_keys, right_keys = tuple(left), tuple(right)
        if set(left_keys) != set(right_keys):
            result.append(_record(path, "mapping_keys", left_keys, right_keys))
        elif left_keys != right_keys:
            result.append(_record(path, "mapping_order", left_keys, right_keys))
        for key in left_keys:
            if key in right:
                compare_exact(left[key], right[key], f"{path}.{key}", result)
        return result

    left_sequence = isinstance(left, (list, tuple))
    right_sequence = isinstance(right, (list, tuple))
    if left_sequence or right_sequence:
        if not (left_sequence and right_sequence):
            result.append(_record(path, "container_type", left, right))
            return result
        if type(left) is not type(right):
            result.append(_record(path, "container_type", left, right))
        if len(left) != len(right):
            result.append(_record(path, "sequence_length", len(left), len(right)))
        for index, (left_item, right_item) in enumerate(zip(left, right)):
            compare_exact(left_item, right_item, f"{path}[{index}]", result)
        return result

    numeric = (int, float, np.number)
    if (isinstance(left, numeric) and not isinstance(left, bool) and
            isinstance(right, numeric) and not isinstance(right, bool)):
        left_number, right_number = float(left), float(right)
        if not (math.isfinite(left_number) and math.isfinite(right_number)):
            result.append(_record(path, "nonfinite_numeric", left, right))
            return result
        bits_equal = float64_bits(left) == float64_bits(right)
        signed_zero_equal = not (left_number == right_number == 0.0) or bits_equal
        if type_category(left) != type_category(right):
            result.append(_record(path, "scalar_type", left, right,
                                  absolute_difference=abs(left_number - right_number),
                                  bit_equal=bits_equal, signed_zero_equal=signed_zero_equal))
        if left_number != right_number or not bits_equal or not signed_zero_equal:
            result.append(_record(path, "numeric_value", left, right,
                                  absolute_difference=abs(left_number - right_number),
                                  bit_equal=bits_equal, signed_zero_equal=signed_zero_equal))
        return result

    if type(left) is not type(right):
        result.append(_record(path, "scalar_type", left, right))
    if left != right:
        result.append(_record(path, "scalar_value", left, right))
    return result


def _schema(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _schema(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return {"container": type_category(value), "length": len(value),
                "items": [_schema(item) for item in value]}
    return type_category(value)


def schema_fingerprint(value: Any) -> str:
    """Fingerprint nested names, order, containers, lengths, and scalar types."""

    payload = json.dumps(_schema(value), separators=(",", ":"), allow_nan=False).encode()
    return sha256_bytes(payload)


def semantic_flags(left: Any, right: Any, serialized_equal: bool) -> dict[str, bool | float | int]:
    """Summarize exact representation, structure, numeric, and semantic identity."""

    differences = compare_exact(left, right)
    container_or_order = [item for item in differences if item.category in {
        "container_type", "mapping_order"}]
    structural_breaks = [item for item in differences if item.category in {
        "mapping_keys", "sequence_length", "scalar_value"}]
    numeric = [item for item in differences if item.category == "numeric_value"]
    scalar_types = [item for item in differences if item.category == "scalar_type"]
    maxima = [item.absolute_difference for item in differences
              if item.absolute_difference is not None]
    structural_identity = not structural_breaks
    numerical_identity = not numeric and all(item.bit_equal is not False for item in scalar_types)
    return {
        "python_equality": left == right,
        "representation_identity": not differences,
        "structural_identity": structural_identity,
        "numerical_identity": numerical_identity,
        "semantic_equivalence": structural_identity and numerical_identity and serialized_equal,
        "container_or_order_difference_count": len(container_or_order),
        "scalar_type_difference_count": len(scalar_types),
        "numeric_value_difference_count": len(numeric),
        "maximum_numeric_absolute_difference": max(maxima, default=0.0),
    }


def public_path(path: str) -> str:
    """Remove reconstructive ordinals while retaining the compared schema location."""

    output = []
    inside = False
    for character in path:
        if character == "[":
            inside = True
            output.append("[]")
        elif character == "]":
            inside = False
        elif not inside:
            output.append(character)
    return "".join(output)


def public_difference_rows(differences: list[Difference]) -> list[dict[str, Any]]:
    """Aggregate private differences into sanitized, non-reconstructive rows."""

    groups: dict[tuple[str, str, str, str], list[Difference]] = {}
    for item in differences:
        key = (public_path(item.path), item.category, item.left_type, item.right_type)
        groups.setdefault(key, []).append(item)
    rows = []
    for (path, category, left_type, right_type), items in sorted(groups.items()):
        maxima = [item.absolute_difference for item in items
                  if item.absolute_difference is not None]
        rows.append({
            "path": path, "category": category, "left_type": left_type,
            "right_type": right_type, "count": len(items),
            "all_float64_bits_equal": all(item.bit_equal is not False for item in items),
            "all_signed_zero_equal": all(item.signed_zero_equal is not False for item in items),
            "maximum_numeric_absolute_difference": max(maxima, default=0.0),
        })
    return rows
