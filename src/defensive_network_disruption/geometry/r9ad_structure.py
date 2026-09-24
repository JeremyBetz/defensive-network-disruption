"""Explicit structural composition: R9T localization remains unchanged."""
import math
import time
from dataclasses import asdict
from .r9t_transition import (old, pv, owner, FieldAuthority, PairAuthority,
    check_deadline, VerificationError, localize, check_order)
from .r9ad_envelope import find_verified_envelope

def canonical_geometry(candidate,origin,receiver,defenders,function,*,deadline=None,sink=lambda **kw:None):
    deadline=min(deadline if deadline is not None else math.inf,time.monotonic()+600)
    onsets=() if candidate=='isotropic' else old.deterministic_directional_onsets(origin,receiver,defenders)
    raw=tuple(x.raw_scalar_result for x in onsets)
    fields=tuple(FieldAuthority.from_geometry(candidate,origin,receiver,d) for d in defenders)
    envelope=find_verified_envelope(function,extra_partitions=raw,fields=fields,deadline=deadline,sink=sink)
    sink(kind='raw_structures',value=dict(onsets=[asdict(x) for x in onsets],
                                        envelope=asdict(envelope)))
    pv.certified_partitions(function,envelope,raw)
    fixed={0.,1.,*(x.canonical for x in onsets)}
    for tie in envelope.tie_intervals:
        for boundary in (tie.start,tie.end):
            if boundary:fixed.update((boundary.outside,boundary.inside))
    fields=tuple(FieldAuthority.from_geometry(candidate,origin,receiver,d) for d in defenders)
    proposals=[]
    locations=[s.location for s in envelope.switches]
    for index,switch in enumerate(envelope.switches):
        check_deadline(deadline)
        if switch.location in fixed:raise VerificationError('coincident_or_unordered_boundary')
        lower,upper=old._switch_witnesses(function,switch)
        original_witnesses=(lower,upper)
        left=max(x for x in fixed if x<switch.location);right=min(x for x in fixed if x>switch.location)
        if index:left=max(left,(locations[index-1]+switch.location)/2)
        if index+1<len(locations):right=min(right,(switch.location+locations[index+1])/2)
        lower=max(lower,left);upper=min(upper,right)
        sink(kind='candidate_region',value=dict(raw_proposal=asdict(switch),
             original_witnesses=original_witnesses,constrained_region=(lower,upper),
             structural_neighbors=(left,right)))
        if not lower<switch.location<upper:raise VerificationError('candidate_region_order')
        transitions=[]
        for pair in switch.crossing_pairs:
            # Use the same production pair inspected by this mathematical authority.
            from dataclasses import replace
            paired=replace(switch,crossing_pairs=(pair,))
            authority=PairAuthority(fields[pair[0]],fields[pair[1]])
            sink(kind='pair_authority',value=authority)
            result=localize(function,paired,authority,
                            lower,upper,deadline=deadline,structural_region=(left,right),sink=sink)
            transitions.append(result)
        if all(x is None for x in transitions):continue
        if any(x is None for x in transitions) or len({x[3] for x in transitions})!=1:
            raise VerificationError('multiway_transition_unresolved')
        proposals.append((switch,transitions[0]))
    canonical=[x[1][3] for x in proposals]
    check_order(canonical)
    all_points=fixed|set(canonical);accepted=[];witnesses=[]
    for switch,transition in proposals:
        root=transition[3]
        if root in fixed:raise VerificationError('coincident_or_unordered_boundary')
        left=max(x for x in all_points if x<root);right=min(x for x in all_points if x>root)
        record,witness=owner.certify_in_region(function,switch,transition,left,right)
        accepted.append(record);witnesses.append(witness)
    return onsets,envelope,tuple(sorted(all_points)),tuple(accepted),tuple(witnesses)
