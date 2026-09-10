"""Frozen Session 5 static multi-defender attenuation primitive."""

from __future__ import annotations

import math

from defensive_network_disruption.geometry.segment import point_to_segment_distance


ATTENUATION_SCALE_METRES = 5.0


def summed_segment_attenuation(defenders, start, end):
    """Sum fixed-scale distance decay around a finite connection segment."""
    distances = sorted(
        point_to_segment_distance(defender, start, end)[0]
        for defender in defenders
    )
    if not distances:
        raise ValueError("at least one valid defender is required")
    contributions = [math.exp(-distance / ATTENUATION_SCALE_METRES) for distance in distances]
    result = math.fsum(contributions)
    if not math.isfinite(result) or result < 0:
        raise ValueError("attenuation must be finite and nonnegative")
    return result
