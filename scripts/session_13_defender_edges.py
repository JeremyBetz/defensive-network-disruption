#!/usr/bin/env python3
"""Session 13 governed, target-free defender-edge structural analysis."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import platform
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from defensive_network_disruption.networks.options import OptionState,FrozenOptionModel,evaluate_options
from defensive_network_disruption.networks.defender_edges import map_defender_edges,summarize_edge_involvement
from defensive_network_disruption.visualization.defender_edges import synthetic_defender_edge_svg
from defensive_network_disruption.validation.construct_diagnostics import distribution

START='b29ef29430e620ae88cb51df3353a2596e0a5d69'
POP_SHA='cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d'
MODEL_SHA='0383561e45bcd9f8d84eccc7e9733b2409536f61c39193fa87d08c36c6f6fd65'
DEV=('1886347','1899585','1925299','1996435','2006229','2011166','2013725','2015213','2017461')
ALIASES=tuple(f'development_{i:02d}' for i in range(1,10));COUNTS=(885,801,952,877,861,629,764,734,724)
POP=Path('outputs/receiver_ranking_m0_m1/local/population.jsonl');MODEL=Path('outputs/reserved_evaluation/final_development_models.json')
PROTOCOL=Path('docs/protocols/phase_13_defender_edge_influence.md');OUT=Path('outputs/defender_edge_influence');LOCAL=OUT/'local'
CONTRACT=OUT/'software_contract.json';AUTH=OUT/'implementation_authority.json';PREP=OUT/'population_authority.json'
IMPL=('scripts/session_13_defender_edges.py','src/defensive_network_disruption/networks/defender_edges.py','src/defensive_network_disruption/visualization/defender_edges.py','tests/test_session13_defender_edges.py')
INHERITED=('src/defensive_network_disruption/networks/options.py','src/defensive_network_disruption/validation/ranking_features.py','src/defensive_network_disruption/geometry/segment.py')
CANONICAL={'match_id','event_id','carrier_xy','candidate_ids','candidate_xy','defender_xy','target_index','target_outside'}
RESULTS=('relation_summary.json','role_overlap.csv','multi_edge_summary.csv','redundancy_summary.csv','qc.json')

def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT).decode().strip()
def safe(path):
    p=ROOT/path
    if any(x.is_symlink() for x in (p,*p.parents)) or not p.resolve().is_relative_to(ROOT.resolve()):raise PermissionError('unsafe_path')
    return p
def digest(path):
    h=hashlib.sha256()
    with safe(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def load(path):return json.loads(safe(path).read_text(),parse_constant=lambda x:(_ for _ in()).throw(ValueError('nonfinite_json')))
def encoded(x):return json.dumps(x,sort_keys=True,indent=2,allow_nan=False)+'\n'
def atomic(path,text):
    if not Path(path).is_relative_to(OUT):raise PermissionError('output_namespace_required')
    dest=safe(path);dest.parent.mkdir(parents=True,exist_ok=True);tmp=dest.with_name('.'+dest.name+'.tmp')
    with tmp.open('x') as f:f.write(text)
    tmp.replace(dest)
def committed(path):
    old=subprocess.check_output(['git','show','HEAD:'+str(path)],cwd=ROOT)
    if hashlib.sha256(old).hexdigest()!=digest(path):raise ValueError('uncommitted_authority')
def ledger(stage,status):
    p=safe(LOCAL/'access.jsonl');p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('a') as f:f.write(json.dumps({'time':datetime.now(timezone.utc).isoformat(),'stage':stage,'status':status,'head':git('rev-parse','HEAD')})+'\n')
def environment():
    from importlib.metadata import version
    return {'python':platform.python_version(),'platform':platform.platform(),'numpy':np.__version__,'scipy':version('scipy'),'uv_lock_sha256':digest('uv.lock')}
def code_hashes():return {p:digest(p) for p in IMPL}
def inherited_hashes():return {p:digest(p) for p in INHERITED}
def historical():
    git('merge-base','--is-ancestor',START,'HEAD')
    old=set(git('ls-tree','-r','--name-only',START).splitlines());changed=set(git('diff','--name-only',START).splitlines())
    for name in old&changed:
        if name not in {'docs/research_log.md','references/library_review.md'}:raise ValueError('historical_change:'+name)
        before=subprocess.check_output(['git','show',START+':'+name],cwd=ROOT)
        if not safe(name).read_bytes().startswith(before):raise ValueError('append_only_violation')
def authorities(require_clean=False,require_prep=False):
    historical()
    if require_clean and git('status','--porcelain'):raise ValueError('clean_commit_required')
    for p in (PROTOCOL,CONTRACT,AUTH):committed(p)
    auth=load(AUTH)
    if auth['start']!=START or auth['protocol_sha256']!=digest(PROTOCOL) or auth['contract_sha256']!=digest(CONTRACT):raise ValueError('authority_binding')
    if auth['implementation_sha256']!=code_hashes() or auth['inherited_sha256']!=inherited_hashes() or auth['environment']!=environment():raise ValueError('implementation_authority')
    if digest(MODEL)!=MODEL_SHA:raise ValueError('model_hash')
    if require_prep:
        committed(PREP);prep=load(PREP)
        if prep['population_sha256']!=POP_SHA or prep['prepared_sha256']!=digest(LOCAL/'prepared.json'):raise ValueError('population_authority')
    return auth
def preflight():
    if not safe(POP).is_file() or digest(POP)!=POP_SHA:raise ValueError('population_hash')
    if not git('check-ignore','--',str(LOCAL/'probe')):raise ValueError('local_not_ignored')
    authorities();print('Session 13 preflight passed; population not parsed')
def project(raw):
    if set(raw)!=CANONICAL or raw['match_id'] not in DEV:raise PermissionError('population_contract')
    if not isinstance(raw['event_id'],str) or not raw['event_id'] or raw['event_id'].strip()!=raw['event_id']:raise ValueError('event_identity')
    state=OptionState(raw['carrier_xy'],tuple(raw['candidate_ids']),tuple(map(tuple,raw['candidate_xy'])),tuple(map(tuple,raw['defender_xy'])))
    return ALIASES[DEV.index(raw['match_id'])],raw['event_id'],state
def prepare():
    authorities(require_clean=True)
    if safe(PREP).exists() or safe(LOCAL/'prepared.json').exists():raise FileExistsError('preparation_exists')
    ledger('prepare','started');counts=Counter();seen=set();rows=[]
    if digest(POP)!=POP_SHA:raise ValueError('population_hash')
    with safe(POP).open() as f:
        for line in f:
            alias,event,state=project(json.loads(line))
            if (alias,event) in seen:raise ValueError('duplicate_event')
            seen.add((alias,event));counts[alias]+=1
            rows.append({'alias':alias,'carrier_xy':state.carrier_xy,'candidate_ids':state.candidate_ids,'candidate_xy':state.candidate_xy,'defender_xy':state.defender_xy})
    if len(rows)!=7227 or tuple(counts[a] for a in ALIASES)!=COUNTS:raise ValueError('population_counts')
    atomic(LOCAL/'prepared.json',encoded(rows));ledger('prepare','passed')
    atomic(PREP,encoded({'schema_version':1,'status':'prepared_no_relations_or_shares','population_sha256':POP_SHA,'states':len(rows),'counts':dict(counts),'prepared_sha256':digest(LOCAL/'prepared.json'),'protocol_sha256':digest(PROTOCOL),'implementation_sha256':code_hashes()}))
    print('Prepared 7,227 target-free geometry states; no distances or shares calculated')
def dist(values,weights):return distribution(values,weights) if values else distribution([],[])
def mean(values):return math.fsum(values)/len(values) if values else None
def state_metrics(state,model):
    mapping=map_defender_edges(state);network=evaluate_options(state,model=model);summary=summarize_edge_involvement(mapping,network=network)
    edges=summary['edge_summaries'];defenders=summary['defender_summaries'];pairs=summary['segment_pair_jaccard']
    out={'edges':summary['edges'],'defenders':summary['defenders'],
         'receiver_unique_nearest_defenders':summary['receiver_unique_nearest_defenders'],
         'segment_unique_nearest_defenders':summary['segment_unique_nearest_defenders']}
    for name in ('nearest_intersects','nearest_equal','same_unique_nearest'):
        out[name]=mean([float(e[name]) for e in edges])
    out['receiver_unique_nearest_edges']=mean([float(e['receiver_nearest_count']==1) for e in edges])
    out['segment_unique_nearest_edges']=mean([float(e['segment_nearest_count']==1) for e in edges])
    for name in ('segment_d2_d1','segment_d3_d1'):
        out[name]=mean([e[name] for e in edges if e[name] is not None])
    out['any_receiver_multi_edge']=float(any(d['receiver_nearest_edges']>=2 for d in defenders.values()))
    out['any_segment_multi_edge']=float(any(d['segment_nearest_edges']>=2 for d in defenders.values()))
    out['max_receiver_nearest_edges']=max(d['receiver_nearest_edges'] for d in defenders.values())
    out['max_segment_nearest_edges']=max(d['segment_nearest_edges'] for d in defenders.values())
    for k in (1,2,3):
        out[f'max_segment_top{k}_edge_share']=max(d[f'segment_top{k}_edge_share'] for d in defenders.values())
        out[f'max_segment_top{k}_m1_weighted']=max(d[f'segment_top{k}_m1_weighted'] for d in defenders.values())
        out[f'segment_top{k}_pair_jaccard']=mean(list(pairs[f'top{k}']))
    out['receiver_distance_mean']=mean([r.receiver_distance for r in mapping.relations])
    out['segment_distance_mean']=mean([r.segment_distance for r in mapping.relations])
    return out
METRICS=('edges','defenders','receiver_unique_nearest_defenders','segment_unique_nearest_defenders','nearest_intersects','nearest_equal','same_unique_nearest','receiver_unique_nearest_edges','segment_unique_nearest_edges','segment_d2_d1','segment_d3_d1','any_receiver_multi_edge','any_segment_multi_edge','max_receiver_nearest_edges','max_segment_nearest_edges','max_segment_top1_edge_share','max_segment_top2_edge_share','max_segment_top3_edge_share','max_segment_top1_m1_weighted','max_segment_top2_m1_weighted','max_segment_top3_m1_weighted','segment_top1_pair_jaccard','segment_top2_pair_jaccard','segment_top3_pair_jaccard','receiver_distance_mean','segment_distance_mean')
def group(rows):
    result={}
    aliases=sorted({a for a,_ in rows})
    for key in METRICS:
        valid=[(a,m[key]) for a,m in rows if m[key] is not None];represented=sorted({a for a,_ in valid});counts=Counter(a for a,_ in valid)
        weights=[1/len(represented)/counts[a] for a,_ in valid] if valid else []
        result[key]={**dist([v for _,v in valid],weights),'represented_matches':len(represented)}
    return result
def rows_csv(groups,fields):
    s=io.StringIO(newline='');w=csv.DictWriter(s,fieldnames=('match_alias','states',*fields),lineterminator='\n');w.writeheader()
    for alias,data in groups.items():w.writerow({'match_alias':alias,'states':data['states'],**{f:data['metrics'][f]['mean'] for f in fields}})
    return s.getvalue()
def analyze():
    authorities(require_clean=True,require_prep=True)
    marker=safe(LOCAL/'analyze.marker');marker.parent.mkdir(parents=True,exist_ok=True)
    with marker.open('x') as f:f.write(git('rev-parse','HEAD')+'\n')
    ledger('analyze','started')
    raw=load(MODEL);model=FrozenOptionModel.from_mapping('m1',raw['models']['m1'])
    details=[]
    for row in load(LOCAL/'prepared.json'):
        state=OptionState(tuple(row['carrier_xy']),tuple(row['candidate_ids']),tuple(map(tuple,row['candidate_xy'])),tuple(map(tuple,row['defender_xy'])))
        details.append((row['alias'],state_metrics(state,model)))
    groups={}
    for alias in (*ALIASES,'match_macro'):
        chosen=details if alias=='match_macro' else [x for x in details if x[0]==alias]
        groups[alias]={'states':len(chosen),'metrics':group(chosen)}
    summary={'schema_version':1,'scope':'target_free_in_sample_development_structure','states':len(details),'counts':dict(Counter(a for a,_ in details)),'groups':groups}
    atomic(OUT/'relation_summary.json',encoded(summary))
    atomic(OUT/'role_overlap.csv',rows_csv(groups,('nearest_intersects','nearest_equal','same_unique_nearest','receiver_unique_nearest_edges','segment_unique_nearest_edges')))
    atomic(OUT/'multi_edge_summary.csv',rows_csv(groups,('any_receiver_multi_edge','any_segment_multi_edge','max_receiver_nearest_edges','max_segment_nearest_edges','max_segment_top1_edge_share','max_segment_top2_edge_share','max_segment_top3_edge_share','max_segment_top1_m1_weighted','max_segment_top2_m1_weighted','max_segment_top3_m1_weighted')))
    atomic(OUT/'redundancy_summary.csv',rows_csv(groups,('segment_d2_d1','segment_d3_d1','segment_top1_pair_jaccard','segment_top2_pair_jaccard','segment_top3_pair_jaccard')))
    atomic(LOCAL/'details.json',encoded(details));ledger('analyze','passed')
    qc={'schema_version':1,'status':'closed_aggregates','states':len(details),'matches':9,'targets_projected':True,'m1_only':True,'conservation_checked_by_production_tests':True,'detail_sha256':digest(LOCAL/'details.json')}
    atomic(OUT/'qc.json',encoded(qc));print('Session 13 aggregates closed; run publication-check before viewing')
def render():atomic(OUT/'synthetic_defender_edge_map.svg',synthetic_defender_edge_svg());print('Synthetic SVG rendered')
def publication():
    authorities(require_prep=True)
    for name in RESULTS:
        if not safe(OUT/name).is_file():raise ValueError('missing_output:'+name)
    summary=load(OUT/'relation_summary.json')
    if summary['states']!=7227 or set(summary['counts'])!=set(ALIASES):raise ValueError('summary_schema')
    for name in ('role_overlap.csv','multi_edge_summary.csv','redundancy_summary.csv'):
        rows=list(csv.DictReader(safe(OUT/name).open()))
        if len(rows)!=10 or [r['match_alias'] for r in rows]!=[*ALIASES,'match_macro']:raise ValueError('csv_schema')
    public=''.join(safe(OUT/n).read_text() for n in RESULTS)
    for forbidden in (*DEV,'target_index','event_id','carrier_xy','candidate_xy','defender_xy'):
        if forbidden in public:raise ValueError('publication_leak')
    outputs={n:digest(OUT/n) for n in (*RESULTS,'synthetic_defender_edge_map.svg') if safe(OUT/n).exists()}
    manifest={'schema_version':1,'status':'closed','start':START,'protocol_sha256':digest(PROTOCOL),'contract_sha256':digest(CONTRACT),'implementation_authority_sha256':digest(AUTH),'population_authority_sha256':digest(PREP),'population_sha256':POP_SHA,'model_sha256':MODEL_SHA,'outputs':outputs}
    atomic(OUT/'manifest.json',encoded(manifest));print('Session 13 publication checks passed')
def main():
    command=argparse.ArgumentParser();command.add_argument('command',choices=('preflight','prepare','analyze','render-synthetic','publication-check'));args=command.parse_args()
    {'preflight':preflight,'prepare':prepare,'analyze':analyze,'render-synthetic':render,'publication-check':publication}[args.command]()
if __name__=='__main__':main()
