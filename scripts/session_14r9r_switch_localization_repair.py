#!/usr/bin/env python3
"""One R9R acceptance. Startup persistence is standard-library only."""
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
START='308bf4ad84af9ea7f6505acc78c3808db194c0d5'
RELEASE='f00690c05d8c1c6db308a65bd311c43f9a8ef2fa'
PROTOCOL='docs/protocols/phase_14r9r_switch_localization_repair.md'
OUT=ROOT/'outputs/continuous_occlusion_switch_localization_repair'
RETAINED=ROOT/'outputs/continuous_occlusion_expanding_switch_equality_diagnosis/local'
INDEX='5652d6e4d57a92c0bf084d20d6cc1ee33708713f15bc5ff4c325b7a715f9c14a'
REVIEW='06061aeb8c6437da39e05503c8383e8c453713028c3bd75af8449d1218db82f1'


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
    sources=git('ls-files','*r9r*').splitlines()
    if len(sources)<7:raise RuntimeError('uncommitted_tooling')
    for path in sources:
        if subprocess.check_output(('git','show','HEAD:'+path),cwd=ROOT)!=(ROOT/path).read_bytes():raise RuntimeError('implementation_freshness')
    local=Path(folder)/'local'
    for name in ('acceptance.marker','numerical.marker','outer_failure.json'):
        if (local/name).exists():raise FileExistsError('governed_attempt_exists')
    from defensive_network_disruption.validation.checkpoint_ci_authority import validate_receipt
    receipt=local/'checkpoint_ci.json';expected=(local/'checkpoint_ci.sha256').read_text().strip()
    ci=validate_receipt(receipt,ci_expectation(),expected_sha256=expected)
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


_ACCESS_SEAL=object()

class AccessPermit:
    __slots__=('seal','checkpoint')
    def __init__(self,seal,checkpoint):
        if seal is not _ACCESS_SEAL:raise PermissionError('access_authority')
        self.seal=seal;self.checkpoint=checkpoint


def unlock(environment,rows,pub):
    history=rows['historical_regressions.csv']
    if not environment.get('ci_receipt_sha256') or not environment.get('head'):raise PermissionError('checkpoint_authority')
    if (len(history),sum(x['components'] for x in history),sum(x['permutations'] for x in history))!=(108,366,399):raise PermissionError('incomplete_numerical_authority')
    if not all(x['status']=='passed' for x in history) or len(rows['topology_controls.csv'])!=14 or not all(x['passed'] for x in rows['topology_controls.csv']) or len(rows['negative_controls.csv'])!=9 or not all(x['blocked'] for x in rows['negative_controls.csv']) or not all(pub['flags'].values()):raise PermissionError('acceptance_failed')
    return AccessPermit(_ACCESS_SEAL,environment['head'])


def selected(local,permit):
    """Only R9Q's already selected edge and its authority; no population fallback."""
    if not isinstance(permit,AccessPermit) or permit.seal is not _ACCESS_SEAL:raise PermissionError('direct_access_rejected')
    if sha(RETAINED/'private_index.json')!=INDEX:raise ValueError('retained_index_hash')
    index=json.loads((RETAINED/'private_index.json').read_bytes())['files']
    allowed=('retained_review.json','access_attempt.json','access_materialized.json','selected_geometry.json')
    for name in allowed:
        if name not in index or sha(RETAINED/name)!=index[name]:raise ValueError('retained_member_hash')
    if sha(RETAINED/'retained_review.json')!=REVIEW:raise ValueError('retained_review_hash')
    receipt=json.loads((RETAINED/'access_materialized.json').read_bytes())
    if receipt['selected_sha256']!=index['selected_geometry.json'] or receipt['attempt_sha256']!=index['access_attempt.json']:raise ValueError('retained_lineage')
    put(local/'retained_lineage.json',dict(index_sha256=INDEX,review_sha256=REVIEW,selected_sha256=index['selected_geometry.json']))
    put(local/'access_attempt.json',dict(schema_version=1,selected_sha256=index['selected_geometry.json']))
    raw=(RETAINED/'selected_geometry.json').read_bytes()
    row=json.loads(raw)
    if set(row)!= {'alias','carrier','receiver','defenders'}:raise ValueError('selected_schema')
    write(local/'selected_geometry.json',raw)
    put(local/'access_materialized.json',dict(schema_version=1,attempt_sha256=sha(local/'access_attempt.json'),selected_sha256=sha(local/'selected_geometry.json')))
    return row


def retained_run(local,row,save,deadline):
    from defensive_network_disruption.geometry import r9r_adapter as adapter
    from defensive_network_disruption.geometry.r9q_diagnosis import deadline_limit
    from defensive_network_disruption.validation.r9r_acceptance import primitive
    from defensive_network_disruption.validation import r9o_terminal as terminal
    from defensive_network_disruption.validation import r9j_linear_publication as linear
    from defensive_network_disruption.validation.r5_persistence import Journal
    from defensive_network_disruption.validation.r7_execution import Progress
    journal=Journal(local/'diagnostic_journal.jsonl');p=Progress(journal)
    state,edge='selected_state','selected_edge'
    p.authorize_access();p.discover_state(state,(edge,));p.project(state,lambda:row)
    p.prepare_state(state);p.start_state(state)
    context=dict(state=state,edge=edge,candidate='expanding')
    journal.append('diagnostic_started',**context);p.context=(state,edge,'expanding')
    observations=[]
    def observe(**detail):
        value=primitive(detail);save('localization',value);observations.append(value)
    def record(**detail):
        p.numerical_context=detail['stage'];journal.append('numerical_stage',**context,detail=detail)
        save('numerical_stage',detail)
    try:
        with deadline_limit(min(deadline,time.monotonic()+600)):
            result=adapter.evaluate('expanding',row['carrier'],row['receiver'],row['defenders'],root=ROOT,
                authority_context={'alias':row['alias'],'state':state,'edge':edge},record=record,
                deadline=deadline,localization_sink=observe)
        save('retained_observations',observations)
        put(local/'retained_result.json',primitive(result[1]))
        # R9Q's excluded region is retained evidence, not recomputed authority.
        index=json.loads((RETAINED/'private_index.json').read_bytes())['files']
        names=[name for name in index if name.endswith('_reference_cell.json')]
        if len(names)!=1:raise ValueError('retained_reference_inventory')
        name=names[0]
        if sha(RETAINED/name)!=index[name]:raise ValueError('retained_reference_hash')
        cell=json.loads((RETAINED/name).read_bytes())
        put(local/'retained_reference_cell.json',cell)
        put(local/'retained_observations.json',observations)
        from fractions import Fraction as F
        def fraction(x):return F(int(x['numerator_hex'],16),int(x['denominator_hex'],16))
        forbidden=(fraction(cell['left']),fraction(cell['right']))
        roots=[o['value'] for o in observations if o['kind']=='isolated_root']
        outside=all(fraction(x[1])<forbidden[0] or fraction(x[0])>forbidden[1] for x in roots)
        if not outside:
            from defensive_network_disruption.geometry.verification_repair import VerificationError
            raise VerificationError('retained_root_region_conflict')
        journal.append('diagnostic_completed',**context);p.context=None
        journal.append('diagnostic_success')
        authority=linear.review(journal.path,expected_head=journal.previous)
        put(local/'diagnostic_authority.json',authority.record())
        terminal.numerical_package(local/'diagnostic_publication',authority,None)
        put(local/'retained_success.json',dict(result_sha256=sha(local/'retained_result.json'),authority_sha256=sha(local/'diagnostic_authority.json'),observations_sha256=sha(local/'retained_observations.json'),reference_sha256=sha(local/'retained_reference_cell.json')))
        return bool(outside)
    except BaseException as error:
        closure=terminal.TerminalClosure(p,local/'numerical_failure')
        closure.fail(error,p.numerical_context or 'geometry',lambda authority,trace:terminal.numerical_package(local/'failed_diagnostic_publication',authority,trace))
        raise
    finally:
        journal.close()


def audit(folder=OUT):
    folder=Path(folder);local=folder/'local';wall=time.monotonic();cpu_start=time.process_time();environment=preflight(folder)
    put(local/'acceptance.marker',dict(schema_version=1,reserved=True,authorizes_access=False))
    from defensive_network_disruption.validation import r9r_evidence as e
    from defensive_network_disruption.validation import r9r_acceptance as acceptance
    from defensive_network_disruption.validation.checkpoint_ci_authority import FailureController
    from defensive_network_disruption.geometry.r9q_diagnosis import deadline_limit
    controller=FailureController(local/'failure');serial=0;io=0.;io_cpu=0.;numeric_start=time.monotonic();deadline=numeric_start+3600
    rows={name:[] for name in e.COLUMNS};retained=dict(path_completed=False,root_free_region_preserved=False,seconds=0.)
    pub=dict(flags=dict.fromkeys(e.SCHEMAS['publication_tripwire.json'][0],False),counts=dict(controls=0),timings=dict(seconds=0.))
    performance=dict(localization_calls=0,subdivisions=0,floats_inspected=0,max_depth=0,unresolved=0)
    def save(label,value):
        nonlocal serial,io,io_cpu
        before=time.monotonic();before_cpu=time.process_time();path=local/f'{serial:06d}_{label}.json';serial+=1;put(path,value);h=sha(path);io+=time.monotonic()-before;io_cpu+=time.process_time()-before_cpu
        if label.startswith('historical_') or label=='localization':
            for obs in value.get('localizations',[]) if label.startswith('historical_') else (value,):
                item=obs['value']
                if obs['kind']=='topology':
                    performance['localization_calls']+=1;performance['subdivisions']+=item['subdivisions']
                    performance['max_depth']=max(performance['max_depth'],item['max_depth'])
                    performance['unresolved']+=item['classification']in ('E','F','G')
                elif obs['kind']=='inspection_work':performance['floats_inspected']+=item['floats_inspected']
        return h
    valid=True;reason='complete';publication_rows=[]
    try:
        with deadline_limit(min(deadline,time.monotonic()+600)):
            rows['topology_controls.csv']=acceptance.topology_controls(save)
            rows['negative_controls.csv']=acceptance.negative_controls(save)
        publication_rows,pub=publication_controls(local/'publication_controls');put(local/'publication_observations.json',dict(rows=publication_rows,summary=pub))
        if not all(r['passed'] for r in rows['topology_controls.csv']) or not all(r['blocked'] for r in rows['negative_controls.csv']) or not all(pub['flags'].values()):
            reason='synthetic_failure'
        else:
            rows['historical_regressions.csv']=acceptance.historical_regression(ROOT,save,deadline=deadline)
            if any(r['status']!='passed' for r in rows['historical_regressions.csv']):reason='historical_incompatibility'
            else:
                permit=unlock(environment,rows,pub)
                put(local/'numerical.marker',dict(schema_version=1,reserved=True,authorizes_access=False))
                row=selected(local,permit);started=time.monotonic()
                try:
                    retained['root_free_region_preserved']=retained_run(local,row,save,deadline)
                    retained['path_completed']=True
                    if not retained['root_free_region_preserved']:reason='retained_unresolved'
                finally:retained['seconds']=time.monotonic()-started
    except BaseException as error:
        controller.capture(error,'retained' if (local/'access_attempt.json').exists() else 'synthetic_acceptance')
        reason='timeout' if isinstance(error,TimeoutError) else 'retained_unresolved' if type(error).__name__ in ('VerificationError','GateFailure') and (local/'access_materialized.json').exists() else 'governed_failure'
        valid=reason in ('timeout','retained_unresolved')
    if not (local/'publication_observations.json').exists():
        put(local/'publication_observations.json',dict(rows=publication_rows,summary=pub))
    put(local/'authority.json',environment)
    elapsed=time.monotonic()-wall;numeric=time.monotonic()-numeric_start
    cpu=max(0.,time.process_time()-cpu_start-io_cpu)
    timings=dict(governed_wall=elapsed,exclusive_compute=cpu,inclusive_numerical=numeric,
                 io=io,waiting=0.,unattributed=max(0.,elapsed-cpu-io))
    for name,items in rows.items():put(local/(name+'.json'),items)
    put(local/'outcome.json',dict(schema_version=1,execution_valid=valid,reason=reason,authority_bound=True,
        timings=timings,retained=retained,publication=pub,performance=performance))
    return e.close(folder,environment)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=('preflight','audit','publication-check'));args=parser.parse_args()
    try:
        if args.command=='preflight':result=preflight()
        elif args.command=='audit':result=audit()
        else:
            from defensive_network_disruption.validation.r9r_evidence import publication_check
            result=publication_check(OUT)
        print(json.dumps(result,sort_keys=True,allow_nan=False))
    except BaseException as error:
        if args.command=='audit' and not isinstance(error,FileExistsError):
            try:
                raw=''.join(traceback.format_exception(error)).encode();write(OUT/'local/outer_traceback.txt',raw)
                put(OUT/'local/outer_failure.json',dict(exception=type(error).__name__,traceback_sha256=hashlib.sha256(raw).hexdigest()))
            except BaseException:pass
        raise


if __name__=='__main__':main()
