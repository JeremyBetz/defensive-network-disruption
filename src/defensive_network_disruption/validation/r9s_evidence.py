"""R9S strict persisted-only validation; no field calls or journal replay."""
import csv
import io
from pathlib import Path
from .r9j_evidence import canonical,digest,load,put,put_bytes,sha,finite,hash_string
from ..geometry.r9s_trace import check_trace,summarize
from . import r9s_authority as source

NAMES=('authority.json','trace_completeness.json','sign_pattern.json','transition_compatibility.json',
       'synthetic_controls.csv','publication_route.json','runtime_summary.json','qc.json','manifest.json')
COLUMNS=('fixture','expected','observed','expected_outcome','observed_outcome','passed','evidence_sha256')


def csv_bytes(rows):
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=COLUMNS,lineterminator='\n');writer.writeheader()
    for row in rows:
        if set(row)!=set(COLUMNS):raise ValueError('control_schema')
        writer.writerow({k:str(v).lower() if type(v)is bool else v for k,v in row.items()})
    return stream.getvalue().encode()


def check_closure(local):
    """Consume immutable one-pass authority, preserving its legacy digest meaning."""
    from .checkpoint_ci_authority import FailureController
    local=Path(local);a=load(local/'numerical_failure/linear_authority.json')
    original=load(local/'numerical_failure/original_failure.json')
    FailureController(local/'numerical_failure').validate()
    legacy=a['legacy'];snapshot=legacy['snapshot'];failure=a['failure']
    if legacy['snapshot_sha256']!=digest(snapshot) or a['lifecycle_snapshot_sha256']!=digest(snapshot['snapshot']):raise ValueError('snapshot_hash')
    if sha(local/'diagnostic_journal.jsonl')!=a['raw_sha256']:raise ValueError('journal_raw_hash')
    if failure['traceback_sha256']!=original['traceback_sha256'] or failure['exception']!=original['exception_type'] or failure['stage']!='geometry':raise ValueError('failure_binding')
    if original['stage']!='binary64_transition_inspection':raise ValueError('precise_stage')
    package=load(local/'numerical_publication/qc.json')
    for name in ('manifest','evidence'):
        if load(local/f'numerical_publication/{name}.json')!=package:raise ValueError('closure_cross_file')
    if set(package)!= {'schema_version','accepted','checks','authority'} or package['schema_version']!=2 or package['accepted'] is not False or package['checks']!={'terminal_valid':True} or package['authority']!=legacy:raise ValueError('closure_package')
    c=snapshot['snapshot']['counters']
    if c['edges_completed']!=0 or c['field_evaluations_completed']!=0 or c['field_evaluations_started']!=0:raise ValueError('fabricated_candidate_work')
    validation=load(local/'closure_validation.json')
    if validation!=dict(validated=True,authority_sha256=sha(local/'numerical_failure/linear_authority.json'),traceback_sha256=original['traceback_sha256']):raise ValueError('closure_validation')
    return a


def derive(local,index):
    # Import only the frozen catalog; no numerical acceptance is executed here.
    from .r9s_acceptance import FIXTURES,PATTERNS,SEQUENCES,OUTCOMES
    local=Path(local);outcome=load(local/'outcome.json')
    if set(outcome)!= {'schema_version','execution_valid','reason','timings'} or outcome['schema_version']!=1 or type(outcome['execution_valid'])is not bool or outcome['reason']not in ('complete','timeout','execution_failure'):raise ValueError('outcome_schema')
    timing=outcome['timings'];keys={'governed_wall','exclusive_compute','inclusive_numerical','io','waiting','unattributed'}
    if set(timing)!=keys or any(type(v)not in (int,float) or v<0 for v in timing.values()):raise ValueError('timing_schema')
    if abs(sum(timing[k] for k in ('exclusive_compute','io','waiting','unattributed'))-timing['governed_wall'])>max(.1,timing['governed_wall']*.01):raise ValueError('timing_reconciliation')
    rows=load(local/'controls.json');byhash={h:local/p for p,h in index.items()}
    for i,row in enumerate(rows):
        if i>=10 or set(row)!=set(COLUMNS) or row['fixture']!=FIXTURES[i] or row['expected']!=PATTERNS[i] or row['expected_outcome']!=OUTCOMES[i] or type(row['passed'])is not bool:raise ValueError('control_catalog')
        detail=load(byhash[row['evidence_sha256']]);actual=summarize(detail['trace'])
        sequence=''.join({-1:'N',0:'Z',1:'P'}[detail['trace']['probes'][n]['sign']] for n in detail['trace']['sorted_ordinals'])
        observed=detail['trace']['outcome']['message'] or 'returned'
        passed=actual['complete'] and actual['pattern']==PATTERNS[i] and sequence==SEQUENCES[i] and observed==OUTCOMES[i]
        if row['passed']!=passed or row['observed']!=actual['pattern'] or row['observed_outcome']!=observed or detail['summary']!=actual:raise ValueError('false_control')
    controls_ok=len(rows)==10 and all(x['passed'] for x in rows)
    pub=None
    if (local/'publication_observations.json').exists():
        pub=load(local/'publication_observations.json')
        if set(pub)!= {'rows','summary'}:raise ValueError('publication_schema')
        if len(pub['rows'])!=5 or pub['summary']['counts']!={'controls':5,'linear_reviews':5}:raise ValueError('publication_count')
        expected_names=('success','pre_access','numerical_failure','publication_init','publisher_failure')
        if tuple(r['fixture'] for r in pub['rows'])!=expected_names:raise ValueError('publication_control_inventory')
        for row in pub['rows']:
            p=local/'publication_controls'/row['fixture']
            if sha(p/'linear_authority.json')!=row['evidence_sha256']:raise ValueError('publication_control_hash')
            a=load(p/'linear_authority.json')
            expected_status='success' if row['fixture']=='success' else 'failure'
            if a['legacy']['snapshot']['snapshot']['status']!=expected_status or row['passed'] is not True or row['reason']!='legacy_unreachable':raise ValueError('publication_observed_status')
            if a['legacy']['snapshot_sha256']!=digest(a['legacy']['snapshot']):raise ValueError('publication_snapshot')
            if row['fixture']!='success':
                from .checkpoint_ci_authority import FailureController
                FailureController(p).validate()
                if a['failure']['traceback_sha256']!=load(p/'original_failure.json')['traceback_sha256']:raise ValueError('control_traceback')
            if row['fixture'] in ('publisher_failure','publication_init') and not (p/'publication_failure.json').exists():raise ValueError('missing_publication_failure')
        expected_flags=dict.fromkeys(('controls_passed','legacy_unreachable','one_review','traceback_bound','independent_failure','rerun_rejected'),True)
        if pub['summary']['flags']!=expected_flags:raise ValueError('publication_observation_flags')
    pub_ok=pub is not None and all(pub['summary']['flags'].values()) and all(r['passed'] for r in pub['rows'])
    attempt=(local/'access_attempt.json').exists();exposed=(local/'access_materialized.json').exists()
    if exposed:
        receipt=load(local/'access_materialized.json')
        if receipt!=dict(schema_version=1,attempt_sha256=sha(local/'access_attempt.json'),selected_sha256=source.SOURCES['selected'][2]) or sha(local/'retained/selected.json')!=source.SOURCES['selected'][2]:raise ValueError('access_receipt')
    summary=None;closure=None
    if (local/'trace.json').exists():
        if not exposed:raise ValueError('trace_without_exposure')
        records={}
        for label,(_,_,h) in source.SOURCES.items():
            p=local/'retained'/f'{label}.json'
            if sha(p)!=h:raise ValueError('retained_authority_hash')
            if label!='selected':records[label]=load(p)
        args,ref,structures=source.context(records)
        trace=load(local/'trace.json')
        if (trace['arguments'],trace['reference'],trace['structures'])!=(args,ref,structures):raise ValueError('invocation_authority')
        # Each consolidated view must equal its synchronized per-call evidence.
        labels={'arguments':[args],'window':trace['windows'],'probe_attempt':trace['attempts'],'probe':trace['probes'],'final_cache':[trace['final']]}
        for label,expected in labels.items():
            actual=[load(local/p) for p in sorted(index) if p.startswith('observations/') and p.endswith('_'+label+'.json')]
            if actual!=expected:raise ValueError('incremental_trace_mismatch')
        summary=summarize(trace,retained=True);closure=check_closure(local)
        if closure['exposure']['edges_opened']!=1:raise ValueError('projection_exposure')
    valid=outcome['execution_valid'] and controls_ok and pub_ok and not (attempt and not exposed)
    if outcome['execution_valid'] and summary is None:raise ValueError('missing_trace')
    decision=summary['diagnosis'] if valid and summary else 'BF';readiness=summary['readiness'] if valid and summary else 4
    qc=dict(schema_version=1,status='complete' if valid and summary['complete'] else 'invalid' if not valid else 'partial',
       execution_valid=bool(valid),diagnosis=decision,diagnostic_readiness=readiness,operational_repair='unresolved',
       states_reopened=int(exposed),edges_reopened=int(exposed),exposure_uncertain=attempt and not exposed,
       trace_count=0 if summary is None else summary['count'],candidates_started=0,candidates_completed=0,edges_completed=0,controls_passed=sum(x['passed'] for x in rows),
       numerical_rejection=None if summary is None else summary['reproduced'],publication='PA' if pub_ok and closure else 'PD')
    def unavailable():return {'available':False}
    records={
      'authority.json':dict(schema_version=1,checkpoint=load(local/'authority.json'),source_hashes={k:v[2] for k,v in source.SOURCES.items()},retained_only=True),
      'trace_completeness.json':unavailable() if summary is None else {k:summary[k] for k in ('complete','count','attempts','windows','outer_covered','limited','reproduced')},
      'sign_pattern.json':unavailable() if summary is None else {k:summary[k] for k in ('pattern','zeros','zero_runs','reversals','ternary_changes','causal_attribution')},
      'transition_compatibility.json':unavailable() if summary is None else {k:summary[k] for k in ('compatibility','mathematical_support','diagnosis','readiness','operational_repair')},
      'publication_route.json':dict(controls=5 if pub else 0,passed=bool(pub_ok),actual_closure_valid=closure is not None,
             precise_stage='binary64_transition_inspection',legacy_stage='geometry',linear_review_per_closure=1 if closure else None,
             authority_sha256=None if closure is None else sha(local/'numerical_failure/linear_authority.json')),
      'runtime_summary.json':dict(schema_version=1,**timing),
      'qc.json':qc,
    }
    finite(records)
    wrapped={}
    for name,value in records.items():
        status=qc['status'] if name=='qc.json' else 'unavailable' if value=={'available':False} else 'complete' if valid else 'invalid'
        wrapped[name]=dict(schema_version=1,status=status,reason=outcome['reason'],data=value)
    return wrapped,rows


def close(folder):
    folder=Path(folder);local=folder/'local'
    index={p.relative_to(local).as_posix():sha(p) for p in sorted(local.rglob('*')) if p.is_file() and p.name!='private_index.json'}
    records,rows=derive(local,index)
    put(local/'private_index.json',dict(schema_version=1,files=index));h=sha(local/'private_index.json')
    for name,value in records.items():put(folder/name,{**value,'evidence_sha256':h})
    put_bytes(folder/'synthetic_controls.csv',csv_bytes(rows))
    put(folder/'manifest.json',dict(schema_version=1,authority=load(local/'authority.json'),private_index_sha256=h,outputs={n:sha(folder/n) for n in NAMES if n!='manifest.json'}))
    return publication_check(folder)


def publication_check(folder):
    folder=Path(folder);local=folder/'local'
    if {p.name for p in folder.iterdir() if p.is_file()}!=set(NAMES):raise ValueError('public_inventory')
    m=load(folder/'manifest.json')
    if set(m)!= {'schema_version','authority','private_index_sha256','outputs'} or m['schema_version']!=1 or set(m['outputs'])!=set(NAMES)-{'manifest.json'}:raise ValueError('manifest_schema')
    for name,h in m['outputs'].items():
        if not hash_string(h) or sha(folder/name)!=h:raise ValueError('public_hash')
    if sha(local/'private_index.json')!=m['private_index_sha256']:raise ValueError('private_index_hash')
    index=load(local/'private_index.json')
    if set(index)!= {'schema_version','files'} or index['schema_version']!=1:raise ValueError('index_schema')
    for name,h in index['files'].items():
        p=Path(name)
        if p.is_absolute() or '..' in p.parts or not hash_string(h) or sha(local/p)!=h:raise ValueError('private_hash')
    if m['authority']!=load(local/'authority.json'):raise ValueError('authority_cross_file')
    records,rows=derive(local,index['files'])
    for name,value in records.items():
        if (folder/name).read_bytes()!=canonical(load(folder/name)):raise ValueError('noncanonical_public')
        if load(folder/name)!={**value,'evidence_sha256':m['private_index_sha256']}:raise ValueError('false_decision_or_cross_file')
    if (folder/'synthetic_controls.csv').read_bytes()!=csv_bytes(rows):raise ValueError('csv_cross_file')
    for name in NAMES:
        raw=(folder/name).read_text()
        if any(x in raw for x in ('/Users/','/private/','"carrier"','"defenders"','"traceback"','"state":','"edge":','"bits":')):raise ValueError('private_leak')
    return dict(valid=True,files=len(NAMES),**{k:records['qc.json']['data'][k] for k in ('diagnosis','diagnostic_readiness','states_reopened','edges_reopened','publication')})
