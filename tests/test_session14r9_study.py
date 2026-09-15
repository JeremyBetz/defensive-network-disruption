"""Synthetic-only tests of the assembled Session 14R9 study path."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import warnings

from defensive_network_disruption.geometry import r7_representation as retry
from defensive_network_disruption.geometry import production_verification as pv
from defensive_network_disruption.geometry.representation_study import order_categories, spearman, weighted_summary
from defensive_network_disruption.validation.r7_execution import Journal,Progress
from defensive_network_disruption.validation.r9_certificate_orchestration import retained_observation_gate

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('r7',ROOT/'scripts/session_14r9_occlusion_study.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)


class Session14R9StudyTests(unittest.TestCase):
    def test_retained_observation_certificate_orchestration(self):
        seen=[]
        def publish(item):
            seen.append(item)
            return runner.validate_certificate_gate_record(item)
        record=retained_observation_gate(ROOT,publish=publish)
        self.assertTrue(record['ready'])
        self.assertEqual(record['evidence_type'],'retained_observation_certificate_orchestration')
        self.assertFalse(record['field_evaluation_performed'])
        self.assertFalse(record['empirical_geometry_accessed'])
        self.assertFalse(record['whole_integral_certified'])
        self.assertEqual(record['aggregate']['independently_certified_count'],1)

    def test_runtime_unmatched_certificate_blocks(self):
        from dataclasses import replace
        from defensive_network_disruption.validation import independent_certificate_verifier as cv
        from defensive_network_disruption.validation.r9_certificate_orchestration import runtime_certificate_lookup
        _,observation,_=cv.load_session14ar_certificate(ROOT)
        with self.assertRaisesRegex(cv.CertificateError,'authority_mismatch'):
            runtime_certificate_lookup(replace(observation,request=replace(observation.request,interval_identity='other')),ROOT)

    def test_complete_assembled_acceptance(self):
        rows,checks=runner.synthetic_acceptance()
        self.assertEqual((len(rows),sum(len(x['errors']) for x in rows),sum(x['permutations'] for x in rows)),(108,366,399))
        self.assertTrue(all(x['passed'] for x in checks))

    def test_failure_propagation(self):
        args=('isotropic',(0.,0.),(20.,0.),((10.,2.),))
        for operation in ('controlled_vector','independent_maximum'):
            with self.subTest(operation=operation),patch.object(retry,operation,side_effect=ValueError('injected')):
                with self.assertRaises(ValueError):retry.evaluate(*args)
        with patch.object(retry.owner,'canonical_geometry',side_effect=ValueError('root failure')):
            with self.assertRaises(ValueError):retry.evaluate(*args)
        def warned(*args,**kwargs):warnings.warn('synthetic warning',RuntimeWarning)
        with patch.object(retry,'independent_maximum',side_effect=warned):
            with self.assertRaises(RuntimeWarning):retry.evaluate(*args)

    def test_degenerate_endpoint_behavior(self):
        stages=[]
        edge,result=retry.evaluate('constant_width',(0.,0.),(0.,0.),((10.,2.),),record=lambda **x:stages.append(x['stage']))
        self.assertEqual(stages,['geometry','accepted'])
        self.assertEqual(edge.receiver_individual,edge.segment_individual)
        self.assertEqual(edge.intervals,0)

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
        def fake(*args,**kwargs):
            args[-1](stage='geometry');args[-1](stage='accepted')
            return VerifiedEdge((.1,.2,.3),(.1,.2,.3),.6,.3,.6,.3,512,0.,0.)
        with tempfile.TemporaryDirectory() as folder:
            journal=Journal(Path(folder).resolve()/'journal');progress=Progress(journal);progress.authorize_access()
            progress.discover_state('0',('0','1'));progress.project('0',lambda:object());progress.prepare_state('0');progress.start_state('0')
            collector=runner.Collect();across=[]
            with patch.object(runner,'PROGRESS',progress),patch.object(runner,'evaluate_edge',side_effect=fake):
                qc=runner.summarize_state(state,0,collector,across)
            self.assertEqual(len(qc),6)
            progress.retain_and_complete_edges('0')
            counters=progress.core.snapshot()['counters']
            self.assertEqual((counters['edges_completed'],counters['field_evaluations_completed']),(2,6));journal.close()

    def test_state_first_pair_aggregation_passes(self):
        result=runner.summary_contract_check()
        self.assertTrue(result['passed'])
        self.assertEqual(result['observed']['mean'],result['expected']['mean'])
        self.assertEqual((result['observed']['minimum'],result['observed']['q50']),(.5,.5))
        runner.require_summary_contract()

    def test_registry_units_and_state_denominators(self):
        collector=runner.Collect()
        collector.add('candidate_pair_comparison.csv',runner.ALIASES[0],0,'paired_difference',[0.,1.])
        collector.add('candidate_pair_comparison.csv',runner.ALIASES[0],1,'paired_difference',[1.,1.])
        rows=collector.tables()['candidate_pair_comparison.csv']
        match=next(row for row in rows if row['alias']==runner.ALIASES[0])
        self.assertEqual((match['unit'],match['observations'],match['source_observations']),
                         ('state_pair_mean',2,4))
        self.assertEqual((match['minimum'],match['q50'],match['maximum']),(.5,.5,1.))

    def test_entirely_unavailable_category_retains_unit(self):
        collector=runner.Collect()
        collector.add('candidate_pair_comparison.csv',runner.ALIASES[0],0,'agreement',[],unit='pair')
        row=next(x for x in collector.tables()['candidate_pair_comparison.csv'] if x['alias']==runner.ALIASES[0])
        self.assertEqual(row['unit'],'state_pair_proportion')
        self.assertEqual((row['observations'],row['source_observations']),(0,0))
        self.assertEqual(row['unavailable_reason'],'no_eligible_pairs')

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
        source=(ROOT/'scripts/session_14r9_occlusion_study.py').read_text()
        for name in ('load_model','evaluate_options','requests.get','target_index]','M2'):
            self.assertNotIn(name,source)
        with self.assertRaises(PermissionError):runner.safe(Path('../outside'))


if __name__=='__main__':unittest.main()
