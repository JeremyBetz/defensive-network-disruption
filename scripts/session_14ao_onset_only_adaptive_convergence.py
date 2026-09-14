#!/usr/bin/env python3
"""Single-edge 14ao evidence study; no production/piecewise/replay route."""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import math
from pathlib import Path
import platform
import re
import subprocess
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import numpy as np
import scipy
from defensive_network_disruption.geometry import onset_convergence as d
from defensive_network_disruption.geometry.occlusion_fields import CarrierOriginField
from defensive_network_disruption.geometry.diagnostic_serialization import project_evidence
from defensive_network_disruption.validation.empirical_switch_diagnosis import project_prepared_edge,project_canonical_edge,selective_bytes
from defensive_network_disruption.validation.r5_persistence import Journal,read_journal
from defensive_network_disruption.validation import retained_evidence_review as v

START='72321255e5c31fc5946d5469717eeb5d17e30dce'
TAG='f00690c05d8c1c6db308a65bd311c43f9a8ef2fa'
PROTOCOL='docs/protocols/phase_14ao_onset_only_adaptive_convergence.md'
SOURCES=(PROTOCOL,'scripts/session_14ao_onset_only_adaptive_convergence.py',
 'src/defensive_network_disruption/geometry/onset_convergence.py','tests/test_session14ao_convergence.py')
OUT=ROOT/'outputs/session14ao_onset_only_adaptive_convergence'
AM=ROOT/'outputs/session14am_constant_width_comparator_diagnosis'
AN=ROOT/'outputs/session14an_retained_evidence_adjudication'
AM_HASH='235585718c4fe6a1eb2c48ac655d95a84f92fe7b342d2e486abfb3542425193e'
AN_HASH='7abbca8d205fb09ac67db3bb40e008241217cce75b8b20a054f99b1961b40459'
INPUTS={'outputs/receiver_ranking_m0_m1/local/population.jsonl':'cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d',
 'outputs/continuous_occlusion_retry_14r8/local/prepared.jsonl':'15a809060f0ba4a8cb3790011dab8008db3dad6e931c287ccb395f61ef1530b0'}
CSV_SCHEMAS={
 'refinement_results.csv':('level','tolerance','status','normal_return','warning','exhausted','neval','terminal_subintervals','subdivision_operations','seconds','trace_sha256','evidence_sha256'),
 'subdivision_summary.csv':('level','status','onset_adjacent_panels','terminal_panels','error_fraction_private','evidence_sha256'),
 'error_estimate_summary.csv':('level','status','reported_bounds_met','reported_error_exceeds_gate','exact_errors_private','evidence_sha256'),
 'reference_comparison.csv':('level','status','reference_within_gate','piecewise_within_gate','anchor_match','delta_exceeds_gate','reference_error_decreased','extra_work','trace_changed','exact_differences_private','evidence_sha256')}
JSON_SCHEMAS={
 'retained_authority.json':{'schema_version','reference_eligible','selected_serialization_verified','onset_count','input_hashes','retained_hashes'},
 'refinement_protocol.json':{'schema_version','tolerances','limit','gate','stability_span','per_level_seconds','total_seconds','candidate','no_extra_boundaries'},
 'timeout_summary.json':{'schema_version','timed_out','failed_level','reason','completed_levels','later_levels_unavailable'},
 'classification.json':{'schema_version','classification','readiness','reason','qualified_B','execution_valid','recommendation'},
 'qc.json':{'schema_version','status','execution_valid','classification','readiness','candidate','levels_attempted','levels_completed','states_opened','edges_opened','exposure_uncertain','journal_head','private_index_sha256','synthetic_controls_passed'},
 'manifest.json':{'schema_version','status','outputs','authority','private_index_sha256'}}
NAMES=tuple(CSV_SCHEMAS)+tuple(n for n in JSON_SCHEMAS if n!='manifest.json')

def git(*args):return subprocess.check_output(('git',*args),cwd=ROOT,text=True).strip()
def put(path,value):v.atomic(path,project_evidence(value))

def preflight():
    if git('status','--porcelain'):raise RuntimeError('dirty_tree')
    git('merge-base','--is-ancestor',START,'HEAD')
    if git('rev-parse','v0.1.0^{}')!=TAG:raise d.AuthorityError('release_changed')
    if Path(sys.prefix).resolve()!=(ROOT/'.venv').resolve():raise RuntimeError('project_environment')
    for name in SOURCES:
        if subprocess.check_output(('git','show','HEAD:'+name),cwd=ROOT)!=(ROOT/name).read_bytes():raise RuntimeError('uncommitted_source')
    historical={}
    for name in git('ls-tree','-r','--name-only',START).splitlines():
        old=subprocess.check_output(('git','show',START+':'+name),cwd=ROOT);now=(ROOT/name).read_bytes()
        if name=='docs/research_log.md':
            if not now.startswith(old):raise d.AuthorityError('history_log')
        elif now!=old:raise d.AuthorityError('history_changed')
        historical[name]=hashlib.sha256(old).hexdigest()
    return dict(start=START,implementation_commit=git('rev-parse','HEAD'),sources={n:v.sha(ROOT/n) for n in SOURCES},
        historical_tree_sha256=v.digest(historical),lock_sha256=v.sha(ROOT/'uv.lock'),python=platform.python_version(),
        numpy=np.__version__,scipy=scipy.__version__,system=platform.system(),architecture=platform.machine())

def checked(path,expected):
    if not path.exists():raise d.MissingAuthority('missing_retained_authority')
    if v.sha(path)!=expected:raise d.AuthorityError('retained_hash_changed')

def retained_index():
    checked(AM/'manifest.json',AM_HASH);checked(AN/'manifest.json',AN_HASH)
    am=v.load(AM/'manifest.json');an=v.load(AN/'manifest.json')
    checked(AN/'reference_eligibility.json',an['outputs']['reference_eligibility.json'])
    if v.load(AN/'reference_eligibility.json')['checks']['eligible'] is not True:raise d.MissingAuthority('eligibility_unestablished')
    checked(AM/'local/private_index.json',am['private_index_sha256'])
    return v.load(AM/'local/private_index.json')['files']

def project_retained(index,label,paths):
    result=[]
    for name,h in index.items():
        if not re.fullmatch(r'[0-9]{6}_'+label+r'\.json',name):continue
        p=AM/'local'/name;checked(p,h)
        result.append((v.Projection(p.read_text(),paths).run(),h))
    if not result:raise d.MissingAuthority('missing_'+label)
    return result

def reference_values(index):
    selected=[];hashes={}
    # Read resolution metadata first; only the reference estimate is decoded.
    for name,h in index.items():
        if not re.fullmatch(r'[0-9]{6}_piecewise\.json',name):continue
        p=AM/'local'/name;checked(p,h)
        meta=v.Projection(p.read_text(),('intervals',)).run()
        if meta.get('intervals')==16384:
            selected.append(v.Projection(p.read_text(),('estimate',)).run()['estimate']);hashes['reference']=h
    if len(selected)!=1:raise d.MissingAuthority('unique_reference_unavailable')
    anchors=project_retained(index,'onset_adaptive',('estimate',));bounds=project_retained(index,'strict',('lower','upper'))
    if len(anchors)!=1 or len(bounds)!=1:raise d.AuthorityError('reference_multiplicity')
    reference=selected[0];anchor=anchors[0][0]['estimate'];bound=(bounds[0][0]['lower'],bounds[0][0]['upper'])
    if not all(v.finite(x) for x in (reference,anchor,*bound)) or bound[0]>bound[1]:raise d.AuthorityError('reference_values_invalid')
    hashes.update(anchor=anchors[0][1],piecewise_bounds=bounds[0][1])
    return reference,anchor,bound,hashes

def retained_onsets(index):
    items=project_retained(index,'structure',('onsets.*.first_post_branch','onsets.*.type'))
    lists=[]
    for item,h in items:
        if any(x.get('type')!='certified_onset' for x in item['onsets']):raise d.AuthorityError('onset_type')
        lists.append(tuple(x['first_post_branch'] for x in item['onsets']))
    if any(x!=lists[0] for x in lists):raise d.AuthorityError('onset_records_disagree')
    if any(not v.finite(x) or not 0.<x<1. for x in lists[0]):raise d.AuthorityError('onset_domain')
    return tuple(sorted({0.,1.,*lists[0]})),[h for _,h in items]

class Evidence:
    def __init__(self,folder):self.folder=folder;self.files={};self.serial=0
    def save(self,label,value):
        name=f'{self.serial:06d}_{label}.json';self.serial+=1;put(self.folder/name,value)
        self.files[name]=v.sha(self.folder/name);return self.files[name]

def selected_line(path):
    with path.open('rb') as f:
        for i,line in enumerate(f):
            if i==4:return line.decode()
    raise d.MissingAuthority('retained_row_missing')

def access_edge(journal,evidence):
    d.guard(4,7,'constant_width')
    for name,h in INPUTS.items():checked(ROOT/name,h)
    rows=[]
    for product,name,projector in [('canonical',next(iter(INPUTS)),project_canonical_edge),('prepared',list(INPUTS)[1],project_prepared_edge)]:
        journal.append('access_attempt',product=product,state=4,edge=7,candidate='constant_width')
        row=projector(selected_line(ROOT/name),7)
        journal.append('access_materialized',product=product,state=4,edge=7,candidate='constant_width')
        rows.append(row)
    if selective_bytes(rows[0])!=selective_bytes(rows[1]):raise d.AuthorityError('selected_serialization_mismatch')
    evidence.save('selected_geometry',rows[0]);return rows[0]

def csv_rows(levels,hashes,comparisons):
    out={n:[] for n in CSV_SCHEMAS}
    for i,tolerance in enumerate(d.TOLERANCES):
        r=levels[i] if i<len(levels) else None;c=comparisons[i] if i<len(comparisons) else {}
        status='complete' if r and r['complete'] else 'partial' if r else 'unavailable';h=hashes[i] if i<len(hashes) else ''
        base=dict(level=i,status=status,evidence_sha256=h)
        out['refinement_results.csv'].append(dict(base,tolerance=tolerance,normal_return=r['normal'] if r else None,
            warning=r['warnings'] if r else None,exhausted=r['exhausted'] if r else None,neval=r['neval'] if r else None,
            terminal_subintervals=r['terminal_panels'] if r else None,subdivision_operations=r['subdivisions'] if r else None,
            seconds=r['seconds'] if r else None,trace_sha256=r['trace_sha256'] if r else ''))
        out['subdivision_summary.csv'].append(dict(base,onset_adjacent_panels=r['onset_adjacent_panels'] if r else None,
            terminal_panels=r['terminal_panels'] if r else None,error_fraction_private=bool(r)))
        out['error_estimate_summary.csv'].append(dict(base,reported_bounds_met=r['reported_bounds_met'] if r else None,
            reported_error_exceeds_gate=(r['reported_error']>d.GATE) if r and r['reported_error'] is not None else None,exact_errors_private=bool(r)))
        out['reference_comparison.csv'].append(dict(base,**{k:c.get(k) for k in ('reference_within_gate','piecewise_within_gate','anchor_match','delta_exceeds_gate','reference_error_decreased','extra_work','trace_changed')},exact_differences_private=bool(r)))
    return out


def recommendation(classification,reason):
    if classification=='A':return 'Separately govern a bounded onset-only comparator convergence/stopping repair.'
    if classification=='B':return 'Separately govern a bounded agreement-contract review distinguishing stable quadrature bias from unjustified verifier requirements.'
    if classification=='C':return 'Separately govern a bounded adaptive stopping/runtime repair.'
    if classification=='D':return 'Separately govern a narrow retained-authority integrity review before any numerical execution.'
    return 'Separately govern a review of the retained terminal subdivision and error evidence from this stopped refinement sequence to identify the specific missing convergence evidence; do not rerun or repair the comparator automatically.'


def close(folder,evidence,levels,hashes,comparisons,authority,retained,reference,valid,reason,timed_out,controls,journal_head,access):
    classification,readiness,why=d.classify(levels,reference,authority_invalid=reason=='authority_invalid',execution_invalid=not valid)
    completed=sum(x['complete'] for x in levels);status='invalid' if not valid else 'complete' if completed==6 else 'partial'
    put(folder/'local/private_index.json',dict(files=evidence.files));index_hash=v.sha(folder/'local/private_index.json')
    records={
      'retained_authority.json':dict(schema_version=1,**retained),
      'refinement_protocol.json':dict(schema_version=1,tolerances=list(d.TOLERANCES),limit=d.LIMIT,gate=d.GATE,stability_span=d.GATE/10,per_level_seconds=600,total_seconds=3600,candidate='constant_width',no_extra_boundaries=True),
      'timeout_summary.json':dict(schema_version=1,timed_out=timed_out,failed_level=len(levels)-1 if levels and not levels[-1]['complete'] else None,reason=reason,completed_levels=completed,later_levels_unavailable=6-len(levels)),
      'classification.json':dict(schema_version=1,classification=classification,readiness=readiness,reason=why,qualified_B=classification=='B',execution_valid=valid,recommendation=recommendation(classification,why)),
      'qc.json':dict(schema_version=1,status=status,execution_valid=valid,classification=classification,readiness=readiness,candidate='constant_width',levels_attempted=len(levels),levels_completed=completed,
        states_opened=access['states_opened'],edges_opened=access['edges_opened'],exposure_uncertain=access['uncertain'],journal_head=journal_head,private_index_sha256=index_hash,synthetic_controls_passed=controls)}
    for n,rows in csv_rows(levels,hashes,comparisons).items():
        f=io.StringIO(newline='');w=csv.DictWriter(f,fieldnames=CSV_SCHEMAS[n],lineterminator='\n');w.writeheader();w.writerows(rows);v.atomic(folder/n,f.getvalue().encode(),raw=True)
    for n,value in records.items():put(folder/n,value)
    put(folder/'manifest.json',dict(schema_version=1,status=status,outputs={n:v.sha(folder/n) for n in NAMES},authority=authority,private_index_sha256=index_hash))
    publication_check(folder)
    return records['qc.json']


def access_summary(records):
    attempts=[];opens=[];authorized=False;active=None;next_level=0;terminal=False
    for r in records:
        action=r['action'];p=r['payload']
        if action=='authorized':
            if authorized or attempts:raise ValueError('duplicate_authorization')
            if set(p)!={'state','edge','candidate'}:raise ValueError('authorization_schema')
            d.guard(p['state'],p['edge'],p['candidate']);authorized=True
        elif action in ('access_attempt','access_materialized'):
            if not authorized or active is not None or terminal:raise ValueError('access_stage')
            if set(p)!={'product','state','edge','candidate'}:raise ValueError('access_schema')
            d.guard(p['state'],p['edge'],p['candidate']);product=p['product']
            if product not in ('canonical','prepared'):raise ValueError('product')
            if action=='access_attempt':
                if product in attempts:raise ValueError('duplicate_attempt')
                attempts.append(product)
            else:
                if product not in attempts or product in opens:raise ValueError('unmatched_receipt')
                opens.append(product)
        elif action=='level_started':
            if set(p)!={'level','tolerance'} or terminal or active is not None or set(opens)!={'canonical','prepared'}:raise ValueError('level_start_stage')
            if type(p['level']) is not int or p['level']!=next_level or not 0<=next_level<6 or p['tolerance']!=d.TOLERANCES[next_level]:raise ValueError('level_start_sequence')
            active=next_level
        elif action=='level_finished':
            if set(p)!={'level','complete','warning','exhausted'} or active is None or p['level']!=active:raise ValueError('level_finish_stage')
            if any(type(p[k]) is not bool for k in ('complete','warning','exhausted')):raise ValueError('level_finish_type')
            if p['complete'] and (p['warning'] or p['exhausted']):raise ValueError('false_completion')
            terminal=not p['complete'];active=None;next_level+=1
        else:raise ValueError('unknown_journal_event')
    return dict(states_opened=int(bool(opens)),edges_opened=int(bool(opens)),uncertain=attempts!=opens)


def publication_check(folder=OUT):
    records={n:v.load(folder/n) for n in JSON_SCHEMAS}
    for n,r in records.items():
        if set(r)!=JSON_SCHEMAS[n] or r['schema_version']!=1:raise ValueError('json_schema')
    m=records['manifest.json'];q=records['qc.json'];c=records['classification.json'];p=records['refinement_protocol.json'];t=records['timeout_summary.json']
    if set(m['outputs'])!=set(NAMES) or m['status']!=q['status'] or q['status'] not in ('complete','partial','invalid'):raise ValueError('manifest_schema')
    if p['tolerances']!=list(d.TOLERANCES) or p['limit']!=1000 or p['gate']!=1e-10 or not p['no_extra_boundaries']:raise ValueError('contract_changed')
    if c['classification'] not in 'ABCDEH' or c['classification']!=q['classification'] or c['readiness']!=q['readiness'] or c['execution_valid']!=q['execution_valid']:raise ValueError('classification_cross_file')
    if not 0<=q['levels_completed']<=q['levels_attempted']<=6 or q['levels_completed']!=t['completed_levels']:raise ValueError('level_counts')
    if q['execution_valid']!=(q['status']!='invalid') or (q['status']=='complete')!=(q['levels_completed']==6 and q['execution_valid']):raise ValueError('status')
    if q['status']=='complete' and (not records['retained_authority.json']['reference_eligible'] or not records['retained_authority.json']['selected_serialization_verified'] or (q['states_opened'],q['edges_opened'])!=(1,1) or q['exposure_uncertain'] or not q['synthetic_controls_passed']):raise ValueError('complete_authority_missing')
    if c['classification'] in 'AB' and (q['status']!='complete' or not q['synthetic_controls_passed']):raise ValueError('false_acceptance')
    if c['classification']=='B' and (c['readiness']!=4 or c['qualified_B'] is not True):raise ValueError('qualified_B')
    if q['private_index_sha256']!=m['private_index_sha256'] or v.sha(folder/'local/private_index.json')!=q['private_index_sha256']:raise ValueError('private_index')
    idx=v.load(folder/'local/private_index.json')['files']
    for n,h in idx.items():
        if Path(n).name!=n or v.sha(folder/'local'/n)!=h:raise ValueError('private_file_hash')
    rows_by_name={}
    for n,h in m['outputs'].items():
        if v.sha(folder/n)!=h:raise ValueError('output_hash')
        if n in CSV_SCHEMAS:
            with (folder/n).open(newline='') as f:r=csv.DictReader(f);rows=list(r)
            if tuple(r.fieldnames)!=CSV_SCHEMAS[n] or len(rows)!=6 or [x['level'] for x in rows]!=list(map(str,range(6))):raise ValueError('csv_schema')
            rows_by_name[n]=rows
        text=(folder/n).read_text()
        if any(s in text for s in ('/Users/','/private/','"carrier"','"defenders"','"traceback"')):raise ValueError('privacy')
    results=rows_by_name['refinement_results.csv']
    if sum(x['status']=='complete' for x in results)!=q['levels_completed'] or sum(x['status']!='unavailable' for x in results)!=q['levels_attempted']:raise ValueError('row_counts')
    for i,row in enumerate(results):
        if row['status'] not in ('complete','partial','unavailable') or (i>=q['levels_attempted'])!=(row['status']=='unavailable') or (i<q['levels_completed'])!=(row['status']=='complete'):raise ValueError('status_prefix')
        if float(row['tolerance'])!=d.TOLERANCES[i]:raise ValueError('row_tolerance')
        for other in rows_by_name.values():
            if other[i]['status']!=row['status'] or other[i]['evidence_sha256']!=row['evidence_sha256']:raise ValueError('row_cross_file')
        if row['status']=='complete' and (row['normal_return']!='True' or row['warning']!='False' or row['exhausted']!='False'):raise ValueError('false_normal')
    private_levels=[]
    for name in idx:
        if re.fullmatch(r'[0-9]{6}_level\.json',name):private_levels.append(v.load(folder/'local'/name))
    if len(private_levels)!=q['levels_attempted']:raise ValueError('private_level_count')
    for row,level in zip(results,private_levels):
        if int(row['neval'])!=level['neval'] or int(row['terminal_subintervals'])!=level['terminal_panels'] or int(row['subdivision_operations'])!=level['subdivisions'] or row['trace_sha256']!=level['trace_sha256']:
            raise ValueError('private_count_cross_file')
        if any(other['status']!=row['status'] for other in (rows_by_name[n][int(row['level'])] for n in CSV_SCHEMAS)):raise ValueError('private_status')
    references=[v.load(folder/'local'/name) for name in idx if re.fullmatch(r'[0-9]{6}_reference\.json',name)]
    if private_levels and len(references)!=1:raise ValueError('missing_private_reference')
    if references:
        expected=d.classify(private_levels,references[0]['reference'],authority_invalid=t['reason']=='authority_invalid',execution_invalid=not q['execution_valid'])
        if expected[:2]!=(c['classification'],c['readiness']):raise ValueError('derived_classification')
        for i,level in enumerate(private_levels):
            expected_comp=d.compare(level,private_levels[i-1] if i else None,references[0]['reference'],references[0]['bounds'],references[0]['anchor'])
            row=rows_by_name['reference_comparison.csv'][i]
            for key in ('reference_within_gate','piecewise_within_gate','anchor_match','delta_exceeds_gate','reference_error_decreased','extra_work','trace_changed'):
                if row[key] != ('' if expected_comp[key] is None else str(expected_comp[key])):raise ValueError('comparison_flag_mismatch')
        if private_levels and private_levels[0]['complete']:
            anchor=d.compare(private_levels[0],None,references[0]['reference'],references[0]['bounds'],references[0]['anchor'])
            if q['levels_attempted']>1 and (not anchor['anchor_match'] or anchor['reference_within_gate'] or anchor['piecewise_within_gate']):raise ValueError('anchor_bypass')
    for name,h in m['authority'].get('sources',{}).items():
        if v.sha(ROOT/name)!=h:raise ValueError('implementation_hash')
    if (folder/'local/journal.jsonl').exists():
        journal,head=read_journal(folder/'local/journal.jsonl',expected_head=q['journal_head']);a=access_summary(journal)
        if (a['states_opened'],a['edges_opened'],a['uncertain'])!=(q['states_opened'],q['edges_opened'],q['exposure_uncertain']):raise ValueError('access_cross_file')
    elif q['states_opened'] or q['edges_opened'] or not q['exposure_uncertain']:raise ValueError('missing_journal')
    return True


def diagnose():
    local=OUT/'local';local.mkdir(parents=True,exist_ok=True);put(local/'attempt.marker',dict(session='14ao',exclusive=True))
    budget=d.Budget();e=Evidence(local);levels=[];hashes=[];comparisons=[];authority={};journal=None;valid=True;reason=None;timed=False;controls=False;reference=0.;active=None
    retained=dict(reference_eligible=False,selected_serialization_verified=False,onset_count=None,input_hashes=INPUTS,retained_hashes={'14am_manifest':AM_HASH,'14an_manifest':AN_HASH})
    try:
        authority=preflight();index=retained_index();retained['reference_eligible']=True
        with budget.operation():control=d.synthetic_controls()
        e.save('synthetic_controls',control);controls=all(x['passed'] for x in control)
        journal=Journal(local/'journal.jsonl');journal.append('authorized',state=4,edge=7,candidate='constant_width')
        reference,anchor,bounds,rhashes=reference_values(index);retained['retained_hashes'].update(rhashes)
        e.save('reference',dict(reference=reference,anchor=anchor,bounds=bounds))
        row=access_edge(journal,e);retained['selected_serialization_verified']=True
        partitions,onset_hashes=retained_onsets(index);retained['onset_count']=len(partitions)-2
        retained['retained_hashes']['onset_records']=onset_hashes;e.save('onsets',dict(partitions=partitions))
        field=CarrierOriginField('constant_width');b=np.asarray(row['carrier']);end=np.asarray(row['receiver']);ds=np.asarray(row['defenders'])
        def function(t):return field.individual_values(b,ds,b[None,:]+np.asarray(t)[:,None]*(end-b)[None,:])
        for i,tol in enumerate(d.TOLERANCES):
            active=i;journal.append('level_started',level=i,tolerance=tol)
            def sink(label,data):e.save(label,data)
            try:level=d.run_level(function,partitions,tol,budget,sink)
            except BaseException as exc:
                if hasattr(exc,'level_partial'):
                    level=exc.level_partial;levels.append(level);comparisons.append(d.compare(level,None,reference,bounds,anchor));hashes.append(e.save('level',level))
                raise
            levels.append(level);comp=d.compare(level,levels[-2] if len(levels)>1 else None,reference,bounds,anchor);comparisons.append(comp)
            hashes.append(e.save('level',level));e.save('comparison',comp)
            journal.append('level_finished',level=i,complete=level['complete'],warning=level['warnings'],exhausted=level['exhausted'])
            if not level['complete']:reason='warning_or_exhaustion';break
            if i==0 and (not comp['anchor_match'] or comp['reference_within_gate'] or comp['piecewise_within_gate']):reason='anchor_not_reproduced';break
    except BaseException as exc:
        timed=isinstance(exc,d.DiagnosticTimeout)
        if isinstance(exc,d.AuthorityError):reason='authority_invalid';valid=False
        elif isinstance(exc,d.MissingAuthority):reason='missing_authority'
        elif timed:reason='timeout'
        else:reason='execution_failure';valid=False
        put(local/'emergency.json',dict(exception=type(exc).__name__,message=str(exc),traceback=traceback.format_exc(),level=active,reason=reason,exposure_uncertain=True))
        e.files['emergency.json']=v.sha(local/'emergency.json')
    finally:
        if journal is not None:journal.close()
    try:
        if (local/'journal.jsonl').exists():
            records,head=read_journal(local/'journal.jsonl');access=access_summary(records);e.files['journal.jsonl']=v.sha(local/'journal.jsonl')
        else:head=None;access=dict(states_opened=0,edges_opened=0,uncertain=True)
        result=close(OUT,e,levels,hashes,comparisons,authority,retained,reference,valid,reason,timed,controls,head,access)
    except BaseException as exc:
        put(local/'publication_emergency.json',dict(exception=type(exc).__name__,traceback=traceback.format_exc(),original_reason=reason,level=active,accepted=False,exposure_uncertain=True));raise
    print(v.canonical(result).decode().strip())

def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=('preflight','diagnose','publication-check'));cmd=p.parse_args().command
    if cmd=='preflight':print(v.canonical(preflight()).decode().strip())
    elif cmd=='diagnose':diagnose()
    else:print('publication-check:',publication_check())
if __name__=='__main__':main()
