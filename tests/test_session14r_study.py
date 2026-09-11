"""Discoverable synthetic tests of actual Session 14R paths."""
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from defensive_network_disruption.geometry import representation_study as s
from defensive_network_disruption.data import representation_projection as projection
from defensive_network_disruption.data.boundary_review import View
from defensive_network_disruption.geometry.occlusion_fields import CarrierOriginField

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('session14r',ROOT/'scripts/session_14r_occlusion_study.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)


class RepresentationTests(unittest.TestCase):
    def test_degenerate_endpoint_exact(self):
        result=s.evaluate_edge('isotropic',(0,0),(0,0),((2,0),))
        self.assertEqual(result.receiver_union,math.exp(-.5))
        self.assertEqual(result.receiver_union,result.segment_union)
        self.assertEqual(result.intervals,0)
    def test_joint_numerical_identity_and_maximum(self):
        from defensive_network_disruption.geometry.integration_review import values_for_components
        from defensive_network_disruption.geometry.verification_audit import controlled_vector
        for candidate in ('isotropic','expanding','constant_width'):
            result=s.evaluate_edge(candidate,(0,0),(20,0),((5,0),))
            n,v,_=controlled_vector(lambda count:values_for_components(CarrierOriginField(candidate),(0,0),(20,0),((5,0),),count))
            self.assertEqual(result.intervals,n);self.assertEqual(result.segment_union,v['union'])
            self.assertEqual(result.segment_maximum,v['maximum'])
    def test_origin_coincidence_blocks(self):
        with self.assertRaises(ValueError):s.evaluate_edge('expanding',(0,0),(20,0),((0,0),))
    def test_cap_blocks_without_maximum_execution(self):
        with patch.object(s,'controlled_vector',return_value=(None,{},1)),patch.object(s,'maximum_checks') as maximum:
            with self.assertRaises(ValueError):s.evaluate_edge('isotropic',(0,0),(20,0),((5,0),))
            maximum.assert_not_called()
    def test_bad_independent_reference_blocks(self):
        with patch.object(s,'maximum_checks',return_value={'piecewise':5.}):
            with self.assertRaises(ValueError):s.evaluate_edge('isotropic',(0,0),(20,0),((5,0),))
    def test_warning_blocks(self):
        import warnings
        def warn(*a,**k):warnings.warn('synthetic warning')
        with patch.object(s,'controlled_vector',side_effect=warn):
            with self.assertRaises(Warning):s.evaluate_edge('isotropic',(0,0),(20,0),((5,0),))
    def test_block_anchor_and_zero_owner(self):
        np.testing.assert_equal(s.block_ranks([1,1-0.75e-12,1-1.5e-12]),[1.5,1.5,3])
        self.assertEqual(s.maximum_set([0,0]),frozenset())
        self.assertEqual(s.maximum_set([1,1]),frozenset((0,1)))
    def test_correlations_constant_unavailable(self):
        self.assertIsNone(s.spearman([1,1],[2,3]))
        self.assertIsNone(s.spearman([1],[2]))
        self.assertAlmostEqual(s.spearman([1,2,2],[4,3,3]),-1)
    def test_orders_partition_all_pairs(self):
        cats=s.order_categories([3,2,1,1],[1,2,2,0])
        self.assertEqual(sum(sum(v) for v in cats.values()),6)
        self.assertTrue(all(len(v)==6 for v in cats.values()))
    def test_endpoint_corridor_opposition(self):
        pairs=s.discordant_pairs([1,2],[2,1])
        self.assertEqual(pairs,[(0,1,1)])
        self.assertEqual(s.follows([4,3],pairs)['endpoint_following'],[1.])
        self.assertEqual(s.follows([3,4],pairs)['corridor_following'],[1.])
        self.assertEqual(s.follows([3,3],pairs)['tied'],[1.])
    def test_weighted_inverse_cdf(self):
        result=s.weighted_summary([1,2,9],[.25,.25,.5])
        self.assertEqual(result['q50'],2)
        self.assertEqual(result['mean'],5.25)
        self.assertIsNone(s.weighted_summary([],[])['mean'])
    def test_equal_minimum_stress_endpoint(self):
        from defensive_network_disruption.geometry.segment import point_to_segment_distance
        a=((15,2),);b=((5,2),(10,2),(15,2))
        self.assertEqual(min(point_to_segment_distance(d,(0,0),(20,0))[0] for d in a),
                         min(point_to_segment_distance(d,(0,0),(20,0))[0] for d in b))
        for candidate in ('isotropic','expanding','constant_width'):
            field=CarrierOriginField(candidate)
            x=field.combined_values((0,0),a,((20,0),))[0]
            y=field.combined_values((0,0),b,((20,0),))[0]
            self.assertGreaterEqual(y,x)


class ProjectionTests(unittest.TestCase):
    def fixture(self):
        return dict(match_id=projection.DEVELOPMENT[0],event_id='synthetic-event',carrier_xy=[0,0],
                    candidate_ids=['synthetic-a','synthetic-b'],candidate_xy=[[2,0],[4,0]],defender_xy=[[1,1]],
                    target_index={'sentinel':'DO_NOT_DECODE'},target_outside=['DO_NOT_DECODE'])
    def test_targets_never_decoded(self):
        raw=self.fixture(); original=View.read
        def guarded(view,span):
            if 'DO_NOT_DECODE' in view.text[slice(*span)]:raise AssertionError('target_decoded')
            return original(view,span)
        with patch.object(View,'read',guarded):key,row=projection.project_line(json.dumps(raw))
        self.assertEqual(set(row),{'alias','carrier','receivers','defenders'})
        self.assertNotIn('synthetic-event',json.dumps(row))
    def test_unauthorized_match_unknown_keys_duplicate_keys(self):
        raw=self.fixture();raw['match_id']='1953632'
        with self.assertRaises(PermissionError):projection.project_line(json.dumps(raw))
        raw=self.fixture();raw['pose']=True
        with self.assertRaises(ValueError):projection.project_line(json.dumps(raw))
        text=json.dumps(self.fixture());text=text[:-1]+',"match_id":"x"}'
        with self.assertRaises(ValueError):projection.project_line(text)
    def test_bad_geometry_and_identity(self):
        for key,value in [('defender_xy',[]),('carrier_xy',[True,0]),('candidate_ids',['x','x']),('defender_xy',[[0,0]])]:
            raw=self.fixture();raw[key]=value
            with self.assertRaises(ValueError):projection.project_line(json.dumps(raw))


class RunnerTests(unittest.TestCase):
    def test_equal_match_not_pooled(self):
        c=r.Collect()
        c.add('match_summary.csv',r.ALIASES[0],0,'x',[0,0]);c.add('match_summary.csv',r.ALIASES[0],1,'x',[0])
        c.add('match_summary.csv',r.ALIASES[1],2,'x',[10]);c.add('match_summary.csv',r.ALIASES[2],3,'x',[])
        rows=c.tables()['match_summary.csv'];macro=next(x for x in rows if x['alias']=='macro')
        self.assertEqual(macro['mean'],5);self.assertEqual(macro['states_unavailable'],1)
        self.assertEqual(macro['represented_matches'],2)
    def test_symlinks_and_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve()
            with patch.object(r,'ROOT',root):
                with self.assertRaises(PermissionError):r.safe('../x')
                (root/'link').symlink_to(root/'other')
                with self.assertRaises(PermissionError):r.safe('link/file')
    def test_exclusive_and_no_rerun(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(r,'ROOT',Path(tmp).resolve()),patch.object(r,'ledger'):
            r.claim('analyze')
            with self.assertRaises(FileExistsError):r.claim('analyze')
    def test_atomic_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(r,'ROOT',Path(tmp).resolve()):
            path=r.OUT/'test.json';r.write(path,{'a':1})
            with self.assertRaises(FileExistsError):r.write(path,{'a':2})
            self.assertEqual(r.load(path),{'a':1})
    def test_prepare_cannot_evaluate_and_analysis_cannot_acquire(self):
        import inspect
        prepare=inspect.getsource(r.prepare);analysis=inspect.getsource(r.analyze)
        self.assertNotIn('evaluate_edge',prepare);self.assertNotIn('summarize_state',prepare)
        for bad in ('urlopen','requests','fit(','evaluate_options','MODEL','target_index'):
            self.assertNotIn(bad,analysis)
    def test_failure_package_and_tamper(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(r,'ROOT',Path(tmp).resolve()),patch.object(r,'ledger'),\
             patch.object(r,'digest',return_value='hash'),patch.object(r,'code_hashes',return_value={}),\
             patch.object(r,'environment',return_value={}):
            try:raise ValueError('synthetic')
            except ValueError as e:r.failure('prepare',e,0)
            m=r.load(r.OUT/'manifest.json')
            self.assertEqual(m['status'],'blocked');self.assertIn('match_summary.csv',m['unavailable'])
            self.assertEqual(r.load(r.OUT/'qc.json')['states_completed'],0)
    def test_fake_end_to_end_summary_and_schema(self):
        row=dict(alias=r.ALIASES[0],carrier=(0,0),receivers=((20,0),(20,10)),defenders=((5,1),(8,2),(10,4)))
        def fake(candidate,b,receiver,ds):
            vals=tuple(.1*(i+1) for i in range(len(ds)))
            return s.VerifiedEdge(vals,vals,.6,.3,.6,.3,512,0.,0.)
        c=r.Collect();across=[]
        with patch.object(r,'evaluate_edge',side_effect=fake):q=r.summarize_state(row,0,c,across)
        self.assertEqual(len(q),6);r.add_across(c,across)
        tables=c.tables();self.assertEqual(set(tables),set(r.CSV_FILES))
        for rows in tables.values():
            self.assertTrue(rows)
            self.assertTrue(all(set(x)==set(r.COLUMNS) for x in rows))
    def test_publication_rejects_unexpected_json(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(r,'ROOT',Path(tmp).resolve()):
            r.write(r.OUT/'qc.json',{'unexpected':True})
            with self.assertRaises(ValueError):r.validate_payloads(['qc.json'],'blocked')


if __name__=='__main__':unittest.main()
