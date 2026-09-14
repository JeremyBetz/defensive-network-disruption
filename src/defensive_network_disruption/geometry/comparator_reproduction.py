"""14am observers and diagnostic records; historical numerical code is unchanged."""
from __future__ import annotations

from collections import Counter
from contextlib import contextmanager
import hashlib
import math
from pathlib import Path
import signal
import sys
import time

import numpy as np

from . import r7_representation as r8
from . import representation_retry as verifier
from . import onset_owner_certification as owner
from . import production_verification as production
from . import verification_audit as vectors
from . import integration_review as integration
from . import micro_interval_verifier as residual
from .comparator_diagnosis import DiagnosticTimeout, maximum_simpson
from .diagnostic_serialization import project_evidence

LADDER = (256, 512, 1024, 2048, 4096, 8192, 16384)


def witness_record(item):
    return dict(left_limit=item.left_limit, before=item.before, canonical=item.canonical,
                after=item.after, right_limit=item.right_limit,
                owners_before=item.owners_before, owners_at=item.owners_at,
                owners_after=item.owners_after)


def structure_record(result):
    onsets, envelope, partitions, switches, witnesses = result
    return project_evidence(dict(onsets=onsets, envelope=envelope, partitions=partitions,
                                 switches=switches, witnesses=[witness_record(x) for x in witnesses]))


class Budget:
    def __init__(self, seconds=3600.0, operation=600.0):
        self.started = time.monotonic()
        self.deadline = self.started + seconds
        self.operation = operation

    @contextmanager
    def limit(self):
        remaining = self.deadline-time.monotonic()
        if remaining <= 0:
            raise DiagnosticTimeout('global_budget')
        previous = signal.getsignal(signal.SIGALRM)
        previous_timer = signal.getitimer(signal.ITIMER_REAL)
        if previous_timer[0] != 0:
            raise RuntimeError('nested_alarm_unsupported')
        def expire(*_):
            raise DiagnosticTimeout('operation_or_global_budget')
        signal.signal(signal.SIGALRM, expire)
        signal.setitimer(signal.ITIMER_REAL, min(remaining, self.operation))
        try:
            yield
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous)


class Observer:
    """Observe function frames without replacing any function or gate."""
    def __init__(self, sink):
        self.sink = sink
        self.saved = {}
        self.samples = []
        self.gates = []
        self.calls = Counter()
        self.wall = Counter()
        self.cpu = Counter()
        self.starts = {}
        self.quad = []
        self.codes = {
            vectors.controlled_vector.__code__: 'controlled_vector',
            integration.values_for_components.__code__: 'vector',
            owner.canonical_geometry.__code__: 'structure',
            residual.bounded_adaptive_maximum.__code__: 'bounded',
            production.adaptive_maximum.__code__: 'onset_adaptive',
            production.require.__code__: 'require',
            verifier.independent_maximum.__code__: 'independent_maximum',
            production.quad.__code__: 'quad',
        }

    def profile(self, frame, event, arg):
        name = self.codes.get(frame.f_code)
        if name is None:
            return
        key = id(frame)
        if event == 'call':
            self.starts[key] = time.perf_counter(), time.process_time()
            self.calls[name] += 1
            if name == 'require' and frame.f_locals.get('reason') == 'piecewise_unsplit':
                parent = frame.f_back
                if parent.f_code is not verifier.independent_maximum.__code__:
                    raise RuntimeError('wrong_gate_caller')
                data = project_evidence({k: parent.f_locals[k] for k in ('strict','repeat','unsplit','partitions')})
                data['condition'] = bool(frame.f_locals['condition'])
                data['reason'] = 'piecewise_unsplit'
                self.gates.append(data)
                self.sink('actual_gate_inputs', data)
        elif event == 'return':
            start = self.starts.pop(key, (time.perf_counter(), time.process_time()))
            self.wall[name] += time.perf_counter()-start[0]
            self.cpu[name] += time.process_time()-start[1]
            if arg is None:
                return
            if name == 'vector':
                item = dict(intervals=frame.f_locals['intervals'], estimates=arg)
                self.samples.append(item)
                self.sink('joint_vector', item)
            elif name == 'controlled_vector':
                self.saved[name] = arg
                self.sink(name, dict(intervals=arg[0], estimates=arg[1], change=arg[2]))
            elif name == 'structure':
                self.saved[name] = arg
                self.sink(name, structure_record(arg))
            elif name == 'bounded':
                label = 'strict' if frame.f_locals['tolerance'] == 1e-13 else 'repeat'
                self.saved[label] = arg
                self.sink(label, project_evidence(arg))
            elif name == 'onset_adaptive':
                self.saved[name] = arg
                self.sink(name, dict(estimate=arg))
            elif name == 'quad':
                item = {k: frame.f_locals[k] for k in ('a','b','epsabs','epsrel','limit')}
                item.update(estimate=arg[0], reported_error=arg[1])
                self.quad.append(project_evidence(item))

    @contextmanager
    def observing(self):
        old = sys.getprofile()
        if old is not None:
            raise RuntimeError('existing_profile_hook')
        sys.setprofile(self.profile)
        try:
            yield
        finally:
            sys.setprofile(old)


def reproduce(origin, receiver, defenders, sink, budget):
    observer = Observer(sink)
    stage = 'geometry'
    durations = []
    stage_start = time.perf_counter()
    stage_cpu = time.process_time()
    def record(**detail):
        nonlocal stage, stage_start, stage_cpu
        durations.append(dict(stage=stage, wall_seconds=time.perf_counter()-stage_start,
                              cpu_seconds=time.process_time()-stage_cpu))
        stage = detail['stage']
        sink('numerical_stage', detail)
        # Reset the per-operation alarm but retain the global deadline.
        remaining = budget.deadline-time.monotonic()
        if remaining <= 0:
            raise DiagnosticTimeout('global_budget')
        signal.setitimer(signal.ITIMER_REAL, min(budget.operation, remaining))
        stage_start, stage_cpu = time.perf_counter(), time.process_time()
    failure = None
    with budget.limit(), observer.observing():
        try:
            r8.evaluate_edge('constant_width', origin, receiver, defenders, record=record)
        except production.GateFailure as error:
            failure = error
    durations.append(dict(stage=stage, wall_seconds=time.perf_counter()-stage_start,
                          cpu_seconds=time.process_time()-stage_cpu))
    if failure is not None:
        import traceback
        sink('original_gate_failure', dict(exception=type(failure).__name__, message=str(failure),
                                          traceback=''.join(traceback.format_exception(failure)), stage=stage))
    reproduced = (type(failure) is production.GateFailure and str(failure) == 'piecewise_unsplit'
                  and stage == 'onset_adaptive' and len(observer.gates) == 1
                  and observer.gates[0]['condition'] is False
                  and observer.calls['controlled_vector'] == 1
                  and observer.calls['structure'] == 2)
    sink('reproduction', dict(reproduced=reproduced, failure=None if failure is None else str(failure),
                             stages=durations, calls=dict(observer.calls),
                             inclusive_wall_seconds=dict(observer.wall),
                             inclusive_cpu_seconds=dict(observer.cpu), adaptive_returns=observer.quad))
    return reproduced, observer, durations


def partition_audit(structure):
    onsets, envelope, partitions, switches, witnesses = structure
    widths = [b-a for a,b in zip(partitions,partitions[1:])]
    ties = [p for t in envelope.tie_intervals for b in (t.start,t.end) if b is not None
            for p in (b.outside,b.inside)]
    checks = dict(domain=partitions[0] == 0.0 and partitions[-1] == 1.0,
                  positive_widths=bool(widths) and all(w > 0 for w in widths),
                  width_sum=bool(abs(math.fsum(widths)-1.0) <= 64*np.finfo(float).eps),
                  onsets_present=all(x.canonical in partitions for x in onsets),
                  switches_present=all(x.canonical in partitions for x in switches),
                  tie_endpoints_preserved=all(x in partitions for x in ties),
                  witnesses_valid=len(switches) == len(witnesses) and all(
                      w.left_limit < w.before < w.canonical < w.after < w.right_limit
                      and (w.owners_before,w.owners_at,w.owners_after) ==
                          (s.owners_before,s.owners_at,s.owners_after)
                      for s,w in zip(switches,witnesses)))
    return dict(checks=checks, passed=all(checks.values()), pieces=len(widths),
                bounded=sum(w <= 1e-12/len(widths) for w in widths),
                onset_count=len(onsets), switch_count=len(switches),
                tie_count=len(envelope.tie_intervals))


def convergence(function, partitions, budget, sink):
    uniform, piecewise = [], []
    for count in LADDER:
        with budget.limit():
            started=time.perf_counter()
            u=maximum_simpson(function,count)
            ur=dict(intervals=count,estimate=u,successive_difference=None if not uniform else u-uniform[-1]['estimate'],seconds=time.perf_counter()-started,evaluations=count+1)
            sink('uniform',ur); uniform.append(ur)
        with budget.limit():
            started=time.perf_counter(); contributions=[]; evaluations=0
            for a,b in zip(partitions,partitions[1:]):
                n=max(2,2*math.ceil(count*(b-a)/2))
                contributions.append(maximum_simpson(function,n,a,b)); evaluations+=n+1
            pr=dict(intervals=count,estimate=math.fsum(contributions),contributions=contributions,
                    seconds=time.perf_counter()-started,evaluations=evaluations)
            pr['successive_difference']=None if not piecewise else pr['estimate']-piecewise[-1]['estimate']
            sink('piecewise',pr); piecewise.append(pr)
    return uniform,piecewise


def reference_eligible(audit, rows):
    return (audit['passed'] and [r['intervals'] for r in rows] == list(LADDER)
            and abs(rows[-1]['estimate']-rows[-2]['estimate']) <= 1e-10)


def synthetic_journal(states):
    records=[]
    def add(action,**payload):
        records.append(dict(action=action,payload=payload))
    add('initialized'); add('access_authorized')
    for i in range(states):
        state=f's{i}'; edges=[f'e{j}' for j in range(10)]; attempt=f'p{i}'
        add('state_discovered',state=state,edges=edges)
        add('projection_attempt',state=state,attempt=attempt)
        add('projection_materialized',attempt=attempt,edges=edges)
        add('state_prepared',state=state)
    return records


def profile_replay(records, budget):
    from ..validation import numerical_failure_publication as publication
    from ..validation import projection_exposure as exposure
    calls=Counter(); prefixes=[]
    def observe(frame,event,arg):
        if event != 'call': return
        if frame.f_code is exposure.replay_exposure.__code__:
            calls['exposure_replay']+=1; prefixes.append(len(frame.f_locals['records']))
        elif frame.f_code is publication.replay.__code__: calls['publication_replay']+=1
    old=sys.getprofile()
    if old is not None: raise RuntimeError('existing_profile_hook')
    started=time.perf_counter(); cpu=time.process_time(); rejection=None
    try:
        with budget.limit():
            sys.setprofile(observe)
            publication.replay(records)
    except Exception as exc:
        if isinstance(exc,DiagnosticTimeout):
            exc.diagnostic_evidence=dict(records=len(records),seconds=time.perf_counter()-started,
                cpu_seconds=time.process_time()-cpu,calls=dict(calls),prefix_visits=sum(prefixes),
                last_prefix=max(prefixes,default=0),completed=False)
            raise
        rejection=type(exc).__name__+':'+str(exc)
    finally:
        sys.setprofile(old)
    return dict(records=len(records),seconds=time.perf_counter()-started,
                cpu_seconds=time.process_time()-cpu,calls=dict(calls),
                prefix_visits=sum(prefixes),last_prefix=max(prefixes,default=0),
                triangular=prefixes == list(range(1,len(prefixes)+1)),
                file_reads=0,hash_operations=0,parse_passes=0,rejection=rejection)
