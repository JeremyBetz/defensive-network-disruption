#!/usr/bin/env python3
"""Governed synthetic-only production wiring acceptance; no empirical routes."""
from __future__ import annotations

import argparse
import ast
import csv
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
from unittest.mock import patch
import warnings

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
import numpy as np
import scipy
from scipy.integrate import IntegrationWarning
from defensive_network_disruption.geometry import production_verification as p
from defensive_network_disruption.geometry.occlusion_fields import CANDIDATES
from defensive_network_disruption.geometry.verification_repair import VerificationReadiness

START = '8ef0a27ebe9f0ac7ca6b4a754cfa7168c8b34ba5'
TAG = 'f00690c05d8c1c6db308a65bd311c43f9a8ef2fa'
PROTOCOL = 'docs/protocols/phase_14g_production_verification_wiring.md'
CODE = ('scripts/session_14g_production_verification.py',
        'src/defensive_network_disruption/geometry/production_verification.py',
        'tests/test_session14g_production.py')
OUT = Path('outputs/continuous_occlusion_production_verification')
E = Path('outputs/continuous_occlusion_verification_repair')
F = Path('outputs/continuous_occlusion_closure_repair')
B = Path('outputs/continuous_occlusion_numerics_14b')
C = Path('outputs/continuous_occlusion_max_switching')
SOURCES = ('scripts/session_14_occlusion_fields.py', 'uv.lock',
           'src/defensive_network_disruption/geometry/occlusion_fields.py',
           'src/defensive_network_disruption/geometry/integration_review.py',
           'src/defensive_network_disruption/geometry/verification_audit.py',
           'src/defensive_network_disruption/geometry/verification_repair.py',
           'src/defensive_network_disruption/geometry/maximum_envelope.py')
INPUTS = (*SOURCES, str(B/'reference_summary.json'), str(C/'unresolved_case_comparison.csv'),
          str(E/'controlled_integration.csv'), str(E/'reference_comparison.csv'),
          str(E/'manifest.json'), str(F/'manifest.json'))
FILES = ('contract.json','wiring_checks.json','reference_comparison.csv',
         'failure_injection.json','readiness.json','qc.json')
SCHEMAS = {
 'contract.json': {'schema_version','start','protocol_commit','implementation_commit','environment','historical_hashes','implementation_hashes','protocol_hash','integration'},
 'wiring_checks.json': {'schema_version','engineering','cases','stopped_reason'},
 'failure_injection.json': {'schema_version','records','verified'},
 'readiness.json': {'schema_version','inputs','ready','classification'},
 'qc.json': {'schema_version','status','classification','cases_completed','references_completed','permutations_completed','unavailable_cases','unavailable_references','empirical_access','failure'},
 'manifest.json': {'schema_version','status','classification','outputs_sha256','contract_sha256'},
}
CSV_KEYS = ('fixture','candidate','component','intervals','estimate','reference','absolute_error','passed')
PASS = 'PASS — PRODUCTION VERIFICATION PATH ESTABLISHED'
BLOCKED = 'BLOCKED — ADDITIONAL BOUNDED REPAIR REQUIRED'
INVALID = 'INVALID — EXECUTION OR INTEGRITY FAILURE'


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()


def safe(relative):
    relative = Path(relative)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('unsafe_path')
    path = ROOT/relative
    if any(p.is_symlink() for p in (path,*path.parents)) or not path.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError('unsafe_path')
    return path


def digest(relative):
    return hashlib.sha256(safe(relative).read_bytes()).hexdigest()


def approved_input(relative):
    if str(relative) not in INPUTS:
        raise ValueError('unapproved_input')
    return safe(relative)


def no_duplicates(pairs):
    result = {}
    for key,value in pairs:
        if key in result: raise ValueError('duplicate_key')
        result[key] = value
    return result


def read_json(path):
    return json.loads(path.read_text(),object_pairs_hook=no_duplicates,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite_json')))


def environment():
    return {'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,
            'uv_lock_sha256':digest('uv.lock')}


def historical_preservation():
    changes = git('diff','--name-only',START).splitlines()
    allowed = {PROTOCOL,*CODE,'docs/session_14g_production_verification_wiring.md','docs/research_log.md'}
    if any(x not in allowed and not x.startswith(str(OUT)+'/') for x in changes):
        raise ValueError('historical_change')
    old = subprocess.check_output(['git','show',f'{START}:docs/research_log.md'],cwd=ROOT)
    if not safe('docs/research_log.md').read_bytes().startswith(old): raise ValueError('log_rewritten')
    for source in INPUTS:
        old = subprocess.check_output(['git','show',f'{START}:{source}'],cwd=ROOT)
        if approved_input(source).read_bytes() != old: raise ValueError('historical_input_changed')


def route_guard():
    for filename in CODE[:2]:
        tree = ast.parse(safe(filename).read_text())
        for node in ast.walk(tree):
            if isinstance(node,(ast.Import,ast.ImportFrom)):
                names = ([node.module or ''] if isinstance(node,ast.ImportFrom) else [n.name for n in node.names])
                if any(any(word in n.lower() for word in ('requests','urllib','socket','receiver_ranking','option_network','fitting','tracking','kloppy')) for n in names):
                    raise ValueError('forbidden_import')
    if set(SOURCES) & set(CODE): raise ValueError('historical_mutation_route')


def preflight():
    if git('status','--porcelain'): raise ValueError('unclean_tree')
    if git('rev-parse','v0.1.0^{}') != TAG: raise ValueError('tag_changed')
    git('merge-base','--is-ancestor',START,'HEAD')
    for filename in (PROTOCOL,*CODE):
        if subprocess.check_output(['git','show',f'HEAD:{filename}'],cwd=ROOT) != safe(filename).read_bytes():
            raise ValueError('uncommitted_authority')
    if subprocess.run(['git','check-ignore','-q',str(OUT/'local/probe')],cwd=ROOT).returncode != 0:
        raise ValueError('storage_not_ignored')
    historical_preservation(); route_guard()
    expected = read_json(approved_input(E/'manifest.json'))['environment']
    if environment() != expected: raise ValueError('environment_changed')


def atomic(relative, text):
    path = safe(relative); path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists(): raise FileExistsError('artifact_exists')
    temporary = path.with_name(path.name+'.tmp')
    with temporary.open('x',encoding='utf-8',newline='\n') as handle: handle.write(text)
    temporary.replace(path)


def write_json(name, obj):
    atomic(OUT/name,json.dumps(obj,sort_keys=True,indent=2,allow_nan=False)+'\n')


def ledger(stage,status):
    path=safe(OUT/'local/access.jsonl'); path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a',encoding='utf-8') as handle:
        handle.write(json.dumps({'time':datetime.now(timezone.utc).isoformat(),'stage':stage,
                               'status':status,'commit':git('rev-parse','HEAD'),'synthetic_only':True})+'\n')


def begin():
    if any(safe(OUT/x).exists() for x in (*FILES,'manifest.json')): raise FileExistsError('outputs_exist')
    p.claim_execution(safe(OUT/'local/execution.marker'))
    ledger('audit','started')


def fixture_rows():
    # Extract only the frozen pure fixture generator; never import its historical runner.
    source=approved_input(SOURCES[0]).read_text()
    function=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='fixtures')
    namespace={}
    exec(compile(ast.Module(body=[function],type_ignores=[]),'<frozen synthetic fixtures>','exec'),namespace)
    rows=tuple(namespace['fixtures']())
    p.require(len(rows)==36,'fixture_count')
    return rows


def authority_cases():
    rows=read_json(approved_input(B/'reference_summary.json'))['records']
    references={(x['fixture'],x['candidate'],x['component']):x['reference'] for x in rows if x['available']}
    missing={(x['fixture'],x['candidate'],x['component']) for x in rows if not x['available']}
    with approved_input(C/'unresolved_case_comparison.csv').open(newline='') as handle: replacements=list(csv.DictReader(handle))
    p.require(len(references)==362 and len(rows)==366 and len(replacements)==4,'reference_counts')
    replacement_keys={(x['fixture'],x['candidate'],'maximum') for x in replacements}
    p.require(replacement_keys==missing,'reference_keys')
    for x in replacements:
        p.require(x['available']=='True','unavailable_replacement')
        references[x['fixture'],x['candidate'],'maximum']=float(x['piecewise_reference'])
    with approved_input(E/'reference_comparison.csv').open(newline='') as handle: old_rows=list(csv.DictReader(handle))
    historical={}
    for row in old_rows:
        key=row['fixture'],row['candidate']
        item=historical.setdefault(key,{'intervals':int(row['intervals']),'estimates':{}})
        item['estimates'][row['component']]=float(row['estimate'])
    for label,origin,receiver,defenders in fixture_rows():
        for candidate in CANDIDATES:
            refs={key[2]:value for key,value in references.items() if key[:2]==(label,candidate)}
            yield label,dict(candidate=candidate,origin=origin,receiver=receiver,defenders=defenders,
                             references=refs,historical=historical[label,candidate],
                             historical_failure=(label,candidate,'maximum') in missing)


def injection_case():
    # Constant on a degenerate synthetic edge: exact oracle exp(0)=1.
    return dict(candidate='isotropic',origin=(0.,0.),receiver=(0.,0.),defenders=((2.,0.),),
                references={key:math.exp(-.5) for key in ('individual_1','union','maximum')})


def failure_injections():
    case=injection_case(); hashes={'synthetic':'identity'}; records=[]
    def run(): return p.run_pipeline([case],hashes,hashes,True)
    control=run()
    records.append({'injection':'valid_control','blocked':not control.readiness.ready,
                    'accepted_count':len(control.accepted),'failure':control.failure})
    patches=(
      ('continuity','check_continuity',{'side_effect':p.GateFailure('continuity_oracle')}),
      ('discontinuous_surrogate','independent_continuity',{'return_value':True}),
      ('failed_root','find_verified_envelope',{'side_effect':p.GateFailure('root_failed')}),
      ('malformed_certification','certified_partitions',{'side_effect':p.GateFailure('uncertified_boundary')}),
      ('nonconvergence','controlled_vector',{'return_value':(None,{},1.)}),
      ('permutation_mismatch','check_permutation',{'side_effect':p.GateFailure('permutation_mismatch')}),
      ('nondeterminism','check_repeatability',{'side_effect':p.GateFailure('nondeterminism')}),
    )
    for label,name,kwargs in patches:
        with patch.object(p,name,**kwargs): outcome=run()
        records.append({'injection':label,'blocked':not outcome.readiness.ready,
                        'accepted_count':len(outcome.accepted),'failure':outcome.failure})
    def warned(*args,**kwargs): warnings.warn('synthetic',IntegrationWarning)
    with patch.object(p,'adaptive_maximum',side_effect=warned): outcome=run()
    records.append({'injection':'warning','blocked':not outcome.readiness.ready,
                    'accepted_count':len(outcome.accepted),'failure':outcome.failure})
    missing={**case,'references':{}}
    for label,args in (('missing_reference',([missing],hashes,hashes,True)),
                       ('integrity_failure',([case],{},hashes,True))):
        outcome=p.run_pipeline(*args)
        records.append({'injection':label,'blocked':not outcome.readiness.ready,
                        'accepted_count':len(outcome.accepted),'failure':outcome.failure})
    with tempfile.TemporaryDirectory() as directory:
        marker=Path(directory).resolve()/'execution.marker'; p.claim_execution(marker)
        with patch.object(p,'verify_case') as numerical:
            try:
                p.claim_execution(marker); run()
                blocked=False
            except FileExistsError: blocked=True
            records.append({'injection':'marker_collision','blocked':blocked and not numerical.called,
                            'accepted_count':0,'failure':'FileExistsError' if blocked else None})
    verified=control.readiness.ready and all(r['blocked'] and r['accepted_count']==0 for r in records[1:])
    return records,verified


def finite_tree(value):
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError('nonfinite_value')
    if isinstance(value, dict):
        for item in value.values(): finite_tree(item)
    elif isinstance(value, list):
        for item in value: finite_tree(item)


def strict_keys(obj, keys):
    if type(obj) is not dict or set(obj)!=keys: raise ValueError('schema_keys')


def validate():
    objects={}
    for name,keys in SCHEMAS.items():
        value=read_json(safe(OUT/name)); strict_keys(value,keys); finite_tree(value)
        if value['schema_version']!=1: raise ValueError('schema_version')
        objects[name]=value
    ready=objects['readiness.json']; qc=objects['qc.json']; manifest=objects['manifest.json']
    strict_keys(ready['inputs'],set(VerificationReadiness.__dataclass_fields__))
    derived=VerificationReadiness(**ready['inputs']).ready
    if type(ready['ready']) is not bool or derived!=ready['ready']: raise ValueError('readiness_mismatch')
    classification=ready['classification']
    if classification not in (PASS,BLOCKED,INVALID): raise ValueError('classification')
    if (classification==PASS)!=derived: raise ValueError('classification_readiness')
    if any(x['classification']!=classification for x in (qc,manifest)): raise ValueError('classification_mismatch')
    if qc['status']!='closed' or manifest['status']!='closed' or qc['empirical_access'] is not False: raise ValueError('closure_state')
    wiring=objects['wiring_checks.json']
    for row in wiring['engineering']:
        strict_keys(row, {'fixture','passed','reason','permutations_checked','partition_count','boundary_enclosures','different_sections'})
        if type(row['passed']) is not bool or row['fixture'] not in p.engineering_functions():
            raise ValueError('engineering_schema')
    injections=objects['failure_injection.json']
    for row in injections['records']:
        strict_keys(row, {'injection','blocked','accepted_count','failure'})
        if type(row['blocked']) is not bool or type(row['accepted_count']) is not int:
            raise ValueError('injection_schema')
    if type(injections['verified']) is not bool: raise ValueError('enforcement_schema')
    cases=wiring['cases']
    for row in cases:
        strict_keys(row, {'fixture','candidate','intervals','estimates','errors','change','maximum',
                         'permutations','continuity','deterministic'})
        if row['candidate'] not in CANDIDATES: raise ValueError('candidate_schema')
        strict_keys(row['maximum'], {'partitions','piece_count','piecewise','repeat','unsplit','direct',
                                    'split_coarse','split_fine','split_evaluations'})
        parts=row['maximum']['partitions']
        if parts!=sorted(set(parts)) or parts[0]!=0. or parts[-1]!=1.: raise ValueError('partition_schema')
        if row['maximum']['piece_count']!=len(parts)-1: raise ValueError('piece_schema')
        if set(row['estimates'])!=set(row['errors']): raise ValueError('component_schema')
        if row['intervals'] not in (512,1024,2048,4096,8192,16384): raise ValueError('interval_schema')
    if qc['cases_completed']!=len(cases) or qc['unavailable_cases']!=108-len(cases): raise ValueError('case_counts')
    with safe(OUT/'reference_comparison.csv').open(newline='') as handle:
        reader=csv.DictReader(handle)
        if tuple(reader.fieldnames)!=CSV_KEYS: raise ValueError('csv_columns')
        rows=list(reader)
    if b'\r' in safe(OUT/'reference_comparison.csv').read_bytes(): raise ValueError('csv_newline')
    if len(rows)!=qc['references_completed'] or qc['unavailable_references']!=366-len(rows): raise ValueError('reference_counts')
    for row in rows:
        if row['candidate'] not in CANDIDATES or row['passed']!='True': raise ValueError('reference_row')
        for key in ('estimate','reference','absolute_error'):
            if not math.isfinite(float(row[key])): raise ValueError('csv_nonfinite')
    if qc['permutations_completed']!=sum(row['permutations'] for row in cases): raise ValueError('permutation_counts')
    indexed={(row['fixture'],row['candidate']):row for row in cases}
    if len(indexed)!=len(cases): raise ValueError('duplicate_case')
    seen=set()
    for row in rows:
        key=(row['fixture'],row['candidate']);component=row['component']
        if (*key,component) in seen or key not in indexed: raise ValueError('reference_identity')
        seen.add((*key,component)); case=indexed[key]
        if component not in case['estimates'] or float(row['estimate'])!=case['estimates'][component]:
            raise ValueError('cross_file_estimate')
        if int(row['intervals'])!=case['intervals'] or float(row['absolute_error'])!=case['errors'][component]:
            raise ValueError('cross_file_qc')
        if abs(float(row['estimate'])-float(row['reference']))!=float(row['absolute_error']):
            raise ValueError('reference_arithmetic')
    if len(rows)!=sum(len(case['estimates']) for case in cases): raise ValueError('missing_components')
    if derived and (len(cases)!=108 or len(rows)!=366 or qc['permutations_completed']!=399): raise ValueError('incomplete_pass')
    if set(manifest['outputs_sha256'])!=set(FILES): raise ValueError('manifest_files')
    for name,expected in manifest['outputs_sha256'].items():
        if digest(OUT/name)!=expected: raise ValueError('output_hash')
    if manifest['contract_sha256']!=digest(OUT/'contract.json'): raise ValueError('contract_hash')
    if derived and (not injections['verified'] or not wiring['engineering'] or
                    not all(row['passed'] for row in wiring['engineering'])):
        raise ValueError('unverified_pass')
    contract=objects['contract.json']
    strict_keys(contract['environment'], {'python','numpy','scipy','uv_lock_sha256'})
    strict_keys(contract['integration'], {'uniform_intervals','joint_tolerance','reference_tolerance','certified_partitions'})
    if set(contract['historical_hashes'])!=set(INPUTS) or set(contract['implementation_hashes'])!=set(CODE):
        raise ValueError('authority_fields')
    for key in ('historical_hashes','implementation_hashes'):
        for path,expected in contract[key].items():
            if path not in (*INPUTS,*CODE) or digest(path)!=expected: raise ValueError('authority_hash')
    if contract['protocol_hash']!=digest(PROTOCOL): raise ValueError('protocol_hash')
    # Fixed public schema and synthetic-only strings; never ingest local diagnostics.
    for name in (*FILES,'manifest.json'):
        text=safe(OUT/name).read_text()
        if any(x in text for x in ('/Users/','/private/','https://','player_id','event_id','target_id','signed_url')):
            raise ValueError('publication_content')
    return classification


def audit():
    preflight(); begin()
    historical={x:digest(x) for x in INPUTS}
    contract={'schema_version':1,'start':START,'protocol_commit':git('log','-1','--format=%H','--',PROTOCOL),
              'implementation_commit':git('rev-parse','HEAD'),'environment':environment(),
              'historical_hashes':historical,'implementation_hashes':{x:digest(x) for x in CODE},
              'protocol_hash':digest(PROTOCOL),
              'integration':{'uniform_intervals':[256,512,1024,2048,4096,8192,16384],
                             'joint_tolerance':1e-7,'reference_tolerance':1e-6,
                             'certified_partitions':'independent maximum verification only'}}
    engineering=[]; cases=[]; comparisons=[]; injections=[]; enforcement=False; failure=None
    classification=INVALID; gate=VerificationReadiness(**{x:False for x in VerificationReadiness.__dataclass_fields__})
    try:
        engineering=p.engineering_checks()
        if not all(x['passed'] for x in engineering):
            failure='engineering_mapped_record_mismatch'; classification=BLOCKED
        else:
            injections,enforcement=failure_injections()
            p.require(enforcement,'failure_enforcement')
            for label,case in authority_cases():
                outcome=p.run_pipeline([case],{x:digest(x) for x in INPUTS},historical,enforcement)
                if not outcome.readiness.ready:
                    failure=outcome.failure; classification=BLOCKED; break
                result=outcome.accepted[0]
                cases.append({'fixture':label,'candidate':case['candidate'],**result})
                for component,estimate in result['estimates'].items():
                    comparisons.append(dict(fixture=label,candidate=case['candidate'],component=component,
                                            intervals=result['intervals'],estimate=estimate,
                                            reference=case['references'][component],absolute_error=result['errors'][component],passed=True))
                ledger('case','verified')
            if failure is None:
                p.require(len(cases)==108 and len(comparisons)==366 and sum(x['permutations'] for x in cases)==399,'complete_counts')
                # Every input derives from completed evidence, not assumed authority.
                gate=VerificationReadiness(
                    continuity_verified=all(x['continuity'] for x in cases),
                    switching_verified=all(x['passed'] for x in engineering) and all(x['maximum']['piece_count']>0 for x in cases),
                    controlled_integration_verified=all(x['intervals'] is not None for x in cases),
                    references_complete=len(comparisons)==366 and all(x['passed'] for x in comparisons),
                    permutation_verified=sum(x['permutations'] for x in cases)==399,
                    deterministic=all(x['deterministic'] for x in cases),failure_enforcement_verified=enforcement,
                    blocking_warnings_absent=len(cases)==108,
                    integrity_verified=p.validate_integrity({x:digest(x) for x in INPUTS},historical))
                classification=PASS if gate.ready else BLOCKED
    except (p.GateFailure,ValueError,Warning) as error:
        failure=type(error).__name__; classification=BLOCKED
    except Exception as error:
        failure=type(error).__name__; classification=INVALID
    if failure: atomic(OUT/'local/failure.json',json.dumps({'failure':failure,'classification':classification})+'\n')
    write_json('contract.json',contract)
    write_json('wiring_checks.json',{'schema_version':1,'engineering':engineering,'cases':cases,'stopped_reason':failure})
    stream=io.StringIO(newline=''); writer=csv.DictWriter(stream,fieldnames=CSV_KEYS,lineterminator='\n')
    writer.writeheader();writer.writerows(comparisons);atomic(OUT/'reference_comparison.csv',stream.getvalue())
    write_json('failure_injection.json',{'schema_version':1,'records':injections,'verified':enforcement})
    write_json('readiness.json',{'schema_version':1,'inputs':asdict(gate),'ready':gate.ready,'classification':classification})
    write_json('qc.json',{'schema_version':1,'status':'closed','classification':classification,
                         'cases_completed':len(cases),'references_completed':len(comparisons),
                         'permutations_completed':sum(x['permutations'] for x in cases),
                         'unavailable_cases':108-len(cases),'unavailable_references':366-len(comparisons),
                         'empirical_access':False,'failure':failure})
    write_json('manifest.json',{'schema_version':1,'status':'closed','classification':classification,
                               'outputs_sha256':{name:digest(OUT/name) for name in FILES},
                               'contract_sha256':digest(OUT/'contract.json')})
    validate(); ledger('audit','closed')
    atomic(OUT/'local/closed.marker',digest(OUT/'manifest.json')+'\n')
    print(classification)
    return 0 if gate.ready else 2


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('preflight','audit','publication-check'))
    command=parser.parse_args().command
    if command=='preflight': preflight(); print('preflight passed'); return 0
    if command=='audit': return audit()
    historical_preservation();route_guard(); print(validate()); return 0


if __name__=='__main__':
    raise SystemExit(main())
