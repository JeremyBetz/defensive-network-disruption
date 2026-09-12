import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from defensive_network_disruption.validation.r5_persistence import (
    Journal, Progress, Launch, durable_write, read_journal, receipts, view,
    validate_persisted, CANDIDATES,
)
from defensive_network_disruption.validation.state_lifecycle import LifecycleError
from defensive_network_disruption.validation.launch_enforcement import (
    EnvironmentObservation, PrerequisiteExpectation, LaunchError, sha256_file,
)
from defensive_network_disruption.validation.r3_launch import test_record


def setup_progress(directory):
    journal=Journal(directory/'journal.jsonl'); p=Progress(journal)
    p.transition('authorize_access')
    p.transition('discover_state','s',('a','b'))
    for i,(state,edge) in enumerate((('s',None),('s','a'),('s','b'))):
        journal.append('access_attempt',attempt=str(i),state=state,edge=edge)
        journal.append('access_opened',attempt=str(i))
    p.transition('open_state','s')
    p.transition('open_edge','s','a');p.transition('open_edge','s','b')
    p.transition('prepare_state','s')
    return journal,p


def finish(p):
    p.transition('start_state_evaluation','s')
    for candidate in CANDIDATES:
        for edge in ('a','b'):
            p.call_start('s',edge,candidate); p.call_complete()
    p.transition('complete_state','s')


def publish(directory,journal,p,mode):
    v=view(journal.path,p.core.snapshot(),mode,expected_head=journal.previous)
    durable_write(directory/'lifecycle_summary.json',v)
    for name in ('qc.json','evidence.json'):
        durable_write(directory/name,dict(schema_version=1,status=p.core.status,progress_authority=v))
    durable_write(directory/'manifest.json',dict(schema_version=1,status=p.core.status,progress_authority=v,
        outputs={name:sha256_file(directory/name) for name in ('qc.json','evidence.json','lifecycle_summary.json')}))
    return validate_persisted(directory,journal.path)


class Session14R5EnforcementTests(unittest.TestCase):
    def test_geometric_edges_and_calls_success(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).resolve();j,p=setup_progress(root);finish(p);p.transition('succeed')
            result=publish(root,j,p,'empirical_success');j.close()
            self.assertEqual(result['candidate_calls'],dict(started=6,completed=6))
            self.assertEqual(result['snapshot']['counters']['edges_completed'],2)
            self.assertEqual(result['access']['edges_opened'],2)

    def test_preparation_regression_and_partial_failure(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).resolve();j,p=setup_progress(root)
            try: raise RuntimeError('synthetic preparation failure')
            except RuntimeError as exc: capture=p.failure('prepare',exc)
            c=capture['terminal']['counters']
            self.assertEqual((c['states_prepared'],c['states_evaluation_started'],c['states_completed']),(1,0,0))
            self.assertEqual(publish(root,j,p,'empirical_failure')['access']['states_opened'],1);j.close()

    def test_candidate_major_active_and_between_call_failures(self):
        for candidate in CANDIDATES:
            for active in (False,True):
                with self.subTest(candidate=candidate,active=active),tempfile.TemporaryDirectory() as d:
                    root=Path(d).resolve();j,p=setup_progress(root);p.transition('start_state_evaluation','s')
                    for c in CANDIDATES:
                        if c==candidate: break
                        for edge in ('a','b'):p.call_start('s',edge,c);p.call_complete()
                    p.call_start('s','a',candidate)
                    if not active:p.call_complete()
                    try:raise RuntimeError('injected')
                    except RuntimeError as exc:capture=p.failure('candidate',exc)
                    self.assertEqual(capture['terminal']['counters']['states_completed'],0)
                    publish(root,j,p,'empirical_failure');j.close()

    def test_processing_complete_publication_failure(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).resolve();j,p=setup_progress(root);finish(p)
            try:raise OSError('publication failed')
            except OSError as exc:capture=p.failure('publication_validation',exc)
            self.assertEqual(capture['terminal']['counters']['edges_completed'],2)
            publish(root,j,p,'empirical_failure');j.close()

    def test_publication_transaction_failure_after_processing_success(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).resolve();j,p=setup_progress(root);finish(p);p.transition('succeed')
            capture=p.failure('publication_validation',OSError('synthetic write failure'))
            self.assertEqual(capture['pre_failure']['status'],'success')
            self.assertEqual(capture['terminal']['status'],'failure')
            self.assertEqual(capture['terminal']['counters']['states_completed'],1)
            publish(root,j,p,'empirical_failure');j.close()

    def test_subprocess_interruption_preserves_synced_receipt(self):
        import subprocess,sys
        with tempfile.TemporaryDirectory() as d:
            path=Path(d).resolve()/'journal'
            code="""import os,sys
from pathlib import Path
from defensive_network_disruption.validation.r5_persistence import Journal
j=Journal(Path(sys.argv[1]))
j.append('access_attempt',attempt='0',state='s',edge=None)
j.append('access_opened',attempt='0')
os._exit(7)
"""
            result=subprocess.run([sys.executable,'-c',code,str(path)])
            self.assertEqual(result.returncode,7)
            access=receipts(read_journal(path)[0])
            self.assertEqual(access['states_opened'],1)
            self.assertEqual(access['states_with_unresolved_edge_exposure'],1)

    def test_concurrent_marker_has_one_winner(self):
        from concurrent.futures import ThreadPoolExecutor
        with tempfile.TemporaryDirectory() as d:
            path=Path(d).resolve()/'marker'
            def attempt():
                try:durable_write(path,{'reserved':True});return True
                except FileExistsError:return False
            with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda _:attempt(),range(2)))
            self.assertEqual(sum(results),1)

    def test_cross_file_mutations_are_rejected_by_persisted_validator(self):
        mutations=(('qc.json','status'),('manifest.json','status'),('evidence.json','status'),
                   ('qc.json','snapshot'),('evidence.json','access'),('manifest.json','journal_sha256'),
                   ('qc.json','snapshot_sha256'),('evidence.json','mode'),
                   ('manifest.json','candidate_calls'),('qc.json','lifecycle_initialized'))
        for name,key in mutations:
            with self.subTest(name=name,key=key),tempfile.TemporaryDirectory() as d:
                root=Path(d).resolve();j,p=setup_progress(root);p.failure('preparation',RuntimeError('synthetic'))
                publish(root,j,p,'empirical_failure')
                record=json.loads((root/name).read_text())
                if key=='status':record[key]='success'
                else:record['progress_authority'][key]=None
                (root/name).write_text(json.dumps(record))
                with self.assertRaises(LifecycleError):validate_persisted(root,j.path)
                j.close()

    def test_missing_persisted_evidence_is_not_reconstructed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).resolve();j,p=setup_progress(root);p.failure('preparation',RuntimeError())
            publish(root,j,p,'empirical_failure');(root/'evidence.json').unlink()
            with self.assertRaises(FileNotFoundError):validate_persisted(root,j.path)
            j.close()

    def test_preinitialization_rejects_nonempty_access_history(self):
        with tempfile.TemporaryDirectory() as d:
            j=Journal(Path(d).resolve()/'j');j.append('access_attempt',attempt='0',state='s',edge=None)
            with self.assertRaisesRegex(LifecycleError,'forged_preinitialization'):
                view(j.path,None,'pre_access',expected_head=j.previous,initialized=False)
            j.close()

    def test_unresolved_access_remains_explicit(self):
        with tempfile.TemporaryDirectory() as d:
            j=Journal(Path(d).resolve()/'j');j.append('access_attempt',attempt='0',state='s',edge=None)
            records,_=read_journal(j.path)
            self.assertEqual(receipts(records)['unresolved_attempts'],1);j.close()

    def test_duplicate_reads_do_not_duplicate_unique_receipts(self):
        with tempfile.TemporaryDirectory() as d:
            j=Journal(Path(d).resolve()/'j')
            for i in range(2):
                j.append('access_attempt',attempt=str(i),state='s',edge=None)
                j.append('access_opened',attempt=str(i))
            self.assertEqual(receipts(read_journal(j.path)[0])['states_opened'],1);j.close()

    def test_journal_truncation_reset_and_interruption(self):
        for how in ('truncate','reset','partial'):
            with self.subTest(how=how),tempfile.TemporaryDirectory() as d:
                j=Journal(Path(d).resolve()/'j');j.append('attempt');j.append('authorization');head=j.previous;j.close()
                raw=j.path.read_bytes()
                j.path.write_bytes(raw.splitlines(keepends=True)[0] if how=='truncate' else b'' if how=='reset' else raw[:-2])
                with self.assertRaises(LifecycleError):read_journal(j.path,expected_head=head)

    def test_flush_sync_before_risky_callback_and_sync_failure(self):
        with tempfile.TemporaryDirectory() as d:
            j=Journal(Path(d).resolve()/'j')
            with patch('os.fsync',side_effect=OSError('injected sync failure')):
                with self.assertRaises(OSError):j.append('attempt')
            with self.assertRaises(LifecycleError):j.append('authorization')
            j.close()

    def test_exclusive_creation_and_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d).resolve()/'marker';durable_write(path,{'a':1})
            with self.assertRaises(FileExistsError):durable_write(path,{'a':2})
            link=Path(d).resolve()/'link';link.symlink_to(path)
            with self.assertRaises(PermissionError):durable_write(link,{})

    def launch(self,root,kind):
        env=EnvironmentObservation('synthetic','CPython',True,'uv-locked-project-environment','a'*64,(('numpy','locked'),('scipy','locked')))
        exp=PrerequisiteExpectation('b'*64,'c'*64,'a'*64,env.fingerprint(),('fixed','discovery'))
        calls=[];launcher=Launch(root)
        def discover():
            if kind=='startup':raise RuntimeError('startup')
            if kind=='environment':return EnvironmentObservation('synthetic','CPython',False,None,'a'*64,())
            return env
        def produce(path,expected):
            if kind=='producer':raise RuntimeError('producer')
            if kind=='missing':return
            record=test_record(expected,'Ran 1 test in 0.01s\n\nOK\n',0)
            if kind=='empty':record.update(tests_run=0,tests_passed=0)
            if kind=='digest':record['lock_sha256']='d'*64
            durable_write(path,record)
        def verify(context):
            calls.append('verify')
            if kind=='warning':warnings.warn('injected')
            if kind=='readiness':return False
            return True
        def access(context):
            calls.append('access')
            if kind=='callback':raise RuntimeError('callback')
        import warnings
        if kind=='ok':launcher.execute(discover=discover,expected=lambda _:exp,produce=produce,verify=verify,access=access)
        else:
            with self.assertRaises((RuntimeError,LaunchError,UserWarning)):
                launcher.execute(discover=discover,expected=lambda _:exp,produce=produce,verify=verify,access=access)
            record=json.loads((root/'failure.json').read_text())
            if kind in ('startup','environment','producer','missing','empty','digest'):
                self.assertEqual(calls,[]);self.assertEqual(record['access_callbacks'],0)
                self.assertFalse((root/'authorization.marker').exists())
        return launcher,calls

    def test_launch_failures_and_actual_callback_spies(self):
        for kind in ('startup','environment','producer','missing','empty','digest','warning','readiness','callback','ok'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as d:
                launcher,calls=self.launch(Path(d).resolve(),kind)
                if kind=='ok':self.assertEqual(calls,['verify','access'])
                with self.assertRaises(FileExistsError):self.launch(Path(d).resolve(),'ok')

    def test_direct_core_entry_requires_readiness_and_context(self):
        with tempfile.TemporaryDirectory() as d:
            launch=Launch(Path(d).resolve()); calls=[]
            with self.assertRaises(LaunchError):launch.core.authorize(None,None,None,None,lambda _:calls.append(1))
            self.assertEqual(calls,[])

    def test_complete_synthetic_launch_processing_and_publication(self):
        for fail in (False,True):
            with self.subTest(fail=fail),tempfile.TemporaryDirectory() as d:
                root=Path(d).resolve();env=EnvironmentObservation('synthetic','CPython',True,'uv-locked-project-environment','a'*64,(('numpy','locked'),('scipy','locked')))
                exp=PrerequisiteExpectation('b'*64,'c'*64,'a'*64,env.fingerprint(),('synthetic','discovery'))
                def produce(path,expected):durable_write(path,test_record(expected,'Ran 1 test in 0.1s\n\nOK\n',0))
                observed=[]
                def callback(context):
                    folder=root/'control';j,p=setup_progress(folder)
                    if fail:
                        p.transition('start_state_evaluation','s');p.call_start('s','a','isotropic')
                        try:raise RuntimeError('synthetic evaluation failure')
                        except RuntimeError as exc:p.failure('evaluation',exc)
                    else:finish(p);p.transition('succeed')
                    result=publish(folder,j,p,'empirical_failure' if fail else 'empirical_success')
                    observed.append(result);j.close()
                Launch(root/'launch').execute(discover=lambda:env,expected=lambda _:exp,produce=produce,verify=lambda _:True,access=callback)
                self.assertEqual(observed[0]['access']['states_opened'],1)
                self.assertEqual(observed[0]['snapshot']['status'],'failure' if fail else 'success')


if __name__=='__main__':unittest.main()
