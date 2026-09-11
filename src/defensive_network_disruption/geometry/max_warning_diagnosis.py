"""Internal numerical diagnostics for an explicitly supplied maximum envelope."""
from __future__ import annotations

from dataclasses import dataclass
import math
import warnings

import numpy as np
from scipy.integrate import IntegrationWarning, quad

from .integration_review import directional_breakpoints, values_for_components
from .occlusion_fields import CarrierOriginField, points, simpson_average
from .production_verification import certified_partitions, split_simpson
from .verification_audit import controlled_vector, scalar_oracle
from .verification_repair import find_verified_envelope


@dataclass(frozen=True)
class QuadDiagnostic:
    value: float
    error: float
    evaluations: int
    subdivisions: int
    message: str | None


@dataclass(frozen=True)
class LocatedWarning:
    candidate: str
    receiver_ordinal: int
    lower: float
    upper: float
    value: float
    error: float
    category: str
    message: str


class WarningLocated(RuntimeError):
    """Internal control flow preserving one real quadrature warning."""

    def __init__(self, record: LocatedWarning):
        super().__init__(record.message)
        self.record = record


def maximum_function(candidate, origin, receiver, defenders):
    """Return the frozen scalar maximum integrand and its certified envelope."""
    field = CarrierOriginField(candidate)
    b = points(origin, one=True)
    end = points(receiver, one=True)
    ds = points(defenders)

    def individual(t):
        query = b[None, :] + np.asarray(t, dtype=np.float64)[:, None] * (end - b)[None, :]
        return field.individual_values(b, ds, query)

    onset = () if candidate == "isotropic" else directional_breakpoints(b, end, ds)
    envelope = find_verified_envelope(individual, extra_partitions=onset)
    partitions = certified_partitions(individual, envelope, onset)
    return field, b, end, ds, individual, onset, envelope, partitions


def locate_warning(candidates, origin, receivers, defenders, evaluate_edge, production_module):
    """Traverse the frozen order and stop at the first real IntegrationWarning."""
    original = production_module.quad
    context = {"candidate": None, "receiver": None}

    def wrapped(function, lower, upper, **kwargs):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", IntegrationWarning)
            value, error = original(function, lower, upper, **kwargs)
        for item in caught:
            if issubclass(item.category, IntegrationWarning):
                record = LocatedWarning(
                    str(context["candidate"]), int(context["receiver"]), float(lower), float(upper),
                    float(value), float(error), item.category.__name__, str(item.message),
                )
                raise WarningLocated(record)
        return value, error

    production_module.quad = wrapped
    try:
        for candidate in candidates:
            context["candidate"] = candidate
            for receiver_ordinal, receiver in enumerate(receivers):
                context["receiver"] = receiver_ordinal
                evaluate_edge(candidate, origin, receiver, defenders)
    finally:
        production_module.quad = original
    return None


def quad_diagnostic(function, lower, upper, tolerance):
    """Return bounded QUADPACK diagnostics without exposing work arrays."""
    result = quad(function, lower, upper, epsabs=tolerance, epsrel=tolerance,
                  limit=1000, full_output=1)
    value, error, info, *tail = result
    message = str(tail[0]) if tail else None
    numbers = (value, error)
    if not all(math.isfinite(float(item)) for item in numbers):
        raise ValueError("nonfinite_quad_diagnostic")
    return QuadDiagnostic(float(value), float(error), int(info.get("neval", 0)),
                          int(info.get("last", 0)), message)


def width_summary(partitions):
    """Summarize every positive normalized partition width."""
    widths = tuple(float(b - a) for a, b in zip(partitions[:-1], partitions[1:], strict=True))
    if not widths or not all(math.isfinite(x) and x > 0 for x in widths):
        raise ValueError("invalid_partition_width")
    adjacent = sum(float(np.nextafter(a, b)) == b for a, b in zip(partitions[:-1], partitions[1:], strict=True))
    return {
        "piece_count": len(widths), "minimum": min(widths),
        "median": float(np.median(np.asarray(widths))), "maximum": max(widths),
        "adjacent_float_pieces": int(adjacent),
    }


def controlled_diagnostic(field, origin, receiver, defenders):
    """Apply the frozen all-component ladder twice and require determinism."""
    first = controlled_vector(lambda n: values_for_components(field, origin, receiver, defenders, n))
    second = controlled_vector(lambda n: values_for_components(field, origin, receiver, defenders, n))
    if first != second:
        raise ValueError("controlled_nondeterministic")
    count, estimates, change = first
    return {
        "converged": count is not None,
        "intervals": count,
        "maximum_component_change": float(change) if change is not None else None,
        "finite": bool(estimates) and all(math.isfinite(x) for x in estimates.values()),
        "deterministic": True,
    }, estimates


def method_diagnostic(individual, onset, partitions):
    """Compare only the previously authorized maximum integration methods."""
    scalar = lambda t: float(np.max(individual(np.array([t], dtype=np.float64))[0]))
    strict_parts = [quad_diagnostic(scalar, a, b, 1e-13)
                    for a, b in zip(partitions[:-1], partitions[1:], strict=True)]
    repeat_parts = [quad_diagnostic(scalar, a, b, 1e-11)
                    for a, b in zip(partitions[:-1], partitions[1:], strict=True)]
    onset_partitions = tuple(sorted({0.0, 1.0, *onset}))
    unsplit_parts = [quad_diagnostic(scalar, a, b, 1e-13)
                     for a, b in zip(onset_partitions[:-1], onset_partitions[1:], strict=True)]
    strict = math.fsum(x.value for x in strict_parts)
    repeat = math.fsum(x.value for x in repeat_parts)
    unsplit = math.fsum(x.value for x in unsplit_parts)
    direct_t = np.linspace(0.0, 1.0, 65537, dtype=np.float64)
    direct = float(simpson_average(np.max(individual(direct_t), axis=1)[:, None])[0])
    split32, eval32 = split_simpson(individual, partitions, 32768)
    split65, eval65 = split_simpson(individual, partitions, 65536)
    values = {"piecewise_strict": strict, "piecewise_repeat": repeat,
              "unsplit_adaptive": unsplit, "direct_simpson_65536": direct,
              "split_simpson_32768": split32, "split_simpson_65536": split65}
    differences = {f"{left}_vs_{right}": abs(values[left] - values[right])
                   for index, left in enumerate(values) for right in tuple(values)[index + 1:]}
    return values, differences, strict_parts, repeat_parts, unsplit_parts, (eval32, eval65)


def continuity_diagnostic(candidate, origin, receiver, defenders, partitions, active_piece):
    """Check production values against an independent scalar oracle near boundaries."""
    field = CarrierOriginField(candidate)
    b, end, ds = points(origin, one=True), points(receiver, one=True), points(defenders)
    edge = end - b
    relevant = sorted(set((active_piece[0], active_piece[1])))
    max_oracle_error = 0.0
    maximum_jumps = []
    owner_transitions = 0
    for boundary in relevant:
        prior = max((x for x in partitions if x < boundary), default=0.0)
        later = min((x for x in partitions if x > boundary), default=1.0)
        room = min(boundary - prior if boundary > 0 else 1.0,
                   later - boundary if boundary < 1 else 1.0)
        step = min(1e-7, room / 4.0)
        if step <= 0:
            continue
        left_t, right_t = max(0.0, boundary - step), min(1.0, boundary + step)
        rows = []
        for t in (left_t, boundary, right_t):
            query = b + t * edge
            actual = field.individual_values(b, ds, query[None, :])[0]
            expected = np.array([scalar_oracle(candidate, b, defender, query) for defender in ds])
            max_oracle_error = max(max_oracle_error, float(np.max(np.abs(actual - expected))))
            rows.append(actual)
        maximum_jumps.append(abs(float(np.max(rows[2])) - float(np.max(rows[0]))))
        before = set(np.flatnonzero(np.max(rows[0]) - rows[0] <= 1e-12))
        after = set(np.flatnonzero(np.max(rows[2]) - rows[2] <= 1e-12))
        owner_transitions += before != after
    return {
        "analytical_continuity_obligation": True,
        "oracle_comparison_passed": max_oracle_error <= 1e-12,
        "maximum_oracle_error": max_oracle_error,
        "largest_two_sided_finite_step_change": max(maximum_jumps, default=0.0),
        "owner_transitions": int(owner_transitions),
        "finite_step_is_not_continuity_proof": True,
    }
