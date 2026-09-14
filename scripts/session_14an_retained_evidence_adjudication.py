#!/usr/bin/env python3
"""Single retained-evidence review; standard-library-only execution route."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
from pathlib import Path
import platform
import re
import subprocess
import sys
import traceback

ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/'src/defensive_network_disruption/validation/retained_evidence_review.py'
spec=importlib.util.spec_from_file_location('retained_review',MODULE)
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
START='c6d972b00857534f7573f58b1b55cf8a7a73df56'
TAG='f00690c05d8c1c6db308a65bd311c43f9a8ef2fa'
PROTOCOL='docs/protocols/phase_14an_retained_evidence_adjudication.md'
SOURCES=(PROTOCOL,str(MODULE.relative_to(ROOT)),'scripts/session_14an_retained_evidence_adjudication.py','tests/test_session14an_review.py')
OLD=ROOT/'outputs/session14am_constant_width_comparator_diagnosis'
OUT=ROOT/'outputs/session14an_retained_evidence_adjudication'
MANIFEST_HASH='235585718c4fe6a1eb2c48ac655d95a84f92fe7b342d2e486abfb3542425193e'

def git(*args):return subprocess.check_output(('git',*args),cwd=ROOT,text=True).strip()

def preflight():
    if git('status','--porcelain'):raise RuntimeError('dirty_tree')
    git('merge-base','--is-ancestor',START,'HEAD')
    if git('rev-parse','v0.1.0^{}')!=TAG:raise RuntimeError('release_changed')
    if Path(sys.prefix).resolve()!=(ROOT/'.venv').resolve():raise RuntimeError('project_interpreter')
    for name in SOURCES:
        if subprocess.check_output(('git','show','HEAD:'+name),cwd=ROOT)!=(ROOT/name).read_bytes():raise RuntimeError('uncommitted_source')
    historical={}
    for name in git('ls-tree','-r','--name-only',START).splitlines():
        old=subprocess.check_output(('git','show',START+':'+name),cwd=ROOT)
        now=(ROOT/name).read_bytes()
        if name=='docs/research_log.md':
            if not now.startswith(old):raise RuntimeError('history_log')
        elif now!=old:raise RuntimeError('history_changed')
        historical[name]=hashlib.sha256(old).hexdigest()
    if v.sha(OLD/'manifest.json')!=MANIFEST_HASH:raise RuntimeError('manifest_authority')
    return dict(start=START,implementation_commit=git('rev-parse','HEAD'),python=platform.python_version(),
        system=platform.system(),architecture=platform.machine(),lock_sha256=v.sha(ROOT/'uv.lock'),
        sources={n:v.sha(ROOT/n) for n in SOURCES},historical_tree_sha256=v.digest(historical),
        retained_manifest_sha256=MANIFEST_HASH)

def record(data):return dict(schema_version=1,status='reviewed',data=data)

def review_inputs():
    m=v.load(OLD/'manifest.json');pub={};rows=[];bindings={}
    if set(m['outputs'])!=set(v.PUBLIC):raise ValueError('historical_public_members')
    for n in v.PUBLIC:
        p=OLD/n;h=m['outputs'][n]
        if not p.exists():pub[n]=None
        else:
            if v.sha(p)!=h:raise ValueError('historical_public_hash')
            pub[n]=v.load(p) if n.endswith('.json') else None
        bindings[n]=h
        rows.append(dict(domain='retained_public',artifact=n,visibility='public',status='available' if p.exists() else 'unavailable',finding='hash_verified' if p.exists() else 'missing',sha256=h))
    index=OLD/'local/private_index.json'
    if not index.exists():return pub,{},rows,bindings
    if v.sha(index)!=m['private_index_sha256']:raise ValueError('private_index_hash')
    idx=v.load(index)
    if set(idx)!={'files'} or not isinstance(idx['files'],dict):raise ValueError('index_schema')
    selected={}
    for name,h in idx['files'].items():
        label=v.select_label(name)
        if label is None:continue
        if not re.fullmatch('[0-9a-f]{64}',h):raise ValueError('index_digest')
        p=OLD/'local'/name
        if not p.exists():
            rows.append(dict(domain=label,artifact=label,visibility='private/hash-bound',status='unavailable',finding='missing',sha256=h));continue
        item=v.read_selected(OLD/'local',name,h)
        selected.setdefault(label,[]).append(item);bindings[name]=h
        rows.append(dict(domain=label,artifact=label,visibility='private/hash-bound',status='available',finding='allowlisted_projection',sha256=h))
    return pub,selected,rows,bindings

def adjudicate(pub,priv):
    def data(n):return (pub.get(n) or {}).get('data',{})
    def last(label):return priv.get(label,[{}])[-1]
    prod=data('production_path.json');checks=prod.get('checks',{});part=data('partition_audit.json')
    cv=last('controlled_vector');strict=last('strict');repeat=last('repeat');onset=last('onset_adaptive')
    reproduction=last('reproduction');comparisons=last('independent_comparisons')
    pw=priv.get('piecewise',[]);lastpw=pw[-1] if pw else {}
    eligible=None
    if part.get('passed') is not None and lastpw.get('intervals')==16384 and v.finite(lastpw.get('successive_difference')):
        eligible=part['passed'] is True and abs(lastpw['successive_difference'])<=1e-10
    routing=part.get('checks',{}).get('routing')
    # Public audit's bounded count and successful strict result support this case's routing.
    if routing is None and part.get('passed') is True and part.get('bounded')==0 and v.finite(strict.get('residual_bound')):
        routing=strict['residual_bound']==0
    gate=data('agreement_gate_replay.json');storedgate=last('actual_gate_inputs')
    no_warning=True if reproduction.get('reproduced') is True and cv and strict and repeat and onset else None
    ref=['production_path.json','partition_audit.json','private:controlled_vector','private:strict','private:independent_comparisons']
    output={}
    output['production_health.json']=v.health(dict(completed=True if cv else None,
        stopping_satisfied=(cv['change']<=1e-7) if v.finite(cv.get('change')) else None,
        finite=v.finite(cv.get('estimates',{}).get('maximum')) if cv else None,
        no_invalidating_production_warning=no_warning,maximum_consistent=checks.get('joint_maximum'),
        reference_agreement=checks.get('production_reference'),fully_verified=False if gate.get('reproduced') else None),
        ['Production remains provisional: the complete verifier failed.','Warning absence is supported by completed warning-as-error route; no new warning check ran.'],ref)
    output['piecewise_health.json']=v.health(dict(partition_valid=part.get('passed'),strict_repeat=checks.get('strict_repeat'),
        routing_valid=routing,finite=(v.finite(strict.get('lower')) and v.finite(strict.get('upper'))) if strict else None,
        adaptive_returned=True if strict and repeat else None,reference_agreement=checks.get('piecewise_reference')),
        ['Finite-grid partition validation is not proof of globally complete switching coverage.'],ref)
    output['reference_eligibility.json']=v.health(dict(partition_valid=part.get('passed'),retained_final_step_passed=(abs(lastpw['successive_difference'])<=1e-10) if v.finite(lastpw.get('successive_difference')) else None,
        eligible=eligible,consistent_with_retained_flag=(eligible==checks['reference_eligible']) if eligible is not None and 'reference_eligible' in checks else None),
        ['Internal diagnostic reference only; no mathematical truth claim; direct 65536 is not substituted.'],['partition_audit.json','private:piecewise','production_path.json'])
    output['onset_only_health.json']=v.health(dict(completed=True if onset else None,finite=v.finite(onset.get('estimate')) if onset else None,
        adaptive_normal_return=True if onset and reproduction.get('reproduced') else None,
        independent_accuracy_established=None,reference_disagreement=(not checks['unsplit_reference']) if checks.get('unsplit_reference') is not None else None,
        refinement_persistence_established=None,insufficient_convergence_established=None),
        ['Normal return and reported errors do not prove accuracy.','No retained onset-only refinement series or adaptive subdivision record establishes convergence trend.','Exact retained discrepancy remains private; retained reference comparison exceeds its frozen 1e-10 criterion.'],
        ['private:onset_adaptive','private:reproduction','private:independent_comparisons','stopping_logic.json'])
    output['gate_adjudication.json']=v.health(dict(exact_route_reproduced=gate.get('actual_r8_route'),
        failed_condition_retained=(storedgate.get('condition') is False) if storedgate else None,
        two_independently_accurate_paths_established=None,unjustified_equivalence_established=None,
        different_estimand_established=False,structural_cause_established=None),
        ['Same maximum integrand; partition choice changes numerical treatment, not estimand.','One retained onset-only result cannot establish persistence across adaptive refinements.','The gate was not invoked in this review.'],['agreement_gate_replay.json','private:actual_gate_inputs','documentary:representation_retry.py'])
    mechanisms={k:None for k in 'ABCDEF'}
    numerical,readiness=v.classify(mechanisms)
    output['numerical_classification.json']=record(dict(classification=numerical,readiness=readiness,mechanisms=mechanisms,
        rationale='Retained disagreement and health checks do not distinguish under-resolution from an unjustified gate contract; numerical defect mechanism remains unestablished.'))
    profiles=data('journal_replay_profile.json').get('profiles',[])
    triangular=bool(profiles) and all(x.get('triangular') is True and x.get('rejection') is None for x in profiles)
    meta=last('journal_metadata');timeout=last('timeout').get('partial_operation',{})
    publication='P1' if triangular else 'P5'
    output['replay_complexity.json']=record(dict(triangular_prefix_work=triangular,profiles=profiles,
        historical_records=meta.get('records'),historical_bytes=meta.get('bytes'),timeout=timeout,
        interpretation='Completed controls demonstrate repeated prefix reconstruction; timeout counts are submitted work with an interrupted last prefix.',
        file_work_scope='Zero read/parse/hash counters apply only inside the measured in-memory routine. Surrounding wrapper counts unavailable.',
        total_runtime_estimate=None,duplicate_failure_cost=None))
    output['publication_classification.json']=record(dict(classification=publication,
        support='Retained successful triangular prefix controls and documentary replay_exposure(base) inside the event loop.' if triangular else 'Required operation evidence unavailable.',
        historical_shape_completion=False if timeout.get('completed') is False else None,
        normal_R8_publication=False,emergency_evidence_distinct=True))
    output['repair_scope.json']=record(dict(combined_authority=False,publication_shape='E' if triangular else None,
        conceptual_design='Eliminate repeated prefix reconstruction with chronological single-pass state updates preserving every check; no checkpoint machinery justified yet.' if triangular else None,
        invariants=['append_only_history','chronological_checks','exact_counts','hash_chain','access_exposure','active_failure','independent_emergency'],
        recommendation='Separately govern a narrowly bounded onset-only adaptive convergence evidence study for the already retained failing edge, capturing subdivision and refinement diagnostics to distinguish insufficient convergence from a gate-contract defect; do not repair or resume the representation study.'))
    return output,numerical,readiness,publication

def close(folder,records,rows,journalrows,authority,private_hash,valid=True):
    for n in v.OUTPUTS:
        if n=='qc.json':continue
        if n.endswith('.csv'):v.atomic(folder/n,v.csv_bytes(rows if n=='evidence_inventory.csv' else journalrows),raw=True)
        else:v.atomic(folder/n,records[n])
    n=records['numerical_classification.json']['data'];p=records['publication_classification.json']['data']
    q=dict(schema_version=1,status='closed' if valid else 'invalid',execution_valid=valid,numerical=n['classification'],readiness=n['readiness'],
        publication=p['classification'],geometry_accesses=0,new_numerical_evidence=0,combined_repair=False,private_projection_sha256=private_hash)
    v.atomic(folder/'qc.json',q)
    v.atomic(folder/'manifest.json',dict(schema_version=1,status=q['status'],outputs={n:v.sha(folder/n) for n in v.OUTPUTS},authority=authority,private_projection_sha256=private_hash))
    v.validate(folder)
    return q

def review():
    local=OUT/'local';local.mkdir(parents=True,exist_ok=True)
    v.atomic(local/'attempt.marker',dict(session='14an',exclusive=True))
    authority={};rows=[];private_hash=None
    try:
        authority=preflight()
        pub,priv,rows,bindings=review_inputs()
        v.atomic(local/'projected_evidence.json',priv);private_hash=v.sha(local/'projected_evidence.json')
        authority['evidence_hashes']=bindings
        records,_,_,_=adjudicate(pub,priv)
        # Domain obligations are explicit even where a source did not retain evidence.
        for domain,name in [('production','production_health.json'),('piecewise','piecewise_health.json'),('reference','reference_eligibility.json'),('onset','onset_only_health.json'),('gate','gate_adjudication.json')]:
            for check,value in records[name]['checks'].items():rows.append(dict(domain=domain,artifact=name,visibility='public',status='unavailable' if value is None else 'available',finding=check,sha256=''))
        rows.extend(dict(domain=d,artifact=a,visibility='public',status='available',finding=f,sha256=bindings.get(a,'')) for d,a,f in [('partition','partition_audit.json','retained_audit'),('continuity','onset_neighborhood.csv','existence_only_no_values_reopened'),('runtime','runtime_breakdown.json','historical_duration_limits_preserved')])
        jr=[r for r in rows if r['domain'] in ('journal_metadata','timeout','retained_failure') or r['artifact'] in ('journal_replay_profile.json','emergency_record_check.json','runtime_breakdown.json')]
        q=close(OUT,records,rows,jr,authority,private_hash)
    except BaseException as error:
        v.atomic(local/'failure.json',dict(exception=type(error).__name__,traceback=traceback.format_exc(),accepted=False))
        # Partial closure is preserved; never overwrite or manufacture successful evidence.
        if not any((OUT/n).exists() for n in v.OUTPUTS):
            empty,_,_,_=adjudicate({},{});q=close(OUT,empty,rows,[],authority,private_hash,valid=False)
        raise
    print(v.canonical(q).decode().strip())

def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=('preflight','review','publication-check'));cmd=p.parse_args().command
    if cmd=='preflight': print(v.canonical(preflight()).decode().strip())
    elif cmd=='review':review()
    else:print('publication-check:',v.validate(OUT))
if __name__=='__main__':main()
