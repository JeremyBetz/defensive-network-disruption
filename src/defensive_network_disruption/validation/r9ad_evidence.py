"""R9AD nine-artifact, immutable persisted closure. No numerical evaluation."""
import csv
import io
import math
from pathlib import Path
from .r9j_evidence import put,put_bytes,load,sha,canonical
from .r9v_publication_ownership import validate_persisted
from .r9ad_controls import NAMES,EXPECTED,NEGATIVES

FILES=('repair_contract.json','topology_controls.csv','negative_controls.csv',
       'retained_edge_replay.json','historical_regressions.csv','publication_validation.json',
       'performance.json','qc.json','manifest.json')

def csv_bytes(rows):
    stream=io.StringIO(newline='')
    if rows:
        writer=csv.DictWriter(stream,fieldnames=tuple(rows[0]),lineterminator='\n')
        writer.writeheader();writer.writerows(rows)
    else:stream.write('status\nunavailable\n')
    return stream.getvalue().encode()

def summary(local):
    local=Path(local); observations=load(local/'observations.json')
    binding=load(local/'binding.json')
    if binding.get('kind') not in ('retained','synthetic'):raise ValueError('binding_kind')
    if binding['kind']=='retained':
        from .checkpoint_ci_authority import CIExpectation
        from .checkpoint_ci_authority_v2 import validate_selected
        from .r9ad_authority import PROTOCOL,RUNNER
        root=local.parents[2]
        for path,h in binding['implementation'].items():
            if sha(root/path)!=h:raise ValueError('implementation_binding')
        expected=CIExpectation(binding['checkpoint_commit'],sha(root/PROTOCOL),sha(root/RUNNER),
                               sha(root/'uv.lock'),sha(root/'.github/workflows/ci.yml'))
        validate_selected(local/'checkpoint_ci.json',expected,expected_sha256=binding['ci_receipt_sha256'])
    if set(observations)!={'topology','negative','history','publication','retained','performance','failure'}:
        raise ValueError('observation_schema')
    top,neg,history,pub=(observations[k] for k in ('topology','negative','history','publication'))
    if top and tuple(r['fixture'] for r in top)!=NAMES:raise ValueError('topology_inventory')
    if neg and tuple(r['fixture'] for r in neg)!=NEGATIVES:raise ValueError('negative_inventory')
    for row,expected in zip(top,EXPECTED):
        detail=load(local/'records'/('topology_'+row['fixture']+'.json'))
        if row['evidence_sha256']!=sha(local/'records'/('topology_'+row['fixture']+'.json')):
            raise ValueError('topology_hash')
        if row['expected']!=expected or row['observed']!=detail['observed'] or row['passed']!=(detail['observed']==expected):
            raise ValueError('topology_claim')
    for row in neg:
        path=local/'records'/('negative_'+row['fixture']+'.json');detail=load(path)
        if row['evidence_sha256']!=sha(path) or row['blocked']!=detail['blocked'] or row['reason']!=detail['reason']:
            raise ValueError('negative_claim')
    for i,row in enumerate(history):
        path=local/'records'/('historical_'+str(i)+'.json');detail=load(path)
        if sha(path)!=row['evidence_sha256']:raise ValueError('history_hash')
        new,old=detail['new'],detail['old']
        expected=detail['expected']
        if row['components']!=len(expected['estimates']) or row['permutations']!=(new['permutations'] if new is not None else 0):
            raise ValueError('history_count_claim')
        structural=(new is not None and all(new.get(k)==old.get(k) for k in ('partitions','canonical_onsets','canonical_switches'))
                    and detail['previous_structures']==[x for x in detail['localizations'] if x.get('kind')=='raw_structures'])
        if row['structure_exact']!=structural:raise ValueError('structure_claim')
        verification=new is not None and new['maximum_interval']==old['maximum_interval'] and new['certificate_evidence']==old['certificate_evidence']
        if row['verification_preserved']!=verification:raise ValueError('verification_claim')
        order=detail['component_order']
        production=(new is not None and new['intervals']==old['intervals']==expected['intervals']
                    and order['new']==order['old']==order['expected'])
        if production:
            for key,v in new['estimates'].items():
                value=v['float']
                if float.fromhex(v['hex'])!=value:raise ValueError('float_encoding')
                for earlier in (old['estimates'][key]['float'],expected['estimates'][key]['float']):
                    production &= math.isfinite(value) and abs(value-earlier)<=64*math.ulp(1.)*max(1.,abs(value),abs(earlier))
        if row['production_preserved']!=production:raise ValueError('production_claim')
        if (row['status']=='passed') != all(row[k] for k in ('structure_exact','production_preserved','verification_preserved')):
            raise ValueError('history_status')
    retained=observations['retained']
    if set(retained)!={'attempted','materialized','completed','candidate_invocations','uncertain_exposure'}:
        raise ValueError('retained_schema')
    if retained['attempted']!=(local/'access_attempt.json').exists() or retained['materialized']!=(local/'access_materialized.json').exists():
        raise ValueError('exposure_claim')
    authority_path=local/'linear_authority.json'
    if not authority_path.exists():authority_path=local/'failure/linear_authority.json'
    pending=bool(load(authority_path)['exposure']['unresolved_projection_attempts'])
    if retained['uncertain_exposure']!=(pending or (retained['attempted'] and not retained['materialized'])):
        raise ValueError('exposure_uncertainty')
    if retained['completed']!=(local/'retained_result.json').exists():raise ValueError('completion_claim')
    if retained['candidate_invocations']!=int((local/'candidate_invocation.json').exists()):raise ValueError('invocation_claim')
    if retained['materialized']:
        receipt=load(local/'access_materialized.json')
        if receipt['attempt_sha256']!=sha(local/'access_attempt.json') or receipt['selected_sha256']!=sha(local/'selected_edge.json'):
            raise ValueError('materialization_binding')
    if observations['failure'] is not None:
        from .checkpoint_ci_authority import FailureController
        capture=FailureController(local/'failure').validate()
        if capture['traceback_sha256']!=observations['failure']['traceback_sha256']:raise ValueError('failure_binding')
    full_history=(len(history),sum(x['components'] for x in history),sum(x['permutations'] for x in history))==(108,366,399)
    history_pass=full_history and all(x['status']=='passed' for x in history)
    controls_pass=len(top)==14 and len(neg)==10 and all(r['passed'] for r in top) and all(r['blocked'] for r in neg)
    publication_pass=len(pub)==9 and all(r['passed'] for r in pub)
    if history and any(r['status']!='passed' for r in history):classification,readiness='C',3
    elif controls_pass and history_pass and publication_pass and retained['completed'] and observations['failure'] is None:classification,readiness='A',1
    elif controls_pass and history_pass and publication_pass and retained['candidate_invocations']==1:classification,readiness='D',3
    else:classification,readiness='E',4
    qc={'schema_version':1,'evidence_kind':binding['kind'],'classification':classification,'readiness':readiness,
        'controls_passed':controls_pass,'historical_passed':history_pass,'publication_controls_passed':publication_pass,
        'new_states':0,'new_edges':0,'reopened_states':int(retained['materialized']),
        'reopened_edges':int(retained['materialized']),'exposure_uncertain':retained['uncertain_exposure'],
        'completed_empirical_states':0,'completed_empirical_edges':0}
    return observations,qc

def close(folder,authority,descriptor):
    folder=Path(folder);local=folder/'local'
    validate_persisted(descriptor,authority)
    observations,qc=summary(local)
    put(local/'closure_validation.json',{'schema_version':1,'linear_reviews':1,'authority_sha256':descriptor.sha256})
    private={p.relative_to(local).as_posix():sha(p) for p in sorted(local.rglob('*')) if p.is_file()}
    put(local/'private_index.json',{'schema_version':1,'files':private})
    index=sha(local/'private_index.json')
    records={
      'repair_contract.json':{'schema_version':1,'pair_equality_separate':True,'maximality_separate':True,
          'historical_interfaces_unchanged':True,'unsupported_clipping_blocks':True,'private_index_sha256':index},
      'retained_edge_replay.json':{'schema_version':1,**observations['retained'],'private_index_sha256':index},
      'publication_validation.json':{'schema_version':1,'linear_reviews':1,'authority_sha256':descriptor.sha256,
          'controls_passed':qc['publication_controls_passed'],'private_index_sha256':index},
      'performance.json':{'schema_version':1,**observations['performance'],'private_index_sha256':index},
      'qc.json':{**qc,'private_index_sha256':index}}
    for name,record in records.items():put(folder/name,record)
    for name,key in (('topology_controls.csv','topology'),('negative_controls.csv','negative'),('historical_regressions.csv','history')):
        put_bytes(folder/name,csv_bytes(observations[key]))
    put(folder/'manifest.json',{'schema_version':1,'private_index_sha256':index,
        'outputs':{name:sha(folder/name) for name in FILES if name!='manifest.json'}})
    return publication_check(folder)

def publication_check(folder):
    folder=Path(folder);local=folder/'local'
    if {p.name for p in folder.iterdir() if p.is_file()}!=set(FILES):raise ValueError('public_inventory')
    manifest=load(folder/'manifest.json')
    if set(manifest)!={'schema_version','private_index_sha256','outputs'} or manifest['schema_version']!=1:raise ValueError('manifest_schema')
    if set(manifest['outputs'])!=set(FILES)-{'manifest.json'}:raise ValueError('manifest_inventory')
    for name,h in manifest['outputs'].items():
        if sha(folder/name)!=h:raise ValueError('public_hash')
    index=load(local/'private_index.json')
    if sha(local/'private_index.json')!=manifest['private_index_sha256']:raise ValueError('private_index')
    actual={p.relative_to(local).as_posix():sha(p) for p in local.rglob('*') if p.is_file() and p.name!='private_index.json'}
    if index!={'schema_version':1,'files':actual}:raise ValueError('private_hash_inventory')
    observations,qc=summary(local)
    closure=load(local/'closure_validation.json')
    authority_path=local/'linear_authority.json'
    if not authority_path.exists():authority_path=local/'failure/linear_authority.json'
    authority=load(authority_path)
    if closure!={'schema_version':1,'linear_reviews':1,'authority_sha256':sha(authority_path)}:
        raise ValueError('closure_authority_binding')
    if authority['raw_sha256']!=sha(local/'journal.jsonl'):raise ValueError('journal_binding')
    exposure=authority['exposure']
    # A synchronized materialization receipt may precede its journal event.
    # Preserve known exposure and unresolved journal confirmation separately.
    for field,reported in (('states_opened','reopened_states'),('edges_opened','reopened_edges')):
        if exposure[field]!=qc[reported] and not (exposure[field]==0 and qc[reported]==1
                and exposure['unresolved_projection_attempts']==1):raise ValueError('linear_exposure_binding')
    if exposure['unresolved_projection_attempts'] and not qc['exposure_uncertain']:
        raise ValueError('linear_uncertainty_binding')
    if load(folder/'qc.json')!={**qc,'private_index_sha256':manifest['private_index_sha256']}:raise ValueError('qc_claim')
    expected_records={
      'repair_contract.json':{'schema_version':1,'pair_equality_separate':True,'maximality_separate':True,
          'historical_interfaces_unchanged':True,'unsupported_clipping_blocks':True,'private_index_sha256':manifest['private_index_sha256']},
      'retained_edge_replay.json':{'schema_version':1,**observations['retained'],'private_index_sha256':manifest['private_index_sha256']},
      'publication_validation.json':{'schema_version':1,'linear_reviews':1,'authority_sha256':sha(authority_path),
          'controls_passed':qc['publication_controls_passed'],'private_index_sha256':manifest['private_index_sha256']},
      'performance.json':{'schema_version':1,**observations['performance'],'private_index_sha256':manifest['private_index_sha256']}}
    for name,expected in expected_records.items():
        if load(folder/name)!=expected:raise ValueError('public_semantics')
    for name,key in (('topology_controls.csv','topology'),('negative_controls.csv','negative'),('historical_regressions.csv','history')):
        if (folder/name).read_bytes()!=csv_bytes(observations[key]):raise ValueError('csv_claim')
    return {'status':'valid','classification':qc['classification'],'readiness':qc['readiness']}
