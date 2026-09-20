"""Strict R9R persisted-package validation. No geometry load or numerical replay."""
from __future__ import annotations

import csv
import io
import math
from pathlib import Path
import re

from .r9j_evidence import canonical,digest,load,put,put_bytes,sha,hash_string,finite

NAMES=('repair_contract.json','topology_controls.csv','negative_controls.csv','retained_edge_replay.json',
       'historical_regressions.csv','performance.json','publication_tripwire.json','qc.json','manifest.json')
COLUMNS={
 'topology_controls.csv':('fixture','family','expected','observed','passed','evidence_sha256'),
 'negative_controls.csv':('fixture','blocked','reason','evidence_sha256'),
 'historical_regressions.csv':('fixture','candidate','status','components','permutations','structure_exact',
    'production_preserved','verification_preserved','reason','evidence_sha256'),
}
TOPOLOGIES=('same_sign','simple','monotone','nonmonotone_no_root','endpoint','tangent','positive_perturbation',
            'nearby','duplicates','inactive','onset_coincidence','multiway','tiny_unresolved','rounded_sign_reversal')
EXPECTED=('A','B','B','A','D','E','A','F','C','C','B','B','G','A')
NEGATIVES=('missing_derivative','ambiguous_roots','malformed_region','inconsistent_onset','false_identity',
           'corrupt_witness','biased_difference','nonfinite','limit')
REASONS=('complete','not_executed','synthetic_failure','historical_incompatibility','retained_unresolved',
         'governed_failure','timeout','publication_failure','invalid_authority')
SCHEMAS={
 'repair_contract.json':(('authority_bound','separate_math_binary64','historical_sources_preserved','no_tolerance_change'),('topology_families','negative_families'),()),
 'retained_edge_replay.json':(('access_confirmed','exposure_uncertain','path_completed','root_free_region_preserved'),('states_reopened','edges_reopened','candidates_completed'),('seconds',)),
 'performance.json':((),('localization_calls','subdivisions','floats_inspected','max_depth','unresolved'),('governed_wall','exclusive_compute','inclusive_numerical','io','waiting','unattributed')),
 'publication_tripwire.json':(('controls_passed','legacy_unreachable','one_review','traceback_bound','independent_failure','rerun_rejected'),('controls',),('seconds',)),
}


def record(flags,counts,timings,*,status='complete',reason='complete'):
    return dict(schema_version=1,status=status,reason=reason,flags=flags,counts=counts,timings=timings)


def validate_record(name,value):
    if set(value)!={'schema_version','status','reason','flags','counts','timings','evidence_sha256'}:raise ValueError('record_schema')
    if type(value['schema_version'])is not int or value['schema_version']!=1 or value['status'] not in ('complete','partial','blocked','invalid','unavailable') or value['reason'] not in REASONS:raise ValueError('record_status')
    for kind,keys in zip(('flags','counts','timings'),SCHEMAS[name]):
        if set(value[kind])!=set(keys):raise ValueError('record_keys')
        for item in value[kind].values():
            if item is None:continue
            if kind=='flags' and type(item)is not bool:raise ValueError('flag_type')
            if kind=='counts' and (type(item)is not int or item<0):raise ValueError('count_type')
            if kind=='timings' and (type(item)not in (float,int) or item<0):raise ValueError('time_type')
    if not hash_string(value['evidence_sha256']):raise ValueError('evidence_hash')
    finite(value)


def csv_bytes(name,rows):
    output=io.StringIO(newline='');writer=csv.DictWriter(output,fieldnames=COLUMNS[name],lineterminator='\n');writer.writeheader()
    for row in rows:
        if set(row)!=set(COLUMNS[name]):raise ValueError('csv_schema')
        if not re.fullmatch('[A-Za-z0-9_.-]+',row['fixture']):raise ValueError('fixture_identifier')
        if not hash_string(row['evidence_sha256']):raise ValueError('row_hash')
        writer.writerow({k:str(v).lower() if type(v)is bool else v for k,v in row.items()})
    return output.getvalue().encode()


def unprimitive(x):
    if isinstance(x,list):return [unprimitive(y) for y in x]
    if isinstance(x,dict):
        if set(x)=={'float','hex'}:
            if type(x['float'])is not float or not math.isfinite(x['float']) or x['float'].hex()!=x['hex']:raise ValueError('float_bits')
            return x['float']
        return {k:unprimitive(v) for k,v in x.items()}
    return x


def historical_flags(detail):
    old,new,expected=(unprimitive(detail[k]) for k in ('old','new','expected'))
    if new is None:return False,False,False
    structure=all(new.get(k)==old.get(k) for k in ('partitions','canonical_onsets','canonical_switches'))
    production=new['intervals']==old['intervals']==expected['intervals'] and detail['component_order']['new']==detail['component_order']['old']==detail['component_order']['expected']
    if production:
        for key,value in new['estimates'].items():
            for other in (old['estimates'][key],expected['estimates'][key]):
                production &= abs(value-other)<=64*(2.**-52)*max(1.,abs(value),abs(other))
    verification=new['maximum_interval']==old['maximum_interval'] and new['certificate_evidence']==old['certificate_evidence']
    return bool(structure),bool(production),bool(verification)


def frozen_catalog():
    # Only committed provider-free fixture definitions and reference vectors.
    # No numerical estimator or empirical record is invoked during validation.
    from .r9r_acceptance import historical_cases,primitive
    root=Path(__file__).resolve().parents[3]
    return [(label,case['candidate'],len(case['historical_vector']['estimates']),
             math.factorial(len(case['defenders'])),digest(primitive(case['historical_vector'])))
            for label,case in historical_cases(root)]


def derive(local,index):
    local=Path(local);outcome=load(local/'outcome.json')
    if set(outcome)!={'schema_version','execution_valid','reason','authority_bound','timings','retained','publication','performance'} or outcome['schema_version']!=1:raise ValueError('outcome_schema')
    if outcome['reason']not in REASONS or type(outcome['execution_valid'])is not bool or type(outcome['authority_bound'])is not bool:raise ValueError('outcome_values')
    rows={name:load(local/(name+'.json')) for name in COLUMNS}
    byhash={h:local/name for name,h in index.items()}
    catalog=frozen_catalog()
    for name,items in rows.items():
        csv_bytes(name,items)
        for ordinal,row in enumerate(items):
            if row['evidence_sha256']not in byhash:raise ValueError('unbound_observation')
            detail=load(byhash[row['evidence_sha256']])
            if name=='topology_controls.csv':
                if row['fixture']not in TOPOLOGIES or row['expected']!=EXPECTED[TOPOLOGIES.index(row['fixture'])]:raise ValueError('topology_expected')
                observed=detail['result']['classification']
                if row['observed']!=observed or type(row['passed'])is not bool or row['passed']!=(observed==row['expected'] and all(detail['extra'].values())):raise ValueError('topology_observation')
            elif name=='negative_controls.csv':
                if row['fixture']not in NEGATIVES or type(row['blocked'])is not bool or row['blocked']!=detail['blocked'] or row['reason']!=detail['reason']:raise ValueError('negative_observation')
            else:
                if ordinal>=len(catalog):raise ValueError('historical_inventory')
                label,candidate,components,permutations,expected_hash=catalog[ordinal]
                if (row['fixture'],row['candidate'],row['components'])!=(label,candidate,components) or digest(detail['expected'])!=expected_hash:raise ValueError('historical_authority')
                if row['status']=='passed' and row['permutations']!=permutations:raise ValueError('historical_permutations')
                flags=historical_flags(detail)
                if tuple(row[k] for k in ('structure_exact','production_preserved','verification_preserved'))!=flags or row['status']!=('passed' if all(flags) else 'blocked'):raise ValueError('historical_observation')
                if type(row['components'])is not int or row['components']!=len(detail['expected']['estimates']):raise ValueError('reference_count')
                expected_perms=detail['new']['permutations'] if detail['new']is not None else 0
                if type(row['permutations'])is not int or row['permutations']!=expected_perms:raise ValueError('permutation_count')
    top=rows['topology_controls.csv'];neg=rows['negative_controls.csv'];hist=rows['historical_regressions.csv']
    controls=[r['fixture'] for r in top]==list(TOPOLOGIES) and all(r['passed'] for r in top)
    negatives=[r['fixture'] for r in neg]==list(NEGATIVES) and all(r['blocked'] for r in neg)
    history=len(hist)==108 and sum(r['components'] for r in hist)==366 and sum(r['permutations'] for r in hist)==399 and all(r['status']=='passed' for r in hist)
    pub=outcome['publication']
    observed_pub=load(local/'publication_observations.json')
    if observed_pub['summary']!=pub:raise ValueError('publication_observation')
    if len(observed_pub['rows'])!=pub['counts']['controls']:raise ValueError('publication_control_count')
    pub_ok=all(pub['flags'].values()) and pub['counts']['controls']==5
    if set(pub)!= {'flags','counts','timings'}:raise ValueError('publication_schema')
    attempt=local/'access_attempt.json';receipt=local/'access_materialized.json';exposed=receipt.exists()
    if exposed:
        value=load(receipt)
        if set(value)!= {'schema_version','attempt_sha256','selected_sha256'} or value['schema_version']!=1 or not attempt.exists():raise ValueError('access_receipt')
        if sha(attempt)!=value['attempt_sha256'] or sha(local/'selected_geometry.json')!=value['selected_sha256']:raise ValueError('access_hash')
    uncertain=attempt.exists() and not exposed;retained=outcome['retained']
    if set(retained)!= {'path_completed','root_free_region_preserved','seconds'} or any(type(retained[k])is not bool for k in ('path_completed','root_free_region_preserved')):raise ValueError('retained_schema')
    if retained['path_completed']:
        if not exposed:raise ValueError('missing_retained_access')
        success=load(local/'retained_success.json')
        expected_success={k:sha(local/name) for k,name in (
            ('result_sha256','retained_result.json'),('authority_sha256','diagnostic_authority.json'),
            ('observations_sha256','retained_observations.json'),('reference_sha256','retained_reference_cell.json'))}
        if success!=expected_success:raise ValueError('retained_success_hash')
        result=unprimitive(load(local/'retained_result.json'))
        if result['degenerate'] or result['intervals']not in (512,1024,2048,4096,8192,16384) or not result['deterministic'] or not result['certificate_evidence']:raise ValueError('retained_result_schema')
        from fractions import Fraction as F
        def frac(x):return F(int(x['numerator_hex'],16),int(x['denominator_hex'],16))
        reference=load(local/'retained_reference_cell.json');region=(frac(reference['left']),frac(reference['right']))
        observations=load(local/'retained_observations.json')
        roots=[x['value'] for x in observations if x['kind']=='isolated_root']
        outside=all(frac(x[1])<region[0] or frac(x[0])>region[1] for x in roots)
        if retained['root_free_region_preserved']!=outside:raise ValueError('retained_region_disagreement')
    valid=outcome['execution_valid'] and outcome['authority_bound'] and pub_ok and not uncertain
    regression=any(r['status']=='blocked' for r in hist)
    if not valid:classification,readiness='E',4
    elif regression:classification,readiness='C',3
    elif not controls or not negatives:classification,readiness='E',4
    elif retained['path_completed'] and retained['root_free_region_preserved']:
        classification,readiness=('A',1) if history else ('B',2)
    elif exposed:classification,readiness='D',3
    else:classification,readiness='E',4
    counts=dict(topology_passed=sum(r['passed'] for r in top),negative_blocked=sum(r['blocked'] for r in neg),
        cases_run=len(hist),cases_passed=sum(r['status']=='passed' for r in hist),
        references_requested=sum(r['components'] for r in hist),
        references_passed=sum(r['components'] for r in hist if r['status']=='passed'),
        permutations_passed=sum(r['permutations'] for r in hist if r['status']=='passed'))
    q=dict(schema_version=1,status='complete' if classification=='A' else 'blocked' if valid else 'invalid',
        execution_valid=outcome['execution_valid'],classification=classification,readiness=readiness,
        states_reopened=int(exposed),edges_reopened=int(exposed),exposure_uncertain=uncertain,
        reason=outcome['reason'],counts=counts)
    records={
        'repair_contract.json':record(dict(authority_bound=outcome['authority_bound'],separate_math_binary64=True,historical_sources_preserved=outcome['authority_bound'],no_tolerance_change=outcome['authority_bound']),dict(topology_families=14,negative_families=9),{}),
        'retained_edge_replay.json':record(dict(access_confirmed=exposed,exposure_uncertain=uncertain,path_completed=retained['path_completed'],root_free_region_preserved=retained['root_free_region_preserved']),dict(states_reopened=int(exposed),edges_reopened=int(exposed),candidates_completed=int(retained['path_completed'])),dict(seconds=retained['seconds']),status='complete' if retained['path_completed'] else 'partial' if exposed else 'unavailable',reason=outcome['reason']),
        'performance.json':record({},outcome['performance'],outcome['timings']),
        'publication_tripwire.json':record(**pub,status='complete' if pub_ok else 'invalid',reason='complete' if pub_ok else 'publication_failure'),
    }
    return records,rows,q


def close(folder,authority):
    folder=Path(folder);local=folder/'local'
    index={p.relative_to(local).as_posix():sha(p) for p in sorted(local.rglob('*')) if p.is_file() and p.name!='private_index.json'}
    records,rows,q=derive(local,index)
    put(local/'private_index.json',dict(schema_version=1,files=index));h=sha(local/'private_index.json')
    for name,value in records.items():
        value={**value,'evidence_sha256':h};validate_record(name,value);put(folder/name,value)
    for name,items in rows.items():put_bytes(folder/name,csv_bytes(name,items))
    put(folder/'qc.json',q)
    put(folder/'manifest.json',dict(schema_version=1,authority=authority,outputs={n:sha(folder/n) for n in NAMES if n!='manifest.json'},private_index_sha256=h))
    return publication_check(folder)


def publication_check(folder):
    folder=Path(folder);local=folder/'local'
    if {p.name for p in folder.iterdir() if p.is_file()}!=set(NAMES):raise ValueError('public_inventory')
    m=load(folder/'manifest.json')
    if set(m)!= {'schema_version','authority','outputs','private_index_sha256'} or m['schema_version']!=1:raise ValueError('manifest_schema')
    if set(m['outputs'])!=set(NAMES)-{'manifest.json'}:raise ValueError('manifest_inventory')
    for name,h in m['outputs'].items():
        if not hash_string(h) or sha(folder/name)!=h:raise ValueError('public_hash')
    if sha(local/'private_index.json')!=m['private_index_sha256']:raise ValueError('private_index_hash')
    index=load(local/'private_index.json')
    if set(index)!= {'schema_version','files'} or index['schema_version']!=1:raise ValueError('private_schema')
    for name,h in index['files'].items():
        p=Path(name)
        if p.is_absolute() or '..' in p.parts or p.is_symlink() or not hash_string(h) or sha(local/p)!=h:raise ValueError('private_hash')
    if load(local/'authority.json')!=m['authority']:raise ValueError('authority_cross_file')
    records,rows,q=derive(local,index['files'])
    if load(folder/'qc.json')!=q:raise ValueError('false_decision')
    for name,value in records.items():
        actual=load(folder/name);validate_record(name,actual)
        if actual!={**value,'evidence_sha256':m['private_index_sha256']}:raise ValueError('cross_file')
    for name,items in rows.items():
        if (folder/name).read_bytes()!=csv_bytes(name,items):raise ValueError('csv_cross_file')
    for name in NAMES:
        raw=(folder/name).read_text()
        if any(x in raw for x in ('/Users/','/private/','"carrier"','"defenders"','"traceback"','"state":','"edge":')):raise ValueError('private_leak')
    return dict(valid=True,files=len(NAMES),classification=q['classification'],readiness=q['readiness'],
                states_reopened=q['states_reopened'],edges_reopened=q['edges_reopened'])
