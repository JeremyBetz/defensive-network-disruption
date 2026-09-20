import copy
from fractions import Fraction as F
import math
import time
import unittest
from unittest.mock import patch
import numpy as np
from defensive_network_disruption.geometry import r9s_trace as t,r9r_localization as old
from defensive_network_disruption.validation import r9s_acceptance as a

class TraceTests(unittest.TestCase):
    def test_ten_frozen_controls(self):
        for name in a.FIXTURES:
            with self.subTest(name=name):
                detail,passed=a.control(name);self.assertTrue(passed);self.assertTrue(t.check_trace(detail['trace'])['complete'])
    def test_arithmetic_patterns(self):
        for name,sequence in [('rounded_plateau','NNZZZZPPP'),('rounded_oscillation','NNPPZNPPP')]:
            self.assertEqual(a.control(name)[0]['sequence'],sequence)
    def test_observation_equivalence(self):
        mid=old.old._bits(.5);lo=old.old._float(mid-4);hi=old.old._float(mid+4)
        calls=[]
        def fn(xs):
            calls.extend(map(float,xs));return np.column_stack((xs-.5,np.zeros_like(xs)))
        expected=old.inspect_production(fn,(0,1),F(1,2),F(1,2),lo,hi,-1,1,deadline=time.monotonic()+10)
        original=list(calls);calls.clear();sample=a.control('isolated_zero')[0]['trace']
        trace,error,result=a.collect(fn,(0,1),F(1,2),F(1,2),lo,hi,-1,1,sample['reference'],sample['structures'],lambda *_:None,engineering=True)
        self.assertIsNone(error);self.assertEqual(result,expected);self.assertEqual(calls,original);self.assertTrue(t.check_trace(trace)['complete'])
    def test_expansion_order(self):
        mid=old.old._bits(.5);lo=old.old._float(mid-80);hi=old.old._float(mid+80)
        ref=dict(enclosure=[t.rational(F(1,2))]*2,outer=[t.binary(lo),t.binary(hi)],one_crossing=False,strict_derivative=False,authority_valid=False,boundary_refuted=False,excluded=None)
        fn=lambda x:np.column_stack((x-old.old._float(mid+25),np.zeros_like(x)))
        tr,err,_=a.collect(fn,(0,1),F(1,2),F(1,2),lo,hi,-1,1,ref,dict(onsets=[],ties=[],status='engineering'),lambda *_:None,engineering=True)
        self.assertIsNone(err);self.assertGreater(len(tr['windows']),1);self.assertNotEqual(tr['sorted_ordinals'],list(range(len(tr['probes']))));self.assertTrue(t.check_trace(tr)['complete'])
    def test_changed_trace_rejected(self):
        for change in ('duplicate','missing','value','cache','order','sign','bits','reference','attempt'):
            tr=copy.deepcopy(a.control('isolated_zero')[0]['trace'])
            if change=='duplicate':tr['probes'][1]=tr['probes'][0]
            elif change=='missing':tr['probes'].pop(2)
            elif change=='value':tr['probes'][0]['values'][0]=t.binary(5.)
            elif change=='cache':tr['final']['cache'][0][1]=1
            elif change=='order':tr['sorted_ordinals'].reverse()
            elif change=='sign':tr['probes'][0]['sign']=1
            elif change=='bits':tr['probes'][0]['parameter']['bits']='0'*16
            elif change=='reference':tr['probes'][0]['reference']['root_relation']='after'
            else:tr['attempts'][0]['key']+=1
            with self.subTest(change=change),self.assertRaises((ValueError,IndexError)):t.check_trace(tr)
    def test_signed_zero_serialization(self):
        self.assertNotEqual(t.binary(0.),t.binary(-0.));self.assertEqual(math.copysign(1,t.number(t.binary(-0.))),-1)
        with self.assertRaises(ValueError):t.binary(float('nan'))
    def test_incomplete_is_h(self):
        tr=a.control('rounded_oscillation')[0]['trace'];tr['final']=None
        self.assertEqual(t.check_trace(tr)['pattern'],'H');self.assertEqual(t.summarize(tr,retained=True)['diagnosis'],'BF')
    def test_insufficient_support(self):
        tr=a.control('rounded_plateau')[0]['trace'];tr['reference']['strict_derivative']=False
        self.assertEqual(t.summarize(tr)['compatibility'],'AMBIGUOUS')
    def test_pattern_disjoint(self):
        self.assertEqual(t.pattern_for([1,-1],True,False),'B')
        self.assertEqual(t.pattern_for([-1,0,-1],True,False),'D')
        self.assertEqual(t.pattern_for([-1,0,-1,0,1],True,False),'F')
        self.assertEqual(t.pattern_for([-1,-1],True,False),'H')
    def test_interrupted_sink(self):
        count=0
        def sink(label,value):
            nonlocal count
            if label=='probe':count+=1
            if count==3:raise OSError('synthetic_write_failure')
        detail,passed=a.control('isolated_zero',sink)
        self.assertFalse(passed);self.assertEqual(detail['trace']['outcome']['exception'],'ObservationFailure')
    def test_deadline(self):
        tr=a.control('isolated_zero')[0]['trace'];fn=lambda x:np.column_stack((x,np.zeros_like(x)))
        value,error,_=a.collect(fn,(0,1),F(1,2),F(1,2),.4,.6,-1,1,tr['reference'],tr['structures'],lambda *_:None,engineering=True,deadline=0)
        self.assertIsInstance(error,TimeoutError);self.assertEqual(value['probes'],[])
    def test_actual_field_hook(self):
        from defensive_network_disruption.geometry.occlusion_fields import CarrierOriginField,validate_geometry,points
        base,defence,_=validate_geometry([0.,0.],[[2.,1.],[3.,-1.]])
        end=points([10.,0.],one=True);field=CarrierOriginField('expanding')
        lo=math.nextafter(.5,0);hi=math.nextafter(.5,1)
        ref=dict(enclosure=[t.rational(F(1,2))]*2,outer=[t.binary(lo),t.binary(hi)],one_crossing=False,strict_derivative=False,authority_valid=False,boundary_refuted=False,excluded=None)
        def fn(x):return field.individual_values(base,defence,base[None,:]+x[:,None]*(end-base)[None,:])
        tr,error,_=a.collect(fn,(0,1),F(1,2),F(1,2),lo,hi,-1,1,ref,dict(onsets=[],ties=[],status='uncertified'),lambda *_:None)
        self.assertEqual(len(tr['probes']),3);self.assertTrue(t.check_trace(tr)['complete']);self.assertIsInstance(tr['probes'][0]['branches'],list)
    def test_no_new_numerical_route(self):
        with patch.object(old,'classify',side_effect=AssertionError()),patch.object(old,'isolate',side_effect=AssertionError()),patch.object(old,'canonical_geometry',side_effect=AssertionError()):
            self.assertTrue(a.control('rounded_plateau')[1])
