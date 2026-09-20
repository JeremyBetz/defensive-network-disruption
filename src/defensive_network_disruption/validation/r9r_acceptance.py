"""Frozen R9R provider-free observations; no retained inputs or access route."""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from fractions import Fraction as F
import importlib.util
import math
from pathlib import Path
import time

import numpy as np

from ..geometry import r9r_localization as repair
from ..geometry import r9r_adapter as adapter
from ..geometry import r9k_comparator as prior
from ..geometry.r9j_reference import Bounds
from ..geometry.r9q_diagnosis import square,deadline_limit
from ..geometry.verification_repair import VerificationError, VerifiedSwitch
from .r9j_evidence import digest

FIXTURES=('same_sign','simple','monotone','nonmonotone_no_root','endpoint','tangent',
          'positive_perturbation','nearby','duplicates','inactive','onset_coincidence',
          'multiway','tiny_unresolved','rounded_sign_reversal')
NEGATIVES=('missing_derivative','ambiguous_roots','malformed_region','inconsistent_onset',
           'false_identity','corrupt_witness','biased_difference','nonfinite','limit')


def primitive(x):
    if type(x) is F:return {'numerator_hex':format(x.numerator,'x'),'denominator_hex':format(x.denominator,'x')}
    if type(x) is float:
        if not math.isfinite(x):raise ValueError('nonfinite_evidence')
        return {'float':x,'hex':x.hex()}
    if type(x) in (str,int,bool) or x is None:return x
    if type(x) in (list,tuple):return [primitive(y) for y in x]
    if type(x) is dict:return {str(k):primitive(v) for k,v in x.items()}
    if type(x) in (repair.Cell,repair.Topology,repair.Transition,Bounds,repair.FieldAuthority,repair.PairAuthority):
        return primitive(asdict(x))
    raise TypeError('unsupported_evidence')


@dataclass(frozen=True)
class Polynomial:
    kind: str
    offset: F = F(0)

    @property
    def proven_touch(self):return self.kind=='square' and self.offset==0

    def bounds(self,a,b):
        t=Bounds(F(a),F(b));u=t-F(1,2)
        if self.kind=='constant':return Bounds.point(self.offset),Bounds.point(0)
        if self.kind=='same':return 1+t,Bounds.point(1)
        if self.kind=='linear':return u,Bounds.point(1)
        if self.kind=='multiway':return 2*u,Bounds.point(2)
        if self.kind=='endpoint':return t,Bounds.point(1)
        if self.kind=='monotone':return u+u*square(u),1+3*square(u)
        if self.kind=='square':return square(u)+self.offset,2*u
        if self.kind=='unknown':return Bounds(F(-1),F(1)),None
        raise ValueError('polynomial_kind')

    def equal_on(self,a,b):return self.kind=='constant' and self.offset==0


def topology_controls(sink=lambda label,value:digest(value)):
    controls=[
        ('same_sign',Polynomial('same'),'A'),('simple',Polynomial('linear'),'B'),
        ('monotone',Polynomial('monotone'),'B'),('nonmonotone_no_root',Polynomial('square',F(1)),'A'),
        ('endpoint',Polynomial('endpoint'),'D'),('tangent',Polynomial('square'),'E'),
        ('positive_perturbation',Polynomial('square',F(1,2**100)),'A'),
        ('nearby',Polynomial('square',-F(1,2**40)),'F'),
    ]
    b=(0.,0.);r=(20.,0.)
    field=lambda d:repair.FieldAuthority.from_geometry('expanding',b,r,d)
    controls += [('duplicates',repair.PairAuthority(field((5.,1.)),field((5.,-1.))),'C'),
                 ('inactive',repair.PairAuthority(field((5.,1.)),field((6.,2.))),'C'),
                 ('onset_coincidence',Polynomial('linear'),'B'),
                 ('multiway',Polynomial('multiway'),'B'),
                 ('tiny_unresolved',Polynomial('unknown'),'G'),
                 ('rounded_sign_reversal',Polynomial('constant',F(1,2**100)),'A')]
    rows=[]
    for name,authority,expected in controls:
        a,b=(F(1,2),F(3,4)) if name=='duplicates' else (F(0),F(1,10)) if name=='inactive' else (F(0),F(1))
        if name=='tiny_unresolved':a,b=F.from_float(math.nextafter(.5,-math.inf)),F.from_float(math.nextafter(.5,math.inf))
        if name=='rounded_sign_reversal':a,b=F(0),F(1,2**51)
        result=repair.classify(authority,a,b,deadline=time.monotonic()+600,max_depth=0 if name=='tiny_unresolved' else 80)
        extra={}
        if name=='onset_coincidence':
            try:repair.owner.interior_probes(.5,.5,1.)
            except VerificationError as error:extra['coincidence_rejected']=str(error)=='coincident_or_unordered_boundary'
            else:extra['coincidence_rejected']=False
        if name=='rounded_sign_reversal':
            points=[0.,2.**-54,2.**-52,2.**-52+2.**-54,2.**-51]
            values=[((1+t)-1)-t+2.**-100 for t in points]
            signs=[1 if x>0 else -1 if x<0 else 0 for x in values]
            extra['rounded_sign_reversals']=sum(x!=y for x,y in zip(signs,signs[1:]))>=2
        detail={'result':primitive(result),'extra':extra}
        h=sink('topology_'+name,detail)
        rows.append(dict(fixture=name,family='field' if name in ('duplicates','inactive') else 'engineering',
                         expected=expected,observed=result.classification,
                         passed=result.classification==expected and all(extra.values()),evidence_sha256=h))
    return rows


def require(value,reason):
    if not value:raise VerificationError(reason)


def negative_controls(sink=lambda label,value:digest(value)):
    rows=[]
    def reject(name,action):
        try:action()
        except (ValueError,VerificationError,TimeoutError) as error:
            blocked=True;reason=type(error).__name__
        else:blocked=False;reason='unexpected_acceptance'
        detail=dict(blocked=blocked,reason=reason)
        rows.append(dict(fixture=name,**detail,evidence_sha256=sink('negative_'+name,detail)))
    def accepted(authority,**kw):
        result=repair.classify(authority,F(0),F(1),deadline=time.monotonic()+600,**kw)
        require(result.classification in ('A','B','C','D'),'unresolved_topology')
    reject('missing_derivative',lambda:accepted(Polynomial('unknown'),max_depth=2))
    reject('ambiguous_roots',lambda:accepted(Polynomial('square',-F(1,2**40))))
    reject('malformed_region',lambda:repair.classify(Polynomial('linear'),F(1),F(0),deadline=time.monotonic()+1))
    reject('inconsistent_onset',lambda:repair.owner.interior_probes(.5,.5,1.))
    reject('false_identity',lambda:require(Polynomial('linear').equal_on(F(0),F(1)),'identity_not_proved'))
    def transition(function,lower=.49999999999999,upper=.50000000000001):
        return repair.inspect_production(function,(0,1),F(1,2),F(1,2),lower,upper,-1,1,
                                         deadline=time.monotonic()+10)
    reject('corrupt_witness',lambda:transition(lambda t:np.column_stack((np.ones_like(t),np.zeros_like(t)))))
    reject('biased_difference',lambda:transition(lambda t:np.column_stack((t-.5+.01,np.zeros_like(t)))))
    reject('nonfinite',lambda:transition(lambda t:np.column_stack((t*float('nan'),t))))
    reject('limit',lambda:repair.classify(Polynomial('linear'),F(0),F(1),deadline=0))
    return rows


def historical_cases(root):
    spec=importlib.util.spec_from_file_location('r9r_authority_cases',Path(root)/'scripts/session_14v_micro_interval_verifier.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return list(module.authority_cases())


def historical_regression(root,sink=lambda label,value:digest(value),*,deadline=math.inf):
    rows=[]
    for index,(label,case) in enumerate(historical_cases(root)):
        start=time.monotonic();stage=None;localizations=[]
        def record(**kw):
            nonlocal stage
            stage=kw['stage']
        kwargs=dict(root=Path(root),authority_context={'alias':'synthetic_r9r'},synthetic=True,
                    historical_failure=case['historical_failure'])
        args=(case['candidate'],case['origin'],case['receiver'],case['defenders'])
        with deadline_limit(min(deadline,time.monotonic()+600)):old_edge,old=prior.evaluate(*args,**kwargs)
        expected=case['historical_vector'];new=None;reason='accepted'
        try:
            with deadline_limit(min(deadline,time.monotonic()+600)):
                new_edge,new=adapter.evaluate(*args,**kwargs,record=record,localization_sink=lambda **kw:localizations.append(primitive(kw)))
        except (VerificationError,pv.GateFailure,TimeoutError) as error:
            reason=str(error) if str(error) in SAFE_FAILURES else type(error).__name__
        structural=('partitions','canonical_onsets','canonical_switches')
        structure=new is not None and all(new.get(k)==old.get(k) for k in structural)
        production=new is not None and new['intervals']==old['intervals']==expected['intervals'] and tuple(new['estimates'])==tuple(old['estimates'])==tuple(expected['estimates'])
        if production:
            for key,value in new['estimates'].items():
                for previous in (old['estimates'][key],expected['estimates'][key]):
                    production &= math.isfinite(value) and abs(value-previous)<=64*np.finfo(float).eps*max(1.,abs(value),abs(previous))
        verification=new is not None and new['maximum_interval']==old['maximum_interval'] and new['certificate_evidence']==old['certificate_evidence']
        valid=structure and production and verification
        detail=dict(fixture=label,component_order={'old':list(old['estimates']),'expected':list(expected['estimates']),'new':None if new is None else list(new['estimates'])},old=primitive(old),new=primitive(new),expected=primitive(expected),localizations=localizations,reason=reason,stage=stage,
                    seconds=time.monotonic()-start)
        h=sink('historical_'+str(index),detail)
        rows.append(dict(fixture=label,candidate=case['candidate'],status='passed' if valid else 'blocked',
            components=len(expected['estimates']),permutations=new['permutations'] if new is not None else 0,
            structure_exact=bool(structure),production_preserved=bool(production),verification_preserved=bool(verification),
            reason=reason if not valid else 'accepted',evidence_sha256=h))
    return rows


from ..geometry import production_verification as pv
SAFE_FAILURES=frozenset(('binary64_nonmonotone_unresolved','binary64_inspection_limit',
    'binary64_bracket_unavailable','binary64_transition_unavailable','candidate_region_order',
    'localization_A','localization_C','localization_D','localization_E','localization_F','localization_G',
    'mathematical_witness_unavailable','multiway_transition_unresolved','partition_owner_semantics_changed',
    'partition_pair_order_not_reversed','coincident_or_unordered_boundary','no_interior_float',
    'localization_deadline','ambiguous_transition_order'))
