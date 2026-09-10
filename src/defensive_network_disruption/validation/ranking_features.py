"""Frozen M0/M1 feature construction."""

from __future__ import annotations

import math
import numpy as np

from defensive_network_disruption.geometry.segment import minimum_defender_segment_distance


M0_NAMES = ("distance", "longitudinal_displacement", "lateral_displacement")
M1_NAMES = M0_NAMES + ("nearest_receiver_defender_distance", "minimum_segment_defender_distance")


def choice_features(choice, model: str) -> tuple[np.ndarray, int]:
    if model not in {"m0", "m1"}:
        raise ValueError("model must be m0 or m1")
    rows = []
    degenerate = 0
    ax, ay = choice.carrier_xy
    for receiver in choice.candidate_xy:
        bx, by = receiver
        dx, dy = bx - ax, by - ay
        base = [math.hypot(dx, dy), dx, dy]
        if model == "m1":
            nearest = min(math.hypot(defender[0] - bx, defender[1] - by) for defender in choice.defender_xy)
            segment = minimum_defender_segment_distance(choice.defender_xy, choice.carrier_xy, receiver)
            if segment is None:
                raise ValueError("M1 requires defenders")
            degenerate += int(base[0] <= 1e-9)
            base.extend([nearest, segment[0]])
        rows.append(base)
    result = np.asarray(rows, dtype=np.float64)
    if not np.isfinite(result).all():
        raise ValueError("features must be finite")
    return result, degenerate
