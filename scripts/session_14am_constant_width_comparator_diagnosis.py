#!/usr/bin/env python3
"""14am one-edge diagnostic execution; no scientific-summary route."""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import platform
import resource
import subprocess
import sys
import tempfile
import time
import traceback

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import numpy as np
import scipy
from defensive_network_disruption.geometry import comparator_reproduction as diagnosis
from defensive_network_disruption.geometry import onset_owner_certification as owner
from defensive_network_disruption.geometry.diagnostic_serialization import canonical_bytes, project_evidence
from defensive_network_disruption.geometry.micro_interval_verifier import point_interval_distance, interval_distance
from defensive_network_disruption.geometry.occlusion_fields import CarrierOriginField
from defensive_network_disruption.geometry.verification_audit import scalar_oracle
from defensive_network_disruption.validation.empirical_switch_diagnosis import project_prepared_edge, project_canonical_edge, selective_bytes
from defensive_network_disruption.validation.r5_persistence import durable_write, Journal, read_journal

START='94092788770b32638ea4dc748c70e2a593436ed1'
TAG='f00690c05d8c1c6db308a65bd311c43f9a8ef2fa'
PROTOCOL='docs/protocols/phase_14am_constant_width_comparator_diagnosis.md'
SOURCES=(PROTOCOL,'scripts/session_14am_constant_width_comparator_diagnosis.py',
         'src/defensive_network_disruption/geometry/comparator_reproduction.py',
         'tests/test_session14am_diagnosis.py')
OUT=ROOT/'outputs/session14am_constant_width_comparator_diagnosis'
PREPARED='outputs/continuous_occlusion_retry_14r8/local/prepared.jsonl'
CANONICAL='outputs/receiver_ranking_m0_m1/local/population.jsonl'
JOURNAL='outputs/continuous_occlusion_retry_14r8/local/journal.jsonl'
ORIGINAL='outputs/continuous_occlusion_retry_14r8/local/original_failure.json'
EMERGENCY='outputs/continuous_occlusion_retry_14r8/local/emergency_failure.json'
BINDINGS={PREPARED:'15a809060f0ba4a8cb3790011dab8008db3dad6e931c287ccb395f61ef1530b0',
 CANONICAL:'cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d',
 JOURNAL:'10b5aa8769458c8695f74028e4cb278aad9edf5740e35c978695758cef54446e',
 ORIGINAL:'ef1e465ab78318f42e1fb10a3e173a4e342649c3f3ea529144934d117b47550a',
 EMERGENCY:'39d8061948ff04975812380eddcb1fca796f19d07fbfb20b5a0eaa57927be3d0'}
NAMES=('serializer_preflight.json','retained_failure_authority.json','topology_summary.json',
 'partition_audit.json','unsplit_convergence.csv','piecewise_convergence.csv','production_path.json',
 'onset_neighborhood.csv','piece_contributions.csv','agreement_gate_replay.json','stopping_logic.json',
 'runtime_breakdown.json','synthetic_reproduction.json','journal_replay_profile.json',
 'publication_options.json','emergency_record_check.json')
CSV_FIELDS=('item','status','reason','private_evidence_sha256')

def git(*args):
    return subprocess.check_output(('git',*args),cwd=ROOT,text=True).strip()

def sha(path):
    path=Path(path)
    if any(p.is_symlink() for p in (path,*path.parents)):raise PermissionError('symlink')
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def put(path,value):
    # Use the unchanged 14al projection and historical durable canonical writer.
    durable_write(Path(path),project_evidence(value))

def load(path):
    def pairs(items):
        result={}
        for k,v in items:
            if k in result:raise ValueError('duplicate_json_key')
            result[k]=v
        return result
    return json.loads(Path(path).read_bytes(),object_pairs_hook=pairs,
                      parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite')))

def claim(path):
    put(path,{'session':'14am','exclusive':True})

def preflight():
    if git('status','--porcelain'):raise RuntimeError('dirty_tree')
    git('merge-base','--is-ancestor',START,'HEAD')
    if git('rev-parse','v0.1.0^{}')!=TAG:raise RuntimeError('release_changed')
    if Path(sys.prefix).resolve()!=(ROOT/'.venv').resolve():raise RuntimeError('locked_environment_required')
    for p in SOURCES:
        if subprocess.check_output(('git','show','HEAD:'+p),cwd=ROOT)!=(ROOT/p).read_bytes():
            raise RuntimeError('uncommitted_implementation')
    # Bind committed history without opening any historical private product.
    changed=git('diff','--name-only',START,'HEAD').splitlines()
    if any(p not in SOURCES and not p.startswith('outputs/session14am_') and
           p not in ('docs/research_log.md','docs/session_14am_constant_width_comparator_diagnosis.md') for p in changed):
        raise RuntimeError('historical_change')
    historical=[p for p in git('ls-tree','-r','--name-only',START).splitlines()
        if p.startswith('src/') or ('14r8' in p or '14ak' in p or '14al' in p) and p.endswith(('.py','.md','manifest.json'))]
    return dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,
                architecture=platform.machine(),system=platform.system(),lock_sha256=sha(ROOT/'uv.lock'),
                historical_authority={p:sha(ROOT/p) for p in historical},
                implementation_commit=git('rev-parse','HEAD'),
                authority={p:sha(ROOT/p) for p in SOURCES})

def synthetic_payload():
    from defensive_network_disruption.geometry.verification_repair import VerifiedEnvelope,VerifiedSwitch,CertifiedBoundary,CertifiedTieInterval
    from defensive_network_disruption.geometry.root_partition_determinism import CertifiedOnset,CertifiedRootTransition
    from defensive_network_disruption.geometry.micro_interval_verifier import IntegralInterval
    boundary=CertifiedBoundary(.25,float(np.nextafter(.25,1.)),'entry',(0,1),(0,1))
    switch=VerifiedSwitch(.5,(0,),(0,1),(1,),((0,1),),False,False,.75)
    witness=owner.OwnerWitness(.25,.4999999,.5,.5000001,.75,(0,),(0,1),(1,))
    structure=((CertifiedOnset(0,0,.25,float(np.nextafter(.25,0.)),.25),),
        VerifiedEnvelope((switch,),(CertifiedTieInterval(boundary,None,(0,1),((0,1),)),),(0,1),(0.,.25,.5,1.),65536),
        (0.,.25,.5,1.),(CertifiedRootTransition(.5,float(np.nextafter(.5,0.)),None,None,.5,(0,),(0,1),(1,),((0,1),)),),(witness,))
    return dict(structure=diagnosis.structure_record(structure),
                strict=IntegralInterval(.2,.20000000000001,1e-14,3,2,1),
                joint=dict(intervals=512,estimates={'individual_1':.2,'union':.2,'maximum':.2},change=1e-8),
                convergence=[dict(intervals=n,estimate=.2,contributions=[.1,.1]) for n in diagnosis.LADDER],
                partition=dict(passed=True,pieces=3),runtime=dict(exclusive_seconds=.01,inclusive_seconds=.02),
                journal=dict(records=16,prefix_visits=136),gate=dict(condition=False,reason='piecewise_unsplit'))

def serializer_preflight(folder):
    value=synthetic_payload(); a=canonical_bytes(value);b=canonical_bytes(value)
    if a!=b:raise RuntimeError('serializer_nondeterminism')
    put(folder/'payload.json',value)
    h=sha(folder/'payload.json')
    put(folder/'manifest.json',dict(payload_sha256=h,accepted=True))
    if load(folder/'manifest.json')['payload_sha256']!=h or (folder/'payload.json').read_bytes()!=a:
        raise RuntimeError('serializer_closure')
    return dict(passed=True,payload_sha256=h,deterministic=True)

class Evidence:
    def __init__(self,folder):
        self.folder=folder;self.files={};self.serial=0;self.io_seconds=0.;self.io_cpu=0.;self.journal=None
    def save(self,label,data):
        started=time.perf_counter();cpu=time.process_time()
        name=f'{self.serial:06d}_{label}.json';self.serial+=1
        put(self.folder/name,data);h=sha(self.folder/name);self.files[name]=h
        self.io_seconds+=time.perf_counter()-started
        self.io_cpu+=time.process_time()-cpu
        return h

def selected_line(path):
    with path.open('rb') as f:
        for i,line in enumerate(f):
            if i==4:return line.decode('utf-8')
    raise ValueError('missing_retained_ordinal')

def check_location(state,receiver,candidate):
    if type(state) is not int or type(receiver) is not int or (state,receiver,candidate)!=(4,7,'constant_width'):
        raise PermissionError('retained_edge_only')

def open_edge(evidence,journal):
    check_location(4,7,'constant_width')
    journal.append('access_attempt',product='prepared',state=4,receiver=7)
    a=project_prepared_edge(selected_line(ROOT/PREPARED),7)
    journal.append('access_materialized',product='prepared',state=4,receiver=7)
    journal.append('access_attempt',product='canonical',state=4,receiver=7)
    b=project_canonical_edge(selected_line(ROOT/CANONICAL),7)
    journal.append('access_materialized',product='canonical',state=4,receiver=7)
    if selective_bytes(a)!=selective_bytes(b):raise RuntimeError('selected_serialization_mismatch')
    evidence.save('selected_geometry',a)
    return a

def unavailable():
    return {n:dict(status='unavailable',reason='not_executed',data={}) for n in NAMES}

def result(data):return dict(status='available',reason=None,data=data)

def close(folder,public,qc,private,environment):
    for name in NAMES:
        item=public[name]
        if name.endswith('.csv'):
            s=io.StringIO(newline='');w=csv.DictWriter(s,fieldnames=CSV_FIELDS,lineterminator='\n');w.writeheader()
            w.writerow(dict(item=name.removesuffix('.csv'),status=item['status'],reason=item['reason'] or 'exact_values_private',
                            private_evidence_sha256=qc['private_index_sha256']))
            p=folder/name;temp=p.with_name('.'+p.name+'.pending')
            with temp.open('xb') as f:f.write(s.getvalue().encode());f.flush();os.fsync(f.fileno())
            os.link(temp,p);temp.unlink()
        else:put(folder/name,dict(schema_version=1,**item))
    put(folder/'qc.json',qc)
    put(folder/'manifest.json',dict(schema_version=1,status=qc['status'],qc_sha256=sha(folder/'qc.json'),
        private_index_sha256=qc['private_index_sha256'],outputs={n:sha(folder/n) for n in (*NAMES,'qc.json')},
        authority=environment))
    publication_check(folder)

def publication_check(folder=OUT):
    m=load(folder/'manifest.json');q=load(folder/'qc.json')
    if set(m)!={'schema_version','status','qc_sha256','private_index_sha256','outputs','authority'}:raise ValueError('manifest_schema')
    if set(q)!={'schema_version','status','execution_valid','numerical','readiness','publication','outcome','reproduced',
                'states_opened','edges_opened','exposure_uncertain','private_index_sha256'}:raise ValueError('qc_schema')
    if q['numerical'] not in 'ABCDEFGHI' or q['readiness'] not in (1,2,3,4) or q['publication'] not in ('P1','P2','P3','P4','P5'):
        raise ValueError('classification')
    if set(m['outputs'])!=set((*NAMES,'qc.json')):raise ValueError('output_members')
    if m['status']!=q['status'] or m['private_index_sha256']!=q['private_index_sha256'] or m['qc_sha256']!=sha(folder/'qc.json'):
        raise ValueError('cross_file')
    if q['numerical'] in 'ABCDEFG' and (not q['reproduced'] or not q['execution_valid']):raise ValueError('false_acceptance')
    if q['status'] not in ('closed','invalid') or q['execution_valid']!=(q['status']=='closed'):
        raise ValueError('execution_status')
    if any(type(q[k]) is not bool for k in ('execution_valid','reproduced','exposure_uncertain')):
        raise ValueError('boolean_schema')
    if (q['states_opened'],q['edges_opened']) not in ((0,0),(1,1)):raise ValueError('access_count')
    for n,h in m['outputs'].items():
        if sha(folder/n)!=h:raise ValueError('output_hash')
        if n.endswith('.json') and n!='qc.json':
            record=load(folder/n)
            if set(record)!={'schema_version','status','reason','data'} or record['schema_version']!=1 or record['status'] not in ('available','unavailable'):
                raise ValueError('evidence_schema')
            if record['status']=='unavailable' and (not record['reason'] or record['data']):raise ValueError('unavailable_schema')
        elif n.endswith('.csv'):
            with (folder/n).open(newline='') as f:
                reader=csv.DictReader(f);rows=list(reader)
            if reader.fieldnames!=list(CSV_FIELDS) or len(rows)!=1 or rows[0]['private_evidence_sha256']!=q['private_index_sha256']:
                raise ValueError('csv_schema')
    index=folder/'local/private_index.json'
    if sha(index)!=q['private_index_sha256']:raise ValueError('private_index')
    for n,h in load(index)['files'].items():
        if Path(n).name!=n or sha(folder/'local'/n)!=h:raise ValueError('private_file')
    journal=folder/'local/access.jsonl'
    if journal.exists():
        records,_=read_journal(journal)
        attempts=[x['payload'] for x in records if x['action']=='access_attempt']
        opened=[x['payload'] for x in records if x['action']=='access_materialized']
        if q['states_opened']!=int(bool(opened)) or q['edges_opened']!=int(bool(opened)) or q['exposure_uncertain']!=(attempts!=opened):
            raise ValueError('access_evidence_mismatch')
    elif q['states_opened'] or q['edges_opened'] or q['exposure_uncertain']:
        raise ValueError('missing_access_evidence')
    if q['reproduced']:
        gate=load(folder/'agreement_gate_replay.json')
        if gate['status']!='available' or gate['data'].get('reproduced') is not True or gate['data'].get('actual_r8_route') is not True:
            raise ValueError('missing_reproduction_evidence')
    if q['numerical']=='A':
        prod=load(folder/'production_path.json');checks=prod['data'].get('checks',{})
        if prod['status']!='available' or any(checks.get(k) is not True for k in
           ('reference_eligible','strict_repeat','joint_maximum','direct_gate','production_reference','piecewise_reference')) or checks.get('unsplit_reference') is not False:
            raise ValueError('healthy_path_unestablished')
    for n in (*NAMES,'qc.json','manifest.json'):
        text=(folder/n).read_text()
        if any(x in text for x in ('/Users/','/private/','"carrier"','"defenders"','"traceback"')):raise ValueError('privacy')
    return True

def diagnose():
    OUT.mkdir(parents=True,exist_ok=True);local=OUT/'local';local.mkdir(exist_ok=True)
    claim(local/'attempt.marker')
    budget=diagnosis.Budget();cpu_start=time.process_time();e=Evidence(local);p=unavailable();env={};journal=None
    numerical='H';readiness=4;publication='P5';valid=True;reproduced=False;outcome='unresolved'
    try:
        env=preflight()
        p['serializer_preflight.json']=result(serializer_preflight(local/'serializer'))
        e.save('serializer_acceptance',p['serializer_preflight.json'])
        profiles=[]
        for n in (16,32,64,128,256,512,1024):
            prof=diagnosis.profile_replay(diagnosis.synthetic_journal(n),budget)
            prof['states']=n;e.save('journal_profile',prof);profiles.append(prof)
            if prof['rejection'] is not None:raise RuntimeError('synthetic_journal_rejected')
        p['journal_replay_profile.json']=result(dict(profiles=profiles,historical_shape_status='not_yet_executed',
            runtime_extrapolation=False,complexity_basis='observed_prefix_visits'))
        publication='P1' if all(x['triangular'] for x in profiles) else 'P5'
        for path,expected in BINDINGS.items():
            if sha(ROOT/path)!=expected:raise RuntimeError('retained_hash_changed')
        e.save('input_authority',BINDINGS)
        original=load(ROOT/ORIGINAL);emergency=load(ROOT/EMERGENCY)
        if original.get('exception')!='GateFailure' or 'piecewise_unsplit' not in original.get('traceback',''):
            raise RuntimeError('retained_failure_not_unique')
        if original.get('context')!=['4','7','constant_width']:raise RuntimeError('retained_context_mismatch')
        e.save('retained_failure',dict(original=original,emergency=emergency))
        journal=Journal(local/'access.jsonl');journal.append('authorized',state=4,receiver=7,candidate='constant_width')
        row=open_edge(e,journal)
        p['retained_failure_authority.json']=result(dict(selected_serialization_verified=True,gate='piecewise_unsplit',
            historical_estimates_available=False,input_hashes=BINDINGS))
        b=np.asarray(row['carrier']);r=np.asarray(row['receiver']);ds=np.asarray(row['defenders'])
        reproduced,obs,durations=diagnosis.reproduce(b,r,ds,e.save,budget)
        p['agreement_gate_replay.json']=result(dict(actual_r8_route=True,reproduced=reproduced,
            absolute_tolerance=1e-10,relative_tolerance=0.,simpson_resolution_applicable=False))
        if not reproduced:
            outcome='exact_failure_not_reproduced'
        else:
            outcome='failure_reproduced'
            structure=obs.saved['structure'];audit=diagnosis.partition_audit(structure)
            p['partition_audit.json']=result(audit)
            p['topology_summary.json']=result({k:audit[k] for k in ('pieces','bounded','onset_count','switch_count','tie_count')})
            if not audit['passed']:
                numerical='D';readiness=3
            else:
                field=CarrierOriginField('constant_width')
                def function(t):return field.individual_values(b,ds,b[None,:]+np.asarray(t)[:,None]*(r-b)[None,:])
                uniform,pieces=diagnosis.convergence(function,structure[2],budget,e.save)
                reference=diagnosis.reference_eligible(audit,pieces)
                with budget.limit():direct=diagnosis.maximum_simpson(function,65536)
                strict,repeat=obs.saved['strict'],obs.saved['repeat'];unsplit=obs.saved['onset_adaptive']
                count,estimates,change=obs.saved['controlled_vector']
                health=dict(reference_eligible=reference,strict_repeat=interval_distance(strict,repeat)<=1e-10,
                    joint_maximum=point_interval_distance(estimates['maximum'],strict)<=1e-6,
                    direct_gate=point_interval_distance(direct,strict)<=1e-9,
                    production_reference=None if not reference else abs(estimates['maximum']-pieces[-1]['estimate'])<=1e-6,
                    piecewise_reference=None if not reference else point_interval_distance(pieces[-1]['estimate'],strict)<=1e-10,
                    unsplit_reference=None if not reference else abs(unsplit-pieces[-1]['estimate'])<=1e-10)
                health={k:None if v is None else bool(v) for k,v in health.items()}
                e.save('independent_comparisons',dict(health=health,direct=direct,reference=pieces[-1]['estimate'],
                    production_difference=estimates['maximum']-pieces[-1]['estimate'],
                    unsplit_difference=unsplit-pieces[-1]['estimate']))
                p['production_path.json']=result(dict(provisional=True,accepted_intervals=count,converged=change<=1e-7,checks=health))
                p['unsplit_convergence.csv']=result({});p['piecewise_convergence.csv']=result({});p['piece_contributions.csv']=result({})
                neighborhoods=[]
                for onset in structure[0]:
                    samples=[]
                    for t in (np.nextafter(onset.canonical,-math.inf),onset.canonical,np.nextafter(onset.canonical,math.inf)):
                        values=function(np.array([t]))[0];q=b+t*(r-b)
                        oracle=np.array([scalar_oracle('constant_width',b,d,q) for d in ds])
                        if not np.allclose(values,oracle,atol=1e-12,rtol=1e-12):raise RuntimeError('scalar_oracle_mismatch')
                        samples.append(dict(t=float(t),values=values.tolist(),oracle=oracle.tolist(),owners=owner.owners(values)))
                    slopes=[(max(y['values'])-max(x['values']))/(y['t']-x['t'])
                            for x,y in zip(samples,samples[1:])]
                    neighborhoods.append(dict(defender=onset.defender_index,branch=onset.branch,samples=samples,
                        finite_step_slopes=slopes,continuity_authority='analytical_continuity_of_frozen_fields_and_finite_maximum',
                        slopes_are_not_continuity_proof=True))
                e.save('onset_neighborhood',neighborhoods);p['onset_neighborhood.csv']=result({})
                p['stopping_logic.json']=result(dict(production='joint_vector_delta',adaptive='QUADPACK_tolerances_and_subdivision_limit',
                    gate_after_adaptive_returns=True,adaptive_on_simpson_ladder=False,subdivisions_unavailable=True))
                if reference and all(health[k] for k in ('strict_repeat','joint_maximum','direct_gate','production_reference','piecewise_reference')) and not health['unsplit_reference']:
                    numerical='A';readiness=1
                elif reference and not health['piecewise_reference']:
                    numerical='D';readiness=3
                # Unresolved health remains H; no classification from pairwise disagreement alone.
                records,head=read_journal(ROOT/JOURNAL)
                e.save('journal_metadata',dict(records=len(records),bytes=(ROOT/JOURNAL).stat().st_size,
                    actions=dict(Counter(x['action'] for x in records)),head=head))
                # Preserve historical event order and count, neutralizing identities without geometry.
                mapping={}
                def neutral(value):
                    if isinstance(value,str):
                        if value not in mapping:mapping[value]=f'key_{len(mapping)}'
                        return mapping[value]
                    return value
                shaped=[]
                for rec in records:
                    payload=dict(rec['payload'])
                    for key in ('state','edge','attempt'):
                        if key in payload:payload[key]=neutral(payload[key])
                    if 'edges' in payload:payload['edges']=[neutral(x) for x in payload['edges']]
                    shaped.append(dict(action=rec['action'],payload=payload))
                prof=diagnosis.profile_replay(shaped,budget);e.save('historical_shape_profile',prof);profiles.append(prof)
                publication='P1' if all(x['triangular'] for x in profiles[:-1]) else 'P5'
                p['journal_replay_profile.json']=result(dict(profiles=profiles,historical_records=len(records),
                    historical_bytes=(ROOT/JOURNAL).stat().st_size,peak_rss_platform_units=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                    runtime_extrapolation=False,complexity_basis='observed_prefix_visits'))
                p['publication_options.json']=result(dict(implemented=False,preferred='one_pass_validation_with_authenticated_checkpoints',
                    alternatives=['streaming_validation','authenticated_incremental_summary','checkpoints_suffix','indexed_validation']))
                p['emergency_record_check.json']=result(dict(original_gate_reference=True,
                    publication_exception_preserved=bool(emergency.get('publication_exception')),
                    traceback_preserved=bool(emergency.get('traceback')),normal_publication=False))
        p['synthetic_reproduction.json']=result(dict(status='documented_only',executed_after_access=False))
    except diagnosis.DiagnosticTimeout as error:
        outcome='budget_exhausted';numerical='H';readiness=4
        e.save('timeout',dict(exception=type(error).__name__,traceback=traceback.format_exc(),
            partial_operation=getattr(error,'diagnostic_evidence',None)))
    except BaseException as error:
        valid=False;numerical='I';readiness=4;outcome='execution_defect'
        put(local/'emergency.json',dict(exception=type(error).__name__,traceback=traceback.format_exc(),
             available_files=dict(e.files),accepted=False))
        e.files['emergency.json']=sha(local/'emergency.json')
    finally:
        if journal is not None:journal.close()
    # Always close from the actually persisted receipts; an unmatched attempt is uncertain.
    access=[]
    if (local/'access.jsonl').exists():
        access=read_journal(local/'access.jsonl')[0];e.files['access.jsonl']=sha(local/'access.jsonl')
    attempts=sum(x['action']=='access_attempt' for x in access)
    opens=sum(x['action']=='access_materialized' for x in access)
    wall=time.monotonic()-budget.started
    compute=max(0.,time.process_time()-cpu_start-e.io_cpu)
    # Process CPU is non-overlapping; do not sum nested profiler durations.
    remainder=wall-compute-e.io_seconds
    p['runtime_breakdown.json']=result(dict(governed_wall_seconds=wall,
        measured_io_seconds=e.io_seconds,exclusive_compute_seconds=compute,nested_inclusive_times_private=True,
        waiting_seconds=None,unattributed_overhead_seconds=remainder,
        reconciliation='process_CPU_less_measured_persistence_CPU_plus_persistence_wall_plus_unattributed_remainder; waiting_not_separately_instrumented',
        historical_55_minutes_attribution='unavailable',operation_cap=600,total_cap=3600))
    put(local/'private_index.json',dict(files=e.files))
    q=dict(schema_version=1,status='closed' if valid else 'invalid',execution_valid=valid,numerical=numerical,
           readiness=readiness,publication=publication,outcome=outcome,reproduced=reproduced,
           states_opened=int(opens>0),edges_opened=int(opens>0),exposure_uncertain=attempts!=opens,
           private_index_sha256=sha(local/'private_index.json'))
    try:close(OUT,p,q,e.files,env)
    except BaseException as error:
        put(local/'publication_emergency.json',dict(exception=type(error).__name__,traceback=traceback.format_exc(),accepted=False))
        raise
    print(json.dumps(q,sort_keys=True))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=('preflight','diagnose','publication-check'))
    command=parser.parse_args().command
    if command=='preflight':print(json.dumps(preflight(),sort_keys=True))
    elif command=='diagnose':diagnose()
    else:print('verified' if publication_check() else 'invalid')

if __name__=='__main__':main()
