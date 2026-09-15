"""Observed R8 journal and publication paths; all geometry is synthetic."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from defensive_network_disruption.validation import r7_execution as r7
from defensive_network_disruption.validation import numerical_failure_publication as pub


def control(folder,edges=('0',),prepare=True):
    j=r7.Journal(Path(folder).resolve()/'journal');p=r7.Progress(j);p.authorize_access()
    p.discover_state('0',edges);p.project('0',lambda:object())
    if prepare:p.prepare_state('0');p.start_state('0')
    return j,p


def finish(p,edges=('0',)):
    for c in r7.CANDIDATES:
        for e in edges:
            p.call_start('0',e,c);p.numerical_stage(stage='geometry');p.numerical_stage(stage='accepted');p.call_complete()
    p.retain_and_complete_edges('0');p.complete_state('0');p.succeed()


def package(folder,j,p,mode):
    d=Path(folder).resolve()/'package';d.mkdir()
    a=r7.view(j.path,p.core.snapshot(),mode,expected_head=j.previous)
    observed=pub.authority(j.path,j.previous)
    acceptance=pub.package(observed,accepted=mode=='empirical_success',checks={'processing':mode=='empirical_success'})
    for n in ('qc','manifest','evidence'):r7.durable_write(d/'numerical_publication'/(n+'.json'),acceptance)
    base=dict(schema_version=1,status='success' if mode=='empirical_success' else 'failure',progress_authority=a)
    r7.durable_write(d/'lifecycle_summary.json',a)
    r7.durable_write(d/'qc.json',dict(**base,stage='synthetic',exception=None if mode=='empirical_success' else 'ValueError',scientific_comparisons_available=mode=='empirical_success'))
    r7.durable_write(d/'evidence.json',base)
    r7.durable_write(d/'manifest.json',dict(**base,outputs={n:r7.sha256_file(d/n) for n in ('qc.json','evidence.json','lifecycle_summary.json')}))
    return d


class Session14R9EnforcementTests(unittest.TestCase):
    def test_full_three_candidate_success(self):
        with tempfile.TemporaryDirectory() as f:
            j,p=control(f,('0','1'));finish(p,('0','1'))
            c=p.core.snapshot()['counters'];self.assertEqual((c['edges_opened'],c['edges_completed'],c['field_evaluations_completed']),(2,2,6))
            r7.validate_persisted(package(f,j,p,'empirical_success'),j.path);j.close()

    def test_numerical_failure_preserves_exposure(self):
        with tempfile.TemporaryDirectory() as f:
            j,p=control(f,('0','1'));p.call_start('0','0','isotropic');p.numerical_stage(stage='geometry');p.numerical_stage(stage='joint_simpson')
            try:raise ValueError('synthetic failure')
            except ValueError as error:p.failure('run',error)
            c=p.core.snapshot()['counters'];self.assertEqual((c['edges_opened'],c['edges_completed'],c['unresolved_exposed_edges']),(2,0,2))
            r7.validate_persisted(package(f,j,p,'empirical_failure'),j.path);j.close()

    def test_missing_and_mismatched_actual_package(self):
        for member in ('qc.json','manifest.json','lifecycle_summary.json','evidence.json'):
            with self.subTest(member=member),tempfile.TemporaryDirectory() as f:
                j,p=control(f);finish(p);d=package(f,j,p,'empirical_success')
                v=json.loads((d/member).read_text());v['forged']=True
                if 'progress_authority' in v:v['progress_authority']['journal_sha256']='0'*64
                else:v['journal_sha256']='0'*64
                (d/member).write_text(json.dumps(v))
                with self.assertRaises(Exception):r7.validate_persisted(d,j.path)
                j.close()

    def test_failed_acceptance_blocks_success(self):
        with tempfile.TemporaryDirectory() as f:
            j,p=control(f);finish(p);d=package(f,j,p,'empirical_success')
            for n in ('qc','manifest','evidence'):
                path=d/'numerical_publication'/(n+'.json');v=json.loads(path.read_text());v['checks']['processing']=False;path.write_text(json.dumps(v))
            with self.assertRaisesRegex(Exception,'acceptance_gate'):r7.validate_persisted(d,j.path)
            j.close()

    def test_unresolved_projection_cannot_be_zero(self):
        with tempfile.TemporaryDirectory() as f:
            j=r7.Journal(Path(f).resolve()/'journal');p=r7.Progress(j);p.authorize_access();p.discover_state('0',('0','1'));p.begin_projection('0')
            self.assertFalse(p.core.snapshot()['confirmed_zero_exposure'])
            with self.assertRaises(Exception):r7.view(j.path,p.core.snapshot(),'pre_access',expected_head=j.previous)
            j.close()

    def test_projection_receipt_before_followup_failure(self):
        with tempfile.TemporaryDirectory() as f:
            j,p=control(f,('0','1'),False);self.assertEqual(p.core.snapshot()['counters']['edges_opened'],2);j.close()

    def test_diagnostic_success_cannot_close_study(self):
        with tempfile.TemporaryDirectory() as f:
            j,p=control(f)
            j.append('diagnostic_started',state='0',edge='0',candidate='constant_width')
            j.append('numerical_stage',state='0',edge='0',candidate='constant_width',detail={'stage':'geometry'})
            j.append('numerical_stage',state='0',edge='0',candidate='constant_width',detail={'stage':'accepted'})
            j.append('diagnostic_completed',state='0',edge='0',candidate='constant_width');j.append('diagnostic_success')
            with self.assertRaisesRegex(Exception,'diagnostic_route'):r7.view(j.path,p.core.snapshot(),'empirical_success',expected_head=j.previous)
            j.close()

    def test_invalid_stage_and_active_context(self):
        for detail in ({'stage':'strict_piecewise'},{'stage':'geometry','extra':1}):
            with tempfile.TemporaryDirectory() as f:
                j,p=control(f);p.call_start('0','0','isotropic');p.numerical_stage(**detail)
                with self.assertRaises(Exception):p.core.snapshot()
                j.close()

    def test_interrupted_receipt_preserves_uncertainty(self):
        with tempfile.TemporaryDirectory() as f:
            j=r7.Journal(Path(f).resolve()/'journal');p=r7.Progress(j);p.authorize_access();p.discover_state('0',('0','1'))
            original=j.append
            def append(action,**payload):
                if action=='projection_materialized':raise OSError('synthetic interruption')
                original(action,**payload)
            with patch.object(j,'append',side_effect=append),self.assertRaises(OSError):p.project('0',lambda:object())
            self.assertEqual(p.core.snapshot()['counters']['unresolved_projection_attempts'],1);j.close()

    def test_all_existing_publication_controls(self):
        from defensive_network_disruption.validation.onset_owner_acceptance import publication_controls
        records=publication_controls();self.assertTrue(all(x['passed'] for x in records))

    def test_marker_collision_and_direct_entry(self):
        from defensive_network_disruption.validation.launch_enforcement import claim_marker
        with tempfile.TemporaryDirectory() as f:
            marker=Path(f).resolve()/'marker';claim_marker(marker)
            with self.assertRaises(FileExistsError):claim_marker(marker)
        # The unchanged launch controls are separately collected by the relevant suite.
        with tempfile.TemporaryDirectory() as f:
            j=r7.Journal(Path(f).resolve()/'journal');p=r7.Progress(j)
            with self.assertRaises(Exception):p.call_start('0','0','isotropic')
            j.close()

    def test_actual_launch_callback_spies(self):
        from defensive_network_disruption.validation.launch_enforcement import EnvironmentObservation, PrerequisiteExpectation
        from defensive_network_disruption.validation.r3_launch import test_record
        good=EnvironmentObservation('3.13','CPython',True,'uv-locked-project-environment','a'*64,(('numpy','1'),('scipy','1')))
        def expected(env):return PrerequisiteExpectation('b'*64,'c'*64,'a'*64,good.fingerprint(),('-m','unittest','discover'))
        for failure in ('none','environment','producer','missing','readiness','callback'):
            with self.subTest(failure=failure),tempfile.TemporaryDirectory() as f:
                folder=Path(f).resolve();calls=[];launch=r7.Launch(folder/'launch')
                def discover():
                    if failure=='environment':raise RuntimeError('synthetic environment')
                    return good
                def produce(path,exp):
                    if failure=='producer':raise RuntimeError('synthetic producer')
                    if failure=='missing':return
                    r7.durable_write(path,test_record(exp,'Ran 1 test in 0.1s\n\nOK\n',0))
                def verify(ctx):calls.append('verify');return failure!='readiness'
                def access(ctx):
                    calls.append('access')
                    if failure=='callback':raise RuntimeError('synthetic callback')
                    j,p=control(folder);finish(p);r7.validate_persisted(package(folder,j,p,'empirical_success'),j.path);j.close()
                if failure=='none':launch.execute(discover=discover,expected=expected,produce=produce,verify=verify,access=access)
                else:
                    with self.assertRaises(Exception):launch.execute(discover=discover,expected=expected,produce=produce,verify=verify,access=access)
                    self.assertTrue((folder/'launch/failure.json').exists())
                self.assertEqual(calls,[] if failure in ('environment','producer','missing') else ['verify'] if failure=='readiness' else ['verify','access'])
                with self.assertRaises(FileExistsError):launch.execute(discover=discover,expected=expected,produce=produce,verify=verify,access=access)

    def test_empty_preaccess_failure_evidence(self):
        with tempfile.TemporaryDirectory() as f:
            folder=Path(f).resolve();j=r7.Journal(folder/'journal');j.close()
            a=r7.view(j.path,None,'pre_access',expected_head=None,initialized=False)
            self.assertEqual(r7.exposure_summary(j.path,expected_head=None)['edges_opened'],0)
            d=folder/'package';base=dict(schema_version=1,status='failure',progress_authority=a)
            r7.durable_write(d/'lifecycle_summary.json',a)
            r7.durable_write(d/'qc.json',dict(**base,stage='preaccess',exception='VerificationError',scientific_comparisons_available=False))
            r7.durable_write(d/'evidence.json',base)
            r7.durable_write(d/'manifest.json',dict(**base,outputs={n:r7.sha256_file(d/n) for n in ('qc.json','evidence.json','lifecycle_summary.json')}))
            self.assertEqual(r7.validate_persisted(d,j.path),a)
            with j.path.open('ab') as handle:handle.write(b'uncertain')
            with self.assertRaises(Exception):r7.validate_persisted(d,j.path)
