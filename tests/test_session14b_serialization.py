"""Serialization-only repair tests for the exact Session 14b rerun."""
from __future__ import annotations

import ast
import importlib.util
import json
import math
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

import numpy as np

from defensive_network_disruption.validation.json_scalars import json_native


RUNNER_PATH=Path(__file__).parents[1]/"scripts/session_14b_synthetic_numerics.py"
SPEC=importlib.util.spec_from_file_location("session14b_runner",RUNNER_PATH)
runner=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(runner)


class SerializationRepairTests(unittest.TestCase):
    def test_nested_numpy_scalars_round_trip_with_native_types(self):
        value={"bool":np.bool_(True),"integer":np.int64(7),"floating":np.float64(2.5),
               "ordinary":[False,3,1.25,None,"x"],"nested":{"items":(np.int32(-2),np.bool_(False))}}
        encoded=runner.encoded(value)
        decoded=json.loads(encoded)
        self.assertIs(decoded["bool"],True)
        self.assertIsInstance(decoded["integer"],int)
        self.assertNotIsInstance(decoded["integer"],bool)
        self.assertEqual(decoded["integer"],7)
        self.assertIsInstance(decoded["floating"],float)
        self.assertEqual(decoded["floating"],2.5)
        self.assertEqual(decoded["ordinary"],[False,3,1.25,None,"x"])
        self.assertEqual(decoded["nested"]["items"],[-2,False])

    def test_deterministic_key_order_and_no_numeric_stringification(self):
        value={"z":np.int64(4),"a":np.float64(1.5),"b":np.bool_(False)}
        first=runner.encoded(value);second=runner.encoded(value)
        self.assertEqual(first,second)
        self.assertLess(first.index('"a"'),first.index('"b"'))
        self.assertLess(first.index('"b"'),first.index('"z"'))
        self.assertNotIn('"4"',first);self.assertNotIn('"1.5"',first)

    def test_rejects_nonfinite_and_unsupported_values(self):
        for value in (float("nan"),np.float64(float("inf"))):
            with self.subTest(value=value),self.assertRaises(ValueError):json_native(value)
        with self.assertRaises(TypeError):json_native(np.array([1.0]))
        with self.assertRaises(TypeError):json_native({1:"not a string key"})

    def test_exact_historical_reproduction_and_inherited_contract(self):
        self.assertEqual(runner.historical_failure(),runner.EXPECTED_FAILURE)
        self.assertEqual(runner.ORDINARY_INTERVALS,(16,32,64,128,256,512,1024,2048))
        self.assertEqual(runner.FINE_INTERVALS,(4096,8192,16384,32768,65536))
        self.assertEqual(len(runner.fixture_rows()),36)
        self.assertTrue(all(row["passed"] for row in runner.polynomial_oracles()))

    def test_numerical_review_body_matches_session14a(self):
        old=ast.parse((RUNNER_PATH.parent/"session_14a_synthetic_numerics.py").read_text())
        new=ast.parse(RUNNER_PATH.read_text())
        def functions(tree):
            return {node.name:ast.dump(node,include_attributes=False) for node in tree.body
                    if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))}
        old_functions=functions(old);new_functions=functions(new)
        for name in ("_component_values","failing_diagnostic","review"):
            self.assertEqual(new_functions[name],old_functions[name])

    def test_no_empirical_model_or_acquisition_route(self):
        tree=ast.parse(RUNNER_PATH.read_text())
        names={node.id for node in ast.walk(tree) if isinstance(node,ast.Name)}
        self.assertFalse(names & {"evaluate_options","FrozenOptionModel","minimize","urlopen"})
        text=RUNNER_PATH.read_text()
        self.assertNotIn("population"+".jsonl",text)
        self.assertNotIn("player_"+"targeted_id",text)

    def test_reference_unavailability_is_a_valid_f_closure(self):
        manifest={"protocol_sha256":"protocol","implementation_sha256":{},"outputs_sha256":{}}
        qc={"empirical_states_read":0,"models_loaded":0,"targets_read":0,"oracle_failures":0,
            "reference_failures":1,"classification":"F — UNRESOLVED"}
        references={"records":[{"available":False},{"available":True}]}
        empty_file=MagicMock();empty_file.read_text.return_value=""
        with patch.object(runner,"verify_history"),patch.object(runner,"committed"), \
             patch.object(runner,"digest",return_value="protocol"), \
             patch.object(runner,"implementation_hashes",return_value={}), \
             patch.object(runner,"load_json",side_effect=[manifest,qc,references]), \
             patch.object(runner,"PUBLIC",()),patch.object(runner,"safe",return_value=empty_file), \
             patch("builtins.print"):
            runner.publication_check()


if __name__=="__main__":unittest.main()
