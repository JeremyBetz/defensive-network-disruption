"""Synthetic-only tests of the actual R3 assembled verification route."""
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
spec=importlib.util.spec_from_file_location('r3',ROOT/'scripts/session_14r5_occlusion_study.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)

class Session14R5Tests(unittest.TestCase):
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


class R5WrapperTests(unittest.TestCase):
    def test_standard_library_startup_closure(self):
        with tempfile.TemporaryDirectory() as d,patch.object(runner,'ROOT',Path(d).resolve()),patch.object(runner,'history'):
            for path in (*runner.CODE,runner.PROTOCOL):
                target=runner.ROOT/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_text('synthetic')
            runner.startup_failure(ImportError('synthetic runtime failure'))
            runner.publication_check()
            self.assertEqual(runner.load(runner.OUT/'qc.json')['stage'],'runtime_import')

    def test_run_startup_failure_never_reaches_preparation(self):
        with tempfile.TemporaryDirectory() as d,patch.object(runner,'ROOT',Path(d).resolve()),patch.object(runner,'PROGRESS',None),patch.object(runner,'preflight'),patch.object(runner,'observe',side_effect=RuntimeError('synthetic environment')),patch.object(runner,'code_hashes',return_value={}),patch.object(runner,'environment',return_value={}),patch.object(runner,'prepare') as prepare:
            p=runner.ROOT/runner.PROTOCOL;p.parent.mkdir(parents=True);p.write_text('synthetic')
            with self.assertRaises(RuntimeError):runner.run()
            prepare.assert_not_called()
            self.assertEqual(runner.load(runner.OUT/'qc.json')['progress_authority']['access']['attempts'],0)

    def test_actual_summary_path_retains_geometric_units(self):
        from defensive_network_disruption.geometry.representation_study import VerifiedEdge
        from defensive_network_disruption.validation.r5_persistence import Journal,Progress
        state=dict(alias=runner.ALIASES[0],carrier=(0,0),receivers=((20,0),(20,10)),defenders=((5,1),(8,2),(10,4)))
        def fake(*args,**kwargs):
            values=(.1,.2,.3)
            return VerifiedEdge(values,values,.6,.3,.6,.3,512,0.,0.)
        with tempfile.TemporaryDirectory() as d:
            j=Journal(Path(d).resolve()/'journal');progress=Progress(j)
            progress.transition('discover_state','0',('0','1'));progress.transition('prepare_state','0')
            progress.transition('start_state_evaluation','0')
            c=runner.Collect();across=[]
            with patch.object(runner,'PROGRESS',progress),patch.object(runner,'evaluate_edge',side_effect=fake):
                result=runner.summarize_state(state,0,c,across)
            self.assertEqual(len(result),6)
            self.assertEqual(progress.core.snapshot()['counters']['edges_completed'],2)
            self.assertEqual(len(progress.calls),6)
            runner.add_across(c,across)
            with patch.object(runner,'ROOT',Path(d).resolve()):
                for name,rows in c.tables().items():runner.write_csv(name,rows)
                runner.validate_tables(runner.OUT)
            j.close()

    def test_pre_access_failure_package_reads_persisted_files(self):
        with tempfile.TemporaryDirectory() as d,patch.object(runner,'ROOT',Path(d).resolve()),patch.object(runner,'PROGRESS',None),patch.object(runner,'code_hashes',return_value={}),patch.object(runner,'environment',return_value={}),patch.object(runner,'history'):
            (runner.ROOT/runner.PROTOCOL).parent.mkdir(parents=True)
            (runner.ROOT/runner.PROTOCOL).write_text('synthetic protocol')
            runner.close_failure('startup',RuntimeError('synthetic'))
            runner.publication_check()
            qc=runner.load(runner.OUT/'qc.json')
            self.assertEqual(qc['progress_authority']['access']['states_opened'],0)
            (runner.ROOT/runner.LOCAL/'failure_package'/'evidence.json').unlink()
            with self.assertRaises(FileNotFoundError):runner.publication_check()

    def test_preparation_requires_guard_and_does_not_score(self):
        import inspect
        with patch.object(runner,'PROGRESS',None):
            with self.assertRaises(PermissionError):runner.prepare()
        self.assertNotIn('evaluate_edge',inspect.getsource(runner.prepare))

    def test_target_skipping(self):
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
        with patch.object(View,'read',read):_,geometry=runner.project_line(json.dumps(row))
        self.assertEqual(set(geometry),{'alias','carrier','receivers','defenders'})

    def test_malformed_row_records_access_before_failure(self):
        from defensive_network_disruption.validation.r5_persistence import Journal,Progress,receipts,read_journal
        with tempfile.TemporaryDirectory() as d,patch.object(runner,'ROOT',Path(d).resolve()):
            p=runner.ROOT/runner.POP;p.parent.mkdir(parents=True);p.write_text('{"synthetic_bad":1}\n')
            j=Journal(runner.ROOT/runner.LOCAL/'journal.jsonl');progress=Progress(j)
            progress.transition('authorize_access')
            with patch.object(runner,'PROGRESS',progress),patch.object(runner,'POP_SHA',runner.digest(runner.POP)):
                with self.assertRaises(ValueError):runner.prepare()
            self.assertEqual(receipts(read_journal(j.path)[0])['states_opened'],1)
            self.assertEqual(progress.core.snapshot()['counters']['states_completed'],0);j.close()

    def test_equal_match_weight_and_unavailable(self):
        c=runner.Collect()
        c.add('match_summary.csv',runner.ALIASES[0],0,'field',[0,0])
        c.add('match_summary.csv',runner.ALIASES[1],1,'field',[10])
        rows=c.tables()['match_summary.csv']
        self.assertEqual(next(x for x in rows if x['alias']=='macro')['mean'],5.)
        self.assertIsNone(next(x for x in rows if x['alias']==runner.ALIASES[2])['mean'])
