"""Test-support comparison contract for historical final-float vectors."""
from __future__ import annotations

import math
import struct
import sys
from collections.abc import Mapping

MULTIPLIER = 64
EPSILON64 = sys.float_info.epsilon


def float_bits(value: float) -> str:
    return struct.pack(">d", float(value)).hex()


def signed_zero(value: float) -> str | None:
    if value != 0.0:
        return None
    return "negative" if math.copysign(1.0, value) < 0.0 else "positive"


def ulp_distance(left: float, right: float) -> int | None:
    """Return finite float64 ULP distance; signed zeros have distance zero."""
    if not math.isfinite(left) or not math.isfinite(right):
        return None
    if left == right:
        return 0

    def ordered(value: float) -> int:
        raw = struct.unpack(">Q", struct.pack(">d", float(value)))[0]
        return (~raw & ((1 << 64) - 1)) if raw >> 63 else raw | (1 << 63)

    return abs(ordered(left) - ordered(right))


def component_tolerance(expected: float, actual: float) -> float:
    return MULTIPLIER * EPSILON64 * max(1.0, abs(expected), abs(actual))


def compare_historical_vector(
    expected_intervals: int,
    expected: Mapping[str, float],
    actual_intervals: int,
    actual: Mapping[str, float],
) -> dict:
    """Compare exact vector structure and bounded finite float64 components."""
    expected_order = tuple(expected)
    actual_order = tuple(actual)
    interval_equal = type(expected_intervals) is int and type(actual_intervals) is int and expected_intervals == actual_intervals
    order_equal = expected_order == actual_order
    rows = []
    for component in expected_order:
        if component not in actual:
            continue
        left, right = float(expected[component]), float(actual[component])
        finite = math.isfinite(left) and math.isfinite(right)
        difference = abs(left - right) if finite else None
        tolerance = component_tolerance(left, right) if finite else None
        denominator = max(abs(left), abs(right)) if finite else 0.0
        relative = (difference / denominator if denominator else 0.0) if finite else None
        rows.append({
            "component": component,
            "expected": left,
            "actual": right,
            "expected_bits": float_bits(left),
            "actual_bits": float_bits(right),
            "expected_signed_zero": signed_zero(left),
            "actual_signed_zero": signed_zero(right),
            "finite": finite,
            "absolute_difference": difference,
            "relative_difference": relative,
            "ulp_distance": ulp_distance(left, right),
            "tolerance": tolerance,
            "equivalent": bool(finite and difference <= tolerance),
        })
    failed = next((row["component"] for row in rows if not row["equivalent"]), None)
    if not interval_equal:
        failed = "accepted_intervals"
    elif not order_equal:
        failed = "component_order"
    equivalent = interval_equal and order_equal and len(rows) == len(expected_order) and all(row["equivalent"] for row in rows)
    return {
        "equivalent": equivalent,
        "interval_equal": interval_equal,
        "component_order_equal": order_equal,
        "expected_order": list(expected_order),
        "actual_order": list(actual_order),
        "failed_component": None if equivalent else failed,
        "maximum_absolute_difference": max((row["absolute_difference"] for row in rows if row["absolute_difference"] is not None), default=None),
        "components": rows,
    }


def assert_historical_vector_equivalent(*args) -> dict:
    result = compare_historical_vector(*args)
    if not result["equivalent"]:
        raise AssertionError(f"historical_vector_changed: {result['failed_component']}: {result}")
    return result
