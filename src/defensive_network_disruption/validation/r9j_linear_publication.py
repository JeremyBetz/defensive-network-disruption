"""Prospective R9J single-pass equivalent of the historical publication replay.

Historical implementations remain unchanged. Numerical diagnostic events never
manufacture lifecycle progress. Only a fully verified stream produces Authority.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import signal
import sys
import time

from . import numerical_failure_publication as old
from . import r9j_evidence as e
from .r5_persistence import CANDIDATES, LifecycleError, canonical_bytes, digest


class Exposure:
    def __init__(self):
        self.states={};self.attempts={};self.pending={};self.opened=set();self.opened_states=set()
        self.edge_started=set();self.edge_completed=set();self.field_started=set();self.field_completed=set()
        self.active_state=self.active_edge=self.active_candidate=None
        self.initialized=self.authorized=False;self.status='active';self.failure_stage=self.exception=None
        self.edge_count=0

    def step(self,action,p):
        if self.status!='active' and action!='failure_evidence':raise LifecycleError('event_after_terminal')
        if action=='initialized':
            if self.initialized:raise LifecycleError('duplicate_initialization')
            self.initialized=True
        elif action=='access_authorized':
            if not self.initialized or self.authorized:raise LifecycleError('invalid_authorization')
            self.authorized=True
        elif action=='state_discovered':
            state=p.get('state');edges=tuple(p.get('edges',()))
            if not self.authorized or not isinstance(state,str) or not state or state in self.states:raise LifecycleError('invalid_state_discovery')
            if not edges or len(set(edges))!=len(edges) or any(not isinstance(x,str) or not x for x in edges):raise LifecycleError('invalid_required_edges')
            self.states[state]={'edges':edges,'edge_set':set(edges),'prepared':False,'evaluation_started':False,'completed':False,'failed':False}
            self.edge_count+=len(edges);self.active_state=state
        elif action=='projection_attempt':
            attempt=p.get('attempt');state=p.get('state')
            if not self.authorized or state not in self.states or not isinstance(attempt,str) or attempt in self.attempts:raise LifecycleError('invalid_projection_attempt')
            if state in self.pending:raise LifecycleError('overlapping_projection_attempt')
            self.attempts[attempt]={'state':state,'status':'pending'};self.pending[state]=attempt;self.active_state=state
        elif action in ('projection_not_materialized','projection_materialized'):
            attempt=p.get('attempt')
            if attempt not in self.attempts or self.attempts[attempt]['status']!='pending':raise LifecycleError('unmatched_projection_receipt')
            item=self.attempts[attempt];state=item['state']
            if action=='projection_not_materialized':item['status']='not_materialized'
            else:
                edges=tuple(p.get('edges',()))
                if edges!=self.states[state]['edges']:raise LifecycleError('projection_edge_mismatch')
                keys={(state,x) for x in edges}
                if self.opened.intersection(keys):raise LifecycleError('duplicate_edge_materialization')
                self.opened.update(keys);self.opened_states.add(state);item['status']='materialized'
            del self.pending[state]
        elif action=='state_prepared':
            state=p.get('state');item=self.states.get(state)
            if item is None or item['prepared'] or not all((state,x) in self.opened for x in item['edges']):raise LifecycleError('invalid_state_preparation')
            item['prepared']=True;self.active_state=state
        elif action=='state_evaluation_started':
            state=p.get('state');item=self.states.get(state)
            if item is None or not item['prepared'] or item['evaluation_started']:raise LifecycleError('invalid_state_evaluation_start')
            item['evaluation_started']=True;self.active_state=state
        elif action in ('field_started','field_completed','edge_completed'):
            state,edge,candidate=p.get('state'),p.get('edge'),p.get('candidate')
            if not isinstance(state,str) or not state or not isinstance(edge,str) or not edge:raise LifecycleError('invalid_edge_identity')
            key=(state,edge);call=(state,edge,candidate);item=self.states.get(state)
            if action=='field_started':
                if item is None or not item['evaluation_started'] or key not in self.opened or edge not in item['edge_set']:raise LifecycleError('field_without_open_edge')
                if candidate not in CANDIDATES or call in self.field_started or self.active_candidate is not None:raise LifecycleError('invalid_field_start')
                if any((state,edge,c) not in self.field_completed for c in CANDIDATES[:CANDIDATES.index(candidate)]):raise LifecycleError('field_order')
                self.field_started.add(call);self.edge_started.add(key)
                self.active_state,self.active_edge,self.active_candidate=state,edge,candidate
            elif action=='field_completed':
                if call not in self.field_started or call in self.field_completed or call!=(self.active_state,self.active_edge,self.active_candidate):raise LifecycleError('invalid_field_completion')
                self.field_completed.add(call);self.active_candidate=None
            else:
                if key not in self.edge_started or key in self.edge_completed or any((state,edge,c) not in self.field_completed for c in CANDIDATES):raise LifecycleError('invalid_edge_completion')
                self.edge_completed.add(key);self.active_edge=self.active_candidate=None
        elif action=='state_completed':
            state=p.get('state');item=self.states.get(state)
            if item is None or not item['evaluation_started'] or item['completed'] or not all((state,x) in self.edge_completed for x in item['edges']):raise LifecycleError('invalid_state_completion')
            item['completed']=True;self.active_state=self.active_edge=self.active_candidate=None
        elif action=='failure':
            self.failure_stage,self.exception=p.get('stage'),p.get('exception')
            if not isinstance(self.failure_stage,str) or not self.failure_stage or not isinstance(self.exception,str) or not self.exception:raise LifecycleError('failure_evidence')
            self.status='failure'
            for field,key in (('active_state','state'),('active_edge','edge'),('active_candidate','candidate')):
                if p.get(key) is not None:setattr(self,field,p[key])
            if self.active_state in self.states:self.states[self.active_state]['failed']=True
        elif action=='blocked':
            if not p.get('stage') or not p.get('reason'):raise LifecycleError('blocked_evidence')
            self.status='blocked';self.failure_stage=p['stage']
        elif action=='success':
            self.status='success';self.active_state=self.active_edge=self.active_candidate=None
        elif action!='failure_evidence':raise LifecycleError('unknown_exposure_event')
        # Preserve historical validation at EVERY lifecycle prefix, without a scan.
        if not self.initialized:raise LifecycleError('journal_not_initialized')
        if not len(self.edge_completed)<=len(self.edge_started)<=len(self.opened)<=self.edge_count:raise LifecycleError('edge_counter_order')
        if action=='success':
            if (not self.states or self.pending or len(self.opened)!=len(self.edge_completed) or
                not all(x['completed'] for x in self.states.values()) or len(self.field_completed)!=3*len(self.edge_completed)):
                raise LifecycleError('incomplete_success')

    def snapshot(self):
        c={'states_discovered':len(self.states),'states_prepared':sum(x['prepared'] for x in self.states.values()),
           'states_evaluation_started':sum(x['evaluation_started'] for x in self.states.values()),
           'states_completed':sum(x['completed'] for x in self.states.values()),'edges_discovered':self.edge_count,
           'edges_opened':len(self.opened),'edges_evaluation_started':len(self.edge_started),'edges_completed':len(self.edge_completed),
           'unresolved_exposed_edges':len(self.opened)-len(self.edge_completed),'projection_attempts':len(self.attempts),
           'unresolved_projection_attempts':len(self.pending),'field_evaluations_started':len(self.field_started),
           'field_evaluations_completed':len(self.field_completed),'state_failures':sum(x['failed'] for x in self.states.values())}
        started=Counter(x[2] for x in self.field_started);completed=Counter(x[2] for x in self.field_completed)
        return {'schema_version':1,'status':self.status,'access_authorized':self.authorized,'counters':c,
                'field_work_by_candidate':{x:{'started':started[x],'completed':completed[x]} for x in CANDIDATES},
                'active':{'state':self.active_state,'edge':self.active_edge,'candidate':self.active_candidate},
                'failure_stage':self.failure_stage,'exception':self.exception,
                'confirmed_zero_exposure':not self.opened and not self.pending}


class Replay:
    def __init__(self):
        self.base=Exposure();self.active=None;self.stage=None;self.diagnostic=False
        self.completed_diagnostics=0;self.terminal=False;self.failed_stage=None;self.base_seen=False;self.failure=None

    def step(self,record):
        action,p=record['action'],record['payload']
        if self.terminal:raise LifecycleError('event_after_terminal')
        if not isinstance(p,dict):raise LifecycleError('payload_type')
        if action in ('diagnostic_started','field_started'):
            ctx=old.context(p)
            item=self.base.states.get(ctx[0])
            if self.active is not None or ctx[:2] not in self.base.opened or item is None or not item['evaluation_started']:raise LifecycleError('work_before_evaluation')
            self.active=ctx;self.stage=None;self.diagnostic=action=='diagnostic_started'
            if self.diagnostic:return
        elif action=='numerical_stage':
            if set(p)!={'state','edge','candidate','detail'}:raise LifecycleError('stage_schema')
            ctx=old.context({k:p[k] for k in ('state','edge','candidate')})
            if self.active!=ctx:raise LifecycleError('stage_context')
            detail=p['detail']
            if not isinstance(detail,dict) or type(detail.get('stage')) is not str or detail['stage'] not in old.STAGES:raise LifecycleError('stage_enum')
            next_stage=detail['stage'];expected={'stage','pieces','bounded','quadrature'} if next_stage=='routing' else {'stage'}
            if set(detail)!=expected:raise LifecycleError('stage_detail_schema')
            if next_stage=='routing':
                if any(type(detail[k]) is not int or detail[k]<0 for k in expected-{'stage'}):raise LifecycleError('routing_type')
                if detail['bounded']+detail['quadrature']!=detail['pieces']:raise LifecycleError('routing_sum')
            if self.stage is None:allowed=('geometry',)
            elif self.stage=='geometry':allowed=('joint_simpson','accepted')
            elif self.stage=='envelope':allowed=('owner_certification','routing')
            else:allowed=(old.STAGES[old.STAGES.index(self.stage)+1],) if self.stage!='accepted' else ()
            if next_stage not in allowed:raise LifecycleError('stage_order')
            self.stage=next_stage;return
        elif action in ('diagnostic_completed','field_completed'):
            if old.context(p)!=self.active or self.stage!='accepted' or self.diagnostic!=(action=='diagnostic_completed'):raise LifecycleError('work_completion')
            if self.diagnostic:
                self.completed_diagnostics+=1;self.active=None;self.stage=None;self.diagnostic=False;return
            self.active=None;self.stage=None
        elif action=='diagnostic_success':
            if p or self.active is not None or self.completed_diagnostics!=1:raise LifecycleError('diagnostic_success')
            self.terminal=True;return
        elif action=='failure':
            if set(p)!={'stage','exception','state','edge','candidate','traceback_sha256'} or type(p['exception']) is not str or not p['exception']:raise LifecycleError('failure_schema')
            if type(p['traceback_sha256']) is not str or len(p['traceback_sha256'])!=64:raise LifecycleError('traceback_authority')
            if self.active is not None:
                if self.stage is None or p['stage']!=self.stage or tuple(p[k] for k in ('state','edge','candidate'))!=self.active:raise LifecycleError('failure_context')
            if p['stage'] not in (*old.STAGES,'startup','preparation','synthetic_acceptance'):raise LifecycleError('failure_stage_enum')
            self.failed_stage=p['stage'];self.terminal=True;self.failure=dict(p)
        elif action=='success':
            if self.active is not None or p:raise LifecycleError('active_success')
            self.terminal=True
        elif action=='blocked':self.terminal=True
        if action not in old.EVENTS:raise LifecycleError('unknown_event')
        self.base.step(action,p);self.base_seen=True

    def result(self):
        if not self.base_seen:raise LifecycleError('missing_initialization')
        snapshot=self.base.snapshot()
        return {'schema_version':2,'snapshot':snapshot,'diagnostic_active':None if self.active is None else list(self.active),
                'numerical_stage':self.stage,'failure_stage':self.failed_stage,'diagnostics_completed':self.completed_diagnostics,
                'terminal':self.terminal,'diagnostic_success':self.terminal and self.completed_diagnostics==1 and snapshot['status']=='active'}


def replay(records):
    engine=Replay()
    for record in records:engine.step(record)
    return engine.result()


_SEAL=object()


@dataclass(frozen=True)
class Authority:
    _bytes: bytes
    _seal: object

    def __post_init__(self):
        if self._seal is not _SEAL:raise TypeError('verified_stream_required')

    def record(self):return json.loads(self._bytes)
    @property
    def legacy(self):return self.record()['legacy']
    @property
    def exposure(self):return self.record()['exposure']
    @property
    def selected_receipt(self):return self.record()['selected_receipt']
    @property
    def records(self):return self.record()['records']
    @property
    def failure(self):return self.record()['failure']

    def progress(self,mode):
        actual=self.legacy
        if actual is None:
            if mode!='pre_access':raise ValueError('empty_empirical_journal')
            return {'schema_version':3,'mode':'pre_access','journal_sha256':None,'snapshot_sha256':None,'snapshot':None,'exposure':self.exposure}
        snapshot=actual['snapshot']['snapshot']
        expected={'empirical_success':'success','empirical_failure':'failure'}.get(mode)
        if mode not in ('empirical_partial','empirical_success','empirical_failure'):raise ValueError('mode')
        if expected is not None and snapshot['status']!=expected:raise ValueError('mode_status')
        if mode=='empirical_partial' and snapshot['status'] not in ('failure','blocked'):raise ValueError('partial_status')
        return {'schema_version':3,'mode':mode,'journal_sha256':actual['journal_sha256'],
                'snapshot_sha256':actual['snapshot_sha256'],'snapshot':snapshot,'exposure':self.exposure}


def review(path,*,expected_sha256=None,expected_head=None,select=None):
    engine=Replay();previous=None;raw_hash=hashlib.sha256();count=0;receipt=None;semantic_error=None
    before=e.safe(path).stat()
    # Chain/encoding errors retain their historical precedence over lifecycle errors.
    with e.safe(path).open('rb') as handle:
        for line in handle:
            raw_hash.update(line)
            if not line.endswith(b'\n'):raise LifecycleError('interrupted_journal_write')
            record=json.loads(line)
            if canonical_bytes(record)!=line:raise LifecycleError('journal_encoding')
            if set(record)!={'schema_version','sequence','previous','action','payload'}:raise LifecycleError('journal_schema')
            if record['schema_version']!=1 or record['sequence']!=count or record['previous']!=previous:raise LifecycleError('journal_chain')
            previous=digest(record);count+=1
            if semantic_error is None:
                try:
                    engine.step(record)
                    if record['action']=='projection_materialized' and select is not None:
                        p=record['payload'];state=engine.base.attempts[p['attempt']]['state']
                        if state==select[0] and select[1] in p['edges']:
                            receipt={'state':state,'edges':list(p['edges']),'sequence':record['sequence'],'record_sha256':previous,'attempt':p['attempt']}
                except Exception as error:semantic_error=error
    raw=raw_hash.hexdigest()
    if expected_sha256 is not None and raw!=expected_sha256:raise LifecycleError('retained_raw_hash')
    if expected_head is not None and previous!=expected_head:raise LifecycleError('journal_truncation_or_reset')
    after=e.safe(path).stat()
    if (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns):
        raise LifecycleError('journal_changed_during_review')
    if semantic_error is not None:raise semantic_error
    if count:
        result=engine.result();snapshot=result['snapshot'];c=snapshot['counters']
    else:
        result=None;snapshot=engine.base.snapshot();c=snapshot['counters']
    exposure=dict(schema_version=2,journal_sha256=previous,states_opened=len(engine.base.opened_states),
        **{k:c[k] for k in ('edges_opened','unresolved_projection_attempts','unresolved_exposed_edges','field_evaluations_started','field_evaluations_completed')},
        field_work_by_candidate=snapshot['field_work_by_candidate'])
    stat=e.safe(path).stat()
    data={'schema_version':1,'legacy':None if result is None else {'journal_sha256':previous,'snapshot_sha256':digest(result),'snapshot':result},
          'lifecycle_snapshot_sha256':digest(snapshot),'exposure':exposure,'selected_receipt':receipt,'failure':engine.failure,
          'records':count,'raw_sha256':raw,'record_visits':count,'source_bytes':stat.st_size,
          'source_path':str(Path(path).absolute()),'source_stat':[stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns]}
    return Authority(canonical_bytes(data),_SEAL)


def validate_numerical_package(folder,authority,*,traceback_path=None):
    if type(authority) is not Authority or authority._seal is not _SEAL:raise TypeError('verified_authority_required')
    record=authority.record();stat=e.safe(record['source_path']).stat()
    if [stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns]!=record['source_stat']:raise LifecycleError('authority_source_changed')
    records={name:e.load(Path(folder)/(name+'.json')) for name in ('qc','manifest','evidence')}
    actual=authority.legacy
    if actual is None:raise LifecycleError('missing_initialization')
    if not actual['snapshot']['terminal']:raise LifecycleError('nonterminal_publication')
    first=records['qc']
    for name,item in records.items():
        if set(item)!={'schema_version','accepted','checks','authority'} or item['schema_version']!=2:raise LifecycleError(name+'_schema')
        if type(item['accepted']) is not bool or not isinstance(item['checks'],dict) or not item['checks'] or any(type(x) is not bool for x in item['checks'].values()):raise LifecycleError('checks_schema')
        if item['authority']!=actual or item!=first:raise LifecycleError('cross_file_mismatch')
    if first['accepted'] and not all(first['checks'].values()):raise LifecycleError('acceptance_gate')
    if first['accepted'] and actual['snapshot']['snapshot']['status'] in ('failure','blocked'):raise LifecycleError('failure_marked_accepted')
    if authority.failure is not None:
        if traceback_path is None or e.sha(traceback_path)!=authority.failure['traceback_sha256']:raise LifecycleError('traceback_missing')
    return actual


def validate_private(folder,authority,mode,*,traceback_path=None):
    """R9E schema compatibility; reuse verified authority, never reread its journal."""
    from .r9e_publication import _validate_success
    folder=Path(folder);actual=authority.progress(mode)
    names=('qc.json','manifest.json','evidence.json','progress_authority.json')
    records={n:e.load(folder/n) for n in names}
    if records['progress_authority.json']!=actual:raise ValueError('private_progress_mismatch')
    base={'schema_version','status','progress_authority'}
    schemas={'qc.json':base|{'stage','exception','scientific_comparisons_available'},'manifest.json':base|{'outputs'},'evidence.json':base}
    for name,keys in schemas.items():
        item=records[name]
        if set(item)!=keys or item['schema_version']!=1:raise ValueError('private_schema')
        if item['progress_authority']!=actual:raise ValueError('private_cross_file')
    status=records['qc.json']['status']
    if status not in ('success','failure','blocked') or any(records[n]['status']!=status for n in ('manifest.json','evidence.json')):raise ValueError('private_status')
    if status=='success':
        _validate_success(actual)
        if records['qc.json']['exception'] is not None or not records['qc.json']['scientific_comparisons_available']:raise ValueError('invalid_private_success')
    elif records['qc.json']['scientific_comparisons_available']:raise ValueError('failure_science_available')
    for name,expected in records['manifest.json']['outputs'].items():
        if Path(name).name!=name or name=='manifest.json' or e.sha(folder/name)!=expected:raise ValueError('private_hash')
    validate_numerical_package(folder/'numerical_publication',authority,traceback_path=traceback_path)
    return actual


def validate_public(directory,private_dir,authority,mode,*,traceback_path=None):
    from .r9a_publication import MANIFEST_MEMBERS
    from .r9e_publication import _validate_success
    directory=Path(directory);private_dir=Path(private_dir)
    m=e.load(directory/'manifest.json');q=e.load(directory/'qc.json')
    keys={'schema_version','status','progress_authority','start','protocol','implementation','environment','outputs','unavailable','private_evidence_sha256','private_manifest_sha256'}
    if set(m)!=keys or m['schema_version']!=1:raise ValueError('manifest_schema')
    if set(m['outputs'])|set(m['unavailable'])!=set(MANIFEST_MEMBERS) or set(m['outputs'])&set(m['unavailable']):raise ValueError('nineteen_file_schema')
    for name,expected in m['outputs'].items():
        if e.sha(directory/name)!=expected:raise ValueError('public_hash')
        if name.endswith('.json'):e.load(directory/name)
    actual=validate_private(private_dir,authority,mode,traceback_path=traceback_path)
    if set(q)!={'schema_version','status','progress_authority','stage','exception','scientific_comparisons_available'}:raise ValueError('qc_schema')
    if q['progress_authority']!=actual or m['progress_authority']!=actual or q['status']!=m['status']:raise ValueError('public_progress_mismatch')
    if m['status']=='success':
        _validate_success(actual)
        if m['unavailable'] or not q['scientific_comparisons_available'] or q['exception'] is not None:raise ValueError('invalid_public_success')
    elif q['scientific_comparisons_available']:raise ValueError('failure_public_science')
    if e.sha(private_dir/'evidence.json')!=m['private_evidence_sha256'] or e.sha(private_dir/'manifest.json')!=m['private_manifest_sha256']:raise ValueError('private_binding')
    return {'schema_version':1,'status':'valid','artifact_count':19,'lifecycle_source':'qc.json.progress_authority',
            'journal_replayed':True,'snapshot_hash_recomputed':True,'states_opened':actual['exposure']['states_opened'],'progress_sha256':digest(actual)}


TRACE=b'synthetic original traceback\n'


def chain(events):
    records=[];head=None
    for action,payload in events:
        record={'schema_version':1,'sequence':len(records),'previous':head,'action':action,'payload':payload}
        records.append(record);head=digest(record)
    return records


def fixture(kind='failure',edges=('0','1')):
    events=[]
    def add(action,**p):events.append((action,p))
    add('initialized')
    if kind=='pre_access':
        add('blocked',stage='startup',reason='synthetic');return chain(events)
    add('access_authorized');add('state_discovered',state='0',edges=list(edges))
    add('projection_attempt',state='0',attempt='attempt_0')
    if kind not in ('uncertain','not_materialized'):
        add('projection_materialized',attempt='attempt_0',edges=list(edges));add('state_prepared',state='0')
    elif kind=='not_materialized':add('projection_not_materialized',attempt='attempt_0')
    if kind in ('uncertain','not_materialized','preparation_failure'):
        add('failure',stage='preparation',exception='RuntimeError',state='0',edge=None,candidate=None,traceback_sha256=hashlib.sha256(TRACE).hexdigest())
        return chain(events)
    if kind=='blocked':
        add('blocked',stage='preparation',reason='synthetic');return chain(events)
    add('state_evaluation_started',state='0')
    candidates=('constant_width',) if kind=='diagnostic' else CANDIDATES
    for c in candidates:
        for edge in edges[:1] if kind=='diagnostic' else edges:
            ctx={'state':'0','edge':edge,'candidate':c}
            add('diagnostic_started' if kind=='diagnostic' else 'field_started',**ctx)
            stages=('geometry','accepted') if kind=='degenerate' else old.STAGES
            for stage in stages:
                detail={'stage':stage}
                if stage=='routing':detail.update(pieces=2,bounded=1,quadrature=1)
                add('numerical_stage',**ctx,detail=detail)
                if kind=='failure' and c=='constant_width' and edge==edges[-1] and stage=='onset_adaptive':
                    add('failure',stage=stage,exception='GateFailure',**ctx,traceback_sha256=hashlib.sha256(TRACE).hexdigest())
                    return chain(events)
                if kind=='partial' and stage=='routing':return chain(events)
            add('diagnostic_completed' if kind=='diagnostic' else 'field_completed',**ctx)
            if c=='constant_width' and kind!='diagnostic':add('edge_completed',state='0',edge=edge)
    if kind=='diagnostic':add('diagnostic_success')
    else:add('state_completed',state='0');add('success')
    return chain(events)


def outcomes(function,records):
    try:return ('value',function(records))
    except Exception as error:return ('error',type(error).__name__,str(error))


def negative_fixtures():
    import copy
    good=fixture('success');bad=[]
    def modify(action,key,value):
        rows=copy.deepcopy(good);item=next(x for x in rows if x['action']==action);item['payload'][key]=value;bad.append(rows)
    modify('field_started','candidate','constant_width')
    modify('numerical_stage','edge','wrong')
    modify('projection_materialized','edges',['1','0'])
    modify('projection_materialized','attempt','missing')
    modify('state_prepared','state','missing')
    modify('state_evaluation_started','state','missing')
    modify('field_completed','candidate','expanding')
    modify('state_completed','state','missing')
    modify('numerical_stage','detail',{'stage':'accepted'})
    modify('numerical_stage','detail',{'stage':'unknown'})
    for detail in ({'stage':'routing','pieces':2,'bounded':2,'quadrature':1},
                   {'stage':'routing','pieces':True,'bounded':0,'quadrature':1}):
        rows=copy.deepcopy(good);next(x for x in rows if x['action']=='numerical_stage' and x['payload']['detail']['stage']=='routing')['payload']['detail']=detail;bad.append(rows)
    bad.append(good[1:]);bad.append(good+[good[0]])
    bad.append(good[:6]+[good[-1]])
    rows=copy.deepcopy(good);rows[0]['action']='unknown';bad.append(rows)
    rows=copy.deepcopy(fixture('failure'));rows[-1]['payload']['stage']='strict_piecewise';bad.append(rows)
    rows=copy.deepcopy(fixture('failure'));rows[-1]['payload']['traceback_sha256']='bad';bad.append(rows)
    rows=copy.deepcopy(good);rows.insert(4,copy.deepcopy(rows[3]));bad.append(rows)
    rows=copy.deepcopy(good);rows.insert(6,copy.deepcopy(rows[4]));bad.append(rows)
    return bad


def write_records(path,records):
    e.put_bytes(path,b''.join(canonical_bytes(x) for x in records))


def persist_control(folder,authority):
    folder=Path(folder);a=authority.legacy;status=a['snapshot']['snapshot']['status']
    mode='empirical_failure' if status=='failure' else 'empirical_success'
    progress=authority.progress(mode);private=folder/'private';public=folder/'public'
    e.put_bytes(folder/'trace.txt',TRACE)
    package=old.package(a,accepted=status=='success',checks={'synthetic_checks':True})
    for name in ('qc','manifest','evidence'):e.put(private/'numerical_publication'/(name+'.json'),package)
    qc=dict(schema_version=1,status=status,progress_authority=progress,stage='onset_adaptive',exception='GateFailure',scientific_comparisons_available=False)
    e.put(private/'qc.json',qc);e.put(private/'evidence.json',{k:qc[k] for k in ('schema_version','status','progress_authority')})
    e.put(private/'progress_authority.json',progress)
    e.put(private/'manifest.json',dict(schema_version=1,status=status,progress_authority=progress,
        outputs={n:e.sha(private/n) for n in ('qc.json','evidence.json','progress_authority.json')}))
    e.put(public/'qc.json',qc)
    from .r9a_publication import MANIFEST_MEMBERS
    e.put(public/'manifest.json',dict(schema_version=1,status=status,progress_authority=progress,start='synthetic',protocol='synthetic',
        implementation='synthetic',environment={},outputs={'qc.json':e.sha(public/'qc.json')},
        unavailable={n:'synthetic_unavailable' for n in MANIFEST_MEMBERS if n!='qc.json'},
        private_evidence_sha256=e.sha(private/'evidence.json'),private_manifest_sha256=e.sha(private/'manifest.json')))
    return private,public,folder/'trace.txt',mode


def acceptance(folder):
    folder=Path(folder);complete=[];prefix=[];negative=[];hashes=[]
    for kind in ('success','failure','blocked','uncertain','not_materialized','preparation_failure','pre_access','diagnostic','partial','degenerate'):
        rows=fixture(kind);complete.append(outcomes(old.replay,rows)==outcomes(replay,rows))
        for end in range(1,len(rows)+1):prefix.append(outcomes(old.replay,rows[:end])==outcomes(replay,rows[:end]))
        path=folder/(kind+'.jsonl');write_records(path,rows)
        authority=review(path);hashes.append(authority.legacy==old.authority(path,digest(rows[-1])))
    for rows in negative_fixtures():
        a,b=outcomes(old.replay,rows),outcomes(replay,rows)
        negative.append(a==b and a[0]=='error')
    # Actual persisted normal failure publication, through both full compatibility routes.
    journal=folder/'failure.jsonl';authority=review(journal)
    private,public,trace,mode=persist_control(folder/'package',authority)
    e.put_bytes(folder/'numerical_traceback.txt',TRACE)
    from . import r9e_publication as historical
    before=historical.validate_public(public,private_dir=private,journal=journal,expected_head=authority.legacy['journal_sha256'],mode=mode)
    after=validate_public(public,private,authority,mode,traceback_path=trace)
    # Historical expects the original traceback next to its source journal.
    flags={'complete_objects_equal':all(complete),'prefixes_equal':all(prefix),'negative_controls':all(negative),
           'persisted_packages':before==after,'legacy_hash_meaning':all(hashes)}
    if not all(flags.values()):raise RuntimeError('linear_equivalence_failed')
    return {'flags':flags,'counts':{'controls':len(complete),'prefixes':len(prefix),'rejections':len(negative)}}


def preparation_fixture(states):
    events=[('initialized',{}),('access_authorized',{})]
    edges=[str(x) for x in range(10)]
    for i in range(states):
        state=str(i);attempt='attempt_'+state
        events.extend((('state_discovered',{'state':state,'edges':edges}),('projection_attempt',{'state':state,'attempt':attempt}),
                       ('projection_materialized',{'attempt':attempt,'edges':edges}),('state_prepared',{'state':state})))
    events.append(('failure',{'stage':'preparation','exception':'RuntimeError','state':str(states-1),'edge':None,'candidate':None,
                              'traceback_sha256':hashlib.sha256(TRACE).hexdigest()}))
    return chain(events)


def work_counts(records):
    base=attempts=prefix_visits=attempt_scans=0
    for record in records:
        if record['action'] in old.EVENTS:
            base+=1
            if record['action']=='projection_attempt':attempts+=1
            prefix_visits+=base
            attempt_scans+=attempts*(attempts-1)//2
    return prefix_visits,attempt_scans


def complexity_probe():
    from .projection_exposure import replay_exposure
    scan_code=next(x for x in replay_exposure.__code__.co_consts if hasattr(x,'co_names') and 'values' not in x.co_names and x.co_name=='<genexpr>' and 'pending' in x.co_consts)
    rows=preparation_fixture(6);count=Counter()
    def observe(frame,event,arg):
        if event=='call' and frame.f_code is replay_exposure.__code__:count['prefix']+=len(frame.f_locals['records'])
        if event=='return' and frame.f_code is scan_code and arg is not None:count['scan']+=1
    previous=sys.getprofile()
    if previous is not None:raise RuntimeError('existing_profile_hook')
    sys.setprofile(observe)
    try:old.replay(rows)
    finally:sys.setprofile(previous)
    prefix,scans=work_counts(rows)
    if (count['prefix'],count['scan'])!=(prefix,scans):raise RuntimeError('complexity_count_mismatch')
    def observe_new(frame,event,arg):
        if event=='call' and frame.f_code is Replay.step.__code__:count['new_visits']+=1
        if event=='call' and frame.f_code is replay_exposure.__code__:count['new_prefix_replays']+=1
    sys.setprofile(observe_new)
    try:replay(rows)
    finally:sys.setprofile(previous)
    return {'flags':{'prefix_replay':count['prefix']==len(rows)*(len(rows)+1)//2 and count['prefix']>len(rows),
                     'attempt_rescan':count['scan']>0,'cubic_preparation_work':count['scan']==scans,
                     'linear_replacement':count['new_visits']==len(rows) and count['new_prefix_replays']==0,'no_runtime_extrapolation':True},
            'counts':{'small_probe_records':len(rows),'measured_prefix_visits':count['prefix'],'predicted_prefix_visits':prefix,
                      'measured_attempt_scans':count['scan'],'predicted_attempt_scans':scans}}


class ReplayTimeout(TimeoutError):pass


def benchmark(nominal,*,old_enabled=True,seconds=60):
    states=nominal//4;rows=preparation_fixture(states);start=time.perf_counter();new=replay(rows);new_seconds=time.perf_counter()-start
    old_seconds='';status='not_run';equal='';reason='earlier_old_timeout' if not old_enabled else ''
    if old_enabled:
        previous=signal.getsignal(signal.SIGALRM)
        if signal.getitimer(signal.ITIMER_REAL)[0]:raise RuntimeError('nested_timer')
        def expire(*_):raise ReplayTimeout('old_benchmark_budget')
        signal.signal(signal.SIGALRM,expire);signal.setitimer(signal.ITIMER_REAL,seconds);start=time.perf_counter()
        try:
            result=old.replay(rows);old_seconds=time.perf_counter()-start;equal=result==new;status='completed'
            if not equal:raise RuntimeError('benchmark_semantic_mismatch')
        except ReplayTimeout:
            old_seconds=time.perf_counter()-start;status='timeout';reason='censored_no_extrapolation'
        finally:
            signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,previous)
    prefix,scans=work_counts(rows)
    return dict(nominal_records=nominal,actual_records=len(rows),states=states,old_status=status,old_seconds=old_seconds,
                new_seconds=new_seconds,equal=equal,prefix_visits=prefix,attempt_scans=scans,reason=reason)


def check_r9i(authority):
    result=authority.record();snapshot=authority.legacy['snapshot']['snapshot'];c=snapshot['counters']
    failure=authority.failure;fields=snapshot['field_work_by_candidate']
    trace=Path(result['source_path']).parent/'numerical_traceback.txt'
    trace_valid=failure is not None and trace.is_file() and e.sha(trace)==failure['traceback_sha256']
    return {'raw_hash':result['raw_sha256']=='6f1c2110d20fc0edbfe9d337f231e829a73df9d90eb47f65f6afb2366054ef3c',
            'chain_valid':result['record_visits']==authority.records==30881,
            'counts_match':all(c[k]==v for k,v in {'states_discovered':7227,'states_prepared':7227,'states_evaluation_started':5,
                'states_completed':4,'edges_opened':72270,'edges_completed':40,'unresolved_exposed_edges':72230,
                'field_evaluations_started':148,'field_evaluations_completed':147,'unresolved_projection_attempts':0}.items())
                and authority.exposure['states_opened']==7227 and fields=={'isotropic':{'started':50,'completed':50},'expanding':{'started':50,'completed':50},'constant_width':{'started':48,'completed':47}},
            'selected_receipt':authority.selected_receipt is not None,
            'failure_match':trace_valid and (failure['state'],failure['edge'],failure['candidate'],failure['stage'],failure['exception'])==('4','7','constant_width','onset_adaptive','GateFailure')}
