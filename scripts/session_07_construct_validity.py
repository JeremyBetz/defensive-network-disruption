#!/usr/bin/env python3
"""Session 7 diagnostics and independent review checkpoints. No fitting route."""
from __future__ import annotations
import argparse
import csv
import hashlib
import html
import json
import math
import os
import platform
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from defensive_network_disruption.validation.construct_diagnostics import (
    Geometry, FEATURES, COMPONENTS, POPULATION_SHA, feature_matrices, prepare_cuts,
    diagnose, distribution, bin_name, select_cases,
)

START='68617d1f94f54707c9cd8d4547f09f894818cbc3'
PROTOCOL=ROOT/'docs/protocols/phase_07_construct_validity_diagnostics.md'
POPULATION=ROOT/'outputs/receiver_ranking_m0_m1/local/population.jsonl'
MODELS=ROOT/'outputs/reserved_evaluation/final_development_models.json'
MODELS_SHA='0383561e45bcd9f8d84eccc7e9733b2409536f61c39193fa87d08c36c6f6fd65'
DEV=frozenset({'1886347','1899585','1925299','1996435','2006229','2011166','2013725','2015213','2017461'})
ALIASES={m:f'development_{i:02d}' for i,m in enumerate(sorted(DEV),1)}
OUTPUT=ROOT/'outputs/construct_validity_diagnostics'
LOCAL=OUTPUT/'local'
PUBLIC=('diagnostic_authority.json','diagnostic_summary.json','feature_disagreement.csv','contribution_summary.json','m2_role_summary.json','stratified_diagnostics.csv','selected_passage_manifest.json','review_summary.json','qc.json','manifest.json')
IMPLEMENTATION=('scripts/session_07_construct_validity.py','src/defensive_network_disruption/validation/construct_diagnostics.py','tests/test_session7_construct.py')
CANONICAL={'match_id','event_id','candidate_ids','candidate_xy','defender_xy','carrier_xy','target_index','target_outside'}


def git(*args):return subprocess.run(['git',*args],cwd=ROOT,check=True,capture_output=True,text=True).stdout.strip()


def safe(path):
    if any(p.is_symlink() for p in (path,*path.parents)):raise PermissionError('symlink prohibited')
    if not path.resolve().is_relative_to(ROOT.resolve()):raise PermissionError('path outside repository')


def sha(path):
    safe(path);h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()


def jtext(obj):return json.dumps(obj,sort_keys=True,indent=2,allow_nan=False)+'\n'


def atomic(path,text):
    safe(path)
    if not path.is_relative_to(OUTPUT):raise PermissionError('output outside Session 7')
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name('.'+path.name+'.tmp')
    with tmp.open('x',encoding='utf-8',newline='') as f:f.write(text);f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)


def write_json(path,obj):atomic(path,jtext(obj))


def read_json(path):
    safe(path)
    if path!=MODELS and not path.is_relative_to(OUTPUT):raise PermissionError('JSON read outside approved authority/Session 7')
    return json.loads(path.read_text())


def write_csv(path,rows):
    import io
    s=io.StringIO(newline='');w=csv.DictWriter(s,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows);atomic(path,s.getvalue())


def impl_hashes():return {p:sha(ROOT/p) for p in IMPLEMENTATION}


def committed(path):
    rel=str(path.relative_to(ROOT));git('ls-files','--error-unmatch',rel)
    raw=subprocess.run(['git','show','HEAD:'+rel],cwd=ROOT,check=True,capture_output=True).stdout
    if hashlib.sha256(raw).hexdigest()!=sha(path):raise RuntimeError('committed authority differs')
    return git('log','-1','--format=%H','--',rel)


def clean():
    if git('status','--porcelain'):raise RuntimeError('clean committed tree required')


def history():
    git('merge-base','--is-ancestor',START,'HEAD')
    for name in git('ls-tree','-r','--name-only',START).splitlines():
        raw=subprocess.run(['git','show',START+':'+name],cwd=ROOT,check=True,capture_output=True).stdout
        path=ROOT/name;safe(path)
        if name=='docs/research_log.md':
            if not path.read_bytes().startswith(raw):raise RuntimeError('historical log rewritten')
        elif sha(path)!=hashlib.sha256(raw).hexdigest():raise RuntimeError('historical artifact changed')


def authority():
    history();committed(PROTOCOL)
    if sha(MODELS)!=MODELS_SHA:raise RuntimeError('final model identity mismatch')
    models=read_json(MODELS)
    # Version metadata only: importing scipy would unnecessarily expand runtime imports.
    from importlib.metadata import version
    env={'python':platform.python_version(),'platform':platform.platform(),'numpy':np.__version__,'scipy':version('scipy'),'uv_lock_sha256':sha(ROOT/'uv.lock')}
    if models['environment']!=env:raise RuntimeError('governed environment mismatch')
    return models


def ready():
    a=authority();clean()
    for p in IMPLEMENTATION:committed(ROOT/p)
    return a


def log(phase,status):
    path=LOCAL/'access.jsonl';safe(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a') as f:f.write(json.dumps({'phase':phase,'status':status,'operator':'assistant','time':datetime.now(timezone.utc).isoformat(),'protocol_sha256':sha(PROTOCOL),'implementation_sha256':impl_hashes()},sort_keys=True)+'\n')


def marker(phase):
    p=LOCAL/(phase+'.marker.json');safe(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:f.write(jtext({'phase':phase,'implementation_sha256':impl_hashes(),'protocol_sha256':sha(PROTOCOL)}))


def read_population(geometry_only=False):
    safe(POPULATION)
    log('canonical_population','hash-verification-started')
    if sha(POPULATION)!=POPULATION_SHA:raise RuntimeError('canonical population hash mismatch')
    log('canonical_population','projected-read-started')
    records=[];counts=Counter();seen=set()
    with POPULATION.open() as f:
        for ordinal,line in enumerate(f):
            raw=json.loads(line)
            if set(raw)!=CANONICAL or raw['match_id'] not in DEV:raise PermissionError('population field or partition violation')
            ids=raw['candidate_ids']
            if not isinstance(ids,list) or len(ids)!=len(set(ids)) or not all(isinstance(x,str) and x for x in ids):raise ValueError('canonical candidate identity invalid')
            event=(raw['match_id'],raw['event_id'])
            if event in seen:raise ValueError('duplicate canonical event')
            seen.add(event)
            geo=Geometry(tuple(raw['carrier_xy']),tuple(tuple(x) for x in raw['candidate_xy']),tuple(tuple(x) for x in raw['defender_xy']))
            if not len(geo.candidate_xy) or len(ids)!=len(geo.candidate_xy) or not len(geo.defender_xy):raise ValueError('empty canonical geometry')
            for point in (geo.carrier_xy,*geo.candidate_xy,*geo.defender_xy):
                if len(point)!=2 or not all(isinstance(v,(float,int)) and not isinstance(v,bool) and math.isfinite(v) for v in point):raise ValueError('invalid canonical coordinate')
            row={'ordinal':ordinal,'alias':ALIASES[raw['match_id']],'geometry':geo}
            if not geometry_only:
                target=raw['target_index']
                if type(target) is not int or not 0<=target<len(ids) or raw['target_outside'] is not False:raise ValueError('unexpected authoritative target eligibility')
                row['target_index']=target
            records.append(row);counts[row['alias']]+=1
    if len(records)!=7227 or set(counts)!=set(ALIASES.values()):raise ValueError('authoritative population coverage mismatch')
    log('canonical_population','projected-read-completed')
    return records


def preflight():
    authority()
    for path in (POPULATION,LOCAL):safe(path)
    if not POPULATION.is_file():raise RuntimeError('canonical population unavailable; no regeneration allowed')
    if not git('check-ignore','--',str((LOCAL/'probe').relative_to(ROOT))):raise RuntimeError('detailed output storage not ignored')
    if (LOCAL/'failure.json').exists():raise RuntimeError('diagnostic failure preserved; no automatic continuation')
    print('Session 7 preflight passed; no development rows parsed')


def prepare_diagnostics():
    a=ready();marker('prepare');rows=read_population(geometry_only=True)
    groups={alias:[] for alias in ALIASES.values()}
    for row in rows:groups[row['alias']].append(row['geometry'])
    cuts=prepare_cuts(groups)
    result={'schema_version':'1','status':'feature_only_authority','starting_commit':START,'protocol_commit':committed(PROTOCOL),'protocol_sha256':sha(PROTOCOL),'implementation_commit':git('rev-parse','HEAD'),'implementation_sha256':impl_hashes(),'population_sha256':POPULATION_SHA,'model_sha256':MODELS_SHA,'environment':a['environment'],'counts':{k:len(v) for k,v in groups.items()},'total':len(rows),'target_access_in_cutpoints':False,'cuts':cuts}
    validate_public('diagnostic_authority.json',result);write_json(OUTPUT/'diagnostic_authority.json',result)
    print('Feature-only authority prepared; commit before outcome-bearing diagnostics')


def load_cuts():
    p=OUTPUT/'diagnostic_authority.json';committed(p);a=read_json(p)
    validate_public(p.name,a)
    if a['implementation_sha256']!=impl_hashes() or a['protocol_sha256']!=sha(PROTOCOL) or a['population_sha256']!=POPULATION_SHA or a['model_sha256']!=MODELS_SHA:raise RuntimeError('diagnostic authority binding mismatch')
    return a['cuts']


def weighted_rows(rows):
    counts=Counter(r['alias'] for r in rows)
    return [1/len(counts)/counts[r['alias']] for r in rows]


def summarize_role(rows):
    weights=weighted_rows(rows)
    def avg(fn):return float(np.average([fn(r) for r in rows],weights=weights))
    pair_rows=[r for r in rows if r['m2_m1_pairs']['pairs']]
    def pair_avg(fn):return None if not pair_rows else float(np.average([fn(r) for r in pair_rows],weights=weighted_rows(pair_rows)))
    deltas=[r['m2_delta'] for r in rows]
    return {'states':len(rows),'improved':sum(x<0 for x in deltas),'worsened':sum(x>0 for x in deltas),'tied':sum(x==0 for x in deltas),'improved_fraction':avg(lambda r:r['m2_delta']<0),'worsened_fraction':avg(lambda r:r['m2_delta']>0),'top_set_changed_fraction':avg(lambda r:r['models']['m1']['top']!=r['models']['m2']['top']),'unchanged_order_fraction':avg(lambda r:r['m2_m1_pairs']['changed_fraction']==0),'utility_moved_without_order_change_fraction':avg(lambda r:r['m2_m1_pairs']['changed_fraction']==0 and np.max(np.abs((np.array(r['models']['m2']['utility'])-np.mean(r['models']['m2']['utility']))-(np.array(r['models']['m1']['utility'])-np.mean(r['models']['m1']['utility']))))>1e-12),'pair_assessable_states':len(pair_rows),'changed_pair_fraction':pair_avg(lambda r:r['m2_m1_pairs']['changed_fraction'] or 0),'strict_reversal_fraction':pair_avg(lambda r:r['m2_m1_pairs']['strict_reversal']/r['m2_m1_pairs']['pairs'] if r['m2_m1_pairs']['pairs'] else 0),'tie_created_fraction':pair_avg(lambda r:r['m2_m1_pairs']['tie_created']/r['m2_m1_pairs']['pairs'] if r['m2_m1_pairs']['pairs'] else 0),'tie_removed_fraction':pair_avg(lambda r:r['m2_m1_pairs']['tie_removed']/r['m2_m1_pairs']['pairs'] if r['m2_m1_pairs']['pairs'] else 0),'rank_change':distribution(deltas,weights),'absolute_rank_change':distribution([abs(v) for v in deltas],weights)}


def disagreement_row(alias,rows):
    eligible=[r for r in rows if r['eligible_pairs']];discordant=[r for r in rows if r['discordant_pairs']]
    def avg(group,fn):return None if not group else float(np.average([fn(r) for r in group],weights=weighted_rows(group)))
    return {'match_alias':alias,'states':len(rows),'eligible_states':len(eligible),'zero_pair_states':len(rows)-len(eligible),'eligible_pairs':sum(r['eligible_pairs'] for r in rows),'discordant_pairs':sum(r['discordant_pairs'] for r in rows),'discordant_states':len(discordant),'weighted_disagreement':avg(eligible,lambda r:r['disagreement_fraction']),**{field:avg(discordant,lambda r:r['disagreement_order'][field]/r['disagreement_order']['pairs']) for field in ('unchanged','strict_reversal','tie_created','tie_removed')}}


def strata_table(rows,cuts):
    bins={name:['bin_'+str(i) for i in range(1,len(c)+2)] for name,c in cuts.items()};bins['direction']=['forward','approximately_lateral','backward','degenerate']
    cells={}
    for row in rows:
        values=row['features'][row['target_index']]
        labels={name:bin_name(values[i],cuts[name]) for i,name in enumerate(FEATURES)}
        labels['direction']=row['direction'];labels['nonnearest_mass']=bin_name(row['nonnearest_mass'],cuts['nonnearest_mass'])
        for feature,b in labels.items():cells.setdefault((feature,b,row['alias']),[]).append(row)
    table=[]
    for feature in bins:
        for b in bins[feature]:
            sub=[]
            for alias in ALIASES.values():
                group=cells.get((feature,b,alias),[]);sub.extend(group)
                table.append(stratum_row(feature,b,alias,group))
            table.append(stratum_row(feature,b,'match_macro',sub))
    return table


def stratum_row(feature,b,alias,group):
    weights=weighted_rows(group) if group else []
    return {'feature':feature,'bin':b,'match_alias':alias,'states':len(group),'represented_matches':len({r['alias'] for r in group}),'m1_mean_rank_change':None if not group else float(np.average([r['m1_delta'] for r in group],weights=weights)),'m2_mean_rank_change':None if not group else float(np.average([r['m2_delta'] for r in group],weights=weights)),**{name+'_'+sign:sum((r[name+'_delta']<0 if sign=='improved' else r[name+'_delta']>0 if sign=='worsened' else r[name+'_delta']==0) for r in group) for name in ('m1','m2') for sign in ('improved','worsened','tied')}}


def summarize():
    a=ready();cuts=load_cuts();marker('summarize');raw=read_population()
    rows=[diagnose(r['geometry'],r['target_index'],a['models'],r['ordinal'],r['alias']) for r in raw]
    localtext=''.join(json.dumps(r,sort_keys=True,allow_nan=False,separators=(',',':'))+'\n' for r in rows)
    atomic(LOCAL/'diagnostics.jsonl',localtext)
    groups={alias:[r for r in rows if r['alias']==alias] for alias in ALIASES.values()}
    weights=weighted_rows(rows)
    summary={'schema_version':'1','status':'diagnostics_closed','interpretation':'in_sample_development_diagnostics','states':len(rows),'match_count':len(groups),'counts':{k:len(v) for k,v in groups.items()},'m1_target_rank_change':distribution([r['m1_delta'] for r in rows],weights),'m2_target_rank_change':distribution([r['m2_delta'] for r in rows],weights),'primary_classification':None,'secondary_classification':None,'diagnostic_authority_sha256':sha(OUTPUT/'diagnostic_authority.json'),'detail_sha256':sha(LOCAL/'diagnostics.jsonl')}
    contributions=[]
    for model in ('m0','m1','m2'):
        for column,component in enumerate(COMPONENTS):
            if column>=({'m0':1,'m1':3,'m2':4}[model]):continue
            for kind in ('components','centered_components','within_choice_range'):
                vals=[];ws=[]
                for row,weight in zip(rows,weights):
                    if kind=='within_choice_range':vals.append(float(np.ptp(np.asarray(row['models'][model]['components'])[:,column])));ws.append(weight)
                    else:
                        x=np.asarray(row['models'][model][kind])[:,column];vals.extend(x);ws.extend([weight/len(x)]*len(x))
                contributions.append({'model':model,'component':component,'kind':kind,'distribution':distribution(vals,ws)})
    bookkeeping=[]
    for comparison in ('m1_m0','m2_m1'):
        for kind in ('shared','added','centered_shared','centered_added'):
            vals=[];ws=[]
            for row,weight in zip(rows,weights):
                x=row['bookkeeping'][comparison][kind];vals.extend(x);ws.extend([weight/len(x)]*len(x))
            bookkeeping.append({'comparison':comparison,'kind':kind,'distribution':distribution(vals,ws)})
    outputs={'diagnostic_summary.json':summary,'contribution_summary.json':{'schema_version':'1','components':contributions,'between_model_bookkeeping':bookkeeping},'m2_role_summary.json':{'schema_version':'1','matches':{k:summarize_role(v) for k,v in groups.items()},'match_macro':summarize_role(rows)},'qc.json':{'schema_version':'1','population_sha256':POPULATION_SHA,'model_sha256':MODELS_SHA,'implementation_sha256':impl_hashes(),'states':len(rows),'in_sample':True,'raw_provider_access':False,'reserved_detail_access':False,'withheld_access':False,'fitting':False,'max_utility_reconstruction_residual':max(r['max_reconstruction_residual'] for r in rows),'detail_sha256':sha(LOCAL/'diagnostics.jsonl')}}
    for name,obj in outputs.items():validate_public(name,obj);write_json(OUTPUT/name,obj)
    write_csv(OUTPUT/'feature_disagreement.csv',[disagreement_row(k,v) for k,v in groups.items()]+[disagreement_row('match_macro',rows)])
    write_csv(OUTPUT/'stratified_diagnostics.csv',strata_table(rows,cuts))
    hashes={n:sha(OUTPUT/n) for n in ('diagnostic_summary.json','contribution_summary.json','m2_role_summary.json','qc.json','feature_disagreement.csv','stratified_diagnostics.csv')}
    write_json(LOCAL/'aggregate_closure.json',{'output_sha256':hashes,'detail_sha256':sha(LOCAL/'diagnostics.jsonl')})
    publication_check()
    print('Development diagnostic aggregates closed; classifications pending human review')


def closed_rows():
    closure=read_json(LOCAL/'aggregate_closure.json')
    for name,digest in closure['output_sha256'].items():
        if sha(OUTPUT/name)!=digest:raise RuntimeError('aggregate closure changed')
    if sha(LOCAL/'diagnostics.jsonl')!=closure['detail_sha256']:raise RuntimeError('diagnostic detail changed')
    return [json.loads(line) for line in (LOCAL/'diagnostics.jsonl').read_text().splitlines()]


def select_passages():
    ready();load_cuts();marker('selection');rows=closed_rows();selected,counts=select_cases(rows)
    write_json(LOCAL/'selection.json',selected)
    manifest={'schema_version':'1','status':'selected_before_rendering','case_ids':[r['case_id'] for r in selected],'category_counts':counts,'shortfalls':{k:3-v for k,v in counts.items()},'selected_count':len(selected),'maximum_per_match':2,'selection_sha256':sha(LOCAL/'selection.json'),'detail_sha256':sha(LOCAL/'diagnostics.jsonl'),'population_sha256':POPULATION_SHA,'model_sha256':MODELS_SHA,'implementation_sha256':impl_hashes(),'diagnostic_authority_sha256':sha(OUTPUT/'diagnostic_authority.json')}
    validate_public('selected_passage_manifest.json',manifest);write_json(OUTPUT/'selected_passage_manifest.json',manifest)
    print('Selection authority ready; commit before rendering')


def selection_authority():
    p=OUTPUT/'selected_passage_manifest.json';committed(p);m=read_json(p)
    if m['implementation_sha256']!=impl_hashes() or m['selection_sha256']!=sha(LOCAL/'selection.json') or m['detail_sha256']!=sha(LOCAL/'diagnostics.jsonl') or m['diagnostic_authority_sha256']!=sha(OUTPUT/'diagnostic_authority.json'):raise RuntimeError('selection authority changed')
    return read_json(LOCAL/'selection.json')


def svg_geometry(geometry,case_id):
    points=(geometry.carrier_xy,*geometry.candidate_xy,*geometry.defender_xy)
    xmin=min(p[0] for p in points)-5;xmax=max(p[0] for p in points)+5
    ymin=min(p[1] for p in points)-5;ymax=max(p[1] for p in points)+5
    scale=min(850/(xmax-xmin),760/(ymax-ymin))
    width=(xmax-xmin)*scale;height=(ymax-ymin)*scale
    ox=75+(850-width)/2;oy=85+(760-height)/2
    def xy(p):return ox+(p[0]-xmin)*scale,oy+(ymax-p[1])*scale
    elements=['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="1000" viewBox="0 0 1000 1000">','<rect width="1000" height="1000" fill="white"/>',f'<text x="50" y="35" font-family="sans-serif" font-size="22">{html.escape(case_id)} · geometry-only decision state</text>','<text x="50" y="60" font-family="sans-serif" font-size="14">Carrier: orange · candidates: blue · defenders: grey · no temporal context</text>']
    ax,ay=xy(geometry.carrier_xy)
    for p in geometry.candidate_xy:
        x,y=xy(p);elements.append(f'<line x1="{ax:.5f}" y1="{ay:.5f}" x2="{x:.5f}" y2="{y:.5f}" stroke="#cbd5e1" stroke-width="1"/>')
    occupied=[]
    point_boxes=[(xy(p)[0]-6,xy(p)[1]-6,xy(p)[0]+6,xy(p)[1]+6) for p in points]
    def intersects(a,b):return a[0]<b[2] and a[2]>b[0] and a[1]<b[3] and a[3]>b[1]
    def label_position(x,y,label):
        width=7*len(label)
        for offset in (10,24,38,52,66):
            for dx,dy in ((offset,-offset),(offset,offset),(-width-offset,-offset),(-width-offset,offset)):
                box=(x+dx,y+dy-12,x+dx+width,y+dy+3)
                if 25<box[0] and box[2]<975 and 75<box[1] and box[3]<865 and not any(intersects(box,b) for b in occupied+point_boxes):
                    occupied.append(box);return x+dx,y+dy
        occupied.append((x+10,y-22,x+10+width,y-7));return x+10,y-10
    for category,ps,color in (('D',geometry.defender_xy,'#64748b'),('C',geometry.candidate_xy,'#2563eb'),('carrier',(geometry.carrier_xy,),'#c2410c')):
        for i,p in enumerate(ps,1):
            x,y=xy(p);label='Carrier' if category=='carrier' else f'{category}{i:02d}'
            lx,ly=label_position(x,y,label)
            if abs(lx-x)>20 or abs(ly-y)>20:elements.append(f'<line x1="{x:.5f}" y1="{y:.5f}" x2="{lx:.5f}" y2="{ly-4:.5f}" stroke="#94a3b8" stroke-width=".7"/>')
            elements.extend([f'<circle cx="{x:.5f}" cy="{y:.5f}" r="5" fill="{color}"/>',f'<text x="{lx:.5f}" y="{ly:.5f}" font-family="sans-serif" font-size="12" fill="#0f172a">{label}</text>'])
    bar=5*scale
    elements.extend([f'<path d="M 70 900 h {bar:.5f}" stroke="#0f172a" stroke-width="3"/>','<text x="70" y="925" font-family="sans-serif" font-size="14">5 m</text>','<path d="M 750 900 h 150 m -12 -6 l 12 6 l -12 6" fill="none" stroke="#0f172a" stroke-width="2"/>','<text x="750" y="925" font-family="sans-serif" font-size="14">Attacking direction (+x)</text>','<text x="50" y="975" font-family="sans-serif" font-size="12">Equal aspect ratio; extent is a display window, not a pitch boundary. Actual ball position is not shown.</text>','</svg>'])
    return '\n'.join(elements)+'\n'


def response_template(selected,raw):
    byordinal={r['ordinal']:r for r in raw}
    return {'reviewer':{'experience':None,'prior_familiarity':None},'cases':[{'case_id':c['case_id'],'candidate_accessibility':{f'C{i+1:02d}':None for i in range(len(byordinal[c['ordinal']]['geometry'].candidate_xy))},'receiver_pressure':None,'corridor_constraints':None,'missing_context':None,'confidence':None,'practitioner_meaningful':None,'notes':''} for c in selected]}


def bind_manifest(status):
    hashes={name:sha(OUTPUT/name) for name in PUBLIC if name!='manifest.json' and (OUTPUT/name).exists()}
    result={'schema_version':'1','status':status,'starting_commit':START,'protocol_commit':committed(PROTOCOL),'protocol_sha256':sha(PROTOCOL),'implementation_sha256':impl_hashes(),'population_sha256':POPULATION_SHA,'model_sha256':MODELS_SHA,'output_sha256':hashes,'access_ledger_sha256':sha(LOCAL/'access.jsonl'),'review_pending':status!='complete'}
    validate_public('manifest.json',result);write_json(OUTPUT/'manifest.json',result)


def render_passages():
    ready();load_cuts();selected=selection_authority();marker('render_a');closed_rows();raw=read_population(geometry_only=True);byordinal={r['ordinal']:r for r in raw}
    hashes={}
    for case in selected:
        p=LOCAL/'stage_a'/(case['case_id']+'.svg');atomic(p,svg_geometry(byordinal[case['ordinal']]['geometry'],case['case_id']));hashes[case['case_id']]=sha(p)
    form=response_template(selected,raw);write_json(LOCAL/'stage_a_responses.json',form);write_json(LOCAL/'stage_a_template.json',form)
    intro='''# Independent review — Stage A\n\nReview these geometry-only decision states before requesting any target/model information. No selection category is disclosed. These are purposively selected development examples, not a representative sample. Study-level results may already be familiar; record that familiarity.\n\nOpen each SVG below. In `../stage_a_responses.json`, replace every null with your own assessment. Candidate ratings: `high`, `intermediate`, `low`, or `not_assessable`. Confidence: `low`, `medium`, `high`. Practitioner meaningfulness: `yes`, `no`, `uncertain`. Text fields may explicitly say “not assessable.” Leave notes empty if unnecessary. Record your experience and prior familiarity. Do not infer intention, body orientation, tactical instruction, actual ball location or temporal motion.\n\nThe assistant must not fill these judgments. Return the completed file through this task. All cases must be recorded before Stage B can be revealed. Your original Stage A answers will remain locked even if the reveal changes your interpretation.\n\n'''
    intro+='\n'.join(f'- [{c["case_id"]}]({c["case_id"]}.svg)' for c in selected)+'\n'
    atomic(LOCAL/'stage_a/README.md',intro)
    write_json(LOCAL/'packet_hashes.json',{'stage_a':hashes,'template_sha256':sha(LOCAL/'stage_a_template.json')})
    review={'schema_version':'1','status':'AWAITING INDEPENDENT REVIEW','selected_cases':len(selected),'stage_a_locked':False,'stage_b_revealed':False,'stage_b_locked':False,'primary_classification':None,'secondary_classification':None,'packet_hashes_sha256':sha(LOCAL/'packet_hashes.json')}
    validate_public('review_summary.json',review);write_json(OUTPUT/'review_summary.json',review)
    log('review_packet','stage_a_ready');bind_manifest('awaiting_independent_review');publication_check()
    print('Stage A packet ready. AWAITING INDEPENDENT REVIEW. No Stage B reveal or classification.')


def verify_packet():
    review=read_json(OUTPUT/'review_summary.json')
    if sha(LOCAL/'packet_hashes.json')!=review['packet_hashes_sha256']:raise RuntimeError('packet identity changed')
    hashes=read_json(LOCAL/'packet_hashes.json')
    for case_id,digest in hashes['stage_a'].items():
        if sha(LOCAL/'stage_a'/(case_id+'.svg'))!=digest:raise RuntimeError('blinded diagram changed')
    if sha(LOCAL/'stage_a_template.json')!=hashes['template_sha256']:raise RuntimeError('Stage A template changed')
    if 'stage_b' in hashes:
        for name,digest in hashes['stage_b'].items():
            if sha(LOCAL/'stage_b'/name)!=digest:raise RuntimeError('revealed material changed')
        if sha(LOCAL/'stage_b_template.json')!=hashes['stage_b_template_sha256']:raise RuntimeError('Stage B template changed')


def validate_review(stage,obj,template):
    if not isinstance(obj,dict) or set(obj)!={'reviewer','cases'} or not isinstance(obj['reviewer'],dict) or set(obj['reviewer'])!={'experience','prior_familiarity'}:raise ValueError('review schema invalid')
    if any(not isinstance(x,str) or not x.strip() for x in obj['reviewer'].values()):raise ValueError('human reviewer metadata required')
    expected={c['case_id']:c for c in template['cases']}
    if not isinstance(obj['cases'],list) or len(obj['cases'])!=len(expected) or len({c.get('case_id') for c in obj['cases']})!=len(expected) or {c.get('case_id') for c in obj['cases']}!=set(expected):raise ValueError('complete unique reviewed cases required')
    for case in obj['cases']:
        ref=expected[case['case_id']]
        if set(case)!=set(ref):raise ValueError('review fields differ from frozen template')
        if stage=='A':
            ratings=case['candidate_accessibility']
            if not isinstance(ratings,dict) or set(ratings)!=set(ref['candidate_accessibility']) or any(v not in {'high','intermediate','low','not_assessable'} for v in ratings.values()):raise ValueError('human candidate ratings incomplete')
            if case['confidence'] not in {'low','medium','high'} or case['practitioner_meaningful'] not in {'yes','no','uncertain'}:raise ValueError('human categories incomplete')
            textfields=('receiver_pressure','corridor_constraints','missing_context')
            if not isinstance(case['notes'],str):raise ValueError('notes must be text')
        else:
            textfields=tuple('q'+str(i) for i in range(1,8))
            if case['q8'] not in {'accessibility_consistent','receiver_selection_only','ambiguous','model_failure'}:raise ValueError('case interpretation missing')
        if any(not isinstance(case[k],str) or not case[k].strip() for k in textfields):raise ValueError('human text judgments incomplete')


def locked_review(stage):
    p=LOCAL/('stage_'+stage.lower()+'_locked.json');receipt=read_json(LOCAL/('stage_'+stage.lower()+'_lock_receipt.json'))
    if sha(p)!=receipt['locked_sha256'] or sha(LOCAL/('stage_'+stage.lower()+'_returned.json'))!=receipt['returned_sha256']:raise RuntimeError('locked human review changed')
    obj=read_json(p);validate_review(stage,obj,read_json(LOCAL/('stage_'+stage.lower()+'_template.json')))
    return obj


def record_review(stage,input_path):
    ready();selection_authority();expected=LOCAL/('stage_'+stage.lower()+'_responses.json')
    if input_path.absolute()!=expected.absolute():raise PermissionError('only the fixed local response path is permitted')
    safe(input_path)
    if stage=='B':locked_review('A')
    verify_packet()
    template=read_json(LOCAL/('stage_'+stage.lower()+'_template.json'));obj=read_json(input_path);validate_review(stage,obj,template)
    marker('record_'+stage.lower())
    returned=LOCAL/('stage_'+stage.lower()+'_returned.json');atomic(returned,input_path.read_text())
    dest=LOCAL/('stage_'+stage.lower()+'_locked.json');write_json(dest,obj)
    write_json(LOCAL/('stage_'+stage.lower()+'_lock_receipt.json'),{'returned_sha256':sha(returned),'locked_sha256':sha(dest)})
    review=read_json(OUTPUT/'review_summary.json');review['stage_'+stage.lower()+'_locked']=True;review['status']='STAGE A LOCKED — REVEAL PENDING' if stage=='A' else 'HUMAN REVIEW RECORDED — INTERPRETATION PENDING'
    write_json(OUTPUT/'review_summary.json',review);log('human_review',stage+'_locked');bind_manifest('review_in_progress');publication_check()
    print('Human review locked; commit checkpoint before the next command')


def reveal_passages():
    ready();committed(OUTPUT/'review_summary.json');verify_packet();locked_review('A');selected=selection_authority();rows={r['ordinal']:r for r in closed_rows()};marker('reveal_b')
    template={'reviewer':{'experience':None,'prior_familiarity':None},'cases':[]}
    questions=['What geometric relationship is M1 using?','Do receiver pressure and corridor obstruction agree or disagree?','Does the model-preferred candidate appear spatially accessible?','Does the provider target appear plausibly constrained or available?','Does M2 capture additional defender structure in a visually interpretable way?','What obvious football factors are absent?','Would a practitioner recognize this distinction as meaningful?','Case interpretation: accessibility_consistent, receiver_selection_only, ambiguous, or model_failure.']
    for case in selected:
        row=rows[case['ordinal']];title=case['case_id'];text=f'# {title} — Stage B\n\n![Geometry](../stage_a/{title}.svg)\n\nProvider target: C{row["target_index"]+1:02d}. Components are fitted model quantities, not causal contributions.\n\n'
        text+='| Candidate | M0 rank | M1 rank | M2 rank | M1 attacking | M1 receiver | M1 segment | M2 attacking | M2 receiver | M2 segment | M2 attenuation | Shared coefficient shift M2−M1 |\n| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |\n'
        for i in range(len(row['features'])):
            numbers=[row['models'][m]['ranks'][i] for m in ('m0','m1','m2')]+row['models']['m1']['centered_components'][i][:3]+row['models']['m2']['centered_components'][i]+[row['bookkeeping']['m2_m1']['centered_shared'][i]]
            text+=f'| C{i+1:02d} | '+' | '.join(f'{v:.5f}' for v in numbers)+' |\n'
        text+='\nAll component values in this table are centered within the choice set. Tied top candidates remain tied.\n\n'+'\n'.join(f'{i}. {q}' for i,q in enumerate(questions,1))+'\n'
        atomic(LOCAL/'stage_b'/(title+'.md'),text);template['cases'].append({'case_id':title,**{'q'+str(i):None for i in range(1,9)}})
    write_json(LOCAL/'stage_b_responses.json',template);write_json(LOCAL/'stage_b_template.json',template)
    atomic(LOCAL/'stage_b/README.md','# Stage B — revealed review\n\nComplete ../stage_b_responses.json after reviewing every case. Original Stage A responses remain locked.\n\n'+'\n'.join(f'- [{c["case_id"]}]({c["case_id"]}.md)' for c in selected)+'\n')
    hashes=read_json(LOCAL/'packet_hashes.json');hashes['stage_b']={p.name:sha(p) for p in (LOCAL/'stage_b').iterdir() if p.is_file()};hashes['stage_b_template_sha256']=sha(LOCAL/'stage_b_template.json');write_json(LOCAL/'packet_hashes.json',hashes)
    review=read_json(OUTPUT/'review_summary.json');review['packet_hashes_sha256']=sha(LOCAL/'packet_hashes.json');review['stage_b_revealed']=True;review['status']='AWAITING STAGE B HUMAN REVIEW';write_json(OUTPUT/'review_summary.json',review)
    log('human_review','stage_b_revealed');bind_manifest('review_in_progress');publication_check()
    print('Stage B revealed; human judgments pending')


def close_review():
    ready();a=locked_review('A');b=locked_review('B');committed(OUTPUT/'review_summary.json')
    p=LOCAL/'interpretation.json';interpretation=read_json(p)
    if set(interpretation)!={'primary','secondary','rationale','alternative_explanations','next_question','human_reviewed'} or interpretation['primary'] not in {'A','B','C','D'} or interpretation['secondary'] not in {'1','2','3','4'} or interpretation['human_reviewed'] is not True:raise ValueError('reviewed interpretation required')
    if any(not isinstance(interpretation[k],str) or not interpretation[k].strip() for k in ('rationale','alternative_explanations','next_question')):raise ValueError('interpretation evidence required')
    marker('close_review')
    review=read_json(OUTPUT/'review_summary.json');review.update(status='COMPLETE',primary_classification=interpretation['primary'],secondary_classification=interpretation['secondary'])
    review['stage_b_outcomes']=dict(Counter(c['q8'] for c in b['cases']));review['interpretation']=interpretation
    validate_public('review_summary.json',review);write_json(OUTPUT/'review_summary.json',review);log('human_review','complete');bind_manifest('complete');publication_check()
    report=ROOT/'docs/session_07_construct_validity_diagnostic_report.md';safe(report)
    if report.exists():raise RuntimeError('final report already exists')
    report.write_text('# Session 7 — Construct-validity diagnostic report\n\nPrimary: '+interpretation['primary']+'. Secondary M2: '+interpretation['secondary']+'.\n\n'+interpretation['rationale']+'\n\n## Alternative explanations\n\n'+interpretation['alternative_explanations']+'\n\nAccessibility remains a proxy; suppression, causal, best-pass, player-value and network-disruption claims remain unsupported. Development diagnostics are in-sample. Independent human judgments are purposive case evidence, not prevalence estimates.\n\n## One future question, not executed\n\n'+interpretation['next_question']+'\n\nManifest SHA-256: `'+sha(OUTPUT/'manifest.json')+'`. Full aggregate evidence is under outputs/construct_validity_diagnostics/. Stop after Session 7.\n')


SCHEMAS={
'diagnostic_authority.json':{'schema_version','status','starting_commit','protocol_commit','protocol_sha256','implementation_commit','implementation_sha256','population_sha256','model_sha256','environment','counts','total','target_access_in_cutpoints','cuts'},
'diagnostic_summary.json':{'schema_version','status','interpretation','states','match_count','counts','m1_target_rank_change','m2_target_rank_change','primary_classification','secondary_classification','diagnostic_authority_sha256','detail_sha256'},
'contribution_summary.json':{'schema_version','components','between_model_bookkeeping'},
'm2_role_summary.json':{'schema_version','matches','match_macro'},
'qc.json':{'schema_version','population_sha256','model_sha256','implementation_sha256','states','in_sample','raw_provider_access','reserved_detail_access','withheld_access','fitting','max_utility_reconstruction_residual','detail_sha256'},
'selected_passage_manifest.json':{'schema_version','status','case_ids','category_counts','shortfalls','selected_count','maximum_per_match','selection_sha256','detail_sha256','population_sha256','model_sha256','implementation_sha256','diagnostic_authority_sha256'},
'review_summary.json':{'schema_version','status','selected_cases','stage_a_locked','stage_b_revealed','stage_b_locked','primary_classification','secondary_classification','packet_hashes_sha256'},
'manifest.json':{'schema_version','status','starting_commit','protocol_commit','protocol_sha256','implementation_sha256','population_sha256','model_sha256','output_sha256','access_ledger_sha256','review_pending'},
}


def validate_distribution(obj):
    if set(obj)!={'count','mean','minimum','maximum','quantiles'} or type(obj['count']) is not int or obj['count']<0:raise ValueError('distribution schema invalid')
    if obj['count']==0:
        if any(obj[k] is not None for k in ('mean','minimum','maximum','quantiles')):raise ValueError('empty distribution must be missing')
    elif set(obj['quantiles'])!={'q05','q25','q50','q75','q95'}:raise ValueError('quantile schema invalid')


def validate_public(name,obj):
    expected=SCHEMAS[name]
    if name=='review_summary.json' and obj.get('status')=='COMPLETE':expected=expected|{'stage_b_outcomes','interpretation'}
    if set(obj)!=expected:raise ValueError('unexpected public schema fields')
    text=jtext(obj)
    prohibited=('"match_id"','"event_id"','"candidate_ids"','"candidate_xy"','"defender_xy"','"carrier_xy"','"target_index"','"ordinal"','"tie_key"','"utility"','"timestamp"','/Users/','DO_NOT_RETAIN')
    if any(x in text for x in prohibited):raise ValueError('restricted public content')
    if name=='diagnostic_authority.json':
        if set(obj['cuts'])!=set(FEATURES)|{'nonnearest_mass'} or obj['target_access_in_cutpoints'] is not False:raise ValueError('feature-only authority schema')
        for values in obj['cuts'].values():
            if values!=sorted(set(values)) or len(values)>3 or not all(math.isfinite(v) for v in values):raise ValueError('cutpoint schema')
    if 'counts' in obj:
        if set(obj['counts'])!=set(ALIASES.values()) or any(type(n) is not int or n<1 for n in obj['counts'].values()):raise ValueError('alias/count schema')
    if name=='selected_passage_manifest.json':
        if obj['selected_count']!=len(obj['case_ids']) or len(set(obj['case_ids']))!=len(obj['case_ids']) or sum(obj['category_counts'].values())!=obj['selected_count'] or any(x>3 for x in obj['category_counts'].values()):raise ValueError('case selection schema')
    if name=='contribution_summary.json':
        for item in obj['components']:
            if set(item)!={'model','component','kind','distribution'}:raise ValueError('component schema invalid')
            validate_distribution(item['distribution'])
        for item in obj['between_model_bookkeeping']:
            if set(item)!={'comparison','kind','distribution'}:raise ValueError('bookkeeping schema invalid')
            validate_distribution(item['distribution'])
    if name=='diagnostic_summary.json':
        validate_distribution(obj['m1_target_rank_change']);validate_distribution(obj['m2_target_rank_change'])
        if obj['states']!=sum(obj['counts'].values()) or obj['primary_classification'] is not None or obj['secondary_classification'] is not None:raise ValueError('diagnostic state schema invalid')
    if name=='qc.json' and any(obj[k] is not False for k in ('raw_provider_access','reserved_detail_access','withheld_access','fitting')):raise ValueError('prohibited route used')
    if name=='review_summary.json' and obj['stage_b_revealed'] and not obj['stage_a_locked']:raise ValueError('unblinding without review')


def publication_check():
    authority()
    for name in PUBLIC:
        p=OUTPUT/name
        if not p.exists():continue
        if name.endswith('.json'):validate_public(name,read_json(p))
        else:
            if b'\r' in p.read_bytes():raise ValueError('CSV must use LF')
            with p.open() as f:
                rows=list(csv.DictReader(f))
            for row in rows:
                if row['match_alias'] not in {*ALIASES.values(),'match_macro'}:raise ValueError('CSV alias outside authority')
                for field,value in row.items():
                    if field not in {'match_alias','feature','bin'} and value and not math.isfinite(float(value)):raise ValueError('CSV numeric field invalid')
    if (LOCAL/'aggregate_closure.json').exists():closed_rows()
    if (OUTPUT/'manifest.json').exists():
        m=read_json(OUTPUT/'manifest.json')
        for name,digest in m['output_sha256'].items():
            if name not in PUBLIC or name=='manifest.json' or sha(OUTPUT/name)!=digest:raise ValueError('manifest output binding mismatch')
    print('Session 7 publication checks passed')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=('preflight','prepare-diagnostics','summarize','select-passages','render-passages','record-review','reveal-passages','close-review','publication-check'));parser.add_argument('--stage',choices=('A','B'));parser.add_argument('--input',type=Path)
    args=parser.parse_args()
    if (LOCAL/'failure.json').exists() and args.command!='publication-check':raise SystemExit('Preserved diagnostic failure; no automatic rerun')
    try:
        if args.command=='record-review':
            if not args.stage or args.input is None:raise ValueError('stage and fixed input path required')
            record_review(args.stage,args.input)
        else:globals()[args.command.replace('-','_')]()
    except Exception as exc:
        # Missing/incomplete human inputs do not invalidate scientific execution.
        if args.command in {'summarize','select-passages','render-passages'} and not isinstance(exc,FileExistsError):
            write_json(LOCAL/'failure.json',{'command':args.command,'category':type(exc).__name__,'implementation_sha256':impl_hashes()})
        raise SystemExit('Session 7 stopped: '+type(exc).__name__) from None


if __name__=='__main__':main()
