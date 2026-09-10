"""Causal event/tracking alignment helpers for structural validation."""

from __future__ import annotations

from bisect import bisect_left

MAX_FRAME_AGE_SECONDS = 0.100


def nearest_strictly_before(frame_times, event_time, *, tolerance=MAX_FRAME_AGE_SECONDS):
    """Return the index of the latest frame strictly before an event, if timely."""
    position = bisect_left(frame_times, event_time) - 1
    if position < 0:
        return None
    age = event_time - frame_times[position]
    if age < 0 or age > tolerance:
        return None
    return position
