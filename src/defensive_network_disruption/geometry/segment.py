"""Synthetic geometric primitives; these are not scoring models."""

from __future__ import annotations

import math

IMPLEMENTATION_TOLERANCE_METRES = 1e-9


def point_to_segment_distance(point, start, end, *, tolerance=IMPLEMENTATION_TOLERANCE_METRES):
    """Return finite-segment distance and projection fraction.

    ``tolerance`` is only a floating-point implementation guard and has no
    football interpretation.
    """
    values = tuple(float(v) for pair in (point, start, end) for v in pair)
    if len(values) != 6 or not all(math.isfinite(v) for v in values):
        raise ValueError("three finite 2D points are required")
    px, py, ax, ay, bx, by = values
    vx, vy = bx - ax, by - ay
    length2 = vx * vx + vy * vy
    if length2 <= tolerance * tolerance:
        return math.hypot(px - ax, py - ay), 0.0
    t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / length2))
    return math.hypot(px - (ax + t * vx), py - (ay + t * vy)), t


def minimum_defender_segment_distance(defenders, start, end):
    """Return distance and all tied indices, or ``None`` for no defenders."""
    distances = [point_to_segment_distance(d, start, end)[0] for d in defenders]
    if not distances:
        return None
    minimum = min(distances)
    ties = tuple(i for i, value in enumerate(distances) if math.isclose(value, minimum, abs_tol=1e-12))
    return minimum, ties
