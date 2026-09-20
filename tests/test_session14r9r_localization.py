"""R9R topology, boundary compatibility, field bounds and preservation tests."""
from dataclasses import replace
from fractions import Fraction as F
import inspect
import math
from pathlib import Path
import time
import unittest
from unittest.mock import patch

import numpy as np

from defensive_network_disruption.geometry import r9r_localization as r
from defensive_network_disruption.geometry import r9r_adapter as adapter
from defensive_network_disruption.geometry import r9k_comparator as prior
from defensive_network_disruption.geometry.occlusion_fields import CarrierOriginField
from defensive_network_disruption.validation import r9r_acceptance as a

ROOT=Path(__file__).resolve().parents[1]


class LocalizationTests(unittest.TestCase):
    def test_fourteen_frozen_controls(self):
        rows=a.topology_controls()
        self.assertEqual(tuple(x['fixture'] for x in rows),a.FIXTURES)
        self.assertTrue(all(x['passed'] for x in rows),rows)
        self.assertEqual(rows,a.topology_controls())

    def test_nine_negative_controls(self):
        rows=a.negative_controls()
        self.assertEqual(tuple(x['fixture'] for x in rows),a.NEGATIVES)
        self.assertTrue(all(x['blocked'] for x in rows))

    def test_field_bounds_three_families_and_scalar_agreement(self):
        b=(0.,0.);end=(20.,0.);defenders=((8.,2.),(12.,-2.))
        for candidate in ('isotropic','expanding','constant_width'):
            field=CarrierOriginField(candidate)
            for defender in defenders:
                authority=r.FieldAuthority.from_geometry(candidate,b,end,defender)
                for t in (0.,.25,.5,.75,1.):
                    bounds,derivative=authority.bounds(F.from_float(t),F.from_float(t))
                    value=float(field.individual_values(b,(defender,),((20*t,0.),))[0,0])
                    lo,hi=bounds.floats()
                    self.assertLessEqual(max(abs(value-lo),abs(value-hi)),1e-12)
                    wide,_=authority.bounds(max(F(0),F.from_float(t)-F(1,1000)),min(F(1),F.from_float(t)+F(1,1000)))
                    self.assertLessEqual(wide.lo,bounds.lo);self.assertGreaterEqual(wide.hi,bounds.hi)

    def test_identity_is_exact_and_immutable(self):
        x=r.FieldAuthority.from_geometry('expanding',(0.,0.),(20.,0.),(5.,1.))
        y=r.FieldAuthority.from_geometry('expanding',(0.,0.),(20.,0.),(5.,-1.))
        z=r.FieldAuthority.from_geometry('expanding',(0.,0.),(20.,0.),(5.,math.nextafter(1.,2.)))
        self.assertTrue(r.PairAuthority(x,y).identical)
        self.assertFalse(r.PairAuthority(x,z).identical)
        with self.assertRaises(AttributeError):x.q=F(1)
        with self.assertRaisesRegex(ValueError,'authority_consistency'):replace(x,rho=r.Bounds.point(1))
        with self.assertRaisesRegex(ValueError,'authority_coefficients'):replace(x,cross2=x.cross2+1)

    def test_bad_authority_inputs_and_limits(self):
        with self.assertRaises(ValueError):r.FieldAuthority.from_geometry('other',(0.,0.),(20.,0.),(5.,1.))
        with self.assertRaises(ValueError):r.FieldAuthority.from_geometry('expanding',(0.,0.),(20.,0.),(0.,0.))
        with self.assertRaises(ValueError):r.FieldAuthority.from_geometry('expanding',(0.,0.),(20.,0.),(float('inf'),1.))
        with self.assertRaises(ValueError):r.classify(a.Polynomial('linear'),0,1,deadline=time.monotonic()+2,max_depth=81)
        with self.assertRaises(TimeoutError):r.classify(a.Polynomial('linear'),0,1,deadline=0)

    def test_production_simple_transition_preserves_old_record(self):
        from defensive_network_disruption.geometry.verification_repair import find_verified_envelope
        f=lambda t:np.column_stack((t-.5,np.zeros_like(t)))
        switch=find_verified_envelope(lambda t:np.column_stack((.5+.25*(t-.5),np.full_like(t,.5))),grid_intervals=128).switches[0]
        # Use unchanged owner module's raw transition on the same engineering function.
        before=r.owner.localize(f,switch)
        after=r.localize(f,switch,a.Polynomial('linear'),.25,.75,deadline=time.monotonic()+2)
        self.assertEqual(before,after)

    def test_nonmonotone_rounded_sequence_blocks_without_equality(self):
        mid=r.old._bits(.5)
        def function(t):
            values=[]
            for x in t:
                key=r.old._bits(float(x))
                values.append(-1. if key<mid else 1. if key==mid else -1. if key==mid+1 else 1.)
            return np.column_stack((values,np.zeros_like(t)))
        with self.assertRaisesRegex(ValueError,'binary64_nonmonotone_unresolved'):
            r.inspect_production(function,(0,1),F(1,2),F(1,2),.49,.51,-1,1,deadline=time.monotonic()+2)

    def test_complete_rounded_zero_block_is_inspected(self):
        middle=r.old._bits(.5);calls=[]
        def function(t):
            calls.extend(map(float,t));values=[-1. if r.old._bits(float(x))<middle-3 else 0. if r.old._bits(float(x))<=middle+4 else 1. for x in t]
            return np.column_stack((values,np.zeros_like(t)))
        result=r.inspect_production(function,(0,1),F(1,2),F(1,2),.49,.51,-1,1,deadline=time.monotonic()+2)
        self.assertEqual(r.old._bits(result.zero_start),middle-3)
        self.assertEqual(r.old._bits(result.zero_end),middle+4)
        self.assertEqual(r.old._bits(result.first_post),middle+5)
        self.assertEqual(result.floats_inspected,len(set(calls)))
        self.assertTrue(all(r.old._float(k) in calls for k in range(middle-3,middle+5)))

    def test_float_cap_and_signed_zero(self):
        with self.assertRaisesRegex(ValueError,'inspection_limit'):
            r.inspect_production(lambda t:np.column_stack((t-.5,t*0)),(0,1),F(1,4),F(3,4),.2,.8,-1,1,deadline=time.monotonic()+2)
        self.assertEqual(r.old._sign(-0.),0)
        self.assertNotEqual(a.primitive(-0.)['hex'],a.primitive(0.)['hex'])

    def test_zero_enclosure_is_not_root_count(self):
        result=r.classify(a.Polynomial('unknown'),0,1,deadline=time.monotonic()+2,max_depth=3)
        self.assertEqual(result.classification,'G');self.assertFalse(result.complete)
        self.assertEqual(result.root_intervals,())

    def test_owner_onset_and_no_interior_rejections_preserved(self):
        with self.assertRaisesRegex(ValueError,'coincident'):r.owner.interior_probes(.5,.5,1.)
        with self.assertRaisesRegex(ValueError,'no_interior'):r.owner.interior_probes(.5,math.nextafter(.5,0.),.75)

    def test_comparator_and_production_calls_are_unchanged(self):
        self.assertIs(adapter.independent_maximum,prior.independent_maximum)
        self.assertIs(adapter.controlled_vector,prior.controlled_vector)
        self.assertIs(adapter.values_for_components,prior.values_for_components)
        geometry=((0.,0.),(20.,0.),((8.,2.),))
        for candidate in ('isotropic','expanding','constant_width'):
            old=prior.evaluate(candidate,*geometry,root=ROOT,authority_context={'alias':'synthetic_r9r'})
            new=adapter.evaluate(candidate,*geometry,root=ROOT,authority_context={'alias':'synthetic_r9r'})
            self.assertEqual(old,new)

    def test_degenerate_edge_unchanged(self):
        geometry=((0.,0.),(0.,0.),((3.,1.),))
        old=prior.evaluate('expanding',*geometry,root=ROOT,authority_context={})
        with patch.object(r,'canonical_geometry',side_effect=AssertionError('degenerate localization')):
            self.assertEqual(adapter.evaluate('expanding',*geometry,root=ROOT,authority_context={}),old)

    def test_complete_historical_adapter_regression(self):
        observed=set()
        def sink(label,detail):
            observations=detail['localizations']
            kinds={item['kind'] for item in observations};observed.update(kinds)
            self.assertIn('raw_structures',kinds)
            for item in observations:
                if item['kind']=='candidate_region':
                    self.assertEqual(set(item['value']),{'raw_proposal','original_witnesses','constrained_region','structural_neighbors'})
            return a.digest(detail)
        rows=a.historical_regression(ROOT,sink)
        self.assertTrue({'candidate_region','pair_authority','transition'}<=observed)
        self.assertEqual(len(rows),108)
        self.assertEqual(sum(x['components'] for x in rows),366)
        self.assertEqual(sum(x['permutations'] for x in rows),399)
        self.assertTrue(all(x['status']=='passed' for x in rows),[x for x in rows if x['status']!='passed'])

    def test_no_runtime_replacement_or_empirical_selection(self):
        source=inspect.getsource(r)
        for prohibited in ('mock.patch','setattr(','read_bytes','open(','selected_geometry','provider','state =='):
            self.assertNotIn(prohibited,source)


if __name__=='__main__':unittest.main()
