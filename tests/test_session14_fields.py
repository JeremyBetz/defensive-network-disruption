"""Synthetic production-path tests; no empirical fixtures or model calls."""
import ast
import contextlib
from dataclasses import FrozenInstanceError
import importlib.util
import io
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from defensive_network_disruption.geometry.occlusion_fields import (
    CANDIDATES, CarrierOriginField, FieldError, QuadratureError,
    combine, simpson_average, validate_geometry)

spec=importlib.util.spec_from_file_location('session14_runner',Path(__file__).parents[1]/'scripts/session_14_occlusion_fields.py')
runner=importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class FieldTests(unittest.TestCase):
    def test_fixed_parameters_and_immutability(self):
        with self.assertRaises(FieldError): CarrierOriginField("alternate")
        with self.assertRaises(FrozenInstanceError): CarrierOriginField("isotropic").candidate="x"
        with self.assertRaises(TypeError): CarrierOriginField("isotropic",sigma=3)

    def test_invalid_coordinates_and_origins(self):
        for ds in ([],[[0,0]],[[1e-10,0]],[[float('inf'),0]],[[True,False]],[["3","2"]]):
            with self.subTest(ds=ds), self.assertRaises(FieldError): validate_geometry((0,0),ds)

    def test_radial_oracle(self):
        f=CarrierOriginField("isotropic")
        v=f.individual_values((0,0),((5,0),),((5,0),(7,0),(5,2)))[:,0]
        np.testing.assert_allclose(v,[1,math.exp(-.5),math.exp(-.5)],rtol=0,atol=1e-15)

    def test_onset_and_behind_receiver(self):
        for name in CANDIDATES[1:]:
            f=CarrierOriginField(name)
            np.testing.assert_array_equal(f.individual_values((0,0),((5,0),),((0,0),(5,0),(5.5,0),(6,0),(40,0)))[:,0],[0,0,.5,1,1])
            self.assertEqual(f.individual_values((0,0),((25,0),),((20,0),))[0,0],0)

    def test_lateral_monotonicity_and_reflection(self):
        for name in CANDIDATES:
            f=CarrierOriginField(name)
            a=f.individual_values((0,0),((5,0),),[(10,y) for y in (0,1,2,5)])[:,0]
            self.assertTrue(np.all(np.diff(a)<=0))
            np.testing.assert_array_equal(a,f.individual_values((0,0),((5,0),),[(10,-y) for y in (0,1,2,5)])[:,0])

    def test_expansion_is_distinct(self):
        a=CarrierOriginField("expanding").individual_values((0,0),((5,0),),((20,5),))[0,0]
        b=CarrierOriginField("constant_width").individual_values((0,0),((5,0),),((20,5),))[0,0]
        self.assertGreater(a,b)

    def test_translation_rotation_invariance(self):
        b=np.array([0.,0.]);ds=np.array([[5.,0.],[12.,2.]])
        q=np.array([[6.,1.],[20.,5.]])
        c,s=math.cos(.7),math.sin(.7);rotation=np.array([[c,-s],[s,c]])
        for name in CANDIDATES:
            f=CarrierOriginField(name);expected=f.individual_values(b,ds,q)
            np.testing.assert_allclose(f.individual_values(b+[11,-7],ds+[11,-7],q+[11,-7]),expected,rtol=1e-12,atol=1e-12)
            np.testing.assert_allclose(f.individual_values(b@rotation.T,ds@rotation.T,q@rotation.T),expected,rtol=1e-12,atol=1e-12)

    def test_combination_bounds_duplicates_permutation(self):
        a=np.array([[0.,0.,0.],[.2,.3,.8],[1.,.5,0.]])
        np.testing.assert_array_equal(combine(a,"union"),combine(a[:,::-1],"union"))
        np.testing.assert_allclose(combine(a,"union"),[0,1-.8*.7*.2,1],atol=1e-15)
        self.assertTrue(np.all(combine(a,"union")>=combine(a,"maximum")))
        self.assertGreater(combine([[.3,.3]],"union")[0],.3)
        for bad in ([[float('nan')]],[[1.1]], [[]]):
            with self.assertRaises(FieldError): combine(bad,"union")

    def test_union_tiny_values(self):
        self.assertAlmostEqual(combine([[1e-20,1e-20]],"union")[0],2e-20,delta=1e-34)

    def test_simpson_polynomial_and_rejections(self):
        t=np.linspace(0,1,81)
        np.testing.assert_allclose(simpson_average(np.column_stack((np.ones_like(t),t,t*t,t**3))),[1,.5,1/3,.25],rtol=0,atol=1e-15)
        with self.assertRaises(FieldError): simpson_average(np.ones((4,1)))

    def test_degenerate_endpoint(self):
        for name in CANDIDATES:
            f=CarrierOriginField(name);r=f.summarize_edge((0,0),(0,0),((5,2),))
            self.assertEqual(r.receiver_individual,r.segment_individual)
            self.assertEqual(r.coarse_intervals,0)

    def test_quadrature_failure_has_no_fallback(self):
        with patch('defensive_network_disruption.geometry.occlusion_fields.simpson_average',side_effect=[np.zeros(3),np.ones(3)]) as p:
            with self.assertRaises(QuadratureError) as ctx: CarrierOriginField("isotropic").summarize_edge((0,0),(20,0),((5,2),))
            self.assertEqual(p.call_count,2)
            self.assertEqual(ctx.exception.diagnostics['absolute_difference'],1.)

    def test_no_io_model_or_fitting_calls(self):
        p=Path(__file__).parents[1]/'src/defensive_network_disruption/geometry/occlusion_fields.py'
        tree=ast.parse(p.read_text())
        names={n.id for n in ast.walk(tree) if isinstance(n,ast.Name)}
        self.assertFalse(names & {'open','evaluate_options','FrozenOptionModel','urlopen','minimize','fit','load'})

    def test_reproducibility(self):
        for name in CANDIDATES:
            f=CarrierOriginField(name)
            np.testing.assert_array_equal(f.combined_values((0,0),((5,2),(10,-1)),((20,0),(5,3))),f.combined_values((0,0),((5,2),(10,-1)),((20,0),(5,3))))

    def test_path_and_output_namespace_rejection(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(runner,'ROOT',Path(tmp).resolve()):
            (runner.ROOT/'sym').symlink_to('/tmp')
            for path in ('../escape','sym/file'):
                with self.assertRaises(PermissionError):runner.safe(Path(path))
            with self.assertRaises(PermissionError):runner.atomic_new(Path('data/file'),{})

    def test_runner_has_no_empirical_or_model_route(self):
        text=Path(runner.__file__).read_text();tree=ast.parse(text)
        names={n.id for n in ast.walk(tree) if isinstance(n,ast.Name)}
        self.assertFalse(names & {'evaluate_options','FrozenOptionModel','OptionState','urlopen','minimize'})
        self.assertNotIn('population.jsonl',text)
        with tempfile.TemporaryDirectory() as tmp, patch.object(runner,'ROOT',Path(tmp).resolve()):
            with self.assertRaisesRegex(RuntimeError,'preempirical_implementation_gate_not_complete'):runner.unavailable_stage()

    def test_blocked_closure_immutability_and_marker(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(runner,'ROOT',Path(tmp).resolve()), \
             patch.object(runner,'preflight'),patch.object(runner,'historical'),patch.object(runner,'committed'), \
             patch.object(runner,'git',return_value='synthetic_commit'),patch.object(runner,'code_hashes',return_value={}), \
             patch.object(runner,'environment',return_value={}),contextlib.redirect_stdout(io.StringIO()):
            protocol=runner.safe(runner.PROTOCOL);protocol.parent.mkdir(parents=True);protocol.write_text('synthetic protocol\n')
            runner.atomic_new(runner.CONTRACT,{'synthetic':True})
            failure=QuadratureError({'absolute_difference':.01,'allowed_difference':1e-6})
            with patch.object(CarrierOriginField,'summarize_edge',side_effect=failure) as call:
                self.assertEqual(runner.synthetic_checks(),2)
                self.assertEqual(call.call_count,1)
            runner.publication_check()
            before=runner.safe(runner.OUT/'manifest.json').read_bytes()
            runner.publication_check()
            self.assertEqual(before,runner.safe(runner.OUT/'manifest.json').read_bytes())
            with self.assertRaises(FileExistsError):runner.synthetic_checks()
            with self.assertRaisesRegex(RuntimeError,'session_closed_no_continuation'):runner.unavailable_stage()
            with runner.safe(runner.OUT/'qc.json').open('a') as f:f.write(' ')
            with self.assertRaisesRegex(ValueError,'closed_output_mismatch'):runner.publication_check()


if __name__ == '__main__': unittest.main()
