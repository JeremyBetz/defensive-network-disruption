"""Observed synthetic R3 callback guards; fixed prerequisite discovery suite."""
from pathlib import Path
import json
import tempfile
import unittest
import warnings

from defensive_network_disruption.validation.launch_enforcement import (
    EnvironmentObservation, PrerequisiteExpectation, LaunchError, LaunchState,
    atomic_write, canonical_json,
)
from defensive_network_disruption.validation.r3_launch import R3Launch, TEST_COMMAND, test_record


def env():
    return EnvironmentObservation('synthetic','CPython',True,'uv-locked-project-environment',
        'a'*64,(('numpy','synthetic'),('scipy','synthetic')))


def expectation(environment):
    return PrerequisiteExpectation('b'*64,'c'*64,'a'*64,env().fingerprint(),TEST_COMMAND)


def exercise(root, injection='valid'):
    runner=R3Launch(root); calls=[]
    def discover():
        if injection=='startup': raise RuntimeError('synthetic startup')
        result=env()
        if injection=='environment':
            from dataclasses import replace
            result=replace(result,in_project_environment=False)
        return result
    def produce(path, expected):
        if injection=='producer': raise RuntimeError('synthetic producer')
        if injection=='missing': return
        record=test_record(expected,'Ran 4 tests in 0.1s\n\nOK\n',0)
        if injection=='empty':record.update(tests_run=0,tests_passed=0)
        if injection=='digest':record['implementation_sha256']='d'*64
        atomic_write(path,canonical_json(record)+'\n')
    def verify(context):
        calls.append('downstream')
        if injection=='warning':warnings.warn('synthetic warning',RuntimeWarning)
        if injection=='downstream':raise RuntimeError('synthetic callback')
        if injection=='readiness':return False
        if injection=='context':context._token='invalid'
        if injection=='context_environment':context._authority='invalid'
        if injection=='context_digest':context._prerequisite='invalid'
        if injection=='access_marker':(root/'access.marker').write_text('reserved\n')
        return True
    def access(_):
        calls.append('access')
        if injection=='access_failure':raise RuntimeError('synthetic access callback')
    if injection=='launch_marker':(root/'launch.marker').write_text('reserved\n')
    error=None
    try:runner.execute(discover=discover,expected=expectation,produce=produce,verify=verify,access=access)
    except Exception as exc:error=type(exc).__name__
    return runner,calls,error


INJECTIONS=('startup','environment','producer','missing','empty','digest','warning',
    'downstream','readiness','context','context_environment','context_digest',
    'access_marker','launch_marker','access_failure')


class EnforcementTests(unittest.TestCase):
    def test_observed_injections(self):
        for injection in INJECTIONS:
            with self.subTest(injection=injection), tempfile.TemporaryDirectory() as tmp:
                runner,calls,error=exercise(Path(tmp),injection)
                self.assertIsNotNone(error)
                self.assertEqual(runner.record['status'],'failed_closed')
                self.assertTrue((Path(tmp)/'failure.json').is_file())
                if injection in ('startup','environment','producer','missing','empty','digest','launch_marker'):
                    self.assertEqual(calls,[])
                    self.assertFalse((Path(tmp)/'access.marker').exists())
                elif injection!='access_failure': self.assertEqual(calls,['downstream'])
                else:self.assertEqual(calls,['downstream','access'])
                self.assertEqual(runner.record['downstream_calls'],calls.count('downstream'))
                self.assertEqual(runner.record['access_calls'],calls.count('access'))

    def test_success_order_and_no_rerun(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);runner,calls,error=exercise(root)
            self.assertIsNone(error);self.assertEqual(calls,['downstream','access'])
            self.assertEqual(runner.core.state,LaunchState.EMPIRICAL_ACCESS_AUTHORIZED)
            again,calls,error=exercise(root)
            self.assertIsNotNone(error);self.assertEqual(calls,[])

    def test_failed_attempt_cannot_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);first,_,_=exercise(root,'startup')
            original=(root/'failure.json').read_bytes()
            second,calls,error=exercise(root)
            self.assertIsNotNone(error);self.assertEqual(calls,[])
            self.assertEqual(original,(root/'failure.json').read_bytes())

    def test_direct_entry_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            runner=R3Launch(Path(tmp));calls=[]
            with self.assertRaises(LaunchError):
                runner.core.authorize(None,env(),expectation(env()),Path(tmp)/'prerequisite.json',lambda _:calls.append(1))
            self.assertEqual(calls,[]);self.assertFalse((Path(tmp)/'access.marker').exists())

    def test_collection_and_failure_parser(self):
        for text,code in (('OK\n',0),('Ran 0 tests in 0s\nOK\n',0),
            ('Ran 1 test in 0s\nFAILED (errors=1)\n',1),('Ran 1 test in 0s\nOK (skipped=1)\n',0)):
            with self.assertRaises(LaunchError):test_record(expectation(env()),text,code)
        self.assertEqual(test_record(expectation(env()),'Ran 2 tests in 0.01s\nOK\n',0)['tests_passed'],2)

    def test_warning_failure_preserved_without_empirical_callback(self):
        with tempfile.TemporaryDirectory() as tmp:
            r,c,e=exercise(Path(tmp),'warning')
            self.assertEqual(e,'RuntimeWarning');self.assertEqual(r.record['access_calls'],0)


if __name__=='__main__':unittest.main()
