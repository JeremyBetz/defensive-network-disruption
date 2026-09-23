import copy
from dataclasses import replace
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from defensive_network_disruption.validation import checkpoint_ci_authority_v2 as v2
from defensive_network_disruption.validation import checkpoint_ci_authority as v1

ROOT=Path(__file__).resolve().parents[1]


def expectation():
    return v2.Expectation('a'*40,'b'*64,'c'*64,'d'*64,'e'*64,10,2)


def source():
    e=expectation();base=f'https://api.github.com/repos/{e.repository}/actions/runs/10'
    run={'id':10,'run_attempt':2,'head_sha':e.checkpoint_commit,'repository':{'full_name':e.repository},
         'workflow_id':e.workflow_id,'name':'CI','path':e.workflow_path,'jobs_url':base+'/attempts/2/jobs',
         'status':'completed','conclusion':'success','created_at':'2026-09-23T00:00:00Z',
         'updated_at':'2026-09-23T01:00:00Z'}
    jobs=[{'id':i,'name':name,'run_id':10,'run_attempt':2,'head_sha':e.checkpoint_commit,
           'run_url':base,'url':f'https://api.github.com/repos/{e.repository}/actions/jobs/{i}',
           'status':'completed','conclusion':'success','started_at':'2026-09-23T00:01:00Z',
           'completed_at':'2026-09-23T00:59:00Z'} for i,name in enumerate(v1.REQUIRED_JOBS,101)]
    return {'run':run,'job_pages':[{'total_count':3,'jobs':jobs}]}


def capture(path, value=None):
    value=value or source();calls=[]
    def command(args):
        calls.append(args)
        return json.dumps(value['job_pages'] if '--paginate' in args else value['run']).encode()
    result=v2.capture(path,expectation(),command=command)
    return result,calls


class ReceiptV2Tests(unittest.TestCase):
    def test_explicit_attempt_capture_and_offline_validation(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d).resolve()/'ci.json';a,calls=capture(p)
            self.assertIn('/attempts/2',calls[0][2]);self.assertIn('--slurp',calls[1])
            with patch.object(v2.subprocess,'check_output',side_effect=AssertionError('network')):
                self.assertEqual(v2.validate_receipt(p,expectation(),expected_sha256=a.receipt_sha256),a)
            self.assertEqual(a.run_attempt,2)

    def test_source_mutations_block(self):
        mutations={
          'cancelled_attempt':lambda s:s['run'].update(run_attempt=1,conclusion='cancelled'),
          'missing_attempt':lambda s:s['run'].pop('run_attempt'),
          'wrong_commit':lambda s:s['run'].update(head_sha='0'*40),
          'wrong_workflow':lambda s:s['run'].update(workflow_id=1),
          'wrong_repository':lambda s:s['run']['repository'].update(full_name='other/repo'),
          'pending':lambda s:s['run'].update(status='in_progress'),
          'failed':lambda s:s['run'].update(conclusion='failure'),
          'mixed_attempt':lambda s:s['job_pages'][0]['jobs'][0].update(run_attempt=1),
          'wrong_job_commit':lambda s:s['job_pages'][0]['jobs'][0].update(head_sha='0'*40),
          'wrong_job_url':lambda s:s['job_pages'][0]['jobs'][0].update(id=999),
          'failed_job':lambda s:s['job_pages'][0]['jobs'][0].update(conclusion='failure'),
          'cancelled_job':lambda s:s['job_pages'][0]['jobs'][0].update(conclusion='cancelled'),
          'pending_job':lambda s:s['job_pages'][0]['jobs'][0].update(status='queued'),
          'timestamp':lambda s:s['job_pages'][0]['jobs'][0].update(completed_at='bad'),
          'chronology':lambda s:s['job_pages'][0]['jobs'][0].update(completed_at='2026-09-22T00:00:00Z'),
          'missing_job':lambda s:s['job_pages'][0]['jobs'].pop(),
          'duplicate_job':lambda s:s['job_pages'][0]['jobs'].__setitem__(1,s['job_pages'][0]['jobs'][0]),
          'wrong_total':lambda s:s['job_pages'][0].update(total_count=4),
          'extra_page':lambda s:s['job_pages'].append({'total_count':3,'jobs':[]}),
          'latest_endpoint':lambda s:s['run'].update(jobs_url=s['run']['jobs_url'].replace('/attempts/2','')),
        }
        for name,mutate in mutations.items():
            with self.subTest(name=name):
                s=source();mutate(s)
                with self.assertRaises((ValueError,KeyError)):
                    v2.source_summary(s,expectation())

    def test_invalid_expectation(self):
        for changed in (replace(expectation(),run_attempt=0),replace(expectation(),run_id=True),
                        replace(expectation(),checkpoint_commit='bad')):
            with self.assertRaises(ValueError):v2.source_summary(source(),changed)

    def test_receipt_mutations_and_noncanonical_block(self):
        for key in ('schema_version','expectation','provenance_sha256','source_sha256','jobs'):
            with self.subTest(key=key),tempfile.TemporaryDirectory() as d:
                p=Path(d).resolve()/'ci.json';capture(p);r=v2.read_canonical(p);r[key]=None
                p.write_bytes(v1.canonical_bytes(r))
                with self.assertRaises((ValueError,TypeError)):
                    v2.validate_receipt(p,expectation(),expected_sha256=v2.sha(p.read_bytes()))
        with tempfile.TemporaryDirectory() as d:
            p=Path(d).resolve()/'ci.json';capture(p);p.write_text(json.dumps(v2.read_canonical(p)))
            with self.assertRaisesRegex(ValueError,'noncanonical'):
                v2.validate_receipt(p,expectation(),expected_sha256=v2.sha(p.read_bytes()))

    def test_changed_source_and_stale_head_block(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d).resolve()/'ci.json';a,_=capture(p)
            with self.assertRaises(ValueError):
                v2.validate_receipt(p,replace(expectation(),checkpoint_commit='f'*40),expected_sha256=a.receipt_sha256)
            s=v2.read_canonical(p.with_suffix('.source.json'));s['run']['run_attempt']=1
            p.with_suffix('.source.json').write_bytes(v1.canonical_bytes(s))
            with self.assertRaises(ValueError):v2.validate_receipt(p,expectation(),expected_sha256=a.receipt_sha256)

    def test_nonexistent_or_interrupted_capture_preserves_failure_and_prevents_retry(self):
        for error in (FileNotFoundError('attempt absent'),KeyboardInterrupt('interrupted')):
            with self.subTest(error=type(error).__name__),tempfile.TemporaryDirectory() as d:
                p=Path(d).resolve()/'ci.json'
                def command(args):raise error
                with self.assertRaises(type(error)):v2.capture(p,expectation(),command=command)
                self.assertFalse(p.exists());v1.FailureController(p.with_suffix('.failure')).validate()
                with self.assertRaises(FileExistsError):capture(p)

    def test_duplicate_capture_and_selection_tampering(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d).resolve()/'ci.json';a,_=capture(p)
            with self.assertRaises(FileExistsError):capture(p)
            bindings=v1.CIExpectation('a'*40,'b'*64,'c'*64,'d'*64,'e'*64)
            self.assertEqual(v2.validate_selected(p,bindings,expected_sha256=a.receipt_sha256),a)
            sel=v2.read_canonical(p.with_suffix('.selection.json'));sel['run_attempt']=1
            p.with_suffix('.selection.json').write_bytes(v1.canonical_bytes(sel))
            with self.assertRaises(ValueError):v2.validate_selected(p,bindings,expected_sha256=a.receipt_sha256)

    def test_historical_v1_remains_valid_but_v2_rejects(self):
        from test_session14r9m import receipt,expectation as old_expectation
        with tempfile.TemporaryDirectory() as d:
            p=Path(d).resolve()/'ci.json';raw=v1.canonical_bytes(receipt());p.write_bytes(raw)
            v1.validate_receipt(p,old_expectation())
            with self.assertRaises(ValueError):v2.validate_receipt(p,expectation(),expected_sha256=v2.sha(raw))
            self.assertEqual(p.read_bytes(),raw)

    def test_actual_r9ac_preflight_receipt_path_without_retained_reads(self):
        spec=importlib.util.spec_from_file_location('ci2_r9ac',ROOT/'scripts/session_14r9ac_terminal_cell_independent_bound.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        from defensive_network_disruption.validation import r9ac_authority as auth
        with tempfile.TemporaryDirectory() as d:
            module.OUT=Path(d).resolve();p=module.OUT/'local/checkpoint_ci.json';capture(p)
            def git(*args):
                if args==('status','--porcelain'):return ''
                if args==('rev-parse','v0.1.0^{}'):return auth.TAG
                return 'a'*40
            with patch.object(module,'git',git),patch.object(module,'expectation',return_value=v1.CIExpectation('a'*40,'b'*64,'c'*64,'d'*64,'e'*64)),patch.object(auth,'metadata',return_value=({}, {}, [])),patch.object(auth,'retained',side_effect=AssertionError('retained')),patch.object(module.sys,'executable',str(ROOT/'.venv/bin/python')):
                self.assertTrue(module.preflight()['preflight_valid'])
                from test_session14r9m import receipt
                p.write_bytes(v1.canonical_bytes(receipt()))
                p.with_suffix('.json.sha256').write_text(v2.sha(p.read_bytes()))
                with self.assertRaises(ValueError):module.preflight()

    def test_persisted_path_requires_v2_before_any_bound_records(self):
        from defensive_network_disruption.validation import r9ac_evidence as ev,r9ac_authority as auth
        with tempfile.TemporaryDirectory() as d:
            local=Path(d).resolve();p=local/'checkpoint_ci.json';a,_=capture(p)
            b={'schema_version':1,'kind':'retained','source_authority_sha256':auth.AUTHORITY_HASH,
               'historical_status_sha256':auth.PARTITION,'protocol_sha256':'b'*64,'runner_sha256':'c'*64,
               'checkpoint_commit':'a'*40,'ci_receipt_sha256':a.receipt_sha256}
            (local/'binding.json').write_bytes(v1.canonical_bytes(b))
            with patch.object(auth,'inventory',return_value={'uv.lock':'d'*64,'.github/workflows/ci.yml':'e'*64}):
                # A valid receipt reaches the next, deliberately absent, linear-authority record.
                with self.assertRaises(FileNotFoundError) as cm:ev.inspect_private(local)
                self.assertIn('linear_authority.json',str(cm.exception))
                from test_session14r9m import receipt
                p.write_bytes(v1.canonical_bytes(receipt()));b['ci_receipt_sha256']=v2.sha(p.read_bytes())
                (local/'binding.json').write_bytes(v1.canonical_bytes(b))
                with self.assertRaises(ValueError):ev.inspect_private(local)

    def test_hash_tampering_blocks_even_with_valid_source(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d).resolve()/'ci.json';capture(p)
            with self.assertRaisesRegex(ValueError,'receipt_hash'):
                v2.validate_receipt(p,expectation(),expected_sha256='0'*64)

    def test_capture_is_independent_of_terminal_and_provider_routes(self):
        from defensive_network_disruption.validation import r9ac_authority
        from defensive_network_disruption.geometry import r9ac_terminal_bound
        with tempfile.TemporaryDirectory() as d,patch.object(r9ac_authority,'retained',side_effect=AssertionError('retained')),patch.object(r9ac_terminal_bound,'bound',side_effect=AssertionError('bound')):
            p=Path(d).resolve()/'ci.json';a,_=capture(p)
            self.assertEqual(v2.validate_receipt(p,expectation(),expected_sha256=a.receipt_sha256),a)

    def test_future_protocol_runner_workflow_lock_bindings_block(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d).resolve()/'ci.json';a,_=capture(p)
            for field in ('protocol_sha256','runner_implementation_sha256','workflow_sha256','lockfile_sha256'):
                with self.subTest(field=field),self.assertRaises(ValueError):
                    v2.validate_receipt(p,replace(expectation(),**{field:'f'*64}),expected_sha256=a.receipt_sha256)

    def test_capture_source_failure_does_not_publish_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d).resolve()/'ci.json';s=source();s['run']['conclusion']='cancelled'
            with self.assertRaises(ValueError):capture(p,s)
            self.assertFalse(p.exists());self.assertTrue(p.with_suffix('.source.json').exists())
            v1.FailureController(p.with_suffix('.failure')).validate()

    def test_git_object_capture_cli_requires_explicit_selection(self):
        import subprocess
        process=subprocess.run([str(ROOT/'.venv/bin/python'),str(ROOT/'scripts/capture_checkpoint_ci_authority_v2.py')],capture_output=True,text=True)
        self.assertEqual(process.returncode,2)
        self.assertIn('--attempt',process.stderr);self.assertIn('--checkpoint',process.stderr)


if __name__=='__main__':unittest.main()
