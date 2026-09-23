#!/usr/bin/env python3
"""Synthetic CI2 acceptance and persisted evidence closure; no R9AC execution."""
from pathlib import Path
import argparse
import csv
import io
import json
import subprocess
import sys
import unittest

from defensive_network_disruption.validation import checkpoint_ci_authority_v2 as v2
from defensive_network_disruption.validation.checkpoint_ci_authority import durable_json,durable_bytes,canonical_bytes

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/continuous_occlusion_checkpoint_attempt_binding_repair'
START='34e44aab799075f52bfe2ea346db87139f3b8a5b'
FILES=('repair_contract.json','receipt_regression.json','negative_controls.csv','historical_preservation.json','qc.json','manifest.json')
PRESERVED=('src/defensive_network_disruption/validation/checkpoint_ci_authority.py',
           'scripts/capture_checkpoint_ci_authority.py','src/defensive_network_disruption/geometry/r9ac_terminal_bound.py',
           'src/defensive_network_disruption/validation/r9ac_run.py','uv.lock','pyproject.toml',
           'src/defensive_network_disruption/__init__.py','docs/public_api.md')


def git(*args):return subprocess.check_output(('git',*args),cwd=ROOT).decode().strip()


def historical_hash(name):
    return v2.sha(subprocess.check_output(('git','show',f'{START}:{name}'),cwd=ROOT))


def expected():
    return v2.Expectation(START,historical_hash('docs/protocols/phase_14r9ac_terminal_cell_independent_bound.md'),
       historical_hash('scripts/session_14r9ac_terminal_cell_independent_bound.py'),
       historical_hash('uv.lock'),historical_hash('.github/workflows/ci.yml'),35878553378,2)


class Results(unittest.TextTestResult):
    observations=[]
    def addSuccess(self,test):
        super().addSuccess(test);self.observations.append({'test':test.id(),'passed':True})
    def addFailure(self,test,error):
        super().addFailure(test,error);self.observations.append({'test':test.id(),'passed':False})
    def addError(self,test,error):
        super().addError(test,error);self.observations.append({'test':test.id(),'passed':False})


def inspect(local):
    receipt=local/'checkpoint_ci.json'
    selection=v2.read_canonical(receipt.with_suffix('.selection.json'))
    checked=v2.validate_receipt(receipt,expected(),expected_sha256=selection['receipt_sha256'])
    v2.require(dict(checked.jobs)=={'distribution':107278457488,'test (3.11)':107278457283,'test (3.13)':107278457058},'historical_job_ids')
    observations=v2.read_canonical(local/'controls.json')
    v2.require(observations['run']>=10 and observations['passed']==observations['run'] and observations['skipped']==0
        and len(observations['cases'])==observations['run'] and all(x['passed'] is True for x in observations['cases']), 'controls')
    preserved=v2.read_canonical(local/'preservation.json')
    v2.require(set(preserved)==set(PRESERVED),'preservation_inventory')
    for name,h in preserved.items():
        v2.require(h==historical_hash(name)==v2.sha((ROOT/name).read_bytes()),'preservation')
    binding=v2.read_canonical(local/'checkpoint.json')
    v2.require(binding['commit']!=START,'stale_capture_gate')
    from dataclasses import replace
    try:v2.validate_receipt(receipt,replace(expected(),checkpoint_commit=binding['commit']),expected_sha256=checked.receipt_sha256)
    except ValueError:pass
    else:raise ValueError('old_receipt_authorized_new_head')
    return checked,observations,preserved


def public_records(local):
    checked,controls,preserved=inspect(local)
    rows=io.StringIO();writer=csv.DictWriter(rows,fieldnames=('test','passed'),lineterminator='\n');writer.writeheader();writer.writerows(controls['cases'])
    return {
      'repair_contract.json':{'schema_version':1,'receipt_version':2,'explicit_attempt':True,'v1_unchanged':True,'r9ac_paths_wired':2,'operational_receipt_created':False},
      'receipt_regression.json':{'schema_version':1,'run_id':checked.run_id,'run_attempt':checked.run_attempt,'checkpoint_commit':checked.checkpoint_commit,'receipt_sha256':checked.receipt_sha256,'jobs':dict(checked.jobs),'offline_valid':True,'old_receipt_rejects_new_head':True},
      'negative_controls.csv':rows.getvalue().encode(),
      'historical_preservation.json':{'schema_version':1,'unchanged':preserved},
      'qc.json':{'schema_version':1,'classification':'A','readiness':1,'execution_valid':True,'states':0,'edges':0,'authority_decodings':0,'bound_invocations':0,'tests_run':controls['run'],'tests_passed':controls['passed'],'tests_skipped':controls['skipped'],'delivery_ci_required':True}}


def publication_check(folder=OUT):
    local=folder/'local';manifest=v2.read_canonical(folder/'manifest.json')
    v2.require(set(manifest)=={'schema_version','public','private','protocol_sha256'},'manifest_schema')
    v2.require(manifest['schema_version']==1 and set(manifest['public'])==set(FILES)-{'manifest.json'},'public_inventory')
    v2.require(sorted(p.name for p in folder.iterdir() if p.is_file())==sorted(FILES),'public_inventory')
    v2.require(manifest['protocol_sha256']==v2.sha((ROOT/'docs/protocols/phase_14r9ac_ci_attempt_binding_repair.md').read_bytes()),'protocol')
    actual={str(p.relative_to(local)) for p in local.rglob('*') if p.is_file()}
    v2.require(actual==set(manifest['private']),'private_inventory')
    for name,h in manifest['private'].items():
        v2.require(not Path(name).is_absolute() and '..' not in Path(name).parts,'private_path')
        v2.require(v2.sha((local/name).read_bytes())==h,'private_hash')
    for name,value in public_records(local).items():
        raw=value if isinstance(value,bytes) else canonical_bytes(value)
        v2.require((folder/name).read_bytes()==raw and v2.sha(raw)==manifest['public'][name],'public_record')
    return {'publication_valid':True,'classification':'A','readiness':1}


def audit():
    local=OUT/'local';durable_json(local/'audit.marker',{'commit':git('rev-parse','HEAD')})
    # The explicit suite consists solely of provider-free receipt tests.
    sys.path.insert(0,str(ROOT/'tests'))
    suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_checkpoint_ci_authority_v2.py')
    Results.observations=[]
    result=unittest.TextTestRunner(resultclass=Results,verbosity=2).run(suite)
    durable_json(local/'controls.json',{'run':result.testsRun,'passed':result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped),
        'skipped':len(result.skipped),'cases':Results.observations})
    if not result.wasSuccessful():raise ValueError('synthetic_acceptance_failed')
    durable_json(local/'checkpoint.json',{'commit':git('rev-parse','HEAD')})
    durable_json(local/'preservation.json',{name:historical_hash(name) for name in PRESERVED})
    records=public_records(local)
    for name,value in records.items():
        if isinstance(value,bytes):durable_bytes(OUT/name,value)
        else:durable_json(OUT/name,value)
    durable_json(OUT/'manifest.json',{'schema_version':1,'public':{n:v2.sha((OUT/n).read_bytes()) for n in records},
        'private':{str(p.relative_to(local)):v2.sha(p.read_bytes()) for p in sorted(local.rglob('*')) if p.is_file()},
        'protocol_sha256':v2.sha((ROOT/'docs/protocols/phase_14r9ac_ci_attempt_binding_repair.md').read_bytes())})
    return publication_check()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=('audit','publication-check'));args=parser.parse_args()
    try:
        answer=audit() if args.command=='audit' else publication_check()
    except BaseException as error:
        if args.command=='audit':
            from defensive_network_disruption.validation.checkpoint_ci_authority import FailureController
            failure=FailureController(OUT/'local/audit_failure')
            if not failure.original_path.exists():failure.capture(error,stage='ci2_audit',context={})
        raise
    print(json.dumps(answer,sort_keys=True))
