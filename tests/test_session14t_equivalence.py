"""Synthetic tests for the Session 14t representation comparator."""
from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path
import unittest

import numpy as np

from defensive_network_disruption.data.row_equivalence import (
    compare_exact, historical_json_bytes, public_difference_rows,
    schema_fingerprint, semantic_flags,
)


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/session_14t_row_equivalence_audit.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("session14t", RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RowEquivalenceTests(unittest.TestCase):
    def test_identical_nested_objects(self):
        value = {"alias": "development", "carrier": (1.0, 2.0)}
        self.assertEqual(compare_exact(value, value), [])
        self.assertTrue(semantic_flags(value, value, True)["representation_identity"])

    def test_tuple_list_python_inequality_but_serialization_identity(self):
        left = {"points": ((1.0, -0.0), (2.0, 3.0))}
        right = json.loads(historical_json_bytes(left))
        self.assertNotEqual(left, right)
        self.assertEqual(historical_json_bytes(left), historical_json_bytes(right))
        flags = semantic_flags(left, right, True)
        self.assertTrue(flags["semantic_equivalence"])
        self.assertFalse(flags["representation_identity"])
        self.assertGreater(flags["container_or_order_difference_count"], 0)

    def test_python_and_numpy_float_types_are_reported_before_semantics(self):
        differences = compare_exact({"x": 1.5}, {"x": np.float64(1.5)})
        self.assertEqual([item.category for item in differences], ["scalar_type"])
        self.assertTrue(differences[0].bit_equal)

    def test_signed_zero_bits_are_not_equal(self):
        differences = compare_exact({"x": 0.0}, {"x": -0.0})
        self.assertEqual(differences[0].category, "numeric_value")
        self.assertFalse(differences[0].bit_equal)
        self.assertFalse(differences[0].signed_zero_equal)

    def test_mapping_order_and_sequence_order_are_distinct(self):
        left = {"a": 1, "b": 2}
        right = {"b": 2, "a": 1}
        self.assertEqual(compare_exact(left, right)[0].category, "mapping_order")
        reordered = compare_exact({"x": [1, 2]}, {"x": [2, 1]})
        self.assertEqual(sum(item.category == "numeric_value" for item in reordered), 2)

    def test_one_bit_float_difference(self):
        adjacent = np.nextafter(1.0, 2.0)
        differences = compare_exact(1.0, adjacent)
        self.assertEqual(differences[0].category, "scalar_type")
        self.assertFalse(differences[0].bit_equal)
        self.assertEqual(differences[1].category, "numeric_value")

    def test_serialization_only_difference_is_separate_input(self):
        value = {"x": [1.0, 2.0]}
        flags = semantic_flags(value, value, serialized_equal=False)
        self.assertTrue(flags["representation_identity"])
        self.assertFalse(flags["semantic_equivalence"])

    def test_missing_field_and_nested_container_are_reported(self):
        differences = compare_exact({"outer": {"points": ((1.0, 2.0),)}},
                                    {"outer": {"other": [[1.0, 2.0]]}})
        self.assertEqual(differences[0].category, "mapping_keys")

    def test_schema_fingerprints_capture_container_difference(self):
        self.assertNotEqual(schema_fingerprint({"x": (1.0,)}),
                            schema_fingerprint({"x": [1.0]}))

    def test_public_rows_remove_ordinals_and_values(self):
        differences = compare_exact({"x": ((1.0, 2.0),)}, {"x": [[1.0, 2.0]]})
        rows = public_difference_rows(differences)
        self.assertTrue(rows)
        self.assertTrue(all("[0]" not in row["path"] for row in rows))
        self.assertFalse(any("left_value" in row for row in rows))

    def test_runner_has_only_bounded_commands_and_no_prohibited_imports(self):
        tree = ast.parse(RUNNER.read_text())
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(item.name for item in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        forbidden = ("production_verification", "representation_study", "networks.options",
                     "scipy", "urllib", "requests", "socket", "kloppy")
        self.assertFalse(any(any(word in name for word in forbidden) for name in imports))
        strings = {node.value for node in ast.walk(tree)
                   if isinstance(node, ast.Constant) and isinstance(node.value, str)}
        self.assertTrue({"preflight", "audit", "publication-check"} <= strings)
        self.assertFalse({"analyze", "score", "fit", "acquire", "integrate"} & strings)

    def test_row_reader_rejects_every_other_ordinal(self):
        runner = load_runner()
        with self.assertRaisesRegex(PermissionError, "only_ordinal_1_authorized"):
            runner.one_line(Path("ignored"), 0)

    def test_classification_precedence_for_container_only_mechanism(self):
        runner = load_runner()
        left = {"x": ((1.0, 2.0),)}
        right = {"x": [[1.0, 2.0]]}
        flags = semantic_flags(left, right, True)
        self.assertEqual(runner.classify(flags, True, False), ("B", 1))
        self.assertEqual(runner.classify(flags, True, True), ("F", 4))


if __name__ == "__main__":
    unittest.main()
