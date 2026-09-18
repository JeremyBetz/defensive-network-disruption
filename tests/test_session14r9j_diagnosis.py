import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

from defensive_network_disruption.geometry import r9j_diagnosis as d
from defensive_network_disruption.validation import r9j_evidence as e
from defensive_network_disruption.data.representation_projection import ALIASES

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('r9j_runner',ROOT/'scripts/session_14r9j_r9i_blocker_diagnosis.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)


class DiagnosticTests(unittest.TestCase):
    def test_selective_receivers_and_skipped_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp).resolve()/'prepared'
            row={'alias':ALIASES[0],'carrier':[0.,0.],'receivers':['FORBIDDEN']*7+[[8.,0.],{'forbidden':'geometry'}],
                 'defenders':[[3.,1.]]}
            p.write_text('NEVER_DECODE\n'*4+json.dumps(row)+'\nNEVER_DECODE\n')
            result=runner.selected_edge(p,{'state':'4','edges':['7']})
            self.assertEqual(result['receiver'],(8.,0.))
            self.assertNotIn('receivers',result)
            with self.assertRaises(PermissionError):runner.selected_edge(p,{'state':'4','edges':['6']})

    def test_unmodified_route_observation(self):
        row={'alias':'synthetic_only','carrier':(0.,0.),'receiver':(8.,0.),'defenders':((3.,1.),)}
        saved=[]
        reproduced,obs,failure=d.reproduce('constant_width',row,ROOT,lambda k,v:saved.append((k,v)),d.Budget(60,30))
        self.assertFalse(reproduced);self.assertIsNone(failure)
        self.assertEqual(obs.calls['controlled'],1);self.assertEqual(obs.calls['structure'],2)
        self.assertEqual({x['stage'] for x in obs.integrals},{'strict_piecewise','repeat_piecewise','onset_adaptive'})
        self.assertTrue(obs.quad);self.assertTrue(obs.pieces)
        for _, value in saved:e.canonical(value)

    def test_forwarding_equals_historical_single_edge_boundary(self):
        spec=importlib.util.spec_from_file_location('r9e_for_test',ROOT/'scripts/session_14r9e_empirical_execution.py')
        base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
        class Progress:
            def call_start(self,*a):pass
            def call_complete(self):pass
            def numerical_stage(self,**kw):pass
        row={'alias':'synthetic_only','carrier':(0.,0.),'receiver':(0.,0.),'defenders':((3.,1.),)}
        calls=[];original=d.route.evaluate_edge
        def observed(*args,**kw):
            calls.append((args,{k:v for k,v in kw.items() if k!='record'}))
            return original(*args,**kw)
        with mock.patch.object(base,'PROGRESS',Progress()),mock.patch.object(base,'evaluate_edge',observed):
            base.calculate_edge('constant_width',row['carrier'],row['receiver'],row['defenders'],row['alias'],4,7)
        with mock.patch.object(d.route,'evaluate_edge',observed):
            d.reproduce('constant_width',row,ROOT,lambda *a:None,d.Budget(60,30))
        self.assertEqual(calls[0],calls[1])

    def test_timeout_restores_timer(self):
        import signal,time
        with self.assertRaises(d.DiagnosticTimeout):
            with d.Budget(1,.01).limit():time.sleep(.1)
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL)[0],0.)

    def test_import_failure_and_marker_collision(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp).resolve()
            def unavailable(_):raise ImportError('synthetic_package_unavailable')
            with self.assertRaises(ImportError):runner.entry(folder,unavailable)
            original=(folder/'local/outer_emergency.json').read_bytes()
            self.assertIn('ImportError',e.load(folder/'local/outer_emergency.json')['traceback'])
            with self.assertRaises(FileExistsError):runner.entry(folder,lambda _:None)
            self.assertEqual(original,(folder/'local/outer_emergency.json').read_bytes())

    def test_original_exception_survives_emergency_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp).resolve();original=runner.bootstrap_write
            def writer(path,value):
                if Path(path).name=='outer_emergency.json':raise OSError('emergency_unavailable')
                original(path,value)
            with mock.patch.object(runner,'bootstrap_write',writer):
                with self.assertRaisesRegex(RuntimeError,'original'):
                    runner.entry(folder,lambda _:(_ for _ in ()).throw(RuntimeError('original')))

    def test_entry_success_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp).resolve()
            self.assertEqual(runner.entry(folder,lambda _: {'synthetic':True}),{'synthetic':True})
            with self.assertRaises(FileExistsError):runner.entry(folder,lambda _:None)

    def test_unsupported_serialization_blocks(self):
        with self.assertRaises(TypeError):d.primitive(object())
        with self.assertRaises(ValueError):d.primitive(float('nan'))

    def test_relative_difference_unavailable_only_at_zero_scale(self):
        self.assertIsNone(d.pairwise_differences({'a':0.,'b':0.})['a_vs_b']['relative'])
        result=d.pairwise_differences({'a':1.,'b':2.})['a_vs_b']
        self.assertEqual(result,{'absolute':1.,'relative':.5})

    def test_package_complete_partial_invalid_and_tampering(self):
        for status in ('complete','partial','invalid'):
            with self.subTest(status=status),tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp).resolve();e.put(folder/'local/test.json',{'synthetic':True})
                qc=dict(status=status,execution_valid=status!='invalid',numerical='NF',publication='PD',readiness=4,
                        states_reopened=0,edges_reopened=0,exposure_uncertain=False)
                e.close(folder,e.empty_public(),{},qc,{})
                self.assertEqual(e.publication_check(folder)['artifacts'],13)
                (folder/'authority.json').write_text('{}\n')
                with self.assertRaises(ValueError):e.publication_check(folder)

    def test_failed_publication_does_not_recreate_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp).resolve();e.put(folder/'local/test.json',{'synthetic':True})
            qc=dict(status='partial',execution_valid=True,numerical='NF',publication='PD',readiness=4,
                    states_reopened=0,edges_reopened=0,exposure_uncertain=False)
            e.close(folder,e.empty_public(),{},qc,{})
            (folder/'independent_reference.json').unlink()
            with self.assertRaises((ValueError,FileNotFoundError)):e.publication_check(folder)
            self.assertFalse((folder/'independent_reference.json').exists())


if __name__=='__main__':unittest.main()
