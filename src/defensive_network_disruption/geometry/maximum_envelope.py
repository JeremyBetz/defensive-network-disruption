"""Internal deterministic switching diagnostics for continuous maximum envelopes."""
from __future__ import annotations

from dataclasses import dataclass
import math
import warnings
from typing import Callable

import numpy as np
from scipy.integrate import IntegrationWarning, quad
from scipy.optimize import brentq


GRID_INTERVALS = 65536
VALUE_TIE_TOLERANCE = 1e-12
ROOT_ABSOLUTE_TOLERANCE = 1e-14
ROOT_RELATIVE_TOLERANCE = 8 * np.finfo(np.float64).eps
ROOT_MAX_ITERATIONS = 100
ROOT_RESIDUAL_TOLERANCE = 1e-12
ROOT_DEDUPLICATION_TOLERANCE = 1e-12
OWNER_PROBE_MAXIMUM = 1e-7
INTEGRATION_STRICT_TOLERANCE = 1e-13
INTEGRATION_REPEAT_TOLERANCE = 1e-11
INTEGRATION_LIMIT = 1000
PIECEWISE_REPEAT_AGREEMENT = 1e-10
UNSPLIT_AGREEMENT = 1e-10
DIRECT_FINE_AGREEMENT = 1e-9
SPLIT_SIMPSON_AGREEMENT = 1e-10


class EnvelopeError(ValueError):
    """A switching or piecewise-integration contract could not be satisfied."""


@dataclass(frozen=True)
class EnvelopeSwitch:
    location: float
    owners_before: tuple[int, ...]
    owners_at: tuple[int, ...]
    owners_after: tuple[int, ...]
    crossing_pairs: tuple[tuple[int, int], ...]
    endpoint: bool
    multiway: bool
    envelope_value: float


@dataclass(frozen=True)
class TieInterval:
    start: float
    end: float
    owners: tuple[int, ...]


@dataclass(frozen=True)
class SwitchResult:
    switches: tuple[EnvelopeSwitch, ...]
    tie_intervals: tuple[TieInterval, ...]
    maximizing_defenders: tuple[int, ...]
    grid_intervals: int


@dataclass(frozen=True)
class PiecewiseIntegral:
    value: float
    repeat_value: float
    estimated_error: float
    partitions: tuple[float, ...]
    warnings: tuple[str, ...]


def _matrix(values_function: Callable[[np.ndarray], np.ndarray], t_values) -> np.ndarray:
    t = np.asarray(t_values, dtype=np.float64)
    values = np.asarray(values_function(t), dtype=np.float64)
    if t.ndim != 1 or values.ndim != 2 or values.shape[0] != len(t) or values.shape[1] < 1:
        raise EnvelopeError("individual_value_shape_invalid")
    if not np.isfinite(values).all() or np.any(values < 0.0) or np.any(values > 1.0):
        raise EnvelopeError("individual_values_invalid")
    return values


def _owners(row: np.ndarray) -> tuple[int, ...]:
    maximum = float(np.max(row))
    if maximum == 0.0:
        return ()
    return tuple(int(index) for index, value in enumerate(row)
                 if maximum - float(value) <= VALUE_TIE_TOLERANCE)


def _deduplicate_roots(records: list[tuple[float, tuple[int, int]]]) -> list[tuple[float, set[tuple[int, int]]]]:
    groups: list[tuple[float, set[tuple[int, int]]]] = []
    for location, pair in sorted(records):
        if groups and abs(location - groups[-1][0]) <= ROOT_DEDUPLICATION_TOLERANCE:
            old_location, pairs = groups[-1]
            pairs.add(pair)
            groups[-1] = (old_location, pairs)
        else:
            groups.append((float(location), {pair}))
    return groups


def find_envelope_switches(values_function: Callable[[np.ndarray], np.ndarray], *,
                           grid_intervals: int = GRID_INTERVALS,
                           extra_partitions: tuple[float, ...] = ()) -> SwitchResult:
    """Locate verified maximum-owner switches without choosing a unique tied owner."""
    if isinstance(grid_intervals, bool) or not isinstance(grid_intervals, int) or grid_intervals < 2:
        raise EnvelopeError("grid_intervals_invalid")
    grid = np.linspace(0.0, 1.0, grid_intervals + 1, dtype=np.float64)
    values = _matrix(values_function, grid)
    defender_count = values.shape[1]
    root_records: list[tuple[float, tuple[int, int]]] = []
    tie_intervals: list[TieInterval] = []

    for first in range(defender_count):
        for second in range(first + 1, defender_count):
            difference = values[:, first] - values[:, second]
            exact = difference == 0.0
            index = 0
            while index < len(grid):
                if not exact[index]:
                    index += 1
                    continue
                end = index
                while end + 1 < len(grid) and exact[end + 1]:
                    end += 1
                midpoint = (float(grid[index]) + float(grid[end])) / 2.0
                midpoint_values = _matrix(values_function, np.array([midpoint]))[0]
                midpoint_owners = _owners(midpoint_values)
                if first in midpoint_owners and second in midpoint_owners and float(np.max(midpoint_values)) > 0.0:
                    tie_interval = TieInterval(float(grid[index]), float(grid[end]), midpoint_owners)
                    if tie_interval.end > tie_interval.start:
                        tie_intervals.append(tie_interval)
                if index == end:
                    root_records.append((float(grid[index]), (first, second)))
                index = end + 1

            sign_indices = np.nonzero(difference[:-1] * difference[1:] < 0.0)[0]
            for position in sign_indices:
                lower, upper = float(grid[position]), float(grid[position + 1])

                def pair_difference(t: float) -> float:
                    row = _matrix(values_function, np.array([t]))[0]
                    return float(row[first] - row[second])

                try:
                    root = brentq(pair_difference, lower, upper, xtol=ROOT_ABSOLUTE_TOLERANCE,
                                  rtol=ROOT_RELATIVE_TOLERANCE, maxiter=ROOT_MAX_ITERATIONS)
                except Exception as error:
                    raise EnvelopeError("bracketed_root_failed") from error
                if abs(pair_difference(root)) > ROOT_RESIDUAL_TOLERANCE:
                    raise EnvelopeError("root_residual_failed")
                root_records.append((float(root), (first, second)))

    grouped = _deduplicate_roots(root_records)
    tie_boundaries = [value for interval in tie_intervals for value in (interval.start, interval.end)]
    raw_partitions = sorted({0.0, 1.0, *(float(x) for x in extra_partitions if 0.0 < x < 1.0),
                             *(location for location, _ in grouped), *tie_boundaries})
    candidate_partitions: list[float] = []
    for value in raw_partitions:
        if not candidate_partitions or value - candidate_partitions[-1] > ROOT_DEDUPLICATION_TOLERANCE:
            candidate_partitions.append(value)
    switches: list[EnvelopeSwitch] = []
    maximizing = set()
    for row in values:
        maximizing.update(_owners(row))

    for location, pairs in grouped:
        at = _matrix(values_function, np.array([location]))[0]
        owners_at = _owners(at)
        if not owners_at:
            continue
        position = min(range(len(candidate_partitions)), key=lambda i: abs(candidate_partitions[i]-location))
        left_distance = location - candidate_partitions[position-1] if position > 0 else 1.0
        right_distance = candidate_partitions[position+1] - location if position+1 < len(candidate_partitions) else 1.0
        probe = min(OWNER_PROBE_MAXIMUM, left_distance/4.0, right_distance/4.0)
        if probe <= 0.0:
            raise EnvelopeError("ownership_probe_invalid")
        if location <= ROOT_DEDUPLICATION_TOLERANCE:
            before = ()
            after = _owners(_matrix(values_function, np.array([min(1.0, location+probe)]))[0])
            endpoint = True
        elif location >= 1.0-ROOT_DEDUPLICATION_TOLERANCE:
            before = _owners(_matrix(values_function, np.array([max(0.0, location-probe)]))[0])
            after = ()
            endpoint = True
        else:
            before = _owners(_matrix(values_function, np.array([location-probe]))[0])
            after = _owners(_matrix(values_function, np.array([location+probe]))[0])
            endpoint = False
        owner_set = set(owners_at)
        envelope_pairs = tuple(sorted(pair for pair in pairs if set(pair).issubset(owner_set)))
        relevant = bool(envelope_pairs) and before != after and (before or after)
        if relevant:
            switches.append(EnvelopeSwitch(float(location), before, owners_at, after,
                                           envelope_pairs, endpoint, len(owners_at) >= 3,
                                           float(np.max(at))))
            maximizing.update(owners_at); maximizing.update(before); maximizing.update(after)

    unique_ties = []
    for interval in sorted(tie_intervals, key=lambda item:(item.start,item.end,item.owners)):
        if not unique_ties or interval != unique_ties[-1]:
            unique_ties.append(interval)
    return SwitchResult(tuple(switches), tuple(unique_ties), tuple(sorted(maximizing)), grid_intervals)


def partition_points(switches: SwitchResult, extra_partitions: tuple[float, ...]) -> tuple[float, ...]:
    values = [0.0, 1.0, *(float(x) for x in extra_partitions if 0.0 < x < 1.0)]
    values.extend(item.location for item in switches.switches if 0.0 < item.location < 1.0)
    values.extend(boundary for interval in switches.tie_intervals for boundary in (interval.start, interval.end)
                  if 0.0 < boundary < 1.0)
    result = []
    for value in sorted(values):
        if not result or value-result[-1] > ROOT_DEDUPLICATION_TOLERANCE:
            result.append(value)
    return tuple(result)


def integrate_maximum_piecewise(values_function: Callable[[np.ndarray], np.ndarray],
                                switches: SwitchResult, *,
                                extra_partitions: tuple[float, ...] = ()) -> PiecewiseIntegral:
    partitions = partition_points(switches, extra_partitions)

    def maximum(t: float) -> float:
        return float(np.max(_matrix(values_function, np.array([t]))[0]))

    strict_parts=[];repeat_parts=[];errors=[];warning_names=[]
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", IntegrationWarning)
        for lower,upper in zip(partitions[:-1],partitions[1:],strict=True):
            if upper-lower <= ROOT_DEDUPLICATION_TOLERANCE:
                continue
            strict,error=quad(maximum,lower,upper,epsabs=INTEGRATION_STRICT_TOLERANCE,
                              epsrel=INTEGRATION_STRICT_TOLERANCE,limit=INTEGRATION_LIMIT)
            repeat,_=quad(maximum,lower,upper,epsabs=INTEGRATION_REPEAT_TOLERANCE,
                          epsrel=INTEGRATION_REPEAT_TOLERANCE,limit=INTEGRATION_LIMIT)
            strict_parts.append(float(strict));repeat_parts.append(float(repeat));errors.append(float(error))
        warning_names.extend(type(item.message).__name__ for item in caught)
    numbers=(*strict_parts,*repeat_parts,*errors)
    if not numbers or not all(math.isfinite(value) for value in numbers):
        raise EnvelopeError("piecewise_integration_nonfinite")
    return PiecewiseIntegral(math.fsum(strict_parts),math.fsum(repeat_parts),math.fsum(errors),
                             partitions,tuple(warning_names))


def split_simpson_maximum(values_function: Callable[[np.ndarray], np.ndarray],
                          partitions: tuple[float, ...], nominal_intervals: int) -> tuple[float,int,int]:
    if nominal_intervals < 2 or nominal_intervals%2:
        raise EnvelopeError("nominal_intervals_invalid")
    pieces=[];interval_total=0;evaluation_total=0
    for lower,upper in zip(partitions[:-1],partitions[1:],strict=True):
        length=upper-lower
        if length <= ROOT_DEDUPLICATION_TOLERANCE:
            continue
        count=max(2,2*math.ceil(nominal_intervals*length/2.0))
        t=np.linspace(lower,upper,count+1,dtype=np.float64)
        maximum=np.max(_matrix(values_function,t),axis=1)
        weighted=math.fsum((float(maximum[0]),float(maximum[-1]),
                            4*math.fsum(float(x) for x in maximum[1:-1:2]),
                            2*math.fsum(float(x) for x in maximum[2:-1:2])))
        pieces.append((upper-lower)*weighted/(3*count))
        interval_total+=count;evaluation_total+=count+1
    return math.fsum(pieces),interval_total,evaluation_total


def switch_slopes(values_function: Callable[[np.ndarray], np.ndarray],
                  switches: SwitchResult, partitions: tuple[float, ...]) -> list[dict]:
    records=[]
    for item in switches.switches:
        if item.endpoint:
            continue
        position=min(range(len(partitions)),key=lambda i:abs(partitions[i]-item.location))
        step=min(1e-6,(item.location-partitions[position-1])/4,
                 (partitions[position+1]-item.location)/4)
        if step <= 0:raise EnvelopeError("slope_probe_invalid")
        ts=np.array([item.location-step,item.location,item.location+step])
        envelope=np.max(_matrix(values_function,ts),axis=1)
        left=float((envelope[1]-envelope[0])/step);right=float((envelope[2]-envelope[1])/step)
        records.append({"location":item.location,"step":step,"envelope_value":float(envelope[1]),
                        "left_slope":left,"right_slope":right,"slope_change":right-left,
                        "continuous":max(abs(float(envelope[0]-envelope[1])),abs(float(envelope[2]-envelope[1]))) <=
                                     max(abs(left),abs(right),1.0)*step+VALUE_TIE_TOLERANCE})
    return records
