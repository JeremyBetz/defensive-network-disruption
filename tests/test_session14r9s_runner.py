import copy
from fractions import Fraction as F
import importlib.util
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from defensive_network_disruption.geometry import r9s_trace as t
from defensive_network_disruption.validation import r9s_authority as authority,r9s_evidence as e,r9s_acceptance as acceptance
from defensive_network_disruption.validation.r9r_acceptance import primitive
from defensive_network_disruption.validation.r9j_evidence import put,sha,load

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('r9s_runner',ROOT/'scripts/session_14r9s_binary64_transition_trace_diagnosis.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)

def source_records():
    bound=lambda a,b:dict(lower=primitive(F(a)),upper=primitive(F(b)))
    proposal=dict(location=.5,crossing_pairs=[[0,1]])
    values=dict(raw=dict(onsets=[],envelope=dict(switches=[proposal],tie_intervals=[])),
        region=dict(raw_proposal=proposal,constrained_region=[.4,.6],structural_neighbors=[0.,1.]),
        pair={},topology=dict(classification='B',complete=True,root_intervals=[[F.from_float(.4),F.from_float(.6)]],
        cells=[dict(kind='crossing',left=F.from_float(.4),right=F.from_float(.6),derivative=dict(lo=F(1),hi=F(2)))]),
        root=[F(1,2),F(1,2)],work=dict(floats_inspected=65))
    records={k:dict(kind=authority.KINDS[k],value=primitive(v)) for k,v in values.items()}
    records['excluded']=dict(left=primitive(F(1,10)),right=primitive(F(1,5)),difference=bound(1,2),status='signed')
    records['receipt']=dict(selected_sha256='synthetic_selected',attempt_sha256='synthetic_attempt')
    records['lineage']=dict(review_sha256='synthetic_review')
    return records

class AuthorityTests(unittest.TestCase):
    def test_context_uses_retained_proof_only(self):
        sources=dict(authority.SOURCES)
        for k in ('selected','attempt','review'):sources[k]=('synthetic','synthetic','synthetic_'+k)
        from defensive_network_disruption.geometry import r9r_localization as old
        with patch.object(authority,'SOURCES',sources),patch.object(old.PairAuthority,'bounds',side_effect=AssertionError('new_reference')):
            args,ref,structures=authority.context(source_records())
            self.assertEqual((args['before'],args['after']),(-1,1));self.assertTrue(ref['one_crossing']);self.assertEqual(structures['status'],'uncertified')
    def test_missing_inconsistent_authority(self):
        sources=dict(authority.SOURCES)
        for k in ('selected','attempt','review'):sources[k]=('synthetic','synthetic','synthetic_'+k)
        for kind in ('derivative','root','count','proposal','exclusion'):
            records=source_records()
            if kind=='derivative':records['topology']['value']['cells'][0]['derivative']=None
            elif kind=='root':records['root']['value']=[primitive(F(9,10))]*2
            elif kind=='count':records['work']['value']['floats_inspected']=64
            elif kind=='proposal':records['raw']['value']['envelope']['switches']=[]
            else:records['excluded']['difference']=dict(lower=primitive(F(-1)),upper=primitive(F(1)));records['excluded']['derivative']=None
            with self.subTest(kind=kind),patch.object(authority,'SOURCES',sources),self.assertRaises(ValueError):authority.context(records)
    def test_direct_entry_and_missing_authority(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name).resolve()
            with self.assertRaises(PermissionError):runner.selected(root,None)
            with self.assertRaises(FileNotFoundError):authority.verify_sources(root)
    def test_selection_preserves_receipt_on_postmaterialization_failure(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name).resolve();local=root/'new';source=root/'synthetic';put(source/'selected.json',{'synthetic':True})
            with patch.object(runner,'ROOT',root),patch.object(authority,'SOURCES',{'selected':('synthetic','selected.json',sha(source/'selected.json'))}),patch.object(authority,'verify_sources'),patch.object(authority,'geometry_match',side_effect=ValueError('post_materialization')):
                row,records=runner.selected(local,runner.Permit(runner._SEAL))
                with self.assertRaises(ValueError):authority.geometry_match(records,row)
                self.assertTrue((local/'access_attempt.json').exists());self.assertTrue((local/'access_materialized.json').exists())
    def test_interrupted_materialization_retains_attempt(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name).resolve();local=root/'new';source=root/'synthetic';put(source/'selected.json',{'synthetic':True})
            real=runner.put
            def fail(path,value):
                if path.name=='access_materialized.json':raise OSError('interrupted')
                return real(path,value)
            with patch.object(runner,'ROOT',root),patch.object(runner,'put',fail),patch.object(authority,'SOURCES',{'selected':('synthetic','selected.json',sha(source/'selected.json'))}),patch.object(authority,'verify_sources'):
                with self.assertRaises(OSError):runner.selected(local,runner.Permit(runner._SEAL))
                self.assertTrue((local/'access_attempt.json').exists());self.assertFalse((local/'access_materialized.json').exists())

class RunnerTests(unittest.TestCase):
    def test_publication_controls_unchanged(self):
        with tempfile.TemporaryDirectory() as name:
            rows,summary=runner.publication_controls(Path(name).resolve())
            self.assertEqual(len(rows),5);self.assertTrue(all(summary['flags'].values()))
    def test_real_retained_entry_synthetic_mapping(self):
        from defensive_network_disruption.validation import r9o_terminal as terminal
        from defensive_network_disruption.validation import numerical_failure_publication as legacy
        tr=acceptance.control('rounded_oscillation')[0]['trace']
        args=tr['arguments'];ref=tr['reference'];structures=tr['structures']
        row=dict(alias='synthetic_only',carrier=[0.,0.],receiver=[10.,0.],defenders=[[2.,1.],[3.,-1.]])
        with tempfile.TemporaryDirectory() as name:
            local=Path(name).resolve()
            with patch.object(runner,'selected',return_value=(row,{})),patch.object(authority,'geometry_match'),patch.object(authority,'context',return_value=(args,ref,structures)),patch.object(legacy,'replay',side_effect=AssertionError('legacy')),patch.object(terminal.linear,'review',wraps=terminal.linear.review) as spy:
                result=runner.retained(local,runner.Permit(runner._SEAL),lambda *_:None,time.monotonic()+10)
                self.assertEqual(spy.call_count,1);self.assertEqual(result['diagnosis'],'BF')
            a=e.check_closure(local);self.assertEqual(a['failure']['stage'],'geometry');self.assertEqual(a['exposure']['field_evaluations_started'],0)
            package=load(local/'numerical_publication/qc.json');package['accepted']=True
            (local/'numerical_publication/qc.json').write_bytes(e.canonical(package))
            with self.assertRaises(ValueError):e.check_closure(local)
    def test_unlock_rejection(self):
        for env,controls,pub in [({},[],{'flags':{}}),({'ci_receipt_sha256':'x'},[{'passed':False}]*10,{'flags':{'x':True}})]:
            with self.assertRaises(PermissionError):runner.unlock(env,controls,pub)
    def test_marker_create_once(self):
        with tempfile.TemporaryDirectory() as name:
            path=Path(name).resolve()/'marker';runner.put(path,{'reserved':True})
            with self.assertRaises(FileExistsError):runner.put(path,{'reserved':True})
    def test_preflight_dirty_before_access(self):
        with patch.object(runner,'git',return_value='dirty'),patch.object(authority,'verify_sources',side_effect=AssertionError('access')):
            with self.assertRaisesRegex(RuntimeError,'dirty_tree'):runner.preflight()
    def test_actual_main_startup_failure(self):
        with tempfile.TemporaryDirectory() as name:
            folder=Path(name).resolve()
            with patch.object(runner,'OUT',folder),patch.object(runner,'diagnose',side_effect=ImportError('synthetic_package_import')),patch('sys.argv',['runner','diagnose']):
                with self.assertRaises(ImportError):runner.main()
            failure=load(folder/'local/outer_failure.json');self.assertEqual(failure['traceback_sha256'],sha(folder/'local/outer_traceback.txt'));self.assertFalse((folder/'local/access_attempt.json').exists())
    def test_closed_blocked_package_and_tampering(self):
        with tempfile.TemporaryDirectory() as name:
            folder=Path(name).resolve();local=folder/'local';put(local/'authority.json',dict(head='synthetic'))
            put(local/'controls.json',[]);put(local/'outcome.json',dict(schema_version=1,execution_valid=False,reason='execution_failure',timings=dict(governed_wall=1.,exclusive_compute=.1,inclusive_numerical=0.,io=.1,waiting=0.,unattributed=.8)))
            result=e.close(folder);self.assertEqual(result['diagnosis'],'BF');self.assertEqual(result['diagnostic_readiness'],4)
            q=load(folder/'qc.json');q['data']['diagnosis']='BC';(folder/'qc.json').write_bytes(e.canonical(q))
            m=load(folder/'manifest.json');m['outputs']['qc.json']=sha(folder/'qc.json');(folder/'manifest.json').write_bytes(e.canonical(m))
            with self.assertRaisesRegex(ValueError,'false_decision'):e.publication_check(folder)
    def test_failed_closure_and_rerun(self):
        with tempfile.TemporaryDirectory() as name:
            folder=Path(name).resolve()
            with self.assertRaises(FileNotFoundError):e.close(folder)
            self.assertFalse((folder/'manifest.json').exists())
    def test_no_numerical_routes_in_checking(self):
        source=(ROOT/'src/defensive_network_disruption/validation/r9s_evidence.py').read_text()
        for text in ('inspect_production(','.evaluate(','.review(','.bounds('):self.assertNotIn(text,source)
