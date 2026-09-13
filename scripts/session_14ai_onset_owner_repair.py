#!/usr/bin/env python3
"""One-shot 14ai acceptance and gated single-edge regression."""
import argparse
import csv
from dataclasses import asdict,is_dataclass
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import traceback

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from defensive_network_disruption.validation.r5_persistence import Journal,durable_write,read_journal,digest as object_hash
from defensive_network_disruption.validation import numerical_failure_publication as pub
from defensive_network_disruption.validation.onset_owner_acceptance import topology_oracles,publication_controls,historical_regression

START='73f72b1d6b0556660594abc22b031a625a4e04c5'
TAG='f00690c05d8c1c6db308a65bd311c43f9a8ef2fa'
PROTOCOL='docs/protocols/phase_14ai_onset_aware_owner_certification.md'
OUT=ROOT/'outputs/session14_onset_owner_repair';LOCAL=OUT/'local'
CODE=('src/defensive_network_disruption/geometry/onset_owner_certification.py',
 'src/defensive_network_disruption/validation/numerical_failure_publication.py',
 'src/defensive_network_disruption/validation/onset_owner_acceptance.py',
 'scripts/session_14ai_onset_owner_repair.py','tests/test_session14ai_contracts.py')
JSON_KEYS={
 'owner_contract.json':{'rule','coincidence_policy','history_expected'},
 'empirical_edge_regression.json':{'available','states_opened','edges_opened','reason','evidence_sha256'},
 'numerical_health.json':{'available','intervals','oracle_verified','maximum_verified'},
 'publication_contract.json':{'stages','schema_version','separate_diagnostic_work'},
 'publication_valid_control.json':{'controls'},
 'publication_failure_closure.json':{'controls'},
 'qc.json':{'checks','accepted','real_states_opened','real_edges_opened','authority','private_package_sha256'}}
CSV_KEYS={
 'synthetic_topology_oracles.csv':('fixture','expected','observed','passed'),
 'historical_switch_regression.csv':('fixture','candidate','passed','components','permutations','error'),
 'publication_negative_controls.csv':('fixture','expected_acceptance','accepted','passed')}


def safe(path):
    path=Path(path)
    if not path.is_absolute():path=ROOT/path
    if not path.resolve().is_relative_to(ROOT.resolve()) or any(p.is_symlink() for p in (path,*path.parents)):
        raise PermissionError('unsafe_path')
    return path


def sha(path):
    h=hashlib.sha256()
    with safe(path).open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()


def git(*args):return subprocess.check_output(('git',*args),cwd=ROOT,text=True).strip()


def encode(x):return (json.dumps(x,sort_keys=True,allow_nan=False,indent=2)+'\n').encode()


def plain(x):
    if is_dataclass(x):return plain(asdict(x))
    if isinstance(x,dict):return {str(k):plain(v) for k,v in x.items()}
    if isinstance(x,(tuple,list)):return [plain(v) for v in x]
    return x


def write(path,value):durable_write(safe(path),value)


def atomic_bytes(path,content):
    path=safe(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name('.'+path.name+'.pending')
    with tmp.open('xb') as f:f.write(content);f.flush();os.fsync(f.fileno())
    os.link(tmp,path);tmp.unlink()


def csv_write(name,rows):
    buffer=io.StringIO(newline='');w=csv.DictWriter(buffer,fieldnames=CSV_KEYS[name],lineterminator='\n')
    w.writeheader();w.writerows(rows);atomic_bytes(OUT/name,buffer.getvalue().encode())


def read(path):
    def pairs(items):
        d={}
        for k,v in items:
            if k in d:raise ValueError('duplicate_key')
            d[k]=v
        return d
    return json.loads(safe(path).read_text(),object_pairs_hook=pairs,
        parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite')))


def preflight():
    if git('status','--porcelain'):raise RuntimeError('dirty_tree')
    git('merge-base','--is-ancestor',START,'HEAD')
    if git('rev-parse','v0.1.0^{}')!=TAG:raise RuntimeError('release_changed')
    if Path(sys.prefix).resolve()!=(ROOT/'.venv').resolve():raise RuntimeError('project_environment_required')
    import numpy,scipy
    for path,expected in re.findall(r'- `([^`]+)`: `([0-9a-f]{64})`',safe(PROTOCOL).read_text()):
        if sha(path)!=expected:raise RuntimeError('historical_binding_changed')
    for p in (*CODE,PROTOCOL,'uv.lock'):
        committed=subprocess.check_output(('git','show','HEAD:'+p),cwd=ROOT)
        if hashlib.sha256(committed).hexdigest()!=sha(p):raise RuntimeError('uncommitted_binding')
    return {'python':platform.python_version(),'numpy':numpy.__version__,'scipy':scipy.__version__,'lock_sha256':sha('uv.lock')}


def empirical(journal):
    from defensive_network_disruption.validation.empirical_switch_diagnosis import project_prepared_edge,project_canonical_edge,selective_bytes
    from defensive_network_disruption.geometry.onset_owner_certification import evaluate
    from defensive_network_disruption.geometry.verification_audit import scalar_oracle
    import numpy as np
    files=(('outputs/continuous_occlusion_retry_14r6/local/prepared.jsonl','15a809060f0ba4a8cb3790011dab8008db3dad6e931c287ccb395f61ef1530b0'),
           ('outputs/receiver_ranking_m0_m1/local/population.jsonl','cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d'))
    oldpath='outputs/session14_empirical_switch_owner_diagnosis/local/exact_evidence.json'
    if sha(oldpath)!='fb4d4083c9c245176f83a710f4359d8d0a034b4147192f78151f55a865064f7a':raise RuntimeError('historical_evidence_hash')
    for p,h in files:
        if sha(p)!=h:raise RuntimeError('input_hash')
    journal.append('access_authorized');journal.append('state_discovered',state='authorized_state',edges=['authorized_edge'])
    journal.append('projection_attempt',state='authorized_state',attempt='authorized_projection')
    selected=[];line_hashes=[]
    for (p,_),projector in zip(files,(project_prepared_edge,project_canonical_edge),strict=True):
        with safe(p).open('rb') as f:
            for i,line in enumerate(f):
                if i==2:break
            else:raise RuntimeError('authorized_ordinal_missing')
        line_hashes.append(hashlib.sha256(line).hexdigest());selected.append(projector(line.decode(),8))
    journal.append('projection_materialized',attempt='authorized_projection',edges=['authorized_edge'])
    if selective_bytes(selected[0])!=selective_bytes(selected[1]):raise RuntimeError('selected_projection_mismatch')
    old=read(oldpath)
    if line_hashes!=[old['prepared_line_sha256'],old['canonical_line_sha256']]:raise RuntimeError('line_identity')
    if hashlib.sha256(selective_bytes(selected[0])).hexdigest()!=old['selective_projection_sha256']:raise RuntimeError('projection_identity')
    row=selected[0];ctx=dict(state='authorized_state',edge='authorized_edge',candidate='constant_width')
    journal.append('state_prepared',state=ctx['state']);journal.append('state_evaluation_started',state=ctx['state'])
    journal.append('diagnostic_started',**ctx)
    def record(**detail):journal.append('numerical_stage',**ctx,detail=detail)
    result=evaluate('constant_width',row['carrier'],row['receiver'],row['defenders'],record=record)
    if plain(result['onsets'])!=old['diagnostic']['onsets']:raise RuntimeError('historical_onset_changed')
    raw_root=old['diagnostic']['switch']['location']
    if not any(s.raw_solver_result==raw_root for s in result['switches']):raise RuntimeError('historical_raw_root_changed')
    if result['intervals']!=4096:raise RuntimeError('historical_resolution_changed')
    from defensive_network_disruption.geometry.occlusion_fields import CarrierOriginField
    field=CarrierOriginField('constant_width');b=np.array(row['carrier']);end=np.array(row['receiver']);ds=np.array(row['defenders'])
    for saved in old['diagnostic']['rows']:
        q=b+saved['point']*(end-b);values=field.individual_values(b,ds,q[None,:])[0]
        if values.tolist()!=saved['values']:raise RuntimeError('historical_neighborhood_changed')
        oracle=np.array([scalar_oracle('constant_width',b,d,q) for d in ds])
        if not np.allclose(values,oracle,atol=1e-12,rtol=1e-12):raise RuntimeError('scalar_oracle')
    write(LOCAL/'empirical_evidence.json',plain(result))
    journal.append('diagnostic_completed',**ctx);journal.append('diagnostic_success')
    return {'available':True,'states_opened':1,'edges_opened':1,'reason':None,'evidence_sha256':sha(LOCAL/'empirical_evidence.json')}, {'available':True,'intervals':4096,'oracle_verified':True,'maximum_verified':True}


def audit():
    # Immutable outer attempt and emergency coverage precede environment discovery.
    write(LOCAL/'audit.marker',{'session':'14ai'})
    journal=None;before=None;terminal=None;environment=None
    topology=[];controls=[];history=[];checks={};original=None
    empirical_result={'available':False,'states_opened':0,'edges_opened':0,'reason':'pre_access_gates','evidence_sha256':None}
    health={'available':False,'intervals':None,'oracle_verified':None,'maximum_verified':None}
    try:
        environment=preflight()
        journal=Journal(safe(LOCAL/'journal'));journal.append('initialized')
        from defensive_network_disruption.geometry.production_verification import engineering_checks
        engineering=engineering_checks()
        checks['engineering']=bool(engineering) and all(r['passed'] for r in engineering)
        write(LOCAL/'engineering.json',engineering)
        topology=topology_oracles();checks['topology']=all(r['passed'] for r in topology)
        controls=publication_controls();checks['publication_controls']=all(r['passed'] for r in controls)
        if all(checks.values()):
            history=historical_regression(ROOT,lambda row:print('synthetic',row['fixture'],row['candidate'],row['passed'],flush=True))
        checks['historical']=len(history)==108 and all(r['passed'] for r in history)
        if not all(checks.values()):
            journal.append('blocked',stage='synthetic_acceptance',reason='acceptance_gate')
        else:
            empirical_result,health=empirical(journal)
            checks['empirical']=True
        journal.close()
        terminal=pub.authority(LOCAL/'journal',journal.previous)
    except BaseException as exc:
        original=exc
        empirical_result['reason']='audit_failed'
        if journal is not None:
            try:before=pub.authority(LOCAL/'journal',journal.previous)
            except Exception:before=None
            trace=''.join(traceback.format_exception(exc)).encode()
            atomic_bytes(LOCAL/'traceback',trace)
            try:
                snap=None if before is None else before['snapshot'];ctx=None if snap is None else snap['diagnostic_active']
                stage='startup' if snap is None else (snap['numerical_stage'] or 'preparation')
                journal.append('failure',stage=stage,exception=type(exc).__name__,state=ctx[0] if ctx else None,
                  edge=ctx[1] if ctx else None,candidate=ctx[2] if ctx else None,traceback_sha256=hashlib.sha256(trace).hexdigest())
                journal.close();terminal=pub.authority(LOCAL/'journal',journal.previous)
            except Exception:terminal=None
        pub.emergency(LOCAL/'emergency.json',exc,stage='audit',before=before,terminal=terminal)
        checks['execution']=False
    if terminal is None:
        raise RuntimeError('failure_evidence_preserved_no_valid_publication') from original
    counters=terminal['snapshot']['snapshot']['counters']
    empirical_result['states_opened']=int(counters['edges_opened']>0)
    empirical_result['edges_opened']=counters['edges_opened']
    accepted=bool(checks) and all(checks.values()) and empirical_result['available']
    package=pub.package(terminal,accepted=accepted,checks=checks)
    try:
        for name in ('qc','manifest','evidence'):write(LOCAL/'package'/(name+'.json'),package)
        pub.validate_persisted(LOCAL/'package',LOCAL/'journal',journal.previous,
                              traceback_path=LOCAL/'traceback' if original else None)
        payloads={
          'owner_contract.json':{'rule':'structural_region_witnesses','coincidence_policy':'fail_closed','history_expected':[108,366,399]},
          'empirical_edge_regression.json':empirical_result,'numerical_health.json':health,
          'publication_contract.json':{'stages':list(pub.STAGES),'schema_version':2,'separate_diagnostic_work':True},
          'publication_valid_control.json':{'controls':[r for r in controls if r['expected_acceptance']]},
          'publication_failure_closure.json':{'controls':[r for r in controls if not r['expected_acceptance']]},
          'qc.json':{'checks':checks,'accepted':accepted,'real_states_opened':empirical_result['states_opened'],
            'real_edges_opened':counters['edges_opened'],'authority':terminal,
            'private_package_sha256':{n:sha(LOCAL/'package'/(n+'.json')) for n in ('qc','manifest','evidence')}}}
        for name,payload in payloads.items():
            if set(payload)!=JSON_KEYS[name]:raise RuntimeError('output_schema')
            write(OUT/name,{'schema_version':1,**payload})
        csv_write('synthetic_topology_oracles.csv',topology);csv_write('historical_switch_regression.csv',history)
        csv_write('publication_negative_controls.csv',[r for r in controls if not r['expected_acceptance']])
        names=(*JSON_KEYS,*CSV_KEYS)
        write(OUT/'manifest.json',{'schema_version':1,'status':'accepted' if accepted else 'blocked',
            'start':START,'implementation_commit':git('rev-parse','HEAD'),'protocol_sha256':sha(PROTOCOL),
            'implementation':{p:sha(p) for p in CODE},'environment':environment,
            'outputs':{n:sha(OUT/n) for n in names},'snapshot_sha256':terminal['snapshot_sha256'],
            'journal_sha256':terminal['journal_sha256']})
        publication_check()
    except BaseException as exc:
        pub.emergency(LOCAL/'publication_emergency.json',original or exc,stage='publication',before=before,terminal=terminal,publication_error=type(exc).__name__)
        raise
    print('Evidence closed. Accepted:',accepted,flush=True)


def publication_check():
    m=read(OUT/'manifest.json')
    if set(m)!={'schema_version','status','start','implementation_commit','protocol_sha256','implementation','environment','outputs','snapshot_sha256','journal_sha256'}:raise ValueError('manifest_schema')
    if set(m['outputs'])!=set(JSON_KEYS)|set(CSV_KEYS):raise ValueError('manifest_members')
    for p,h in m['implementation'].items():
        if sha(p)!=h:raise ValueError('implementation_hash')
    if sha(PROTOCOL)!=m['protocol_sha256']:raise ValueError('protocol_hash')
    for n,h in m['outputs'].items():
        if sha(OUT/n)!=h:raise ValueError('output_hash')
        if n in JSON_KEYS:
            if set(read(OUT/n))!={'schema_version'}|JSON_KEYS[n]:raise ValueError('output_schema')
        else:
            with (OUT/n).open(newline='') as f:
                if tuple(csv.DictReader(f).fieldnames)!=CSV_KEYS[n]:raise ValueError('csv_schema')
    q=read(OUT/'qc.json');trace=LOCAL/'traceback'
    actual=pub.validate_persisted(LOCAL/'package',LOCAL/'journal',m['journal_sha256'],traceback_path=trace if trace.exists() else None)
    if actual!=q['authority'] or actual['snapshot_sha256']!=m['snapshot_sha256']:raise ValueError('cross_file_authority')
    for n,h in q['private_package_sha256'].items():
        if sha(LOCAL/'package'/(n+'.json'))!=h:raise ValueError('private_package_hash')
    private_q=read(LOCAL/'package/qc.json')
    if q['checks']!=private_q['checks'] or q['accepted']!=private_q['accepted']:raise ValueError('cross_file_checks')
    if (m['status']=='accepted')!=q['accepted']:raise ValueError('cross_file_status')
    if q['real_edges_opened']!=actual['snapshot']['snapshot']['counters']['edges_opened']:raise ValueError('access_mismatch')
    print('Publication integrity validated; acceptance is',q['accepted'])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=('preflight','audit','publication-check'))
    {'preflight':preflight,'audit':audit,'publication-check':publication_check}[p.parse_args().command]()
