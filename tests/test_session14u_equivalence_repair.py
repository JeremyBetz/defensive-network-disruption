"""Synthetic tests for the Session 14u equivalence repair and bounded runner."""
from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path
import unittest

from defensive_network_disruption.data.prepared_equivalence_gate import require_historical_prepared_bytes
from defensive_network_disruption.data.row_equivalence import historical_json_bytes
from defensive_network_disruption.geometry.max_warning_diagnosis import maximum_function, width_summary


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/session_14u_warning_diagnosis_resumed.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("session14u", RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EquivalenceRepairTests(unittest.TestCase):
    def test_tuple_list_regression_passes_at_historical_byte_layer(self):
        current = {"alias": "synthetic", "carrier": (0.0, -0.0),
                   "receivers": ((1.0, 2.0),), "defenders": ((3.0, 4.0),)}
        preserved = historical_json_bytes(current)
        decoded = json.loads(preserved)
        self.assertNotEqual(current, decoded)
        self.assertEqual(require_historical_prepared_bytes(current, preserved), preserved)

    def test_exact_gate_rejects_numeric_sequence_missing_signed_zero_and_scalar_changes(self):
        base = {"x": (0.0, 1.0), "name": "a"}
        changes = (
            {"x": (0.0, 1.0000000000000002), "name": "a"},
            {"x": (1.0, 0.0), "name": "a"},
            {"x": (0.0, 1.0)},
            {"x": (-0.0, 1.0), "name": "a"},
            {"x": (0.0, 1.0), "name": "b"},
        )
        preserved = historical_json_bytes(base)
        for changed in changes:
            with self.subTest(changed=changed):
                with self.assertRaisesRegex(ValueError, "prepared_historical_bytes_mismatch"):
                    require_historical_prepared_bytes(changed, preserved)

    def test_serialization_is_deterministic_and_exact(self):
        row = {"b": (2.0,), "a": (1.0,)}
        self.assertEqual(historical_json_bytes(row), historical_json_bytes(row))
        self.assertEqual(historical_json_bytes(row), b'{"a": [1.0], "b": [2.0]}\n')

    def test_nonbytes_preserved_line_rejected(self):
        with self.assertRaisesRegex(TypeError, "preserved_line must be bytes"):
            require_historical_prepared_bytes({}, "{}\n")

    def test_partition_diagnostic_is_bounded(self):
        *_, partitions = maximum_function("constant_width", (0, 0), (20, 0), ((5, 1),))
        summary = width_summary(partitions)
        self.assertGreater(summary["piece_count"], 0)
        self.assertGreater(summary["minimum"], 0.0)

    def test_classification_rules(self):
        runner = load_runner()
        healthy = {"converged": True, "finite": True, "deterministic": True}
        continuity = {"oracle_comparison_passed": True}
        self.assertEqual(runner.classify(True, healthy, continuity, True, 1e-11), ("A", 1))
        self.assertEqual(runner.classify(True, healthy, continuity, True, 1e-5), ("B", 1))
        self.assertEqual(runner.classify(True, {**healthy, "converged": False}, continuity, True, 0.0), ("D", 3))
        self.assertEqual(runner.classify(False, healthy, continuity, True, 0.0), ("G", 4))

    def test_only_ordinal_one_can_be_read(self):
        runner = load_runner()
        with self.assertRaisesRegex(PermissionError, "only_ordinal_1_authorized"):
            runner.one_line(Path("unopened"), 2)

    def test_runner_commands_and_imports_are_bounded(self):
        tree = ast.parse(RUNNER.read_text())
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(item.name for item in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        forbidden = ("receiver_ranking", "networks.options", "urllib", "requests", "socket", "kloppy")
        self.assertFalse(any(any(word in name for word in forbidden) for name in imports))
        strings = {node.value for node in ast.walk(tree)
                   if isinstance(node, ast.Constant) and isinstance(node.value, str)}
        self.assertTrue({"preflight", "diagnose", "publication-check"} <= strings)
        self.assertFalse({"analyze", "score", "fit", "acquire"} & strings)


if __name__ == "__main__":
    unittest.main()
