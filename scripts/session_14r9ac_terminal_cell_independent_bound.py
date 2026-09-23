#!/usr/bin/env python3
"""Session 14R9AC: coefficient-only diagnosis; no empirical acquisition."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/continuous_occlusion_terminal_cell_independent_bound'
PROTOCOL=ROOT/'docs/protocols/phase_14r9ac_terminal_cell_independent_bound.md'


def git(*args):
    return subprocess.check_output(('git',*args),cwd=ROOT,text=True).strip()


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def expectation():
    from defensive_network_disruption.validation.checkpoint_ci_authority import CIExpectation
    return CIExpectation(git('rev-parse','HEAD'),sha(PROTOCOL),sha(Path(__file__)),
                         sha(ROOT/'uv.lock'),sha(ROOT/'.github/workflows/ci.yml'))


def preflight():
    from defensive_network_disruption.validation.r9ac_authority import verify_bindings,metadata,TAG
    from defensive_network_disruption.validation.checkpoint_ci_authority import validate_receipt
    if git('status','--porcelain'):raise RuntimeError('dirty_tree')
    if git('rev-parse','HEAD')!=git('rev-parse','origin/main'):raise RuntimeError('tracking_mismatch')
    if git('rev-parse','v0.1.0^{}')!=TAG:raise RuntimeError('release_tag')
    for path in (Path(__file__),PROTOCOL):
        git('ls-files','--error-unmatch',str(path.relative_to(ROOT)))
    if not Path(sys.executable).absolute().is_relative_to(ROOT/'.venv'):
        raise RuntimeError('locked_interpreter_required')
    verify_bindings(ROOT);metadata(ROOT)
    if (OUT/'local/attempt.marker').exists():raise FileExistsError('governed_attempt_exists')
    if any(p.is_file() for p in OUT.glob('*')):raise FileExistsError('public_namespace_exists')
    receipt=OUT/'local/checkpoint_ci.json'
    authority=validate_receipt(receipt,expectation(),expected_sha256=receipt.with_suffix('.json.sha256').read_text().strip())
    return {'head':authority.checkpoint_commit,'receipt_sha256':authority.receipt_sha256,'preflight_valid':True}


def governed():
    from defensive_network_disruption.validation.r9ac_authority import access_guard,retained,AUTHORITY_HASH,PARTITION
    from defensive_network_disruption.validation.r9ac_run import execute
    # A failed preflight has no retained decode. The startup boundary preserves it.
    with access_guard(ROOT,OUT):
        receipt=preflight()
        binding={'schema_version':1,'kind':'retained','source_authority_sha256':AUTHORITY_HASH,
                 'historical_status_sha256':PARTITION,'protocol_sha256':sha(PROTOCOL),
                 'runner_sha256':sha(Path(__file__)),'checkpoint_commit':receipt['head'],
                 'ci_receipt_sha256':receipt['receipt_sha256']}
        return execute(OUT,gate=lambda:None,load_inputs=lambda:retained(ROOT),binding=binding)


def _startup_failure(error):
    """Independent stdlib preservation even if installed-package imports fail."""
    folder=OUT/'local/startup_failure'
    if (OUT/'local/failure/original_failure.json').exists() or (OUT/'local/attempt.marker').exists():return
    folder.mkdir(parents=True,exist_ok=True)
    def write(name,raw):
        with (folder/name).open('xb') as handle:
            handle.write(raw);handle.flush();os.fsync(handle.fileno())
        fd=os.open(folder,os.O_RDONLY)
        try:os.fsync(fd)
        finally:os.close(fd)
    raw=''.join(traceback.format_exception(error)).encode()
    write('traceback.txt',raw)
    record={'schema_version':1,'exception_type':type(error).__name__,'exception_message':str(error),
            'stage':'startup_or_preflight','traceback_sha256':hashlib.sha256(raw).hexdigest(),
            'new_states':0,'new_edges':0,'reopened_states':0,'reopened_edges':0}
    encoded=(json.dumps(record,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
    write('original_failure.json',encoded)
    write('emergency_failure.json',(json.dumps({'original_failure_sha256':hashlib.sha256(encoded).hexdigest(),
        'traceback_sha256':record['traceback_sha256']},sort_keys=True,separators=(',',':'))+'\n').encode())


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=('preflight','bound','publication-check'))
    args=parser.parse_args(argv)
    try:
        if args.command=='preflight':result=preflight()
        elif args.command=='bound':result=governed()
        else:
            from defensive_network_disruption.validation.r9ac_evidence import publication_check
            result=publication_check(OUT)
    except BaseException as error:
        if args.command=='bound':
            try:_startup_failure(error)
            except BaseException:
                # Preserve the original exception; never replace it with a publisher error.
                pass
        raise
    print(json.dumps(result,sort_keys=True,allow_nan=False))


if __name__=='__main__':main()
