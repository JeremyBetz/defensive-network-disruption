"""R9Q strict persisted evidence, with no retained-journal or geometry reader."""
from __future__ import annotations

import csv
import io
from pathlib import Path

from .r9j_evidence import canonical, digest, load, put, put_bytes, sha, hash_string, finite

NAMES = ('authority.json','failure_reproduction.json','equality_semantics.json',
         'root_switch_audit.json','independent_reference.json','synthetic_controls.csv',
         'publication_route.json','qc.json','manifest.json')
SCHEMAS = {
 'authority.json': (('source_hashes','review_valid','receipt_matches'),('records',),()),
 'failure_reproduction.json': (('reproduced','original_preserved','observed_route','uncertified'),('localizations','probes'),('seconds',)),
 'equality_semantics.json': (('exact_binary64_check','owner_rule_distinct','nonzero_inside','monotone_refuted'),(),()),
 'root_switch_audit.json': (('provisional_only','root_count_available','coverage_complete','scalar_comparison'),('roots','sampled_nodes'),()),
 'independent_reference.json': (('complete','identity','equality_refuted'),('cells','signed','crossings','equal','unresolved'),('seconds',)),
 'publication_route.json': (('controls_passed','legacy_unreachable','one_review','traceback_bound','independent_failure','rerun_rejected'),('controls',),('seconds',)),
}
COLUMNS = ('fixture','family','topology','expected_roots','observed_status','observed_reason',
           'reference_passed','observation_preserved','passed','evidence_sha256')
FIXTURES = ('duplicates','simple_crossing','tangent','near_double','nearby_roots','endpoint',
            'true_interval','onset_switch','tiny_interval','nonzero_interior','multiway')
REASONS = {'not_executed','reviewed_once','exact_reproduction','different_result','exact_binary64_semantics',
           'reference_complete','reference_unresolved','linear_controls','publication_control_failure',
           'governed_failure','numerical_timeout','synthetic_control_failure','shared_integrity_failure',
           'diagnosis_complete','reference_limit'}


def empty():
    return {name:dict(schema_version=1,status='unavailable',reason='not_executed',
       flags=dict.fromkeys(spec[0]),counts=dict.fromkeys(spec[1]),timings=dict.fromkeys(spec[2]))
       for name,spec in SCHEMAS.items()}


def fill(records,name,*,status='complete',reason,flags=None,counts=None,timings=None):
    item=records[name]
    item.update(status=status,reason=reason)
    for kind,values in (('flags',flags),('counts',counts),('timings',timings)):
        if values:
            if set(values)-set(item[kind]):raise ValueError('unknown_record_field')
            item[kind].update(values)


def validate_record(name,value):
    if set(value)!={'schema_version','status','reason','flags','counts','timings','evidence_sha256'}:
        raise ValueError('record_schema')
    if value['schema_version']!=1 or value['status'] not in ('complete','partial','invalid','unavailable') or value['reason'] not in REASONS:
        raise ValueError('record_status')
    for kind,keys in zip(('flags','counts','timings'),SCHEMAS[name]):
        if set(value[kind])!=set(keys):raise ValueError('record_fields')
        for x in value[kind].values():
            if x is None:continue
            if kind=='flags' and type(x)is not bool:raise ValueError('record_boolean')
            if kind=='counts' and (type(x)is not int or x<0):raise ValueError('record_count')
            if kind=='timings' and (type(x)not in (int,float) or x<0):raise ValueError('record_time')
    if not hash_string(value['evidence_sha256']):raise ValueError('record_hash')
    finite(value)


def derive(local):
    """Decisions from persisted observations; checking cannot create missing records."""
    local=Path(local);outcome=load(local/'outcome.json')
    if set(outcome)!={'schema_version','records','reason','execution_valid','timings'} or outcome['schema_version']!=1:
        raise ValueError('outcome_schema')
    records=outcome['records']
    if set(records)!=set(SCHEMAS):raise ValueError('outcome_records')
    rows=load(local/'control_rows.json')
    controls_ok=(tuple(row['fixture'] for row in rows)==FIXTURES and all(
       row['reference_passed'] is True and row['observation_preserved'] is True and row['passed'] is True for row in rows))
    pub=load(local/'publication_observations.json')
    expected={'controls_passed','legacy_unreachable','one_review','traceback_bound','independent_failure','rerun_rejected'}
    if set(pub)!=expected or any(type(x)is not bool for x in pub.values()):raise ValueError('publication_observations')
    if records['publication_route.json']['flags'] != pub and records['publication_route.json']['status']!='unavailable':
        raise ValueError('publication_cross_file')
    publication='PA' if all(pub.values()) else 'PB' if records['publication_route.json']['status']!='unavailable' else 'PD'
    if outcome['reason']=='shared_integrity_failure':publication='PD'
    ref=records['independent_reference.json']['flags']
    repro=records['failure_reproduction.json']['flags']
    sem=records['equality_semantics.json']['flags']
    audit=records['root_switch_audit.json']['flags']
    authority=records['authority.json']['flags']
    numeric='NF'
    if outcome['execution_valid'] and controls_ok and all(authority.values()) and repro['reproduced'] and ref['complete'] and audit['scalar_comparison']:
        if sem['monotone_refuted'] and sem['nonzero_inside']:numeric='NC'
        elif ref['equality_refuted'] and sem['nonzero_inside']:numeric='NE'
    reference_result=load(local/'reference_summary.json')
    if set(reference_result)!= {'topology','complete','root_count'} or reference_result['topology'] not in tuple('ABCDEFGHI'):
        raise ValueError('reference_summary_schema')
    if ref['complete'] is not None and ref['complete']!=reference_result['complete']:raise ValueError('reference_cross_file')
    if records['root_switch_audit.json']['counts']['roots']!=reference_result['root_count']:raise ValueError('root_cross_file')
    attempt=local/'access_attempt.json';receipt=local/'access_materialized.json'
    exposed=receipt.exists()
    if exposed:
        value=load(receipt)
        if set(value)!={'schema_version','selected_sha256','attempt_sha256'} or value['schema_version']!=1 or not attempt.exists():raise ValueError('access_receipt')
        if sha(attempt)!=value['attempt_sha256'] or sha(local/'selected_geometry.json')!=value['selected_sha256']:raise ValueError('access_binding')
    q=dict(schema_version=1,status='complete' if numeric!='NF' else 'partial' if outcome['execution_valid'] else 'invalid',
        execution_valid=outcome['execution_valid'],numerical=numeric,topology=reference_result['topology'],publication=publication,
        readiness=3 if publication=='PA' else 4,states_reopened=int(exposed),edges_reopened=int(exposed),
        exposure_uncertain=attempt.exists() and not exposed,reason=outcome['reason'],
        controls_passed=sum(row['passed'] is True for row in rows),timings=outcome['timings'])
    if type(q['execution_valid'])is not bool or q['reason'] not in REASONS:raise ValueError('outcome_status')
    for x in q['timings'].values():
        if type(x)not in (int,float) or x<0:raise ValueError('timing_value')
    finite(q)
    return records,rows,q


def csv_bytes(rows):
    output=io.StringIO(newline='');writer=csv.DictWriter(output,fieldnames=COLUMNS,lineterminator='\n');writer.writeheader()
    for row in rows:
        if set(row)!=set(COLUMNS):raise ValueError('control_fields')
        if row['fixture'] not in FIXTURES or row['family'] not in ('engineering','expanding') or row['topology'] not in tuple('ABCDEFGHI'):raise ValueError('control_label')
        writer.writerow({k: str(v).lower() if type(v)is bool else '' if v is None else v for k,v in row.items()})
    return output.getvalue().encode()


def close(folder,environment):
    folder=Path(folder);local=folder/'local'
    records,rows,q=derive(local)
    private={p.relative_to(local).as_posix():sha(p) for p in sorted(local.rglob('*')) if p.is_file() and p.name!='private_index.json'}
    put(local/'private_index.json',dict(schema_version=1,files=private))
    index_hash=sha(local/'private_index.json')
    for name,record in records.items():
        record={**record,'evidence_sha256':index_hash};validate_record(name,record);put(folder/name,record)
    put_bytes(folder/'synthetic_controls.csv',csv_bytes(rows));put(folder/'qc.json',q)
    put(folder/'manifest.json',dict(schema_version=1,authority=environment,
      outputs={name:sha(folder/name) for name in NAMES if name!='manifest.json'},private_index_sha256=index_hash))
    return publication_check(folder)


def publication_check(folder):
    folder=Path(folder);local=folder/'local'
    if {p.name for p in folder.iterdir() if p.is_file()}!=set(NAMES):raise ValueError('public_inventory')
    m=load(folder/'manifest.json')
    if set(m)!= {'schema_version','authority','outputs','private_index_sha256'} or m['schema_version']!=1:raise ValueError('manifest_schema')
    if set(m['outputs'])!=set(NAMES)-{'manifest.json'}:raise ValueError('manifest_inventory')
    for name,h in m['outputs'].items():
        if not hash_string(h) or sha(folder/name)!=h:raise ValueError('public_hash')
    index=local/'private_index.json'
    if sha(index)!=m['private_index_sha256']:raise ValueError('private_index_hash')
    values=load(index)
    if set(values)!= {'schema_version','files'} or values['schema_version']!=1:raise ValueError('index_schema')
    for name,h in values['files'].items():
        if Path(name).is_absolute() or '..' in Path(name).parts or not hash_string(h) or sha(local/name)!=h:raise ValueError('private_hash')
    records,rows,q=derive(local)
    if load(folder/'qc.json')!=q:raise ValueError('false_decision_or_counters')
    for name,record in records.items():
        expected={**record,'evidence_sha256':m['private_index_sha256']}
        actual=load(folder/name);validate_record(name,actual)
        if actual!=expected:raise ValueError('cross_file_record')
    if (folder/'synthetic_controls.csv').read_bytes()!=csv_bytes(rows):raise ValueError('control_cross_file')
    for row in rows:
        if row['evidence_sha256'] not in values['files'].values():raise ValueError('control_evidence')
    for name in NAMES:
        raw=(folder/name).read_text()
        if any(s in raw for s in ('/Users/','/private/','"defenders"','"carrier"','"traceback"','"state":','"edge":')):raise ValueError('private_value_leak')
    return dict(valid=True,files=len(NAMES),numerical=q['numerical'],publication=q['publication'],readiness=q['readiness'],historical_journal_replayed=False)
