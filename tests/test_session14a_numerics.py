"""Synthetic tests for the Session 14a numerical review."""
from __future__ import annotations

import ast
import importlib.util
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from defensive_network_disruption.geometry.integration_review import (
    FINE_INTERVALS, ORDINARY_INTERVALS, adaptive_reference, components,
    directional_breakpoints, historical_failure, polynomial_oracles,
    values_for_components)
from defensive_network_disruption.geometry.occlusion_fields import CarrierOriginField


RUNNER_PATH=Path(__file__).parents[1]/"scripts/session_14a_synthetic_numerics.py"
SPEC=importlib.util.spec_from_file_location("session14a_runner",RUNNER_PATH)
runner=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(runner)


class IntegrationReviewTests(unittest.TestCase):
    def test_historical_failure_exact(self):
        self.assertEqual(historical_failure(), runner.EXPECTED_FAILURE)

    def test_polynomial_oracles_and_ladder(self):
        self.assertEqual(ORDINARY_INTERVALS,(16,32,64,128,256,512,1024,2048))
        self.assertEqual(FINE_INTERVALS,(4096,8192,16384,32768,65536))
        records=polynomial_oracles()
        self.assertEqual(len(records),32)
        self.assertTrue(all(row["passed"] for row in records))

    def test_component_order_and_simpson_determinism(self):
        self.assertEqual([item.name for item in components(2)],
                         ["individual_1","individual_2","union","maximum"])
        field=CarrierOriginField("expanding")
        first=values_for_components(field,(0,0),(20,0),((5,1),(10,-2)),256)
        second=values_for_components(field,(0,0),(20,0),((5,1),(10,-2)),256)
        self.assertEqual(first,second)
        self.assertTrue(all(math.isfinite(value) for value in first.values()))

    def test_interval_validation(self):
        field=CarrierOriginField("isotropic")
        for bad in (True,1,3,-2):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                values_for_components(field,(0,0),(20,0),((5,1),),bad)

    def test_directional_breakpoints(self):
        radius=math.sqrt(26)
        self.assertEqual(directional_breakpoints((0,0),(20,0),((5,1),)),
                         (0.26,(26+radius)/100))

    def test_reference_available_on_failing_fixture(self):
        field=CarrierOriginField("expanding")
        estimates={count:values_for_components(field,(0,0),(20,0),((5,1),),count)
                   for count in FINE_INTERVALS}
        reference=adaptive_reference(field,(0,0),(20,0),((5,1),),components(1)[0],estimates)
        self.assertTrue(reference.available,reference.reason)
        self.assertAlmostEqual(reference.value,0.5424834469711288,places=14)

    def test_zero_directional_field(self):
        for name in ("expanding","constant_width"):
            result=values_for_components(CarrierOriginField(name),(0,0),(20,0),((25,0),),64)
            self.assertEqual(set(result.values()),{0.0})

    def test_runner_has_no_empirical_or_model_route(self):
        tree=ast.parse(RUNNER_PATH.read_text())
        names={node.id for node in ast.walk(tree) if isinstance(node,ast.Name)}
        self.assertFalse(names & {"evaluate_options","FrozenOptionModel","minimize","urlopen"})
        text=RUNNER_PATH.read_text()
        for forbidden in ("population"+".jsonl","player_"+"targeted_id"):
            self.assertNotIn(forbidden,text)

    def test_safe_paths_and_atomic_outputs(self):
        with tempfile.TemporaryDirectory() as directory,patch.object(runner,"ROOT",Path(directory).resolve()):
            (runner.ROOT/"sym").symlink_to("/tmp")
            for value in ("../escape","sym/file"):
                with self.assertRaises(PermissionError):runner.safe(value)
            runner.atomic_json(runner.OUT/"one.json",{"finite":1})
            with self.assertRaises(FileExistsError):runner.atomic_json(runner.OUT/"one.json",{})

    def test_fixture_authority_uses_closed_generator(self):
        rows=runner.fixture_rows()
        self.assertEqual(len(rows),36)
        self.assertEqual(rows[4][0],"lateral_x5_y0")
        self.assertEqual(rows[5][0],"lateral_x5_y1")


if __name__=="__main__":unittest.main()
