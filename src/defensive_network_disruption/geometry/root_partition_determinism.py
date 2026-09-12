"""Internal deterministic structural boundaries for Session 14aa.

The historical envelope and integration implementations remain unchanged.  This
module certifies their structural transitions in ordered float64 space and is
used only by the Session 14aa verification adapter.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import struct
from typing import Callable, Iterable

import numpy as np

from .verification_repair import VerifiedEnvelope, VerifiedSwitch, VerificationError


def _bits(value: float) -> int:
    value = float(value)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise VerificationError("boundary_out_of_domain")
    return struct.unpack(">Q", struct.pack(">d", value))[0]


def _float(bits: int) -> float:
    return struct.unpack(">d", struct.pack(">Q", bits))[0]


def _row(function: Callable[[np.ndarray], np.ndarray], point: float) -> np.ndarray:
    values = np.asarray(function(np.array([point], dtype=np.float64)), dtype=np.float64)
    if values.ndim != 2 or values.shape[0] != 1 or values.shape[1] < 1:
        raise VerificationError("individual_value_shape_invalid")
    if not np.isfinite(values).all():
        raise VerificationError("individual_values_invalid")
    return values[0]


def _pair(function, pair: tuple[int, int], point: float) -> float:
    values = _row(function, point)
    return float(values[pair[0]] - values[pair[1]])


def _sign(value: float) -> int:
    return 0 if value == 0.0 else (-1 if math.copysign(1.0, value) < 0.0 else 1)


def _first_true(lower: float, upper: float, predicate: Callable[[float], bool]) -> float:
    """Return the first float in ``[lower, upper]`` satisfying a monotone predicate."""
    lo, hi = _bits(lower), _bits(upper)
    if predicate(_float(lo)) or not predicate(_float(hi)):
        raise VerificationError("transition_bracket_invalid")
    while hi - lo > 1:
        middle = (lo + hi) // 2
        if predicate(_float(middle)):
            hi = middle
        else:
            lo = middle
    return _float(hi)


def _last_true(lower: float, upper: float, predicate: Callable[[float], bool]) -> float:
    lo, hi = _bits(lower), _bits(upper)
    if not predicate(_float(lo)) or predicate(_float(hi)):
        raise VerificationError("transition_bracket_invalid")
    while hi - lo > 1:
        middle = (lo + hi) // 2
        if predicate(_float(middle)):
            lo = middle
        else:
            hi = middle
    return _float(lo)


@dataclass(frozen=True)
class CertifiedRootTransition:
    raw_solver_result: float
    last_pre_switch: float
    exact_zero_start: float | None
    exact_zero_end: float | None
    first_post_switch: float
    owners_before: tuple[int, ...]
    owners_at: tuple[int, ...]
    owners_after: tuple[int, ...]
    crossing_pairs: tuple[tuple[int, int], ...]

    @property
    def canonical(self) -> float:
        return self.first_post_switch


@dataclass(frozen=True)
class CertifiedOnset:
    defender_index: int
    branch: int
    raw_scalar_result: float
    last_pre_branch: float
    first_post_branch: float

    @property
    def canonical(self) -> float:
        return self.first_post_branch


def _switch_witnesses(function, switch: VerifiedSwitch) -> tuple[float, float]:
    raw = switch.location
    cell = 1.0 / 65536.0
    lower, upper = max(0.0, raw - cell), min(1.0, raw + cell)
    pair = switch.crossing_pairs[0]
    after_sign = _sign(_pair(function, pair, min(1.0, raw + min(1e-7, cell / 4))))
    before_sign = _sign(_pair(function, pair, max(0.0, raw - min(1e-7, cell / 4))))
    for _ in range(24):
        if _sign(_pair(function, pair, lower)) == before_sign and _sign(_pair(function, pair, upper)) == after_sign:
            return lower, upper
        cell *= 2.0
        lower, upper = max(0.0, raw - cell), min(1.0, raw + cell)
    raise VerificationError("switch_witnesses_unavailable")


def certify_switch(function: Callable[[np.ndarray], np.ndarray], switch: VerifiedSwitch) -> CertifiedRootTransition:
    if switch.endpoint or not switch.crossing_pairs:
        raise VerificationError("interior_switch_required")
    lower, upper = _switch_witnesses(function, switch)
    pair = switch.crossing_pairs[0]
    before_sign, after_sign = _sign(_pair(function, pair, lower)), _sign(_pair(function, pair, upper))
    if before_sign == 0 or after_sign == 0 or before_sign == after_sign:
        raise VerificationError("switch_sign_transition_invalid")
    last_pre = _last_true(lower, upper, lambda t: _sign(_pair(function, pair, t)) == before_sign)
    first_post = _first_true(lower, upper, lambda t: _sign(_pair(function, pair, t)) == after_sign)
    zero_start = float(np.nextafter(last_pre, math.inf))
    zero_end = float(np.nextafter(first_post, -math.inf))
    if zero_start > zero_end:
        zero_start = zero_end = None
    else:
        for point in (zero_start, zero_end, _float((_bits(zero_start) + _bits(zero_end)) // 2)):
            if _pair(function, pair, point) != 0.0:
                raise VerificationError("nonzero_inside_switch_equality_interval")
    # Ownership uses the inherited block tolerance, so adjacent floats can remain
    # in the same owner block even though their raw pair order has changed.
    # Certify owner semantics at the bracket witnesses and raw order at the
    # adjacent transition records.
    before_point, after_point = lower, upper
    before_row, after_row = _row(function, before_point), _row(function, after_point)
    def owners(row: np.ndarray) -> tuple[int, ...]:
        high = float(np.max(row))
        return () if high == 0.0 else tuple(i for i, value in enumerate(row) if high - float(value) <= 1e-12)
    if owners(before_row) != switch.owners_before or owners(after_row) != switch.owners_after:
        raise VerificationError("switch_owner_semantics_changed")
    for crossing in switch.crossing_pairs:
        if _sign(_pair(function, crossing, before_point)) == _sign(_pair(function, crossing, after_point)):
            raise VerificationError("crossing_pair_order_not_reversed")
    return CertifiedRootTransition(
        switch.location, last_pre, zero_start, zero_end, first_post,
        switch.owners_before, switch.owners_at, switch.owners_after, switch.crossing_pairs,
    )


def deterministic_directional_onsets(origin, receiver, defenders) -> tuple[CertifiedOnset, ...]:
    bx, by = map(float, origin)
    qx, qy = map(float, receiver)
    ex, ey = qx - bx, qy - by
    records: list[CertifiedOnset] = []
    for index, defender in enumerate(defenders):
        dx, dy = float(defender[0]) - bx, float(defender[1]) - by
        radius = math.hypot(dx, dy)
        if radius <= 1e-9:
            raise VerificationError("origin_defender_direction_undefined")
        dot = math.fsum((ex * dx, ey * dy))
        if dot == 0.0:
            continue
        slope = dot / radius
        intercept = -radius
        for branch, target in enumerate((0.0, 1.0)):
            numerator = math.fsum((radius * radius, target * radius))
            raw = numerator / dot
            if not 0.0 < raw < 1.0:
                continue
            def post(t: float, *, target=target, slope=slope, intercept=intercept) -> bool:
                ell = math.fsum((intercept, slope * t))
                return ell > target if slope > 0.0 else ell < target
            first_post = _first_true(0.0, 1.0, post)
            last_pre = float(np.nextafter(first_post, -math.inf))
            if post(last_pre) or not post(first_post):
                raise VerificationError("onset_transition_uncertified")
            records.append(CertifiedOnset(index, branch, raw, last_pre, first_post))
    return tuple(sorted(records, key=lambda item: (_bits(item.canonical), item.defender_index, item.branch)))


def deterministic_partitions(function, envelope: VerifiedEnvelope,
                             onsets: Iterable[CertifiedOnset]) -> tuple[tuple[float, ...], tuple[CertifiedRootTransition, ...]]:
    switches = tuple(certify_switch(function, item) for item in envelope.switches)
    tagged: list[tuple[float, int, int]] = [(0.0, 0, 0), (1.0, 0, 1)]
    tagged.extend((item.canonical, 1, index) for index, item in enumerate(onsets))
    tagged.extend((item.canonical, 2, index) for index, item in enumerate(switches))
    tie_values: set[float] = set()
    for tie in envelope.tie_intervals:
        for boundary in (tie.start, tie.end):
            if boundary is not None:
                tie_values.update((boundary.outside, boundary.inside))
    tagged.extend((value, 3, index) for index, value in enumerate(sorted(tie_values, key=_bits)))
    ordered = sorted(tagged, key=lambda item: (_bits(item[0]), item[1], item[2]))
    points: list[float] = []
    for value, kind, _ in ordered:
        if not 0.0 <= value <= 1.0:
            raise VerificationError("partition_domain")
        if value in tie_values or not points or value != points[-1]:
            points.append(value)
    if points[0] != 0.0 or points[-1] != 1.0 or any(b <= a for a, b in zip(points, points[1:])):
        raise VerificationError("partition_order")
    return tuple(points), switches
