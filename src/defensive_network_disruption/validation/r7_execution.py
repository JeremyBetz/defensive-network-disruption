"""Session 14R7 adapter over accepted launch and projection-exposure authorities."""
from __future__ import annotations

import copy
import json
import traceback
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from . import numerical_failure_publication as publication
from .projection_exposure import MODES
import hashlib
from .r5_persistence import (
    CANDIDATES,
    Journal,
    Launch,
    LifecycleError,
    durable_write,
    read_journal,
)
from .launch_enforcement import sha256_file


class _CoreView:
    def __init__(self, progress: "Progress") -> None:
        self._progress = progress

    def snapshot(self) -> dict[str, Any]:
        records, _ = read_journal(self._progress.journal.path)
        return publication.replay(records)['snapshot']


class Progress:
    """R7 façade whose state is derived entirely from the durable journal."""

    def __init__(self, journal: Journal):
        self.journal = journal
        self.numerical_context = None
        self.context: tuple[str, str, str] | None = None
        self.before_success: Mapping[str, Any] | None = None
        self._states: dict[str, dict[str, Any]] = {}
        self._attempts: dict[str, str] = {}
        self._fields: set[tuple[str, str, str]] = set()
        self.core = _CoreView(self)
        self.journal.append("initialized")

    def _append(self, action: str, **payload: Any) -> None:
        self.journal.append(action, **payload)

    def transition(self, action: str, *args: Any, **kwargs: Any) -> None:
        if kwargs:
            raise LifecycleError("r7_transition_keywords")
        routes: dict[str, Callable[..., None]] = {
            "authorize_access": self.authorize_access,
            "discover_state": self.discover_state,
            "prepare_state": self.prepare_state,
            "start_state_evaluation": self.start_state,
            "complete_state": self.complete_state,
            "succeed": self.succeed,
        }
        if action not in routes:
            raise LifecycleError("r7_transition_route")
        routes[action](*args)

    def authorize_access(self) -> None:
        self._append("access_authorized")

    def discover_state(self, state: str, edges: Sequence[str]) -> None:
        edge_tuple = tuple(edges)
        if state in self._states or not edge_tuple or len(set(edge_tuple)) != len(edge_tuple):
            raise LifecycleError("state_registration")
        self._states[state] = {"edges": edge_tuple, "opened": set(), "prepared": False,
                               "started": False, "completed": set(), "done": False}
        self._append("state_discovered", state=state, edges=list(edges))

    def begin_projection(self, state: str) -> str:
        attempt = f"projection_{self.journal.count:09d}"
        if state not in self._states or state in self._attempts.values():
            raise LifecycleError("projection_state")
        self._attempts[attempt] = state
        self._append("projection_attempt", attempt=attempt, state=state)
        return attempt

    def project(self, state: str, callback: Callable[[], Any]) -> Any:
        attempt = self.begin_projection(state)
        try:
            result = callback()
        except BaseException:
            self._append("projection_not_materialized", attempt=attempt)
            del self._attempts[attempt]
            raise
        edges = self._states[state]["edges"]
        self._append("projection_materialized", attempt=attempt, edges=list(edges))
        self._states[state]["opened"].update(edges);del self._attempts[attempt]
        return result

    def prepare_state(self, state: str) -> None:
        item=self._states[state]
        if item["opened"] != set(item["edges"]):raise LifecycleError("prepare_without_projection")
        item["prepared"]=True
        self._append("state_prepared", state=state)

    def start_state(self, state: str) -> None:
        item=self._states[state]
        if not item["prepared"] or item["started"]:raise LifecycleError("state_start")
        item["started"]=True
        self._append("state_evaluation_started", state=state)

    def call_start(self, state: str, edge: str, candidate: str) -> None:
        if self.context is not None:
            raise LifecycleError("candidate_context")
        item=self._states[state];key=(state,edge,candidate)
        if not item["started"] or edge not in item["opened"] or key in self._fields:
            raise LifecycleError("field_context")
        index=CANDIDATES.index(candidate)
        if index and (state,edge,CANDIDATES[index-1]) not in self._fields:
            raise LifecycleError("field_order")
        self._append("field_started", state=state, edge=edge, candidate=candidate)
        self.context = (state, edge, candidate)

    def call_complete(self) -> None:
        if self.context is None:
            raise LifecycleError("call_not_started")
        state, edge, candidate = self.context
        self._append("field_completed", state=state, edge=edge, candidate=candidate)
        self._fields.add((state,edge,candidate))
        self.context = None

    def retain_and_complete_edges(self, state):
        for edge in self._states[state]['edges']:
            if not all((state,edge,c) in self._fields for c in CANDIDATES):
                raise LifecycleError('missing_candidate_completion')
            self._append('edge_completed',state=state,edge=edge)
            self._states[state]['completed'].add(edge)

    def complete_state(self, state: str) -> None:
        item=self._states[state]
        if item["completed"] != set(item["edges"]):raise LifecycleError("invalid_state_completion")
        item["done"]=True
        self._append("state_completed", state=state)

    def succeed(self) -> None:
        if self._attempts or not self._states or not all(x["done"] for x in self._states.values()):
            raise LifecycleError("incomplete_success")
        self.before_success = copy.deepcopy(self.core.snapshot())
        self._append("success")

    def numerical_stage(self, **detail):
        if self.context is None: raise LifecycleError('numerical_without_active_call')
        state,edge,candidate=self.context
        self.journal.append('numerical_stage',state=state,edge=edge,candidate=candidate,detail=detail)
        self.numerical_context=detail['stage']

    def failure(self, stage, error):
        trace=''.join(traceback.format_exception(error))
        tracepath=self.journal.path.parent/'numerical_traceback.txt'
        if not tracepath.exists():
            with tracepath.open('x') as f:
                f.write(trace);f.flush();__import__('os').fsync(f.fileno())
        before=None
        try: before=self.core.snapshot()
        except BaseException: pass
        state,edge,candidate=self.context or (None,None,None)
        numerical_stage=self.numerical_context if self.context else 'preparation'
        if numerical_stage is None: numerical_stage='geometry'
        self._append('failure',stage=numerical_stage,exception=type(error).__name__,state=state,
                     edge=edge,candidate=candidate,traceback_sha256=sha256_file(tracepath))
        terminal=self.core.snapshot()
        return dict(pre_failure=before,terminal=terminal,context=self.context,stage=numerical_stage,
                    exception=type(error).__name__,traceback=trace)


def view(path, snapshot, mode, *, expected_head, initialized=True):
    if mode not in MODES: raise LifecycleError('publication_mode')
    records,head=read_journal(path,expected_head=expected_head)
    if not initialized:
        if records: raise LifecycleError('forged_preinitialization')
        return dict(schema_version=2,mode='pre_access',journal_sha256=head,snapshot_sha256=None,snapshot=None)
    if any(r['action'].startswith('diagnostic_') for r in records):
        raise LifecycleError('diagnostic_route_not_full_study')
    authoritative=publication.authority(path,head)
    actual=authoritative['snapshot']['snapshot']
    if actual!=snapshot: raise LifecycleError('lifecycle_journal_mismatch')
    if mode=='pre_access' and (actual['access_authorized'] or not actual['confirmed_zero_exposure']):
        raise LifecycleError('pre_access_not_confirmed_zero')
    if mode=='empirical_success' and actual['status']!='success': raise LifecycleError('full_success_required')
    if mode=='empirical_failure' and actual['status']!='failure': raise LifecycleError('failure_required')
    if mode=='empirical_partial' and actual['status'] not in ('blocked','failure'):raise LifecycleError('partial_must_be_stopped')
    return dict(schema_version=2,mode=mode,journal_sha256=head,snapshot_sha256=authoritative['snapshot_sha256'],snapshot=actual)


def exposure_summary(path, *, expected_head):
    records,head=read_journal(path,expected_head=expected_head)
    if not records:
        return dict(schema_version=2,journal_sha256=head,states_opened=0,edges_opened=0,
            unresolved_projection_attempts=0,unresolved_exposed_edges=0,
            field_evaluations_started=0,field_evaluations_completed=0,
            field_work_by_candidate={c:{'started':0,'completed':0} for c in CANDIDATES})
    snapshot=publication.replay(records)['snapshot']
    attempts={r['payload']['attempt']:r['payload']['state'] for r in records if r['action']=='projection_attempt'}
    states={attempts[r['payload']['attempt']] for r in records if r['action']=='projection_materialized'}
    c=snapshot['counters']
    return dict(schema_version=2,journal_sha256=head,states_opened=len(states),
                **{k:c[k] for k in ('edges_opened','unresolved_projection_attempts','unresolved_exposed_edges',
                                   'field_evaluations_started','field_evaluations_completed')},
                field_work_by_candidate=snapshot['field_work_by_candidate'])


def validate_persisted(directory, journal):
    directory=Path(directory)
    def load(name):
        def pairs(items):
            out={}
            for k,v in items:
                if k in out: raise LifecycleError('duplicate_key')
                out[k]=v
            return out
        return json.loads((directory/name).read_text(),object_pairs_hook=pairs,
            parse_constant=lambda _: (_ for _ in ()).throw(LifecycleError('nonfinite_json')))
    loaded={n:load(n) for n in ('qc.json','manifest.json','lifecycle_summary.json','evidence.json')}
    base={'schema_version','status','progress_authority'}
    schemas={'qc.json':base|{'stage','exception','scientific_comparisons_available'},
             'manifest.json':base|{'outputs'},'evidence.json':base}
    for n,keys in schemas.items():
        if set(loaded[n])!=keys or loaded[n]['schema_version']!=1:raise LifecycleError('persisted_schema_'+n)
    bound=loaded['lifecycle_summary.json']
    if set(bound)!={'schema_version','mode','journal_sha256','snapshot_sha256','snapshot'} or bound['schema_version']!=2:
        raise LifecycleError('lifecycle_schema')
    actual=view(journal,bound['snapshot'],bound['mode'],expected_head=bound['journal_sha256'],initialized=bound['snapshot'] is not None)
    if bound!=actual:raise LifecycleError('lifecycle_summary_mismatch')
    for n in ('qc.json','manifest.json','evidence.json'):
        if loaded[n].get('progress_authority')!=actual or loaded[n].get('status')!=loaded['qc.json']['status']:
            raise LifecycleError('cross_file_'+n)
    status=loaded['qc.json']['status']
    if status not in ('success','failure','blocked'):raise LifecycleError('status_enum')
    if (status=='success') != (actual['mode']=='empirical_success'):raise LifecycleError('success_context')
    if status=='success' and (not loaded['qc.json'].get('scientific_comparisons_available') or loaded['qc.json'].get('exception') is not None):
        raise LifecycleError('scientific_acceptance')
    if actual['snapshot'] is not None:
        # Compare real persisted adapter evidence; never manufacture it from QC.
        publication.validate_persisted(directory/'numerical_publication',journal,bound['journal_sha256'],
            traceback_path=Path(journal).parent/'numerical_traceback.txt')
    for n,h in loaded['manifest.json']['outputs'].items():
        if Path(n).name!=n or sha256_file(directory/n)!=h:raise LifecycleError('persisted_hash_mismatch')
    return actual


__all__=['Journal','Launch','Progress','durable_write','exposure_summary','read_journal','view','validate_persisted']
