"""Expected tie-aware receiver-ranking metrics."""

from __future__ import annotations

import numpy as np


def expected_credits(scores, target_index, *, tolerance=1e-12):
    if target_index is None:
        return {"rr": 0.0, "hit1": 0.0, "hit3": 0.0, "tied": False}
    values = np.asarray(scores, dtype=np.float64)
    if not np.isfinite(values).all() or target_index < 0 or target_index >= len(values):
        raise ValueError("finite scores and a valid target index are required")
    order = np.argsort(-values, kind="stable")
    start = 0
    target_block = None
    while start < len(order):
        high = values[order[start]]
        end = start + 1
        while end < len(order) and high - values[order[end]] <= tolerance:
            end += 1
        if target_index in order[start:end]:
            target_block = (start + 1, end)
            break
        start = end
    first, last = target_block
    tied = last - first + 1
    positions = range(first, last + 1)
    rr = sum(1 / position for position in positions) / tied
    return {"rr": rr, "hit1": sum(position <= 1 for position in positions) / tied,
            "hit3": sum(position <= 3 for position in positions) / tied, "tied": tied > 1}


def match_macro(match_metrics, field):
    values = [float(metrics[field]) for metrics in match_metrics.values()]
    if not values:
        raise ValueError("at least one match is required")
    return sum(values) / len(values)
