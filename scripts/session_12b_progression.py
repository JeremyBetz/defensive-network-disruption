#!/usr/bin/env python3
"""Governed progression audit; commands do not cross commit boundaries."""
import argparse
from collections import Counter
from dataclasses import asdict
from datetime import datetime,timezone
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from defensive_network_disruption.networks.options import OptionState,FrozenOptionModel,evaluate_options
from defensive_network_disruption.networks.spatial_value import NormalizedGoalwardProgression,compare_horizons,identity_check,sign
from defensive_network_disruption.validation.construct_diagnostics import distribution
from defensive_network_disruption.data.dimension_projection import project_dimensions
from defensive_network_disruption.data.session6c_source import Session6cSourceClient,TreeEntry,verify_blob,git_blob_oid,SOURCE_COMMIT

START='9c48bf5b3146222e27e9eeb151af448e6beeb882'
DEV=('1886347','1899585','1925299','1996435','2006229','2011166','2013725','2015213','2017461')
ALIASES=tuple(f'development_{i:02d}' for i in range(1,10))
COUNTS=(885,801,952,877,861,629,764,734,724)
POP=Path('outputs/receiver_ranking_m0_m1/local/population.jsonl')
POP_SHA='cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d'
MODEL=Path('outputs/reserved_evaluation/final_development_models.json')
MODEL_SHA='0383561e45bcd9f8d84eccc7e9733b2409536f61c39193fa87d08c36c6f6fd65'
OUT=Path('outputs/internal_threat_baseline');LOCAL=OUT/'local'
PROTOCOL=Path('docs/protocols/phase_12b_internal_threat_baseline.md')
AMEND=Path('docs/protocols/phase_12b_metadata_dimensions_amendment.md')
IMPL=('scripts/session_12b_progression.py','src/defensive_network_disruption/networks/spatial_value.py','src/defensive_network_disruption/data/dimension_projection.py','tests/test_session12b_progression.py')
CANONICAL={'match_id','event_id','carrier_xy','candidate_ids','candidate_xy','defender_xy','target_index','target_outside'}
SIGNS=('negative','zero','positive')
RESULTS=('horizon_summary.json','match_summary.csv','concentration_value_typology.csv','qc.json')


def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT).decode().strip()
def safe(path):
    p=ROOT/path
    if any(x.is_symlink() for x in (p,*p.parents)) or not p.resolve().is_relative_to(ROOT.resolve()):raise PermissionError('unsafe_path')
    return p

def digest(path):
    h=hashlib.sha256()
    with safe(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def load(path):return json.loads(safe(path).read_text(),parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite_json')))
def encoded(v):return json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n'
def atomic(path,value):
    if not (path.is_relative_to(OUT) or path.is_relative_to(Path('data/session_12b'))):raise PermissionError('output_path')
    p=safe(path);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name('.'+p.name+'.tmp')
    with t.open('x') as f:f.write(value if isinstance(value,str) else encoded(value))
    t.replace(p)

def ledger(stage,status,**details):
    p=safe(LOCAL/'access.jsonl');p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('a') as f:f.write(json.dumps(dict(stage=stage,status=status,time=datetime.now(timezone.utc).isoformat(),protocol=digest(PROTOCOL),implementation=git('rev-parse','HEAD'),**details))+'\n')

def exclusive(name):
    p=safe(LOCAL/(name+'.marker'));p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:f.write(git('rev-parse','HEAD'))

def committed(p):
    if hashlib.sha256(subprocess.check_output(['git','show','HEAD:'+str(p)],cwd=ROOT)).hexdigest()!=digest(p):raise ValueError('uncommitted_authority')

def code_hashes():return {p:digest(Path(p)) for p in IMPL}
def environment():return {'python':platform.python_version(),'numpy':np.__version__,'lock':digest(Path('uv.lock'))}
def preflight():
    if git('status','--porcelain'):raise ValueError('clean_tree_required')
    git('merge-base','--is-ancestor',START,'HEAD')
    if git('rev-parse','v0.1.0^{}')!='f00690c05d8c1c6db308a65bd311c43f9a8ef2fa':raise ValueError('release_changed')
    for p in (PROTOCOL,AMEND,*(Path(x) for x in IMPL)):committed(p)
    if digest(MODEL)!=MODEL_SHA:raise ValueError('model_hash')
    model_environment=load(MODEL)['environment']
    if model_environment['python']!=platform.python_version() or model_environment['numpy']!=np.__version__:raise ValueError('historical_numerical_environment')
    changed=git('diff','--name-only',START).splitlines()
    old=set(git('ls-tree','-r','--name-only',START).splitlines())
    for name in set(changed)&old:
        if name not in {'docs/research_log.md','references/library_review.md'}:raise ValueError('historical_mutation')
        before=subprocess.check_output(['git','show',START+':'+name],cwd=ROOT)
        if not safe(Path(name)).read_bytes().startswith(before):raise ValueError('history_not_append_only')
    if not git('check-ignore','--',str(LOCAL/'probe')):raise ValueError('details_not_ignored')
    if safe(LOCAL/'failure.json').exists():raise ValueError('prior_failure_no_rerun')


def metadata_path(match,product='metadata'):
    if match not in DEV or product!='metadata':raise PermissionError('partition_product_rejected')
    return f'data/matches/{match}/{match}_match.json'


class MetadataSource(Session6cSourceClient):
    def _request(self,url,**kwargs):
        if not url.startswith('https://api.github.com/repos/SkillCorner/opendata/git/') or '?' in url:
            raise PermissionError('metadata_api_route_only')
        return super()._request(url,**kwargs)

    def entry(self,match):
        path=metadata_path(match)
        c=self._json(f'/repos/SkillCorner/opendata/git/commits/{SOURCE_COMMIT}',label='commit')
        if c.get('sha')!=SOURCE_COMMIT:raise ValueError('source_commit_mismatch')
        oid=c['tree']['sha'];tree_id=oid
        for part in path.split('/'):
            tree=self._json(f'/repos/SkillCorner/opendata/git/trees/{oid}',label='tree')
            if tree.get('sha')!=oid or tree.get('truncated'):raise ValueError('tree_mismatch')
            entries=[e for e in tree['tree'] if e['path']==part]
            if len(entries)!=1:raise ValueError('path_missing_or_duplicate')
            e=entries[0]
            if e.get('mode')=='120000':raise ValueError('source_symlink')
            if part!=path.split('/')[-1] and e['type']!='tree':raise ValueError('source_type')
            oid=e['sha']
        if e['type']!='blob' or not isinstance(e.get('size'),int) or not 0<e['size']<=1_000_000:raise ValueError('metadata_type_size')
        return tree_id,TreeEntry(path,'blob',oid,e['size'])


def verify_dimensions():
    preflight();exclusive('dimensions');ledger('dimensions','started')
    token=subprocess.check_output(['gh','auth','token']).decode().strip()
    mapping={};receipts={}
    for match,alias in zip(DEV,ALIASES):
        src=MetadataSource(token,ledger=lambda label,attempt,status,category:ledger('metadata_request',status,alias=alias,request=label,attempt=attempt,category=category))
        tree,entry=src.entry(match)
        existing=Path('data/session_02')/entry.path
        ledger('metadata_bytes','started',alias=alias)
        if safe(existing).is_file():
            data=safe(existing).read_bytes()
            if len(data)!=entry.git_size or git_blob_oid(data)!=entry.git_oid:raise ValueError('existing_metadata_integrity')
            origin='existing_verified'
        else:
            env=src._json('/repos/SkillCorner/opendata/git/blobs/'+entry.git_oid,label='metadata_blob')
            data=verify_blob(entry,env,decoded_limit=1_000_000);origin='pinned_blob'
            dest=safe(Path('data/session_12b')/entry.path);dest.parent.mkdir(parents=True,exist_ok=True)
            with dest.open('xb') as f:f.write(data)
        values=project_dimensions(data)
        mapping[match]=values;receipts[alias]={'git_oid':entry.git_oid,'size':len(data),'sha256':hashlib.sha256(data).hexdigest(),'tree':tree,'origin':origin}
        atomic(LOCAL/'dimensions.partial.json',{'mapping':mapping,'receipts':receipts})
        ledger('metadata_bytes','verified_projected',alias=alias)
    atomic(LOCAL/'dimensions.json',{'mapping':mapping,'receipts':receipts,'implementation':code_hashes(),'environment':environment()})
    ledger('dimensions','passed')


def project_row(raw):
    if set(raw)!=CANONICAL or raw['match_id'] not in DEV:raise ValueError('population_contract')
    event=raw['event_id']
    if not isinstance(event,str) or not event or event.strip()!=event:raise ValueError('event_identity')
    state=OptionState(raw['carrier_xy'],raw['candidate_ids'],raw['candidate_xy'],raw['defender_xy'])
    return raw['match_id'],event,state


def prepare():
    preflight();exclusive('prepare')
    dims=load(LOCAL/'dimensions.json')
    if dims['implementation']!=code_hashes() or dims['environment']!=environment() or set(dims['mapping'])!=set(DEV):raise ValueError('dimension_authority')
    ledger('population','hash_started')
    if digest(POP)!=POP_SHA:raise ValueError('population_hash')
    counts=Counter();seen=set();prepared=[];violations=Counter()
    ledger('population','projection_started')
    with safe(POP).open() as f:
        for line in f:
            match,event,state=project_row(json.loads(line));alias=ALIASES[DEV.index(match)]
            if (match,event) in seen:raise ValueError('duplicate_identity')
            seen.add((match,event));counts[alias]+=1
            length=dims['mapping'][match]['pitch_length'];surface=NormalizedGoalwardProgression(length)
            # Bounds only: preparation deliberately does not call value_at.
            points=(state.carrier_xy,*state.candidate_xy)
            violations[alias]+=sum(not -length/2<=p[0]<=length/2 for p in points)
            prepared.append({'alias':alias,'state':asdict(state),'length':length})
    if tuple(counts[a] for a in ALIASES)!=COUNTS:raise ValueError('population_counts')
    qc={'counts':dict(counts),'longitudinal_violation_points':dict(violations),'states':len(prepared)}
    atomic(LOCAL/'preparation_qc.json',qc)
    if not sum(violations.values()):atomic(LOCAL/'prepared.json',prepared)
    a={'schema_version':1,'status':'coordinate_blocked' if sum(violations.values()) else 'coordinate_ready','source_commit':SOURCE_COMMIT,'population_sha256':POP_SHA,'model_sha256':MODEL_SHA,'protocol_sha256':digest(PROTOCOL),'amendment_sha256':digest(AMEND),'implementation':code_hashes(),'environment':environment(),'dimensions_sha256':digest(LOCAL/'dimensions.json'),'prepared_sha256':None if sum(violations.values()) else digest(LOCAL/'prepared.json'),'counts':dict(counts),'formula':'0.5 + x_prime / actual_pitch_length','dimension_products_verified':9,'metadata_receipts_sha256':hashlib.sha256(encoded(dims['receipts']).encode()).hexdigest()}
    atomic(OUT/'value_surface_authority.json',a)
    if sum(violations.values()):raise ValueError('longitudinal_bound_violation')
    ledger('population','prepared_no_scores')


def pearson(x,y):
    x=np.asarray(x);y=np.asarray(y);x=x-x.mean();y=y-y.mean()
    if not np.any(x) or not np.any(y):return None
    return float(np.dot(x,y)/math.sqrt(float(np.dot(x,x)*np.dot(y,y))))

def stats(rows,key):
    counts=Counter(r['alias'] for r in rows)
    weights=[1/len(counts)/counts[r['alias']] for r in rows]
    return distribution([r[key] for r in rows],weights)

def summarize(rows):
    groups={}
    for alias in (*ALIASES,'match_macro'):
        rs=rows if alias=='match_macro' else [r for r in rows if r['alias']==alias]
        if not rs:continue
        counts=Counter(r['alias'] for r in rs);weight=lambda r:1/len(counts)/counts[r['alias']]
        signs={k:{s:{'count':sum(sign(r[k])==s for r in rs),'proportion':math.fsum(weight(r) for r in rs if sign(r[k])==s)} for s in SIGNS} for k in ('H0','H1','S','D')}
        cells={d+'_'+s:{'count':sum(sign(r['D'])==d and sign(r['S'])==s for r in rs),'proportion':math.fsum(weight(r) for r in rs if sign(r['D'])==d and sign(r['S'])==s)} for d in SIGNS for s in SIGNS}
        strata={d:{'counts':dict(Counter(r['alias'] for r in rs if sign(r['D'])==d)),'shift':stats([r for r in rs if sign(r['D'])==d],'S')} for d in SIGNS}
        groups[alias]={'states':len(rs),'distributions':{k:stats(rs,k) for k in ('H0','H1','S','D')},'signs':signs,'typology':cells,'strata':strata,'pearson_S_D':None if alias=='match_macro' else pearson([r['S'] for r in rs],[r['D'] for r in rs])}
    return {'schema_version':1,'scope':'label_free_in_sample_normalized_progression','groups':groups}


def csv_rows(rows):
    f=io.StringIO(newline='');w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows);return f.getvalue()

def validate_summary(s):
    if set(s)!={'schema_version','scope','groups'} or s['schema_version']!=1 or s['scope']!='label_free_in_sample_normalized_progression':raise ValueError('summary_schema')
    if set(s['groups'])!=set(ALIASES)|{'match_macro'}:raise ValueError('summary_aliases')
    for alias,g in s['groups'].items():
        expected=sum(COUNTS) if alias=='match_macro' else COUNTS[ALIASES.index(alias)]
        if g['states']!=expected or set(g)!={'states','distributions','signs','typology','strata','pearson_S_D'}:raise ValueError('group_schema')
        if set(g['distributions'])!={'H0','H1','S','D'} or set(g['signs'])!={'H0','H1','S','D'} or set(g['strata'])!=set(SIGNS):raise ValueError('metric_schema')
        if set(g['typology'])!={d+'_'+v for d in SIGNS for v in SIGNS}:raise ValueError('typology_schema')
        for group in (*g['signs'].values(),g['typology']):
            if sum(x['count'] for x in group.values())!=expected:raise ValueError('cell_count')
            identity_check(math.fsum(x['proportion'] for x in group.values()),1.,[x['proportion'] for x in group.values()])
        for k,dist in g['distributions'].items():
            validate_distribution(dist,expected)
        for d,stratum in g['strata'].items():
            if set(stratum)!={'counts','shift'} or not set(stratum['counts'])<=set(ALIASES):raise ValueError('stratum_schema')
            validate_distribution(stratum['shift'],sum(stratum['counts'].values()))
        for group in (*g['signs'].values(),g['typology']):
            for cell in group.values():
                if set(cell)!={'count','proportion'} or type(cell['count']) is not int or not 0<=cell['count']<=expected or not 0<=cell['proportion']<=1+1e-14:raise ValueError('cell_schema')
        corr=g['pearson_S_D']
        if corr is not None and (not math.isfinite(corr) or not -1.000000000001<=corr<=1.000000000001):raise ValueError('correlation_range')
    encoded(s)


def validate_distribution(d,n):
    if set(d)!={'count','mean','minimum','maximum','quantiles'} or d['count']!=n:raise ValueError('distribution_schema')
    if not n:
        if any(d[k] is not None for k in ('mean','minimum','maximum','quantiles')):raise ValueError('empty_distribution')
        return
    if set(d['quantiles'])!={'q05','q25','q50','q75','q95'}:raise ValueError('quantile_schema')
    values=[d['minimum'],*[d['quantiles'][k] for k in ('q05','q25','q50','q75','q95')],d['maximum']]
    if not all(math.isfinite(v) for v in (*values,d['mean'])) or values!=sorted(values) or not d['minimum']-1e-14<=d['mean']<=d['maximum']+1e-14:raise ValueError('distribution_values')


def analyze():
    preflight();committed(OUT/'value_surface_authority.json');a=load(OUT/'value_surface_authority.json')
    if a['status']!='coordinate_ready' or a['implementation']!=code_hashes() or a['environment']!=environment() or a['prepared_sha256']!=digest(LOCAL/'prepared.json') or a['dimensions_sha256']!=digest(LOCAL/'dimensions.json'):raise ValueError('coordinate_authority_changed')
    if any(safe(OUT/n).exists() for n in RESULTS):raise ValueError('existing_results')
    raw=load(MODEL);models={n:FrozenOptionModel.from_mapping(n,raw['models'][n]) for n in ('m0','m1')}
    exclusive('analyze');ledger('analysis','started');rows=[];residual=0.
    for r in load(LOCAL/'prepared.json'):
        state=OptionState(**r['state']);m0=evaluate_options(state,model=models['m0']);m1=evaluate_options(state,model=models['m1'])
        c=compare_horizons(state,m0,m1,NormalizedGoalwardProgression(r['length']));residual=max(residual,c.maximum_identity_residual)
        rows.append({'alias':r['alias'],'H0':c.m0.horizon,'H1':c.m1.horizon,'S':c.shift,'D':m1.effective_option_count-m0.effective_option_count})
    atomic(LOCAL/'analysis_details.json',rows)
    s=summarize(rows);validate_summary(s)
    old=load(Path('outputs/attacking_option_network/network_summary.json'))
    for alias,g in s['groups'].items():
        lhs=g['distributions']['D'];rhs=old['groups'][alias]['models']['change']['effective_option_count']
        for key in ('mean','minimum','maximum'):identity_check(lhs[key],rhs[key],[lhs[key],rhs[key]])
        for key in lhs['quantiles']:identity_check(lhs['quantiles'][key],rhs['quantiles'][key],[lhs['quantiles'][key],rhs['quantiles'][key]])
    atomic(OUT/'horizon_summary.json',s)
    atomic(OUT/'match_summary.csv',csv_rows([{'match_alias':alias,'states':g['states'],**{k+'_mean':v['mean'] for k,v in g['distributions'].items()},**{k+'_median':v['quantiles']['q50'] for k,v in g['distributions'].items()}} for alias,g in s['groups'].items()]))
    atomic(OUT/'concentration_value_typology.csv',csv_rows([{'match_alias':alias,'cell':cell,**v} for alias,g in s['groups'].items() for cell,v in g['typology'].items()]))
    atomic(OUT/'qc.json',{'status':'valid','states':len(rows),'max_identity_residual':residual,'session8_concentration_check':'passed'})
    close_manifest('pending');publication_check();close_manifest('closed');ledger('analysis','closed')


def close_manifest(status):
    names=['value_surface_authority.json',*RESULTS,'synthetic_progression_redistribution.svg']
    atomic(OUT/'manifest.json',{'schema_version':1,'status':status,'protocol':digest(PROTOCOL),'amendment':digest(AMEND),'implementation':code_hashes(),'environment':environment(),'population':POP_SHA,'models':MODEL_SHA,'outputs':{n:digest(OUT/n) for n in names if safe(OUT/n).is_file()},'unavailable':[n for n in names if not safe(OUT/n).is_file()]})


def synthetic_svg():
    coords=((-10,-15),(0,15),(20,0));surface=NormalizedGoalwardProgression(100)
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="600" viewBox="0 0 1200 600"><rect width="1200" height="600" fill="white"/><g font-family="sans-serif" fill="#182b40"><text x="35" y="30" font-size="20">SYNTHETIC — SPATIAL VALUE PROXY — NOT CALIBRATED xT</text>']
    for k,ps in enumerate(((.5,.3,.2),(.2,.3,.5))):
        ox=40+600*k;cx=ox+150;cy=285
        parts.append(f'<rect x="{ox}" y="135" width="500" height="300" fill="#f4f7fa" stroke="#999"/>')
        h=math.fsum(p*(surface.value_at(*xy)-.3) for p,xy in zip(ps,coords))
        parts.append(f'<text x="{ox}" y="90">Illustrative distribution {k}; H={h:.3f}</text>')
        for label,xy,p in zip('ABC',coords,ps):
            x=ox+5*(xy[0]+50);y=285-5*xy[1];v=surface.value_at(*xy)
            parts.append(f'<line x1="{cx}" y1="{cy}" x2="{x}" y2="{y}" stroke="#457b9d" stroke-width="{1+12*p}"/><circle cx="{x}" cy="{y}" r="10" fill="rgb({int(230-150*v)},120,{int(220-100*v)})"/><text x="{x+15}" y="{y-15}">{label}: p={p:.1f}, V={v:.1f}, ΔV={v-.3:+.1f}</text>')
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="8"/><text x="{cx-40}" y="{cy+28}">Carrier</text>')
    parts.append('<text x="35" y="495">Identical concentration; progression shift +0.090. Shares are illustrative, not fitted outputs.</text><text x="35" y="530">Width: share. Color: destination progression. Equal metric scales; attack →.</text></g></svg>\n')
    return ''.join(parts)

def render_synthetic():
    if load(OUT/'manifest.json')['status']!='closed':raise ValueError('analysis_closure_required')
    svg=synthetic_svg()
    if svg!=synthetic_svg():raise ValueError('render_nondeterministic')
    atomic(OUT/'synthetic_progression_redistribution.svg',svg);close_manifest('closed')


def publication_check():
    m=load(OUT/'manifest.json')
    if set(m)!={'schema_version','status','protocol','amendment','implementation','environment','population','models','outputs','unavailable'}:raise ValueError('manifest_schema')
    if m['protocol']!=digest(PROTOCOL) or m['amendment']!=digest(AMEND) or m['implementation']!=code_hashes():raise ValueError('manifest_authority')
    for name,h in m['outputs'].items():
        if name not in {'value_surface_authority.json',*RESULTS,'synthetic_progression_redistribution.svg'} or digest(OUT/name)!=h:raise ValueError('output_identity')
        text=safe(OUT/name).read_text()
        if any(s in text for s in (*DEV,'1953632','/Users/','candidate_xy','event_id','target_index')):raise ValueError('publication_content')
    if m['status'] in {'closed','pending'}:
        summary=load(OUT/'horizon_summary.json');validate_summary(summary)
        rows=list(csv.DictReader(io.StringIO(safe(OUT/'match_summary.csv').read_text())))
        if len(rows)!=10 or {x['match_alias'] for x in rows}!=set(summary['groups']):raise ValueError('csv_aliases')
        for row in rows:
            g=summary['groups'][row['match_alias']]
            if set(row)!={'match_alias','states',*(k+'_mean' for k in ('H0','H1','S','D')),*(k+'_median' for k in ('H0','H1','S','D'))} or int(row['states'])!=g['states']:raise ValueError('csv_schema')
            for k in ('H0','H1','S','D'):
                if float(row[k+'_mean'])!=g['distributions'][k]['mean'] or float(row[k+'_median'])!=g['distributions'][k]['quantiles']['q50']:raise ValueError('csv_cross_file')
        rows=list(csv.DictReader(io.StringIO(safe(OUT/'concentration_value_typology.csv').read_text())))
        if len(rows)!=90 or len({(x['match_alias'],x['cell']) for x in rows})!=90:raise ValueError('typology_csv_count')
        for row in rows:
            v=summary['groups'][row['match_alias']]['typology'][row['cell']]
            if set(row)!={'match_alias','cell','count','proportion'} or int(row['count'])!=v['count'] or float(row['proportion'])!=v['proportion']:raise ValueError('typology_csv_cross_file')
    elif m['status']!='blocked':raise ValueError('closure_status')
    return True


def failure(stage,error):
    category=str(error) if str(error) in {'longitudinal_bound_violation','population_counts','population_hash','metadata_dimension_schema_invalid'} else type(error).__name__
    atomic(LOCAL/'failure.json',{'stage':stage,'category':category})
    ledger(stage,'blocked',category=category)
    q={'status':'blocked','stage':stage,'category':category,'empirical_horizons':'not executed' if not safe(LOCAL/'analyze.marker').exists() else 'execution attempted; preserve partial outputs'}
    if safe(LOCAL/'preparation_qc.json').exists():q['preparation']=load(LOCAL/'preparation_qc.json')
    atomic(OUT/'qc.json',q);close_manifest('blocked')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=('preflight','verify-dimensions','prepare','analyze','render-synthetic','publication-check'));args=p.parse_args()
    commands={'preflight':preflight,'verify-dimensions':verify_dimensions,'prepare':prepare,'analyze':analyze,'render-synthetic':render_synthetic,'publication-check':publication_check}
    try:commands[args.command]();print(args.command+': passed')
    except Exception as error:
        if args.command in {'verify-dimensions','prepare','analyze'}:failure(args.command,error)
        print(args.command+': stopped ('+type(error).__name__+')');sys.exit(1)
