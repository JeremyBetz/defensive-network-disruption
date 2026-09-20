"""Provider-free canonicalization, proof separation and exact preservation."""
from dataclasses import replace
from fractions import Fraction as F
import inspect
import math
from pathlib import Path
import time
import unittest
from unittest.mock import patch
import numpy as np
from defensive_network_disruption.geometry import r9t_transition as r,r9t_adapter as adapter,r9r_adapter as prior
from defensive_network_disruption.validation import r9t_acceptance as a,r9t_authority as auth,r9t_evidence as e
ROOT=Path(__file__).resolve().parents[1]

class TransitionTests(unittest.TestCase):
    def test_fifteen_exact_controls_and_determinism(self):
        observed=[]
        rows=a.trace_controls(lambda label,v:observed.append(v) or a.digest(v))
        self.assertEqual(tuple(x['fixture'] for x in rows),a.FIXTURES)
        self.assertTrue(all(x['passed'] for x in rows),rows)
        self.assertEqual(rows,a.trace_controls())
        for row,detail in zip(rows,observed):self.assertEqual(e.trace_control_observation(detail),row['observed'])

    def test_ten_negative_families(self):
        rows=a.negative_controls();self.assertEqual(tuple(x['fixture'] for x in rows),a.NEGATIVES)
        self.assertTrue(all(x['blocked'] for x in rows))

    def test_pure_rule_has_no_field_calls(self):
        args=a.fixture('NNZPNZPPP')
        with patch.object(r.old,'_pair',side_effect=AssertionError('no_probes')),patch.object(r.PairAuthority,'bounds',side_effect=AssertionError('no_reference')):
            result=r.canonicalize(*args)
        self.assertEqual(result.canonical_index,6);self.assertEqual(result.suffix_length,3)
        self.assertEqual(result.transition.last_pre,r.old._float(args[2][4].key))
        self.assertEqual(result.transition.zero_start,r.old._float(args[2][5].key))

    def test_nonzero_gap_has_no_fabricated_zero_metadata(self):
        result=r.canonicalize(*a.fixture('NNZPNZPPP'))
        # A different reentry leaves a strict pre then earlier post and zero; the
        # legacy gap is interpreted only relative to the last strict pre witness.
        result=r.canonicalize(*a.fixture('NNPNPZPPP'))
        self.assertIsNone(result.transition.zero_start);self.assertIsNone(result.transition.zero_end)

    def test_signed_zero_preserved_and_interrupts_suffix(self):
        args=list(a.fixture('NNNNZPPPP'));p=list(args[2]);p[4]=replace(p[4],difference=-0.)
        args[2]=tuple(p);args[3]=tuple((q.key,q.sign) for q in p)
        result=r.canonicalize(*args)
        self.assertEqual(result.canonical_index,5)
        self.assertEqual(a.primitive(result)['probes'][4]['difference']['hex'],'-0x0.0p+0')
        restored=auth.evidence(a.primitive(result));self.assertEqual(a.primitive(restored),a.primitive(result))

    def test_pair_reversal_preserves_coordinate(self):
        args=list(a.fixture('NNZPNZPPP'));one=r.canonicalize(*args)
        inverse=a.fixture('PPZN PZNNN'.replace(' ',''))
        two=r.canonicalize(*inverse)
        self.assertEqual(one.transition.first_post,two.transition.first_post)

    def test_clean_historical_records_exact(self):
        for sequence in ('NNNNPPPPP','NNNNZPPPP','NNNZZZPPP','PPPPNNNNN'):
            args=a.fixture(sequence);authority=args[0];by={p.key:p.difference for p in args[2]}
            function=lambda ts:np.column_stack(([by[r.old._bits(float(t))] for t in ts],np.zeros_like(ts)))
            old=r.inherited.inspect_production(function,(0,1),*authority.enclosure,authority.lower,authority.upper,authority.before,authority.after,deadline=time.monotonic()+5)
            new=r.inspect_production(function,(0,1),authority,deadline=time.monotonic()+5)
            self.assertEqual(old.legacy(),new.legacy());self.assertEqual(old.floats_inspected,len(new.probes))

    def test_no_widening_to_rescue_short_suffix(self):
        args=a.fixture('NPNPNPNNP');values={p.key:p.difference for p in args[2]};calls=[]
        def function(ts):
            calls.extend(map(float,ts));return np.column_stack(([values[r.old._bits(float(t))] for t in ts],np.zeros_like(ts)))
        with self.assertRaisesRegex(ValueError,'suffix_too_short'):r.inspect_production(function,(0,1),args[0],deadline=time.monotonic()+5)
        self.assertEqual(len(calls),9)

    def test_window_expansion_same_order_as_inherited(self):
        authority=a.fixture()[0]
        # Wider structural and witness bounds permit unchanged deterministic widening.
        lower,upper=.49,.51;math=a.Linear(F(1,2));top=r.classify(math,F.from_float(lower),F.from_float(upper),deadline=time.monotonic()+2)
        c=r.CrossingAuthority(top,(F(1,2),F(1,2)),lower,upper,-1,1,(lower,upper))
        middle=r.old._bits(.5);orders=[]
        def run(new):
            calls=[]
            def f(ts):
                calls.extend(map(float,ts));return np.column_stack(([float(r.old._bits(float(t))-(middle+20)) for t in ts],np.zeros_like(ts)))
            if new:r.inspect_production(f,(0,1),c,deadline=time.monotonic()+5)
            else:r.inherited.inspect_production(f,(0,1),F(1,2),F(1,2),lower,upper,-1,1,deadline=time.monotonic()+5)
            return calls
        self.assertEqual(run(False),run(True))

    def test_corrupt_cache_duplicate_missing_or_forged_result(self):
        c,w,p,k=a.fixture()
        for bad in (p[:-1],(*p[:-1],p[0])):
            with self.assertRaises(ValueError):r.canonicalize(c,w,bad,k)
        with self.assertRaises(ValueError):r.canonicalize(c,w,p,(*k[:-1],(k[-1][0],-1)))
        result=r.canonicalize(c,w,p,k)
        with self.assertRaises(ValueError):r.validate_evidence(replace(result,suffix_length=999))

    def test_bad_mathematical_authority_blocks(self):
        c,w,p,k=a.fixture()
        for label in ('A','C','D','E','F','G'):
            with self.assertRaises(ValueError):replace(c,topology=replace(c.topology,classification=label))
        with self.assertRaises(ValueError):replace(c,topology=replace(c.topology,complete=False))
        with self.assertRaises(ValueError):replace(c,right_sign=-1)
        with self.assertRaises(ValueError):replace(c,enclosure=(F(0),F(1)))

    def test_no_extra_probes_after_interrupted_sink(self):
        c,*_=a.fixture();calls=[]
        def f(ts):calls.extend(ts);return np.column_stack((ts-.5,ts*0))
        def sink(**v):
            if v['kind']=='probe_completed':raise OSError('interrupted_receipt')
        with self.assertRaises(OSError):r.inspect_production(f,(0,1),c,deadline=time.monotonic()+5,sink=sink)
        self.assertEqual(len(calls),1)

    def test_unchanged_primitives_and_degenerate(self):
        for name in ('independent_maximum','controlled_vector','values_for_components','validate_geometry'):
            self.assertIs(getattr(adapter,name),getattr(prior,name))
        with patch.object(r,'canonical_geometry',side_effect=AssertionError('degenerate')):
            args=('expanding',(0.,0.),(0.,0.),((3.,1.),))
            self.assertEqual(adapter.evaluate(*args,root=ROOT,authority_context={}),prior.evaluate(*args,root=ROOT,authority_context={}))

    def test_actual_inspector_resolves_oscillatory_controls(self):
        for sequence,expected in (('NNZPNZPPP',6),('NNNNPNPPP',6),('NPNPNPNPP',7)):
            c,w,p,k=a.fixture(sequence);values={v.key:v.difference for v in p};calls=[]
            def function(ts):
                calls.extend(map(float,ts));return np.column_stack(([values[r.old._bits(float(t))] for t in ts],np.zeros_like(ts)))
            result=r.inspect_production(function,(0,1),c,deadline=time.monotonic()+5)
            self.assertEqual(result.canonical_index,expected);self.assertEqual(len(calls),9)
            self.assertEqual(a.primitive(result),a.primitive(r.canonicalize(c,w,p,k)))

    def test_two_crossings_cannot_merge_authority(self):
        middle=r.old._bits(.5);first=F.from_float(r.old._float(middle-8));second=F.from_float(r.old._float(middle+8))
        authority=a.TwoRoots(first,second)
        # Exact polynomial values at the midpoint and endpoints prove two roots;
        # the merged interval therefore cannot become one simple crossing.
        lower,upper=r.old._float(middle-12),r.old._float(middle+12)
        top=r.classify(authority,F.from_float(lower),F.from_float(upper),deadline=time.monotonic()+5)
        self.assertNotEqual(top.classification,'B')
        with self.assertRaises(ValueError):r.CrossingAuthority(top,(first,second),lower,upper,-1,1,(lower,upper))

    def test_complete_108_366_399_historical_regression(self):
        rows=a.historical_regression(ROOT)
        self.assertEqual((len(rows),sum(x['components'] for x in rows),sum(x['permutations'] for x in rows)),(108,366,399))
        self.assertTrue(all(x['status']=='passed' for x in rows),[x for x in rows if x['status']!='passed'])

    def test_no_geometry_reload_or_identifier_selection(self):
        text=inspect.getsource(r)
        for token in ('read_bytes','open(','mock.patch','setattr(','selected_geometry','state =='):
            self.assertNotIn(token,text)

if __name__=='__main__':unittest.main()
