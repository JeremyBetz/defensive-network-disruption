#!/usr/bin/env python3
"""One governed R9Q diagnosis; startup and emergency persistence are stdlib only."""
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
START='da18745b1c02fdddf34e3e2d68cbf02892a890c1'
RELEASE='f00690c05d8c1c6db308a65bd311c43f9a8ef2fa'
PROTOCOL='docs/protocols/phase_14r9q_expanding_switch_equality_diagnosis.md'
OUT=ROOT/'outputs/continuous_occlusion_expanding_switch_equality_diagnosis'
OLD=ROOT/'outputs/continuous_occlusion_empirical_retry_r9n/local'
PREPARED='15a809060f0ba4a8cb3790011dab8008db3dad6e931c287ccb395f61ef1530b0'
RECEIPT='06061aeb8c6437da39e05503c8383e8c453713028c3bd75af8449d1218db82f1'
RETAINED={
 'original_failure.json':'12a8fbf3e61fdc7f5197458bef2303148dbbf6eba77d0e884dee7ee54c7aeee9',
 'numerical_traceback.txt':'6d8cf23e2486fd161878260501975e9ec4409eab27bf91ee811be78e0bc3834c',
 'emergency_failure.json':'8acf7a829c83858888bedd8c26655c4383676c280fa04143e8926c1f76cfdc6a',
 'publication_failure.json':'0107fbf0237287f836c43685a797adf5835eb2b990139703bf6a8eaec8b862d5',
 'publication_traceback.txt':'21d1b6cdd701879d5bed4131265345781b63a5416008143e3fb28f5ecc4feb65',
}


def canonical(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
    return h.hexdigest()


def write(path,raw):
    path=Path(path)
    if any(p.is_symlink() for p in (path,*path.parents)):raise PermissionError('symlink')
    path.parent.mkdir(parents=True,exist_ok=True)
    pending=path.with_name('.'+path.name+'.pending')
    with pending.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    os.link(pending,path);pending.unlink()
    fd=os.open(path.parent,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)


def put(path,value):write(path,canonical(value))


def git(*args):return subprocess.check_output(('git',*args),cwd=ROOT,text=True).strip()


def bindings():
    return json.loads((ROOT/PROTOCOL).read_text().split('```json\n',1)[1].split('\n```',1)[0])


def ci_expectation():
    from defensive_network_disruption.validation.checkpoint_ci_authority import CIExpectation
    return CIExpectation(git('rev-parse','HEAD'),sha(ROOT/PROTOCOL),sha(Path(__file__)),
                         sha(ROOT/'uv.lock'),sha(ROOT/'.github/workflows/ci.yml'))


def preflight(folder=OUT):
    if git('status','--porcelain'):raise RuntimeError('dirty_tree')
    if git('rev-parse','HEAD')!=git('rev-parse','origin/main'):raise RuntimeError('tracking_mismatch')
    git('merge-base','--is-ancestor',START,'HEAD')
    if git('rev-parse','v0.1.0^{}')!=RELEASE:raise RuntimeError('release_target')
    if Path(sys.prefix).resolve()!=(ROOT/'.venv').resolve():raise RuntimeError('project_environment')
    for path,h in bindings().items():
        if sha(ROOT/path)!=h:raise RuntimeError('inherited_authority_hash')
    sources=git('ls-files','*r9q*',PROTOCOL).splitlines()
    if len(sources)<5:raise RuntimeError('missing_committed_tooling')
    for path in sources:
        if subprocess.check_output(('git','show','HEAD:'+path),cwd=ROOT)!=(ROOT/path).read_bytes():raise RuntimeError('implementation_freshness')
    local=Path(folder)/'local'
    for name in ('review.marker','numerical.marker','outer_failure.json'):
        if (local/name).exists():raise FileExistsError('governed_attempt_exists')
    from defensive_network_disruption.validation.checkpoint_ci_authority import validate_receipt
    receipt=local/'checkpoint_ci.json'
    expected=(local/'checkpoint_ci.sha256').read_text().strip()
    ci=validate_receipt(receipt,ci_expectation(),expected_sha256=expected)
    return dict(head=git('rev-parse','HEAD'),protocol_sha256=sha(ROOT/PROTOCOL),
                implementation={p:sha(ROOT/p) for p in sources},ci_receipt_sha256=ci.receipt_sha256,
                release=RELEASE)


def selected(prepared,authority):
    from defensive_network_disruption.validation.r9p_retained_authority import RetainedJournalAuthority,R9N
    if not isinstance(authority,RetainedJournalAuthority):raise PermissionError('verified_receipt_required')
    value=authority.record();receipt=value['selected_receipt']
    if value['authority_id']!=R9N.authority_id or authority.sha256!=RECEIPT or value['terminal']!={k:v for k,v in zip(('state','edge','candidate','stage','exception'),R9N.terminal)} or receipt['state']!=R9N.selected_state or receipt['edge_present'] is not True:
        raise PermissionError('selected_receipt_mismatch')
    return lexical_selected(prepared,5,8)


def lexical_selected(prepared,state,edge):
    from defensive_network_disruption.validation.empirical_switch_diagnosis import project_prepared_edge
    with Path(prepared).open('rb') as f:
        for ordinal,line in enumerate(f):
            if ordinal==state:return project_prepared_edge(line.decode(),edge)
    raise ValueError('retained_row_missing')


def publication_controls(folder):
    """Test-only instrumentation of real terminal closure; no numerical substitution."""
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
    return rows,dict(controls_passed=all(r['passed'] for r in rows),legacy_unreachable=all(r['reason']=='legacy_unreachable' for r in rows),
      one_review=count==len(rows) and one_terminal,traceback_bound=trace_valid,
      independent_failure=all((Path(folder)/n/'publication_failure.json').exists() for n in ('publication_init','publisher_failure')),
      rerun_rejected=rerun)


def diagnose(folder=OUT):
    # No package import or retained read before the outer standard-library boundary.
    folder=Path(folder);local=folder/'local';wall=time.monotonic()
    environment=preflight(folder)
    put(local/'review.marker',dict(reserved=True,authorizes_access=False))
    from defensive_network_disruption.validation import r9q_evidence as e
    from defensive_network_disruption.validation.checkpoint_ci_authority import FailureController
    records=e.empty();controls=[];pub=dict.fromkeys(e.SCHEMAS['publication_route.json'][0],False)
    summary=dict(topology='H',complete=False,root_count=None)
    reason='not_executed';valid=False;serial=0;io_seconds=0.;pub_seconds=0.;repro_seconds=0.;ref_seconds=0.;numerical_start=None;repro_io=0.;ref_io=0.
    controller=FailureController(local/'failure')
    def save(label,value):
        nonlocal serial,io_seconds
        before=time.monotonic();path=local/f'{serial:06d}_{label}.json';serial+=1
        put(path,value);h=sha(path);io_seconds+=time.monotonic()-before;return h
    try:
        for name,h in RETAINED.items():
            if sha(OLD/name)!=h:raise ValueError('retained_failure_hash')
        from defensive_network_disruption.validation.r9p_retained_authority import review_registered,R9N
        authority=review_registered(OLD/'journal.jsonl',OLD/'numerical_traceback.txt',R9N)
        if authority.sha256!=RECEIPT:raise ValueError('retained_receipt_binding')
        put(local/'retained_review.json',authority.record())
        e.fill(records,'authority.json',reason='reviewed_once',flags=dict(source_hashes=True,review_valid=True,receipt_matches=True),counts=dict(records=authority.derived_record_count))
        from defensive_network_disruption.geometry import r9q_diagnosis as d
        controls=d.controls(save)
        if not all(r['passed'] for r in controls):raise RuntimeError('synthetic_control_failure')
        before=time.monotonic()
        try:
            publication_rows,pub=publication_controls(local/'publication_controls')
            save('publication_controls',publication_rows)
        except BaseException as error:
            controller.capture(error,'publication_controls');reason='publication_control_failure'
        pub_seconds=time.monotonic()-before
        e.fill(records,'publication_route.json',status='complete' if all(pub.values()) else 'invalid',reason='linear_controls' if all(pub.values()) else 'publication_control_failure',flags=pub,counts=dict(controls=5),timings=dict(seconds=pub_seconds))
        # Geometry safety requires synthetic observation and persistence controls.
        if not all(pub.values()):raise RuntimeError('publication_control_failure')
        put(local/'numerical.marker',dict(reserved=True,authorizes_access=False))
        numerical_start=time.monotonic();total_deadline=numerical_start+14400
        if sha(OLD/'prepared.jsonl')!=PREPARED:raise ValueError('prepared_hash')
        put(local/'access_attempt.json',dict(schema_version=1,state=5,edge=8,authority_sha256=authority.sha256))
        row=selected(OLD/'prepared.jsonl',authority)
        put(local/'selected_geometry.json',row)
        put(local/'access_materialized.json',dict(schema_version=1,selected_sha256=sha(local/'selected_geometry.json'),attempt_sha256=sha(local/'access_attempt.json')))
        reference_deadline=min(total_deadline,time.monotonic()+9000)
        io_before=io_seconds
        original=FailureController(local/'numerical_original')
        reproduction=d.reproduce(row,ROOT,save,reference_deadline,lambda error,stage:original.capture(error,stage));repro_seconds=reproduction['seconds']
        repro_io=io_seconds-io_before
        save('reproduction_summary',{k:v for k,v in reproduction.items() if k!='capture'})
        exact=reproduction['reproduced'];capture=reproduction['capture']
        e.fill(records,'failure_reproduction.json',status='complete' if exact else 'partial',reason='exact_reproduction' if exact else 'different_result',
          flags=dict(reproduced=exact,original_preserved=reproduction['exception'] is not None,observed_route=True,uncertified=True),
          counts=dict(localizations=int(capture is not None),probes=len(capture['probes']) if capture else 0),timings=dict(seconds=repro_seconds))
        valid=reproduction['observer_error'] is None and (exact or reproduction['timeout'] or reproduction['exception'] in (None,'VerificationError','GateFailure'))
        if not exact:
            reason='numerical_timeout' if reproduction['timeout'] else 'different_result'
        else:
            audit=d.probe_audit(capture);save('probe_audit',d.primitive(audit))
            e.fill(records,'equality_semantics.json',reason='exact_binary64_semantics',flags=dict(exact_binary64_check=True,owner_rule_distinct=True,nonzero_inside=audit['interior_nonzero_observed'],monotone_refuted=audit['monotone_predicate_refuted']))
            values=capture['locals'];pair=values['pair'];left,right=values['start'],values['end']
            functions=[d.Expanding(tuple(row['carrier']),tuple(row['receiver']),tuple(row['defenders'][i])) for i in pair]
            save('reference_coefficients',[d.primitive(f.identity) for f in functions])
            before=time.monotonic();io_before=io_seconds
            try:
                ref=d.reference(*functions,left,right,deadline=reference_deadline,sink=save)
            finally:
                ref_seconds=time.monotonic()-before;ref_io=io_seconds-io_before
            summary=dict(topology=ref['topology'],complete=ref['complete'],root_count=ref['root_count'])
            # No new production field probes: compare captured rows with independent bounds.
            from defensive_network_disruption.geometry.verification_audit import scalar_oracle
            scalar_ok=True;sampled=0;scalar_records=[]
            with d.deadline_limit(reference_deadline):
                for record in capture['rows']:
                    t=record['point']
                    if not left<=t<=right:continue
                    for position,field in zip(pair,functions,strict=True):
                        interval=field.bounds(d.F.from_float(t),d.F.from_float(t))[0]
                        actual=record['values'][position]
                        distance=max(interval.lo-d.F.from_float(actual),d.F.from_float(actual)-interval.hi,d.F(0))
                        query=tuple(b+t*(r-b) for b,r in zip(row['carrier'],row['receiver'],strict=True))
                        scalar=scalar_oracle('expanding',row['carrier'],row['defenders'][position],query)
                        scalar_ok &= distance<=d.F.from_float(1e-12) and abs(scalar-actual)<=1e-12;sampled+=1
                        scalar_records.append(dict(point=t,defender=position,production=actual,scalar=scalar,reference_distance=distance))
            scalar_ok=bool(scalar_ok and sampled)
            save('scalar_comparison',d.primitive(dict(passed=scalar_ok,sampled=sampled,records=scalar_records)))
            e.fill(records,'root_switch_audit.json',status='complete' if ref['complete'] else 'partial',reason='reference_complete' if ref['complete'] else 'reference_unresolved',
              flags=dict(provisional_only=True,root_count_available=ref['root_count'] is not None,coverage_complete=ref['complete'],scalar_comparison=scalar_ok),counts=dict(roots=ref['root_count'],sampled_nodes=sampled))
            e.fill(records,'independent_reference.json',status='complete' if ref['complete'] else 'partial',reason='reference_complete' if ref['complete'] else 'reference_unresolved',
              flags=dict(complete=ref['complete'],identity=ref['identity'],equality_refuted=ref['equality_refuted']),
              counts=dict(cells=ref['counts']['leaves'],**{k:ref['counts'][k] for k in ('signed','crossings','equal','unresolved')}),timings=dict(seconds=ref_seconds))
            reason='diagnosis_complete' if ref['complete'] else 'reference_limit'
    except BaseException as error:
        if not (local/'failure/original_failure.json').exists():controller.capture(error,'governed_diagnosis')
        else:controller.publication_failure(error)
        reason='numerical_timeout' if isinstance(error,TimeoutError) else 'synthetic_control_failure' if str(error)=='synthetic_control_failure' else 'publication_control_failure' if str(error)=='publication_control_failure' else 'shared_integrity_failure' if numerical_start is None or str(error) in ('prepared_hash','retained_failure_hash','retained_receipt_binding') else 'governed_failure'
        valid=isinstance(error,TimeoutError)
    elapsed=time.monotonic()-wall
    numerical_seconds=0. if numerical_start is None else time.monotonic()-numerical_start
    exclusive=max(0.,repro_seconds-repro_io)+max(0.,ref_seconds-ref_io)
    # Other source review, synthetic controls, uninstrumented I/O and closure overhead
    # are explicitly unattributed rather than charged to a numerical method.
    timings=dict(governed_wall=elapsed,numerical_wall=numerical_seconds,reproduction_inclusive=repro_seconds,
                 reference_inclusive=ref_seconds,publication_inclusive=pub_seconds,io=io_seconds,
                 waiting=0.,exclusive_compute=exclusive,unattributed=max(0.,elapsed-exclusive-io_seconds))
    put(local/'control_rows.json',controls);put(local/'publication_observations.json',pub);put(local/'reference_summary.json',summary)
    put(local/'outcome.json',dict(schema_version=1,records=records,reason=reason,execution_valid=valid,timings=timings))
    return e.close(folder,environment)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=('preflight','diagnose','publication-check'));args=parser.parse_args()
    try:
        if args.command=='preflight':result=preflight()
        elif args.command=='diagnose':result=diagnose()
        else:
            from defensive_network_disruption.validation.r9q_evidence import publication_check
            result=publication_check(OUT)
        print(json.dumps(result,sort_keys=True,allow_nan=False))
    except BaseException as error:
        if args.command=='diagnose' and not isinstance(error,FileExistsError):
            try:
                raw=''.join(traceback.format_exception(error)).encode()
                write(OUT/'local/outer_traceback.txt',raw)
                put(OUT/'local/outer_failure.json',dict(exception=type(error).__name__,traceback_sha256=hashlib.sha256(raw).hexdigest()))
            except BaseException:pass
        raise


if __name__=='__main__':main()
