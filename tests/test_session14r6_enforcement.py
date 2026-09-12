"""Synthetic enforcement tests for the Session 14R6 execution adapter."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from defensive_network_disruption.validation.projection_exposure import LifecycleError
from defensive_network_disruption.validation.r6_execution import (
    Journal, Launch, Progress, durable_write, exposure_summary, validate_persisted, view)
from defensive_network_disruption.validation.launch_enforcement import EnvironmentObservation,PrerequisiteExpectation
from defensive_network_disruption.validation.r3_launch import test_record


def authority(directory, edges=('0','1')):
    journal=Journal(Path(directory).resolve()/'journal.jsonl'); progress=Progress(journal)
    progress.authorize_access();progress.discover_state('state',edges)
    return journal,progress


def publish(directory,journal,progress,mode):
    root=Path(directory).resolve();current=view(journal.path,progress.core.snapshot(),mode,expected_head=journal.previous)
    records=(('lifecycle_summary.json',current),
        ('exposure_summary.json',exposure_summary(journal.path,expected_head=journal.previous)),
        ('qc.json',dict(schema_version=1,status=current['snapshot']['status'],progress_authority=current)),
        ('evidence.json',dict(schema_version=1,status=current['snapshot']['status'],progress_authority=current)))
    for name,value in records:durable_write(root/name,value)
    outputs={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n,_ in records}
    durable_write(root/'manifest.json',dict(schema_version=1,status=current['snapshot']['status'],
        progress_authority=current,outputs=outputs))
    return validate_persisted(root,journal.path)


class Session14R6EnforcementTests(unittest.TestCase):
    def test_r5_interruption_regression_preserves_both_edges(self):
        with tempfile.TemporaryDirectory() as folder:
            journal,progress=authority(folder)
            result=progress.project('state',lambda:{'receivers':((1.,2.),(3.,4.))})
            self.assertEqual(len(result['receivers']),2)
            progress.failure('after_projection',RuntimeError('injected'))
            counts=progress.core.snapshot()['counters']
            self.assertEqual((counts['edges_opened'],counts['edges_completed'],counts['unresolved_exposed_edges']),(2,0,2))
            self.assertEqual(exposure_summary(journal.path,expected_head=journal.previous)['states_opened'],1)
            publish(folder,journal,progress,'empirical_failure');journal.close()

    def test_projection_failure_opens_nothing(self):
        with tempfile.TemporaryDirectory() as folder:
            journal,progress=authority(folder,('0',))
            with self.assertRaises(RuntimeError):progress.project('state',lambda:(_ for _ in ()).throw(RuntimeError('injected')))
            counts=progress.core.snapshot()['counters']
            self.assertEqual((counts['edges_opened'],counts['unresolved_projection_attempts']),(0,0));journal.close()

    def test_unresolved_attempt_cannot_claim_zero(self):
        with tempfile.TemporaryDirectory() as folder:
            journal,progress=authority(folder,('0',));progress.begin_projection('state')
            progress.failure('receipt',RuntimeError('interrupted'))
            self.assertFalse(progress.core.snapshot()['confirmed_zero_exposure'])
            with self.assertRaisesRegex(LifecycleError,'pre_access_not_confirmed_zero'):
                view(journal.path,progress.core.snapshot(),'pre_access',expected_head=journal.previous)
            journal.close()

    def test_geometric_edge_and_field_work_are_separate(self):
        with tempfile.TemporaryDirectory() as folder:
            journal,progress=authority(folder,('0',));progress.project('state',lambda:object())
            progress.prepare_state('state');progress.start_state('state')
            for candidate in ('isotropic','expanding','constant_width'):
                progress.call_start('state','0',candidate);progress.call_complete()
            progress.complete_state('state');progress.succeed()
            counts=progress.core.snapshot()['counters']
            self.assertEqual((counts['edges_opened'],counts['edges_completed'],counts['field_evaluations_completed']),(1,1,3))
            publish(folder,journal,progress,'empirical_success');journal.close()

    def test_candidate_order_and_early_state_completion_fail(self):
        with tempfile.TemporaryDirectory() as folder:
            journal,progress=authority(folder,('0',));progress.project('state',lambda:object())
            progress.prepare_state('state');progress.start_state('state')
            with self.assertRaisesRegex(LifecycleError,'field_order'):progress.call_start('state','0','expanding')
            with self.assertRaisesRegex(LifecycleError,'invalid_state_completion'):progress.complete_state('state')
            journal.close()

    def test_cross_file_mutation_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            journal,progress=authority(folder,('0',));progress.project('state',lambda:object())
            progress.failure('stop',RuntimeError('injected'));publish(folder,journal,progress,'empirical_failure')
            path=Path(folder)/'qc.json';record=json.loads(path.read_text());record['progress_authority']['snapshot']['counters']['edges_opened']=0
            path.write_text(json.dumps(record))
            with self.assertRaises(LifecycleError):validate_persisted(Path(folder),journal.path)
            journal.close()

    def test_exclusive_marker(self):
        with tempfile.TemporaryDirectory() as folder:
            marker=Path(folder).resolve()/'marker';durable_write(marker,{'reserved':True})
            with self.assertRaises(FileExistsError):durable_write(marker,{'reserved':True})

    def test_launch_blocks_failed_prerequisite_and_reaches_valid_callback(self):
        env=EnvironmentObservation('synthetic','CPython',True,'uv-locked-project-environment','a'*64,(('numpy','locked'),('scipy','locked')))
        expected=PrerequisiteExpectation('b'*64,'c'*64,'a'*64,env.fingerprint(),('fixed','tests'))
        for failing in (True,False):
            with self.subTest(failing=failing),tempfile.TemporaryDirectory() as folder:
                root=Path(folder).resolve();calls=[]
                def produce(path,authority):
                    if failing:raise RuntimeError('producer')
                    durable_write(path,test_record(authority,'Ran 1 test in 0.01s\n\nOK\n',0))
                if failing:
                    with self.assertRaises(RuntimeError):
                        Launch(root).execute(discover=lambda:env,expected=lambda _:expected,
                            produce=produce,verify=lambda _:calls.append('verify'),access=lambda _:calls.append('access'))
                    self.assertEqual(calls,[])
                else:
                    Launch(root).execute(discover=lambda:env,expected=lambda _:expected,
                        produce=produce,verify=lambda _:True,access=lambda _:calls.append('access'))
                    self.assertEqual(calls,['access'])

    def test_no_empirical_or_scoring_route(self):
        import defensive_network_disruption.validation.r6_execution as module
        for forbidden in ('project_line','evaluate_edge','load_model','target','fit','acquire'):
            self.assertNotIn(forbidden,set(vars(module)))


if __name__=='__main__':unittest.main()
