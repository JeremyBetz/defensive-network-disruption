#!/usr/bin/env python3
"""R9AD: startup protection precedes installed-package dependencies."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/'docs/protocols/phase_14r9ad_tie_boundary_mechanism_repair.md'
OUT=ROOT/'outputs/continuous_occlusion_tie_boundary_mechanism_repair'

def git(*args):return subprocess.check_output(('git',*args),cwd=ROOT,text=True).strip()
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def expectation(commit=None):
    from defensive_network_disruption.validation.checkpoint_ci_authority import CIExpectation
    return CIExpectation(commit or git('rev-parse','HEAD'),sha(PROTOCOL),sha(Path(__file__)),
        sha(ROOT/'uv.lock'),sha(ROOT/'.github/workflows/ci.yml'))

def preflight():
    from defensive_network_disruption.validation import r9ad_authority as source
    from defensive_network_disruption.validation.checkpoint_ci_authority_v2 import validate_selected
    if git('status','--porcelain'):raise RuntimeError('dirty_tree')
    head=git('rev-parse','HEAD')
    if head!=git('rev-parse','origin/main'):raise RuntimeError('tracking_mismatch')
    git('merge-base','--is-ancestor',source.START,'HEAD')
    if git('rev-parse','v0.1.0^{}')!=source.TAG:raise RuntimeError('release_tag')
    if not Path(sys.executable).absolute().is_relative_to(ROOT/'.venv'):raise RuntimeError('locked_interpreter')
    paths=git('ls-files','*r9ad*').splitlines()
    if len(paths)<9:raise RuntimeError('uncommitted_tooling')
    for path in paths:
        if (ROOT/path).read_bytes()!=subprocess.check_output(('git','show','HEAD:'+path),cwd=ROOT):
            raise RuntimeError('implementation_freshness')
    retained_files=source.verify(ROOT)
    if any((OUT/'local'/name).exists() for name in ('acceptance.marker','retained_attempt.marker','access_attempt.json','startup_failure/original_failure.json')):
        raise FileExistsError('governed_attempt_exists')
    if any(p.is_file() for p in OUT.glob('*')):raise FileExistsError('public_namespace_exists')
    receipt=OUT/'local/checkpoint_ci.json'
    ci=validate_selected(receipt,expectation(),expected_sha256=receipt.with_suffix('.json.sha256').read_text().strip())
    return {'schema_version':1,'kind':'retained','checkpoint_commit':head,'ci_receipt_sha256':ci.receipt_sha256,
            'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(Path(__file__)),
            'selected_sha256':retained_files['selected_edge.json'],
            'implementation':{p:sha(ROOT/p) for p in paths}}

def audit():
    from defensive_network_disruption.validation import r9ad_authority as source
    from defensive_network_disruption.validation.r9ad_run import execute
    permission=[False]
    with source.guard(ROOT,OUT,permission):
        binding=preflight()
        def selected():
            permission[0]=True
            try:return source.selected(ROOT,OUT/'local',True)
            finally:permission[0]=False
        return execute(ROOT,OUT,gate=lambda:binding,load_inputs=selected,binding=binding)

def startup_failure(error):
    if (OUT/'local/acceptance.marker').exists():return
    folder=OUT/'local/startup_failure';folder.mkdir(parents=True,exist_ok=True)
    def write(name,raw):
        with (folder/name).open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        fd=os.open(folder,os.O_RDONLY)
        try:os.fsync(fd)
        finally:os.close(fd)
    trace=''.join(traceback.format_exception(error)).encode();write('traceback.txt',trace)
    value={'schema_version':1,'stage':'startup_or_preflight','exception_type':type(error).__name__,
           'exception_message':str(error),'traceback_sha256':hashlib.sha256(trace).hexdigest(),
           'reopened_states':0,'reopened_edges':0}
    raw=(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
    write('original_failure.json',raw)
    write('emergency_failure.json',(json.dumps({'original_failure_sha256':hashlib.sha256(raw).hexdigest(),
        'traceback_sha256':value['traceback_sha256']},sort_keys=True,separators=(',',':'))+'\n').encode())

def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=('preflight','audit','publication-check'))
    args=parser.parse_args(argv)
    try:
        if args.command=='preflight':result=preflight()
        elif args.command=='audit':result=audit()
        else:
            from defensive_network_disruption.validation.r9ad_evidence import publication_check
            result=publication_check(OUT)
    except BaseException as error:
        if args.command=='audit':
            try:startup_failure(error)
            except BaseException:pass
        raise
    print(json.dumps(result,sort_keys=True,allow_nan=False))

if __name__=='__main__':main()
