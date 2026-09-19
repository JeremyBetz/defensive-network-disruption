"""Provider-free R9Q reference, observation and failure controls."""
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path
import tempfile
import time
import unittest

from defensive_network_disruption.geometry import r9q_diagnosis as d
from defensive_network_disruption.geometry.r9j_reference import Bounds, sqrt_bounds, exp_negative


class Linear:
    identity=('linear',)
    def bounds(self,a,b):return Bounds(F(a)-F(1,2),F(b)-F(1,2)),Bounds.point(1)

class Zero:
    identity=('zero',)
    def bounds(self,a,b):return Bounds.point(0),Bounds.point(0)

class SmallPositive:
    identity=('small',)
    def bounds(self,a,b):return Bounds.point(F(1,2**80)),Bounds.point(0)

class Unknown:
    identity=('unknown',)
    def bounds(self,a,b):return Bounds(-F(1),F(1)),None


class ReferenceTests(unittest.TestCase):
    def test_duplicate_and_inactive_branches(self):
        a=d.Expanding((0.,0.),(20.,0.),(5.,1.));b=d.Expanding((0.,0.),(20.,0.),(5.,-1.))
        c=d.Expanding((0.,0.),(20.,0.),(6.,2.))
        for first,second,left,right,topology in ((a,b,.5,.75,'A'),(a,c,0.,.1,'G')):
            result=d.reference(first,second,left,right,deadline=time.monotonic()+10,sink=lambda *_:None)
            self.assertTrue(result['complete']);self.assertEqual(result['topology'],topology)

    def test_simple_crossing_and_no_tolerance_equality(self):
        r=d.reference(Linear(),Zero(),0.,1.,deadline=time.monotonic()+10,sink=lambda *_:None)
        self.assertEqual((r['topology'],r['root_count']),('B',1))
        r=d.reference(SmallPositive(),Zero(),0.,1.,deadline=time.monotonic()+10,sink=lambda *_:None)
        self.assertEqual(r['root_count'],0);self.assertTrue(r['equality_refuted']);self.assertFalse(r['identity'])

    def test_uncertain_limit_preserves_every_cell(self):
        cells=[]
        r=d.reference(Unknown(),Zero(),0.,1.,deadline=time.monotonic()+10,sink=lambda k,v:cells.append((k,v)),max_depth=2)
        self.assertFalse(r['complete']);self.assertIsNone(r['root_count']);self.assertEqual(r['counts']['unresolved'],4)
        self.assertEqual(sum(k=='reference_cell' for k,_ in cells),4)

    def test_deadline_and_invalid_domain(self):
        with self.assertRaises(d.DeadlineExceeded):d.reference(Linear(),Zero(),0.,1.,deadline=0,sink=lambda *_:None)
        for left,right in ((.6,.4),(-.1,.3),(0.,math.inf)):
            with self.assertRaises(ValueError):d.reference(Linear(),Zero(),left,right,deadline=time.monotonic()+10,sink=lambda *_:None)

    def test_single_float_region_is_not_widened_into_an_interval(self):
        r=d.reference(SmallPositive(),Zero(),.5,.5,deadline=time.monotonic()+10,sink=lambda *_:None)
        self.assertEqual((r['complete'],r['root_count']),(True,0))
        r=d.reference(Unknown(),Zero(),.5,.5,deadline=time.monotonic()+10,sink=lambda *_:None)
        self.assertEqual(r['counts']['leaves'],1);self.assertFalse(r['complete'])

    def test_square_sqrt_exp_bounds(self):
        s=d.square(Bounds(-F(2),F(3)));self.assertEqual((s.lo,s.hi),(0,9))
        for q in (F(0),F(2),F(4),F(1,3)):
            b=sqrt_bounds(q);self.assertLessEqual(b.lo*b.lo,q);self.assertGreaterEqual(b.hi*b.hi,q)
        from decimal import Decimal,localcontext
        with localcontext() as c:
            c.prec=110
            for x in (F(0),F(1,10),F(1,2),F(7)):
                b=exp_negative(x);actual=(-Decimal(x.numerator)/Decimal(x.denominator)).exp()
                self.assertLessEqual(Decimal(b.lo.numerator)/Decimal(b.lo.denominator),actual)
                self.assertGreaterEqual(Decimal(b.hi.numerator)/Decimal(b.hi.denominator),actual)

    def test_derivative_and_scalar_on_fixed_branches(self):
        from defensive_network_disruption.geometry.verification_audit import scalar_oracle
        f=d.Expanding((0.,0.),(20.,0.),(5.,1.))
        for t in (.1,.28,.5,.9):
            value,derivative=f.bounds(F.from_float(t),F.from_float(t))
            actual=scalar_oracle('expanding',(0.,0.),(5.,1.),(20*t,0.))
            self.assertLessEqual(max(value.lo-F.from_float(actual),F.from_float(actual)-value.hi,F(0)),F.from_float(1e-12))
            self.assertIsNotNone(derivative)
        _,derivative=f.bounds(F(1,5),F(2,5));self.assertIsNone(derivative)

    def test_exact_smoothstep_derivative(self):
        f=d.Expanding((0.,0.),(20.,0.),(5.,0.))
        value,derivative=f.bounds(F(11,40),F(11,40))
        self.assertLessEqual(value.lo,F(1,2));self.assertGreaterEqual(value.hi,F(1,2))
        self.assertLessEqual(derivative.lo,F(30));self.assertGreaterEqual(derivative.hi,F(30))
        value,derivative=f.bounds(F(1,2),F(3,4))
        self.assertEqual((value.lo,value.hi),(1,1));self.assertEqual((derivative.lo,derivative.hi),(0,0))

    def test_signed_zero_serialization_and_nonfinite(self):
        self.assertNotEqual(d.primitive(-0.)['bits'],d.primitive(0.)['bits'])
        for x in (float('nan'),float('inf')):
            with self.assertRaises(ValueError):d.primitive(x)
        with self.assertRaises(TypeError):d.primitive(object())
        with self.assertRaises(ValueError):d.Expanding((0.,0.),(1.,0.),(0.,0.))

    def test_eleven_controls_deterministic(self):
        def sink(k,v):return hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest()
        a=d.controls(sink);b=d.controls(sink)
        self.assertEqual(a,b);self.assertEqual(len(a),11)
        self.assertTrue(all(row['passed'] for row in a))
        self.assertEqual(a[1]['observed_status'],'returned')
        self.assertEqual(a[2]['observed_status'],'rejected')
        self.assertEqual(a[4]['expected_roots'],2)

    def test_probe_nonmonotonicity_and_false_NA(self):
        c={'locals':dict(lower=0.,upper=1.,before=-1,after=1,start=.2,end=.8,point=.4),
           'probes':[dict(point=t,value=v) for t,v in ((0.,-1.),(.2,0.),(.4,-1.),(.8,1.),(1.,1.))]}
        audit=d.probe_audit(c);self.assertTrue(audit['monotone_predicate_refuted'])
        self.assertEqual(d.numerical_decision(True,{'complete':True,'equality_refuted':True},audit,True),'NC')
        self.assertEqual(d.numerical_decision(False,{'complete':True},audit,True),'NF')
        self.assertEqual(d.numerical_decision(True,{'complete':False},audit,True),'NF')
        c['probes'].append(dict(point=.4,value=1.))
        with self.assertRaises(ValueError):d.probe_audit(c)

    def test_observer_write_failure_does_not_replace_solver_exception(self):
        import numpy as np
        from defensive_network_disruption.geometry.onset_owner_certification import localize
        from defensive_network_disruption.geometry.verification_repair import VerifiedSwitch
        def function(t):return np.column_stack(((t-.5)**2,np.zeros_like(t)))
        switch=VerifiedSwitch(.5,(1,),(0,1),(0,),((0,1),),False,False,0.)
        def broken(*_):raise OSError('synthetic_disk_failure')
        observer=d.Observer(broken)
        with observer.enabled():
            with self.assertRaisesRegex(ValueError,'switch_sign_transition_invalid'):localize(function,switch)
        self.assertEqual(observer.error['exception'],'OSError')

    def test_observer_cannot_swallow_deadline(self):
        def expired(*_):raise d.DeadlineExceeded('synthetic_deadline')
        observer=d.Observer(expired)
        with self.assertRaises(d.DeadlineExceeded):observer.write('stage',{})

    def test_actual_r9k_route_observation_preserves_result(self):
        from defensive_network_disruption.geometry.r9k_comparator import evaluate_edge
        root=Path(__file__).parents[1]
        arguments=('expanding',(0.,0.),(8.,0.),((3.,1.),))
        plain=evaluate_edge(*arguments,root=root,authority_context={'alias':'synthetic'})
        with d.Observer(lambda *_:None).enabled():
            observed=evaluate_edge(*arguments,root=root,authority_context={'alias':'synthetic'})
        self.assertEqual(plain,observed)
