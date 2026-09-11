"""Internal synthetic audit instruments; never an empirical integration path."""
from __future__ import annotations

import ast
from dataclasses import asdict
import itertools
import math
from unittest.mock import patch

import numpy as np

from . import maximum_envelope as envelope
from .integration_review import values_for_components
from .occlusion_fields import CarrierOriginField, CANDIDATES

COUNTS = (256, 512, 1024, 2048, 4096, 8192, 16384)


def controlled_vector(evaluator):
    """First jointly converged finer vector; no per-component early stop."""
    previous = None
    for count in COUNTS:
        current = evaluator(count)
        if not current or any(not math.isfinite(x) for x in current.values()):
            raise ValueError('invalid_estimates')
        if previous is not None:
            if set(current) != set(previous):
                raise ValueError('component_mismatch')
            change = max(abs(current[k]-previous[k]) for k in current)
            if change <= 1e-7:
                return count, current, change
        previous = current
    return None, current, change


def scalar_oracle(candidate, origin, defender, query):
    """Independent scalar formula using dot/cross operations and piecewise gate."""
    dx, dy = defender[0]-origin[0], defender[1]-origin[1]
    radius = math.hypot(dx, dy)
    if radius <= 1e-9:
        raise ValueError('invalid_origin')
    qx, qy = query[0]-defender[0], query[1]-defender[1]
    if candidate == 'isotropic':
        return math.exp(-(qx*qx+qy*qy)/8)
    ell = (qx*dx+qy*dy)/radius
    lateral = abs(qx*dy-qy*dx)/radius
    gate = 0.0 if ell <= 0 else 1.0 if ell >= 1 else 3*ell**2-2*ell**3
    width = 2.0 + (max(ell, 0)*math.tan(math.pi/18) if candidate == 'expanding' else 0)
    return gate*math.exp(-lateral*lateral/(2*width*width))


def value_oracles():
    rows = []
    for origin, defender in (((0, 0), (5, 0)), ((1, -2), (4, 2))):
        dx, dy = defender[0]-origin[0], defender[1]-origin[1]
        radius = math.hypot(dx, dy)
        for ell, lateral in ((-1, 0), (0, 0), (.5, 0), (1, 0), (5, 0), (5, 2)):
            query = (defender[0]+ell*dx/radius-lateral*dy/radius,
                     defender[1]+ell*dy/radius+lateral*dx/radius)
            for candidate in CANDIDATES:
                expected = scalar_oracle(candidate, origin, defender, query)
                actual = float(CarrierOriginField(candidate).individual_values(origin, (defender,), (query,))[0, 0])
                rows.append({'candidate': candidate, 'origin_kind': 'axial' if origin == (0, 0) else 'rotated',
                             'ell': ell, 'lateral': lateral, 'expected': expected, 'actual': actual,
                             'error': abs(actual-expected),
                             'passed': math.isclose(actual, expected, abs_tol=1e-12, rel_tol=1e-12)})
    return rows


def perturbation_oracles():
    rows = []
    for candidate in CANDIDATES:
        field = CarrierOriginField(candidate)
        for point in ((5, 0), (6, 0), (10, 0), (10, 2)):
            for axis in (0, 1):
                for delta in (1e-1, 1e-2, 1e-3, 1e-4):
                    left, right = list(point), list(point)
                    left[axis] -= delta; right[axis] += delta
                    values = field.individual_values((0, 0), ((5, 0),), (left, point, right))[:, 0]
                    rows.append({'candidate': candidate, 'point': list(point), 'axis': axis,
                                 'displacement': delta, 'left_delta': float(values[0]-values[1]),
                                 'right_delta': float(values[2]-values[1])})
    return rows


def discontinuity_counterexample():
    def step(t):
        return np.column_stack((np.where(t < .5, .2, .8), np.zeros_like(t)))
    switch = envelope.EnvelopeSwitch(.5, (0,), (0,), (0,), (), False, False, .8)
    result = envelope.SwitchResult((switch,), (), (0,), 65536)
    observed = envelope.switch_slopes(step, result, (0., .5, 1.))[0]
    return {'known_jump': .6, 'historical_flag': bool(observed['continuous']),
            'left_slope': observed['left_slope'], 'right_slope': observed['right_slope'],
            'historical_flag_distinguishes_jump': not bool(observed['continuous'])}


def complete_signature(result, permutation):
    """Map all governed records back into original defender coordinates."""
    owners = lambda seq: tuple(sorted(permutation[i] for i in seq))
    switches = tuple((s.location, owners(s.owners_before), owners(s.owners_at), owners(s.owners_after),
                      tuple(sorted(tuple(sorted((permutation[a], permutation[b]))) for a, b in s.crossing_pairs)),
                      s.endpoint, s.multiway, s.envelope_value) for s in result.switches)
    ties = tuple(sorted((x.start, x.end, owners(x.owners)) for x in result.tie_intervals))
    return switches, ties, owners(result.maximizing_defenders), result.grid_intervals


def engineering_switching():
    functions = {
        'single': lambda t: np.column_stack((t, 1-t)),
        'multiple': lambda t: np.column_stack((.5+.2*np.sin(4*math.pi*t), np.full_like(t, .5))),
        'non_envelope': lambda t: np.column_stack((.2+.1*t, .3-.1*t, np.full_like(t, .8))),
        'endpoint': lambda t: np.column_stack((.5+.4*t, .5-.1*t)),
        'zero': lambda t: np.column_stack((np.zeros_like(t), np.zeros_like(t))),
        'duplicates': lambda t: np.column_stack((np.full_like(t, .7), np.full_like(t, .7), np.full_like(t, .2))),
        'three_way': lambda t: np.column_stack((t, 1-t, np.full_like(t, .5))),
        'tie_interval': lambda t: np.column_stack((np.full_like(t, .6), .6-.1*np.maximum.reduce((.25-t, t-.75, np.zeros_like(t))))),
        'non_node_tie': lambda t: np.column_stack((np.full_like(t, .6), .6-.1*np.maximum.reduce((.251-t, t-.749, np.zeros_like(t))))),
        'hidden_crossings': lambda t: np.column_stack((np.full_like(t, .4), .3+.2*np.maximum(0, 1-np.abs(t-(32768.5/65536))/(.4/65536)))),
    }
    rows = []
    for name, function in functions.items():
        result = envelope.find_envelope_switches(function)
        rows.append({'fixture': name, 'interior_switches': sum(not s.endpoint for s in result.switches),
                     'endpoint_ties': sum(s.endpoint for s in result.switches),
                     'tie_intervals': [asdict(x) for x in result.tie_intervals],
                     'maximizing_count': len(result.maximizing_defenders)})
    def tiny(t):
        return np.column_stack((np.full_like(t, 5e-200)+1e-200*(t-.500001), np.full_like(t, 5e-200)))
    with patch.object(envelope, 'brentq', wraps=envelope.brentq) as root:
        envelope.find_envelope_switches(tiny)
        root_calls = root.call_count
    rows.append({'fixture': 'raw_sign_underflow', 'expected_raw_brackets': 1, 'brent_calls': root_calls})
    with patch.object(envelope, 'brentq', side_effect=RuntimeError('injected')):
        try:
            envelope.find_envelope_switches(lambda t: np.column_stack((.9*t+.001, 1-t)))
        except envelope.EnvelopeError:
            blocked = True
        else:
            blocked = False
    rows.append({'fixture': 'failed_root', 'blocked': blocked})
    dedup = envelope._deduplicate_roots([(.5, (0, 1)), (.5+5e-13, (1, 2))])
    rows.append({'fixture': 'deduplication', 'groups': len(dedup), 'pairs': len(dedup[0][1])})
    return rows


def historical_decision_function(source):
    """Extract unchanged decision statements only; never run the historical review."""
    tree = ast.parse(source)
    review = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'review')
    def assigned(node, name):
        return isinstance(node, ast.Assign) and any(isinstance(x, ast.Name) and x.id == name for x in node.targets)
    start = next(i for i, n in enumerate(review.body) if assigned(n, 'unresolved'))
    end = next(i for i, n in enumerate(review.body) if assigned(n, 'grouped'))
    result = ast.Return(ast.Tuple([ast.Name(x, ast.Load()) for x in ('classification', 'maximum_decision', 'readiness')], ast.Load()))
    function = ast.FunctionDef(name='decision', args=ast.arguments(posonlyargs=[], args=[ast.arg(x) for x in
        ('case_rows', 'switch_rows', 'deterministic', 'permutation_stable')], kwonlyargs=[], kw_defaults=[], defaults=[]),
        body=review.body[start:end]+[result], decorator_list=[])
    module = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
    scope = {'SPLIT_SIMPSON_AGREEMENT': 1e-10}
    exec(compile(module, '<historical-decision-only>', 'exec'), scope)
    return scope['decision']


def enforcement_oracles(source):
    decision = historical_decision_function(source)
    results = []
    for failure in ('none', 'warning', 'unavailable_reference', 'numerical_agreement',
                    'nondeterminism', 'permutation_mismatch', 'continuity'):
        rows = [{'historical_status': 'unresolved', 'available': True, 'interior_switch_count': 1,
                 'split_simpson_difference': 0., 'controlled_intervals': 512,
                 'controlled_reference_error': 0.} for _ in range(4)]
        if failure in ('warning', 'unavailable_reference', 'numerical_agreement'):
            rows[0]['available'] = False
        classification, maximum, readiness = decision(rows, [{'continuous': failure != 'continuity'}],
                                                       failure != 'nondeterminism', failure != 'permutation_mismatch')
        results.append({'injected': failure, 'classification': classification, 'maximum_decision': maximum,
                        'readiness': readiness, 'blocks_retry': not readiness.startswith(('1', '2'))})
    return results


def summarize_result(oracles, switches, controlled, enforcement):
    defects = []
    if not all(r['passed'] for r in oracles): defects.append('field_oracle_mismatch')
    if any(not r['deterministic'] or not r['permutation_equal'] for r in switches):
        defects.append('full_permutation_or_repeat_mismatch')
    if any(not r['blocks_retry'] for r in enforcement if r['injected'] != 'none'):
        defects.append('historical_failure_gate_allows_readiness')
    if any(not r['passed'] for r in controlled): defects.append('controlled_vector_reference_failure')
    # Other engineering defects are appended by the caller, after all obligations finish.
    return defects
