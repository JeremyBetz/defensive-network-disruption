"""Internal synthetic acceptance wiring; explicit inputs, no data or model loading."""
from __future__ import annotations

from dataclasses import dataclass
import itertools
import math
from pathlib import Path
import warnings

import numpy as np
from scipy.integrate import quad

from .integration_review import directional_breakpoints, values_for_components
from .occlusion_fields import CarrierOriginField, simpson_average
from .verification_audit import controlled_vector, scalar_oracle
from .verification_repair import (
    VerificationReadiness, find_verified_envelope, mapped_signature,
    independent_continuity, opposite_nonzero_signs,
)


class GateFailure(ValueError):
    """A required verification obligation failed; no accepted value is returned."""


def require(condition, reason):
    if not condition:
        raise GateFailure(reason)


def claim_execution(path: Path) -> None:
    """Exclusively claim a caller-supplied ignored execution location."""
    require(not any(p.is_symlink() for p in (path, *path.parents)), 'unsafe_marker')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as handle:
        handle.write('execution_claimed\n')


def validate_integrity(actual: dict[str, str], expected: dict[str, str]) -> bool:
    require(bool(expected) and actual == expected, 'integrity_mismatch')
    return actual == expected


def check_continuity(candidate, origin, defenders) -> bool:
    """Analytical valid-domain obligation plus independent scalar value checks."""
    require(independent_continuity(0., 0.) and independent_continuity(1., 1.), 'onset_limits')
    require(not independent_continuity(.2, .8), 'discontinuous_control')
    # Smoothstep derivatives at both joins equal the constant-branch derivative.
    require(6*0.-6*0.**2 == 0. and 6*1.-6*1.**2 == 0., 'onset_derivatives')
    field = CarrierOriginField(candidate)
    for defender in defenders:
        delta = np.asarray(defender, dtype=np.float64)-np.asarray(origin, dtype=np.float64)
        radius = float(np.linalg.norm(delta))
        require(math.isfinite(radius) and radius > 1e-9, 'continuity_domain')
        axis = delta/radius
        normal = np.array([-axis[1], axis[0]])
        for ell, lateral in ((-.1, 0.), (0., 0.), (.5, 2.), (1., 0.), (5., 2.)):
            for step in (0., 1e-1, 1e-2, 1e-3, 1e-4, 1e-5, 1e-6):
                for sign in (-1., 1.):
                    query = np.asarray(defender)+(ell+sign*step)*axis+lateral*normal
                    actual = float(field.individual_values(origin, (defender,), (query,))[0, 0])
                    expected = scalar_oracle(candidate, origin, defender, query)
                    require(math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12), 'continuity_oracle')
    return True


def certified_partitions(function, envelope, onset=()) -> tuple[float, ...]:
    """Validate and retain *both* float endpoints; never tolerance-deduplicate."""
    points = {0., 1., *onset, *envelope.partitions}
    for switch in envelope.switches:
        points.add(switch.location)
    for tie in envelope.tie_intervals:
        for boundary in (tie.start, tie.end):
            if boundary is None:
                continue
            outside, inside = boundary.outside, boundary.inside
            require(float(np.nextafter(outside, inside)) == inside, 'uncertified_boundary')
            require((outside < inside) == (boundary.direction == 'entry'), 'boundary_direction')
            values = function(np.array([outside, inside], dtype=np.float64))
            a, b = boundary.pair
            require(values[0, a] != values[0, b] and values[1, a] == values[1, b], 'boundary_predicate')
            maximum = float(np.max(values[1]))
            owners = tuple(int(i) for i in np.flatnonzero(maximum-values[1] <= 1e-12))
            require(maximum > 0. and owners == boundary.owners and set((a, b)) <= set(owners), 'boundary_owners')
            points.update((outside, inside))
    result = tuple(sorted(points))
    require(all(math.isfinite(x) and 0. <= x <= 1. for x in result), 'partition_domain')
    require(result[0] == 0. and result[-1] == 1., 'partition_endpoints')
    return result


def adaptive_maximum(function, partitions, tolerance):
    """Scalar quadrature of every positive-width piece, including float enclosures."""
    values = []
    for lower, upper in zip(partitions[:-1], partitions[1:], strict=True):
        require(upper > lower, 'partition_order')
        value, error = quad(lambda t: float(np.max(function(np.array([t], dtype=np.float64))[0])),
                            lower, upper, epsabs=tolerance, epsrel=tolerance, limit=1000)
        require(math.isfinite(value) and math.isfinite(error), 'adaptive_nonfinite')
        values.append(float(value))
    require(bool(values), 'no_pieces')
    return math.fsum(values)


def split_simpson(function, partitions, nominal):
    values = []; evaluations = 0
    for lower, upper in zip(partitions[:-1], partitions[1:], strict=True):
        require(upper > lower, 'partition_order')
        count = max(2, 2*math.ceil(nominal*(upper-lower)/2.))
        points = np.linspace(lower, upper, count+1, dtype=np.float64)
        maximum = np.max(function(points), axis=1)
        values.append((upper-lower)*float(simpson_average(maximum[:, None])[0]))
        evaluations += count+1
    return math.fsum(values), evaluations


def maximum_checks(function, envelope, onset, historical_failure):
    partitions = certified_partitions(function, envelope, onset)
    strict = adaptive_maximum(function, partitions, 1e-13)
    repeat = adaptive_maximum(function, partitions, 1e-11)
    unsplit = adaptive_maximum(function, tuple(sorted({0., 1., *onset})), 1e-13)
    direct = float(simpson_average(np.max(function(np.linspace(0., 1., 65537)), axis=1)[:, None])[0])
    require(abs(strict-repeat) <= 1e-10, 'piecewise_repeat')
    require(abs(strict-unsplit) <= 1e-10, 'piecewise_unsplit')
    require(abs(strict-direct) <= 1e-9, 'piecewise_direct')
    coarse = fine = None
    evaluations = None
    if historical_failure:
        coarse, first = split_simpson(function, partitions, 32768)
        fine, second = split_simpson(function, partitions, 65536)
        evaluations = [first, second]
        require(abs(coarse-fine) <= 1e-10, 'split_simpson_agreement')
    return {'partitions': list(partitions), 'piece_count': len(partitions)-1,
            'piecewise': strict, 'repeat': repeat, 'unsplit': unsplit, 'direct': direct,
            'split_coarse': coarse, 'split_fine': fine, 'split_evaluations': evaluations}


def check_repeatability(first, second):
    require(first == second, 'nondeterminism')
    return first == second


def check_permutation(expected, observed):
    require(expected == observed, 'permutation_mismatch')
    return expected == observed


def verify_case(candidate, origin, receiver, defenders, references, historical=None,
                historical_failure=False):
    """Accept one explicit synthetic case only after all numerical checks pass.

    The returned estimates are the unchanged uniform joint-Simpson vector.
    Certified partitions affect only independent maximum verification.
    Warnings and exceptions propagate; no partial result can be accepted.
    """
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        continuity = check_continuity(candidate, origin, defenders)
        field = CarrierOriginField(candidate)
        b = np.asarray(origin, dtype=np.float64)
        edge = np.asarray(receiver, dtype=np.float64)-b
        def function(t):
            return field.individual_values(origin, defenders, b[None, :]+t[:, None]*edge[None, :])
        onset = () if candidate == 'isotropic' else directional_breakpoints(origin, receiver, defenders)
        envelope = find_verified_envelope(function, extra_partitions=onset)
        repeat = find_verified_envelope(function, extra_partitions=onset)
        deterministic = check_repeatability(envelope, repeat)
        identity = tuple(range(len(defenders)))
        expected = mapped_signature(envelope, identity)
        permutation_count = 0
        for permutation in itertools.permutations(identity):
            permuted = envelope if permutation == identity else find_verified_envelope(
                lambda t, p=permutation: function(t)[:, p], extra_partitions=onset)
            check_permutation(expected, mapped_signature(permuted, permutation))
            permutation_count += 1
        maximum = maximum_checks(function, envelope, onset, historical_failure)
        count, estimates, change = controlled_vector(
            lambda n: values_for_components(field, origin, receiver, defenders, n))
        require(count is not None, 'controlled_nonconvergence')
        require(set(estimates) == set(references), 'references_unavailable')
        errors = {}
        for name, value in estimates.items():
            reference = references[name]
            require(type(reference) in (float, int) and math.isfinite(reference), 'reference_nonfinite')
            errors[name] = abs(value-reference)
            require(errors[name] <= 1e-6, 'reference_error')
        if historical is not None:
            require(count == historical['intervals'] and estimates == historical['estimates'], 'historical_vector_changed')
        return {'intervals': count, 'estimates': estimates, 'errors': errors,
                'change': change, 'maximum': maximum, 'permutations': permutation_count,
                'continuity': continuity, 'deterministic': deterministic}


@dataclass(frozen=True)
class PipelineOutcome:
    readiness: VerificationReadiness
    accepted: tuple[dict, ...]
    failure: str | None


def run_pipeline(cases, actual_hashes, expected_hashes, enforcement_verified):
    """All-or-nothing acceptance; any actual pipeline failure leaves readiness false."""
    states = {name: False for name in VerificationReadiness.__dataclass_fields__}
    results = []
    try:
        states['integrity_verified'] = validate_integrity(actual_hashes, expected_hashes)
        require(bool(cases), 'cases_unavailable')
        for case in cases:
            results.append(verify_case(**case))
        states.update(continuity_verified=all(r['continuity'] for r in results),
                      switching_verified=all(r['maximum']['piece_count'] > 0 for r in results),
                      controlled_integration_verified=all(r['intervals'] is not None for r in results),
                      references_complete=all(bool(r['errors']) and max(r['errors'].values()) <= 1e-6 for r in results),
                      permutation_verified=all(r['permutations'] > 0 for r in results),
                      deterministic=all(r['deterministic'] for r in results),
                      failure_enforcement_verified=enforcement_verified,
                      blocking_warnings_absent=len(results) == len(cases))
        gate = VerificationReadiness(**states)
        return PipelineOutcome(gate, tuple(results) if gate.ready else (), None if gate.ready else 'enforcement_unverified')
    except Exception as error:
        # Failure categories are class names, never caller values or payloads.
        return PipelineOutcome(VerificationReadiness(**states), (), type(error).__name__)


def engineering_functions():
    """Prospectively frozen engineering oracles; not field alternatives."""
    return {
        'constant': lambda t: np.full((len(t), 1), .6),
        'crossing': lambda t: np.column_stack((t, 1-t)),
        'three_constants': lambda t: np.full((len(t), 3), .6),
        'rounded_plateau': lambda t: np.column_stack((np.full_like(t, .6),
            .6-.1*np.maximum.reduce((.251-t, t-.749, np.zeros_like(t))))),
        'exact_plateau': lambda t: np.column_stack((np.full_like(t, .6),
            np.where((t >= .251) & (t <= .749), .6, np.nextafter(.6, 0.)))),
        'multiway_plateau': lambda t: np.column_stack((np.full_like(t, .6), *[
            .6-.1*np.maximum.reduce((.251-t, t-.749, np.zeros_like(t))) for _ in range(3)])),
    }


def engineering_checks():
    """Stop on any additional detector defect without repairing it."""
    rows = []
    for name, function in engineering_functions().items():
        result = find_verified_envelope(function)
        partitions = certified_partitions(function, result)
        count = function(np.array([.5])).shape[1]
        identity = tuple(range(count))
        signature = mapped_signature(result, identity)
        comparisons = 0
        enclosures = [[boundary.outside, boundary.inside] for tie in result.tie_intervals
                      for boundary in (tie.start, tie.end) if boundary is not None]
        for permutation in itertools.permutations(identity):
            other = result if permutation == identity else find_verified_envelope(lambda t, p=permutation: function(t)[:, p])
            observed = mapped_signature(other, permutation)
            if signature != observed:
                rows.append({'fixture': name, 'passed': False, 'reason': 'mapped_record_mismatch',
                             'permutations_checked': comparisons+1, 'partition_count': len(partitions),
                             'boundary_enclosures': enclosures,
                             'different_sections': [name for name, a, b in zip(
                                 ('switches','tie_intervals','maximizing_defenders','partitions','grid'),
                                 signature, observed, strict=True) if a != b]})
                return rows
            comparisons += 1
        rows.append({'fixture': name, 'passed': True, 'reason': None,
                     'permutations_checked': comparisons, 'partition_count': len(partitions),
                     'boundary_enclosures': enclosures, 'different_sections': []})
    return rows
