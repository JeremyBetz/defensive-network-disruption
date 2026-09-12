"""Session 14R2 explicit-geometry adapter; no data, model or acquisition route."""
from dataclasses import asdict
import itertools
import math
import warnings
import numpy as np
from . import production_verification as pv
from .occlusion_fields import CarrierOriginField, combine, points, validate_geometry, simpson_average
from .integration_review import values_for_components
from .verification_audit import controlled_vector
from .verification_repair import find_verified_envelope, mapped_signature
from .root_partition_determinism import deterministic_directional_onsets, deterministic_partitions
from .micro_interval_verifier import bounded_adaptive_maximum, interval_distance, point_interval_distance
from .representation_study import VerifiedEdge


def canonical_geometry(candidate, origin, receiver, defenders, function):
    onsets = () if candidate == 'isotropic' else deterministic_directional_onsets(origin, receiver, defenders)
    raw = tuple(x.raw_scalar_result for x in onsets)
    envelope = find_verified_envelope(function, extra_partitions=raw)
    # Validate inherited enclosure predicates, without using its raw-root partitions.
    pv.certified_partitions(function, envelope, raw)
    partitions, switches = deterministic_partitions(function, envelope, onsets)
    return onsets, envelope, partitions, switches


def independent_maximum(function, partitions, onsets, historical_failure=False, record=lambda **kw: None):
    widths = [b-a for a,b in zip(partitions, partitions[1:])]
    pv.require(widths and all(x > 0 for x in widths), 'partition_order')
    bounded = [w for w in widths if w <= 1e-12/len(widths)]
    record(stage='routing', pieces=len(widths), bounded=len(bounded), quadrature=len(widths)-len(bounded))
    record(stage='strict_piecewise')
    strict = bounded_adaptive_maximum(function, partitions, 1e-13)
    record(stage='repeat_piecewise')
    repeat = bounded_adaptive_maximum(function, partitions, 1e-11)
    pv.require(interval_distance(strict, repeat) <= 1e-10, 'piecewise_repeat')
    record(stage='onset_adaptive')
    unsplit = pv.adaptive_maximum(function, tuple(sorted({0., 1., *(x.canonical for x in onsets)})), 1e-13)
    pv.require(point_interval_distance(unsplit, strict) <= 1e-10, 'piecewise_unsplit')
    record(stage='direct_simpson')
    direct = float(simpson_average(np.max(function(np.linspace(0.,1.,65537,dtype=np.float64)),axis=1)[:,None])[0])
    pv.require(point_interval_distance(direct, strict) <= 1e-9, 'piecewise_direct')
    if historical_failure:
        first,_ = pv.split_simpson(function, partitions, 32768)
        second,_ = pv.split_simpson(function, partitions, 65536)
        pv.require(abs(first-second)<=1e-10 and point_interval_distance(first,strict)<=1e-10 and
                   point_interval_distance(second,strict)<=1e-10, 'split_simpson_agreement')
    return strict


def evaluate(candidate, origin, receiver, defenders, *, synthetic=False, historical_failure=False,
             record=lambda **kw: None):
    """Return unchanged joint estimates, accepted only after independent checks."""
    with warnings.catch_warnings(record=True) as observed_warnings:
        warnings.simplefilter('error')
        record(stage='geometry')
        b, ds, _ = validate_geometry(origin, defenders)
        end = points(receiver, one=True)
        field = CarrierOriginField(candidate)
        endpoint = field.individual_values(b,ds,end[None,:])[0]
        union = float(combine(endpoint[None,:], 'union')[0]); maximum = float(np.max(endpoint))
        if math.dist(b,end)<=1e-9:
            values = {**{f'individual_{i+1}':float(x) for i,x in enumerate(endpoint)},'union':union,'maximum':maximum}
            return VerifiedEdge(tuple(endpoint),tuple(endpoint),union,maximum,union,maximum,0,0.,0.), dict(estimates=values,degenerate=True)
        record(stage='joint_simpson')
        count, estimates, change = controlled_vector(lambda n: values_for_components(field,b,end,ds,n))
        pv.require(count is not None, 'controlled_nonconvergence')
        def function(t): return field.individual_values(b,ds,b[None,:]+t[:,None]*(end-b)[None,:])
        record(stage='envelope')
        onsets,envelope,partitions,switches = canonical_geometry(candidate,b,end,ds,function)
        repeated=canonical_geometry(candidate,b,end,ds,function)
        deterministic=(onsets,envelope,partitions,switches)==repeated
        pv.require(deterministic, 'nondeterminism')
        permutations=0; continuity=False
        if synthetic:
            continuity=pv.check_continuity(candidate,b,ds)
            pv.require(continuity, 'continuity')
            identity=tuple(range(len(ds))); signature=mapped_signature(envelope,identity)
            for perm in itertools.permutations(identity):
                other=canonical_geometry(candidate,b,end,ds[list(perm)],lambda t,p=perm:function(t)[:,p])
                pv.check_permutation(signature,mapped_signature(other[1],perm))
                pv.require(partitions==other[2], 'canonical_partition_permutation')
                permutations+=1
        interval=independent_maximum(function,partitions,onsets,historical_failure,record)
        error=point_interval_distance(estimates['maximum'],interval)
        pv.require(error<=1e-6,'joint_maximum_reference_error')
        record(stage='accepted')
        edge=VerifiedEdge(tuple(map(float,endpoint)),tuple(estimates[f'individual_{i+1}'] for i in range(len(ds))),
            union,maximum,estimates['union'],estimates['maximum'],count,change,error)
        return edge,dict(estimates=estimates,intervals=count,change=change,permutations=permutations,
            partitions=partitions,maximum_interval=asdict(interval),degenerate=False,
            continuity=continuity,deterministic=deterministic,warnings=len(observed_warnings),
            canonical_onsets=[(x.defender_index,x.branch,x.last_pre_branch,x.canonical) for x in onsets],
            canonical_switches=[(x.last_pre_switch,x.exact_zero_start,x.exact_zero_end,x.canonical,
                x.owners_before,x.owners_at,x.owners_after,x.crossing_pairs) for x in switches])


def evaluate_edge(candidate,origin,receiver,defenders,record=lambda **kw:None):
    return evaluate(candidate,origin,receiver,defenders,record=record)[0]
