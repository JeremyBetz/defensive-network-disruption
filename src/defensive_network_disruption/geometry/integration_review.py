"""Internal synthetic numerical diagnostics for the closed Session 14 fields."""
from __future__ import annotations

from dataclasses import dataclass
import math
import warnings

import numpy as np
from scipy.integrate import IntegrationWarning, quad

from .occlusion_fields import CarrierOriginField, combine, points, simpson_average


ORDINARY_INTERVALS = (16, 32, 64, 128, 256, 512, 1024, 2048)
FINE_INTERVALS = (4096, 8192, 16384, 32768, 65536)
REFERENCE_ABSOLUTE_TOLERANCE = 1e-13
REFERENCE_RELATIVE_TOLERANCE = 1e-13
REFERENCE_LIMIT = 1000
REFERENCE_REPEAT_TOLERANCE = 1e-10
REFERENCE_FINE_DELTA_TOLERANCE = 1e-10
REFERENCE_FINE_ERROR_TOLERANCE = 1e-9
RELATIVE_ERROR_FLOOR = 1e-12
ORACLE_TOLERANCE = 32 * np.finfo(np.float64).eps


@dataclass(frozen=True)
class Component:
    name: str
    defender_index: int | None = None


@dataclass(frozen=True)
class Reference:
    value: float
    estimated_error: float
    repeat_value: float
    fine_32768: float
    fine_65536: float
    available: bool
    reason: str | None


def components(defender_count: int) -> tuple[Component, ...]:
    if defender_count < 1:
        raise ValueError("positive_defender_count_required")
    return tuple(Component(f"individual_{i + 1}", i) for i in range(defender_count)) + (
        Component("union"), Component("maximum"))


def values_for_components(field: CarrierOriginField, origin, receiver, defenders, intervals: int) -> dict[str, float]:
    if isinstance(intervals, bool) or not isinstance(intervals, int) or intervals < 2 or intervals % 2:
        raise ValueError("positive_even_interval_count_required")
    b = points(origin, one=True)
    end = points(receiver, one=True)
    ds = points(defenders)
    t = np.linspace(0.0, 1.0, intervals + 1, dtype=np.float64)
    queries = b[None, :] + t[:, None] * (end - b)[None, :]
    individual = field.individual_values(b, ds, queries)
    all_values = np.column_stack((individual, combine(individual, "union"), combine(individual, "maximum")))
    estimates = simpson_average(all_values)
    return {component.name: float(value) for component, value in zip(components(len(ds)), estimates, strict=True)}


def directional_breakpoints(origin, receiver, defenders) -> tuple[float, ...]:
    """Return exact normalized-edge locations where any directional gate changes piece."""
    b = points(origin, one=True)
    end = points(receiver, one=True)
    ds = points(defenders)
    edge = end - b
    locations: list[float] = []
    for defender in ds:
        vector = defender - b
        radius = math.hypot(float(vector[0]), float(vector[1]))
        if radius <= 1e-9:
            raise ValueError("origin_defender_direction_undefined")
        unit = vector / radius
        slope = float(np.dot(edge, unit))
        intercept = float(np.dot(b - defender, unit))
        if slope == 0.0:
            continue
        for target in (0.0, 1.0):
            location = (target - intercept) / slope
            if 0.0 < location < 1.0:
                locations.append(float(location))
    return tuple(sorted(set(locations)))


def scalar_component(field: CarrierOriginField, origin, receiver, defenders, component: Component, t: float) -> float:
    b = points(origin, one=True)
    end = points(receiver, one=True)
    ds = points(defenders)
    query = b + float(t) * (end - b)
    row = field.individual_values(b, ds, query[None, :])
    if component.defender_index is not None:
        return float(row[0, component.defender_index])
    return float(combine(row, component.name)[0])


def adaptive_reference(field: CarrierOriginField, origin, receiver, defenders, component: Component,
                       fine_estimates: dict[int, dict[str, float]]) -> Reference:
    breakpoints = directional_breakpoints(origin, receiver, defenders) if field.candidate != "isotropic" else ()

    def integrand(t: float) -> float:
        return scalar_component(field, origin, receiver, defenders, component, t)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", IntegrationWarning)
        strict, strict_error = quad(integrand, 0.0, 1.0, epsabs=REFERENCE_ABSOLUTE_TOLERANCE,
                                    epsrel=REFERENCE_RELATIVE_TOLERANCE, limit=REFERENCE_LIMIT,
                                    points=breakpoints or None)
        repeat, _ = quad(integrand, 0.0, 1.0, epsabs=1e-11, epsrel=1e-11,
                         limit=REFERENCE_LIMIT, points=breakpoints or None)
    reasons: list[str] = []
    if caught:
        reasons.append("adaptive_warning")
    numbers = (strict, strict_error, repeat, fine_estimates[32768][component.name], fine_estimates[65536][component.name])
    if not all(math.isfinite(float(value)) for value in numbers):
        reasons.append("nonfinite_reference")
    if abs(strict - repeat) > REFERENCE_REPEAT_TOLERANCE:
        reasons.append("adaptive_repeat_disagreement")
    if abs(fine_estimates[65536][component.name] - fine_estimates[32768][component.name]) > REFERENCE_FINE_DELTA_TOLERANCE:
        reasons.append("fine_grid_not_converged")
    if abs(fine_estimates[65536][component.name] - strict) > REFERENCE_FINE_ERROR_TOLERANCE:
        reasons.append("fine_grid_adaptive_disagreement")
    return Reference(float(strict), float(strict_error), float(repeat),
                     fine_estimates[32768][component.name], fine_estimates[65536][component.name],
                     not reasons, ";".join(reasons) or None)


def polynomial_oracles(intervals: tuple[int, ...] = ORDINARY_INTERVALS) -> list[dict[str, float | int | str | bool]]:
    expected = (1.0, 0.5, 1.0 / 3.0, 0.25)
    names = ("constant", "linear", "quadratic", "cubic")
    records = []
    for count in intervals:
        t = np.linspace(0.0, 1.0, count + 1, dtype=np.float64)
        estimates = simpson_average(np.column_stack((np.ones_like(t), t, t * t, t * t * t)))
        for name, estimate, truth in zip(names, estimates, expected, strict=True):
            error = abs(float(estimate) - truth)
            records.append({"function": name, "intervals": count, "estimate": float(estimate),
                            "expected": truth, "absolute_error": error, "passed": error <= ORACLE_TOLERANCE})
    return records


def historical_failure() -> dict[str, float | int]:
    field = CarrierOriginField("expanding")
    coarse = values_for_components(field, (0, 0), (20, 0), ((5, 1),), 80)["individual_1"]
    fine = values_for_components(field, (0, 0), (20, 0), ((5, 1),), 160)["individual_1"]
    return {"coarse_intervals": 80, "fine_intervals": 160, "coarse_value": coarse,
            "fine_value": fine, "absolute_difference": abs(fine - coarse)}

