"""Discoverable synthetic production-path tests; no governed audit execution."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import importlib.util
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import warnings

import numpy as np
from scipy.integrate import IntegrationWarning
from defensive_network_disruption.geometry import production_verification as p
from defensive_network_disruption.geometry import verification_repair as v

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('session14i_tests',ROOT/'scripts/session_14i_signature_repair.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)


class Session14iAcceptanceTests(unittest.TestCase):
    def test_independent_continuity_and_discontinuous_surrogate(self):
        for candidate in ('isotropic','expanding','constant_width'):
            self.assertTrue(p.check_continuity(candidate,(1.,-2.),((4.,2.),)))
        with patch.object(p,'independent_continuity',return_value=True):
            with self.assertRaises(p.GateFailure):p.check_continuity('isotropic',(0,0),((2,0),))

    def test_actual_field_oracle_mismatch_blocks(self):
        with patch.object(p,'scalar_oracle',return_value=-1.):
            with self.assertRaises(p.GateFailure):p.check_continuity('isotropic',(0,0),((2,0),))

    def test_tiny_sign_controls(self):
        for value in (1e-8,1e-12,1e-15,1e-200):
            self.assertTrue(v.opposite_nonzero_signs(value,-value))
            self.assertFalse(v.opposite_nonzero_signs(value,value))
        self.assertFalse(v.opposite_nonzero_signs(0.,-1.))
        self.assertFalse(v.opposite_nonzero_signs(0.,0.))

    def test_certified_enclosure_consumed_without_collapse(self):
        function=p.engineering_functions()['exact_plateau']
        envelope=v.find_verified_envelope(function,grid_intervals=128)
        partitions=p.certified_partitions(function,envelope)
        bounds=[x for tie in envelope.tie_intervals for b in (tie.start,tie.end) if b for x in (b.outside,b.inside)]
        self.assertEqual(len(bounds),4)
        self.assertTrue(set(bounds)<=set(partitions))
        visited=[]
        def fake_quad(function,lower,upper,**kwargs):
            visited.append((lower,upper));return ((upper-lower)*function((lower+upper)/2),0.)
        with patch.object(p,'quad',side_effect=fake_quad): result=p.adaptive_maximum(function,partitions,1e-13)
        self.assertAlmostEqual(result,.6)
        self.assertEqual(visited,list(zip(partitions[:-1],partitions[1:])))
        self.assertEqual(sum(np.nextafter(a,b)==b for a,b in visited),2)

    def test_bad_enclosure_rejected(self):
        function=p.engineering_functions()['exact_plateau']; env=v.find_verified_envelope(function,grid_intervals=128)
        tie=env.tie_intervals[0];bad=replace(tie.start,outside=tie.start.outside-.01)
        env=replace(env,tie_intervals=(replace(tie,start=bad),))
        with self.assertRaises(p.GateFailure):p.certified_partitions(function,env)

    def test_constant_piecewise_and_split_oracles(self):
        function=p.engineering_functions()['constant']
        parts=(0.,.251,float(np.nextafter(.251,1.)),.749,1.)
        self.assertAlmostEqual(p.adaptive_maximum(function,parts,1e-13),.6)
        value,count=p.split_simpson(function,parts,256)
        self.assertAlmostEqual(value,.6);self.assertGreater(count,256)

    def test_maximum_crossing_reference(self):
        function=p.engineering_functions()['crossing']; env=v.find_verified_envelope(function,grid_intervals=128)
        record=p.maximum_checks(function,env,(),True)
        self.assertAlmostEqual(record['piecewise'],.75)
        self.assertIn(.5,record['partitions'])
        self.assertAlmostEqual(record['split_fine'],.75)

    def test_joint_vector_oracle_unchanged(self):
        case=r.injection_case()
        record=p.verify_case(**case)
        self.assertEqual(record['intervals'],512)
        for value in record['estimates'].values(): self.assertAlmostEqual(value,math.exp(-.5),places=14)
        old={'intervals':record['intervals'],'estimates':record['estimates']}
        again=p.verify_case(**case,historical=old)
        self.assertEqual(record['estimates'],again['estimates'])
        with self.assertRaises(p.GateFailure):p.verify_case(**case,historical={**old,'intervals':1024})

    def test_failure_injections_use_pipeline(self):
        # Every injected fault enters the real entrypoint; no synthetic ready toggles.
        records,passed=r.failure_injections()
        self.assertTrue(passed)
        self.assertEqual(len(records),12)
        self.assertTrue(all(x['accepted_count']==0 and x['blocked'] for x in records[1:]))

    def test_actual_brent_failure_reaches_pipeline(self):
        case=dict(candidate='isotropic',origin=(0,0),receiver=(20,0),defenders=((5,1),(15,1)),references={})
        with patch.object(v,'brentq',side_effect=RuntimeError('synthetic root failure')):
            # Pair equality is at an exact node here; shifted defender forces a bracket.
            case['defenders']=((5,1),(15.01,1))
            outcome=p.run_pipeline([case],{'x':'x'},{'x':'x'},True)
        self.assertFalse(outcome.readiness.ready);self.assertEqual(outcome.accepted,())

    def test_warning_is_error(self):
        def warned(*args,**kwargs):warnings.warn('synthetic',IntegrationWarning)
        with patch.object(p,'quad',side_effect=warned):
            out=p.run_pipeline([r.injection_case()],{'x':'x'},{'x':'x'},True)
        self.assertFalse(out.readiness.ready);self.assertEqual(out.failure,'IntegrationWarning')

    def test_missing_enforcement_cannot_be_pass(self):
        outcome=p.run_pipeline([r.injection_case()],{'x':'x'},{'x':'x'},False)
        self.assertFalse(outcome.readiness.ready);self.assertEqual(outcome.accepted,())

    def test_atomic_concurrent_markers_and_no_rerun(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker=Path(tmp).resolve()/'run.marker'
            def attempt(_):
                try:p.claim_execution(marker);return True
                except FileExistsError:return False
            with ThreadPoolExecutor(max_workers=2) as pool: values=list(pool.map(attempt,range(2)))
            self.assertEqual(sum(values),1)
            with self.assertRaises(FileExistsError):p.claim_execution(marker)

    def test_unsafe_and_unapproved_inputs(self):
        for path in ('../escape','/tmp/escape','data/anything','outputs/receiver_ranking_m0_m1/qc.json'):
            with self.assertRaises(ValueError):r.approved_input(path)
        with tempfile.TemporaryDirectory() as tmp,patch.object(r,'ROOT',Path(tmp).resolve()):
            (Path(tmp)/'linked').symlink_to('/tmp')
            with self.assertRaises(ValueError):r.safe('linked/file')
            with self.assertRaises(p.GateFailure):p.claim_execution(Path(tmp)/'linked/marker')

    def test_finite_json_duplicate_schema_guards(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'case.json'
            for text in ('{"x":1,"x":2}','{"x":NaN}'):
                path.write_text(text)
                with self.assertRaises(ValueError):r.read_json(path)
        with self.assertRaises(ValueError):r.strict_keys({'a':1,'extra':2},{'a'})

    def test_frozen_fixture_extraction_and_reference_membership(self):
        self.assertEqual(len(r.fixture_rows()),36)
        cases=list(r.authority_cases());self.assertEqual(len(cases),108)
        self.assertEqual(sum(len(x['references']) for _,x in cases),366)
        self.assertEqual(sum(x['historical_failure'] for _,x in cases),4)

    def test_route_guard_and_commands(self):
        r.route_guard()
        source=(ROOT/r.CODE[0]).read_text()
        self.assertIn("choices=('preflight','audit','publication-check')",source)
        self.assertNotIn('record-review',source)

    def test_failure_closure_schema_hashes_and_no_rerun(self):
        original_environment=r.environment()
        with tempfile.TemporaryDirectory() as tmp,patch.object(r,'ROOT',Path(tmp).resolve()), \
             patch.object(r,'preflight'),patch.object(r,'git',return_value='synthetic_commit'), \
             patch.object(r,'environment',return_value=original_environment), \
             patch.object(p,'engineering_checks',return_value=[{
                 'fixture':'multiway_plateau','passed':False,'reason':'mapped_record_mismatch',
                 'permutations_checked':2,'partition_count':6,'boundary_enclosures':[],
                 'different_sections':['tie_intervals']}]):
            real_digest=r.digest
            def digest(path):
                if str(path).startswith(str(r.OUT)+'/'): return real_digest(path)
                return '0'*64
            with patch.object(r,'digest',side_effect=digest):
                self.assertEqual(r.audit(),2)
                self.assertEqual(r.validate(),r.BLOCKED)
                self.assertTrue(r.safe(r.OUT/'local/failure.json').exists())
                self.assertTrue(r.safe(r.OUT/'local/closed.marker').exists())
                with self.assertRaises(FileExistsError):r.audit()
                qc=r.safe(r.OUT/'qc.json');qc.write_text(qc.read_text()+' ')
                with self.assertRaises(ValueError):r.validate()

    def test_existing_output_and_marker_prevent_runner(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(r,'ROOT',Path(tmp).resolve()),patch.object(r,'ledger'):
            r.begin()
            with self.assertRaises(FileExistsError):r.begin()
            self.assertTrue(r.safe(r.OUT/'local/execution.marker').exists())


if __name__=='__main__': unittest.main()
