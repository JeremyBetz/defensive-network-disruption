"""Bounded-residual verification for machine-scale maximum-envelope pieces."""
from __future__ import annotations

from dataclasses import dataclass
import itertools
import math
import warnings

import numpy as np

from . import production_verification as historical
from .integration_review import directional_breakpoints, values_for_components
from .occlusion_fields import CarrierOriginField, simpson_average
from .verification_audit import controlled_vector
from .verification_repair import find_verified_envelope, mapped_signature


GLOBAL_RESIDUAL_BUDGET = 1e-12
FIELD_UPPER_BOUND = 1.0


@dataclass(frozen=True)
class IntegralInterval:
    """Closed integral interval plus deterministic work-accounting metadata."""

    lower: float
    upper: float
    residual_bound: float
    structural_piece_count: int
    quadrature_piece_count: int
    bounded_piece_count: int


def interval_distance(first: IntegralInterval, second: IntegralInterval) -> float:
    """Return the gap between closed intervals, or zero when they overlap."""
    return max(0.0, first.lower - second.upper, second.lower - first.upper)


def point_interval_distance(value: float, interval: IntegralInterval) -> float:
    """Return the distance from a finite point to a closed interval."""
    historical.require(math.isfinite(value), "nonfinite_comparison")
    return max(0.0, interval.lower - value, value - interval.upper)


def bounded_adaptive_maximum(function, partitions, tolerance, *,
                             residual_budget=GLOBAL_RESIDUAL_BUDGET,
                             upper_bound=FIELD_UPPER_BOUND) -> IntegralInterval:
    """Integrate ordinary pieces and bound qualifying machine-scale pieces.

    Structural pieces are never merged or removed from the accounting record.
    The adaptive work list alone omits pieces whose worst-case integral fits the
    fixed per-piece allocation of the global residual budget.
    """
    historical.require(type(partitions) in (tuple, list) and len(partitions) >= 2,
                       "no_pieces")
    historical.require(math.isfinite(residual_budget) and residual_budget >= 0.0,
                       "invalid_residual_budget")
    historical.require(math.isfinite(upper_bound) and upper_bound == 1.0,
                       "field_bound_changed")
    pieces = []
    for lower, upper in zip(partitions[:-1], partitions[1:], strict=True):
        lower = float(lower); upper = float(upper)
        historical.require(math.isfinite(lower) and math.isfinite(upper) and upper > lower,
                           "partition_order")
        pieces.append((lower, upper, upper - lower))
    allocation = residual_budget / len(pieces)
    estimates = []
    residuals = []
    bounded = 0
    for lower, upper, width in pieces:
        worst_case = upper_bound * width
        if worst_case <= allocation:
            residuals.append(worst_case)
            bounded += 1
            continue
        value, error = historical.quad(
            lambda t: float(np.max(function(np.array([t], dtype=np.float64))[0])),
            lower, upper, epsabs=tolerance, epsrel=tolerance, limit=1000,
        )
        historical.require(math.isfinite(value) and math.isfinite(error),
                           "adaptive_nonfinite")
        estimates.append(float(value))
    summed_estimate = math.fsum(estimates)
    summed_residual = math.fsum(residuals)
    # Outward rounding makes the published float64 enclosure conservative even
    # when the ordinary-piece sum or residual sum rounds toward the interior.
    lower_total = (max(0.0, float(np.nextafter(summed_estimate, -math.inf)))
                   if estimates else 0.0)
    residual_total = summed_residual
    historical.require(residual_total <= residual_budget, "residual_budget_exceeded")
    upper_total = float(np.nextafter(math.fsum((summed_estimate, residual_total)), math.inf))
    return IntegralInterval(lower_total, upper_total, residual_total, len(pieces),
                            len(estimates), bounded)


def maximum_checks(function, envelope, onset=(), historical_failure=False):
    """Apply interval-aware independent maximum checks without changing Simpson."""
    partitions = historical.certified_partitions(function, envelope, onset)
    strict = bounded_adaptive_maximum(function, partitions, 1e-13)
    repeat = bounded_adaptive_maximum(function, partitions, 1e-11)
    onset_partitions = tuple(sorted({0.0, 1.0, *onset}))
    unsplit = historical.adaptive_maximum(function, onset_partitions, 1e-13)
    direct = float(simpson_average(
        np.max(function(np.linspace(0.0, 1.0, 65537, dtype=np.float64)), axis=1)[:, None]
    )[0])
    historical.require(interval_distance(strict, repeat) <= 1e-10, "piecewise_repeat")
    historical.require(point_interval_distance(unsplit, strict) <= 1e-10,
                       "piecewise_unsplit")
    historical.require(point_interval_distance(direct, strict) <= 1e-9,
                       "piecewise_direct")
    coarse = fine = None
    evaluations = None
    if historical_failure:
        coarse, first = historical.split_simpson(function, partitions, 32768)
        fine, second = historical.split_simpson(function, partitions, 65536)
        evaluations = [first, second]
        historical.require(abs(coarse - fine) <= 1e-10, "split_simpson_agreement")
        historical.require(point_interval_distance(coarse, strict) <= 1e-10,
                           "split_coarse_reference")
        historical.require(point_interval_distance(fine, strict) <= 1e-10,
                           "split_fine_reference")
    return {
        "partitions": list(partitions), "piece_count": len(partitions) - 1,
        "piecewise": strict, "repeat": repeat, "unsplit": unsplit, "direct": direct,
        "split_coarse": coarse, "split_fine": fine, "split_evaluations": evaluations,
    }


def verify_case(candidate, origin, receiver, defenders, references, historical_vector=None,
                historical_failure=False):
    """Run the accepted synthetic path with interval-aware maximum verification."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        continuity = historical.check_continuity(candidate, origin, defenders)
        field = CarrierOriginField(candidate)
        base = np.asarray(origin, dtype=np.float64)
        edge = np.asarray(receiver, dtype=np.float64) - base

        def function(t):
            query = base[None, :] + t[:, None] * edge[None, :]
            return field.individual_values(origin, defenders, query)

        onset = () if candidate == "isotropic" else directional_breakpoints(
            origin, receiver, defenders)
        envelope = find_verified_envelope(function, extra_partitions=onset)
        repeated = find_verified_envelope(function, extra_partitions=onset)
        deterministic = historical.check_repeatability(envelope, repeated)
        identity = tuple(range(len(defenders)))
        signature = mapped_signature(envelope, identity)
        permutations = 0
        for permutation in itertools.permutations(identity):
            permuted = envelope if permutation == identity else find_verified_envelope(
                lambda t, p=permutation: function(t)[:, p], extra_partitions=onset)
            historical.check_permutation(signature, mapped_signature(permuted, permutation))
            permutations += 1
        maximum = maximum_checks(function, envelope, onset, historical_failure)
        intervals, estimates, change = controlled_vector(
            lambda count: values_for_components(field, origin, receiver, defenders, count))
        historical.require(intervals is not None, "controlled_nonconvergence")
        historical.require(set(estimates) == set(references), "references_unavailable")
        errors = {}
        for component, estimate in estimates.items():
            reference = references[component]
            historical.require(type(reference) in (float, int) and math.isfinite(reference),
                               "reference_nonfinite")
            errors[component] = abs(estimate - reference)
            historical.require(errors[component] <= 1e-6, "reference_error")
        historical.require(point_interval_distance(float(references["maximum"]),
                                                   maximum["piecewise"]) <= 1e-6,
                           "maximum_reference_interval")
        historical.require(point_interval_distance(float(estimates["maximum"]),
                                                   maximum["piecewise"]) <= 1e-6,
                           "joint_maximum_interval")
        if historical_vector is not None:
            historical.require(intervals == historical_vector["intervals"] and
                               estimates == historical_vector["estimates"],
                               "historical_vector_changed")
        return {
            "intervals": intervals, "estimates": estimates, "errors": errors,
            "change": change, "maximum": maximum, "permutations": permutations,
            "continuity": continuity, "deterministic": deterministic,
        }
