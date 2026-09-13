"""Prospective 14ai structural witnessing; historical primitives are unchanged."""
from dataclasses import dataclass
import math
import numpy as np
from . import root_partition_determinism as old
from .verification_repair import VerificationError, find_verified_envelope

@dataclass(frozen=True)
class OwnerWitness:
    left_limit: float
    before: float
    canonical: float
    after: float
    right_limit: float
    owners_before: tuple[int, ...]
    owners_at: tuple[int, ...]
    owners_after: tuple[int, ...]


def owners(row):
    high = float(np.max(row))
    return () if high == 0 else tuple(i for i, value in enumerate(row) if high-float(value) <= 1e-12)


def interior_probes(root, left, right):
    if not 0 <= left < root < right <= 1:
        raise VerificationError('coincident_or_unordered_boundary')
    before_max = float(np.nextafter(root, -math.inf))
    after_min = float(np.nextafter(root, math.inf))
    if before_max <= left or after_min >= right:
        raise VerificationError('no_interior_float')
    step = min(1e-7, (root-left)/4, (right-root)/4)
    before, after = root-step, root+step
    if not left < before < root: before = before_max
    if not root < after < right: after = after_min
    return before, after


def localize(function, switch):
    """Raw transition evidence only: no provisional record is accepted here."""
    lower, upper = old._switch_witnesses(function, switch)
    pair = switch.crossing_pairs[0]
    before = old._sign(old._pair(function, pair, lower))
    after = old._sign(old._pair(function, pair, upper))
    if before == 0 or after == 0 or before == after:
        raise VerificationError('switch_sign_transition_invalid')
    last = old._last_true(lower, upper, lambda t: old._sign(old._pair(function,pair,t)) == before)
    first = old._first_true(lower, upper, lambda t: old._sign(old._pair(function,pair,t)) == after)
    start, end = float(np.nextafter(last, math.inf)), float(np.nextafter(first, -math.inf))
    if start > end: start = end = None
    else:
        for point in (start, end, old._float((old._bits(start)+old._bits(end))//2)):
            if old._pair(function,pair,point) != 0:
                raise VerificationError('nonzero_inside_switch_equality_interval')
    return last, start, end, first


def certify_in_region(function, switch, transition, left, right):
    last, start, end, canonical = transition
    before, after = interior_probes(canonical,left,right)
    row_before, row_at, row_after = (old._row(function,t) for t in (before,canonical,after))
    observed = owners(row_before), owners(row_at), owners(row_after)
    if observed != (switch.owners_before,switch.owners_at,switch.owners_after):
        raise VerificationError('partition_owner_semantics_changed')
    for pair in switch.crossing_pairs:
        a,b = old._sign(old._pair(function,pair,before)),old._sign(old._pair(function,pair,after))
        if a == 0 or b == 0 or a == b:
            raise VerificationError('partition_pair_order_not_reversed')
    accepted = old.CertifiedRootTransition(switch.location,last,start,end,canonical,
        *observed,switch.crossing_pairs)
    return accepted, OwnerWitness(left,before,canonical,after,right,*observed)


def certify_partitions(function, envelope, onsets):
    provisional = [localize(function,s) for s in envelope.switches]
    fixed = {0.,1.,*(x.canonical for x in onsets)}
    tie_points = set()
    for tie in envelope.tie_intervals:
        for boundary in (tie.start,tie.end):
            if boundary is not None: tie_points.update((boundary.outside,boundary.inside))
    fixed.update(tie_points)
    canonical = [x[3] for x in provisional]
    if len(set(canonical)) != len(canonical):
        raise VerificationError('ambiguous_transition_order')
    all_points = fixed | set(canonical)
    accepted=[]; witnesses=[]
    for s,t in zip(envelope.switches,provisional,strict=True):
        root=t[3]
        if root in fixed: raise VerificationError('coincident_or_unordered_boundary')
        left=max(x for x in all_points if x<root);right=min(x for x in all_points if x>root)
        record,witness=certify_in_region(function,s,t,left,right)
        accepted.append(record); witnesses.append(witness)
    # Exact deduplication only; every distinct adjacent-float tie endpoint survives.
    return tuple(sorted(all_points)),tuple(accepted),tuple(witnesses)


def canonical_geometry(candidate, origin, receiver, defenders, function):
    from . import production_verification as pv
    onsets=() if candidate=='isotropic' else old.deterministic_directional_onsets(origin,receiver,defenders)
    raw=tuple(x.raw_scalar_result for x in onsets)
    envelope=find_verified_envelope(function,extra_partitions=raw)
    pv.certified_partitions(function,envelope,raw)
    partitions,switches,witnesses=certify_partitions(function,envelope,onsets)
    return onsets,envelope,partitions,switches,witnesses


def evaluate(candidate, origin, receiver, defenders, *, historical_failure=False, record=lambda **kw: None):
    """Compose frozen estimator and verifier with new certified owner partitions."""
    import warnings
    from dataclasses import asdict
    from .occlusion_fields import CarrierOriginField, points, validate_geometry
    from .integration_review import values_for_components
    from .verification_audit import controlled_vector
    from .representation_retry import independent_maximum
    from .micro_interval_verifier import point_interval_distance
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        record(stage='geometry')
        b,ds,_=validate_geometry(origin,defenders);end=points(receiver,one=True)
        field=CarrierOriginField(candidate)
        if math.dist(b,end)<=1e-9:
            raise VerificationError('diagnostic_degenerate_edge_unavailable')
        record(stage='joint_simpson')
        count,estimates,change=controlled_vector(lambda n:values_for_components(field,b,end,ds,n))
        if count is None: raise VerificationError('controlled_nonconvergence')
        def function(t): return field.individual_values(b,ds,b[None,:]+t[:,None]*(end-b)[None,:])
        record(stage='envelope')
        record(stage='owner_certification')
        onsets,envelope,partitions,switches,witnesses=canonical_geometry(candidate,b,end,ds,function)
        record(stage='partition_construction')
        interval=independent_maximum(function,partitions,onsets,historical_failure,record)
        if point_interval_distance(estimates['maximum'],interval)>1e-6:
            raise VerificationError('joint_maximum_reference_error')
        record(stage='accepted')
        return dict(intervals=count,estimates=estimates,change=change,partitions=partitions,
            switches=switches,onsets=onsets,envelope=envelope,witnesses=witnesses,
            maximum_interval=asdict(interval))
