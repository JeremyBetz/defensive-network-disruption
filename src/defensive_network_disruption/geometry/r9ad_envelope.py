"""Explicit prospective envelope assembly; historical root discovery unchanged."""
from typing import Callable
import numpy as np
from .verification_repair import (GRID_INTERVALS, ROOT_ABSOLUTE_TOLERANCE,
 ROOT_RELATIVE_TOLERANCE, ROOT_MAX_ITERATIONS, ROOT_RESIDUAL_TOLERANCE,
 ROOT_DEDUPLICATION_TOLERANCE, OWNER_PROBE_MAXIMUM, VerificationError,
 VerifiedEnvelope, VerifiedSwitch, CertifiedTieInterval, brentq,
 opposite_nonzero_signs, _matrix, _pair_value, _owners, _adjacent,
 _certify_boundary, _merge_ties)
from .r9ad_tie_regions import proposal, review, disposition
from .r9r_localization import check_deadline
from fractions import Fraction as F


def equality_witness(function, pair, outside, inside, deadline):
    """Retain historical equality search without asserting global ownership."""
    if _pair_value(function, pair, outside) == 0 or _pair_value(function, pair, inside) != 0:
        raise VerificationError('tie_boundary_bracket_invalid')
    for _ in range(1100):
        check_deadline(deadline)
        if _adjacent(outside, inside):
            return outside, inside
        midpoint = float((np.float64(outside)+np.float64(inside))/np.float64(2.))
        if midpoint in (outside, inside):
            raise VerificationError('tie_boundary_not_adjacent')
        if _pair_value(function, pair, midpoint) == 0:
            inside = midpoint
        else:
            outside = midpoint
    raise VerificationError('tie_boundary_bisection_exhausted')


def plateaus(function, grid, values, fields, deadline, sink):
    records = []
    for first in range(values.shape[1]):
        for second in range(first+1, values.shape[1]):
            pair = (first, second)
            exact = values[:, first] == values[:, second]
            index = 0
            while index < len(grid):
                check_deadline(deadline)
                if not exact[index]:
                    index += 1
                    continue
                end = index
                while end+1 < len(grid) and exact[end+1]:
                    end += 1
                if end > index:
                    midpoint = float((grid[index]+grid[end])/2.)
                    owners = _owners(_matrix(function, np.array([midpoint]))[0])
                    # Same proposal eligibility as historical discovery. Unselected
                    # non-owner equalities are not promoted to structural ties.
                    if owners and set(pair).issubset(owners):
                        start = None if index == 0 else equality_witness(function, pair, float(grid[index-1]), float(grid[index]), deadline)
                        finish = None if end == len(grid)-1 else equality_witness(function, pair, float(grid[end+1]), float(grid[end]), deadline)
                        left = 0. if start is None else start[1]
                        right = 1. if finish is None else finish[1]
                        item = proposal(fields, pair, F.from_float(left), F.from_float(right))
                        coverage = review(fields, item, deadline=deadline,
                                          sink=lambda c: sink(kind='tie_cell', value=c))
                        sink(kind='tie_coverage', value=coverage)
                        decision = disposition(coverage)
                        sink(kind='tie_disposition', value=decision)
                        if decision == 'retain':
                            a = None if start is None else _certify_boundary(function, pair, *start, 'entry')
                            b = None if finish is None else _certify_boundary(function, pair, *finish, 'exit')
                            for point in [midpoint]+[x.inside for x in (a,b) if x is not None]:
                                row = _matrix(function, np.array([point]))[0]
                                if _pair_value(function,pair,point) != 0 or not set(pair).issubset(_owners(row)):
                                    raise VerificationError('tie_plateau_topology_invalid')
                            records.append(CertifiedTieInterval(a,b,owners,(pair,)))
                index = end+1
    return _merge_ties(records)


def find_verified_envelope(function: Callable[[np.ndarray], np.ndarray], *,
                           grid_intervals: int = GRID_INTERVALS,
                           extra_partitions: tuple[float, ...] = (), fields, deadline, sink) -> VerifiedEnvelope:
    if isinstance(grid_intervals, bool) or not isinstance(grid_intervals, int) or grid_intervals < 2:
        raise VerificationError("grid_intervals_invalid")
    grid = np.linspace(0.0, 1.0, grid_intervals + 1, dtype=np.float64)
    values = _matrix(function, grid)
    ties = plateaus(function, grid, values, fields, deadline, sink)
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
