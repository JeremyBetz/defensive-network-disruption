#!/usr/bin/env python3
"""Governed Session 14R, explicit label-free geometry and immutable stages."""
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
import numpy as np
from defensive_network_disruption.geometry import production_verification as pv
from defensive_network_disruption.geometry.occlusion_fields import CANDIDATES, CarrierOriginField, combine
from defensive_network_disruption.geometry.verification_repair import VerificationReadiness
from defensive_network_disruption.geometry.representation_study import (
    evaluate_edge, spearman, weighted_summary, maximum_set, order_categories,
    discordant_pairs, follows, block_ranks)
from defensive_network_disruption.data.representation_projection import project_line, ALIASES, COUNTS, DEVELOPMENT
from defensive_network_disruption.networks.options import OptionState
from defensive_network_disruption.networks.defender_edges import map_defender_edges, summarize_edge_involvement

START='3f58ede93143fda336e3e6515e15b0cc8c1a6fa9'
TAG='f00690c05d8c1c6db308a65bd311c43f9a8ef2fa'
POP_SHA='cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d'
POP=Path('outputs/receiver_ranking_m0_m1/local/population.jsonl')
OUT=Path('outputs/continuous_occlusion_retry'); LOCAL=OUT/'local'; AUTH=OUT/'authority'
PROTOCOL=Path('docs/protocols/phase_14r_continuous_occlusion_retry.md')
CODE=('scripts/session_14r_occlusion_study.py',
      'src/defensive_network_disruption/geometry/representation_study.py',
      'src/defensive_network_disruption/data/representation_projection.py','tests/test_session14r_study.py')
CSV_FILES=('structural_correspondence.csv','receiver_segment_divergence.csv','union_vs_max.csv','multi_edge_summary.csv','match_summary.csv')
FINAL_FILES=('candidate_summary.json',*CSV_FILES,'synthetic_stress_summary.json','qc.json','synthetic_field_comparison.svg')
KEYS=('candidate','comparison','summary','combination','metric')
STAT_KEYS=('mean','minimum','maximum','q05','q25','q50','q75','q95')
COLUMNS=(*KEYS,'alias','unit','represented_matches','states_total','states_assessable','states_unavailable','observations','source_observations',*STAT_KEYS)


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
    return {p:digest(p) for p in names if p.startswith('src/') or
            p in ('uv.lock','scripts/session_14i_signature_repair.py','scripts/session_14_occlusion_fields.py') or
            p.startswith('outputs/continuous_occlusion_') and not '/local/' in p or
            p=='outputs/defender_edge_influence/manifest.json'}


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
    print('Session 14R preflight passed; no empirical input opened')


def synthetic_module():
    # Only explicit pure synthetic authority functions are called, never the old audit.
    spec=importlib.util.spec_from_file_location('session14i_authority',safe('scripts/session_14i_signature_repair.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def verify_production():
    preflight();claim('verify-production')
    rows=[]; checks=[]; injections=[]
    try:
        bound=inherited_hashes(); module=synthetic_module()
        checks=pv.engineering_checks();pv.require(all(x['passed'] for x in checks),'engineering_checks')
        injections,enforced=module.failure_injections();pv.require(enforced,'failure_enforcement')
        for fixture,case in module.authority_cases():
            outcome=pv.run_pipeline([case],bound,bound,enforced)
            pv.require(outcome.readiness.ready,'synthetic_pipeline')
            r=outcome.accepted[0]
            rows.append(dict(fixture=fixture,candidate=case['candidate'],intervals=r['intervals'],
                             estimates=r['estimates'],errors=r['errors'],permutations=r['permutations']))
        pv.require(len(rows)==108 and sum(len(x['errors']) for x in rows)==366 and
                   sum(x['permutations'] for x in rows)==399,'acceptance_counts')
        gate=VerificationReadiness(continuity_verified=all(x['passed'] for x in checks),
            switching_verified=len(rows)==108,controlled_integration_verified=all(x['intervals'] is not None for x in rows),
            references_complete=sum(len(x['errors']) for x in rows)==366,
            permutation_verified=sum(x['permutations'] for x in rows)==399,deterministic=all(x['passed'] for x in checks),
            failure_enforcement_verified=enforced,blocking_warnings_absent=True,
            integrity_verified=bound==inherited_hashes())
        pv.require(gate.ready,'readiness_false')
        write(AUTH/'production.json',dict(schema_version=1,status='passed',protocol=digest(PROTOCOL),
              implementation=code_hashes(),inherited=bound,environment=environment(),
              readiness=asdict(gate),cases=rows,engineering=checks,injections=injections))
        stress=[x for x in rows if x['fixture'].startswith('equal_minimum')]
        write(OUT/'synthetic_stress_summary.json',dict(schema_version=1,scope='synthetic_only',records=stress))
        ledger('verify-production','passed');print('Synthetic production gate passed: 108 cases, 366 references, 399 permutations')
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
                buf=io.StringIO();fig.savefig(buf,format='svg',metadata={'Date':None,'Creator':'Session 14R synthetic illustration'});plt.close(fig)
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
    current=code_hashes()
    if prod['implementation'] != current:
        # Only the explicitly allowed pre-access renderer and binding check changed.
        import ast
        revision=load(AUTH/'visual_revision.json')
        baseline=safe(LOCAL/'verified_runner.py.txt').read_text()
        pv.require(hashlib.sha256(baseline.encode()).hexdigest()==prod['implementation'][CODE[0]],'baseline_source')
        for name in CODE[1:]:pv.require(prod['implementation'][name]==current[name],'numerical_code_changed')
        def signature(text):
            tree=ast.parse(text)
            tree.body=[n for n in tree.body if not isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) or n.name not in ('render_synthetic','check_binding')]
            return hashlib.sha256(ast.dump(tree,include_attributes=False).encode()).hexdigest()
        pv.require(signature(baseline)==signature(safe(CODE[0]).read_text())==revision['nonvisual_runner_ast_sha256'],'nonvisual_code_changed')
    pv.require(prod['inherited']==inherited_hashes(),'historical_code')
    pv.require(prod['environment']==environment() and VerificationReadiness(**prod['readiness']).ready,'production_environment')


def empirical_authority(prepared=False):
    preflight()
    pv.require(not git('status','--porcelain'),'clean_tree_required')
    for path in (PROTOCOL,*map(Path,CODE),AUTH/'production.json',AUTH/'visual_approval.json',OUT/'synthetic_field_comparison.svg'):
        committed(path)
    check_binding(load(AUTH/'production.json'))
    pv.require(load(AUTH/'visual_approval.json')['svg_sha256']==digest(OUT/'synthetic_field_comparison.svg'),'visual_authority')
    if prepared:
        committed(AUTH/'population.json');p=load(AUTH/'population.json')
        pv.require(p['implementation']==code_hashes() and p['protocol']==digest(PROTOCOL),'prepared_authority')
        pv.require(p['prepared_sha256']==digest(LOCAL/'prepared.jsonl'),'prepared_hash')
        pv.require(p['states']==7227 and p['counts']==dict(zip(ALIASES,COUNTS)),'prepared_counts')


def prepare():
    empirical_authority();claim('prepare');count=Counter();seen=set();n=0
    try:
        ledger('population','hash_before_parse')
        pv.require(digest(POP)==POP_SHA,'population_hash')
        dest=safe(LOCAL/'prepared.jsonl')
        with safe(POP).open() as src,dest.open('x') as dst:
            for line in src:
                key,row=project_line(line)
                pv.require(key not in seen,'duplicate_observation');seen.add(key)
                count[row['alias']]+=1;n+=1
                dst.write(json.dumps(row,sort_keys=True,allow_nan=False)+'\n')
        pv.require(n==7227 and tuple(count[a] for a in ALIASES)==COUNTS,'population_counts')
        pv.require(digest(POP)==POP_SHA,'population_changed')
        write(AUTH/'population.json',dict(schema_version=1,status='prepared_geometry_only',states=n,counts=dict(count),
              population_sha256=POP_SHA,prepared_sha256=digest(LOCAL/'prepared.jsonl'),
              protocol=digest(PROTOCOL),implementation=code_hashes()))
        ledger('prepare','passed');print('Prepared 7,227 geometry-only states; commit population authority before analysis')
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
        results=[evaluate_edge(candidate,origin,r,defenders) for r in receivers]
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
    for first,second in itertools.combinations(CANDIDATES,2):
        for summary in ('receiver','segment'):
            for combination in ('union','maximum'):
                a=fields[first][summary,combination];b=fields[second][summary,combination]
                kw=dict(comparison=first+'_to_'+second,summary=summary,combination=combination)
                add('match_summary.csv','paired_difference',[y-x for x,y in zip(a,b)],**kw)
                add('structural_correspondence.csv','candidate_pair_spearman',[spearman(a,b)],unit='state',**kw)
                for metric,vs in order_categories(a,b).items():add('structural_correspondence.csv',metric,vs,unit='pair',**kw)
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


def write_csv(name,rows):
    buf=io.StringIO(newline='');writer=csv.DictWriter(buf,fieldnames=COLUMNS,lineterminator='\n')
    writer.writeheader();writer.writerows(rows);atomic(OUT/name,buf.getvalue())


def analyze():
    empirical_authority(True);claim('analyze');done=0;collector=Collect();across=[];qc=[]
    try:
        with safe(LOCAL/'prepared.jsonl').open() as f:
            for index,line in enumerate(f):
                row=json.loads(line)
                qc.extend(summarize_state(row,index,collector,across));done+=1
                if done%10==0:ledger('analyze',f'states_completed_{done}')
        pv.require(done==7227,'analysis_count');add_across(collector,across)
        tables=collector.tables()
        for name,rows in tables.items():write_csv(name,rows)
        write(OUT/'candidate_summary.json',dict(schema_version=1,status='closed_descriptive_evidence',
            candidates=list(CANDIDATES),scope='label_free_spent_development_geometry',
            origin='carrier-position proxy for ball origin',states=done,counts=dict(zip(ALIASES,COUNTS)),
            classifications='report_after_hash_closure'))
        write(OUT/'qc.json',dict(schema_version=1,status='valid',stage='analyze',states_completed=done,
            empirical_access=True,exception=None,interval_counts=dict(Counter(str(x[0]) for x in qc)),
            max_joint_change=max(x[1] for x in qc),max_maximum_reference_error=max(x[2] for x in qc)))
        close_manifest('valid');ledger('analyze','closed');print('Representation aggregates closed and hash-validated')
    except Exception as e:
        # Values already calculated stay private; never publish a partial scientific comparison.
        write(LOCAL/'partial_summary.json',dict(states_completed=done,qc=qc,
            records=[dict(key=k,values=v) for k,v in collector.data.items()],across=across))
        failure('analyze',e,done);raise


def finite(value):
    if isinstance(value,float) and not math.isfinite(value):raise ValueError('nonfinite')
    if isinstance(value,dict):
        for v in value.values():finite(v)
    elif isinstance(value,list):
        for v in value:finite(v)


def failure(stage,error,states):
    detail=dict(stage=stage,exception=type(error).__name__,message=str(error),traceback=traceback.format_exc(),states_completed=states)
    write(LOCAL/'failure.json',detail);ledger(stage,'failed')
    if not safe(OUT/'qc.json').exists():
        write(OUT/'qc.json',dict(schema_version=1,status='blocked',stage=stage,states_completed=states,
            empirical_access=stage in ('prepare','analyze'),exception=type(error).__name__,interval_counts={},
            max_joint_change=None,max_maximum_reference_error=None))
    close_manifest('blocked')
    print('Session 14R blocked; failure preserved, automatic rerun forbidden')


def validate_payloads(files,status):
    for name in files:
        path=OUT/name
        if name.endswith('.json'):
            value=load(path);finite(value)
            schemas={
                'candidate_summary.json':{'schema_version','status','candidates','scope','origin','states','counts','classifications'},
                'synthetic_stress_summary.json':{'schema_version','scope','records'},
                'qc.json':{'schema_version','status','stage','states_completed','empirical_access','exception','interval_counts','max_joint_change','max_maximum_reference_error'}}
            if name in schemas and set(value)!=schemas[name]:raise ValueError('output_schema')
        if name in CSV_FILES:
            with safe(path).open(newline='') as f:
                reader=csv.DictReader(f);pv.require(tuple(reader.fieldnames)==COLUMNS,'csv_schema');rows=list(reader)
            pv.require(bool(rows),'empty_table')
            rowkeys=[tuple(row[k] for k in (*KEYS,'alias','unit')) for row in rows]
            pv.require(len(set(rowkeys))==len(rowkeys),'duplicate_output_rows')
            for row in rows:
                pv.require(row['alias'] in (*ALIASES,'macro'),'alias')
                pv.require(row['candidate'] in (*CANDIDATES,'none'),'candidate')
                pv.require(row['summary'] in ('receiver','segment','none'),'summary')
                pv.require(row['combination'] in ('union','maximum','none'),'combination')
                for key in STAT_KEYS:
                    if row[key]!='':pv.require(math.isfinite(float(row[key])),'finite_csv')
                pv.require(int(row['states_total'])==int(row['states_assessable'])+int(row['states_unavailable']),'csv_counts')
        if not name.endswith('.svg'):
            text=safe(path).read_text()
            for forbidden in (*DEVELOPMENT,'/Users/','/private/','target_index','event_id','carrier_xy','candidate_xy','defender_xy','token='):
                if forbidden in text:raise ValueError('publication_content')
    if status=='valid':
        pv.require(set(files)==set(FINAL_FILES),'complete_outputs')
        q=load(OUT/'qc.json');pv.require(q['states_completed']==7227 and q['exception'] is None,'valid_qc')


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
    pv.require(m['protocol']==digest(PROTOCOL) and m['implementation']==code_hashes() and m['environment']==environment(),'manifest_authority')
    pv.require(set(m['outputs'])|set(m['unavailable'])==set(FINAL_FILES),'manifest_membership')
    for p,h in m['authority'].items():pv.require(digest(p)==h,'authority_hash')
    for p,h in m['outputs'].items():pv.require(digest(OUT/p)==h,'output_hash')
    validate_payloads(m['outputs'],m['status']);print('Session 14R publication checks passed: '+m['status'])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=('preflight','verify-production','render-synthetic','prepare','analyze','publication-check'))
    parser.add_argument('--approve-visual',action='store_true');args=parser.parse_args()
    if args.approve_visual and args.command!='render-synthetic':parser.error('visual approval requires render-synthetic')
    routes={'preflight':preflight,'verify-production':verify_production,'render-synthetic':lambda:render_synthetic(args.approve_visual),
            'prepare':prepare,'analyze':analyze,'publication-check':publication_check}
    routes[args.command]()


if __name__=='__main__':main()
