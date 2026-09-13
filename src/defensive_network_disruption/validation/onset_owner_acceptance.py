"""Frozen synthetic acceptance for 14ai. No empirical inputs or acquisition."""
from dataclasses import asdict
import copy
import importlib.util
import itertools
import json
from pathlib import Path
import tempfile
import numpy as np
from ..geometry import onset_owner_certification as new
from ..geometry import representation_retry as historical
from ..geometry.verification_repair import VerifiedSwitch, VerificationError, mapped_signature
from ..geometry.micro_interval_verifier import IntegralInterval, point_interval_distance
from . import numerical_failure_publication as pub
from .r5_persistence import Journal, durable_write


def topology_oracles():
    rows=[]
    few=.5
    for _ in range(4):few=float(np.nextafter(few,-np.inf))
    cases=(('ordinary',.5,0.,1.,False,None),('ell0_after',.5,.5-2e-8,1.,False,None),
      ('ell1_before',.5,0.,.5+2e-8,False,None),('ell1_after',.5,.5-2e-8,1.,False,None),
      ('coincident',.5,.5,1.,False,'coincident_or_unordered_boundary'),
      ('one_ulp',.5,float(np.nextafter(.5,-np.inf)),1.,False,'no_interior_float'),
      ('few_ulp',.5,few,1.,False,'partition_owner_semantics_changed'),
      ('multiway',.5,.5-2e-8,1.,True,None),('point_tie',.5,0.,1.,False,None),
      ('neighbor_switch',.5,0.,.500001,False,None),('endpoint',2e-7,0.,1.,False,None))
    for name,root,left,right,multi,expected in cases:
        def f(t):
            columns=[.5+.25*(t-root),.5-.25*(t-root)]
            if multi:columns.append(np.full_like(t,.5))
            return np.column_stack(columns)
        s=VerifiedSwitch(root,new.owners(f(np.array([root-1e-7]))[0]),new.owners(f(np.array([root]))[0]),
            new.owners(f(np.array([root+1e-7]))[0]),((0,1),),False,multi,.5)
        error=None
        try:
            transition=new.localize(f,s)
            # The exact-coincidence oracle fixes its certified coordinate at the boundary.
            if name in ('coincident','one_ulp','few_ulp'):transition=(*transition[:3],root)
            new.certify_in_region(f,s,transition,left,right)
        except VerificationError as exc:error=str(exc)
        rows.append(dict(fixture=name,expected=expected or 'accepted',observed=error or 'accepted',passed=error==expected))
    def plateau(t):
        delta=np.where(t<.4,t-.4,np.where(t>.6,t-.6,0.))*.25
        return np.column_stack((.5+delta,.5-delta))
    from ..geometry.verification_repair import find_verified_envelope
    error=None
    try:
        envelope=find_verified_envelope(plateau)
        parts,_,_=new.certify_partitions(plateau,envelope,())
        endpoints={p for tie in envelope.tie_intervals for boundary in (tie.start,tie.end) if boundary
                   for p in (boundary.outside,boundary.inside)}
        if not endpoints or not endpoints.issubset(parts):raise VerificationError('tie_endpoints_lost')
    except VerificationError as exc:error=str(exc)
    rows.append(dict(fixture='plateau',expected='accepted',observed=error or 'accepted',passed=error is None))
    return rows


def publication_controls():
    import hashlib
    trace=b'synthetic traceback'
    def events(success=False):
        rows=[]
        def add(action,**payload):rows.append((action,payload))
        add('initialized');add('access_authorized');add('state_discovered',state='s',edges=['e'])
        add('projection_attempt',state='s',attempt='a');add('projection_materialized',attempt='a',edges=['e'])
        add('state_prepared',state='s');add('state_evaluation_started',state='s')
        for candidate in pub.CANDIDATES:
            ctx=dict(state='s',edge='e',candidate=candidate)
            add('field_started',**ctx);add('numerical_stage',**ctx,detail={'stage':'geometry'})
            if candidate=='constant_width' and not success:
                add('failure',**ctx,stage='geometry',exception='RuntimeError',traceback_sha256=hashlib.sha256(trace).hexdigest())
                return rows
            add('numerical_stage',**ctx,detail={'stage':'accepted'});add('field_completed',**ctx)
        add('edge_completed',state='s',edge='e');add('state_completed',state='s');add('success')
        return rows
    valid=events();ix=next(i for i,(a,p) in enumerate(valid) if a=='numerical_stage')
    cases=[('valid_failure',valid,True,False),('valid_success',events(True),True,True)]
    for label,detail in [('missing_stage',{}),('unknown_stage',{'stage':'other'}),('malformed_type',{'stage':False}),
                         ('extra_field',{'stage':'geometry','extra':1})]:
        rows=copy.deepcopy(valid);rows[ix][1]['detail']=detail;cases.append((label,rows,False,False))
    for key in ('state','edge','candidate'):
        rows=copy.deepcopy(valid);del rows[ix][1][key];cases.append(('missing_'+key,rows,False,False))
    cases.append(('premature_stage',[valid[ix],*valid],False,False))
    cases.append(('postterminal_stage',valid+[valid[ix]],False,False))
    cases.append(('no_failure_stage',[x for x in valid if not(x[0]=='numerical_stage' and x[1]['candidate']=='constant_width')],False,False))
    cases.append(('forged_success',valid,False,True))
    results=[]
    for name,rows,expected,accepted in cases:
        error=None
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d).resolve();journal=Journal(folder/'journal')
            for action,payload in rows:journal.append(action,**payload)
            head=journal.previous;journal.close();(folder/'trace').write_bytes(trace)
            try:
                auth=pub.authority(folder/'journal',head)
                record=pub.package(auth,accepted=accepted,checks={'synthetic':True})
                for key in ('qc','manifest','evidence'):durable_write(folder/(key+'.json'),record)
                pub.validate_persisted(folder,folder/'journal',head,traceback_path=folder/'trace')
            except Exception as exc:error=type(exc).__name__
        results.append(dict(fixture=name,expected_acceptance=expected,accepted=error is None,passed=(error is None)==expected))
    for name in ('qc_reset','manifest_hash','evidence_reset','missing_file','missing_traceback','journal_truncated','false_acceptance_gate'):
        error=None
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d).resolve();j=Journal(folder/'journal')
            for action,payload in events(name=='false_acceptance_gate'):j.append(action,**payload)
            head=j.previous;j.close();(folder/'trace').write_bytes(trace)
            auth=pub.authority(folder/'journal',head)
            record=pub.package(auth,accepted=name=='false_acceptance_gate',checks={'synthetic':True})
            for member in ('qc','manifest','evidence'):
                item=copy.deepcopy(record)
                if name=='false_acceptance_gate':item['checks']['synthetic']=False
                if name==member+'_reset':item['authority']['snapshot']['snapshot']['counters']['edges_opened']=0
                if name=='manifest_hash' and member=='manifest':item['authority']['snapshot_sha256']='0'*64
                durable_write(folder/(member+'.json'),item)
            if name=='missing_file':(folder/'evidence.json').unlink()
            if name=='missing_traceback':(folder/'trace').unlink()
            if name=='journal_truncated':
                content=(folder/'journal').read_bytes();(folder/'journal').write_bytes(content[:-1])
            try:pub.validate_persisted(folder,folder/'journal',head,traceback_path=folder/'trace')
            except Exception as exc:error=type(exc).__name__
        results.append(dict(fixture=name,expected_acceptance=False,accepted=error is None,passed=error is not None))
    # An independent emergency record must remain writable even if replay/normal publication cannot run.
    with tempfile.TemporaryDirectory() as d:
        path=Path(d).resolve()/'emergency'
        try:raise RuntimeError('synthetic_original_failure')
        except RuntimeError as exc:pub.emergency(path,exc,stage='owner_certification',before=None,terminal=None,publication_error='synthetic_replay_failure')
        saved=json.loads(path.read_text())
        passed=(not saved['accepted'] and saved['original_exception']=='RuntimeError' and
                'synthetic_original_failure' in saved['traceback'] and saved['publication_error']=='synthetic_replay_failure')
        results.append(dict(fixture='independent_failure_preservation',expected_acceptance=True,accepted=passed,passed=passed))
    return results


def historical_regression(root, progress=lambda row:None):
    spec=importlib.util.spec_from_file_location('ai_frozen_cases',root/'scripts/session_14v_micro_interval_verifier.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    rows=[]
    for fixture,case in module.authority_cases():
        try:
            result=new.evaluate(case['candidate'],case['origin'],case['receiver'],case['defenders'],historical_failure=case['historical_failure'])
            expected=case['historical_vector']
            if result['intervals']!=expected['intervals'] or tuple(result['estimates'])!=tuple(expected['estimates']):
                raise VerificationError('historical_order_resolution')
            for name,value in result['estimates'].items():
                old=expected['estimates'][name]
                if not np.isfinite(value) or abs(value-old)>64*np.finfo(float).eps*max(1,abs(value),abs(old)):
                    raise VerificationError('historical_final_float')
                error=point_interval_distance(case['references'][name],IntegralInterval(**result['maximum_interval'])) if name=='maximum' else abs(value-case['references'][name])
                if error>1e-6:raise VerificationError('reference_error')
            from ..geometry.occlusion_fields import CarrierOriginField
            b=np.array(case['origin']);end=np.array(case['receiver']);ds=np.array(case['defenders'])
            field=CarrierOriginField(case['candidate'])
            def f(t):return field.individual_values(b,ds,b[None,:]+t[:,None]*(end-b)[None,:])
            old=historical.canonical_geometry(case['candidate'],b,end,ds,f)
            if result['partitions']!=old[2] or result['switches']!=old[3]:raise VerificationError('historical_structure')
            perms=0
            for perm in itertools.permutations(range(len(ds))):
                other=new.canonical_geometry(case['candidate'],b,end,ds[list(perm)],lambda t,p=perm:f(t)[:,p])
                if result['partitions']!=other[2] or mapped_signature(result['envelope'],tuple(range(len(ds))))!=mapped_signature(other[1],perm):
                    raise VerificationError('permutation_mismatch')
                def canonical_signature(switches,permutation):
                    return [(s.last_pre_switch,s.exact_zero_start,s.exact_zero_end,s.canonical,
                        tuple(sorted(permutation[i] for i in s.owners_before)),
                        tuple(sorted(permutation[i] for i in s.owners_at)),
                        tuple(sorted(permutation[i] for i in s.owners_after)),
                        tuple(sorted(tuple(sorted(permutation[i] for i in pair)) for pair in s.crossing_pairs)))
                        for s in switches]
                if canonical_signature(result['switches'],tuple(range(len(ds))))!=canonical_signature(other[3],perm):
                    raise VerificationError('canonical_owner_permutation')
                perms+=1
            row=dict(fixture=fixture,candidate=case['candidate'],passed=True,components=len(result['estimates']),permutations=perms,error='')
        except Exception as exc:
            row=dict(fixture=fixture,candidate=case['candidate'],passed=False,components=0,permutations=0,error=str(exc) if isinstance(exc,VerificationError) else type(exc).__name__)
            rows.append(row);progress(row);return rows
        rows.append(row);progress(row)
    if len(rows)!=108 or sum(x['components'] for x in rows)!=366 or sum(x['permutations'] for x in rows)!=399:
        raise VerificationError('historical_counts')
    return rows
