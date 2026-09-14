"""Internal 14ao observational onset-only adaptive diagnostics; no repair route."""
from __future__ import annotations
from contextlib import contextmanager
import math
import signal
import time
import warnings
import numpy as np
from scipy.integrate import quad
from .diagnostic_serialization import canonical_bytes, project_evidence
from ..validation.retained_evidence_review import atomic, sha, strict_json, digest

TOLERANCES=(1e-13,5e-14,2e-14,1e-14,5e-15,2e-15)
LIMIT=1000
GATE=1e-10

class AuthorityError(RuntimeError):pass
class MissingAuthority(RuntimeError):pass
class DiagnosticTimeout(TimeoutError):pass

class Budget:
    def __init__(self,total=3600.,level=600.):
        self.started=time.monotonic();self.deadline=self.started+total;self.level=level
    @contextmanager
    def operation(self):
        duration=min(self.level,self.deadline-time.monotonic())
        if duration<=0:raise DiagnosticTimeout('global_budget')
        old=signal.getsignal(signal.SIGALRM)
        if signal.getitimer(signal.ITIMER_REAL)[0]:raise RuntimeError('nested_timer')
        def expire(*_):raise DiagnosticTimeout('level_or_global_budget')
        signal.signal(signal.SIGALRM,expire);signal.setitimer(signal.ITIMER_REAL,duration)
        try:yield
        finally:signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,old)


def guard(state,edge,candidate):
    if type(state) is not int or type(edge) is not int or (state,edge,candidate)!=(4,7,'constant_width'):
        raise PermissionError('single_retained_edge_only')


def scalar(function,t):
    return float(np.max(function(np.array([t],dtype=np.float64))[0]))


def diagnostic_piece(function,a,b,tolerance,*,limit=LIMIT):
    """Preserve quad arithmetic; full_output only exposes initialized metadata."""
    trace=[];start=time.perf_counter();failure=None;observed=[];returned=None
    def callback(t):
        value=scalar(function,t)
        if not math.isfinite(value):raise ValueError('nonfinite_integrand')
        trace.append((float(t),value));return value
    try:
        with warnings.catch_warnings(record=True) as observed:
            warnings.simplefilter('always')
            returned=quad(callback,a,b,epsabs=tolerance,epsrel=tolerance,limit=limit,full_output=1)
    except BaseException as exc:
        failure=exc
    result=dict(a=float(a),b=float(b),tolerance=tolerance,limit=limit,seconds=time.perf_counter()-start,
        callback_count=len(trace),trace_sha256=digest(trace),trace=trace,
        warnings=[dict(category=type(w.message).__name__,message=str(w.message)) for w in observed],
        exception=None if failure is None else type(failure).__name__,message=None,
        normal=False,exhausted=False,estimate=None,reported_error=None,neval=None,last=None,
        alist=[],blist=[],rlist=[],elist=[])
    if returned is not None:
        if len(returned) not in (3,4):raise ValueError('quad_return_schema')
        estimate,error,info=returned[:3];last=int(info['last']);neval=int(info['neval'])
        if not 1<=last<=limit or neval!=len(trace):raise ValueError('quad_counter_mismatch')
        arrays={k:[float(x) for x in info[k][:last]] for k in ('alist','blist','rlist','elist')}
        if not all(math.isfinite(x) for values in arrays.values() for x in values):raise ValueError('nonfinite_metadata')
        if not math.isfinite(estimate) or not math.isfinite(error):raise ValueError('nonfinite_terminal')
        message=str(returned[3]) if len(returned)==4 else None
        result.update(estimate=float(estimate),reported_error=float(error),neval=neval,last=last,
            message=message,normal=message is None and not observed,exhausted=last>=limit,**arrays)
        # Full-output messages represent the warning that the plain route emits.
        if message is not None:result['warnings'].append(dict(category='IntegrationWarning',message=message))
    if failure is not None:
        failure.diagnostic_piece=result
        raise failure
    canonical_bytes(result)
    return result


def run_level(function,partitions,tolerance,budget,sink):
    if not partitions or partitions[0]!=0. or partitions[-1]!=1. or any(b<=a for a,b in zip(partitions,partitions[1:])):
        raise ValueError('partition_order')
    pieces=[];started=time.perf_counter()
    try:
        with budget.operation():
            for i,(a,b) in enumerate(zip(partitions,partitions[1:])):
                sink('piece_started',dict(piece=i))
                try:p=diagnostic_piece(function,a,b,tolerance)
                except BaseException as exc:
                    if hasattr(exc,'diagnostic_piece'):
                        pieces.append(exc.diagnostic_piece);sink('piece',exc.diagnostic_piece)
                    raise
                pieces.append(p);sink('piece',p)
                if not p['normal'] or p['exhausted']:break
    except BaseException as exc:
        exc.level_partial=level_record(pieces,partitions,tolerance,time.perf_counter()-started)
        raise
    return level_record(pieces,partitions,tolerance,time.perf_counter()-started)


def level_record(pieces,partitions,tolerance,seconds):
    complete=len(pieces)==len(partitions)-1 and all(p['normal'] and not p['exhausted'] for p in pieces)
    valid=[p for p in pieces if p['last'] is not None]
    onsets=set(partitions[1:-1]);adjacent=0;adjacent_errors=[]
    for p in valid:
        for a,b,e in zip(p['alist'],p['blist'],p['elist']):
            if a in onsets or b in onsets:adjacent+=1;adjacent_errors.append(e)
    reported=math.fsum(p['reported_error'] for p in valid) if valid else None
    panel_error=math.fsum(e for p in valid for e in p['elist']) if valid else None
    return dict(tolerance=tolerance,complete=complete,normal=complete,
        warnings=any(p['warnings'] for p in pieces),exhausted=any(p['exhausted'] for p in pieces),
        neval=sum(p['callback_count'] for p in pieces),terminal_panels=sum(p['last'] for p in valid),
        subdivisions=sum(p['last']-1 for p in valid),onset_adjacent_panels=adjacent,
        onset_error_fraction=math.fsum(adjacent_errors)/panel_error if panel_error else None,
        estimate=math.fsum(p['estimate'] for p in pieces) if complete else None,
        reported_error=reported,reported_bounds_met=all(p['reported_error']<=max(tolerance,tolerance*abs(p['estimate'])) for p in valid) if valid else None,
        seconds=seconds,trace_sha256=digest([p['trace_sha256'] for p in pieces]),
        pieces_attempted=len(pieces),pieces_required=len(partitions)-1)


def compare(level,previous,reference,bounds,anchor):
    if not level['complete']:return dict(reference_within_gate=None,piecewise_within_gate=None,anchor_match=None,
        delta_exceeds_gate=None,reference_error_decreased=None,extra_work=None,trace_changed=None,
        reference_error=None,relative_error=None,delta=None)
    value=level['estimate'];error=abs(value-reference)
    delta=None if previous is None else abs(value-previous['estimate'])
    changed=None if previous is None else level['trace_sha256']!=previous['trace_sha256']
    work=None if previous is None else changed and (level['neval']>previous['neval'] or level['subdivisions']>previous['subdivisions'])
    return dict(reference_within_gate=error<=GATE,
        piecewise_within_gate=max(0.,bounds[0]-value,value-bounds[1])<=GATE,
        anchor_match=abs(value-anchor)<=GATE if previous is None else None,
        delta_exceeds_gate=None if delta is None else delta>GATE,
        reference_error_decreased=None if previous is None else error<abs(previous['estimate']-reference),
        extra_work=work,trace_changed=changed,reference_error=error,
        relative_error=error/abs(reference) if abs(reference)>64*np.finfo(np.float64).eps else None,delta=delta)


def classify(levels,reference,*,authority_invalid=False,execution_invalid=False):
    if authority_invalid:return 'D',3,'retained_authority_invalidated'
    if execution_invalid:return 'H',4,'execution_failure'
    if len(levels)!=6 or any(not r['complete'] or r['warnings'] or r['exhausted'] for r in levels):
        return 'H',4,'incomplete_or_warning_limited'
    if tuple(r['tolerance'] for r in levels)!=TOLERANCES:raise ValueError('sequence_changed')
    values=[r['estimate'] for r in levels];errors=[abs(x-reference) for x in values]
    changes=[abs(b-a) for a,b in zip(values,values[1:])]
    extra=[b['trace_sha256']!=a['trace_sha256'] and (b['neval']>a['neval'] or b['subdivisions']>a['subdivisions']) for a,b in zip(levels,levels[1:])]
    late=all(changes[i]>GATE and errors[i+1]<errors[i] and extra[i] for i in (3,4))
    recovered=errors[0]>GATE and errors[-1]<=GATE and errors[-1]<errors[0] and any(d>GATE and w for d,w in zip(changes,extra))
    if late or recovered:return 'A',1,'observed_added_refinement_moves_estimate_toward_reference'
    stable=max(values[-3:])-min(values[-3:])<=GATE/10
    if stable and all(e>GATE for e in errors[-3:]) and all(extra[-2:]):return 'B',4,'qualified_stabilized_disagreement'
    return 'H',4,'insufficient_or_mixed_refinement_evidence'


def synthetic_controls():
    from .production_verification import adaptive_maximum
    outcomes=[]
    for name,f in [('constant',lambda t:np.ones_like(t)),('polynomial',lambda t:t**3),('kink',lambda t:abs(t-.371))]:
        plain_trace=[]
        def function(t):plain_trace.extend(t.tolist());return f(t)[:,None]
        historical=adaptive_maximum(function,(0.,.25,1.),1e-13)
        expected_trace=list(plain_trace);plain_trace.clear()
        plain=[]
        for a,b in ((0.,.25),(.25,1.)):
            plain.append(quad(lambda t:scalar(function,t),a,b,epsabs=1e-13,epsrel=1e-13,limit=1000))
        diagnostic=[diagnostic_piece(function,a,b,1e-13) for a,b in ((0.,.25),(.25,1.))]
        observed=[t for p in diagnostic for t,_ in p['trace']]
        passed=historical==math.fsum(p['estimate'] for p in diagnostic) and observed==expected_trace and all(p['normal'] and (p['estimate'],p['reported_error'])==q for p,q in zip(diagnostic,plain))
        if not passed:raise RuntimeError('observational_control_failed')
        outcomes.append(dict(fixture=name,passed=passed))
    warning=diagnostic_piece(lambda t:abs(t-.371)[:,None],0.,1.,1e-13,limit=1)
    if warning['normal'] or not warning['warnings']:raise RuntimeError('warning_control_failed')
    outcomes.append(dict(fixture='insufficient_limit',passed=True))
    return outcomes
