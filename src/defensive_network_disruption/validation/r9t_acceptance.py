"""Frozen provider-free R9T controls and actual-adapter preservation replay."""
from dataclasses import asdict, is_dataclass, replace
from fractions import Fraction as F
import math
from pathlib import Path
import time
import numpy as np
from ..geometry import r9t_transition as r
from ..geometry import r9t_adapter as adapter
from ..geometry import r9r_adapter as prior
from ..geometry import r9k_comparator as baseline
from ..geometry.r9q_diagnosis import deadline_limit
from .r9r_acceptance import historical_cases, Polynomial
from .r9j_evidence import digest

FIXTURES=('clean_np','clean_pn','isolated_zero','plateau','reentry','contradiction',
 'oscillation','insufficient','rounded_plateau','asymmetric','onset_boundary','tie_boundary',
 'two_crossings','duplicates','no_root')
EXPECTED=('4','4','5','6','6','6','7','blocked','6','6','blocked','blocked','two','tie','no_switch')
SEQUENCES=('NNNNPPPPP','PPPPNNNNN','NNNNZPPPP','NNNZZZPPP','NNZPNZPPP','NNNNPNPPP',
 'NPNPNPNPP','NPNPNPNNP','NNZZZZPPP','NNPPZNPPP','NNNNNNNPP','NNNNNNNPP')
NEGATIVES=('wrong_direction','incomplete_trace','out_of_bounds','unresolved_coincidence',
 'root_order','collapsed_roots','fabricated_plateau','corrupt_witness','nonfinite_probe','exhausted_limits')


def primitive(x):
    if type(x)is F:return {'numerator_hex':format(x.numerator,'x'),'denominator_hex':format(x.denominator,'x')}
    if type(x)is float:
        if not math.isfinite(x):raise ValueError('nonfinite_evidence')
        return {'float':x,'hex':x.hex()}
    if type(x) in (str,int,bool) or x is None:return x
    if isinstance(x,(list,tuple)):return [primitive(y) for y in x]
    if type(x)is dict:return {str(k):primitive(v) for k,v in x.items()}
    if is_dataclass(x):return primitive(asdict(x))
    raise TypeError('unsupported_evidence')


class Linear:
    def __init__(self,root,direction=1):self.root,self.direction=F(root),direction
    def bounds(self,a,b):return (r.Bounds(F(a),F(b))-self.root)*self.direction,r.Bounds.point(self.direction)
    def equal_on(self,a,b):return False


class TwoRoots:
    def __init__(self,a,b):self.a,self.b=F(a),F(b)
    def bounds(self,a,b):
        t=r.Bounds(F(a),F(b));return (t-self.a)*(t-self.b),2*t-self.a-self.b
    def equal_on(self,a,b):return False


def fixture(sequence='NNNNPPPPP',*,offset=-4,authority=None,structural=None):
    mid=r.old._bits(.5);keys=tuple(range(mid+offset,mid+offset+9));points=tuple(r.old._float(k) for k in keys)
    root=F.from_float(points[4]);direction=1 if sequence[-1]=='P' else -1
    math_authority=authority or Linear(root,direction)
    lo,hi=points[0],points[-1]
    topology=r.classify(math_authority,F.from_float(lo),F.from_float(hi),deadline=time.monotonic()+10)
    left,_=math_authority.bounds(F.from_float(lo),F.from_float(lo));right,_=math_authority.bounds(F.from_float(hi),F.from_float(hi))
    crossing=r.CrossingAuthority(topology,(root,root),lo,hi,r.sign(left),r.sign(right),
        structural or (r.old._float(keys[0]-2),r.old._float(keys[-1]+2)))
    probes=tuple(r.Probe(i,0,key,{'N':-1.,'P':1.,'Z':0.}[s]) for i,(key,s) in enumerate(zip(keys,sequence)))
    return crossing,((keys[0],keys[-1]),),probes,tuple((p.key,p.sign) for p in probes)


def trace_controls(sink=lambda label,value:digest(value)):
    rows=[]
    for index,(name,expected) in enumerate(zip(FIXTURES,EXPECTED)):
        detail=dict(fixture=name,expected=expected);observed='unavailable'
        family='engineering'
        try:
            if name=='duplicates':
                family='field'
                x=r.FieldAuthority.from_geometry('expanding',(0.,0.),(20.,0.),(5.,1.))
                y=r.FieldAuthority.from_geometry('expanding',(0.,0.),(20.,0.),(5.,-1.))
                result=r.classify(r.PairAuthority(x,y),F(1,2),F(3,4),deadline=time.monotonic()+10)
                detail['topology']=primitive(result);observed='tie' if result.classification=='C' else result.classification
            elif name=='no_root':
                result=r.classify(Polynomial('same'),F(0),F(1),deadline=time.monotonic()+10)
                detail['topology']=primitive(result);observed='no_switch' if result.classification=='A' else result.classification
            elif name=='two_crossings':
                mid=r.old._bits(.5);roots=[F.from_float(r.old._float(mid+d)) for d in (-8,8)]
                authority=TwoRoots(*roots);results=[]
                for offset,sequence in ((-12,'PPPPZNNNN'),(4,'NNNNZPPPP')):
                    evidence=r.canonicalize(*fixture(sequence,offset=offset,authority=authority));results.append(evidence)
                r.check_order([v.transition.first_post for v in results])
                detail['results']=primitive(results);observed='two' if all(v.canonical_index==5 for v in results) else 'wrong'
            else:
                args=list(fixture(SEQUENCES[index]))
                if name in ('onset_boundary','tie_boundary'):
                    # The exact structural endpoint is the confirmation successor;
                    # restrict the inspection upper witness to it as well.
                    args=list(fixture('NNNNNNNPP',structural=(r.old._float(args[2][0].key-2),r.old._float(args[2][-1].key))))
                if name in ('rounded_plateau','asymmetric'):
                    probes=[]
                    for p in args[2]:
                        t=r.old._float(p.key)
                        value=((1+t)-1)-.5 if name=='rounded_plateau' else ((1+t)-1)-t+(t-.5)*2.**-40
                        probes.append(replace(p,difference=value))
                    args[2]=tuple(probes);args[3]=tuple((p.key,p.sign) for p in probes)
                    signs=''.join({-1:'N',0:'Z',1:'P'}[p.sign] for p in probes)
                    if signs!=SEQUENCES[index]:raise AssertionError('arithmetic_fixture_changed')
                detail['input']=primitive(args)
                result=r.canonicalize(*args);detail['result']=primitive(result);observed=str(result.canonical_index)
        except r.VerificationError as error:
            detail['rejection']=str(error);observed='blocked'
        detail['observed']=observed
        h=sink('trace_'+name,detail)
        rows.append(dict(fixture=name,family=family,expected=expected,observed=observed,
            passed=observed==expected,evidence_sha256=h))
    return rows


def negative_controls(sink=lambda label,value:digest(value)):
    rows=[];args=fixture('NNZPNZPPP')
    def altered_probes(probes):return r.canonicalize(args[0],args[1],tuple(probes),tuple((p.key,p.sign) for p in probes))
    def reject(name,action):
        try:action()
        except (ValueError,TimeoutError,TypeError) as error:blocked=True;reason=type(error).__name__
        else:blocked=False;reason='unexpected_acceptance'
        detail=dict(blocked=blocked,reason=reason)
        rows.append(dict(fixture=name,**detail,evidence_sha256=sink('negative_'+name,detail)))
    reject('wrong_direction',lambda:r.canonicalize(replace(args[0],left_sign=args[0].right_sign,right_sign=args[0].left_sign),*args[1:]))
    reject('incomplete_trace',lambda:altered_probes(args[2][:-1]))
    def outside():
        # Valid outer witnesses, but no representable post confirmation interior.
        short=fixture('NNNNNNNPP');c,w,p,k=short
        r.canonicalize(replace(c,structural_region=(c.lower,c.upper)),w,p,k)
    reject('out_of_bounds',outside)
    reject('unresolved_coincidence',lambda:r.owner.interior_probes(.5,.5,1.))
    reject('root_order',lambda:r.check_order([.6,.4]))
    reject('collapsed_roots',lambda:r.check_order([.5,.5]))
    result=r.canonicalize(*args)
    reject('fabricated_plateau',lambda:r.validate_evidence(replace(result,transition=replace(result.transition,zero_start=.5,zero_end=.5))))
    reject('corrupt_witness',lambda:r.validate_evidence(replace(result,transition=replace(result.transition,last_pre=.4))))
    reject('nonfinite_probe',lambda:altered_probes((replace(args[2][0],difference=float('nan')),*args[2][1:])))
    reject('exhausted_limits',lambda:r.inspect_production(lambda t:np.column_stack((t-.5,t*0)),(0,1),args[0],deadline=0))
    return rows


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
        with deadline_limit(min(deadline,time.monotonic()+600)):base_edge,base=baseline.evaluate(*args,**kwargs)
        if old!=base:raise ValueError('inherited_authority_disagreement')
        expected=case['historical_vector'];new=None;reason='accepted'
        try:
            with deadline_limit(min(deadline,time.monotonic()+600)):
                new_edge,new=adapter.evaluate(*args,**kwargs,record=record,localization_sink=lambda **kw:localizations.append(primitive(kw)))
        except (r.VerificationError,r.pv.GateFailure,TimeoutError) as error:
            reason=type(error).__name__
        structural=('partitions','canonical_onsets','canonical_switches')
        structure=new is not None and all(new.get(k)==old.get(k) for k in structural)
        production=new is not None and new['intervals']==old['intervals']==expected['intervals'] and tuple(new['estimates'])==tuple(old['estimates'])==tuple(expected['estimates'])
        if production:
            for key,value in new['estimates'].items():
                for previous in (old['estimates'][key],expected['estimates'][key]):
                    production &= math.isfinite(value) and abs(value-previous)<=64*np.finfo(float).eps*max(1.,abs(value),abs(previous))
        verification=new is not None and new['maximum_interval']==old['maximum_interval'] and new['certificate_evidence']==old['certificate_evidence']
        valid=structure and production and verification
        detail=dict(fixture=label,component_order={'old':list(old['estimates']),'expected':list(expected['estimates']),'new':None if new is None else list(new['estimates'])},old=primitive(old),baseline=primitive(base),new=primitive(new),expected=primitive(expected),localizations=localizations,reason=reason,stage=stage,
                    seconds=time.monotonic()-start)
        h=sink('historical_'+str(index),detail)
        rows.append(dict(fixture=label,candidate=case['candidate'],status='passed' if valid else 'blocked',
            components=len(expected['estimates']),permutations=new['permutations'] if new is not None else 0,
            structure_exact=bool(structure),production_preserved=bool(production),verification_preserved=bool(verification),
            reason=reason if not valid else 'accepted',evidence_sha256=h))
    return rows
