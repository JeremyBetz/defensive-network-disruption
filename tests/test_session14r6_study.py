"""Synthetic-only tests of the assembled Session 14R6 study path."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import warnings

from defensive_network_disruption.geometry import representation_retry as retry
from defensive_network_disruption.geometry import production_verification as pv
from defensive_network_disruption.geometry.representation_study import order_categories, spearman, weighted_summary
from defensive_network_disruption.validation.r6_execution import Journal,Progress

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('r6',ROOT/'scripts/session_14r6_occlusion_study.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)


class Session14R6StudyTests(unittest.TestCase):
    def test_complete_assembled_acceptance(self):
        rows,checks=runner.synthetic_acceptance()
        self.assertEqual((len(rows),sum(len(x['errors']) for x in rows),sum(x['permutations'] for x in rows)),(108,366,399))
        self.assertTrue(all(x['passed'] for x in checks))

    def test_failure_propagation(self):
        args=('isotropic',(0.,0.),(20.,0.),((10.,2.),))
        for operation in ('controlled_vector','find_verified_envelope','deterministic_partitions','bounded_adaptive_maximum'):
            with self.subTest(operation=operation),patch.object(retry,operation,side_effect=ValueError('injected')):
                with self.assertRaises(ValueError):retry.evaluate(*args)
        def warned(*args,**kwargs):warnings.warn('synthetic warning',RuntimeWarning)
        with patch.object(retry,'bounded_adaptive_maximum',side_effect=warned):
            with self.assertRaises(RuntimeWarning):retry.evaluate(*args)

    def test_discovery_skips_geometry_and_targets(self):
        row=dict(match_id=runner.DEVELOPMENT[0],event_id='synthetic',candidate_ids=['a','b'],
            carrier_xy={'sentinel':'NO_GEOMETRY'},candidate_xy=['NO_GEOMETRY'],defender_xy=['NO_GEOMETRY'],
            target_index={'sentinel':'NO_TARGET'},target_outside=['NO_TARGET'])
        key,edges=runner.discover_line(json.dumps(row))
        self.assertEqual((key[0],edges),(runner.ALIASES[0],('0','1')))

    def test_projection_skips_targets(self):
        row=dict(match_id=runner.DEVELOPMENT[0],event_id='synthetic',carrier_xy=[0,0],candidate_ids=['a'],
            candidate_xy=[[20,0]],defender_xy=[[10,1]],target_index={'sentinel':'NO_LABEL'},target_outside=['NO_LABEL'])
        from defensive_network_disruption.data.boundary_review import View
        original=View.read
        def read(view,span):
            self.assertNotIn('NO_LABEL',view.text[slice(*span)]);return original(view,span)
        with patch.object(View,'read',read):_,geometry=runner.project_line(json.dumps(row))
        self.assertEqual(set(geometry),{'alias','carrier','receivers','defenders'})

    def test_summary_path_counts_edges_once(self):
        from defensive_network_disruption.geometry.representation_study import VerifiedEdge
        state=dict(alias=runner.ALIASES[0],carrier=(0,0),receivers=((20,0),(20,10)),defenders=((5,1),(8,2),(10,4)))
        fake=lambda *a,**k:VerifiedEdge((.1,.2,.3),(.1,.2,.3),.6,.3,.6,.3,512,0.,0.)
        with tempfile.TemporaryDirectory() as folder:
            journal=Journal(Path(folder).resolve()/'journal');progress=Progress(journal);progress.authorize_access()
            progress.discover_state('0',('0','1'));progress.project('0',lambda:object());progress.prepare_state('0');progress.start_state('0')
            collector=runner.Collect();across=[]
            with patch.object(runner,'PROGRESS',progress),patch.object(runner,'evaluate_edge',side_effect=fake):
                qc=runner.summarize_state(state,0,collector,across)
            self.assertEqual(len(qc),6)
            counters=progress.core.snapshot()['counters']
            self.assertEqual((counters['edges_completed'],counters['field_evaluations_completed']),(2,6));journal.close()

    def test_ordering_weighting_and_unavailable(self):
        self.assertIsNone(spearman([1,1],[1,2]))
        self.assertEqual(order_categories([1,2],[2,1])['strict_reversal'],[1.])
        self.assertIsNone(weighted_summary([],[])['mean'])

    def test_prepare_requires_guard_and_does_not_score(self):
        import inspect
        with patch.object(runner,'PROGRESS',None):
            with self.assertRaises(PermissionError):runner.prepare()
        self.assertNotIn('evaluate_edge',inspect.getsource(runner.prepare))

    def test_no_prohibited_routes_and_path_escape(self):
        source=(ROOT/'scripts/session_14r6_occlusion_study.py').read_text()
        for name in ('load_model','evaluate_options','requests.get','target_index]','M2'):
            self.assertNotIn(name,source)
        with self.assertRaises(PermissionError):runner.safe(Path('../outside'))


if __name__=='__main__':unittest.main()
