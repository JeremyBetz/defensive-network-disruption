#!/usr/bin/env python3
"""One bounded R9S inspection; standard-library startup failure boundary."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import traceback
import warnings

ROOT=Path(__file__).resolve().parents[1]
START='b5a30b76237b98bc143c29eafb4988437e7df6af'
RELEASE='f00690c05d8c1c6db308a65bd311c43f9a8ef2fa'
PROTOCOL='docs/protocols/phase_14r9s_binary64_transition_trace_diagnosis.md'
OUT=ROOT/'outputs/continuous_occlusion_binary64_transition_trace'

def canonical(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for raw in iter(lambda:f.read(1048576),b''):h.update(raw)
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
    sources=git('ls-files','*r9s*').splitlines()
    if len(sources)<7:raise RuntimeError('uncommitted_tooling')
    for path in sources:
        if subprocess.check_output(('git','show','HEAD:'+path),cwd=ROOT)!=(ROOT/path).read_bytes():raise RuntimeError('implementation_freshness')
    local=Path(folder)/'local'
    for name in ('diagnosis.marker','numerical.marker','outer_failure.json'):
        if (local/name).exists():raise FileExistsError('governed_attempt_exists')
    from defensive_network_disruption.validation.checkpoint_ci_authority import validate_receipt
    receipt=local/'checkpoint_ci.json';expected=(local/'checkpoint_ci.sha256').read_text().strip()
    ci=validate_receipt(receipt,ci_expectation(),expected_sha256=expected)
    from defensive_network_disruption.validation.r9s_authority import verify_sources
    verify_sources(ROOT)
    return dict(head=git('rev-parse','HEAD'),protocol_sha256=sha(ROOT/PROTOCOL),release=RELEASE,
                implementation={p:sha(ROOT/p) for p in sources},ci_receipt_sha256=ci.receipt_sha256)

_SEAL=object()
class Permit:
    def __init__(self,seal):
        if seal is not _SEAL:raise PermissionError('access_authority')
        self.seal=seal

def unlock(environment,controls,publication):
    if not environment.get('ci_receipt_sha256') or len(controls)!=10 or not all(x['passed'] for x in controls) or not all(publication['flags'].values()):raise PermissionError('acceptance_failed')
    return Permit(_SEAL)

def selected(local,permit):
    if type(permit)is not Permit or permit.seal is not _SEAL:raise PermissionError('direct_entry')
    from defensive_network_disruption.validation import r9s_authority as a
    a.verify_sources(ROOT)
    put(local/'access_attempt.json',dict(schema_version=1,source_sha256=a.SOURCES['selected'][2]))
    records={}
    for label,(directory,name,h) in a.SOURCES.items():
        raw=(ROOT/directory/name).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=h:raise ValueError('source_changed')
        write(local/'retained'/f'{label}.json',raw)
        if label!='selected':records[label]=json.loads(raw)
    row=json.loads((local/'retained/selected.json').read_bytes())
    # A geometry receipt precedes subsequent verification; later rejection must
    # retain actual exposure, even if authority construction fails.
    put(local/'access_materialized.json',dict(schema_version=1,attempt_sha256=sha(local/'access_attempt.json'),selected_sha256=sha(local/'retained/selected.json')))
    return row,records

def publication_controls(folder):
    # Unchanged provider-free controls and observer-only review counter.
    import importlib.util
    spec=importlib.util.spec_from_file_location('r9s_inherited_controls',ROOT/'scripts/session_14r9r_switch_localization_repair.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    from unittest.mock import patch
    from defensive_network_disruption.validation import r9j_linear_publication as linear
    with patch.object(linear,'review',wraps=linear.review) as review:
        rows,summary=module.publication_controls(folder)
    summary['counts']['linear_reviews']=review.call_count
    return rows,summary

def retained(local,permit,save,deadline):
    from defensive_network_disruption.geometry import r9s_trace as t
    from defensive_network_disruption.geometry.occlusion_fields import CarrierOriginField,validate_geometry,points
    from defensive_network_disruption.geometry.r9q_diagnosis import deadline_limit
    from defensive_network_disruption.validation.r9s_acceptance import collect
    from defensive_network_disruption.validation import r9o_terminal as terminal
    from defensive_network_disruption.validation.r7_execution import Progress
    from defensive_network_disruption.validation.r5_persistence import Journal
    journal=Journal(local/'diagnostic_journal.jsonl');p=Progress(journal)
    state,edge='selected_state','selected_edge';p.authorize_access();p.discover_state(state,(edge,))
    try:
        row,records=p.project(state,lambda:selected(local,permit))
        from defensive_network_disruption.validation import r9s_authority as source
        source.geometry_match(records,row)
        args,reference,structures=source.context(records)
        put(local/'invocation_authority.json',dict(arguments=args,reference=reference,structures=structures))
        p.prepare_state(state);p.start_state(state)
        journal.append('diagnostic_started',state=state,edge=edge,candidate='expanding');p.context=(state,edge,'expanding')
        p.numerical_stage(stage='geometry')
        base,defence,_=validate_geometry(row['carrier'],row['defenders']);end=points(row['receiver'],one=True)
        field=CarrierOriginField('expanding')
        def function(ts):
            return field.individual_values(base,defence,base[None,:]+ts[:,None]*(end-base)[None,:])
        with deadline_limit(min(deadline,time.monotonic()+600)),warnings.catch_warnings():
            warnings.simplefilter('error')
            trace,error,result=collect(function,tuple(args['pair']),*map(t.fraction,args['enclosure']),
               *map(t.number,args['outer']),args['before'],args['after'],reference,structures,save,deadline=min(deadline,time.monotonic()+600))
        # Persist original exception before any analysis or normal publication.
        if error is None:
            try:raise RuntimeError('expected_rejection_not_reproduced')
            except RuntimeError as caught:error=caught
        closure=terminal.TerminalClosure(p,local/'numerical_failure')
        def publish(authority,path):
            terminal.numerical_package(local/'numerical_publication',authority,path)
            put(local/'closure_validation.json',dict(validated=True,authority_sha256=sha(local/'numerical_failure/linear_authority.json'),traceback_sha256=sha(path)))
        closure.fail(error,'binary64_transition_inspection',publish)
        put(local/'trace.json',trace)
        return t.summarize(trace,retained=True)
    except BaseException as error:
        if not (local/'numerical_failure/terminal.marker').exists():
            terminal.TerminalClosure(p,local/'numerical_failure').fail(error,'binary64_transition_inspection',
               lambda a,t:terminal.numerical_package(local/'numerical_publication',a,t))
        raise
    finally:journal.close()

def diagnose(folder=OUT):
    folder=Path(folder);local=folder/'local';wall=time.monotonic();cpu=time.process_time()
    environment=preflight(folder)
    put(local/'diagnosis.marker',dict(reserved=True,authorizes_access=False))
    from defensive_network_disruption.validation import r9s_evidence as e,r9s_acceptance as acceptance
    from defensive_network_disruption.validation.checkpoint_ci_authority import FailureController
    serial=0;io=0.;io_cpu=0.;controls=[];pub=None;valid=True;reason='complete';numeric=0.
    def save(label,value):
        nonlocal serial,io,io_cpu
        start=time.monotonic();c=time.process_time();path=local/'observations'/f'{serial:06d}_{label}.json';serial+=1
        put(path,value);h=sha(path);io+=time.monotonic()-start;io_cpu+=time.process_time()-c
        return h
    put(local/'authority.json',environment)
    try:
        controls=acceptance.controls(save)
        rows,pub=publication_controls(local/'publication_controls')
        put(local/'publication_observations.json',dict(rows=rows,summary=pub))
        permit=unlock(environment,controls,pub)
        put(local/'numerical.marker',dict(reserved=True,authorizes_access=False))
        start=time.monotonic()
        try:retained(local,permit,save,wall+3600)
        finally:numeric=time.monotonic()-start
    except BaseException as error:
        FailureController(local/'outer_failure').capture(error,'diagnostic_execution')
        valid=False;reason='timeout' if isinstance(error,TimeoutError) else 'execution_failure'
    put(local/'controls.json',controls)
    elapsed=time.monotonic()-wall;compute=max(0.,time.process_time()-cpu-io_cpu)
    put(local/'outcome.json',dict(schema_version=1,execution_valid=valid,reason=reason,
        timings=dict(governed_wall=elapsed,exclusive_compute=compute,inclusive_numerical=numeric,
                     io=io,waiting=0.,unattributed=max(0.,elapsed-compute-io))))
    return e.close(folder)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=('preflight','diagnose','publication-check'));args=parser.parse_args()
    try:
        if args.command=='preflight':result=preflight()
        elif args.command=='diagnose':result=diagnose()
        else:
            from defensive_network_disruption.validation.r9s_evidence import publication_check
            result=publication_check(OUT)
        print(json.dumps(result,sort_keys=True,allow_nan=False))
    except BaseException as error:
        if args.command=='diagnose' and not isinstance(error,FileExistsError):
            try:
                raw=''.join(traceback.format_exception(error)).encode();write(OUT/'local/outer_traceback.txt',raw)
                put(OUT/'local/outer_failure.json',dict(exception=type(error).__name__,stage='startup_or_closure',traceback_sha256=hashlib.sha256(raw).hexdigest()))
            except BaseException:pass
        raise
if __name__=='__main__':main()
