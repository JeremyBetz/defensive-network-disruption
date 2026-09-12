"""Internal R5 durable receipts and processing adapter; no data or numerical routes."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import traceback
import warnings
import copy

from .state_lifecycle import LifecycleProgress, LifecycleError, canonical_bytes, snapshot_digest, validate_snapshot
from .launch_enforcement import GovernedLauncher, LaunchError, sha256_file
from .r3_launch import strict_prerequisite

CANDIDATES = ('isotropic', 'expanding', 'constant_width')
MODES = ('pre_access', 'empirical_partial', 'empirical_failure', 'empirical_success')


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def safe(path):
    path = Path(path)
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise PermissionError('symlink_rejected')
    return path


def durable_write(path, value):
    """Create once; persist file and directory before returning."""
    path = safe(path); path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name('.' + path.name + '.pending')
    if path.exists():
        raise FileExistsError('immutable_record_exists')
    with temp.open('xb') as handle:
        handle.write(canonical_bytes(value)); handle.flush(); os.fsync(handle.fileno())
    # link provides no-overwrite publication, including concurrent writers.
    os.link(temp, path); temp.unlink()
    fd = os.open(path.parent, os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)


class Journal:
    """Exclusive, incrementally synchronized journal. An incomplete append blocks."""
    def __init__(self, path):
        self.path = safe(path); self.path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = self.path.open('xb')
        self.count = 0; self.previous = None; self.failed = False
        self.handle.flush(); os.fsync(self.handle.fileno())

    def append(self, action, **payload):
        if self.failed: raise LifecycleError('journal_failed')
        record = dict(schema_version=1, sequence=self.count, previous=self.previous,
                      action=action, payload=payload)
        try:
            self.handle.write(canonical_bytes(record))
            self.handle.flush(); os.fsync(self.handle.fileno())
        except BaseException:
            self.failed = True
            raise
        self.previous = digest(record); self.count += 1
        return self.previous

    def close(self):
        self.handle.close()


def read_journal(path, *, expected_head=None):
    records=[]; previous=None
    with safe(path).open('rb') as handle:
        for line in handle:
            if not line.endswith(b'\n'): raise LifecycleError('interrupted_journal_write')
            record=json.loads(line)
            if canonical_bytes(record) != line: raise LifecycleError('journal_encoding')
            if set(record) != {'schema_version','sequence','previous','action','payload'}:
                raise LifecycleError('journal_schema')
            if record['schema_version'] != 1 or record['sequence'] != len(records) or record['previous'] != previous:
                raise LifecycleError('journal_chain')
            previous=digest(record); records.append(record)
    if expected_head is not None and previous != expected_head:
        raise LifecycleError('journal_truncation_or_reset')
    return records, previous


def receipts(records):
    attempts={}; opened_states=set(); opened_edges=set(); resolved=set(); registered=set()
    for r in records:
        p=r['payload']; action=r['action']
        if action=='transition_completed' and p['operation']=='discover_state':registered.add(p['args'][0])
        if action=='access_attempt':
            key=p['attempt']
            if key in attempts: raise LifecycleError('duplicate_access_attempt')
            attempts[key]=(p['state'],p['edge'])
        elif action in ('access_opened','access_not_opened'):
            key=p['attempt']
            if key not in attempts or key in resolved: raise LifecycleError('unmatched_access_receipt')
            resolved.add(key)
            if action=='access_opened':
                state,edge=attempts[key]
                if edge is None: opened_states.add(state)
                else:
                    if state not in opened_states: raise LifecycleError('edge_without_state_receipt')
                    opened_edges.add((state,edge))
    return dict(states_opened=len(opened_states), edges_opened=len(opened_edges),
                attempts=len(attempts), unresolved_attempts=len(set(attempts)-resolved),
                states_with_unresolved_edge_exposure=len(opened_states-registered))


class Progress:
    """Preserved lifecycle with durable action records and distinct candidate calls."""
    def __init__(self, journal):
        self.journal=journal; self.core=LifecycleProgress(); self.calls={}; self.context=None
        self.before_success=None
        journal.append('initialized', snapshot=self.core.snapshot())

    def transition(self, action, *args, **kwargs):
        # Persist intent before mutation; a crash cannot assert the mutation completed.
        self.journal.append('transition_attempt', operation=action, args=args, kwargs=kwargs)
        if action=='succeed':self.before_success=copy.deepcopy(self.core)
        getattr(self.core, action)(*args, **kwargs)
        self.journal.append('transition_completed', operation=action, args=args, kwargs=kwargs,
                            snapshot=self.core.snapshot())

    def call_start(self, state, edge, candidate):
        if candidate not in CANDIDATES or self.context is not None: raise LifecycleError('candidate_context')
        key=(state,edge,candidate)
        if key in self.calls: raise LifecycleError('candidate_repeated')
        if candidate=='isotropic': self.transition('start_edge', state, edge)
        else:
            prior=CANDIDATES[CANDIDATES.index(candidate)-1]
            if self.calls.get((state,edge,prior)) != 'completed': raise LifecycleError('candidate_order')
        self.journal.append('call_started', state=state, edge=edge, candidate=candidate)
        self.calls[key]='started'; self.context=key

    def call_complete(self):
        if self.context is None: raise LifecycleError('call_not_started')
        state,edge,candidate=self.context
        self.journal.append('call_completed',state=state,edge=edge,candidate=candidate)
        self.calls[self.context]='completed'; self.context=None
        if candidate==CANDIDATES[-1]: self.transition('complete_edge',state,edge)

    def failure(self, stage, error):
        before=self.core.snapshot(); trace=traceback.format_exc()
        self.journal.append('pre_failure',snapshot=before,context=self.context,
                            stage=stage,exception=type(error).__name__)
        if self.core.status=='success':
            if self.before_success is None:raise LifecycleError('missing_prepublication_state')
            # Processing is complete; final publication is a separate transaction.
            self.core=self.before_success
            self.core.fail('publication_validation',type(error).__name__)
            self.journal.append('publication_failed',snapshot=self.core.snapshot(),exception=type(error).__name__)
            return dict(pre_failure=before,terminal=self.core.snapshot(),context=self.context,
                        stage='publication_validation',exception=type(error).__name__,traceback=trace)
        state=before['active_state']; edge=None
        if self.context is not None: state,edge,_=self.context
        # A between-call failure is attached to the state, never a stale active edge.
        self.transition('fail',stage,type(error).__name__,state_key=state,edge_key=edge)
        after=self.core.snapshot()
        return dict(pre_failure=before,terminal=after,context=self.context,
                    stage=stage,exception=type(error).__name__,traceback=trace)


def replay(records):
    core=LifecycleProgress(); initialized=False; pending=None; calls={}; active=None; before_success=None
    for r in records:
        action=r['action']; p=r['payload']
        if action=='initialized':
            if initialized or p['snapshot']!=core.snapshot(): raise LifecycleError('initialization_record')
            initialized=True
        elif action=='transition_attempt':
            if not initialized or pending is not None: raise LifecycleError('transition_overlap')
            pending=p
        elif action=='transition_completed':
            if pending is None or any(p[k]!=pending[k] for k in ('operation','args','kwargs')):
                raise LifecycleError('transition_receipt')
            if p['operation'] not in ('discover_state','prepare_state','start_state_evaluation','start_edge',
                                     'complete_edge','complete_state','authorize_access','open_state','open_edge',
                                     'fail','block','succeed'):
                raise LifecycleError('transition_route')
            if p['operation']=='succeed':before_success=copy.deepcopy(core)
            getattr(core,p['operation'])(*p['args'],**p['kwargs'])
            if core.snapshot()!=p['snapshot']: raise LifecycleError('snapshot_replay_mismatch')
            pending=None
        elif action=='call_started':
            key=(p['state'],p['edge'],p['candidate'])
            if active is not None or key in calls or key[2] not in CANDIDATES: raise LifecycleError('call_replay')
            calls[key]='started'; active=key
        elif action=='call_completed':
            key=(p['state'],p['edge'],p['candidate'])
            if key!=active: raise LifecycleError('call_receipt')
            calls[key]='completed'; active=None
        elif action=='publication_failed':
            if core.status!='success' or before_success is None:raise LifecycleError('publication_failure_stage')
            core=before_success;core.fail('publication_validation',p['exception'])
            if core.snapshot()!=p['snapshot']:raise LifecycleError('publication_failure_snapshot')
        elif action not in ('access_attempt','access_opened','access_not_opened','pre_failure','numerical_stage','authorization','attempt'):
            raise LifecycleError('unknown_journal_action')
    return core.snapshot() if initialized else None, dict(started=len(calls),completed=sum(v=='completed' for v in calls.values())), pending


def view(path, snapshot, mode, *, expected_head, initialized=True):
    records,head=read_journal(path,expected_head=expected_head)
    access=receipts(records); reproduced,calls,pending=replay(records)
    if mode not in MODES: raise LifecycleError('publication_context')
    if initialized:
        if snapshot!=reproduced: raise LifecycleError('lifecycle_journal_mismatch')
        validate_snapshot(snapshot)
    elif snapshot is not None or reproduced is not None or access['attempts']:
        raise LifecycleError('forged_preinitialization')
    if mode=='pre_access' and access['attempts']: raise LifecycleError('pre_access_history_nonempty')
    if access['attempts'] and (snapshot is None or not snapshot['access_authorized']):
        raise LifecycleError('access_history_without_authorization')
    if mode=='empirical_success':
        if snapshot is None or snapshot['status']!='success' or pending or access['unresolved_attempts'] or access['states_with_unresolved_edge_exposure']:
            raise LifecycleError('success_incomplete_history')
        c=snapshot['counters']
        if calls['started']!=calls['completed'] or calls['completed']!=3*c['edges_completed']:
            raise LifecycleError('candidate_completion_count')
        if (access['states_opened'],access['edges_opened'])!=(c['states_discovered'],c['edges_discovered']):
            raise LifecycleError('success_access_counts')
    elif mode=='empirical_failure' and (snapshot is None or snapshot['status']!='failure'):
        raise LifecycleError('failure_required')
    elif mode=='empirical_partial' and (snapshot is None or snapshot['status'] not in ('blocked','failure')):
        raise LifecycleError('partial_must_be_stopped')
    return dict(schema_version=1,mode=mode,lifecycle_initialized=initialized,snapshot=snapshot,
                snapshot_sha256=digest(snapshot),journal_sha256=head,access=access,candidate_calls=calls,
                transition_unresolved=pending is not None)


def validate_persisted(directory, journal):
    """Read all actual artifacts; never manufacture evidence from QC."""
    directory=safe(directory)
    names=('qc.json','manifest.json','lifecycle_summary.json','evidence.json')
    loaded={n:json.loads(safe(directory/n).read_text()) for n in names}
    base={'schema_version','status','progress_authority'}
    schemas={'qc.json':(base,base|{'stage','exception','scientific_comparisons_available'}),
             'evidence.json':(base,), 'manifest.json':(base|{'outputs'},)}
    for name,allowed in schemas.items():
        if set(loaded[name]) not in allowed or loaded[name]['schema_version']!=1:
            raise LifecycleError('persisted_schema_'+name)
    authority=loaded['lifecycle_summary.json']
    actual=view(journal,authority['snapshot'],authority['mode'],expected_head=authority['journal_sha256'],
                initialized=authority['lifecycle_initialized'])
    if authority!=actual: raise LifecycleError('lifecycle_summary_mismatch')
    for name in ('qc.json','manifest.json','evidence.json'):
        if loaded[name].get('progress_authority')!=actual: raise LifecycleError('cross_file_'+name)
        if loaded[name].get('status') != ('failure' if actual['snapshot'] is None else actual['snapshot']['status']):
            raise LifecycleError('cross_file_status')
    manifest=loaded['manifest.json']
    for name,expected in manifest['outputs'].items():
        if Path(name).name!=name or name=='manifest.json': raise LifecycleError('manifest_path')
        if sha256_file(safe(directory/name))!=expected: raise LifecycleError('persisted_hash_mismatch')
    if not {'qc.json','lifecycle_summary.json','evidence.json'} <= set(manifest['outputs']):
        raise LifecycleError('missing_evidence_hash')
    return actual


class Launch:
    """One R5 wrapper around the unchanged governed launcher, with outer closure."""
    def __init__(self, directory):
        self.directory=safe(directory); self.stage='startup'; self.downstream=0; self.access=0
        self.core=GovernedLauncher(self.directory/'core.marker',self.directory/'authorization.marker')

    def execute(self, *, discover, expected, produce, verify, access):
        # Reserve before environment discovery, but this does not grant access.
        durable_write(self.directory/'attempt.json',dict(schema_version=1,status='reserved'))
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('error')
                self.stage='environment'; env=discover(); exp=expected(env)
                path=self.directory/'prerequisite.json'
                def producer():
                    self.stage='prerequisite'; produce(path,exp); strict_prerequisite(path,exp)
                def readiness(context):
                    self.stage='readiness'; strict_prerequisite(path,exp)
                    if context._authority!=env.fingerprint() or context._prerequisite!=sha256_file(path):
                        raise LaunchError('r5_context_mismatch')
                    self.downstream+=1
                    return verify(context)
                def guarded(context):
                    self.stage='access'; strict_prerequisite(path,exp)
                    self.access+=1; access(context)
                self.core.run(environment=env,expected=exp,required_packages=('numpy','scipy'),
                    prerequisite_path=path,produce_prerequisite=producer,
                    verify_synthetic=readiness,authorize_empirical=guarded)
        except BaseException as exc:
            durable_write(self.directory/'failure.json',dict(schema_version=1,stage=self.stage,
                exception=type(exc).__name__,traceback=traceback.format_exc(),downstream=self.downstream,
                access_callbacks=self.access,transitions=self.core.transitions))
            raise
