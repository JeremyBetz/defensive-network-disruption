#!/usr/bin/env python3
"""Session 14 synthetic-first gate and immutable closure.

The empirical stages remain unavailable until the prerequisite gate is passed.
No empirical file is opened by this prerequisite implementation.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
import numpy as np
from defensive_network_disruption.geometry.occlusion_fields import (
    CANDIDATES, CarrierOriginField, QuadratureError)

START = '9754a03abc5701934313432e815b4bc29e39ee7b'
TAG_TARGET = 'f00690c05d8c1c6db308a65bd311c43f9a8ef2fa'
OUT = Path('outputs/continuous_occlusion_hypotheses')
PROTOCOL = Path('docs/protocols/phase_14_continuous_occlusion_hypotheses.md')
CONTRACT = OUT/'candidate_contract.json'
IMPLEMENTATION = ('scripts/session_14_occlusion_fields.py',
    'src/defensive_network_disruption/geometry/occlusion_fields.py',
    'tests/test_session14_fields.py')
UNAVAILABLE = ['population_authority.json','structural_comparison.csv',
    'overlap_sensitivity.csv','smoothness_summary.json','synthetic_occlusion_field.svg']


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT).decode().strip()


def safe(relative):
    p=ROOT/relative
    if not p.resolve().is_relative_to(ROOT.resolve()) or any(x.is_symlink() for x in (p,*p.parents)):
        raise PermissionError('unsafe_path')
    return p


def digest(relative):
    return hashlib.sha256(safe(relative).read_bytes()).hexdigest()


def load(relative):
    return json.loads(safe(relative).read_text(),parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite_json')))


def encoded(value):
    return json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n'


def atomic_new(relative,value):
    if not Path(relative).is_relative_to(OUT):
        raise PermissionError('output_namespace')
    p=safe(relative)
    if p.exists():raise FileExistsError('artifact_exists')
    p.parent.mkdir(parents=True,exist_ok=True)
    temp=safe(Path(relative).with_name('.'+p.name+'.tmp'))
    with temp.open('x') as f:f.write(encoded(value))
    temp.replace(p)


def code_hashes():
    return {name:digest(name) for name in IMPLEMENTATION}


def environment():
    return {'python':platform.python_version(),'numpy':np.__version__,
            'platform':platform.platform(),'uv_lock_sha256':digest('uv.lock')}


def committed(relative):
    before=subprocess.check_output(['git','show','HEAD:'+str(relative)],cwd=ROOT)
    if hashlib.sha256(before).hexdigest()!=digest(relative):raise ValueError('uncommitted_protocol')


def historical():
    git('merge-base','--is-ancestor',START,'HEAD')
    old=set(git('ls-tree','-r','--name-only',START).splitlines())
    changed=set(git('diff','--name-only',START).splitlines())
    for name in old & changed:
        if name not in ('docs/research_log.md','references/library_review.md'):
            raise ValueError('historical_change')
        before=subprocess.check_output(['git','show',START+':'+name],cwd=ROOT)
        if not safe(name).read_bytes().startswith(before):raise ValueError('history_not_append_only')
    if git('rev-parse','v0.1.0^{}')!=TAG_TARGET:raise ValueError('release_changed')


def ledger(stage,status):
    p=safe(OUT/'local/access.jsonl');p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('a') as f:
        f.write(json.dumps({'time':datetime.now(timezone.utc).isoformat(),'stage':stage,
            'status':status,'head':git('rev-parse','HEAD'),'protocol_sha256':digest(PROTOCOL),
            'implementation':code_hashes(),'empirical_access':False})+'\n')


def preflight():
    historical();committed(PROTOCOL);committed(CONTRACT)
    if not git('check-ignore','--',str(OUT/'local/probe')):raise ValueError('local_storage_not_ignored')
    contract=load(CONTRACT)
    if contract['candidates']!=list(CANDIDATES) or contract['sigma_metres']!=2. or contract['onset_metres']!=1. or contract['half_angle_degrees']!=10.:
        raise ValueError('contract_changed')
    print('Session 14 preflight passed; no empirical files or models opened')


def fixtures():
    for i,d in enumerate(((-5,0),(5,0),(20,0),(25,0))):
        yield f'axial_{i+1}',(0,0),(20,0),(d,)
    for x in (5,10,15):
        for y in (0,1,2,5):
            yield f'lateral_x{x}_y{y}',(0,0),(20,0),((x,y),)
    for x in (4,5,5.5,6,10,20,40):
        for y in (0,2):
            yield f'depth_x{x}_y{y}',(0,0),(x,y),((5,0),)
    yield 'equal_minimum_one',(0,0),(20,0),((15,2),)
    yield 'equal_minimum_three',(0,0),(20,0),((5,2),(10,2),(15,2))
    for i,q in enumerate(((20,-10),(25,0),(20,10),(-10,5))):
        yield f'star_edge_{i+1}',(0,0),q,((5,0),(18,-9),(18,9),(-7,4))


def synthetic_checks():
    preflight()
    marker=safe(OUT/'local/synthetic.marker');marker.parent.mkdir(parents=True,exist_ok=True)
    with marker.open('x') as f:f.write(git('rev-parse','HEAD')+'\n')
    ledger('synthetic-checks','started')
    completed=[]
    for label,b,q,ds in fixtures():
        for candidate in CANDIDATES:
            try:
                result=CarrierOriginField(candidate).summarize_edge(b,q,ds)
            except QuadratureError as error:
                checks={'schema_version':1,'status':'blocked_quadrature','completed':completed,
                    'first_failure':{'fixture':label,**error.diagnostics},
                    'empirical_access':False,'implementation_sha256':code_hashes()}
                atomic_new(OUT/'synthetic_checks.json',checks)
                ledger('synthetic-checks','blocked_quadrature')
                close_blocked(checks)
                print('Session 14 stopped at the frozen synthetic quadrature gate; failure preserved')
                return 2
            completed.append({'fixture':label,'candidate':candidate,
                'maximum_agreement_error':result.maximum_agreement_error,
                'coarse_intervals':result.coarse_intervals,'fine_intervals':result.fine_intervals})
    atomic_new(OUT/'synthetic_checks.json',{'schema_version':1,'status':'quadrature_passed',
        'completed':completed,'first_failure':None,'empirical_access':False,
        'implementation_sha256':code_hashes()})
    ledger('synthetic-checks','quadrature_passed')
    print('Quadrature fixtures passed; remaining pre-access implementation gates required')
    return 0


def close_blocked(checks):
    atomic_new(OUT/'implementation_authority.json',{'schema_version':1,
        'status':'prerequisite_implementation_only','protocol_sha256':digest(PROTOCOL),
        'contract_sha256':digest(CONTRACT),'implementation_sha256':code_hashes(),
        'environment':environment(),'empirical_stage_implemented':False})
    atomic_new(OUT/'qc.json',{'schema_version':1,'status':'blocked_before_empirical_access',
        'failed_stage':'synthetic-checks','category':'quadrature_agreement_failed',
        'completed_fixture_candidate_checks':len(checks['completed']),
        'empirical_states_read':0,'models_loaded':0,'rerun':False})
    outputs={name:digest(OUT/name) for name in ('candidate_contract.json',
        'implementation_authority.json','synthetic_checks.json','qc.json')}
    atomic_new(OUT/'manifest.json',{'schema_version':1,'status':'closed_blocked',
        'start':START,'protocol_commit':git('log','-1','--format=%H','--',str(PROTOCOL)),
        'protocol_sha256':digest(PROTOCOL),'implementation_sha256':code_hashes(),
        'environment':environment(),'outputs':outputs,'unavailable':UNAVAILABLE,
        'empirical_access':False})


def unavailable_stage():
    if safe(OUT/'manifest.json').exists():
        raise RuntimeError('session_closed_no_continuation')
    raise RuntimeError('preempirical_implementation_gate_not_complete')


def publication_check():
    historical();committed(PROTOCOL);committed(CONTRACT)
    m=load(OUT/'manifest.json')
    if set(m)!={'schema_version','status','start','protocol_commit','protocol_sha256',
                'implementation_sha256','environment','outputs','unavailable','empirical_access'}:
        raise ValueError('manifest_schema')
    if m['status']!='closed_blocked' or m['start']!=START or m['empirical_access'] is not False:
        raise ValueError('manifest_status')
    if m['implementation_sha256']!=code_hashes() or m['protocol_sha256']!=digest(PROTOCOL) or m['environment']!=environment():
        raise ValueError('authority_mismatch')
    if set(m['outputs'])!={'candidate_contract.json','implementation_authority.json','synthetic_checks.json','qc.json'}:
        raise ValueError('output_allowlist')
    for name,h in m['outputs'].items():
        if digest(OUT/name)!=h:raise ValueError('closed_output_mismatch')
    if m['unavailable']!=UNAVAILABLE or any(safe(OUT/name).exists() for name in UNAVAILABLE):
        raise ValueError('unavailable_artifact_present')
    c=load(OUT/'synthetic_checks.json');q=load(OUT/'qc.json')
    if set(c)!={'schema_version','status','completed','first_failure','empirical_access','implementation_sha256'} or c['status']!='blocked_quadrature':raise ValueError('checks_schema')
    if q['completed_fixture_candidate_checks']!=len(c['completed']) or q['empirical_states_read']!=0 or q['models_loaded']!=0:raise ValueError('qc_mismatch')
    for name in m['outputs']:
        text=safe(OUT/name).read_text()
        if any(x in text for x in ('/Users/','event_id','player_id','candidate_xy','defender_xy','https://','token=')):
            raise ValueError('publication_content')
    print('Session 14 blocked-package publication checks passed; no output hashes rebound')


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=('preflight','synthetic-checks',
        'render-synthetic','prepare','analyze','publication-check'));args=p.parse_args()
    return {'preflight':preflight,'synthetic-checks':synthetic_checks,
        'render-synthetic':unavailable_stage,'prepare':unavailable_stage,
        'analyze':unavailable_stage,'publication-check':publication_check}[args.command]()


if __name__=='__main__':sys.exit(main())
