#!/usr/bin/env python3
"""One bounded coordinate review; no model/scoring or payload-download route."""
import argparse
from collections import Counter,defaultdict
import csv
from datetime import datetime,timezone
import hashlib
import io
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from defensive_network_disruption.data.boundary_review import canonical_projection,occurrence_points,carrier_reference,exact_events,metadata_projection,frame_header,player_samples,neighbors,verify_point,describe,local_runs,clock_microseconds,select_decision_frame,attack_sign,active_in_period
from defensive_network_disruption.data.session6c_source import Session6cSourceClient,git_blob_oid,verify_blob,SOURCE_COMMIT

START='ca17380b7f987d33d8841aa2493897e311f98436'
DEV=('1886347','1899585','1925299','1996435','2006229','2011166','2013725','2015213','2017461')
ALIASES=tuple(f'development_{i:02d}' for i in range(1,10));COUNTS=(885,801,952,877,861,629,764,734,724);VIOLATIONS=(2,1,3,2,1,1,2,0,0)
POP=Path('outputs/receiver_ranking_m0_m1/local/population.jsonl');POP_SHA='cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d'
DIMS=Path('outputs/internal_threat_baseline/local/dimensions.json');DIMS_SHA='ded8721ad91f18b98c09488852481aaadfe3098d7b5f2039f0531e6e4f923c69'
PRIOR={'value_surface_authority.json':'03311326e7339ca093e0f50da6b0603e650f53b20df24b6f68501896d0470936','qc.json':'fd870f22276d1a15c19376abc4e905ac483fefb2124fcff80a9fe9d7c24152dc','manifest.json':'e53062040d7c89914924c50a44b1729c655f7725433a456471c387c94c1b586d'}
OUT=Path('outputs/coordinate_boundary_review');LOCAL=OUT/'local';PROTOCOL=Path('docs/protocols/phase_12c_coordinate_boundary_review.md')
IMPL=('scripts/session_12c_boundary.py','src/defensive_network_disruption/data/boundary_review.py','tests/test_session12c_boundary.py')
RESULTS=('occurrence_authority.json','occurrence_summary.json','match_summary.csv','qc.json')


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

def text(v):return json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n'
def load(path):return json.loads(safe(path).read_text())
def atomic(path,value):
    if not path.is_relative_to(OUT):raise PermissionError('output_scope')
    p=safe(path);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name('.'+p.name+'.tmp')
    with t.open('x') as f:f.write(value if isinstance(value,str) else text(value))
    t.replace(p)

def code():return {p:digest(Path(p)) for p in IMPL}
def ledger(stage,status,**kw):
    p=safe(LOCAL/'access.jsonl');p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('a') as f:f.write(json.dumps(dict(stage=stage,status=status,time=datetime.now(timezone.utc).isoformat(),protocol=digest(PROTOCOL),implementation=git('rev-parse','HEAD'),**kw))+'\n')

def exclusive(stage):
    p=safe(LOCAL/(stage+'.marker'));p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:f.write(git('rev-parse','HEAD'))

def committed(path):
    if hashlib.sha256(subprocess.check_output(['git','show','HEAD:'+str(path)],cwd=ROOT)).hexdigest()!=digest(path):raise ValueError('uncommitted_authority')

def preservation():
    old=set(git('ls-tree','-r','--name-only',START).splitlines())
    for p in old&set(git('diff','--name-only',START).splitlines()):
        if p not in {'docs/research_log.md','references/library_review.md'}:raise ValueError('history_changed')
        if not safe(Path(p)).read_bytes().startswith(subprocess.check_output(['git','show',START+':'+p],cwd=ROOT)):raise ValueError('history_not_append_only')

def preflight():
    if git('status','--porcelain'):raise ValueError('clean_commit_required')
    git('merge-base','--is-ancestor',START,'HEAD');preservation()
    if git('rev-parse','v0.1.0^{}')!='f00690c05d8c1c6db308a65bd311c43f9a8ef2fa':raise ValueError('tag_changed')
    for p in (PROTOCOL,*(Path(p) for p in IMPL)):committed(p)
    for name,h in PRIOR.items():
        if digest(Path('outputs/internal_threat_baseline')/name)!=h:raise ValueError('12b_authority_changed')
    if not git('check-ignore','--',str(LOCAL/'probe')):raise ValueError('local_not_ignored')
    if safe(LOCAL/'failure.json').exists():raise ValueError('prior_failure_no_rerun')


def validate_occurrence_counts(counts,occ):
    if tuple(counts.get(a,0) for a in ALIASES)!=COUNTS or tuple(occ.get(a,0) for a in ALIASES)!=VIOLATIONS:raise ValueError('occurrence_reproduction_mismatch')


def identify():
    preflight();exclusive('identify');ledger('identify','hash_started')
    if digest(POP)!=POP_SHA or digest(DIMS)!=DIMS_SHA:raise ValueError('population_dimension_hash')
    dims=load(DIMS)['mapping']
    if set(dims)!=set(DEV):raise ValueError('dimension_mapping')
    counts=Counter();occ=Counter();seen=set();selected=[];ledger('identify','projection_started')
    with safe(POP).open() as f:
        for ordinal,line in enumerate(f):
            row=canonical_projection(line);match,event=row[:2]
            if match not in DEV:raise PermissionError('development_only')
            if (match,event) in seen:raise ValueError('duplicate_event')
            seen.add((match,event));alias=ALIASES[DEV.index(match)];counts[alias]+=1
            for point in occurrence_points(row,dims[match]['pitch_length']):
                point.update(ordinal=ordinal,alias=alias,review_id=f'occurrence_{len(selected)+1:02d}');selected.append(point);occ[alias]+=1
    validate_occurrence_counts(counts,occ)
    atomic(LOCAL/'occurrences.json',selected)
    a={'schema_version':1,'status':'exact_reproduction','population_sha256':POP_SHA,'dimensions_sha256':DIMS_SHA,'previous_authorities':PRIOR,'counts':dict(counts),'occurrence_counts':{a:occ[a] for a in ALIASES},'occurrences':len(selected),'local_occurrence_sha256':digest(LOCAL/'occurrences.json'),'protocol_sha256':digest(PROTOCOL),'implementation':code(),'environment':{'python':platform.python_version(),'lock_sha256':digest(Path('uv.lock'))}}
    atomic(OUT/'occurrence_authority.json',a);ledger('identify','closed')


def product_path(match,product):
    if match not in DEV[:7] or product not in {'metadata','events','tracking'}:raise PermissionError('partition_product')
    suffix={'metadata':'match.json','events':'dynamic_events.csv','tracking':'tracking_extrapolated.jsonl'}[product]
    return f'data/matches/{match}/{match}_{suffix}'


class ObjectSource(Session6cSourceClient):
    def _request(self,url,**kw):
        if not url.startswith('https://api.github.com/repos/SkillCorner/opendata/git/'):raise PermissionError('object_metadata_only')
        return super()._request(url,**kw)
    def tree_entries(self,paths):
        allowed={product_path(m,p) for m in DEV[:7] for p in ('metadata','events','tracking')}|{'README.md'}
        if not paths<=allowed:raise PermissionError('source_path_scope')
        return super().tree_entries(paths)
    def acquire(self,*args,**kw):raise PermissionError('payload_acquisition_forbidden')


def verify_sources(matches):
    token=subprocess.check_output(['gh','auth','token']).decode().strip()
    src=ObjectSource(token,ledger=lambda label,attempt,status,category:ledger('object_request',status,label=label,attempt=attempt,category=category))
    paths={product_path(m,p) for m in matches for p in ('metadata','events','tracking')}|{'README.md'}
    tree,entries=src.tree_entries(paths);receipts={}
    dims=load(DIMS)
    for match in matches:
        alias=ALIASES[DEV.index(match)];receipts[match]={}
        for product in ('metadata','events','tracking'):
            path=product_path(match,product);entry=entries[path];local=Path('data/session_02')/path
            ledger('local_integrity','started',alias=alias,product=product)
            if not safe(local).is_file():raise ValueError('local_product_unavailable')
            if product=='tracking':
                pointer,pointer_bytes=src.pointer(entry,label=alias+'_pointer')
                actual=digest(local)
                if safe(local).stat().st_size!=pointer.payload_size or actual!=pointer.payload_sha256:raise ValueError('tracking_integrity')
                receipt={'git_oid':entry.git_oid,'git_size':entry.git_size,'payload_sha256':actual,'payload_size':pointer.payload_size,'pointer_sha256':hashlib.sha256(pointer_bytes).hexdigest()}
            else:
                b=safe(local).read_bytes()
                if len(b)!=entry.git_size or git_blob_oid(b)!=entry.git_oid:raise ValueError('ordinary_integrity')
                receipt={'git_oid':entry.git_oid,'size':len(b),'sha256':hashlib.sha256(b).hexdigest()}
                if product=='metadata':
                    prior=dims['receipts'][alias]
                    if receipt['git_oid']!=prior['git_oid'] or receipt['sha256']!=prior['sha256']:raise ValueError('dimension_join_defect')
            receipts[match][product]=receipt;ledger('local_integrity','verified',alias=alias,product=product)
    e=entries['README.md'];env=src._json('/repos/SkillCorner/opendata/git/blobs/'+e.git_oid,label='provider_readme')
    readme=verify_blob(e,env,decoded_limit=100_000)
    atomic(LOCAL/'provider_readme.txt',readme.decode())
    atomic(LOCAL/'source_receipts.json',{'tree':tree,'products':receipts,'readme_git_oid':e.git_oid,'readme_sha256':hashlib.sha256(readme).hexdigest()})
    return receipts


def build_index(handle):
    out={1:[],2:[]}
    for line_index,line in enumerate(handle):
        h=frame_header(line)
        if h['period'] is not None and type(h['period']) is not int:raise ValueError('period_representation')
        if h['period'] not in out or h['timestamp'] is None:continue
        t=clock_microseconds(h['timestamp']);frame=h['frame']
        if type(frame) is not int:raise ValueError('frame_representation')
        index=out[h['period']]
        if index and t<=index[-1][0]:raise ValueError('clock_nonmonotonic')
        index.append((t,frame,line_index))
    return out


def recover_match(match,occs,dimensions):
    alias=ALIASES[DEV.index(match)];ledger('event_recovery','started',alias=alias)
    with safe(Path('data/session_02')/product_path(match,'events')).open(encoding='utf-8-sig',newline='') as f:events=exact_events(f,{o['event'] for o in occs})
    carriers={eid:carrier_reference(event) for eid,event in events.items()}
    wanted=set(carriers.values())|{o['player'] for o in occs if o['player'] is not None}
    ledger('metadata_projection','started',alias=alias)
    meta=metadata_projection(safe(Path('data/session_02')/product_path(match,'metadata')).read_text(),wanted)
    if any(meta[k]!=dimensions[k] for k in ('pitch_length','pitch_width')):raise ValueError('dimension_join_defect')
    tracking=Path('data/session_02')/product_path(match,'tracking');ledger('tracking_index','started',alias=alias)
    with safe(tracking).open() as f:index=build_index(f)
    requests=defaultdict(set);contexts=[]
    for o in occs:
        event=events[o['event']];period=int(event['period'])
        if period not in index:raise ValueError('event_period')
        selected=select_decision_frame(index[period],clock_microseconds(event['time_end']))
        if selected is None:raise ValueError('decision_frame_unavailable')
        position=index[period].index(selected);pid=o['player'] or carriers[o['event']]
        carrier=meta['players'][carriers[o['event']]];player=meta['players'][pid]
        if not active_in_period(carrier,period,selected[1]) or not active_in_period(player,period,selected[1]):raise ValueError('active_interval_defect')
        if player['team_id']!=carrier['team_id']:raise ValueError('team_join_defect')
        direction=attack_sign(meta['home_team']['id'],carrier['team_id'],meta['home_team_side'][period-1])
        window=neighbors(index[period],position)
        for i in window:requests[index[period][i][2]].add(pid)
        contexts.append((o,period,position,pid,direction,window))
    ledger('selected_samples','started',alias=alias);samples={}
    with safe(tracking).open() as f:
        for line_no,line in enumerate(f):
            if line_no in requests:samples[line_no]=player_samples(line,requests[line_no])
    results=[];run_samples={};edges=set();window_sets=[]
    for o,period,position,pid,direction,window in contexts:
        center=samples[index[period][position][2]].get(pid)
        if center is None:raise ValueError('decision_player_unavailable')
        excess=verify_point(o['xy'],center['xy'],direction,dimensions['pitch_length'])
        details=[];keys=set()
        for i in window:
            sample=samples[index[period][i][2]].get(pid);key=(match,period,pid,i);keys.add(key)
            if sample is None:run_samples[key]=None
            else:
                x=direction*sample['xy'][0];side=1 if x>dimensions['pitch_length']/2 else -1 if x<-dimensions['pitch_length']/2 else 0
                run_samples[key]={'side':side,'status':sample['status']}
            details.append({'index':i,'frame':index[period][i][1],'time_us':index[period][i][0],'sample':sample,'side':None if sample is None else side})
        edges.update(((match,period,pid,window[0]),(match,period,pid,window[-1])));window_sets.append(keys)
        results.append({'review_id':o['review_id'],'alias':alias,'role':o['role'],'player':pid,'period':period,'frame':index[period][position][1],'position':position,'excess':excess,'side':'positive' if o['xy'][0]>0 else 'negative','length':dimensions['pitch_length'],'status':center['status'],'lateral_crossing':abs(o['xy'][1])>dimensions['pitch_width']/2,'raw_xy':center['xy'],'canonical_xy':o['xy'],'sign':direction,'samples':details})
    ledger('match_review','verified',alias=alias)
    return results,run_samples,edges,window_sets


def aggregate(results,samples,edges,windows):
    status={s:describe([r['excess'] for r in results if r['status']==s]) for s in ('detected','extrapolated','unavailable')}
    unique={(r['alias'],r['period'],r['player'],r['frame']) for r in results};players=Counter((r['alias'],r['player']) for r in results)
    transitions=0
    for k,v in samples.items():
        previous=samples.get((*k[:3],k[3]-1))
        if v is not None and previous is not None and previous['status']!=v['status']:transitions+=1
    return {'schema_version':1,'status':'review_complete','occurrences':len(results),'roles':dict(Counter(r['role'] for r in results)),'boundary_sides':dict(Counter(r['side'] for r in results)),'pitch_length_classes':dict(Counter(str(r['length']) for r in results)),'excess_metres':describe([r['excess'] for r in results]),'detection_excess':status,'simultaneous_lateral_crossings':sum(r['lateral_crossing'] for r in results),'distinct_player_frames':len(unique),'repeated_occurrences':len(results)-len(unique),'distinct_players':len(players),'players_with_repeated_occurrences':sum(n>1 for n in players.values()),'overlapping_window_pairs':sum(bool(a&b) for i,a in enumerate(windows) for b in windows[i+1:]),'authorized_unique_samples':len(samples),'missing_samples':sum(v is None for v in samples.values()),'detection_status_transitions':transitions,**local_runs(samples,edges),'transformation':'exactly_verified','dimension_join':'exactly_verified','interpretation_status':'pending_documentary_interpretation_in_report'}


def close(status):
    atomic(OUT/'manifest.json',{'schema_version':1,'status':status,'protocol_sha256':digest(PROTOCOL),'implementation':code(),'population_sha256':POP_SHA,'dimension_sha256':DIMS_SHA,'outputs':{n:digest(OUT/n) for n in RESULTS if safe(OUT/n).exists()},'unavailable':[n for n in RESULTS if not safe(OUT/n).exists()]})


def review():
    preflight();committed(OUT/'occurrence_authority.json');a=load(OUT/'occurrence_authority.json')
    if a['implementation']!=code() or a['protocol_sha256']!=digest(PROTOCOL) or a['local_occurrence_sha256']!=digest(LOCAL/'occurrences.json'):raise ValueError('occurrence_authority_changed')
    if digest(POP)!=POP_SHA or digest(DIMS)!=DIMS_SHA:raise ValueError('input_hash_changed')
    exclusive('review');ledger('review','started');occs=load(LOCAL/'occurrences.json');matches=sorted({o['match'] for o in occs})
    receipts=verify_sources(matches);dims=load(DIMS)['mapping'];results=[];samples={};edges=set();windows=[]
    for match in matches:
        result,ss,ee,ww=recover_match(match,[o for o in occs if o['match']==match],dims[match]);results.extend(result);samples.update(ss);edges.update(ee);windows.extend(ww)
        atomic(LOCAL/'review.partial.json',results)
    summary=aggregate(results,samples,edges,windows)
    # F is a conservative machine status; report interpretation requires documentary evidence.
    atomic(OUT/'occurrence_summary.json',summary)
    f=io.StringIO(newline='');writer=csv.DictWriter(f,fieldnames=('match_alias','occurrences','carriers','candidates','detected','extrapolated','unavailable'),lineterminator='\n');writer.writeheader()
    for alias in ALIASES:
        rr=[r for r in results if r['alias']==alias]
        writer.writerow({'match_alias':alias,'occurrences':len(rr),'carriers':sum(r['role']=='carrier' for r in rr),'candidates':sum(r['role']=='candidate' for r in rr),**{s:sum(r['status']==s for r in rr) for s in ('detected','extrapolated','unavailable')}})
    atomic(OUT/'match_summary.csv',f.getvalue());atomic(OUT/'qc.json',{'status':'valid_review','occurrence_reproduction':12,'source_products_verified':sum(len(x) for x in receipts.values()),'source_receipts_sha256':digest(LOCAL/'source_receipts.json'),'transformation_verified':12,'dimension_join_verified':12,'no_outcome_access':True,'partial_detail_sha256':digest(LOCAL/'review.partial.json')})
    close('pending');publication_check();close('closed');ledger('review','closed')


def publication_check():
    m=load(OUT/'manifest.json')
    if set(m)!={'schema_version','status','protocol_sha256','implementation','population_sha256','dimension_sha256','outputs','unavailable'} or m['status'] not in {'pending','closed','stopped'}:raise ValueError('manifest_schema')
    if m['implementation']!=code() or m['protocol_sha256']!=digest(PROTOCOL):raise ValueError('manifest_authority')
    for n,h in m['outputs'].items():
        if n not in RESULTS or digest(OUT/n)!=h:raise ValueError('result_hash')
        raw=safe(OUT/n).read_text()
        if any(x in raw for x in (*DEV,'1953632','event_id','raw_xy','canonical_xy','time_us','/Users/')):raise ValueError('publication_content')
    if m['status'] in {'closed','pending'}:
        s=load(OUT/'occurrence_summary.json')
        expected={'schema_version','status','occurrences','roles','boundary_sides','pitch_length_classes','excess_metres','detection_excess','simultaneous_lateral_crossings','distinct_player_frames','repeated_occurrences','distinct_players','players_with_repeated_occurrences','overlapping_window_pairs','authorized_unique_samples','missing_samples','detection_status_transitions','observed_local_runs','censored_runs','single_observed_sample_runs','transformation','dimension_join','interpretation_status'}
        if set(s)!=expected or s['occurrences']!=12:raise ValueError('summary_schema')
        for key in ('roles','boundary_sides','pitch_length_classes'):
            if sum(s[key].values())!=12:raise ValueError('summary_count')
        if sum(d['count'] for d in s['detection_excess'].values())!=12:raise ValueError('detection_count')
        if not set(s['roles'])<={'carrier','candidate'} or not set(s['boundary_sides'])<={'positive','negative'} or set(s['detection_excess'])!={'detected','extrapolated','unavailable'}:raise ValueError('category_schema')
        for d in (s['excess_metres'],*s['detection_excess'].values()):
            if set(d)!={'count','minimum','median','maximum'} or type(d['count']) is not int or not 0<=d['count']<=12:raise ValueError('distance_schema')
            if d['count']:
                if not all(isinstance(d[k],(int,float)) and math.isfinite(d[k]) for k in ('minimum','median','maximum')) or not 0<d['minimum']<=d['median']<=d['maximum']:raise ValueError('distance_values')
            elif any(d[k] is not None for k in ('minimum','median','maximum')):raise ValueError('empty_distance')
        if s['distinct_player_frames']+s['repeated_occurrences']!=12 or s['missing_samples']>s['authorized_unique_samples'] or s['censored_runs']>s['observed_local_runs']:raise ValueError('summary_consistency')
        text(s)
        rows=list(csv.DictReader(io.StringIO(safe(OUT/'match_summary.csv').read_text())))
        if len(rows)!=9 or tuple(r['match_alias'] for r in rows)!=ALIASES or tuple(int(r['occurrences']) for r in rows)!=VIOLATIONS:raise ValueError('csv_counts')
        for row in rows:
            if set(row)!={'match_alias','occurrences','carriers','candidates','detected','extrapolated','unavailable'} or int(row['carriers'])+int(row['candidates'])!=int(row['occurrences']) or sum(int(row[k]) for k in ('detected','extrapolated','unavailable'))!=int(row['occurrences']):raise ValueError('csv_schema')
    return True


def failure(stage,error):
    known={'transformation_defect','dimension_join_defect','active_interval_defect','team_join_defect','occurrence_reproduction_mismatch','carrier_reference_conflict','local_product_unavailable','detection_status_invalid'}
    reason=str(error) if str(error) in known else type(error).__name__
    atomic(LOCAL/'failure.json',{'stage':stage,'reason':reason});ledger(stage,'stopped',reason=reason)
    defect=reason in {'transformation_defect','dimension_join_defect','active_interval_defect','team_join_defect'}
    atomic(OUT/'qc.json',{'status':'stopped','stage':stage,'reason':reason,'primary':'C' if defect else 'F','remedy_readiness':3 if defect else 4});close('stopped')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=('preflight','identify','review','publication-check'));args=parser.parse_args()
    try:{'preflight':preflight,'identify':identify,'review':review,'publication-check':publication_check}[args.command]();print(args.command+': passed')
    except Exception as exc:
        if args.command in {'identify','review'}:failure(args.command,exc)
        print(args.command+': stopped ('+type(exc).__name__+')');sys.exit(1)
