"""Prospective bounded localization; mathematical and binary64 evidence are distinct.

No I/O, empirical identifiers, integration, tolerance overrides, or certificates.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction as F
import math
import time

import numpy as np

from . import onset_owner_certification as owner
from . import root_partition_determinism as old
from . import production_verification as pv
from .r9j_reference import Bounds, down, up, rational, sqrt_bounds, smooth
from .r9q_diagnosis import square, gaussian, sign
from .verification_repair import VerificationError, find_verified_envelope

MAX_DEPTH = 80
MAX_LEAVES = 65536
MAX_FLOATS = 65536


@dataclass(frozen=True)
class FieldAuthority:
    candidate: str
    q: F
    dot: F
    cross2: F
    vv: F
    rho: Bounds
    alpha: Bounds
    beta2: Bounds
    tangent: F

    def __post_init__(self):
        if self.candidate not in ('isotropic','expanding','constant_width') or any(type(x)is not F for x in (self.q,self.dot,self.cross2,self.vv,self.tangent)):
            raise VerificationError('field_authority_types')
        if self.q<=F.from_float(1e-9)**2 or self.vv<0 or self.cross2<0 or self.cross2!=self.q*self.vv-self.dot*self.dot:
            raise VerificationError('field_authority_coefficients')
        rho=sqrt_bounds(self.q)
        if self.rho!=rho or self.alpha!=Bounds.point(self.dot)/rho or self.beta2!=Bounds.point(self.cross2/self.q) or self.tangent!=F.from_float(math.tan(math.radians(10.))):
            raise VerificationError('field_authority_consistency')

    @classmethod
    def from_geometry(cls, candidate, origin, receiver, defender):
        if candidate not in ('isotropic', 'expanding', 'constant_width'):
            raise VerificationError('field_authority_candidate')
        b,r,d = [tuple(rational(float(x)) for x in p) for p in (origin,receiver,defender)]
        if any(len(p)!=2 for p in (b,r,d)):
            raise VerificationError('field_authority_shape')
        u=tuple(y-x for x,y in zip(b,d));v=tuple(y-x for x,y in zip(b,r))
        q=sum(x*x for x in u);dot=sum(x*y for x,y in zip(u,v))
        cross=u[0]*v[1]-u[1]*v[0];vv=sum(x*x for x in v)
        if q<=F.from_float(1e-9)**2:
            raise VerificationError('field_authority_origin')
        rho=sqrt_bounds(q)
        return cls(candidate,q,dot,cross*cross,vv,rho,Bounds.point(dot)/rho,
                   Bounds.point(cross*cross/q),F.from_float(math.tan(math.radians(10.))))

    @property
    def identity(self):
        return ((self.candidate,self.q,self.dot,self.vv) if self.candidate=='isotropic'
                else (self.candidate,self.q,self.dot,self.cross2,self.tangent))

    def bounds(self,a,b):
        t=Bounds(F(a),F(b))
        if self.candidate=='isotropic':
            z=(square(t)*self.vv-2*self.dot*t+self.q)*F(1,8)
            # A squared distance is nonnegative even if dependency widens its bound.
            z=Bounds(max(F(0),z.lo),max(F(0),z.hi))
            val=gaussian(z);derivative=val*(Bounds.point(self.dot)-self.vv*t)*F(1,4)
            return val,derivative
        ell=self.alpha*t-self.rho
        gate=Bounds(down(smooth(ell.lo)),up(smooth(ell.hi)))
        width=(2+Bounds(max(F(0),ell.lo),max(F(0),ell.hi))*self.tangent
               if self.candidate=='expanding' else Bounds.point(2))
        val_exp=gaussian(self.beta2*square(t)/(width*width)*F(1,2))
        val=gate*val_exp
        derivative=None
        if ell.hi<=0:
            derivative=Bounds.point(0)
        elif ell.lo>=0 and (ell.hi<=1 or ell.lo>=1):
            gp=(6*ell*(Bounds.point(1)-ell)*self.alpha if ell.hi<=1 else Bounds.point(0))
            wp=self.alpha*self.tangent if self.candidate=='expanding' else Bounds.point(0)
            zp=self.beta2*t*(width-t*wp)/(width*width*width)
            derivative=val_exp*(gp-gate*zp)
        return val,derivative


@dataclass(frozen=True)
class PairAuthority:
    first: FieldAuthority
    second: FieldAuthority

    @property
    def identical(self): return self.first.identity==self.second.identity

    def bounds(self,a,b):
        x,dx=self.first.bounds(a,b);y,dy=self.second.bounds(a,b)
        return x-y,None if dx is None or dy is None else dx-dy

    def equal_on(self,a,b):
        if self.identical:return True
        x,_=self.first.bounds(a,b);y,_=self.second.bounds(a,b)
        return x.lo==x.hi==y.lo==y.hi==0


@dataclass(frozen=True)
class Cell:
    left: F
    right: F
    depth: int
    kind: str
    difference: Bounds
    derivative: Bounds | None


@dataclass(frozen=True)
class Topology:
    classification: str
    cells: tuple[Cell,...]
    root_intervals: tuple[tuple[F,F],...]
    boundary_roots: tuple[F,...]
    subdivisions: int
    max_depth: int
    complete: bool


def check_deadline(deadline):
    if time.monotonic()>=deadline:raise TimeoutError('localization_deadline')


def classify(authority,a,b,*,deadline,max_depth=MAX_DEPTH,max_leaves=MAX_LEAVES):
    a,b=F(a),F(b)
    if not 0<=a<b<=1 or not 0<=max_depth<=MAX_DEPTH or not 1<=max_leaves<=MAX_LEAVES:
        raise VerificationError('localization_domain_or_limits')
    pending=[(a,b,0)];cells=[];roots=[];points=set();splits=0
    while pending:
        check_deadline(deadline)
        x,y,depth=pending.pop()
        diff,derivative=authority.bounds(x,y)
        if not isinstance(diff,Bounds) or derivative is not None and not isinstance(derivative,Bounds):
            raise VerificationError('localization_bound_type')
        left,_=authority.bounds(x,x);right,_=authority.bounds(y,y)
        left_zero=left.lo==left.hi==0;right_zero=right.lo==right.hi==0
        monotone=derivative is not None and sign(derivative)!=0
        if authority.equal_on(x,y):kind='equal'
        elif sign(diff) or (monotone and sign(left) and sign(left)==sign(right)):kind='signed'
        elif monotone and sign(left)*sign(right)==-1:
            kind='crossing';roots.append((x,y))
        elif monotone and ((left_zero and sign(right)) or (right_zero and sign(left))):
            kind='endpoint';points.add(x if left_zero else y)
        elif depth>=max_depth or len(cells)+len(pending)+1>=max_leaves:
            kind='unresolved'
        else:
            middle=(x+y)/2;splits+=1
            pending.extend(((middle,y,depth+1),(x,middle,depth+1)));continue
        cells.append(Cell(x,y,depth,kind,diff,derivative))
    if cells[0].left!=a or cells[-1].right!=b or any(x.right!=y.left for x,y in zip(cells,cells[1:])):
        raise VerificationError('localization_coverage')
    kinds={c.kind for c in cells};interior=points-{a,b}
    count=len(roots)+len(interior)
    complete='unresolved' not in kinds
    if kinds=={'equal'}:label='C'
    elif complete and kinds<={'signed'}:label='A'
    elif complete and 'equal' not in kinds and count==1 and not (points&{a,b}):label='B'
    elif complete and 'equal' not in kinds and count==0 and points and points<={a,b}:label='D'
    elif count>1:label='F'
    else:label='G'
    # A proved polynomial touch can be supplied by analytic authority; it is not a switch.
    if label=='G' and getattr(authority,'proven_touch',False):label='E'
    roots.extend((x,x) for x in sorted(interior))
    return Topology(label,tuple(cells),tuple(sorted(roots)),tuple(sorted(points)),splits,
                    max(c.depth for c in cells),complete)


def isolate(authority,left,right,*,deadline):
    """Bisect only a certified mathematical crossing, never a rounded predicate."""
    a,b=F(left),F(right)
    for _ in range(MAX_DEPTH):
        check_deadline(deadline)
        if a==b:return a,b
        low=float(a);high=float(b)
        if old._bits(high)-old._bits(low)<=32:return a,b
        m=(a+b)/2;v,_=authority.bounds(m,m)
        if v.lo==v.hi==0:return m,m
        left_value,_=authority.bounds(a,a)
        if not sign(v):
            # Two further exact midpoint subdivisions retain the central cells.
            # A zero-containing midpoint is not an exact-root assertion.
            quarter_left=(a+m)/2;quarter_right=(m+b)/2
            ql,_=authority.bounds(quarter_left,quarter_left)
            qr,_=authority.bounds(quarter_right,quarter_right)
            if sign(ql)*sign(qr)==-1:
                a,b=quarter_left,quarter_right
                continue
            return a,b
        if sign(v)==sign(left_value):a=m
        else:b=m
    return a,b


@dataclass(frozen=True)
class Transition:
    last_pre: float
    zero_start: float | None
    zero_end: float | None
    first_post: float
    floats_inspected: int

    def legacy(self):return self.last_pre,self.zero_start,self.zero_end,self.first_post


def inspect_production(function,pair,a,b,lower,upper,before_sign,after_sign,*,deadline,sink=lambda **kw:None):
    """Inspect every float in a bounded root neighborhood; no sign binary search.

    Mathematical isolation is only neighborhood selection. It is not an enclosure
    for the production operations. Non-monotone observed order remains blocking.
    """
    lo=max(old._bits(lower),old._bits(float(a))-16)
    hi=min(old._bits(upper),old._bits(float(b))+16)
    cache={}
    try:
        while True:
            check_deadline(deadline)
            if hi-lo+1>MAX_FLOATS:raise VerificationError('binary64_inspection_limit')
            for key in range(lo,hi+1):
                if key not in cache:
                    check_deadline(deadline)
                    cache[key]=old._sign(old._pair(function,pair,old._float(key)))
            if cache[lo]==before_sign and cache[hi]==after_sign:break
            width=max(16,hi-lo+1)
            new_lo=max(old._bits(lower),lo-width);new_hi=min(old._bits(upper),hi+width)
            if (new_lo,new_hi)==(lo,hi):raise VerificationError('binary64_bracket_unavailable')
            lo,hi=new_lo,new_hi
        # Explicit ordering, not an assumption about the discrete predicate.
        phase=0;last=None;first=None;zero=[]
        for key in range(lo,hi+1):
            s=cache[key]
            if s==before_sign:
                if phase:raise VerificationError('binary64_nonmonotone_unresolved')
                last=key
            elif s==0:
                if phase==2:raise VerificationError('binary64_nonmonotone_unresolved')
                phase=1;zero.append(key)
            elif s==after_sign:
                phase=2
                if first is None:first=key
            else:raise VerificationError('binary64_sign_invalid')
        if last is None or first is None:raise VerificationError('binary64_transition_unavailable')
        return Transition(old._float(last),old._float(zero[0]) if zero else None,
                          old._float(zero[-1]) if zero else None,old._float(first),len(cache))
    finally:
        sink(kind='inspection_work',value=dict(floats_inspected=len(cache)))


def localize(function,switch,authority,lower,upper,*,deadline,sink=lambda **kw:None):
    topology=classify(authority,F.from_float(lower),F.from_float(upper),deadline=deadline)
    sink(kind='topology',value=topology)
    if topology.classification=='A':return None
    if topology.classification!='B':raise VerificationError('localization_'+topology.classification)
    a,b=topology.root_intervals[0]
    a,b=isolate(authority,a,b,deadline=deadline)
    sink(kind='isolated_root',value=(a,b))
    left,_=authority.bounds(F.from_float(lower),F.from_float(lower))
    right,_=authority.bounds(F.from_float(upper),F.from_float(upper))
    if not sign(left) or sign(left)*sign(right)!=-1:raise VerificationError('mathematical_witness_unavailable')
    transition=inspect_production(function,switch.crossing_pairs[0],a,b,lower,upper,
                                  sign(left),sign(right),deadline=deadline,sink=sink)
    sink(kind='transition',value=transition)
    return transition.legacy()


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
                            lower,upper,deadline=deadline,sink=sink)
            transitions.append(result)
        if all(x is None for x in transitions):continue
        if any(x is None for x in transitions) or len({x[3] for x in transitions})!=1:
            raise VerificationError('multiway_transition_unresolved')
        proposals.append((switch,transitions[0]))
    canonical=[x[1][3] for x in proposals]
    if len(set(canonical))!=len(canonical):raise VerificationError('ambiguous_transition_order')
    all_points=fixed|set(canonical);accepted=[];witnesses=[]
    for switch,transition in proposals:
        root=transition[3]
        if root in fixed:raise VerificationError('coincident_or_unordered_boundary')
        left=max(x for x in all_points if x<root);right=min(x for x in all_points if x>root)
        record,witness=owner.certify_in_region(function,switch,transition,left,right)
        accepted.append(record);witnesses.append(witness)
    return onsets,envelope,tuple(sorted(all_points)),tuple(accepted),tuple(witnesses)
