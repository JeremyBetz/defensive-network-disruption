"""Finite terminal-suffix convention; no empirical identifiers, I/O or integration.

Mathematical crossing authority, rounded observations and canonical structure are
separate immutable records. Historical R9R localization is reused unchanged.
"""
from dataclasses import asdict, dataclass, replace
from fractions import Fraction as F
import math
import sys
import time

from . import r9r_localization as inherited
from .r9r_localization import (old, owner, pv, FieldAuthority, PairAuthority,
    Bounds, Topology, classify, isolate, sign, check_deadline, MAX_FLOATS,
    VerificationError, find_verified_envelope)


@dataclass(frozen=True)
class CrossingAuthority:
    topology: Topology
    enclosure: tuple[F, F]
    lower: float
    upper: float
    left_sign: int
    right_sign: int
    structural_region: tuple[float, float]

    def __post_init__(self):
        t=self.topology;a,b=self.enclosure
        if (type(t)is not Topology or t.classification!='B' or not t.complete
            or len(t.root_intervals)!=1 or not t.cells
            or not all(type(x)is F for x in (a,b))
            or not all(type(x)is float and math.isfinite(x) for x in (self.lower,self.upper))
            or not 0<=self.lower<float(a)<=float(b)<self.upper<=1):
            raise VerificationError('transition_mathematical_authority')
        if (len(self.structural_region)!=2 or any(type(x)is not float or not math.isfinite(x) for x in self.structural_region)
            or not 0<=self.structural_region[0]<=self.lower<self.upper<=self.structural_region[1]<=1):
            raise VerificationError('transition_structural_region')
        lo,hi=map(F.from_float,(self.lower,self.upper))
        if t.cells[0].left!=lo or t.cells[-1].right!=hi or any(x.right!=y.left for x,y in zip(t.cells,t.cells[1:])):
            raise VerificationError('transition_mathematical_coverage')
        if any(c.kind not in ('signed','crossing','endpoint') for c in t.cells):
            raise VerificationError('transition_unresolved_topology')
        x,y=t.root_intervals[0]
        if not x<=a<=b<=y:raise VerificationError('transition_enclosure')
        direction=self.right_sign
        if type(direction)is not int or direction not in (-1,1) or type(self.left_sign)is not int or self.left_sign!=-direction:
            raise VerificationError('transition_mathematical_witnesses')
        covering=[c for c in t.cells if c.left<=b and c.right>=a]
        if not covering or any(c.derivative is None or sign(c.derivative)!=direction for c in covering):
            raise VerificationError('transition_derivative_authority')

    @property
    def before(self):return self.left_sign
    @property
    def after(self):return self.right_sign


@dataclass(frozen=True)
class Probe:
    ordinal: int
    window: int
    key: int
    difference: float

    @property
    def sign(self):return old._sign(self.difference)


@dataclass(frozen=True)
class TransitionEvidence:
    authority: CrossingAuthority
    windows: tuple[tuple[int,int],...]
    probes: tuple[Probe,...]
    cache: tuple[tuple[int,int],...]
    transition: inherited.Transition
    suffix_length: int
    canonical_index: int

    def legacy(self):return self.transition.legacy()


def canonicalize(authority,windows,probes,cache):
    """Pure resolution of complete stored observations. Never calls a field."""
    if type(authority)is not CrossingAuthority:raise VerificationError('transition_authority_type')
    # Revalidate even records constructed by deserialization/object manipulation.
    authority.__post_init__()
    if not windows or len(probes)>MAX_FLOATS:raise VerificationError('binary64_inspection_limit')
    a,b=authority.enclosure;outer=(old._bits(authority.lower),old._bits(authority.upper))
    expected_window=(max(outer[0],old._bits(float(a))-16),min(outer[1],old._bits(float(b))+16))
    seen=set();expected=[];previous=None;by_key={p.key:p for p in probes}
    for index,window in enumerate(windows):
        if type(window)is not tuple or len(window)!=2 or any(type(x)is not int for x in window):raise VerificationError('transition_window_schema')
        lo,hi=window
        if window!=expected_window or not outer[0]<=lo<=hi<=outer[1] or hi-lo+1>MAX_FLOATS:raise VerificationError('transition_window')
        if previous is not None:
            if previous[0] not in by_key or previous[1] not in by_key:raise VerificationError('transition_incomplete')
            if by_key[previous[0]].sign==authority.before and by_key[previous[1]].sign==authority.after:
                raise VerificationError('transition_unnecessary_widening')
        expected.extend((index,k) for k in range(lo,hi+1) if k not in seen)
        seen.update(range(lo,hi+1));width=max(16,hi-lo+1)
        expected_window=(max(outer[0],lo-width),min(outer[1],hi+width));previous=window
    if len(expected)!=len(probes) or len(by_key)!=len(probes):raise VerificationError('transition_incomplete')
    for i,(probe,(window,key)) in enumerate(zip(probes,expected)):
        if (type(probe)is not Probe or probe.ordinal!=i or probe.window!=window or probe.key!=key
            or type(probe.difference)is not float or not math.isfinite(probe.difference)):
            raise VerificationError('transition_probe')
    actual=tuple(sorted((p.key,p.sign) for p in probes))
    if cache!=actual:raise VerificationError('transition_cache')
    lo,hi=windows[-1];signs=dict(actual)
    if signs[lo]!=authority.before or signs[hi]!=authority.after:raise VerificationError('transition_direction')
    j=hi
    while j>lo and signs[j-1]==authority.after:j-=1
    suffix=hi-j+1
    if suffix<2:raise VerificationError('transition_suffix_too_short')
    before=[k for k in range(lo,j) if signs[k]==authority.before]
    if not before or j==lo:raise VerificationError('transition_pre_witness')
    last=before[-1]
    canonical,successor=old._float(j),old._float(j+1)
    if not authority.structural_region[0]<canonical<successor<authority.structural_region[1]:
        raise VerificationError('transition_structural_confirmation')
    gap=list(range(last+1,j))
    zeros=gap if gap and all(signs[k]==0 for k in gap) else []
    transition=inherited.Transition(old._float(last),old._float(zeros[0]) if zeros else None,
        old._float(zeros[-1]) if zeros else None,canonical,len(probes))
    return TransitionEvidence(authority,tuple(windows),tuple(probes),actual,transition,suffix,j-lo)


def validate_evidence(value):
    if type(value)is not TransitionEvidence:raise VerificationError('transition_evidence_type')
    rebuilt=canonicalize(value.authority,value.windows,value.probes,value.cache)
    if asdict(rebuilt)!=asdict(value):raise VerificationError('forged_transition_evidence')
    return rebuilt


def inspect_production(function,pair,authority,*,deadline,sink=lambda **kw:None):
    """Same R9R window/cache-miss route; only final canonicalization changes."""
    authority.__post_init__();a,b=authority.enclosure
    lo=max(old._bits(authority.lower),old._bits(float(a))-16)
    hi=min(old._bits(authority.upper),old._bits(float(b))+16)
    cache={};probes=[];windows=[]
    try:
        while True:
            check_deadline(deadline)
            if hi-lo+1>MAX_FLOATS:raise VerificationError('binary64_inspection_limit')
            windows.append((lo,hi))
            for key in range(lo,hi+1):
                if key not in cache:
                    check_deadline(deadline)
                    sink(kind='probe_attempt',value=dict(ordinal=len(probes),window=len(windows)-1,key=key))
                    value=old._pair(function,pair,old._float(key))
                    if not math.isfinite(value):raise VerificationError('transition_nonfinite')
                    probe=Probe(len(probes),len(windows)-1,key,float(value))
                    sink(kind='probe_completed',value=asdict(probe))
                    probes.append(probe);cache[key]=probe.sign
            if cache[lo]==authority.before and cache[hi]==authority.after:break
            width=max(16,hi-lo+1)
            new_lo=max(old._bits(authority.lower),lo-width);new_hi=min(old._bits(authority.upper),hi+width)
            if (new_lo,new_hi)==(lo,hi):raise VerificationError('binary64_bracket_unavailable')
            lo,hi=new_lo,new_hi
        result=canonicalize(authority,tuple(windows),tuple(probes),tuple(sorted(cache.items())))
        sink(kind='transition_evidence',value=asdict(result))
        return result
    finally:
        original=sys.exc_info()[1]
        try:sink(kind='inspection_work',value=dict(floats_inspected=len(cache),windows=windows,cache=sorted(cache.items())))
        except BaseException:
            if original is None:raise
            # Preserve the first failure if a final diagnostic write also fails.



def localize(function,switch,authority,lower,upper,*,deadline,structural_region=None,sink=lambda **kw:None):
    topology=classify(authority,F.from_float(lower),F.from_float(upper),deadline=deadline)
    sink(kind='topology',value=topology)
    if topology.classification=='A':return None
    if topology.classification!='B':raise VerificationError('localization_'+topology.classification)
    a,b=isolate(authority,*topology.root_intervals[0],deadline=deadline)
    sink(kind='isolated_root',value=(a,b))
    left,_=authority.bounds(F.from_float(lower),F.from_float(lower))
    right,_=authority.bounds(F.from_float(upper),F.from_float(upper))
    crossing=CrossingAuthority(topology,(a,b),lower,upper,sign(left),sign(right),structural_region or (lower,upper))
    result=inspect_production(function,switch.crossing_pairs[0],crossing,deadline=deadline,sink=sink)
    sink(kind='transition',value=result.transition)
    return result.legacy()


def check_order(canonical):
    if any(not math.isfinite(x) for x in canonical) or any(x>=y for x,y in zip(canonical,canonical[1:])):
        raise VerificationError('ambiguous_transition_order')


def canonical_geometry(candidate,origin,receiver,defenders,function,*,deadline=None,sink=lambda **kw:None):
    deadline=min(deadline if deadline is not None else math.inf,time.monotonic()+600)
    onsets=() if candidate=='isotropic' else old.deterministic_directional_onsets(origin,receiver,defenders)
    raw=tuple(x.raw_scalar_result for x in onsets)
    envelope=find_verified_envelope(function,extra_partitions=raw)
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
