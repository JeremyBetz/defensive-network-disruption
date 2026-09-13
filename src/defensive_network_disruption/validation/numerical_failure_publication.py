"""14ai strict diagnostic journal/publication contract; no numerical or data route."""
import json
from pathlib import Path
import traceback
from .projection_exposure import replay_exposure
from .r5_persistence import CANDIDATES, LifecycleError, digest, read_journal, durable_write

STAGES = ('geometry','joint_simpson','envelope','owner_certification','partition_construction',
          'routing','strict_piecewise','repeat_piecewise','onset_adaptive','direct_simpson','accepted')
EVENTS = {'initialized','access_authorized','state_discovered','projection_attempt',
 'projection_not_materialized','projection_materialized','state_prepared','state_evaluation_started',
 'field_started','field_completed','edge_completed','state_completed','failure','blocked','success'}


def context(payload):
    if not isinstance(payload,dict) or set(payload)!={'state','edge','candidate'}:
        raise LifecycleError('context_schema')
    if any(type(payload[k]) is not str or not payload[k] for k in ('state','edge')) or payload['candidate'] not in CANDIDATES:
        raise LifecycleError('context_type')
    return tuple(payload[k] for k in ('state','edge','candidate'))


def replay(records):
    base=[]; active=None; stage=None; diagnostic=False; completed_diagnostics=0; terminal=False
    opened=set(); evaluated=set(); snapshot=None; failed_stage=None
    for record in records:
        action,p=record['action'],record['payload']
        if terminal: raise LifecycleError('event_after_terminal')
        if not isinstance(p,dict): raise LifecycleError('payload_type')
        if action in ('diagnostic_started','field_started'):
            ctx=context(p)
            if active is not None or ctx[:2] not in opened or ctx[0] not in evaluated:
                raise LifecycleError('work_before_evaluation')
            active=ctx;stage=None;diagnostic=action=='diagnostic_started'
            if diagnostic: continue
        elif action=='numerical_stage':
            if set(p)!={'state','edge','candidate','detail'}: raise LifecycleError('stage_schema')
            ctx=context({k:p[k] for k in ('state','edge','candidate')})
            if active!=ctx: raise LifecycleError('stage_context')
            detail=p['detail']
            if not isinstance(detail,dict) or type(detail.get('stage')) is not str or detail['stage'] not in STAGES:
                raise LifecycleError('stage_enum')
            next_stage=detail['stage']; expected={'stage','pieces','bounded','quadrature'} if next_stage=='routing' else {'stage'}
            if set(detail)!=expected: raise LifecycleError('stage_detail_schema')
            if next_stage=='routing':
                if any(type(detail[k]) is not int or detail[k]<0 for k in expected-{'stage'}): raise LifecycleError('routing_type')
                if detail['bounded']+detail['quadrature']!=detail['pieces']: raise LifecycleError('routing_sum')
            if stage is None:
                allowed=('geometry',)
            elif stage=='geometry': allowed=('joint_simpson','accepted')
            elif stage=='envelope': allowed=('owner_certification','routing')
            else: allowed=(STAGES[STAGES.index(stage)+1],) if stage!='accepted' else ()
            if next_stage not in allowed: raise LifecycleError('stage_order')
            stage=next_stage
            continue
        elif action in ('diagnostic_completed','field_completed'):
            if context(p)!=active or stage!='accepted' or diagnostic!=(action=='diagnostic_completed'):
                raise LifecycleError('work_completion')
            if diagnostic:
                completed_diagnostics+=1;active=None;stage=None;diagnostic=False
                continue
            active=None;stage=None
        elif action=='diagnostic_success':
            if p or active is not None or completed_diagnostics!=1:
                raise LifecycleError('diagnostic_success')
            # Diagnostic success does not assert full three-candidate edge completion.
            terminal=True
            continue
        elif action=='failure':
            expected={'stage','exception','state','edge','candidate','traceback_sha256'}
            if set(p)!=expected or type(p['exception']) is not str or not p['exception']:
                raise LifecycleError('failure_schema')
            if type(p['traceback_sha256']) is not str or len(p['traceback_sha256'])!=64:
                raise LifecycleError('traceback_authority')
            if active is not None:
                if stage is None or p['stage']!=stage or tuple(p[k] for k in ('state','edge','candidate'))!=active:
                    raise LifecycleError('failure_context')
            if p['stage'] not in (*STAGES,'startup','preparation','synthetic_acceptance'):raise LifecycleError('failure_stage_enum')
            failed_stage=p['stage']; terminal=True
        elif action=='success':
            if active is not None or p: raise LifecycleError('active_success')
            terminal=True
        elif action=='blocked': terminal=True
        if action not in EVENTS: raise LifecycleError('unknown_event')
        base.append(record)
        snapshot=replay_exposure(base)  # Check lifecycle at each prefix, not after stripping all diagnostics.
        if action=='projection_materialized':
            attempt=next(r['payload'] for r in base if r['action']=='projection_attempt' and r['payload']['attempt']==p['attempt'])
            opened.update((attempt['state'],edge) for edge in p['edges'])
        elif action=='state_evaluation_started': evaluated.add(p['state'])
    if snapshot is None: raise LifecycleError('missing_initialization')
    return {'schema_version':2,'snapshot':snapshot,'diagnostic_active':None if active is None else list(active),
            'numerical_stage':stage,'failure_stage':failed_stage,'diagnostics_completed':completed_diagnostics,
            'terminal':terminal,'diagnostic_success':terminal and completed_diagnostics==1 and snapshot['status']=='active'}


def authority(path, head):
    records,actual=read_journal(path,expected_head=head)
    result=replay(records)
    return {'journal_sha256':actual,'snapshot_sha256':digest(result),'snapshot':result}


def package(authority_record, *, accepted, checks):
    if type(accepted) is not bool or not checks or any(type(v) is not bool for v in checks.values()):
        raise LifecycleError('checks_schema')
    return {'schema_version':2,'accepted':accepted,'checks':dict(checks),'authority':authority_record}


def validate_package(journal_path, head, records, *, traceback_path=None):
    if set(records)!={'qc','manifest','evidence'}: raise LifecycleError('package_members')
    actual=authority(journal_path,head)
    if not actual['snapshot']['terminal']:raise LifecycleError('nonterminal_publication')
    first=records['qc']
    for name,item in records.items():
        if set(item)!={'schema_version','accepted','checks','authority'} or item['schema_version']!=2:
            raise LifecycleError(name+'_schema')
        if type(item['accepted']) is not bool or not isinstance(item['checks'],dict) or not item['checks'] or any(type(v) is not bool for v in item['checks'].values()):
            raise LifecycleError('checks_schema')
        if item['authority']!=actual or item!=first: raise LifecycleError('cross_file_mismatch')
    if first['accepted'] and (not all(first['checks'].values()) or not actual['snapshot']['terminal']):
        raise LifecycleError('acceptance_gate')
    if first['accepted'] and actual['snapshot']['snapshot']['status'] in ('failure','blocked'):
        raise LifecycleError('failure_marked_accepted')
    source=read_journal(journal_path,expected_head=head)[0]
    failure=next((r['payload'] for r in source if r['action']=='failure'),None)
    if failure is not None:
        import hashlib
        if traceback_path is None or hashlib.sha256(Path(traceback_path).read_bytes()).hexdigest()!=failure['traceback_sha256']:
            raise LifecycleError('traceback_missing')
    return actual


def validate_persisted(folder, journal_path, head, *, traceback_path=None):
    def load(path):
        def pairs(items):
            result={}
            for key,value in items:
                if key in result: raise LifecycleError('duplicate_key')
                result[key]=value
            return result
        return json.loads(Path(path).read_text(),object_pairs_hook=pairs,
            parse_constant=lambda _: (_ for _ in ()).throw(LifecycleError('nonfinite_json')))
    records={name:load(Path(folder)/(name+'.json')) for name in ('qc','manifest','evidence')}
    return validate_package(journal_path,head,records,traceback_path=traceback_path)


def emergency(path, error, *, stage, before, terminal, publication_error=None):
    """Independent immutable preservation: never calls replay or the normal validator."""
    durable_write(path,{'schema_version':2,'original_exception':type(error).__name__,
        'traceback':''.join(traceback.format_exception(error)), 'stage':stage,
        'pre_failure':before,'terminal':terminal,'publication_error':publication_error,
        'accepted':False})
