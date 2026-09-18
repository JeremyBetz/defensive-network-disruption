import math
from fractions import Fraction as F
from pathlib import Path
import tempfile
import time
import unittest

from defensive_network_disruption.geometry import r9j_reference as r
from defensive_network_disruption.validation import r9j_evidence as e


class ReferenceTests(unittest.TestCase):
    def test_sqrt_exact_and_irrational(self):
        for q in (F(0), F(1), F(2), F(3, 7), F(10**12)):
            x = r.sqrt_bounds(q)
            self.assertLessEqual(x.lo*x.lo, q); self.assertGreaterEqual(x.hi*x.hi, q)

    def test_outward_operations(self):
        a = r.Bounds.point(F(1, 3)); b = r.Bounds.point(F(2, 7))
        for interval, exact in ((a+b, F(13,21)), (a*b, F(2,21)), (a/b, F(7,6)), (a-b,F(1,21))):
            self.assertLessEqual(interval.lo, exact); self.assertGreaterEqual(interval.hi, exact)
            lo, hi = interval.floats()
            self.assertLessEqual(F.from_float(lo), interval.lo)
            self.assertGreaterEqual(F.from_float(hi), interval.hi)

    def test_exp_remainder_against_separate_exact_series(self):
        for x in (F(0), F(1, 8), F(1,2), F(2), F(5)):
            value = r.exp_negative(x)
            term = total = F(1)
            for n in range(1, 151):
                term *= -x/n; total += term
            error = abs(term*x/151)
            self.assertLessEqual(value.lo, total-error)
            self.assertGreaterEqual(value.hi, total)

    def test_constant_and_zero(self):
        one = r.Integrand.coefficients(1, 10, 0)
        zero = r.Integrand.coefficients(1, -10, 0)
        for field, expected in ((one, F(3,4)), (zero,F(0))):
            result = r.enclose((field,), (F(1,4),F(1)))
            self.assertTrue(result['eligible'])
            self.assertEqual(result['bound'].lo, expected)
            self.assertEqual(result['bound'].hi, expected)

    def test_smoothstep_polynomial_antiderivative(self):
        result = r.enclose((r.Integrand.coefficients(1, 2, 0),), (F(1,2),F(1)))
        self.assertTrue(result['eligible'])
        self.assertLessEqual(result['bound'].lo, F(1,4))
        self.assertGreaterEqual(result['bound'].hi, F(1,4))

    def test_taylor_gaussian_integral(self):
        a, b = F(1,4), F(1)
        result = r.enclose((r.Integrand.coefficients(1,10,1),),(a,b))
        exact = sum(((-1)**n*(b**(2*n+1)-a**(2*n+1))/F(math.factorial(n)*(2*n+1)) for n in range(101)),F(0))
        remainder = (b**203-a**203)/F(math.factorial(101)*203)
        self.assertTrue(result['eligible'])
        self.assertLessEqual(result['bound'].lo, exact-remainder)
        self.assertGreaterEqual(result['bound'].hi, exact)

    def test_onset_straddling_without_detector(self):
        result = r.enclose((r.Integrand.coefficients(1,2,0),),(F(0),F(1)))
        self.assertTrue(result['eligible'])
        self.assertLessEqual(result['bound'].lo,F(1,4)); self.assertGreaterEqual(result['bound'].hi,F(1,4))

    def test_crossing_and_missed_switch_are_bounded(self):
        fields = (r.Integrand.coefficients(1,10,2), r.Integrand.coefficients(4,10,F(1,2)))
        result = r.enclose(fields,(F(0),F(1)))
        self.assertTrue(result['eligible'])
        self.assertGreater(result['leaves'],1)
        refined = r.enclose(fields,(F(0),F(1,2),F(1)))
        self.assertLessEqual(max(result['bound'].lo,refined['bound'].lo), min(result['bound'].hi,refined['bound'].hi))

    def test_exact_tie_not_tolerance_tie(self):
        fields = r.from_geometry((0.,0.),(8.,0.),((1.,1.),(1.,1.)))
        self.assertEqual(len(fields),1)
        other = r.from_geometry((0.,0.),(8.,0.),((1.,1.),(1.,math.nextafter(1.,2.))))
        self.assertEqual(len(other),2)

    def test_point_interval_decisions(self):
        ref=r.Bounds(F(1,4),F(1,4))
        self.assertTrue(r.compare((.25,.25),ref,1e-10)['accurate'])
        self.assertTrue(r.compare((.5,.5),ref,1e-10)['inaccurate'])
        wide=r.Bounds(F(0),F(1))
        decision=r.compare((.25,.25),wide,1e-10)
        self.assertFalse(decision['accurate']);self.assertFalse(decision['inaccurate'])

    def test_signed_zero_finite_and_geometry_rejection(self):
        self.assertEqual(r.rational(-0.),r.rational(0.))
        for bad in (math.nan,math.inf,True,1):
            with self.assertRaises(ValueError):r.rational(bad)
        with self.assertRaises(ValueError):r.from_geometry((0.,0.),(1.,0.),((0.,0.),))

    def test_limits_preserve_enclosure(self):
        fields=(r.Integrand.coefficients(1,3,2),)
        for kwargs, reason in (({'max_leaves':1},'leaf_limit'),({'max_depth':0},'depth_limit'),({'deadline':0},'deadline')):
            result=r.enclose(fields,(F(0),F(1)),**kwargs)
            self.assertFalse(result['eligible']);self.assertEqual(result['reason'],reason)
            self.assertLessEqual(result['bound'].lo,result['bound'].hi)

    def test_deterministic_bounds(self):
        field=r.Integrand.coefficients(1,2,0)
        first=r.enclose((field,),(F(0),F(1)));second=r.enclose((field,),(F(0),F(1)))
        self.assertEqual(first['bound'],second['bound']);self.assertEqual(first['leaves'],second['leaves'])


class EvidenceTests(unittest.TestCase):
    def test_create_once_and_deterministic_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp).resolve()/'record.json';e.put(p,{'v':-.0})
            self.assertEqual(p.read_bytes(),e.canonical({'v':-.0}))
            with self.assertRaises(FileExistsError):e.put(p,{'v':0.})

    def test_nonfinite_and_duplicate_keys(self):
        with self.assertRaises(ValueError):e.canonical({'x':math.inf})
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp).resolve()/'bad';p.write_text('{"x":1,"x":2}')
            with self.assertRaises(ValueError):e.load(p)

    def test_emergency_independent_of_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp).resolve()/'emergency.json'
            try:raise RuntimeError('synthetic_original')
            except RuntimeError as error:e.emergency(p,error,'synthetic')
            self.assertIn('synthetic_original',e.load(p)['traceback'])

    def test_strict_schema_and_extra_fields(self):
        item=e.empty_public()['authority.json'];item['evidence_sha256']='a'*64
        e.validate_record('authority.json',item)
        item['extra']=1
        with self.assertRaises(ValueError):e.validate_record('authority.json',item)


if __name__ == '__main__': unittest.main()
