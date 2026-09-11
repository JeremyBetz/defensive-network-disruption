"""Synthetic float-vector reproducibility diagnostics."""
from __future__ import annotations

import math
import struct


def float_bits(value: float) -> str:
    """Return a float64 bit pattern as fixed-width hexadecimal."""
    return f"{struct.unpack('>Q', struct.pack('>d', float(value)))[0]:016x}"


def signed_zero(value: float) -> str | None:
    """Describe a signed zero while leaving nonzero values unlabelled."""
    value = float(value)
    if value != 0.0:
        return None
    return "negative" if math.copysign(1.0, value) < 0.0 else "positive"


def _ordered(bits: int) -> int:
    return 0x8000000000000000 - bits if bits & 0x8000000000000000 else bits + 0x8000000000000000


def ulp_distance(left: float, right: float) -> int | None:
    """Return finite float64 ULP distance; signed zeros have distance zero."""
    left, right = float(left), float(right)
    if not math.isfinite(left) or not math.isfinite(right):
        return None
    if left == 0.0 and right == 0.0:
        return 0
    a = struct.unpack('>Q', struct.pack('>d', left))[0]
    b = struct.unpack('>Q', struct.pack('>d', right))[0]
    return abs(_ordered(a) - _ordered(b))


def component_record(name: str, expected: float, actual: float) -> dict:
    """Build an exact, JSON-safe component comparison record."""
    expected, actual = float(expected), float(actual)
    finite = math.isfinite(expected) and math.isfinite(actual)
    absolute = abs(actual - expected) if finite else None
    relative = (absolute / abs(expected) if finite and expected != 0.0 else None)
    return {
        "component": name, "expected": expected, "actual": actual,
        "expected_bits": float_bits(expected), "actual_bits": float_bits(actual),
        "expected_signed_zero": signed_zero(expected),
        "actual_signed_zero": signed_zero(actual),
        "absolute_difference": absolute, "relative_difference": relative,
        "ulp_distance": ulp_distance(expected, actual),
        "finite": finite, "python_equal": expected == actual,
        "bitwise_equal": float_bits(expected) == float_bits(actual),
    }


def extract_log_envelope(text: str) -> bytes:
    """Decode exactly one bounded Session 14x log envelope and verify its hash."""
    import base64, hashlib
    prefix, suffix = "SESSION14X_DIAGNOSTIC_BEGIN ", "SESSION14X_DIAGNOSTIC_END"
    lines = [line.strip() for line in text.splitlines()]
    starts = [line for line in lines if prefix in line]
    ends = [line for line in lines if suffix in line]
    if len(starts) != 1 or len(ends) != 1:
        raise ValueError("diagnostic_envelope_cardinality")
    payload = starts[0].split(prefix, 1)[1]
    claimed, encoded = payload.split(" ", 1)
    raw = base64.b64decode(encoded, validate=True)
    if len(raw) > 2_000_000:
        raise ValueError("diagnostic_envelope_oversized")
    if hashlib.sha256(raw).hexdigest() != claimed:
        raise ValueError("diagnostic_envelope_hash")
    return raw
