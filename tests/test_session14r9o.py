import importlib.util
import math
from fractions import Fraction as F
from pathlib import Path
import tempfile
import unittest
from defensive_network_disruption.geometry.r9o_diagnosis import Expanding, compare_functions, controls
from defensive_network_disruption.geometry.r9j_reference import Bounds

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('r9o_runner',ROOT/'scripts/session_14r9o_switch_equality_failure_diagnosis.py')
R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)

class R9ODiagnosisTests(unittest.TestCase):
    def test_zero_lateral_full_onset(self):
        f=Expanding((0.,0.),(20.,0.),(5.,0.))
        value,derivative=f.bounds(F(1,2),F(3,4))
        self.assertEqual((value.lo,value.hi),(1,1));self.assertEqual((derivative.lo,derivative.hi),(0,0))

    def test_zero_gate(self):
        f=Expanding((0.,0.),(20.,0.),(5.,1.))
        value,derivative=f.bounds(F(0),F(1,10))
        self.assertEqual(value.hi,0);self.assertEqual(derivative.hi,0)

    def test_independent_point_bounds(self):
        from defensive_network_disruption.geometry.verification_audit import scalar_oracle
        f=Expanding((0.,0.),(20.,0.),(5.,1.))
        for t in (.3,.4,.7,1.):
            value,_=f.bounds(F.from_float(t),F.from_float(t))
            actual=scalar_oracle('expanding',(0.,0.),(5.,1.),(20*t,0.))
            a,b=value.floats();self.assertLessEqual(max(a-actual,actual-b),1e-12)

    def test_duplicates(self):
        import time
        f=Expanding((0.,0.),(20.,0.),(5.,1.))
        r=compare_functions(f,f,.4,.5,deadline=time.monotonic()+5)
        self.assertTrue(r['identity']);self.assertEqual(len(r['cells']),1)

    def test_timeout(self):
        import time
        f=Expanding((0.,0.),(20.,0.),(5.,1.))
        with self.assertRaises(TimeoutError):compare_functions(f,f,.4,.5,deadline=time.monotonic()-1)

    def test_controls_deterministic(self):
        a,b=controls(),controls();self.assertEqual(a,b);self.assertEqual(len(a),10)
        result={r['fixture']:r for r in a}
        self.assertEqual(result['simple_crossing']['status'],'returned')
        self.assertEqual(result['duplicates']['status'],'rejected')
        self.assertEqual(result['tangent']['status'],'rejected')

    def test_create_once(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d).resolve()/'record.json';R.put(p,{'a':1})
            with self.assertRaises(FileExistsError):R.put(p,{'a':2})
            self.assertEqual(p.read_text(),'{"a":1}\n')

    def test_schema(self):
        R.check_record(R.record())
        for key,value in [('counts',{'n':True}),('timings',{'t':math.inf}),('flags',{'x':1}),('status','success')]:
            r=R.record();r[key]=value
            with self.assertRaises(ValueError):R.check_record(r)

    def test_receipt_required_before_read(self):
        with self.assertRaises(PermissionError):R.selected(Path('/nonexistent'),None)

    def test_nonfinite_reference(self):
        with self.assertRaises(ValueError):Expanding((math.nan,0.),(1.,0.),(2.,0.))

class R9ORunnerTests(unittest.TestCase):
    def test_selective_sentinels(self):
        import json
        from defensive_network_disruption.data.representation_projection import ALIASES
        with tempfile.TemporaryDirectory() as d:
            p=Path(d).resolve()/'prepared'
            row={'alias':ALIASES[0],'carrier':[0.,0.],'defenders':[[3.,1.]],'receivers':['FORBIDDEN']*8+[[8.,0.],'FORBIDDEN']}
            p.write_text('FORBIDDEN_ROW\n'*5+json.dumps(row)+'\nFORBIDDEN_ROW\n')
            result=R.selected(p,{'state':'5','edges':['8']})
            self.assertEqual(result['receiver'],(8.,0.));self.assertNotIn('receivers',result)

    def test_runner_shared_integrity_failure_closes_without_access(self):
        from unittest.mock import patch
        from defensive_network_disruption.validation import r9j_linear_publication as linear
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d).resolve()
            with patch.object(R,'preflight',return_value={'protocol':'0'*64,'sources':{}}), \
                 patch.object(R,'sha',wraps=R.sha) as hasher, \
                 patch.object(R,'selected',side_effect=AssertionError('forbidden_access')) as access:
                # Missing retained authority is handled before any journal replay/access.
                with patch.object(R,'OLD',folder/'missing'):
                    result=R.diagnose(folder/'output')
                self.assertTrue(result['valid']);self.assertEqual(result['numerical'],'NF')
                access.assert_not_called()
            with self.assertRaises(FileExistsError):
                with patch.object(R,'preflight',return_value={'protocol':'0'*64,'sources':{}}):R.diagnose(folder/'output')
            manifest=folder/'output/authority.json'
            manifest.write_text('{}')
            with self.assertRaises(ValueError):R.publication_check(folder/'output')
