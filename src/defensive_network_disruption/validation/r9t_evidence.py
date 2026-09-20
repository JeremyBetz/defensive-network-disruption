"""Strict R9T stored-evidence publication. No field evaluation or journal replay."""
import csv
import io
import math
from pathlib import Path
from .r9j_evidence import canonical,digest,load,put,put_bytes,sha,finite,hash_string
from .r9r_evidence import frozen_catalog,historical_flags
from . import r9t_authority as source

NAMES=('repair_contract.json','synthetic_trace_controls.csv','negative_controls.csv',
 'retained_trace_resolution.json','retained_candidate_replay.json','historical_regressions.csv',
 'performance.json','publication_tripwire.json','qc.json','manifest.json')
COLUMNS={
 'synthetic_trace_controls.csv':('fixture','family','expected','observed','passed','evidence_sha256'),
 'negative_controls.csv':('fixture','blocked','reason','evidence_sha256'),
 'historical_regressions.csv':('fixture','candidate','status','components','permutations','structure_exact','production_preserved','verification_preserved','reason','evidence_sha256')}
REASONS=('complete','synthetic_failure','historical_incompatibility','trace_blocked','candidate_unresolved','timeout','execution_failure')
TIMES=('governed_wall','exclusive_compute','inclusive_numerical','io','waiting','unattributed')


def csv_bytes(name,rows):
    stream=io.StringIO(newline='');w=csv.DictWriter(stream,fieldnames=COLUMNS[name],lineterminator='\n');w.writeheader()
    for row in rows:
        if set(row)!=set(COLUMNS[name]) or not hash_string(row['evidence_sha256']):raise ValueError('csv_schema')
        if any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-' for c in row['fixture']):raise ValueError('fixture_privacy')
        w.writerow({k:str(v).lower() if type(v)is bool else v for k,v in row.items()})
    return stream.getvalue().encode()


def publication_controls(local):
    value=load(local/'publication_observations.json')
    if set(value)!= {'rows','summary'}:raise ValueError('publication_controls_schema')
    rows,summary=value['rows'],value['summary']
    if len(rows)!=5 or [r['fixture'] for r in rows]!=['success','pre_access','numerical_failure','publication_init','publisher_failure']:raise ValueError('publication_inventory')
    for row in rows:
        p=local/'publication_controls'/row['fixture'];a=load(p/'linear_authority.json')
        if sha(p/'linear_authority.json')!=row['evidence_sha256'] or row['passed'] is not True or row['reason']!='legacy_unreachable':raise ValueError('publication_control')
        if a['legacy']['snapshot_sha256']!=digest(a['legacy']['snapshot']):raise ValueError('control_snapshot')
        expected='success' if row['fixture']=='success' else 'failure'
        if a['legacy']['snapshot']['snapshot']['status']!=expected:raise ValueError('control_status')
        if expected=='failure':
            from .checkpoint_ci_authority import FailureController
            FailureController(p).validate()
            if a['failure']['traceback_sha256']!=load(p/'original_failure.json')['traceback_sha256']:raise ValueError('control_traceback')
        if row['fixture']in ('publication_init','publisher_failure') and not (p/'publication_failure.json').exists():raise ValueError('publisher_failure_missing')
    flags=dict.fromkeys(('controls_passed','legacy_unreachable','one_review','traceback_bound','independent_failure','rerun_rejected'),True)
    if set(summary)!= {'flags','counts','timings'} or summary['flags']!=flags or summary['counts']!={'controls':5}:raise ValueError('publication_flags')
    return summary


def check_closure(local):
    """Validate immutable review receipt and persisted package, without replay."""
    from .checkpoint_ci_authority import FailureController
    a=load(local/'closure_authority.json');legacy=a['legacy'];snapshot=legacy['snapshot']
    if legacy['snapshot_sha256']!=digest(snapshot) or a['lifecycle_snapshot_sha256']!=digest(snapshot['snapshot']):raise ValueError('snapshot_hash')
    if sha(local/'diagnostic_journal.jsonl')!=a['raw_sha256']:raise ValueError('journal_hash')
    package=load(local/'numerical_publication/qc.json')
    for n in ('manifest','evidence'):
        if load(local/f'numerical_publication/{n}.json')!=package:raise ValueError('closure_cross_file')
    success=snapshot['diagnostic_success']
    if set(package)!= {'schema_version','accepted','checks','authority'} or package['schema_version']!=2 or package['accepted']!=success or package['checks']!={'terminal_valid':True} or package['authority']!=legacy:raise ValueError('closure_package')
    failure=a['failure']
    if failure:
        FailureController(local/'numerical_failure').validate()
        original=load(local/'numerical_failure/original_failure.json')
        if failure['traceback_sha256']!=original['traceback_sha256'] or failure['exception']!=original['exception_type']:raise ValueError('failure_binding')
    elif not success:raise ValueError('nonterminal_closure')
    c=snapshot['snapshot']['counters']
    if any(c[k]!=0 for k in ('edges_completed','states_completed','field_evaluations_completed','field_evaluations_started')):raise ValueError('fabricated_empirical_completion')
    validation=load(local/'closure_validation.json')
    if validation!=dict(validated=True,linear_reviews=1,authority_sha256=sha(local/'closure_authority.json')):raise ValueError('closure_validation')
    return a


def trace_control_observation(detail):
    from ..geometry import r9t_transition as t
    from .r9t_acceptance import primitive
    name=detail['fixture']
    if name in ('duplicates','no_root'):
        top=source.topology(source.decode(detail['topology']))
        return 'tie' if name=='duplicates' and top.classification=='C' and top.complete else 'no_switch' if name=='no_root' and top.classification=='A' and top.complete else 'wrong'
    if name=='two_crossings':
        results=[t.validate_evidence(source.evidence(v)) for v in detail['results']]
        t.check_order([v.transition.first_post for v in results])
        return 'two' if len(results)==2 and all(v.canonical_index==5 for v in results) else 'wrong'
    try:result=t.canonicalize(*source.input_tuple(detail['input']))
    except t.VerificationError as error:
        if detail.get('rejection')!=str(error) or 'result' in detail:raise ValueError('rejection_evidence')
        return 'blocked'
    if detail.get('result')!=primitive(result):raise ValueError('canonical_evidence')
    return str(result.canonical_index)


def derive(local,index):
    from .r9t_acceptance import FIXTURES,EXPECTED,NEGATIVES,primitive
    from ..geometry import r9t_transition as t
    local=Path(local);outcome=load(local/'outcome.json')
    if set(outcome)!= {'schema_version','execution_valid','reason','timings','performance'} or outcome['schema_version']!=1 or type(outcome['execution_valid'])is not bool or outcome['reason']not in REASONS:raise ValueError('outcome_schema')
    timings=outcome['timings']
    if set(timings)!=set(TIMES) or any(type(v)not in (int,float) or not math.isfinite(v) or v<0 for v in timings.values()):raise ValueError('timings')
    if abs(sum(timings[k] for k in ('exclusive_compute','io','waiting','unattributed'))-timings['governed_wall'])>max(.1,timings['governed_wall']*.01):raise ValueError('timing_reconciliation')
    perf=outcome['performance']
    if set(perf)!= {'localization_calls','subdivisions','floats_inspected','max_depth','unresolved'} or any(type(v)is not int or v<0 for v in perf.values()):raise ValueError('performance_schema')
    byhash={h:local/p for p,h in index.items()};rows={n:load(local/(n+'.json')) for n in COLUMNS};catalog=frozen_catalog()
    for name,items in rows.items():
        csv_bytes(name,items)
        for i,row in enumerate(items):
            if row['evidence_sha256']not in byhash:raise ValueError('unbound_observation')
            detail=load(byhash[row['evidence_sha256']])
            if name=='synthetic_trace_controls.csv':
                if i>=len(FIXTURES) or row['fixture']!=FIXTURES[i] or row['expected']!=EXPECTED[i] or row['family']!=('field' if FIXTURES[i]=='duplicates' else 'engineering'):raise ValueError('fixture_catalog')
                observed=trace_control_observation(detail)
                if row['observed']!=observed or type(row['passed'])is not bool or row['passed']!=(observed==EXPECTED[i]):raise ValueError('false_control')
            elif name=='negative_controls.csv':
                if i>=len(NEGATIVES) or row['fixture']!=NEGATIVES[i] or detail!={k:row[k] for k in ('blocked','reason')} or type(row['blocked'])is not bool or row['blocked']!=(row['reason'] in ('VerificationError','ValueError','TimeoutError','TypeError')):raise ValueError('negative_observation')
            else:
                if i>=len(catalog):raise ValueError('historical_inventory')
                label,candidate,components,permutations,expected_hash=catalog[i]
                if (row['fixture'],row['candidate'],row['components'])!=(label,candidate,components) or digest(detail['expected'])!=expected_hash:raise ValueError('historical_authority')
                if detail.get('baseline')!=detail['old']:raise ValueError('inherited_disagreement')
                flags=historical_flags(detail)
                if tuple(row[k] for k in ('structure_exact','production_preserved','verification_preserved'))!=flags or row['status']!=('passed' if all(flags) else 'blocked'):raise ValueError('historical_observation')
                if row['permutations']!=(detail['new']['permutations'] if detail['new']else 0) or row['status']=='passed' and row['permutations']!=permutations:raise ValueError('permutation_count')
    top,neg,hist=(rows[n] for n in COLUMNS)
    controls=len(top)==15 and all(r['passed'] for r in top);negatives=len(neg)==10 and all(r['blocked'] for r in neg)
    history=len(hist)==108 and sum(r['components'] for r in hist)==366 and sum(r['permutations'] for r in hist)==399 and all(r['status']=='passed' for r in hist)
    pub=publication_controls(local) if (local/'publication_observations.json').exists() else None
    trace_attempt=(local/'trace_attempt.json').exists();trace_read=(local/'trace_materialized.json').exists()
    resolved=False;suffix=0;trace_count=0
    if trace_read:
        receipt=load(local/'trace_materialized.json')
        if receipt!=dict(schema_version=1,attempt_sha256=sha(local/'trace_attempt.json'),trace_sha256=sha(local/'retained/trace.json')):raise ValueError('trace_receipt')
        bound=load(local/'retained_bindings.json')
        if bound!=source.allowlist(Path(__file__).resolve().parents[3]):raise ValueError('retained_authority_rebinding')
        for name,h in bound.items():
            if name=='retained/selected.json':continue
            if sha(local/'retained'/name)!=h:raise ValueError('retained_copy_hash')
        trace=load(local/'retained/trace.json');trace_count=len(trace['probes'])
        records={Path(n).stem:load(local/'retained'/n) for n in bound if n.startswith('retained/') and n!='retained/selected.json'}
        if (local/'trace_resolution.json').exists():
            resolution=load(local/'trace_resolution.json')
            try:result=source.resolve_saved(trace,records)
            except t.VerificationError as error:
                if resolution!=dict(status='blocked',exception=type(error).__name__,reason=str(error)):raise ValueError('false_trace_block')
            else:
                if resolution!=dict(status='accepted',evidence=primitive(result)):raise ValueError('false_trace_resolution')
                resolved=True;suffix=result.suffix_length
        elif outcome['execution_valid'] or not (local/'outer_failure/original_failure.json').exists():
            raise ValueError('missing_trace_resolution')
    access=(local/'access_attempt.json').exists();exposed=(local/'access_materialized.json').exists()
    if exposed:
        receipt=load(local/'access_materialized.json')
        if not resolved or receipt!=dict(schema_version=1,attempt_sha256=sha(local/'access_attempt.json'),selected_sha256=sha(local/'selected_geometry.json')):raise ValueError('geometry_receipt')
        if receipt['selected_sha256']!=load(local/'retained_bindings.json')['retained/selected.json']:raise ValueError('selected_authority')
    uncertainty=(trace_attempt and not trace_read) or (access and not exposed)
    closure=None
    if (local/'closure_authority.json').exists():
        try:closure=check_closure(local)
        except (ValueError,FileNotFoundError):
            if not ((local/'numerical_failure/publication_failure.json').exists() or (local/'publication_failure/original_failure.json').exists()):raise
    completed=bool(closure and closure['legacy']['snapshot']['diagnostic_success'])
    runtime_match=False
    if closure:
        if closure['exposure']['edges_opened']!=int(exposed):raise ValueError('exposure_mismatch')
    if completed:
        result=source.decode(load(local/'retained_result.json'))
        if not exposed or not result['deterministic'] or not result['certificate_evidence'] or result['intervals']not in (512,1024,2048,4096,8192,16384):raise ValueError('candidate_result')
        matches=load(local/'runtime_trace_matches.json')
        runtime_match=bool(matches) and all(v==load(local/'trace_resolution.json')['evidence'] for v in matches)
        if not runtime_match:raise ValueError('runtime_trace_disagreement')
    gates=controls and negatives and history and pub is not None
    valid=outcome['execution_valid'] and pub is not None and not uncertainty
    # No retained result can turn missing mandatory pre-access observations into
    # a valid but merely incomplete B outcome.
    if trace_attempt and not gates:valid=False
    if access and closure is None:valid=False
    if not valid:classification,readiness='E',4
    elif any(r['status']=='blocked' for r in hist):classification,readiness='C',3
    elif not controls or not negatives:classification,readiness='E',4
    elif completed and runtime_match:classification,readiness=('A',1) if history else ('B',2)
    elif trace_read:classification,readiness='D',3
    else:classification,readiness='E',4
    qc=dict(schema_version=1,classification=classification,readiness=readiness,execution_valid=valid,
        reason=outcome['reason'],trace_records_read=int(trace_read),trace_resolved=resolved,
        states_reopened=int(exposed),edges_reopened=int(exposed),exposure_uncertain=uncertainty,
        diagnostic_candidates_completed=int(completed),empirical_edges_completed=0,empirical_states_completed=0,
        trace_controls_passed=sum(r['passed'] for r in top),negative_controls_blocked=sum(r['blocked'] for r in neg),
        cases_run=len(hist),cases_passed=sum(r['status']=='passed' for r in hist),
        references_passed=sum(r['components'] for r in hist if r['status']=='passed'),
        permutations_passed=sum(r['permutations'] for r in hist if r['status']=='passed'),publication_valid=pub is not None and (not access or closure is not None))
    data={
      'repair_contract.json':dict(schema_version=1,authority=load(local/'authority.json'),rule='complete_terminal_suffix',minimum_confirmation=2,finite_convention=True,mathematical_equality_from_zeros=False,historical_boundary_moves_allowed=False),
      'retained_trace_resolution.json':dict(read=trace_read,complete=trace_read and trace_count==65,resolved=resolved,probes=trace_count,suffix_length=suffix,additional_trace_probes=0),
      'retained_candidate_replay.json':dict(materialized=exposed,exposure_uncertain=access and not exposed,completed=completed,runtime_matches_saved=runtime_match,invocations=int((local/'candidate_invocation.json').exists()),historical_downstream_comparison='unavailable'),
      'performance.json':dict(counts=perf,timings=timings),
      'publication_tripwire.json':dict(controls=pub,actual_closure=closure is not None,linear_reviews=1 if closure else 0,diagnostic_only=True),
      'qc.json':qc}
    finite(data)
    status='complete' if classification=='A' else 'blocked' if valid else 'invalid'
    records={n:dict(schema_version=1,status='unavailable' if n=='retained_trace_resolution.json' and not trace_read or n=='retained_candidate_replay.json' and not access else status,reason=outcome['reason'],data=v) for n,v in data.items()}
    return records,rows


def close(folder):
    folder=Path(folder);local=folder/'local'
    index={p.relative_to(local).as_posix():sha(p) for p in sorted(local.rglob('*')) if p.is_file() and p.name!='private_index.json'}
    records,rows=derive(local,index)
    put(local/'private_index.json',dict(schema_version=1,files=index));h=sha(local/'private_index.json')
    for name,value in records.items():put(folder/name,{**value,'evidence_sha256':h})
    for name,values in rows.items():put_bytes(folder/name,csv_bytes(name,values))
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
        if p.is_absolute() or '..'in p.parts or not hash_string(h) or sha(local/p)!=h:raise ValueError('private_hash')
    if load(local/'authority.json')!=m['authority']:raise ValueError('authority_cross_file')
    records,rows=derive(local,index['files'])
    for name,v in records.items():
        expected={**v,'evidence_sha256':m['private_index_sha256']}
        if (folder/name).read_bytes()!=canonical(expected):raise ValueError('false_decision_or_cross_file')
    for name,v in rows.items():
        if (folder/name).read_bytes()!=csv_bytes(name,v):raise ValueError('csv_cross_file')
    for name in NAMES:
        raw=(folder/name).read_text()
        if any(x in raw for x in ('/Users/','/private/','"carrier"','"defenders"','"traceback"','"state":','"edge":','"bits":')):raise ValueError('private_leak')
    q=records['qc.json']['data']
    return dict(valid=True,files=len(NAMES),**{k:q[k] for k in ('classification','readiness','states_reopened','edges_reopened','trace_resolved','diagnostic_candidates_completed')})
