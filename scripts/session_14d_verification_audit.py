#!/usr/bin/env python3
"""Synthetic verification audit with immutable historical inputs and one execution."""
from __future__ import annotations
import argparse
import ast
import csv
from datetime import datetime, timezone
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
import numpy as np
import scipy
from defensive_network_disruption.geometry.verification_audit import (
    complete_signature, controlled_vector, discontinuity_counterexample, engineering_switching,
    enforcement_oracles, perturbation_oracles, summarize_result, value_oracles)
from defensive_network_disruption.geometry.maximum_envelope import find_envelope_switches
from defensive_network_disruption.geometry.integration_review import directional_breakpoints, values_for_components
from defensive_network_disruption.geometry.occlusion_fields import CarrierOriginField, CANDIDATES
from defensive_network_disruption.validation.json_scalars import json_native

START = 'd80aa7ff8438568e874263f8273bbe82c35121d4'
TAG = 'f00690c05d8c1c6db308a65bd311c43f9a8ef2fa'
PROTOCOL = 'docs/protocols/phase_14d_numerical_verification_contract_audit.md'
OUT = Path('outputs/continuous_occlusion_verification_audit')
CODE = ('scripts/session_14d_verification_audit.py',
        'src/defensive_network_disruption/geometry/verification_audit.py',
        'tests/test_session14d_verification.py')
INPUTS = ('scripts/session_14_occlusion_fields.py', 'scripts/session_14c_maximum_switching.py',
          'src/defensive_network_disruption/geometry/occlusion_fields.py',
          'src/defensive_network_disruption/geometry/integration_review.py',
          'src/defensive_network_disruption/geometry/maximum_envelope.py',
          'outputs/continuous_occlusion_numerics_14b/reference_summary.json',
          'outputs/continuous_occlusion_max_switching/unresolved_case_comparison.csv',
          'outputs/continuous_occlusion_max_switching/manifest.json',
          'outputs/continuous_occlusion_numerics_14b/manifest.json', 'uv.lock')
FILES = ('verification_obligations.json', 'oracle_results.json', 'controlled_integration.csv',
         'switching_coverage.csv', 'qc.json')
CONTROL_KEYS = ('fixture', 'candidate', 'component', 'reference_source', 'intervals',
                'successive_vector_difference', 'estimate', 'reference', 'absolute_error', 'passed')
SWITCH_KEYS = ('fixture', 'candidate', 'defender_count', 'permutations', 'deterministic',
               'permutation_equal', 'mismatch_count')
SCHEMAS = {
    'verification_obligations.json': {'schema_version','result','defects','continuity','switching','controlled','enforcement'},
    'oracle_results.json': {'schema_version','values','perturbations','jump','switch_engineering','enforcement'},
    'qc.json': {'schema_version','status','result','cases','components','empirical_access','models_loaded','error'},
    'manifest.json': {'schema_version','status','start','protocol','implementation','inputs','environment',
                      'outputs','unavailable','execution_commit'},
}


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT).decode().strip()


def safe(relative):
    relative = Path(relative)
    if relative.is_absolute() or '..' in relative.parts: raise ValueError('unsafe_path')
    path = ROOT/relative
    if not path.resolve().is_relative_to(ROOT.resolve()) or any(p.is_symlink() for p in (path,*path.parents)):
        raise ValueError('unsafe_path')
    return path


def digest(relative): return hashlib.sha256(safe(relative).read_bytes()).hexdigest()


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result: raise ValueError('duplicate_key')
        result[key] = value
    return result


def load(relative):
    if str(relative) not in INPUTS and not Path(relative).is_relative_to(OUT): raise ValueError('input_not_allowlisted')
    return json.loads(safe(relative).read_text(), object_pairs_hook=no_duplicates,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite')))


def atomic(relative, text):
    if not Path(relative).is_relative_to(OUT): raise ValueError('output_not_allowlisted')
    path = safe(relative); path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists(): raise FileExistsError('preserve_existing')
    temporary = safe(Path(relative).with_name('.'+path.name+'.tmp'))
    with temporary.open('x', newline='\n') as handle: handle.write(text)
    temporary.replace(path)


def put_json(name, value):
    if set(value) != SCHEMAS[name]: raise ValueError('schema_keys')
    atomic(OUT/name, json.dumps(json_native(value), sort_keys=True, indent=2, allow_nan=False)+'\n')


def put_csv(name, keys, rows):
    import io
    text = io.StringIO(newline='')
    writer = csv.DictWriter(text, fieldnames=keys, lineterminator='\n')
    writer.writeheader(); writer.writerows(rows)
    atomic(OUT/name, text.getvalue())


def environment():
    return {'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__,
            'lock': digest('uv.lock')}


def history():
    if git('rev-parse','v0.1.0^{}') != TAG: raise ValueError('tag_changed')
    git('merge-base','--is-ancestor',START,'HEAD')
    for path in INPUTS:
        original = subprocess.check_output(['git','show',START+':'+path],cwd=ROOT)
        if hashlib.sha256(original).hexdigest() != digest(path): raise ValueError('historical_input_changed')
    for path in git('diff','--name-only','--diff-filter=MDR',START).splitlines():
        if path != 'docs/research_log.md': raise ValueError('historical_change')
        before = subprocess.check_output(['git','show',START+':'+path],cwd=ROOT)
        if not safe(path).read_bytes().startswith(before): raise ValueError('log_not_append_only')


def committed(path):
    before = subprocess.check_output(['git','show','HEAD:'+path],cwd=ROOT)
    if hashlib.sha256(before).hexdigest()!=digest(path): raise ValueError('uncommitted_authority')


def routes():
    for path in CODE[:2]:
        tree = ast.parse(safe(path).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and any(x in (node.module or '') for x in ('models','networks','data.')):
                raise ValueError('forbidden_import')
            if isinstance(node, ast.Import) and any(x.name.split('.')[0] in ('requests','urllib') for x in node.names):
                raise ValueError('forbidden_network')
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ('evaluate_options','minimize','urlopen'):
                raise ValueError('forbidden_call')


def preflight():
    history(); routes()
    for path in (PROTOCOL,*CODE): committed(path)
    if not git('check-ignore','--',str(OUT/'local/probe')): raise ValueError('unignored_ledger')
    for manifest_path, artifact in ((INPUTS[7], INPUTS[6]), (INPUTS[8], INPUTS[5])):
        authority = load(manifest_path)
        if authority['outputs_sha256'][Path(artifact).name] != digest(artifact):
            raise ValueError('historical_manifest_binding')
    old_environment = load(INPUTS[7])['environment']
    current = environment()
    if any(old_environment[k] != current[k] for k in ('python','numpy','scipy')) or old_environment['uv_lock_sha256'] != current['lock']:
        raise ValueError('governed_environment_mismatch')
    print('Session 14d preflight passed; synthetic inputs only')


def ledger(stage, status):
    path=safe(OUT/'local/access.jsonl'); path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a') as f:
        f.write(json.dumps({'time':datetime.now(timezone.utc).isoformat(),'stage':stage,'status':status,
                            'commit':git('rev-parse','HEAD'),'protocol':digest(PROTOCOL)})+'\n')


def begin():
    if git('status','--porcelain'): raise ValueError('clean_tree_required')
    if any(safe(OUT/x).exists() for x in (*FILES,'manifest.json')): raise FileExistsError('artifacts_exist')
    atomic(OUT/'local/execution.marker',git('rev-parse','HEAD')+'\n')
    ledger('audit','started')


def fixture_rows():
    path=safe(INPUTS[0]); spec=importlib.util.spec_from_file_location('closed14d_fixture_source',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return tuple(module.fixtures())


def references():
    rows=load(INPUTS[5])['records']
    refs={(r['fixture'],r['candidate'],r['component']): (r['reference'],'14b') for r in rows if r['available']}
    missing={(r['fixture'],r['candidate'],r['component']) for r in rows if not r['available']}
    with safe(INPUTS[6]).open(newline='') as f: replacements=list(csv.DictReader(f))
    keys={(r['fixture'],r['candidate'],'maximum') for r in replacements}
    if len(rows)!=366 or len(refs)!=362 or missing!=keys or len(keys)!=4: raise ValueError('reference_keys')
    for r in replacements:
        if r['available']!='True': raise ValueError('reference_unavailable')
        refs[r['fixture'],r['candidate'],'maximum']=(float(r['piecewise_reference']),'14c')
    if any(not math.isfinite(v[0]) for v in refs.values()): raise ValueError('nonfinite_reference')
    return refs


def perform():
    ledger('oracles','started')
    values=value_oracles(); perturbations=perturbation_oracles(); jump=discontinuity_counterexample()
    engineering=engineering_switching()
    enforcement=enforcement_oracles(safe(INPUTS[1]).read_text())
    ledger('oracles','completed')
    refs=references(); controls=[]; switching=[]
    fixtures=fixture_rows()
    if len(fixtures)!=36: raise ValueError('fixture_count')
    for label,b,q,ds in fixtures:
        for candidate in CANDIDATES:
            field=CarrierOriginField(candidate)
            count, estimates, change=controlled_vector(lambda n: values_for_components(field,b,q,ds,n))
            for component, estimate in estimates.items():
                reference,source=refs[label,candidate,component]
                error=abs(estimate-reference)
                controls.append(dict(zip(CONTROL_KEYS,(label,candidate,component,source,count,change,
                                                      estimate,reference,error,count is not None and error<=1e-6))))
            b_array=np.array(b,dtype=np.float64); edge=np.array(q,dtype=np.float64)-b_array
            def make(permutation):
                selected=tuple(ds[i] for i in permutation)
                return lambda t: field.individual_values(b,selected,b_array[None,:]+t[:,None]*edge[None,:])
            identity=tuple(range(len(ds)))
            onset=() if candidate=='isotropic' else directional_breakpoints(b,q,ds)
            first=find_envelope_switches(make(identity),extra_partitions=onset)
            repeated=find_envelope_switches(make(identity),extra_partitions=onset)
            signature=complete_signature(first,identity); mismatches=0; permutations=0
            for permutation in itertools.permutations(identity):
                # Identity was already evaluated and repeated above.
                other=first if permutation==identity else find_envelope_switches(make(permutation),extra_partitions=onset)
                mismatches+=complete_signature(other,permutation)!=signature
                permutations+=1
            switching.append(dict(zip(SWITCH_KEYS,(label,candidate,len(ds),permutations,
                                                   first==repeated,mismatches==0,mismatches))))
        ledger(label,'completed')
    if len(controls)!=366 or len(switching)!=108: raise ValueError('completed_counts')
    defects=summarize_result(values,switching,controls,enforcement)
    by_name={r['fixture']:r for r in engineering}
    if by_name['raw_sign_underflow']['brent_calls']!=1: defects.append('raw_sign_product_underflow')
    intervals=by_name['non_node_tie']['tie_intervals']
    if not intervals or intervals[0]['start']!=.251 or intervals[0]['end']!=.749:
        defects.append('grid_tie_boundaries_not_exact')
    result='BLOCKED — Bounded repair required' if defects else 'PASS — Retry contract adequately supported'
    oracle={'schema_version':1,'values':values,'perturbations':perturbations,'jump':jump,
            'switch_engineering':engineering,'enforcement':enforcement}
    obligations={'schema_version':1,'result':result,'defects':defects,
                 'continuity':{'analytic_continuity_valid_on_domain':True,'independent_values_pass':all(r['passed'] for r in values),
                               'historical_flag_is_independent':False,'known_jump_flag':jump['historical_flag']},
                 'switching':{'case_count':108,'all_full_permutations_equal':all(r['permutation_equal'] for r in switching),
                              'finite_grid_completeness_claim':False,'hidden_crossings_found':by_name['hidden_crossings']['interior_switches']},
                 'controlled':{'component_count':366,'all_pass':all(r['passed'] for r in controls),
                               'maximum_error':max(r['absolute_error'] for r in controls)},
                 'enforcement':{'all_injected_failures_block_retry':all(r['blocks_retry'] for r in enforcement if r['injected']!='none'),
                                'historical_review_has_clean_tree_gate':False}}
    put_json('oracle_results.json',oracle)
    put_csv('controlled_integration.csv',CONTROL_KEYS,controls)
    put_csv('switching_coverage.csv',SWITCH_KEYS,switching)
    put_json('verification_obligations.json',obligations)
    put_json('qc.json',{'schema_version':1,'status':'complete','result':result,'cases':108,'components':366,
                       'empirical_access':False,'models_loaded':0,'error':None})


def validate():
    for name in FILES:
        if not safe(OUT/name).exists(): continue
        if name.endswith('.json'):
            value=load(OUT/name)
            if set(value)!=SCHEMAS[name]: raise ValueError('schema_keys')
            json_native(value)
        text=safe(OUT/name).read_text()
        if any(token in text for token in ('/Users/','player_id','event_id','https://','token=')):
            raise ValueError('publication_sensitive')
    qc=load(OUT/'qc.json')
    if qc['empirical_access'] is not False or qc['models_loaded']!=0: raise ValueError('access_counts')
    if qc['status']=='complete':
        for name,keys,count in (('controlled_integration.csv',CONTROL_KEYS,366),('switching_coverage.csv',SWITCH_KEYS,108)):
            raw=safe(OUT/name).read_bytes()
            if b'\r' in raw: raise ValueError('csv_line_endings')
            with safe(OUT/name).open(newline='') as f:
                reader=csv.DictReader(f);rows=list(reader)
                if tuple(reader.fieldnames)!=keys or len(rows)!=count: raise ValueError('csv_schema')
            identities={(r['fixture'],r['candidate'],r.get('component','')) for r in rows}
            if len(identities)!=count: raise ValueError('duplicate_case')
            for row in rows:
                for key in ('estimate','reference','absolute_error','successive_vector_difference') if name.startswith('controlled') else ():
                    if not math.isfinite(float(row[key])): raise ValueError('nonfinite_csv')
        obligations=load(OUT/'verification_obligations.json')
        if qc['result']!=obligations['result']: raise ValueError('result_mismatch')
        if qc['cases']!=108 or qc['components']!=366: raise ValueError('qc_counts')


def close():
    validate(); history()
    present={name:digest(OUT/name) for name in FILES if safe(OUT/name).exists()}
    qc=load(OUT/'qc.json')
    put_json('manifest.json',{'schema_version':1,'status':'closed' if qc['status']=='complete' else 'closed_invalid',
                             'start':START,'protocol':digest(PROTOCOL),'implementation':{p:digest(p) for p in CODE},
                             'inputs':{p:digest(p) for p in INPUTS},'environment':environment(),
                             'outputs':present,'unavailable':[n for n in FILES if n not in present],
                             'execution_commit':git('rev-parse','HEAD')})
    ledger('audit','closed')


def audit():
    preflight();begin()
    try:
        perform();close()
    except Exception as error:
        ledger('audit','invalid_'+type(error).__name__)
        if not safe(OUT/'qc.json').exists():
            put_json('qc.json',{'schema_version':1,'status':'invalid','result':'INVALID — Audit execution failure',
                               'cases':0,'components':0,'empirical_access':False,'models_loaded':0,'error':type(error).__name__})
        if not safe(OUT/'manifest.json').exists():
            # Preserve partial files without making a failed validation into a success.
            present={n:digest(OUT/n) for n in FILES if safe(OUT/n).exists()}
            put_json('manifest.json',{'schema_version':1,'status':'closed_invalid','start':START,'protocol':digest(PROTOCOL),
                 'implementation':{p:digest(p) for p in CODE},'inputs':{p:digest(p) for p in INPUTS},
                 'environment':environment(),'outputs':present,'unavailable':[n for n in FILES if n not in present],
                 'execution_commit':git('rev-parse','HEAD')})
        raise RuntimeError('audit_invalid_preserved') from None
    print(load(OUT/'qc.json')['result'])


def publication_check():
    preflight()
    manifest=load(OUT/'manifest.json')
    if set(manifest)!=SCHEMAS['manifest.json']: raise ValueError('manifest_schema')
    if manifest['protocol']!=digest(PROTOCOL) or manifest['environment']!=environment(): raise ValueError('authority_changed')
    for group in ('implementation','inputs'):
        expected=set(CODE if group=='implementation' else INPUTS)
        if set(manifest[group])!=expected: raise ValueError('authority_schema')
        for path,expected_hash in manifest[group].items():
            if digest(path)!=expected_hash: raise ValueError('authority_hash')
    if set(manifest['outputs'])|set(manifest['unavailable'])!=set(FILES): raise ValueError('file_set')
    for name,expected in manifest['outputs'].items():
        if digest(OUT/name)!=expected: raise ValueError('output_hash')
    if manifest['status']=='closed': validate()
    elif manifest['status']!='closed_invalid': raise ValueError('closure_state')
    print('Session 14d publication passed; hashes unchanged')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=('preflight','audit','publication-check'))
    {'preflight':preflight,'audit':audit,'publication-check':publication_check}[parser.parse_args().command]()
