#!/usr/bin/env python3
"""R9O single-use diagnosis. Startup emergency path uses standard library only."""
from pathlib import Path
import argparse
import csv
import hashlib
import io
import json
import os
import subprocess
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/continuous_occlusion_r9n_blocker_diagnosis'
OLD=ROOT/'outputs/continuous_occlusion_empirical_retry_r9n/local'
PROTOCOL='docs/protocols/phase_14r9o_switch_equality_failure_diagnosis.md'
START='a78b32fa824226fc3ac5ac269fdea4354374801c'
JOURNAL='ab5600ba8eea54092996bb2f4c613c76a5ba331c25c2c9d2b7bb65fa6e9555db'
PREPARED='15a809060f0ba4a8cb3790011dab8008db3dad6e931c287ccb395f61ef1530b0'
NAMES=('authority.json','numerical_reproduction.json','equality_semantics.json','function_reference.json','root_switch_audit.json','synthetic_controls.csv','publication_route.json','publication_controls.csv','runtime_summary.json','qc.json','manifest.json')


def put(path,value):
    raw=(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
    write(path,raw)


def write(path,raw):
    path=Path(path)
    if any(p.is_symlink() for p in (path,*path.parents)):raise PermissionError('symlink')
    path.parent.mkdir(parents=True,exist_ok=True)
    pending=path.with_name('.'+path.name+'.pending')
    with pending.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    os.link(pending,path);pending.unlink()
    fd=os.open(path.parent,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
    return h.hexdigest()


def git(*args):return subprocess.check_output(('git',*args),cwd=ROOT,text=True).strip()


def bindings():return json.loads((ROOT/PROTOCOL).read_text().split('```json\n')[1].split('\n```')[0])


def preflight():
    if git('status','--porcelain'):raise RuntimeError('dirty_tree')
    git('merge-base','--is-ancestor',START,'HEAD')
    if git('rev-parse','v0.1.0^{}')!='f00690c05d8c1c6db308a65bd311c43f9a8ef2fa':raise RuntimeError('release')
    if Path(sys.prefix).resolve()!=(ROOT/'.venv').resolve():raise RuntimeError('project_environment')
    for p,h in bindings().items():
        if sha(ROOT/p)!=h:raise RuntimeError('inherited_hash')
    sources=git('ls-files','*r9o*',PROTOCOL).splitlines()
    for p in sources:
        if subprocess.check_output(('git','show','HEAD:'+p),cwd=ROOT)!=(ROOT/p).read_bytes():raise RuntimeError('uncommitted_tooling')
    for name in ('review.marker','numerical.marker'):
        if (OUT/'local'/name).exists():raise FileExistsError('attempt_exists')
    return dict(head=git('rev-parse','HEAD'),sources={p:sha(ROOT/p) for p in sources},protocol=sha(ROOT/PROTOCOL))


def record(status='unavailable',reason='not_executed',flags=None,counts=None,timings=None,evidence=None):
    return dict(schema_version=1,status=status,flags=flags or {},counts=counts or {},timings=timings or {},reason=reason,evidence_sha256=evidence)


def check_record(value):
    if set(value)!={'schema_version','status','flags','counts','timings','reason','evidence_sha256'}:raise ValueError('schema')
    if value['schema_version']!=1 or value['status'] not in ('complete','partial','invalid','unavailable'):raise ValueError('status')
    if any(type(x)is not bool for x in value['flags'].values()):raise ValueError('flags')
    if any(type(x)is not int or x<0 for x in value['counts'].values()):raise ValueError('counts')
    if any(type(x)not in (int,float) or x<0 or not __import__('math').isfinite(x) for x in value['timings'].values()):raise ValueError('timings')
    h=value['evidence_sha256']
    if h is not None and (len(h)!=64 or any(c not in '0123456789abcdef' for c in h)):raise ValueError('hash')


def publication_check(folder=OUT):
    folder=Path(folder);m=json.loads((folder/'manifest.json').read_text())
    if set(m)!={'schema_version','protocol','implementation','outputs','private_index_sha256'} or m['schema_version']!=1:raise ValueError('manifest_schema')
    if set(m['outputs'])!=set(NAMES)-{'manifest.json'}:raise ValueError('inventory')
    if {p.name for p in folder.iterdir() if p.is_file()}!=set(NAMES):raise ValueError('extra_file')
    for name,h in m['outputs'].items():
        if sha(folder/name)!=h:raise ValueError('output_hash')
        if name.endswith('.json') and name!='qc.json':check_record(json.loads((folder/name).read_text()))
        if name.endswith('.csv'):
            with (folder/name).open() as f:
                reader=csv.DictReader(f)
                if reader.fieldnames!=['fixture','status','passed','reason','evidence_sha256']:raise ValueError('csv_schema')
                list(reader)
    index=folder/'local/private_index.json'
    if sha(index)!=m['private_index_sha256']:raise ValueError('private_index_hash')
    for name,h in json.loads(index.read_text()).items():
        if Path(name).name!=name or sha(folder/'local'/name)!=h:raise ValueError('private_hash')
    q=json.loads((folder/'qc.json').read_text())
    if set(q)!={'schema_version','numerical','publication','readiness','execution_valid','states_reopened','edges_reopened','exposure_uncertain','reason'}:raise ValueError('qc_schema')
    if q['numerical'] not in ('NA','NB','NC','ND','NE','NF') or q['publication'] not in ('PA','PB','PC','PD') or q['readiness'] not in (1,2,3,4):raise ValueError('decision')
    if q['publication']=='PA' and not json.loads((folder/'publication_route.json').read_text())['flags'].get('all_controls_passed'):raise ValueError('false_PA')
    return {'valid':True,'files':11,'numerical':q['numerical'],'publication':q['publication']}


def selected(prepared,receipt):
    if receipt is None or receipt['state']!='5' or '8' not in receipt['edges']:raise PermissionError('selected_receipt')
    from defensive_network_disruption.validation.empirical_switch_diagnosis import project_prepared_edge
    with prepared.open('rb') as f:
        for i,line in enumerate(f):
            if i==5:return project_prepared_edge(line.decode(),8)
    raise ValueError('selected_missing')


def diagnose(folder=OUT):
    environment=preflight();folder=Path(folder);local=folder/'local';started=time.monotonic()
    put(local/'review.marker',{'reserved':True,'authorizes_access':False})
    public={n:record() for n in NAMES if n.endswith('.json') and n not in ('qc.json','manifest.json')}
    rows={'synthetic_controls.csv':[],'publication_controls.csv':[]}
    q=dict(schema_version=1,numerical='NF',publication='PD',readiness=4,execution_valid=False,states_reopened=0,edges_reopened=0,exposure_uncertain=False,reason='not_executed')
    serial=0
    def save(label,value):
        nonlocal serial
        p=local/f'{serial:06d}_{label}.json';serial+=1;put(p,value);return sha(p)
    try:
        from defensive_network_disruption.validation.r9j_linear_publication import review
        from defensive_network_disruption.geometry import r9o_diagnosis as d
        authority=review(OLD/'journal.jsonl',expected_sha256=JOURNAL,select=('5','8'))
        h=save('retained_review',authority.record())
        count=authority.records
        public['authority.json']=record('complete','reviewed_once',{'hash_valid':True,'record_count_matches':count==30881}, {'expected_records':30881,'observed_records':count},evidence=h)
        if count!=30881:raise RuntimeError('retained_journal_record_count_mismatch')
        failure=authority.failure
        if failure is None or tuple(failure[k] for k in ('state','edge','candidate'))!=('5','8','expanding') or failure['exception']!='VerificationError':raise RuntimeError('failure_context')
        rows['synthetic_controls.csv']=d.controls()
        from defensive_network_disruption.validation.r9o_terminal import controls
        rows['publication_controls.csv']=controls(local/'controls')
        passed=all(x['passed'] for x in rows['publication_controls.csv'])
        public['publication_route.json']=record('complete','linear_terminal_controls',{'all_controls_passed':passed}, {'controls':len(rows['publication_controls.csv'])})
        q['publication']='PA' if passed else 'PB';q['readiness']=3 if passed else 4
        if not passed:raise RuntimeError('publication_controls_failed')
        put(local/'numerical.marker',{'reserved':True,'authorizes_access':False})
        if sha(OLD/'prepared.jsonl')!=PREPARED:raise RuntimeError('prepared_hash')
        put(local/'access_attempt.json',{'state':5,'edge':8});q['exposure_uncertain']=True
        row=selected(OLD/'prepared.jsonl',authority.selected_receipt)
        h=save('selected_geometry',row);put(local/'access_materialized.json',{'selected_sha256':h})
        q.update(states_reopened=1,edges_reopened=1,exposure_uncertain=False)
        reproduced,captured,deadline=d.reproduce(row,ROOT,save)
        public['numerical_reproduction.json']=record('complete' if reproduced else 'partial','exact_route',{'reproduced':reproduced})
        if not reproduced:q['reason']='exact_failure_not_reproduced'
        else:
            pair=captured['pair'];a=captured['start'];b=captured['end']
            reference=d.compare_functions(d.Expanding(row['carrier'],row['receiver'],row['defenders'][pair[0]]),d.Expanding(row['carrier'],row['receiver'],row['defenders'][pair[1]]),a,b,deadline=deadline)
            h=save('reference',d.primitive(reference))
            public['function_reference.json']=record('complete','independent_expanding_bounds',{'identity':reference['identity'],'strict_disagreement':reference['strict_disagreement'],'within_tolerance':reference['within_tolerance']},{'cells':len(reference['cells'])},evidence=h)
            public['equality_semantics.json']=record('complete','exact_binary64_pair_difference_not_owner_tolerance',{'raw_equality_required':True,'provisional_uncertified':True})
            public['root_switch_audit.json']=record('partial','monotone_predicate_assumption_requires_review',{'certified_root_returned':False})
            q['reason']='bounded_evidence_requires_contract_review'
        q['execution_valid']=True
    except BaseException as error:
        save('emergency',dict(type=type(error).__name__,message=str(error),traceback=''.join(traceback.format_exception(error))))
        q['reason']=str(error) if str(error) in ('retained_journal_record_count_mismatch','failure_context','prepared_hash','publication_controls_failed') else 'diagnostic_execution_failure'
    public['runtime_summary.json']=record('complete','governed_wall_including_io',timings={'wall':time.monotonic()-started})
    for name,value in public.items():check_record(value);put(folder/name,value)
    for name,items in rows.items():
        out=io.StringIO();w=csv.DictWriter(out,fieldnames=['fixture','status','passed','reason','evidence_sha256'],lineterminator='\n');w.writeheader();w.writerows(items);write(folder/name,out.getvalue().encode())
    put(folder/'qc.json',q)
    index={p.name:sha(p) for p in local.iterdir() if p.is_file()};put(local/'private_index.json',index)
    put(folder/'manifest.json',dict(schema_version=1,protocol=environment['protocol'],implementation=environment['sources'],outputs={n:sha(folder/n) for n in NAMES if n!='manifest.json'},private_index_sha256=sha(local/'private_index.json')))
    return publication_check(folder)


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=('preflight','diagnose','publication-check'));args=p.parse_args()
    try:
        result={'preflight':preflight,'diagnose':diagnose,'publication-check':publication_check}[args.command]()
        print(json.dumps(result,sort_keys=True))
    except BaseException as error:
        if args.command=='diagnose' and not isinstance(error,FileExistsError):
            try:put(OUT/'local/outer_emergency.json',dict(exception=type(error).__name__,traceback=''.join(traceback.format_exception(error))))
            except BaseException:pass
        raise

if __name__=='__main__':main()
