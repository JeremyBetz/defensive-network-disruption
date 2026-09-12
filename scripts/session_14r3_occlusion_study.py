#!/usr/bin/env python3
"""Governed Session 14R3, explicit label-free geometry and immutable stages."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
import csv
import hashlib
import importlib.util
import io
import itertools
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import traceback
import warnings
from importlib.metadata import version
import re

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))

START='8da64387fe62d5bd15f0a347456252e931988945'
TAG='f00690c05d8c1c6db308a65bd311c43f9a8ef2fa'
POP_SHA='cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d'
POP=Path('outputs/receiver_ranking_m0_m1/local/population.jsonl')
OUT=Path('outputs/continuous_occlusion_retry_14r3'); LOCAL=OUT/'local'; AUTH=OUT/'authority'
PROTOCOL=Path('docs/protocols/phase_14r3_continuous_occlusion_empirical_retry.md')
CODE=('scripts/session_14r3_occlusion_study.py',
      'src/defensive_network_disruption/geometry/representation_study.py',
      'src/defensive_network_disruption/data/representation_projection.py','tests/test_session14r3_study.py','src/defensive_network_disruption/geometry/representation_retry.py',
      'src/defensive_network_disruption/validation/r3_launch.py', 'tests/test_session14r3_enforcement.py')
CSV_FILES=('candidate_pair_comparison.csv','structural_correspondence.csv','receiver_segment_divergence.csv','union_vs_max.csv','multi_edge_summary.csv','match_summary.csv')
FINAL_FILES=('candidate_summary.json',*CSV_FILES,'synthetic_stress_summary.json','qc.json','synthetic_field_comparison.svg')
KEYS=('candidate','comparison','summary','combination','metric')
STAT_KEYS=('mean','minimum','maximum','q05','q25','q50','q75','q95')
COLUMNS=(*KEYS,'alias','unit','represented_matches','states_total','states_assessable','states_unavailable','observations','source_observations',*STAT_KEYS)


ACCESS=dict(authorized=False,population_opens=0,states_prepared=0,states_completed=0,
            edges_started=0,edges_completed=0,stage='startup')


def startup_close(error):
    """Standard-library closure even if numerical-package imports fail."""
    out=ROOT/OUT; local=ROOT/LOCAL
    if any(p.is_symlink() for p in (out,local,*local.parents)):
        raise PermissionError('unsafe_startup_output')
    if (out/'manifest.json').exists(): return
    local.mkdir(parents=True,exist_ok=True)
    def emit(path,value):
        temporary=path.with_name('.'+path.name+'.startup.tmp')
        if path.exists():raise FileExistsError('existing_startup_record')
        with temporary.open('x') as f:json.dump(value,f,sort_keys=True,allow_nan=False);f.write('\n')
        temporary.replace(path)
    def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
    emit(local/'startup_failure.json',dict(stage='runtime_import',exception=type(error).__name__,states=0,edges=0))
    emit(out/'qc.json',dict(schema_version=1,status='blocked',stage='startup',states_completed=0,
        empirical_access=False,access=dict(ACCESS),exception=type(error).__name__,interval_counts={},
        max_joint_change=None,max_maximum_reference_error=None))
    emit(out/'manifest.json',dict(schema_version=1,status='blocked',start=START,protocol=sha(PROTOCOL),
        implementation={p:sha(p) for p in CODE},environment={'unavailable':'runtime_import_failure'},authority={},
        outputs={'qc.json':sha(OUT/'qc.json')},unavailable=[n for n in FINAL_FILES if n!='qc.json']))


try:
    import numpy as np
    from defensive_network_disruption.validation.r3_launch import R3Launch, TEST_COMMAND, test_record, strict_prerequisite
    from defensive_network_disruption.validation.launch_enforcement import EnvironmentObservation, PrerequisiteExpectation
    from defensive_network_disruption.geometry import production_verification as pv
    from defensive_network_disruption.geometry.occlusion_fields import CANDIDATES, CarrierOriginField, combine
    from defensive_network_disruption.geometry.verification_repair import VerificationReadiness
    from defensive_network_disruption.geometry.representation_study import (
        spearman, weighted_summary, maximum_set, order_categories,
        discordant_pairs, follows, block_ranks)
    from defensive_network_disruption.geometry.representation_retry import evaluate, evaluate_edge
    from defensive_network_disruption.data.representation_projection import project_line, ALIASES, COUNTS, DEVELOPMENT
    from defensive_network_disruption.networks.options import OptionState
    from defensive_network_disruption.networks.defender_edges import map_defender_edges, summarize_edge_involvement
except Exception as error:
    startup_close(error)
    raise



def git(*args):
    return subprocess.check_output(['git',*map(str,args)],cwd=ROOT).decode().strip()


def safe(path):
    p=ROOT/path
    if any(x.is_symlink() for x in (p,*p.parents)) or not p.resolve().is_relative_to(ROOT.resolve()):
        raise PermissionError('unsafe_path')
    return p


def digest(path):
    h=hashlib.sha256()
    with safe(path).open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''): h.update(block)
    return h.hexdigest()


def encoded(x): return json.dumps(x,sort_keys=True,indent=2,allow_nan=False)+'\n'


def duplicate_free(pairs):
    out={}
    for k,v in pairs:
        if k in out: raise ValueError('duplicate_key')
        out[k]=v
    return out


def load(path):
    return json.loads(safe(path).read_text(),object_pairs_hook=duplicate_free,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite_json')))


def atomic(path,content):
    if not Path(path).is_relative_to(OUT): raise PermissionError('output_namespace')
    dest=safe(path)
    if dest.exists(): raise FileExistsError('output_exists')
    dest.parent.mkdir(parents=True,exist_ok=True)
    temp=dest.with_name('.'+dest.name+'.tmp')
    with temp.open('x') as f: f.write(content)
    temp.replace(dest)


def write(path,value): atomic(path,encoded(value))


def committed(path):
    b=subprocess.check_output(['git','show','HEAD:'+str(path)],cwd=ROOT)
    if hashlib.sha256(b).hexdigest()!=digest(path): raise ValueError('uncommitted_authority')


def environment():
    from importlib.metadata import version
    return dict(python=platform.python_version(),numpy=np.__version__,scipy=version('scipy'),
                matplotlib=version('matplotlib'),lock=digest('uv.lock'))


def code_hashes(): return {p:digest(p) for p in CODE}


def inherited_hashes():
    names=git('ls-tree','-r','--name-only',START).splitlines()
    return {p:digest(p) for p in names if p!='docs/research_log.md'}


def history():
    git('merge-base','--is-ancestor',START,'HEAD')
    old=set(git('ls-tree','-r','--name-only',START).splitlines())
    for p in old.intersection(git('diff','--name-only',START).splitlines()):
        if p!='docs/research_log.md': raise ValueError('historical_file_changed')
        if not safe(p).read_bytes().startswith(subprocess.check_output(['git','show',START+':'+p],cwd=ROOT)):
            raise ValueError('log_not_append_only')
    if git('rev-parse','v0.1.0^{}')!=TAG: raise ValueError('release_changed')


def ledger(stage,status):
    p=safe(LOCAL/'access.jsonl');p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('a') as f:
        f.write(json.dumps(dict(stage=stage,status=status,time=datetime.now(timezone.utc).isoformat(),
                               head=git('rev-parse','HEAD'),protocol=digest(PROTOCOL)))+'\n')


def claim(stage):
    if safe(OUT/'manifest.json').exists(): raise ValueError('closed_no_rerun')
    pv.claim_execution(safe(LOCAL/(stage+'.marker')))
    ledger(stage,'started')


def preflight():
    history();committed(PROTOCOL)
    if not git('check-ignore','--',str(LOCAL/'probe')): raise ValueError('local_not_ignored')
    if digest('outputs/continuous_occlusion_production_acceptance/manifest.json')!='1c65769260cc6e1b8a79b69129b3b5a227d4a0a41aec93be4533168a042ace88':
        raise ValueError('session14i_manifest')
    print('Session 14R3 preflight passed; no empirical input opened')


def synthetic_module():
    spec=importlib.util.spec_from_file_location('r2_synthetic_authority',safe('scripts/session_14v_micro_interval_verifier.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def synthetic_acceptance(progress=lambda **kw:None):
    from defensive_network_disruption.geometry.micro_interval_verifier import IntegralInterval, point_interval_distance
    from defensive_network_disruption.geometry.verification_repair import opposite_nonzero_signs
    module=synthetic_module(); rows=[]
    historical_routes=load(Path('outputs/cross_platform_canonical_comparison/local_diagnostic.json'))
    routes={(x['fixture'],x['candidate']):x['routing'] for x in historical_routes['records']}
    pv.require(opposite_nonzero_signs(-1e-200,1e-200) and not opposite_nonzero_signs(0.,1.),'tiny_sign')
    engineering=pv.engineering_checks()
    pv.require(all(x['passed'] for x in engineering),'engineering_checks')
    for fixture,case in module.authority_cases():
        progress(fixture=fixture,candidate=case['candidate'],stage='synthetic_case')
        edge,result=evaluate(case['candidate'],case['origin'],case['receiver'],case['defenders'],
            synthetic=True,historical_failure=case['historical_failure'],record=progress)
        expected=case['historical_vector']; actual=result['estimates']
        route=routes[fixture,case['candidate']]
        pv.require(list(result['partitions'])==route['partitions'],'canonical_historical_partitions')
        observed_onsets=[tuple(x) for x in result['canonical_onsets']]
        expected_onsets=[(x['defender'],x['branch'],x['last_pre'],x['canonical']) for x in route['onsets']]
        pv.require(observed_onsets==expected_onsets,'canonical_historical_onsets')
        expected_switches=[(x['last_pre'],x['zero_start'],x['zero_end'],x['canonical'],
            tuple(x['owners_before']),tuple(x['owners_at']),tuple(x['owners_after']),tuple(tuple(p) for p in x['crossing_pairs'])) for x in route['switches']]
        pv.require(result['canonical_switches']==expected_switches,'canonical_historical_switches')
        pv.require(edge.intervals==expected['intervals'] and tuple(actual)==tuple(expected['estimates']),'historical_structure')
        pv.require(tuple(actual)==tuple(case['references']),'reference_order')
        interval=IntegralInterval(**result['maximum_interval']);errors={}
        for name,value in actual.items():
            old=expected['estimates'][name]
            pv.require(math.isfinite(value) and abs(value-old)<=64*np.finfo(np.float64).eps*max(1.,abs(value),abs(old)),'historical_final_float')
            ref=case['references'][name]
            errors[name]=point_interval_distance(ref,interval) if name=='maximum' else abs(value-ref)
            pv.require(math.isfinite(ref) and errors[name]<=1e-6,'reference_error')
        rows.append(dict(fixture=fixture,candidate=case['candidate'],intervals=edge.intervals,
            estimates=actual,errors=errors,permutations=result['permutations'],continuity=result['continuity'],
            deterministic=result['deterministic'],warnings=result['warnings']))
    pv.require(len(rows)==108 and sum(len(r['errors']) for r in rows)==366 and sum(r['permutations'] for r in rows)==399,'acceptance_counts')
    return rows,engineering


def verify_production():
    preflight()
    produce_tests(LOCAL/'preaccess_tests.json')
    tests=load(LOCAL/'preaccess_tests.json')
    strict_prerequisite(safe(LOCAL/'preaccess_tests.json'), expectation(observe()))
    claim('verify-production')
    try:
        bound=inherited_hashes()
        def progress(**kw):
            with safe(LOCAL/'synthetic_progress.jsonl').open('a') as f:f.write(json.dumps(kw,allow_nan=False)+'\n')
        rows,engineering=synthetic_acceptance(progress)
        gate=VerificationReadiness(continuity_verified=all(x['continuity'] for x in rows),
            switching_verified=len(rows)==108,controlled_integration_verified=all(x['intervals']>0 for x in rows),
            references_complete=sum(len(x['errors']) for x in rows)==366,
            permutation_verified=sum(x['permutations'] for x in rows)==399,deterministic=all(x['deterministic'] for x in rows),
            failure_enforcement_verified=tests['failure_enforcement_passed'],blocking_warnings_absent=all(x['warnings']==0 for x in rows),
            integrity_verified=bound==inherited_hashes())
        pv.require(gate.ready,'readiness_false')
        write(AUTH/'production.json',dict(schema_version=1,status='passed',protocol=digest(PROTOCOL),
              implementation=code_hashes(),inherited=bound,environment=environment(),
              readiness=asdict(gate),cases=rows,engineering=engineering,tests=tests))
        write(OUT/'synthetic_stress_summary.json',dict(schema_version=1,scope='synthetic_only',
            records=[r for r in rows if r['fixture'].startswith('equal_minimum')]))
        ledger('verify-production','passed');print('108/366/399 assembled synthetic acceptance passed')
    except Exception as e:
        failure('verify-production',e,0);raise



def render_synthetic(approve=False):
    preflight()
    prod=load(AUTH/'production.json');check_binding(prod)
    if approve:
        visual=load(AUTH/'visual_generation.json')
        pv.require(visual['svg_sha256']==digest(OUT/'synthetic_field_comparison.svg'),'visual_hash')
        write(AUTH/'visual_approval.json',dict(schema_version=1,status='approved',svg_sha256=visual['svg_sha256'],
            implementation=code_hashes(),checks=['full_frame','no_clipping','legible_labels','equal_geometry','shared_scale','deterministic_bytes']))
        print('Visual QA approval recorded');return
    claim('render-synthetic')
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        origin=(0,0); ds=((5,0),(18,-9),(18,9),(-7,4)); rs=((20,-10),(25,0),(20,10),(-10,5))
        def render():
            with matplotlib.rc_context({'svg.hashsalt':'phase14r-fixed','font.family':'DejaVu Sans','font.size':11}):
                fig,axes=plt.subplots(1,3,figsize=(18,8),dpi=100)
                fig.subplots_adjust(left=.045,right=.92,bottom=.12,top=.80,wspace=.16)
                fig.suptitle('SYNTHETIC · CARRIER-ORIGIN GEOMETRIC OCCLUSION HYPOTHESIS',fontsize=18,y=.955)
                fig.text(.5,.89,'NOT VALIDATED COVER SHADOW · NOT SUPPRESSION',ha='center',fontsize=14)
                x=np.linspace(-15,35,251);y=np.linspace(-20,20,201);xx,yy=np.meshgrid(x,y)
                for ax,candidate in zip(axes,CANDIDATES):
                    z=CarrierOriginField(candidate).combined_values(origin,ds,np.column_stack((xx.ravel(),yy.ravel())))
                    im=ax.imshow(z.reshape(xx.shape),extent=(-15,35,-20,20),origin='lower',cmap='YlGnBu',vmin=0,vmax=1,interpolation='nearest',aspect='equal')
                    for i,r in enumerate(rs):
                        ax.plot([0,r[0]],[0,r[1]],color='#b54a15',linewidth=1.5)
                        ax.scatter(*r,c='white',edgecolors='#b54a15',s=75,zorder=5)
                        ax.annotate(f'R{i+1}',r,xytext=(7,5),textcoords='offset points',weight='bold',bbox=dict(facecolor='white',edgecolor='none',alpha=.85,pad=1))
                    ax.scatter(*zip(*ds),c='#8a1744',marker='s',s=70,zorder=5)
                    for i,d in enumerate(ds):ax.annotate(f'D{i+1}',d,xytext=((7,-18) if i==3 else (-24,10)),textcoords='offset points',weight='bold',bbox=dict(facecolor='white',edgecolor='none',alpha=.85,pad=1))
                    ax.scatter(0,0,c='black',marker='*',s=180,zorder=6)
                    ax.annotate('Origin',origin,xytext=(-25,-19),textcoords='offset points',weight='bold')
                    ax.set(xlim=(-15,35),ylim=(-20,20),aspect='equal',xlabel='Metric x (m)',title=candidate.replace('_',' ').title())
                axes[0].set_ylabel('Metric y (m)')
                cax=fig.add_axes([.94,.26,.015,.43]);fig.colorbar(im,cax=cax,label='Union field (dimensionless)')
                fig.text(.5,.045,'Identical synthetic geometry in every panel · fixed scale 0–1 · no pitch or temporal inference',ha='center')
                fig.savefig(safe(LOCAL/'visual_preview.png'),format='png',dpi=100)
                buf=io.StringIO();fig.savefig(buf,format='svg',metadata={'Date':None,'Creator':'Session 14R3 synthetic illustration'});plt.close(fig)
                return '\n'.join(line.rstrip() for line in buf.getvalue().replace('width="1296pt" height="576pt"', 'width="1800px" height="800px"').splitlines())+'\n'
        first=render();second=render();pv.require(first==second,'visual_nondeterminism')
        atomic(OUT/'synthetic_field_comparison.svg',first)
        write(AUTH/'visual_generation.json',dict(schema_version=1,status='generated_requires_visual_qa',
            svg_sha256=digest(OUT/'synthetic_field_comparison.svg'),byte_identical=True))
        ledger('render-synthetic','generated')
        print('Synthetic SVG generated twice identically; full-frame inspection required before approval')
    except Exception as e:
        failure('render-synthetic',e,0);raise


def check_binding(prod):
    pv.require(prod['status']=='passed' and prod['protocol']==digest(PROTOCOL),'production_protocol')
    pv.require(prod['implementation']==code_hashes(),'implementation_changed')
    pv.require(prod['inherited']==inherited_hashes(),'historical_code')
    pv.require(prod['environment']==environment() and VerificationReadiness(**prod['readiness']).ready,'production_environment')


def empirical_authority():
    preflight()
    pv.require(not git('status','--porcelain'),'clean_tree_required')
    ci=load(LOCAL/'ci.json')
    pv.require(ci['head']==git('rev-parse','HEAD'),'ci_checkpoint')
    pv.require(ci['python311']=='success' and ci['python313']=='success' and ci['distribution']=='success','preaccess_ci')
    for path in (PROTOCOL,*map(Path,CODE),AUTH/'production.json',AUTH/'visual_approval.json',OUT/'synthetic_field_comparison.svg'):
        committed(path)
    check_binding(load(AUTH/'production.json'))
    pv.require(load(AUTH/'visual_approval.json')['svg_sha256']==digest(OUT/'synthetic_field_comparison.svg'),'visual_authority')



def prepare():
    if not ACCESS['authorized']: raise PermissionError('single_launch_required')
    ACCESS['stage']='prepare'
    count=Counter();seen=set();n=0
    try:
        ledger('population','hash_before_parse');ACCESS['population_opens']+=1
        pv.require(digest(POP)==POP_SHA,'population_hash')
        dest=safe(LOCAL/'prepared.jsonl')
        ACCESS['population_opens']+=1
        with safe(POP).open() as src,dest.open('x') as dst:
            for line in src:
                key,row=project_line(line)
                pv.require(key not in seen,'duplicate_observation');seen.add(key)
                count[row['alias']]+=1;n+=1;ACCESS['states_prepared']=n
                dst.write(json.dumps(row,sort_keys=True,allow_nan=False)+'\n')
        pv.require(n==7227 and tuple(count[a] for a in ALIASES)==COUNTS,'population_counts')
        ACCESS['population_opens']+=1
        pv.require(digest(POP)==POP_SHA,'population_changed')
        write(LOCAL/'population.json',dict(schema_version=1,status='prepared_geometry_only',states=n,counts=dict(count),
              population_sha256=POP_SHA,prepared_sha256=digest(LOCAL/'prepared.jsonl'),
              protocol=digest(PROTOCOL),implementation=code_hashes(),ci=load(LOCAL/'ci.json')))
        ledger('prepare','passed');print('Prepared 7,227 geometry-only states; private population authority frozen within launch')
    except Exception as e:
        failure('prepare',e,n);raise


class Collect:
    def __init__(self):self.data=defaultdict(list)
    def add(self,file,alias,state,metric,values,*,candidate='none',comparison='none',summary='none',combination='none',unit='edge',source_observations=None):
        key=(file,candidate,comparison,summary,combination,metric,unit)
        vals=[float(x) for x in values if x is not None]
        if not all(math.isfinite(x) for x in vals):raise ValueError('nonfinite_metric')
        self.data[key].append((alias,state,vals,len(vals) if source_observations is None else source_observations))
    def tables(self):
        tables={f:[] for f in CSV_FILES}
        for key,records in sorted(self.data.items()):
            file,candidate,comparison,summary,combination,metric,unit=key
            for group in (*ALIASES,'macro'):
                selected=[x for x in records if group=='macro' or x[0]==group]
                valid=[x for x in selected if x[2]]
                bymatch=Counter(a for a,s,v,n in valid)
                values=[];weights=[]
                for alias,state,v,n in valid:
                    values.extend(v);weights.extend([1/len(bymatch)/bymatch[alias]/len(v)]*len(v))
                row=dict(candidate=candidate,comparison=comparison,summary=summary,combination=combination,
                         metric=metric,alias=group,unit=unit,represented_matches=len(bymatch),
                         states_total=len(selected),states_assessable=len(valid),states_unavailable=len(selected)-len(valid),
                         observations=len(values),source_observations=sum(x[3] for x in selected),**weighted_summary(values,weights))
                tables[file].append(row)
        return tables


def mean(xs):return math.fsum(xs)/len(xs) if len(xs) else None


def summarize_state(row,state_index,collector,across):
    alias=row['alias'];receivers=row['receivers'];defenders=row['defenders'];origin=row['carrier']
    state=OptionState(origin,tuple(f'R{i+1}' for i in range(len(receivers))),receivers,defenders)
    mapping=map_defender_edges(state);geometry=summarize_edge_involvement(mapping)
    edges=geometry['edge_summaries'];relations=[mapping.for_receiver(i) for i in range(len(receivers))]
    rd=[min(r.receiver_distance for r in rs) for rs in relations]
    sd=[min(r.segment_distance for r in rs) for rs in relations]
    gaps={name:[r['segment_'+name] for r in edges] for name in ('d2_d1','d3_d1')}
    descriptor={name:mean([x for x in v if x is not None]) for name,v in gaps.items()}
    for k in (1,2,3):
        descriptor[f'top{k}_jaccard']=mean(geometry['segment_pair_jaccard'][f'top{k}'])
        descriptor[f'top{k}_distinct']=float(len({r.defender_index for r in mapping.relations if r.membership('segment',k)>0}))
        descriptor[f'top{k}_maximum_involvement']=max(x[f'segment_top{k}_involvement'] for x in geometry['defender_summaries'].values())
    def add(file,metric,values,**kw):collector.add(file,alias,state_index,metric,values,**kw)
    for metric in ('nearest_intersects','nearest_equal','nearest_jaccard'):
        add('receiver_segment_divergence.csv',metric,[x[metric] for x in edges])
    pairs=discordant_pairs(rd,sd)
    validpairs=[(i,j) for i in range(len(rd)) for j in range(i+1,len(rd)) if
                block_ranks(rd,False)[i]!=block_ranks(rd,False)[j] and block_ranks(sd,False)[i]!=block_ranks(sd,False)[j]]
    discord={(i,j) for i,j,_ in pairs}
    add('receiver_segment_divergence.csv','raw_order_disagreement',[float((i,j) in discord) for i,j in validpairs],unit='pair')
    fields={};qc=[]
    for candidate in CANDIDATES:
        results=[]
        for ordinal,r in enumerate(receivers):
            context=dict(state_ordinal=state_index,edge_ordinal=ordinal,candidate=candidate,stage='edge_start')
            def record(**kw):
                context.update(kw)
                safe(LOCAL).mkdir(parents=True,exist_ok=True)
                with safe(LOCAL/'edge_stages.jsonl').open('a') as f:f.write(json.dumps(context,allow_nan=False)+'\n')
            record()
            ACCESS['edges_started']+=1
            results.append(evaluate_edge(candidate,origin,r,defenders,record))
            ACCESS['edges_completed']+=1
        qc.extend((r.intervals,r.convergence_change,r.maximum_reference_error) for r in results)
        fields[candidate]={}
        for summary in ('receiver','segment'):
            uv=[getattr(r,summary+'_union') for r in results];mv=[getattr(r,summary+'_maximum') for r in results]
            overlap=[u-m for u,m in zip(uv,mv)]
            # Negative beyond the same numerical equality tolerance is an integrity defect.
            pv.require(min(overlap)>=-1e-12,'union_less_than_maximum')
            add('union_vs_max.csv','difference',overlap,candidate=candidate,summary=summary)
            add('union_vs_max.csv','numerically_equal',[float(abs(v)<=1e-12) for v in overlap],candidate=candidate,summary=summary)
            if summary=='segment':
                for name,g in gaps.items():
                    kept=[(x,y) for x,y in zip(overlap,g) if y is not None]
                    rho=spearman([x for x,y in kept],[y for x,y in kept])
                    add('structural_correspondence.csv','overlap_vs_'+name,[rho],candidate=candidate,summary=summary,unit='state')
                across.append((alias,state_index,candidate,mean(overlap),descriptor))
            for combination,vals in (('union',uv),('maximum',mv)):
                kw=dict(candidate=candidate,summary=summary,combination=combination)
                fields[candidate][summary,combination]=vals
                add('match_summary.csv','field',vals,**kw)
                distances=rd if summary=='receiver' else sd
                add('structural_correspondence.csv','field_vs_negative_distance',[spearman(vals,[-x for x in distances])],unit='state',**kw)
                for metric,vs in follows(vals,pairs).items():add('receiver_segment_divergence.csv',metric,vs,unit='pair',**kw)
            individual=[getattr(r,summary+'_individual') for r in results]
            sets=[maximum_set(v) for v in individual];available=[s for s in sets if s]
            involvement=Counter(d for s in available for d in s)
            kw=dict(candidate=candidate,summary=summary)
            add('multi_edge_summary.csv','distinct_maximum_defenders',[float(len(involvement))] if available else [],unit='state',**kw)
            add('multi_edge_summary.csv','multi_edge',[float(max(involvement.values())>=2)] if available else [],unit='state',**kw)
            add('multi_edge_summary.csv','maximum_involvement',[float(max(involvement.values()))] if available else [],unit='state',**kw)
            add('multi_edge_summary.csv','field_owner_available',[float(bool(s)) for s in sets],**kw)
            for kind in ('receiver','segment'):
                intersects=[];jaccards=[];fractions={k:[] for k in (1,2,3)}
                for rs,v,s in zip(relations,individual,sets):
                    nearest={r.defender_index for r in rs if getattr(r,kind+'_block')==0}
                    if s:
                        intersects.append(float(bool(s&nearest)));jaccards.append(len(s&nearest)/len(s|nearest))
                    total=math.fsum(v)
                    for k in (1,2,3):
                        if total>0:fractions[k].append(math.fsum(v[r.defender_index]*r.membership(kind,k) for r in rs)/total)
                add('multi_edge_summary.csv',kind+'_nearest_intersection',intersects,**kw)
                add('multi_edge_summary.csv',kind+'_nearest_jaccard',jaccards,**kw)
                for k in fractions:add('multi_edge_summary.csv',kind+f'_top{k}_strength_fraction',fractions[k],**kw)
    for candidate in CANDIDATES:
        for combination in ('union','maximum'):
            a=fields[candidate]['receiver',combination];b=fields[candidate]['segment',combination]
            kw=dict(candidate=candidate,comparison='receiver_to_segment',combination=combination)
            add('receiver_segment_divergence.csv','field_summary_spearman',[spearman(a,b)],unit='state',**kw)
            for metric,vs in order_categories(a,b).items():add('receiver_segment_divergence.csv',metric,vs,unit='pair',**kw)
    for first,second in itertools.combinations(CANDIDATES,2):
        for summary in ('receiver','segment'):
            for combination in ('union','maximum'):
                a=fields[first][summary,combination];b=fields[second][summary,combination]
                kw=dict(comparison=first+'_to_'+second,summary=summary,combination=combination)
                add('candidate_pair_comparison.csv','paired_difference',[y-x for x,y in zip(a,b)],**kw)
                add('candidate_pair_comparison.csv','candidate_pair_spearman',[spearman(a,b)],unit='state',**kw)
                for metric,vs in order_categories(a,b).items():add('candidate_pair_comparison.csv',metric,vs,unit='pair',**kw)
    return qc


def add_across(collector,across):
    for candidate in CANDIDATES:
        names=sorted(next(x[4] for x in across if x[2]==candidate))
        for name in names:
            for alias in ALIASES:
                rows=[x for x in across if x[0]==alias and x[2]==candidate and x[4][name] is not None]
                rho=spearman([x[3] for x in rows],[x[4][name] for x in rows])
                collector.add('structural_correspondence.csv',alias,-1,'across_state_overlap_vs_'+name,[rho],
                              candidate=candidate,summary='segment',unit='match',source_observations=len(rows))


def write_csv(name,rows,base=OUT):
    buf=io.StringIO(newline='');writer=csv.DictWriter(buf,fieldnames=COLUMNS,lineterminator='\n')
    writer.writeheader();writer.writerows(rows);atomic(base/name,buf.getvalue())


def analyze():
    if not ACCESS['authorized']: raise PermissionError('single_launch_required')
    ACCESS['stage']='analyze'
    population=load(LOCAL/'population.json')
    pv.require(population['prepared_sha256']==digest(LOCAL/'prepared.jsonl'),'prepared_hash')
    done=0;collector=Collect();across=[];qc=[]
    try:
        with safe(LOCAL/'prepared.jsonl').open() as f:
            for index,line in enumerate(f):
                row=json.loads(line)
                qc.extend(summarize_state(row,index,collector,across));done+=1;ACCESS['states_completed']=done
                if done%10==0:ledger('analyze',f'states_completed_{done}')
        pv.require(done==7227,'analysis_count');add_across(collector,across)
        tables=collector.tables()
        staging=LOCAL/'package'
        for name,rows in tables.items():write_csv(name,rows,staging)
        write(staging/'candidate_summary.json',dict(schema_version=1,status='closed_descriptive_evidence',
            candidates=list(CANDIDATES),scope='label_free_spent_development_geometry',
            origin='carrier-position proxy for ball origin',states=done,counts=dict(zip(ALIASES,COUNTS)),
            classifications='report_after_hash_closure'))
        write(staging/'qc.json',dict(schema_version=1,status='valid',stage='analyze',states_completed=done,
            empirical_access=True,access=dict(ACCESS),exception=None,interval_counts=dict(Counter(str(x[0]) for x in qc)),
            max_joint_change=max(x[1] for x in qc),max_maximum_reference_error=max(x[2] for x in qc)))
        for name in ('synthetic_stress_summary.json','synthetic_field_comparison.svg'):
            atomic(staging/name,safe(OUT/name).read_text())
        validate_payloads(FINAL_FILES,'valid',staging)
        ledger('analyze','private_package_validated')
    except Exception as e:
        # Values already calculated stay private; never publish a partial scientific comparison.
        write(LOCAL/'partial_summary.json',dict(states_completed=done,qc=qc,
            records=[dict(key=k,values=v) for k,v in collector.data.items()],across=across))
        failure('analyze',e,done);raise


def finite(value):
    if isinstance(value,float) and not math.isfinite(value):raise ValueError('nonfinite')
    if isinstance(value,dict):
        for v in value.values():finite(v)
    elif isinstance(value,(list,tuple)):
        for v in value:finite(v)


def failure(stage,error,states):
    detail=dict(stage=stage,exception=type(error).__name__,message=str(error),traceback=traceback.format_exc(),states_completed=states)

    if safe(OUT/'manifest.json').exists(): return
    write(LOCAL/'failure.json',detail);ledger(stage,'failed')
    if not safe(OUT/'qc.json').exists():
        write(OUT/'qc.json',dict(schema_version=1,status='blocked',stage=stage,states_completed=states,
            empirical_access=ACCESS['population_opens']>0,access=dict(ACCESS),exception=type(error).__name__,interval_counts={},
            max_joint_change=None,max_maximum_reference_error=None))
    close_manifest('blocked')
    print('Session 14R3 blocked; failure preserved, automatic rerun forbidden')


def validate_payloads(files,status,base=OUT):
    pv.require(status in ('valid','blocked'),'package_status')
    pv.require(set(files)<=set(FINAL_FILES),'unexpected_output')
    for name in files:
        path=base/name
        if name.endswith('.json'):
            value=load(path);finite(value)
            schemas={
                'candidate_summary.json':{'schema_version','status','candidates','scope','origin','states','counts','classifications'},
                'synthetic_stress_summary.json':{'schema_version','scope','records'},
                'qc.json':{'schema_version','status','stage','states_completed','empirical_access','access','exception','interval_counts','max_joint_change','max_maximum_reference_error'}}
            if name not in schemas or set(value)!=schemas[name]:raise ValueError('output_schema')
            pv.require(value['schema_version']==1,'schema_version')
            if name=='qc.json':
                pv.require(value['status']==status and type(value['empirical_access']) is bool,'qc_status')
                pv.require(type(value['states_completed']) is int and 0<=value['states_completed']<=7227,'qc_count')
                pv.require(set(value['access'])==set(ACCESS),'access_schema')
                counts=value['access']
                for key in ('population_opens','states_prepared','states_completed','edges_started','edges_completed'):
                    pv.require(type(counts[key]) is int and counts[key]>=0,'access_count_type')
                pv.require(counts['edges_completed']<=counts['edges_started'],'edge_completion_count')
                pv.require(value['empirical_access']==(counts['population_opens']>0),'access_truth')
                pv.require(value['stage'] in ('preflight','verify-production','render-synthetic','run','prepare','analyze','startup'),'qc_stage')
                pv.require((value['exception'] is None)==(status=='valid'),'qc_exception')
            if name=='candidate_summary.json':
                pv.require(value['states']==7227 and value['counts']==dict(zip(ALIASES,COUNTS)) and value['candidates']==list(CANDIDATES),'summary_membership')
        if name in CSV_FILES:
            with safe(path).open(newline='') as f:
                reader=csv.DictReader(f);pv.require(tuple(reader.fieldnames)==COLUMNS,'csv_schema');rows=list(reader)
            pv.require(bool(rows),'empty_table')
            rowkeys=[tuple(row[k] for k in (*KEYS,'alias','unit')) for row in rows]
            pv.require(len(set(rowkeys))==len(rowkeys),'duplicate_output_rows')
            families={tuple(row[k] for k in (*KEYS,'unit')) for row in rows}
            pv.require(families==expected_families()[name],'exact_row_families')
            pv.require(len(rows)==10*len(families),'all_match_rows')
            for row in rows:
                pv.require(row['alias'] in (*ALIASES,'macro'),'alias')
                pv.require(row['candidate'] in (*CANDIDATES,'none'),'candidate')
                pv.require(row['summary'] in ('receiver','segment','none'),'summary')
                pv.require(row['combination'] in ('union','maximum','none'),'combination')
                pv.require(row['comparison'] in ('none','receiver_to_segment',*[a+'_to_'+b for a,b in itertools.combinations(CANDIDATES,2)]),'comparison')
                pv.require(row['unit'] in ('edge','pair','state','match'),'unit')
                for key in ('represented_matches','states_total','states_assessable','states_unavailable','observations','source_observations'):
                    pv.require(int(row[key])>=0,'negative_count')
                pv.require(int(row['represented_matches'])<=9,'represented_matches')
                values=[row[k] for k in STAT_KEYS]
                pv.require(all(x=='' for x in values) or all(x!='' for x in values),'partial_statistics')
                if values[0]!='':
                    pv.require(float(row['minimum'])<=float(row['mean'])+1e-12 and float(row['mean'])<=float(row['maximum'])+1e-12,'mean_bounds')
                    quantiles=[float(row[k]) for k in ('minimum','q05','q25','q50','q75','q95','maximum')]
                    pv.require(quantiles==sorted(quantiles),'quantile_order')
                for key in STAT_KEYS:
                    if row[key]!='':pv.require(math.isfinite(float(row[key])),'finite_csv')
                pv.require(int(row['states_total'])==int(row['states_assessable'])+int(row['states_unavailable']),'csv_counts')
        if not name.endswith('.svg'):
            text=safe(path).read_text()
            for forbidden in (*DEVELOPMENT,'/Users/','/private/','target_index','event_id','carrier_xy','candidate_xy','defender_xy','token='):
                if forbidden in text:raise ValueError('publication_content')
    if status=='valid':
        pv.require(set(files)==set(FINAL_FILES),'complete_outputs')
        q=load(base/'qc.json');pv.require(q['states_completed']==7227 and q['exception'] is None,'valid_qc')
        pv.require(q['access']['states_completed']==7227 and q['access']['states_prepared']==7227,'complete_access_counts')
        pv.require(q['access']['edges_started']==q['access']['edges_completed'],'complete_edges')


def expected_families():
    """Exact prospective CSV families; all have nine aliases plus macro."""
    result={name:set() for name in CSV_FILES}
    def add(file,metric,candidate='none',comparison='none',summary='none',combination='none',unit='edge'):
        result[file].add((candidate,comparison,summary,combination,metric,unit))
    divergence='receiver_segment_divergence.csv'; structure='structural_correspondence.csv'
    orders=('agreement','strict_reversal','tie_creation','tie_removal','both_tied')
    for metric in ('nearest_intersects','nearest_equal','nearest_jaccard'):add(divergence,metric)
    add(divergence,'raw_order_disagreement',unit='pair')
    for c in CANDIDATES:
        for s in ('receiver','segment'):
            for metric in ('difference','numerically_equal'):add('union_vs_max.csv',metric,c,summary=s)
            for combination in ('union','maximum'):
                add('match_summary.csv','field',c,summary=s,combination=combination)
                add(structure,'field_vs_negative_distance',c,summary=s,combination=combination,unit='state')
                for metric in ('endpoint_following','corridor_following','tied'):
                    add(divergence,metric,c,summary=s,combination=combination,unit='pair')
            for metric in ('distinct_maximum_defenders','multi_edge','maximum_involvement'):
                add('multi_edge_summary.csv',metric,c,summary=s,unit='state')
            add('multi_edge_summary.csv','field_owner_available',c,summary=s)
            for kind in ('receiver','segment'):
                for suffix in ('nearest_intersection','nearest_jaccard','top1_strength_fraction','top2_strength_fraction','top3_strength_fraction'):
                    add('multi_edge_summary.csv',kind+'_'+suffix,c,summary=s)
        for gap in ('d2_d1','d3_d1'):add(structure,'overlap_vs_'+gap,c,summary='segment',unit='state')
        for descriptor in ('d2_d1','d3_d1',*[f'top{k}_{suffix}' for k in (1,2,3) for suffix in ('jaccard','distinct','maximum_involvement')]):
            add(structure,'across_state_overlap_vs_'+descriptor,c,summary='segment',unit='match')
        for combination in ('union','maximum'):
            for metric in ('field_summary_spearman',*orders):
                add(divergence,metric,c,'receiver_to_segment',combination=combination,
                    unit='state' if metric=='field_summary_spearman' else 'pair')
    for a,b in itertools.combinations(CANDIDATES,2):
        for s in ('receiver','segment'):
            for combination in ('union','maximum'):
                for metric in ('paired_difference','candidate_pair_spearman',*orders):
                    add('candidate_pair_comparison.csv',metric,comparison=a+'_to_'+b,summary=s,combination=combination,
                        unit='edge' if metric=='paired_difference' else 'state' if metric=='candidate_pair_spearman' else 'pair')
    return result


def close_manifest(status):
    existing=[name for name in FINAL_FILES if safe(OUT/name).exists()]
    validate_payloads(existing,status)
    authority={str(p.relative_to(ROOT)):digest(p.relative_to(ROOT)) for p in safe(AUTH).glob('*.json')} if safe(AUTH).exists() else {}
    write(OUT/'manifest.json',dict(schema_version=1,status=status,start=START,protocol=digest(PROTOCOL),
        implementation=code_hashes(),environment=environment(),authority=authority,
        outputs={name:digest(OUT/name) for name in existing},unavailable=[n for n in FINAL_FILES if n not in existing]))


def publication_check():
    history();m=load(OUT/'manifest.json')
    pv.require(set(m)=={'schema_version','status','start','protocol','implementation','environment','authority','outputs','unavailable'},'manifest_schema')
    pv.require(m['protocol']==digest(PROTOCOL) and m['implementation']==code_hashes() and (m['environment']==environment() or (m['status']=='blocked' and m['environment']=={'unavailable':'runtime_import_failure'})),'manifest_authority')
    pv.require(set(m['outputs'])|set(m['unavailable'])==set(FINAL_FILES) and not set(m['outputs'])&set(m['unavailable']),'manifest_membership')
    for p,h in m['authority'].items():pv.require(digest(p)==h,'authority_hash')
    for p,h in m['outputs'].items():pv.require(digest(OUT/p)==h,'output_hash')
    validate_payloads(m['outputs'],m['status']);print('Session 14R3 publication checks passed: '+m['status'])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=('preflight','verify-production','render-synthetic','run','publication-check'))
    parser.add_argument('--approve-visual',action='store_true');args=parser.parse_args()
    if args.approve_visual and args.command!='render-synthetic':parser.error('visual approval requires render-synthetic')
    routes={'preflight':preflight,'verify-production':verify_production,'render-synthetic':lambda:render_synthetic(args.approve_visual),
            'run':run,'publication-check':publication_check}
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error')
            routes[args.command]()
    except Exception as exc:
        if args.command!='publication-check':failure(args.command,exc,ACCESS['states_completed'])
        raise





def observe():
    if Path(sys.prefix).resolve()!=safe(Path('.venv')).resolve():
        raise RuntimeError('project_environment_required')
    return EnvironmentObservation(platform.python_version(),platform.python_implementation(),True,
        'uv-locked-project-environment',digest('uv.lock'),
        tuple((name,version(name)) for name in ('numpy','scipy','matplotlib')))


def expectation(env):
    return PrerequisiteExpectation(digest(PROTOCOL),hashlib.sha256(encoded(code_hashes()).encode()).hexdigest(),
        digest('uv.lock'),env.fingerprint(),TEST_COMMAND)


def produce_tests(path,exp=None):
    env=observe();exp=exp or expectation(env)
    result=subprocess.run([sys.executable,*TEST_COMMAND],cwd=ROOT,text=True,capture_output=True)
    output=result.stdout+result.stderr
    record=test_record(exp,output,result.returncode)
    write(path,record)


def run():
    preflight()
    launcher=R3Launch(safe(LOCAL/'launch'))
    def producer(path,exp):produce_tests(path.relative_to(ROOT),exp)
    def verify(context):empirical_authority();return True
    def access(context):
        ACCESS['authorized']=True
        prepare()
        analyze()
    try:
        launcher.execute(discover=observe,expected=expectation,produce=producer,verify=verify,access=access)
        for name in (*[n for n in FINAL_FILES if n!='qc.json'],'qc.json'):
            if safe(OUT/name).exists():
                pv.require(digest(OUT/name)==digest(LOCAL/'package'/name),'staged_existing_hash')
            else:atomic(OUT/name,safe(LOCAL/'package'/name).read_text())
        close_manifest('valid');ledger('run','closed')
        print('Representation aggregates closed and hash-validated')
    except Exception as exc:
        failure(ACCESS['stage'] if ACCESS['authorized'] else 'run',exc,ACCESS['states_completed'])
        raise


if __name__=='__main__':main()
