#!/usr/bin/env python3
"""One R9T acceptance. Startup persistence is standard-library only."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[1]
START='7ad2d95231355801d2c6cb9f4ce6bfac0aa5bd2d'
RELEASE='f00690c05d8c1c6db308a65bd311c43f9a8ef2fa'
PROTOCOL='docs/protocols/phase_14r9t_binary64_transition_contract_repair.md'
OUT=ROOT/'outputs/continuous_occlusion_binary64_transition_contract_repair'


def canonical(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for data in iter(lambda:f.read(1048576),b''):h.update(data)
    return h.hexdigest()
def write(path,raw):
    path=Path(path)
    if any(p.is_symlink() for p in (path,*path.parents)):raise PermissionError('symlink')
    path.parent.mkdir(parents=True,exist_ok=True);pending=path.with_name('.'+path.name+'.pending')
    with pending.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    os.link(pending,path);pending.unlink();fd=os.open(path.parent,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)
def put(path,value):write(path,canonical(value))
def git(*args):return subprocess.check_output(('git',*args),cwd=ROOT,text=True).strip()
def bindings():return json.loads((ROOT/PROTOCOL).read_text().split('```json\n',1)[1].split('\n```',1)[0])
def ci_expectation():
    from defensive_network_disruption.validation.checkpoint_ci_authority import CIExpectation
    return CIExpectation(git('rev-parse','HEAD'),sha(ROOT/PROTOCOL),sha(Path(__file__)),sha(ROOT/'uv.lock'),sha(ROOT/'.github/workflows/ci.yml'))

def preflight(folder=OUT):
    if git('status','--porcelain'):raise RuntimeError('dirty_tree')
    if git('rev-parse','HEAD')!=git('rev-parse','origin/main'):raise RuntimeError('tracking_mismatch')
    git('merge-base','--is-ancestor',START,'HEAD')
    if git('rev-parse','v0.1.0^{}')!=RELEASE:raise RuntimeError('release_target')
    if Path(sys.prefix).resolve()!=(ROOT/'.venv').resolve():raise RuntimeError('project_environment')
    for path,h in bindings().items():
        if sha(ROOT/path)!=h:raise RuntimeError('inherited_authority_hash')
    sources=git('ls-files','*r9t*').splitlines()
    if len(sources)<7:raise RuntimeError('uncommitted_tooling')
    for path in sources:
        if subprocess.check_output(('git','show','HEAD:'+path),cwd=ROOT)!=(ROOT/path).read_bytes():raise RuntimeError('implementation_freshness')
    local=Path(folder)/'local'
    for name in ('acceptance.marker','retained_trace.marker','retained_candidate.marker','outer_failure.json'):
        if (local/name).exists():raise FileExistsError('governed_attempt_exists')
    from defensive_network_disruption.validation.checkpoint_ci_authority import validate_receipt
    receipt=local/'checkpoint_ci.json';expected=(local/'checkpoint_ci.sha256').read_text().strip()
    ci=validate_receipt(receipt,ci_expectation(),expected_sha256=expected)
    from defensive_network_disruption.validation.r9t_authority import verify_sources
    verify_sources(ROOT)
    return dict(head=git('rev-parse','HEAD'),protocol_sha256=sha(ROOT/PROTOCOL),release=RELEASE,
                implementation={p:sha(ROOT/p) for p in sources},ci_receipt_sha256=ci.receipt_sha256)


def publication_controls(folder):
    """Test-only instrumentation of real terminal closure; no numerical substitution."""
    started=time.monotonic()
    from unittest.mock import patch
    from defensive_network_disruption.validation import r9o_terminal as terminal
    from defensive_network_disruption.validation.r7_execution import Progress,Journal
    with patch.object(terminal.linear,'review',wraps=terminal.linear.review) as spy:
        rows=terminal.controls(folder)
        count=spy.call_count
    trace_valid=True;one_terminal=True;rerun=True
    for row in rows:
        local=Path(folder)/row['fixture']
        records=[json.loads(line) for line in (local/'journal.jsonl').read_bytes().splitlines()]
        terminal_events=[r for r in records if r['action'] in ('success','failure')]
        one_terminal &= len(terminal_events)==1
        if row['fixture']!='success':
            original=json.loads((local/'original_failure.json').read_text())
            trace_valid &= terminal_events[0]['payload']['traceback_sha256']==original['traceback_sha256']
            trace_valid &= terminal.FailureController(local).validate()['status']=='valid'
        journal=Journal(local/'rerun_guard.jsonl');progress=Progress(journal)
        try:
            try:terminal.TerminalClosure(progress,local).fail(ValueError('second'),'synthetic',lambda *_:None)
            except FileExistsError:pass
            else:rerun=False
        finally:journal.close()
    flags=dict(controls_passed=all(r['passed'] for r in rows),legacy_unreachable=all(r['reason']=='legacy_unreachable' for r in rows),
      one_review=count==len(rows) and one_terminal,traceback_bound=trace_valid,
      independent_failure=all((Path(folder)/n/'publication_failure.json').exists() for n in ('publication_init','publisher_failure')),
      rerun_rejected=rerun)

    return rows,dict(flags=flags,counts=dict(controls=len(rows)),timings=dict(seconds=time.monotonic()-started))


_SEAL=object()
class Permit:
    def __init__(self,seal):
        if seal is not _SEAL:raise PermissionError('direct_entry')
        self.seal=seal

def unlock(environment,rows,pub):
    from defensive_network_disruption.validation.r9t_acceptance import FIXTURES,NEGATIVES
    history=rows['historical_regressions.csv'];top=rows['synthetic_trace_controls.csv'];neg=rows['negative_controls.csv']
    if not environment.get('ci_receipt_sha256') or not environment.get('head'):raise PermissionError('checkpoint_authority')
    if (len(history),sum(x['components'] for x in history),sum(x['permutations'] for x in history))!=(108,366,399) or any(x['status']!='passed' for x in history):raise PermissionError('historical_authority')
    if tuple(x['fixture'] for x in top)!=FIXTURES or tuple(x['fixture'] for x in neg)!=NEGATIVES or not all(x['passed'] for x in top) or not all(x['blocked'] for x in neg) or not all(pub['flags'].values()):raise PermissionError('acceptance_failed')
    return Permit(_SEAL)

def check_permit(permit):
    if type(permit)is not Permit or permit.seal is not _SEAL:raise PermissionError('direct_entry')

def trace_review(local,permit):
    check_permit(permit)
    from defensive_network_disruption.validation import r9t_authority as source
    from defensive_network_disruption.validation.r9t_acceptance import primitive
    from defensive_network_disruption.geometry.verification_repair import VerificationError
    allowed=source.verify_sources(ROOT)
    put(local/'retained_bindings.json',allowed)
    put(local/'trace_attempt.json',dict(schema_version=1,trace_sha256=allowed['trace.json'],index_sha256=source.INDEX))
    records={}
    for name,h in allowed.items():
        if name=='retained/selected.json':continue
        raw=(ROOT/source.SOURCE/name).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=h:raise ValueError('retained_changed')
        write(local/'retained'/name,raw)
        if name.startswith('retained/'):records[Path(name).stem]=json.loads(raw)
    trace=json.loads((local/'retained/trace.json').read_bytes())
    put(local/'trace_materialized.json',dict(schema_version=1,attempt_sha256=sha(local/'trace_attempt.json'),trace_sha256=sha(local/'retained/trace.json')))
    try:result=source.resolve_saved(trace,records)
    except VerificationError as error:
        put(local/'trace_resolution.json',dict(status='blocked',exception=type(error).__name__,reason=str(error)))
        close_trace_block(local,error)
        return None,records
    put(local/'trace_resolution.json',dict(status='accepted',evidence=primitive(result)))
    return result,records



def close_trace_block(local,error):
    """Terminal publication for a conservative trace-only block: zero geometry."""
    from defensive_network_disruption.validation import r9o_terminal as terminal
    from defensive_network_disruption.validation.r5_persistence import Journal
    from defensive_network_disruption.validation.r7_execution import Progress
    journal=Journal(local/'diagnostic_journal.jsonl');progress=Progress(journal)
    def publish(authority,trace):
        put(local/'closure_authority.json',authority.record())
        terminal.numerical_package(local/'numerical_publication',authority,trace)
        put(local/'closure_validation.json',dict(validated=True,linear_reviews=1,authority_sha256=sha(local/'closure_authority.json')))
    try:terminal.TerminalClosure(progress,local/'numerical_failure').fail(error,'retained_trace_canonicalization',publish)
    finally:journal.close()


def selected(local,permit):
    check_permit(permit)
    from defensive_network_disruption.validation import r9t_authority as source
    allowed=json.loads((local/'retained_bindings.json').read_bytes());name='retained/selected.json'
    put(local/'access_attempt.json',dict(schema_version=1,selected_sha256=allowed[name]))
    raw=(ROOT/source.SOURCE/name).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=allowed[name]:raise ValueError('selected_hash')
    row=json.loads(raw)
    # Exposure is acknowledged before schema/coefficient/downstream validation.
    write(local/'selected_geometry.json',raw)
    put(local/'access_materialized.json',dict(schema_version=1,attempt_sha256=sha(local/'access_attempt.json'),selected_sha256=sha(local/'selected_geometry.json')))
    return row


def retained_candidate(local,permit,resolution,records,save,deadline):
    check_permit(permit)
    from defensive_network_disruption.geometry import r9t_adapter as adapter
    from defensive_network_disruption.geometry.r9q_diagnosis import deadline_limit
    from defensive_network_disruption.validation.r9t_acceptance import primitive
    from defensive_network_disruption.validation import r9s_authority, r9o_terminal as terminal, r9j_linear_publication as linear
    from defensive_network_disruption.validation.r5_persistence import Journal
    from defensive_network_disruption.validation.r7_execution import Progress
    from defensive_network_disruption.validation.checkpoint_ci_authority import FailureController
    journal=Journal(local/'diagnostic_journal.jsonl');p=Progress(journal)
    state,edge='selected_state','selected_edge';matches=[]
    expected=primitive(resolution)
    def publish(authority,trace):
        put(local/'closure_authority.json',authority.record())
        if authority.legacy['snapshot']['diagnostic_success']:
            package=linear.old.package(authority.legacy,accepted=True,checks={'terminal_valid':True})
            for n in ('qc','manifest','evidence'):put(local/'numerical_publication'/(n+'.json'),package)
            linear.validate_numerical_package(local/'numerical_publication',authority)
        else:terminal.numerical_package(local/'numerical_publication',authority,trace)
        put(local/'closure_validation.json',dict(validated=True,linear_reviews=1,authority_sha256=sha(local/'closure_authority.json')))
    def observe(**kw):
        value=primitive(kw);save('localization',value)
        if kw['kind']=='transition_evidence':
            a=value['value']['authority'];b=expected['authority']
            if all(a[k]==b[k] for k in ('enclosure','lower','upper')):matches.append(value['value'])
    def stage(**kw):
        p.numerical_stage(**kw);save('numerical_stage',kw)
    try:
        p.authorize_access();p.discover_state(state,(edge,))
        attempt=p.begin_projection(state)
        row=selected(local,permit)
        # An interrupted callback/receipt leaves the existing attempt pending.
        # No confirmed-zero event is emitted on uncertain materialization.
        journal.append('projection_materialized',attempt=attempt,edges=[edge])
        p._states[state]['opened'].add(edge);del p._attempts[attempt]
        r9s_authority.geometry_match(records,row)
        p.prepare_state(state);p.start_state(state)
        journal.append('diagnostic_started',state=state,edge=edge,candidate='expanding');p.context=(state,edge,'expanding')
        put(local/'candidate_invocation.json',dict(schema_version=1,candidate='expanding',invocations=1))
        with deadline_limit(min(deadline,time.monotonic()+600)):
            _,details=adapter.evaluate('expanding',row['carrier'],row['receiver'],row['defenders'],root=ROOT,
                authority_context={'alias':row['alias'],'state':state,'edge':edge},record=stage,
                localization_sink=observe,deadline=min(deadline,time.monotonic()+600))
        put(local/'retained_result.json',primitive(details));put(local/'runtime_trace_matches.json',matches)
        if not matches or any(v!=expected for v in matches):raise ValueError('runtime_trace_resolution_mismatch')
        journal.append('diagnostic_completed',state=state,edge=edge,candidate='expanding');p.context=None
        journal.append('diagnostic_success')
    except BaseException as error:
        closure=terminal.TerminalClosure(p,local/'numerical_failure')
        closure.fail(error,p.numerical_context or 'retained_materialization',publish)
        raise
    else:
        # Successful single-candidate diagnostic; ordinary edge/state counts stay zero.
        try:
            authority=linear.review(journal.path,expected_head=journal.previous)
            publish(authority,None)
        except BaseException as error:
            controller=FailureController(local/'publication_failure')
            controller.capture(error,'diagnostic_success_publication')
            raise
    finally:journal.close()


def audit(folder=OUT):
    folder=Path(folder);local=folder/'local';wall=time.monotonic();cpu=time.process_time()
    environment=preflight(folder)
    put(local/'acceptance.marker',dict(reserved=True,authorizes_access=False))
    from defensive_network_disruption.validation import r9t_acceptance as a, r9t_evidence as e
    from defensive_network_disruption.validation.checkpoint_ci_authority import FailureController
    from defensive_network_disruption.geometry.r9q_diagnosis import deadline_limit
    from defensive_network_disruption.geometry.verification_repair import VerificationError
    from defensive_network_disruption.geometry.production_verification import GateFailure
    serial=0;io=0.;io_cpu=0.;numeric=0.;valid=True;reason='complete';deadline=wall+3600
    rows={n:[] for n in e.COLUMNS};perf=dict(localization_calls=0,subdivisions=0,floats_inspected=0,max_depth=0,unresolved=0)
    put(local/'authority.json',environment)
    def measured(function,*args,**kwargs):
        nonlocal numeric
        started=time.monotonic()
        try:return function(*args,**kwargs)
        finally:numeric+=time.monotonic()-started
    def save(label,value):
        nonlocal serial,io,io_cpu
        start=time.monotonic();c=time.process_time();path=local/'observations'/f'{serial:06d}_{label}.json';serial+=1
        put(path,value);h=sha(path);io+=time.monotonic()-start;io_cpu+=time.process_time()-c
        observations=value.get('localizations',[]) if label.startswith('historical_') else (value,) if label=='localization' else ()
        for obs in observations:
            v=obs['value']
            if obs['kind']=='topology':
                perf['localization_calls']+=1;perf['subdivisions']+=v['subdivisions'];perf['max_depth']=max(perf['max_depth'],v['max_depth']);perf['unresolved']+=v['classification']in ('E','F','G')
            elif obs['kind']=='inspection_work':perf['floats_inspected']+=v['floats_inspected']
        return h
    try:
        with deadline_limit(min(deadline,time.monotonic()+600)):
            rows['synthetic_trace_controls.csv']=measured(a.trace_controls,save)
            rows['negative_controls.csv']=measured(a.negative_controls,save)
        pubrows,pub=publication_controls(local/'publication_controls');put(local/'publication_observations.json',dict(rows=pubrows,summary=pub))
        if not all(r['passed'] for r in rows['synthetic_trace_controls.csv']) or not all(r['blocked'] for r in rows['negative_controls.csv']) or not all(pub['flags'].values()):reason='synthetic_failure'
        else:
            rows['historical_regressions.csv']=measured(a.historical_regression,ROOT,save,deadline=deadline)
            if any(r['status']!='passed' for r in rows['historical_regressions.csv']):reason='historical_incompatibility'
            else:
                permit=unlock(environment,rows,pub)
                put(local/'retained_trace.marker',dict(reserved=True,authorizes_access=False))
                resolution,records=measured(trace_review,local,permit)
                if resolution is None:reason='trace_blocked'
                else:
                    put(local/'retained_candidate.marker',dict(reserved=True,authorizes_access=False))
                    measured(retained_candidate,local,permit,resolution,records,save,deadline)
    except BaseException as error:
        FailureController(local/'outer_failure').capture(error,'retained_candidate' if (local/'access_attempt.json').exists() else 'trace_review' if (local/'trace_attempt.json').exists() else 'synthetic_acceptance')
        reason='timeout' if isinstance(error,TimeoutError) else 'candidate_unresolved' if isinstance(error,(VerificationError,GateFailure)) and (local/'access_materialized.json').exists() else 'execution_failure'
        valid=reason in ('timeout','candidate_unresolved')
    for name,values in rows.items():put(local/(name+'.json'),values)
    elapsed=time.monotonic()-wall;compute=max(0.,time.process_time()-cpu-io_cpu)
    put(local/'outcome.json',dict(schema_version=1,execution_valid=valid,reason=reason,performance=perf,
        timings=dict(governed_wall=elapsed,exclusive_compute=compute,inclusive_numerical=numeric,
            io=io,waiting=0.,unattributed=max(0.,elapsed-compute-io))))
    return e.close(folder)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=('preflight','audit','publication-check'));args=parser.parse_args()
    try:
        if args.command=='preflight':result=preflight()
        elif args.command=='audit':result=audit()
        else:
            from defensive_network_disruption.validation.r9t_evidence import publication_check
            result=publication_check(OUT)
        print(json.dumps(result,sort_keys=True,allow_nan=False))
    except BaseException as error:
        if args.command=='audit' and not isinstance(error,FileExistsError):
            try:
                raw=''.join(traceback.format_exception(error)).encode();write(OUT/'local/outer_traceback.txt',raw)
                put(OUT/'local/outer_failure.json',dict(exception=type(error).__name__,stage='startup_or_closure',traceback_sha256=hashlib.sha256(raw).hexdigest()))
            except BaseException:pass
        raise
if __name__=='__main__':main()
