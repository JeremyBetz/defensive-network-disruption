"""R7 composition of accepted numerical primitives; explicit geometry only."""
from dataclasses import asdict
import itertools
import math
import warnings
import numpy as np
from . import onset_owner_certification as owner
from . import production_verification as pv
from .occlusion_fields import CarrierOriginField, combine, points, validate_geometry
from .representation_study import VerifiedEdge
from .representation_retry import independent_maximum
from .integration_review import values_for_components
from .verification_audit import controlled_vector
from .verification_repair import mapped_signature
from .micro_interval_verifier import point_interval_distance


def evaluate(candidate, origin, receiver, defenders, *, synthetic=False,
             historical_failure=False, record=lambda **kw: None):
    with warnings.catch_warnings():
        warnings.simplefilter('error')
        record(stage='geometry')
        b,ds,_=validate_geometry(origin,defenders); end=points(receiver,one=True)
        field=CarrierOriginField(candidate)
        endpoint=field.individual_values(b,ds,end[None,:])[0]
        union=float(combine(endpoint[None,:],'union')[0]); maximum=float(np.max(endpoint))
        if math.dist(b,end)<=1e-9:
            estimates={**{f'individual_{i+1}':float(x) for i,x in enumerate(endpoint)},'union':union,'maximum':maximum}
            record(stage='accepted')
            return VerifiedEdge(tuple(endpoint),tuple(endpoint),union,maximum,union,maximum,0,0.,0.),dict(estimates=estimates,degenerate=True)
        record(stage='joint_simpson')
        count,estimates,change=controlled_vector(lambda n:values_for_components(field,b,end,ds,n))
        pv.require(count is not None,'controlled_nonconvergence')
        def function(t): return field.individual_values(b,ds,b[None,:]+t[:,None]*(end-b)[None,:])
        record(stage='envelope'); record(stage='owner_certification')
        structure=owner.canonical_geometry(candidate,b,end,ds,function)
        onsets,envelope,partitions,switches,witnesses=structure
        pv.require(structure==owner.canonical_geometry(candidate,b,end,ds,function),'nondeterminism')
        permutations=0;continuity=False
        if synthetic:
            continuity=pv.check_continuity(candidate,b,ds);pv.require(continuity,'continuity')
            identity=tuple(range(len(ds)));signature=mapped_signature(envelope,identity)
            def canonical_signature(items,perm):
                return tuple((x.last_pre_switch,x.exact_zero_start,x.exact_zero_end,x.canonical,
                    tuple(sorted(perm[i] for i in x.owners_before)),tuple(sorted(perm[i] for i in x.owners_at)),
                    tuple(sorted(perm[i] for i in x.owners_after)),
                    tuple(sorted(tuple(sorted((perm[a],perm[c]))) for a,c in x.crossing_pairs))) for x in items)
            for perm in itertools.permutations(identity):
                other=owner.canonical_geometry(candidate,b,end,ds[list(perm)],lambda t,p=perm:function(t)[:,p])
                pv.check_permutation(signature,mapped_signature(other[1],perm))
                pv.require(partitions==other[2] and canonical_signature(switches,identity)==canonical_signature(other[3],perm),'canonical_permutation')
                permutations+=1
        record(stage='partition_construction')
        interval=independent_maximum(function,partitions,onsets,historical_failure,record)
        error=point_interval_distance(estimates['maximum'],interval)
        pv.require(error<=1e-6,'joint_maximum_reference_error')
        record(stage='accepted')
        edge=VerifiedEdge(tuple(map(float,endpoint)),tuple(estimates[f'individual_{i+1}'] for i in range(len(ds))),
            union,maximum,estimates['union'],estimates['maximum'],count,change,error)
        return edge,dict(estimates=estimates,intervals=count,change=change,permutations=permutations,
            partitions=partitions,maximum_interval=asdict(interval),degenerate=False,continuity=continuity,
            deterministic=True,warnings=0,canonical_onsets=[(x.defender_index,x.branch,x.last_pre_branch,x.canonical) for x in onsets],
            canonical_switches=[(x.last_pre_switch,x.exact_zero_start,x.exact_zero_end,x.canonical,
                x.owners_before,x.owners_at,x.owners_after,x.crossing_pairs) for x in switches])


def evaluate_edge(candidate,origin,receiver,defenders,record=lambda **kw:None):
    return evaluate(candidate,origin,receiver,defenders,record=record)[0]
