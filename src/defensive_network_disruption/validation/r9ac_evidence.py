"""Persisted R9AC proof validation and nine-file sanitized publication."""
from __future__ import annotations
import csv
import hashlib
import io
import json
from pathlib import Path

from .checkpoint_ci_authority import canonical_bytes, durable_bytes, durable_json, FailureController
from .r9ac_authority import sha, load
from ..geometry.r9ac_terminal_bound import validate_result
from ..geometry.r9x_terminal_authority import digest

FILES=('authority.json','bound_contract.json','refinement_summary.csv','terminal_cell_result.json',
       'mechanism_update.json','synthetic_controls.csv','publication_validation.json','qc.json','manifest.json')
STAGES=('authorized','controls_passed','authority_loaded','bound_completed')
CSV_HEADERS={'refinement_summary.csv':('classification','nodes','leaves','additional_depth','unresolved_leaves','resource_limited','seconds','evidence_sha256'),
             'synthetic_controls.csv':('control','expected','observed','passed')}
ZERO={'new_states':0,'new_edges':0,'reopened_states':0,'reopened_edges':0,'production_field_evaluations':0,'candidate_evaluations':0}


def put(path,value):durable_json(Path(path),value)


def stage(local,name,sequence,record_hash=None):
    if name not in STAGES or STAGES.index(name)!=sequence:raise ValueError('stage_order')
    put(Path(local)/'stages'/f'{sequence:02d}.json',{'schema_version':1,'sequence':sequence,'stage':name,'record_sha256':record_hash})


def _validate_stages(local,valid):
    paths=sorted((local/'stages').glob('*.json'))
    if valid and len(paths)!=4:raise ValueError('missing_stage')
    if len(paths)>4:raise ValueError('extra_stage')
    for i,path in enumerate(paths):
        row=load(path)
        if set(row)!={'schema_version','sequence','stage','record_sha256'} or row['schema_version']!=1 or row['sequence']!=i or row['stage']!=STAGES[i]:raise ValueError('stage_record')
        target={1:'controls.json',2:'authority.json',3:'result.json'}.get(i)
        if target and row['record_sha256']!=sha(local/target):raise ValueError('stage_hash')


def decisions(summary,statuses):
    keys={'ordinal','depth','pair_status','maximum_status'}
    if not statuses or any(set(x)!=keys for x in statuses) or [x['ordinal'] for x in statuses]!=list(range(len(statuses))):raise ValueError('history_schema')
    pending=[x for x in statuses if x['maximum_status']=='unresolved']
    if len(pending)!=1:raise ValueError('history_unresolved')
    counts={k:sum(x['maximum_status']==k for x in statuses) for k in ('maximum','dominated','unresolved','not_applicable')}
    local=summary['classification']
    sufficient=(summary['coverage_complete'] and summary['pair_equality_proved'] and local in ('TA','TB','TC')
                and all(x['pair_status']=='equal' for x in statuses) and counts['dominated']>0)
    return {'mechanism':'ND' if sufficient else 'NF',
            'readiness':1 if sufficient else 2 if local=='TD' else 3,
            'repair_specification':'restrict_exact_pair_tie_structures_to_independently_certified_global_maximal_regions' if sufficient else None,
            'historical_counts':counts}


def inspect_private(local):
    """Pure persisted-evidence validation. Never computes a field enclosure."""
    local=Path(local)
    binding=load(local/'binding.json')
    if set(binding)!={'schema_version','kind','source_authority_sha256','historical_status_sha256',
                       'protocol_sha256','runner_sha256','checkpoint_commit','ci_receipt_sha256'} or binding['schema_version']!=1:
        raise ValueError('binding_schema')
    if binding['kind'] not in ('synthetic','retained'):raise ValueError('binding_kind')
    from .r9ac_authority import OUTPUT, AUTHORITY_HASH, PARTITION, inventory
    if local.parent.name==Path(OUTPUT).name and binding['kind']!='retained':raise ValueError('retained_namespace')
    if binding['kind']=='retained':
        from .checkpoint_ci_authority import CIExpectation
        from .checkpoint_ci_authority_v2 import validate_selected
        root=Path(__file__).resolve().parents[3]; inherited=inventory(root)
        if binding['source_authority_sha256']!=AUTHORITY_HASH or binding['historical_status_sha256']!=PARTITION:
            raise ValueError('retained_binding')
        expected=CIExpectation(binding['checkpoint_commit'],binding['protocol_sha256'],binding['runner_sha256'],
                               inherited['uv.lock'],inherited['.github/workflows/ci.yml'])
        validate_selected(local/'checkpoint_ci.json',expected,expected_sha256=binding['ci_receipt_sha256'])
    linear=load(local/'linear_authority.json')
    if linear['records']!=0 or linear['legacy'] is not None or linear['failure'] is not None or linear['raw_sha256']!=hashlib.sha256(b'').hexdigest():raise ValueError('zero_exposure_authority')
    if (local/'empirical_journal.jsonl').read_bytes()!=b'':raise ValueError('unexpected_empirical_events')
    exposure=linear['exposure']
    if any(exposure[k]!=0 for k in ('states_opened','edges_opened','unresolved_projection_attempts','unresolved_exposed_edges','field_evaluations_started','field_evaluations_completed')):raise ValueError('nonzero_exposure')
    for work in exposure['field_work_by_candidate'].values():
        if any(value!=0 for value in work.values()):raise ValueError('nonzero_candidate_work')
    failure=(local/'failure/original_failure.json').exists()
    _validate_stages(local,not failure)
    if failure:
        FailureController(local/'failure').validate()
        return {'valid':False,'summary':None,'mechanism':'NF','readiness':4,'repair_specification':None,'historical_counts':{},'controls':load(local/'controls.json') if (local/'controls.json').exists() else []}
    authority=load(local/'authority.json');result=load(local/'result.json')
    binding=load(local/'binding.json')
    if digest(authority)!=binding['source_authority_sha256']:raise ValueError('input_authority_binding')
    nodes=[load(path) for path in sorted((local/'nodes').glob('*.json'))]
    if [p.name for p in sorted((local/'nodes').glob('*.json'))]!=[f'{i:06d}.json' for i in range(len(nodes))]:raise ValueError('node_files')
    summary=validate_result(authority,nodes,result)
    controls=load(local/'controls.json')
    if len(controls)!=10 or any(set(x)!=set(CSV_HEADERS['synthetic_controls.csv']) or x['passed'] is not True or x['observed']!=x['expected'] for x in controls):raise ValueError('control_results')
    # Verify positive synthetic evidence too; current fields are never reevaluated.
    details=load(local/'control_details.json')
    if len(details)!=10 or [x['control'] for x in details]!=[x['control'] for x in controls]:raise ValueError('control_details')
    for item,row in zip(details[:8],controls[:8]):
        observed=validate_result(item['authority'],item['nodes'],item['result'])
        if observed['classification']!=row['observed']:raise ValueError('control_false_claim')
    history=load(local/'historical_status.json')
    if digest(history)!=binding['historical_status_sha256']:raise ValueError('historical_status_binding')
    decision=decisions(summary,history)
    selected=authority['cell']['ordinal']
    if selected>=len(history) or history[selected]['maximum_status']!='unresolved' or history[selected]['depth']!=authority['cell']['depth']:raise ValueError('history_cell_binding')
    return {'valid':True,'summary':summary,**decision,'controls':controls}


def csv_bytes(name,rows):
    out=io.StringIO(newline='');writer=csv.DictWriter(out,fieldnames=CSV_HEADERS[name],lineterminator='\n')
    writer.writeheader();writer.writerows(rows)
    return out.getvalue().encode()


def expected_public(local,private_hash):
    local=Path(local); observed=inspect_private(local);summary=observed['summary']
    valid=observed['valid']; local_class=summary['classification'] if summary else None
    status='invalid' if not valid else 'partial' if local_class in ('TD','TE') else 'complete'
    binding=load(local/'binding.json'); authority_hash=sha(local/'authority.json') if valid else None
    result_hash=sha(local/'result.json') if valid else None
    result=load(local/'result.json') if valid else None
    public={
      'authority.json':{'schema_version':1,'status':status,'authority_sha256':authority_hash,
        'source_authority_sha256':binding['source_authority_sha256'],'validated':valid,'source_version':2 if valid else None,**ZERO},
      'bound_contract.json':{'schema_version':1,'status':status,'precision_bits':256,'additional_depth_limit':80,
        'leaf_limit':65536,'operation_seconds':900,'session_seconds':7200,'both_pair_members':True,
        'tie_label_is_proof':False,'production_changed':False,'exact_values':'private','protocol_sha256':binding['protocol_sha256']},
      'terminal_cell_result.json':{'schema_version':1,'status':status,'local':local_class,'summary':summary,
        'result_sha256':result_hash,'final_enclosure_width':'private' if valid else 'unavailable'},
      'mechanism_update.json':{'schema_version':1,'status':status,'mechanism':observed['mechanism'],
        'readiness':observed['readiness'],'historical_counts':observed['historical_counts'],
        'repair_specification':observed['repair_specification'],'repair_implemented':False},
      'publication_validation.json':{'schema_version':1,'status':status,'linear_reviews':1,
        'zero_exposure_authority':True,'single_writer':True,'persisted_proofs_valid':valid,
        'historical_replays':0,'private_index_sha256':private_hash,'linear_authority_sha256':sha(local/'linear_authority.json')},
      'qc.json':{'schema_version':1,'status':status,'execution_valid':valid,'local':local_class,
        'mechanism':observed['mechanism'],'readiness':observed['readiness'],**ZERO,
        'scientific_result':False,'operational_repair':'unresolved','private_index_sha256':private_hash},
    }
    rows=[]
    if valid:
        rows=[{'classification':local_class,'nodes':summary['nodes'],'leaves':summary['leaves'],
               'additional_depth':summary['additional_depth'],'unresolved_leaves':summary['unresolved_leaves'],
               'resource_limited':summary['resource_limited'],'seconds':result['elapsed_seconds'],
               'evidence_sha256':result_hash}]
    public['refinement_summary.csv']=csv_bytes('refinement_summary.csv',rows)
    public['synthetic_controls.csv']=csv_bytes('synthetic_controls.csv',observed['controls'])
    return public


def close(folder,authority,descriptor):
    from .r9v_publication_ownership import validate_persisted,write_package_file
    folder=Path(folder);local=folder/'local'
    validate_persisted(descriptor,authority)
    inspect_private(local)  # Validate before acceptance or public-file creation.
    files={str(p.relative_to(local)):sha(p) for p in sorted(local.rglob('*')) if p.is_file() and p.name!='private_index.json'}
    if any('.pending' in name for name in files):raise ValueError('incomplete_write')
    put(local/'private_index.json',{'schema_version':1,'files':files})
    ih=sha(local/'private_index.json')
    public=expected_public(local,ih)
    for name,value in public.items():
        validate_persisted(descriptor,authority)
        if isinstance(value,bytes):durable_bytes(folder/name,value)
        else:write_package_file(folder/name,value,authority,descriptor)
    manifest={'schema_version':1,'outputs':{name:sha(folder/name) for name in public},
              'private_index_sha256':ih,'protocol_sha256':load(local/'binding.json')['protocol_sha256']}
    write_package_file(folder/'manifest.json',manifest,authority,descriptor)
    return publication_check(folder)


def publication_check(folder):
    folder=Path(folder);local=folder/'local'
    if sorted(p.name for p in folder.iterdir() if p.is_file())!=sorted(FILES):raise ValueError('public_inventory')
    manifest=load(folder/'manifest.json')
    if set(manifest)!={'schema_version','outputs','private_index_sha256','protocol_sha256'} or manifest['schema_version']!=1 or set(manifest['outputs'])!=set(FILES)-{'manifest.json'}:raise ValueError('manifest_schema')
    for name,h in manifest['outputs'].items():
        if sha(folder/name)!=h:raise ValueError('public_hash')
    index=load(local/'private_index.json',manifest['private_index_sha256'])
    if set(index)!={'schema_version','files'} or index['schema_version']!=1:raise ValueError('private_index_schema')
    actual={str(p.relative_to(local)) for p in local.rglob('*') if p.is_file()}-{'private_index.json'}
    if actual!=set(index['files']):raise ValueError('private_inventory')
    for name,h in index['files'].items():
        if Path(name).is_absolute() or '..' in Path(name).parts:raise ValueError('private_path')
        if sha(local/name)!=h:raise ValueError('private_hash')
    if manifest['protocol_sha256']!=load(local/'binding.json')['protocol_sha256']:raise ValueError('protocol_binding')
    expected=expected_public(local,manifest['private_index_sha256'])
    for name,value in expected.items():
        raw=value if isinstance(value,bytes) else canonical_bytes(value)
        if (folder/name).read_bytes()!=raw:raise ValueError('public_semantics')
    qc=load(folder/'qc.json')
    return {'publication_valid':True,'execution_valid':qc['execution_valid'],'local':qc['local'],
            'mechanism':qc['mechanism'],'readiness':qc['readiness'],**ZERO}
