"""Synthetic and explicit-geometry helpers for the Session 14ak diagnosis."""
from __future__ import annotations

from contextlib import contextmanager
import math
import signal
import time
from typing import Callable, Iterable, Sequence

import numpy as np

from .occlusion_fields import simpson_average


class DiagnosticTimeout(RuntimeError):
    """A governed diagnostic operation exceeded its prospective wall limit."""


@contextmanager
def wall_limit(seconds: float):
    if not math.isfinite(seconds) or seconds <= 0:
        raise ValueError("seconds")
    previous = signal.getsignal(signal.SIGALRM)

    def expired(_signum, _frame):
        raise DiagnosticTimeout("operation_timeout")

    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def timed(operation: Callable[[], object], *, limit_seconds: float) -> tuple[object, float]:
    started = time.perf_counter()
    with wall_limit(limit_seconds):
        value = operation()
    return value, time.perf_counter() - started


def audit_partitions(partitions: Sequence[float], onsets: Iterable[float]) -> dict[str, object]:
    points = tuple(float(x) for x in partitions)
    if len(points) < 2 or not all(math.isfinite(x) for x in points):
        raise ValueError("partition_points")
    widths = tuple(b - a for a, b in zip(points, points[1:]))
    onset_points = tuple(float(x) for x in onsets if 0.0 < float(x) < 1.0)
    return {
        "covers_domain": points[0] == 0.0 and points[-1] == 1.0,
        "strictly_ordered": all(width > 0.0 for width in widths),
        "width_sum_exact": math.fsum(widths) == 1.0,
        "piece_count": len(widths),
        "onset_count": len(onset_points),
        "onsets_once": all(sum(point == onset for point in points) == 1 for onset in onset_points),
        "minimum_width": min(widths),
        "maximum_width": max(widths),
    }


def maximum_simpson(function: Callable[[np.ndarray], np.ndarray], intervals: int,
                    lower: float = 0.0, upper: float = 1.0) -> float:
    if isinstance(intervals, bool) or not isinstance(intervals, int) or intervals <= 0 or intervals % 2:
        raise ValueError("intervals")
    if not (math.isfinite(lower) and math.isfinite(upper) and upper > lower):
        raise ValueError("bounds")
    points = np.linspace(lower, upper, intervals + 1, dtype=np.float64)
    values = np.max(function(points), axis=1)
    if values.shape != (intervals + 1,) or not np.isfinite(values).all():
        raise ValueError("integrand")
    return (upper - lower) * float(simpson_average(values[:, None])[0])


def split_simpson_curve(function: Callable[[np.ndarray], np.ndarray], partitions: Sequence[float],
                         ladder: Sequence[int]) -> list[dict[str, float | int]]:
    rows: list[dict[str, float | int]] = []
    previous: float | None = None
    for nominal in ladder:
        started = time.perf_counter()
        values = []
        evaluations = 0
        for lower, upper in zip(partitions[:-1], partitions[1:]):
            count = max(2, 2 * math.ceil(nominal * (upper - lower) / 2.0))
            values.append(maximum_simpson(function, count, lower, upper))
            evaluations += count + 1
        estimate = math.fsum(values)
        rows.append({"intervals": nominal, "estimate": estimate,
                     "delta": 0.0 if previous is None else estimate - previous,
                     "evaluations": evaluations, "seconds": time.perf_counter() - started})
        previous = estimate
    return rows


def uniform_simpson_curve(function: Callable[[np.ndarray], np.ndarray], ladder: Sequence[int]) -> list[dict[str, float | int]]:
    rows: list[dict[str, float | int]] = []
    previous: float | None = None
    for intervals in ladder:
        started = time.perf_counter()
        estimate = maximum_simpson(function, intervals)
        rows.append({"intervals": intervals, "estimate": estimate,
                     "delta": 0.0 if previous is None else estimate - previous,
                     "evaluations": intervals + 1, "seconds": time.perf_counter() - started})
        previous = estimate
    return rows


def sanitize_curve(rows: Sequence[dict[str, float | int]]) -> list[dict[str, object]]:
    """Remove empirical totals while retaining convergence and runtime evidence."""
    if not rows:
        return []
    reference = float(rows[-1]["estimate"])
    return [{"intervals": int(row["intervals"]), "evaluations": int(row["evaluations"]),
             "successive_abs_delta": abs(float(row["delta"])),
             "highest_abs_delta": abs(float(row["estimate"]) - reference),
             "seconds": float(row["seconds"])} for row in rows]


__all__ = ["DiagnosticTimeout", "audit_partitions", "maximum_simpson",
           "sanitize_curve", "split_simpson_curve", "timed", "uniform_simpson_curve", "wall_limit"]
