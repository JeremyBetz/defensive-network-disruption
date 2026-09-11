"""Synthetic verification repair for the frozen continuous-occlusion fields.

This module is internal.  It deliberately does not expose empirical, model, or
acquisition routes and does not replace the preserved historical verifiers.
"""
from __future__ import annotations

from dataclasses import dataclass, fields
import math
from typing import Callable

import numpy as np
from scipy.optimize import brentq

from .maximum_envelope import (
    GRID_INTERVALS,
    OWNER_PROBE_MAXIMUM,
    ROOT_ABSOLUTE_TOLERANCE,
    ROOT_DEDUPLICATION_TOLERANCE,
    ROOT_MAX_ITERATIONS,
    ROOT_RELATIVE_TOLERANCE,
    ROOT_RESIDUAL_TOLERANCE,
    VALUE_TIE_TOLERANCE,
)


class VerificationError(ValueError):
    """A required synthetic verification obligation could not be certified."""


@dataclass(frozen=True)
class CertifiedBoundary:
    outside: float
    inside: float
    direction: str
    pair: tuple[int, int]
    owners: tuple[int, ...]


@dataclass(frozen=True)
class CertifiedTieInterval:
    start: CertifiedBoundary | None
    end: CertifiedBoundary | None
    owners: tuple[int, ...]
    pairs: tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class VerifiedSwitch:
    location: float
    owners_before: tuple[int, ...]
    owners_at: tuple[int, ...]
    owners_after: tuple[int, ...]
    crossing_pairs: tuple[tuple[int, int], ...]
    endpoint: bool
    multiway: bool
    envelope_value: float


@dataclass(frozen=True)
class VerifiedEnvelope:
    switches: tuple[VerifiedSwitch, ...]
    tie_intervals: tuple[CertifiedTieInterval, ...]
    maximizing_defenders: tuple[int, ...]
    partitions: tuple[float, ...]
    grid_intervals: int


@dataclass(frozen=True)
class VerificationReadiness:
    continuity_verified: bool
    switching_verified: bool
    controlled_integration_verified: bool
    references_complete: bool
    permutation_verified: bool
    deterministic: bool
    failure_enforcement_verified: bool
    blocking_warnings_absent: bool
    integrity_verified: bool

    def __post_init__(self) -> None:
        for item in fields(self):
            if type(getattr(self, item.name)) is not bool:
                raise TypeError(f"{item.name}_must_be_bool")

    @property
    def ready(self) -> bool:
        return all(getattr(self, item.name) for item in fields(self))


def _matrix(function: Callable[[np.ndarray], np.ndarray], points: np.ndarray) -> np.ndarray:
    t = np.asarray(points, dtype=np.float64)
    values = np.asarray(function(t), dtype=np.float64)
    if t.ndim != 1 or values.ndim != 2 or values.shape[0] != len(t) or values.shape[1] < 1:
        raise VerificationError("individual_value_shape_invalid")
    if not np.isfinite(values).all() or np.any(values < 0.0) or np.any(values > 1.0):
        raise VerificationError("individual_values_invalid")
    return values


def _owners(row: np.ndarray) -> tuple[int, ...]:
    high = float(np.max(row))
    if high == 0.0:
        return ()
    return tuple(i for i, value in enumerate(row) if high - float(value) <= VALUE_TIE_TOLERANCE)


def opposite_nonzero_signs(left: float, right: float) -> bool:
    """Return raw sign opposition without multiplying underflow-sensitive values."""
    if not math.isfinite(left) or not math.isfinite(right):
        raise VerificationError("nonfinite_pair_difference")
    return left != 0.0 and right != 0.0 and bool(np.signbit(left)) != bool(np.signbit(right))


def _pair_value(function, pair: tuple[int, int], point: float) -> float:
    row = _matrix(function, np.array([point], dtype=np.float64))[0]
    return float(row[pair[0]] - row[pair[1]])


def _adjacent(left: float, right: float) -> bool:
    return float(np.nextafter(np.float64(left), np.float64(right))) == right


def _certify_boundary(function, pair, outside: float, inside: float, direction: str) -> CertifiedBoundary:
    if _pair_value(function, pair, outside) == 0.0 or _pair_value(function, pair, inside) != 0.0:
        raise VerificationError("tie_boundary_bracket_invalid")
    for _ in range(1100):
        if _adjacent(outside, inside):
            break
        midpoint = float((np.float64(outside) + np.float64(inside)) / np.float64(2.0))
        if midpoint in (outside, inside):
            raise VerificationError("tie_boundary_not_adjacent")
        if _pair_value(function, pair, midpoint) == 0.0:
            inside = midpoint
        else:
            outside = midpoint
    else:
        raise VerificationError("tie_boundary_bisection_exhausted")
    if not _adjacent(outside, inside):
        raise VerificationError("tie_boundary_not_adjacent")
    inside_row = _matrix(function, np.array([inside]))[0]
    outside_row = _matrix(function, np.array([outside]))[0]
    owners = _owners(inside_row)
    if not set(pair).issubset(owners) or float(np.max(inside_row)) <= 0.0:
        raise VerificationError("tie_boundary_not_maximal")
    if _pair_value(function, pair, inside) != 0.0 or _pair_value(function, pair, outside) == 0.0:
        raise VerificationError("tie_boundary_predicate_failed")
    if not _owners(outside_row):
        raise VerificationError("tie_boundary_neighbor_ownerless")
    return CertifiedBoundary(outside, inside, direction, pair, owners)


def _plateaus(function, grid: np.ndarray, values: np.ndarray) -> list[CertifiedTieInterval]:
    records: list[CertifiedTieInterval] = []
    count = values.shape[1]
    for first in range(count):
        for second in range(first + 1, count):
            pair = (first, second)
            exact = values[:, first] == values[:, second]
            index = 0
            while index < len(grid):
                if not exact[index]:
                    index += 1
                    continue
                end = index
                while end + 1 < len(grid) and exact[end + 1]:
                    end += 1
                if end > index:
                    midpoint = float((grid[index] + grid[end]) / 2.0)
                    owners = _owners(_matrix(function, np.array([midpoint]))[0])
                    if set(pair).issubset(owners) and owners:
                        start = None if index == 0 else _certify_boundary(
                            function, pair, float(grid[index - 1]), float(grid[index]), "entry")
                        finish = None if end == len(grid) - 1 else _certify_boundary(
                            function, pair, float(grid[end + 1]), float(grid[end]), "exit")
                        probes = [midpoint]
                        if start is not None:
                            probes.append(start.inside)
                        if finish is not None:
                            probes.append(finish.inside)
                        for point in probes:
                            row = _matrix(function, np.array([point]))[0]
                            if _pair_value(function, pair, point) != 0.0 or not set(pair).issubset(_owners(row)):
                                raise VerificationError("tie_plateau_topology_invalid")
                        records.append(CertifiedTieInterval(start, finish, owners, (pair,)))
                index = end + 1
    return _merge_ties(records)


def _boundary_key(boundary: CertifiedBoundary | None, endpoint: float) -> float:
    return endpoint if boundary is None else boundary.inside


def _merge_ties(records: list[CertifiedTieInterval]) -> list[CertifiedTieInterval]:
    groups: list[CertifiedTieInterval] = []
    for item in sorted(records, key=lambda x: (_boundary_key(x.start, 0.0), _boundary_key(x.end, 1.0), x.owners)):
        start, end = _boundary_key(item.start, 0.0), _boundary_key(item.end, 1.0)
        match = None
        for idx, old in enumerate(groups):
            if (abs(start - _boundary_key(old.start, 0.0)) <= ROOT_DEDUPLICATION_TOLERANCE and
                    abs(end - _boundary_key(old.end, 1.0)) <= ROOT_DEDUPLICATION_TOLERANCE):
                match = idx
                break
        if match is None:
            groups.append(item)
        else:
            old = groups[match]
            owners = tuple(sorted(set(old.owners) | set(item.owners)))
            pairs = tuple(sorted(set(old.pairs) | set(item.pairs)))
            groups[match] = CertifiedTieInterval(old.start or item.start, old.end or item.end, owners, pairs)
    return groups


def find_verified_envelope(function: Callable[[np.ndarray], np.ndarray], *,
                           grid_intervals: int = GRID_INTERVALS,
                           extra_partitions: tuple[float, ...] = ()) -> VerifiedEnvelope:
    if isinstance(grid_intervals, bool) or not isinstance(grid_intervals, int) or grid_intervals < 2:
        raise VerificationError("grid_intervals_invalid")
    grid = np.linspace(0.0, 1.0, grid_intervals + 1, dtype=np.float64)
    values = _matrix(function, grid)
    ties = _plateaus(function, grid, values)
    roots: list[tuple[float, tuple[int, int]]] = []
    for first in range(values.shape[1]):
        for second in range(first + 1, values.shape[1]):
            pair = (first, second)
            difference = values[:, first] - values[:, second]
            for idx, value in enumerate(difference):
                if value == 0.0 and (idx == 0 or difference[idx - 1] != 0.0) and (idx == len(grid)-1 or difference[idx+1] != 0.0):
                    roots.append((float(grid[idx]), pair))
            for idx in range(len(grid)-1):
                if not opposite_nonzero_signs(float(difference[idx]), float(difference[idx+1])):
                    continue
                lower, upper = float(grid[idx]), float(grid[idx+1])
                try:
                    root = brentq(lambda t: _pair_value(function, pair, t), lower, upper,
                                  xtol=ROOT_ABSOLUTE_TOLERANCE, rtol=ROOT_RELATIVE_TOLERANCE,
                                  maxiter=ROOT_MAX_ITERATIONS)
                except Exception as error:
                    raise VerificationError("bracketed_root_failed") from error
                if abs(_pair_value(function, pair, root)) > ROOT_RESIDUAL_TOLERANCE:
                    raise VerificationError("root_residual_failed")
                roots.append((float(root), pair))
    grouped: list[tuple[float, set[tuple[int, int]]]] = []
    for location, pair in sorted(roots):
        if grouped and abs(location-grouped[-1][0]) <= ROOT_DEDUPLICATION_TOLERANCE:
            grouped[-1][1].add(pair)
        else:
            grouped.append((location, {pair}))
    partitions = [0.0, 1.0, *(float(x) for x in extra_partitions if 0.0 < x < 1.0)]
    for tie in ties:
        for boundary in (tie.start, tie.end):
            if boundary is not None:
                partitions.extend((boundary.outside, boundary.inside))
    partitions.extend(location for location, _ in grouped if 0.0 < location < 1.0)
    partitions = sorted(set(partitions))
    switches: list[VerifiedSwitch] = []
    maximizing = set()
    for row in values:
        maximizing.update(_owners(row))
    for location, pairs in grouped:
        row = _matrix(function, np.array([location]))[0]
        at = _owners(row)
        if not at:
            continue
        prior = max((x for x in partitions if x < location), default=0.0)
        later = min((x for x in partitions if x > location), default=1.0)
        probe = min(OWNER_PROBE_MAXIMUM, max(location-prior, 0.0)/4.0, max(later-location, 0.0)/4.0)
        if location == 0.0:
            before, after, endpoint = (), _owners(_matrix(function, np.array([min(1.0, location+OWNER_PROBE_MAXIMUM)]))[0]), True
        elif location == 1.0:
            before, after, endpoint = _owners(_matrix(function, np.array([max(0.0, location-OWNER_PROBE_MAXIMUM)]))[0]), (), True
        else:
            if probe <= 0.0:
                raise VerificationError("ownership_probe_invalid")
            before = _owners(_matrix(function, np.array([location-probe]))[0])
            after = _owners(_matrix(function, np.array([location+probe]))[0])
            endpoint = False
        relevant_pairs = tuple(sorted(pair for pair in pairs if set(pair).issubset(at)))
        if relevant_pairs and before != after and (before or after):
            switches.append(VerifiedSwitch(location, before, at, after, relevant_pairs,
                                           endpoint, len(at) >= 3, float(np.max(row))))
            maximizing.update(at); maximizing.update(before); maximizing.update(after)
    return VerifiedEnvelope(tuple(switches), tuple(ties), tuple(sorted(maximizing)), tuple(partitions), grid_intervals)


def mapped_signature(result: VerifiedEnvelope, permutation: tuple[int, ...]) -> tuple:
    owners = lambda seq: tuple(sorted(permutation[i] for i in seq))
    boundary = lambda value: None if value is None else (
        value.outside, value.inside, value.direction,
        tuple(sorted(permutation[i] for i in value.pair)), owners(value.owners))
    switches = tuple((x.location, owners(x.owners_before), owners(x.owners_at), owners(x.owners_after),
                      tuple(sorted(tuple(sorted((permutation[a], permutation[b]))) for a,b in x.crossing_pairs)),
                      x.endpoint, x.multiway, x.envelope_value) for x in result.switches)
    ties = tuple(sorted((boundary(x.start), boundary(x.end), owners(x.owners),
                         tuple(sorted(tuple(sorted((permutation[a], permutation[b]))) for a,b in x.pairs)))
                        for x in result.tie_intervals))
    return switches, ties, owners(result.maximizing_defenders), result.partitions, result.grid_intervals


def independent_continuity(left_limit: float, right_limit: float, *,
                           absolute_tolerance: float = 1e-12,
                           relative_tolerance: float = 1e-12) -> bool:
    if not math.isfinite(left_limit) or not math.isfinite(right_limit):
        return False
    return math.isclose(left_limit, right_limit, abs_tol=absolute_tolerance, rel_tol=relative_tolerance)

