"""Synthetic-only tests of the actual R2 assembled verification route."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import warnings
import numpy as np
from defensive_network_disruption.geometry import representation_retry as r
from defensive_network_disruption.geometry import production_verification as pv
from defensive_network_disruption.geometry.representation_study import order_categories, spearman, weighted_summary

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('r2',ROOT/'scripts/session_14r2_occlusion_study.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)

class Session14R2Tests(unittest.TestCase):
    def test_complete_assembled_acceptance(self):
        rows,checks=runner.synthetic_acceptance()
        self.assertEqual(len(rows),108)
        self.assertEqual(sum(len(x['errors']) for x in rows),366)
        self.assertEqual(sum(x['permutations'] for x in rows),399)
        self.assertTrue(all(x['passed'] for x in checks))

    def test_partitions_consumed_without_collapsing(self):
        f=lambda t:np.full((len(t),1),.5)
        parts=(0.,.5,float(np.nextafter(.5,1.)),1.)
        captured=[]
        original=r.bounded_adaptive_maximum
        def capture(function,partitions,tolerance):
            captured.append(partitions)
            return original(function,partitions,tolerance)
        with patch.object(r,'bounded_adaptive_maximum',side_effect=capture):
            result=r.independent_maximum(f,parts,())
        self.assertEqual(captured,[parts,parts]);self.assertEqual(result.bounded_piece_count,1)

    def test_failure_propagation(self):
        args=('isotropic',(0.,0.),(20.,0.),((10.,2.),))
        for operation in ('controlled_vector','find_verified_envelope','deterministic_partitions','bounded_adaptive_maximum'):
            with self.subTest(operation=operation),patch.object(r,operation,side_effect=ValueError('injected')):
                with self.assertRaises(ValueError):r.evaluate(*args)
        with patch.object(r,'controlled_vector',return_value=(None,{},1.)):
            with self.assertRaises(pv.GateFailure):r.evaluate(*args)
        def warned(*a,**kw):warnings.warn('synthetic warning',RuntimeWarning)
        with patch.object(r,'bounded_adaptive_maximum',side_effect=warned):
            with self.assertRaises(RuntimeWarning):r.evaluate(*args)

    def test_exclusive_marker(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder).resolve()/'marker';pv.claim_execution(p)
            with self.assertRaises(FileExistsError):pv.claim_execution(p)

    def test_ordering_and_unavailable(self):
        self.assertIsNone(spearman([1,1],[1,2]))
        self.assertEqual(order_categories([1,2],[2,1])['strict_reversal'],[1.])
        self.assertIsNone(weighted_summary([],[])['mean'])

    def test_nondeterminism_and_continuity_block(self):
        args=('isotropic',(0.,0.),(20.,0.),((10.,2.),))
        with patch.object(r.pv,'check_continuity',return_value=False):
            with self.assertRaises(pv.GateFailure):r.evaluate(*args,synthetic=True)
        original=r.canonical_geometry; calls=[]
        def changed(*a,**kw):
            out=original(*a,**kw);calls.append(1)
            return out if len(calls)==1 else (out[0],out[1],(0.,.4,1.),out[3])
        with patch.object(r,'canonical_geometry',side_effect=changed):
            with self.assertRaises(pv.GateFailure):r.evaluate(*args)

    def test_missing_reference_blocks(self):
        module=runner.synthetic_module();label,case=next(module.authority_cases())
        case=dict(case);case['references']={}
        with patch.object(module,'authority_cases',return_value=[(label,case)]),patch.object(runner,'synthetic_module',return_value=module),patch.object(runner.pv,'engineering_checks',return_value=[{'passed':True}]):
            with self.assertRaises(pv.GateFailure):runner.synthetic_acceptance()

    def test_permutation_mismatch_blocks(self):
        args=('isotropic',(0.,0.),(20.,0.),((10.,2.),))
        with patch.object(r.pv,'check_permutation',side_effect=pv.GateFailure('permutation_mismatch')):
            with self.assertRaises(pv.GateFailure):r.evaluate(*args,synthetic=True)

    def test_no_prohibited_calls(self):
        source=(ROOT/'src/defensive_network_disruption/geometry/representation_retry.py').read_text()
        for name in ('load_model','evaluate_options','requests','urllib','fit_model','summarize_edge('):
            self.assertNotIn(name,source)

    def test_hash_and_path_firewalls(self):
        with self.assertRaises(PermissionError):runner.safe(Path('/outside'))
        with self.assertRaises(PermissionError):runner.safe(Path('../outside'))

class R2GovernanceTests(unittest.TestCase):
    def test_projection_before_records(self):
        import json
        from defensive_network_disruption.data import representation_projection as projection
        from defensive_network_disruption.data.boundary_review import View
        row=dict(match_id=projection.DEVELOPMENT[0],event_id='synthetic',carrier_xy=[0,0],
            candidate_ids=['a'],candidate_xy=[[20,0]],defender_xy=[[10,1]],
            target_index={'sentinel':'NO_LABEL_DECODE'},target_outside=['NO_LABEL_DECODE'])
        original=View.read
        def read(view,span):
            self.assertNotIn('NO_LABEL_DECODE',view.text[slice(*span)])
            return original(view,span)
        with patch.object(View,'read',read):key,geometry=projection.project_line(json.dumps(row))
        self.assertEqual(set(geometry),{'alias','carrier','receivers','defenders'})
        row['match_id']='synthetic_unauthorized'
        with self.assertRaises(PermissionError):projection.project_line(json.dumps(row))

    def test_failure_closure_and_no_rerun(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(runner,'ROOT',Path(tmp).resolve()),patch.object(runner,'ledger'),patch.object(runner,'digest',return_value='hash'),patch.object(runner,'code_hashes',return_value={}),patch.object(runner,'environment',return_value={}):
            runner.failure('verify-production',ValueError('synthetic'),0)
            manifest=runner.load(runner.OUT/'manifest.json')
            self.assertEqual(manifest['status'],'blocked')
            self.assertFalse(runner.load(runner.OUT/'qc.json')['empirical_access'])
            self.assertIn('candidate_pair_comparison.csv',manifest['unavailable'])
            with self.assertRaises(ValueError):runner.claim('analyze')

    def test_equal_match_weighting(self):
        c=runner.Collect()
        c.add('match_summary.csv',runner.ALIASES[0],0,'field',[0,0])
        c.add('match_summary.csv',runner.ALIASES[1],1,'field',[10])
        rows=c.tables()['match_summary.csv']
        self.assertEqual(next(x for x in rows if x['alias']=='macro')['mean'],5.)

    def test_atomic_and_schema(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(runner,'ROOT',Path(tmp).resolve()):
            runner.write(runner.OUT/'qc.json',{'unexpected':True})
            with self.assertRaises(FileExistsError):runner.write(runner.OUT/'qc.json',{})
            with self.assertRaises(ValueError):runner.validate_payloads(['qc.json'],'blocked')

    def test_synthetic_summary_end_to_end(self):
        from defensive_network_disruption.geometry.representation_study import VerifiedEdge
        state=dict(alias=runner.ALIASES[0],carrier=(0,0),receivers=((20,0),(20,10)),defenders=((5,1),(8,2),(10,4)))
        def fake(candidate,b,end,ds,record):
            values=(.1,.2,.3)
            return VerifiedEdge(values,values,.6,.3,.6,.3,512,0.,0.)
        c=runner.Collect();across=[]
        with patch.object(runner,'evaluate_edge',side_effect=fake):
            result=runner.summarize_state(state,0,c,across)
        self.assertEqual(len(result),6)
        runner.add_across(c,across);tables=c.tables()
        self.assertEqual(set(tables),set(runner.CSV_FILES))
        with tempfile.TemporaryDirectory() as tmp,patch.object(runner,'ROOT',Path(tmp).resolve()):
            for filename,rows in tables.items():
                self.assertTrue(rows);runner.write_csv(filename,rows)
            runner.validate_payloads(list(tables),'blocked')
        self.assertTrue(any(row['comparison']=='receiver_to_segment' for row in tables['receiver_segment_divergence.csv']))

    def test_prepare_and_analyze_separation(self):
        import inspect
        self.assertNotIn('evaluate_edge',inspect.getsource(runner.prepare))
        for name in ('urlopen','requests','fit(','evaluate_options','load_model'):
            self.assertNotIn(name,inspect.getsource(runner.analyze))

if __name__=='__main__':unittest.main()
