"""Provider-free tie evidence, frozen oracles and explicit routing."""
from dataclasses import replace
from fractions import Fraction as F
from pathlib import Path
import time
import unittest
from unittest.mock import patch

from defensive_network_disruption.geometry import r9ad_tie_regions as r
from defensive_network_disruption.geometry import r9ad_adapter as adapter
from defensive_network_disruption.geometry import r9t_adapter as historical
from defensive_network_disruption.geometry import r9ad_envelope as envelope
from defensive_network_disruption.validation import r9ad_controls as controls
from defensive_network_disruption.validation.r9t_acceptance import primitive
from defensive_network_disruption.validation.r9j_evidence import canonical


class TieRegionTests(unittest.TestCase):
    def test_fourteen_frozen_controls(self):
        rows = controls.controls()
        self.assertEqual(tuple(row['fixture'] for row in rows), controls.NAMES)
        self.assertTrue(all(row['passed'] for row in rows), rows)

    def test_ten_negative_families(self):
        rows = controls.negatives()
        self.assertEqual(tuple(row['fixture'] for row in rows), controls.NEGATIVES)
        self.assertTrue(all(row['blocked'] for row in rows), rows)

    def test_both_functions_and_all_competitors_bounded(self):
        fields = controls.fields_for('maximal')
        with patch.object(controls.Polynomial,'bounds',autospec=True,
                          side_effect=controls.Polynomial.bounds) as spy:
            proof = r.review(fields,r.proposal(fields,(0,1),F(0),F(1)),deadline=time.monotonic()+2)
        self.assertEqual(spy.call_count,5)
        self.assertEqual(proof.bound_calls,5)
        self.assertEqual(r.disposition(proof),'retain')

    def test_zero_maximum_has_no_positive_owner_authority(self):
        fields = (controls.Polynomial(0),)*3
        proof = r.review(fields,r.proposal(fields,(0,1),F(0),F(1)),deadline=time.monotonic()+2)
        self.assertEqual(r.disposition(proof),'exclude_inactive')

    def test_signed_zero_is_exact_zero_without_owner_claim(self):
        fields = (controls.Polynomial(-0.0),controls.Polynomial(0.0))
        proof = r.review(fields,r.proposal(fields,(0,1),F(0),F(1)),deadline=time.monotonic()+2)
        self.assertEqual(r.disposition(proof),'exclude_inactive')

    def test_interval_limits_preserve_coverage_and_block(self):
        fields = controls.fields_for('maximal_left')
        proof = r.review(fields,r.proposal(fields,(0,1),F(0),F(1)),deadline=time.monotonic()+2,max_depth=2,max_leaves=4)
        self.assertEqual(proof.cells[0].left,0)
        self.assertEqual(proof.cells[-1].right,1)
        self.assertLessEqual(len(proof.cells),4)
        self.assertTrue(proof.exhausted)
        with self.assertRaises(r.VerificationError):r.disposition(proof)

    def test_deadline_blocks_before_first_bound(self):
        fields = controls.fields_for('maximal')
        with patch.object(controls.Polynomial,'bounds',side_effect=AssertionError('evaluated')):
            with self.assertRaises(TimeoutError):
                r.review(fields,r.proposal(fields,(0,1),F(0),F(1)),deadline=0)

    def test_deterministic_canonical_proofs(self):
        fields=controls.fields_for('maximal'); item=r.proposal(fields,(0,1),F(0),F(1))
        a=r.review(fields,item,deadline=time.monotonic()+2)
        b=r.review(fields,item,deadline=time.monotonic()+2)
        self.assertEqual(canonical(primitive(a)),canonical(primitive(b)))

    def test_corrupted_proof_rejected_without_field_evaluation(self):
        fields=controls.fields_for('maximal'); item=r.proposal(fields,(0,1),F(0),F(1))
        proof=r.review(fields,item,deadline=time.monotonic()+2)
        forged=replace(proof,cells=(replace(proof.cells[0],positive=False),))
        with patch.object(controls.Polynomial,'bounds',side_effect=AssertionError('reevaluation')):
            with self.assertRaises(r.VerificationError):r.validate_coverage(forged)

    def test_actual_adapter_preserves_ordinary_result(self):
        args=('isotropic',(0.,0.),(10.,0.),((5.,2.),))
        kw=dict(root=Path(__file__).resolve().parents[1],authority_context={'alias':'synthetic_r9ad'})
        before=historical.evaluate(*args,**kw)
        with patch.object(envelope,'plateaus',wraps=envelope.plateaus) as spy:
            after=adapter.evaluate(*args,**kw)
        self.assertEqual(before,after)
        self.assertEqual(spy.call_count,2)

    def test_no_historical_runtime_substitution(self):
        self.assertIs(adapter.independent_maximum,historical.independent_maximum)
        self.assertIsNot(adapter.owner,historical.owner)
        self.assertIs(adapter.owner.localize,historical.owner.localize)

    def test_duplicate_field_tie_with_inactive_prefix_preserved(self):
        args=('constant_width',(0.,0.),(20.,0.),((5.,1.),(5.,-1.)))
        kw=dict(root=Path(__file__).resolve().parents[1],authority_context={'alias':'synthetic_r9ad'})
        self.assertEqual(adapter.evaluate(*args,**kw),historical.evaluate(*args,**kw))

    def test_nonfinite_engineering_values_rejected(self):
        with self.assertRaises(ValueError): controls.Polynomial(float('nan'))

if __name__=='__main__': unittest.main()
