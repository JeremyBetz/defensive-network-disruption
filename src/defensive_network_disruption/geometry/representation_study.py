"""Internal explicit-geometry representation summaries; no data or model loading."""
from dataclasses import dataclass
import math
import warnings
import numpy as np
from scipy.stats import rankdata
from .occlusion_fields import CarrierOriginField, combine, validate_geometry, points
from .integration_review import values_for_components, directional_breakpoints
from .verification_audit import controlled_vector
from .verification_repair import find_verified_envelope
from .production_verification import maximum_checks, require, check_repeatability


@dataclass(frozen=True)
class VerifiedEdge:
    receiver_individual: tuple[float, ...]
    segment_individual: tuple[float, ...]
    receiver_union: float
    receiver_maximum: float
    segment_union: float
    segment_maximum: float
    intervals: int
    convergence_change: float
    maximum_reference_error: float


def evaluate_edge(candidate, origin, receiver, defenders):
    """Unchanged joint estimates plus independent certified maximum verification."""
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        b, ds, _ = validate_geometry(origin, defenders)
        end = points(receiver, one=True)
        field = CarrierOriginField(candidate)
        endpoint = field.individual_values(b, ds, end[None, :])[0]
        union = float(combine(endpoint[None, :], 'union')[0])
        maximum = float(np.max(endpoint))
        if math.dist(b, end) <= 1e-9:
            return VerifiedEdge(tuple(map(float, endpoint)), tuple(map(float, endpoint)),
                                union, maximum, union, maximum, 0, 0., 0.)
        count, estimates, change = controlled_vector(
            lambda n: values_for_components(field, b, end, ds, n))
        require(count is not None, 'controlled_nonconvergence')
        def function(t):
            return field.individual_values(b, ds, b[None, :]+t[:, None]*(end-b)[None, :])
        onset = () if candidate == 'isotropic' else directional_breakpoints(b, end, ds)
        envelope = find_verified_envelope(function, extra_partitions=onset)
        repeat = find_verified_envelope(function, extra_partitions=onset)
        check_repeatability(envelope, repeat)
        checked = maximum_checks(function, envelope, onset, False)
        error = abs(estimates['maximum']-checked['piecewise'])
        require(error <= 1e-6, 'joint_maximum_reference_error')
        return VerifiedEdge(tuple(map(float, endpoint)),
            tuple(estimates[f'individual_{i+1}'] for i in range(len(ds))),
            union, maximum, estimates['union'], estimates['maximum'], count, change, error)


def block_ranks(values, descending=True):
    """Block-anchor expected ranks; identity never resolves a tie."""
    values = np.asarray(values, dtype=float)
    require(values.ndim == 1 and len(values) > 0 and np.isfinite(values).all(), 'rank_values')
    order = sorted(range(len(values)), key=lambda i: -values[i] if descending else values[i])
    ranks = np.empty(len(values)); start = 0
    while start < len(order):
        end = start+1
        while end < len(order) and abs(values[order[end]]-values[order[start]]) <= 1e-12:
            end += 1
        ranks[order[start:end]] = (start+1+end)/2
        start = end
    return ranks


def maximum_set(values):
    if not any(values):
        return frozenset()
    ranks = block_ranks(values)
    return frozenset(np.flatnonzero(ranks == min(ranks)).tolist())


def spearman(x, y):
    if len(x) != len(y):
        raise ValueError('correlation_alignment')
    if len(x) < 2:
        return None
    x, y = np.asarray(x, float), np.asarray(y, float)
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError('correlation_nonfinite')
    if np.ptp(x) == 0 or np.ptp(y) == 0:
        return None
    return float(np.corrcoef(rankdata(x, method='average'), rankdata(y, method='average'))[0, 1])


def order_categories(first, second):
    a, b = block_ranks(first), block_ranks(second)
    out = {k: [] for k in ('agreement', 'strict_reversal', 'tie_creation', 'tie_removal', 'both_tied')}
    for i in range(len(a)):
        for j in range(i+1, len(a)):
            x, y = np.sign(a[j]-a[i]), np.sign(b[j]-b[i])
            key = ('both_tied' if x == y == 0 else 'tie_creation' if y == 0 else
                   'tie_removal' if x == 0 else 'agreement' if x == y else 'strict_reversal')
            for k in out:
                out[k].append(float(k == key))
    return out


def discordant_pairs(receiver_distance, segment_distance):
    a = block_ranks(receiver_distance, False); b = block_ranks(segment_distance, False)
    return [(i, j, int(np.sign(a[j]-a[i]))) for i in range(len(a)) for j in range(i+1, len(a))
            if (a[j]-a[i])*(b[j]-b[i]) < 0]


def follows(values, pairs):
    ranks = block_ranks(values)
    out = {k: [] for k in ('endpoint_following', 'corridor_following', 'tied')}
    for i, j, endpoint_order in pairs:
        sign = np.sign(ranks[j]-ranks[i])
        key = 'tied' if sign == 0 else 'endpoint_following' if sign == endpoint_order else 'corridor_following'
        for k in out:
            out[k].append(float(k == key))
    return out


def weighted_summary(values, weights):
    if not values:
        return dict(mean=None, minimum=None, maximum=None, q05=None, q25=None, q50=None, q75=None, q95=None)
    x = np.asarray(values, float); w = np.asarray(weights, float)
    require(np.isfinite(x).all() and np.isfinite(w).all() and (w > 0).all(), 'summary_values')
    order = np.argsort(x, kind='stable'); x=x[order]; w=w[order]
    cumulative = np.cumsum(w)/np.sum(w)
    qs = [float(x[min(int(np.searchsorted(cumulative, q, side='left')), len(x)-1)]) for q in (.05,.25,.5,.75,.95)]
    return dict(mean=float(np.sum(x*w)/np.sum(w)), minimum=float(x[0]), maximum=float(x[-1]),
                **dict(zip(('q05','q25','q50','q75','q95'), qs)))
