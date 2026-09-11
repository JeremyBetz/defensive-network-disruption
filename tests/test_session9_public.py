"""Synthetic tests for the Session 9 experimental public tooling."""
from __future__ import annotations

import importlib
import importlib.util
import ast
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

import defensive_network_disruption as dnd
from defensive_network_disruption.examples import (
    demonstration_models,
    synthetic_option_sequence,
    synthetic_option_state,
)

SPEC = importlib.util.spec_from_file_location(
    "session9", Path(__file__).parents[1] / "scripts/session_09_public_tooling.py")
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class PublicCoreTests(unittest.TestCase):
    def test_public_surface_and_frozen_numerics(self):
        expected = {
            "OptionState", "FrozenOptionModel", "OptionEdge", "OptionNetwork",
            "evaluate_options", "compare_options", "option_state_from_kloppy",
            "plot_option_network", "animate_option_network_comparison",
        }
        self.assertTrue(expected.issubset(set(dnd.__all__)))
        state = synthetic_option_state()
        for model in demonstration_models():
            network = dnd.evaluate_options(state, model=model)
            matrix, _ = importlib.import_module(
                "defensive_network_disruption.validation.ranking_features"
            ).choice_features(state, model.name)
            expected_utility = ((matrix - model.mean) / model.scale) @ model.coefficients
            np.testing.assert_array_equal(
                [edge.utility for edge in network.edges], expected_utility)

    def test_properties_ranks_records_and_immutability(self):
        network = dnd.evaluate_options(synthetic_option_state(), model=demonstration_models()[1])
        self.assertEqual(network.top_option, network.top_options[0])
        self.assertEqual(network.top_one_share, network.summary["top_one_share"])
        self.assertEqual(network.top_two_share, network.summary["top_two_share"])
        self.assertEqual(network.entropy, network.summary["entropy"])
        self.assertEqual(network.normalized_entropy, network.summary["normalized_entropy"])
        self.assertEqual(network.effective_option_count, network.summary["effective_option_count"])
        self.assertEqual(network.utility_range, network.summary["utility_range"])
        with self.assertRaises(TypeError):
            network.option_weights["A"] = 0
        records = network.to_records()
        self.assertEqual(tuple(records[0]), (
            "receiver_id", "utility", "option_share", "expected_rank",
            "tie_block", "is_top_option"))
        records[0]["utility"] = 99
        self.assertNotEqual(records, network.to_records())

    def test_tied_top_has_no_unique_top_and_expected_rank(self):
        model = dnd.FrozenOptionModel(
            "m0", ("distance", "longitudinal_displacement", "lateral_displacement"),
            (0, 0, 0), (1, 1, 1), (0, 0, 0),
        )
        network = dnd.evaluate_options(synthetic_option_state(), model=model)
        self.assertIsNone(network.top_option)
        self.assertEqual({edge.expected_rank for edge in network.edges}, {2.5})

    def test_pandas_export_schema_and_fresh_ownership(self):
        network = dnd.evaluate_options(synthetic_option_state(), model=demonstration_models()[1])
        frame = network.to_pandas()
        self.assertEqual(list(frame), [
            "carrier_id", "receiver_id", "utility", "option_share",
            "expected_rank", "tie_block", "is_top_option"])
        frame.loc[0, "utility"] = 99
        self.assertNotEqual(frame.loc[0, "utility"], network.edges[0].utility)

    def test_missing_pandas_message(self):
        network = dnd.evaluate_options(synthetic_option_state(), model=demonstration_models()[1])
        real_import = __import__
        def blocked(name, *args, **kwargs):
            if name == "pandas":
                raise ImportError("synthetic")
            return real_import(name, *args, **kwargs)
        with patch("builtins.__import__", side_effect=blocked):
            with self.assertRaisesRegex(ImportError, "dataframe.*extra"):
                network.to_pandas()

    def test_permutation_stability(self):
        state = synthetic_option_state()
        model = demonstration_models()[1]
        left = dnd.evaluate_options(state, model=model)
        right_state = dnd.OptionState(
            state.carrier_xy, state.candidate_ids[::-1], state.candidate_xy[::-1],
            state.defender_xy[::-1], carrier_id=state.carrier_id,
        )
        right = dnd.evaluate_options(right_state, model=model)
        self.assertEqual(left.top_options, right.top_options)
        self.assertEqual(dict(left.option_weights), dict(right.option_weights))


class PublicVisualizationTests(unittest.TestCase):
    def test_plot_returns_objects_and_rejects_mismatch(self):
        state = synthetic_option_state()
        network = dnd.evaluate_options(state, model=demonstration_models()[1])
        figure, axis = dnd.plot_option_network(
            state, network, pitch_length=105, pitch_width=68,
        )
        self.assertIs(axis.figure, figure)
        import matplotlib.pyplot as plt
        plt.close(figure)
        other = dnd.OptionState(
            state.carrier_xy, ("Q", *state.candidate_ids[1:]), state.candidate_xy,
            state.defender_xy, carrier_id=state.carrier_id,
        )
        with self.assertRaisesRegex(ValueError, "exactly match"):
            dnd.plot_option_network(other, network, pitch_length=105, pitch_width=68)

    def test_plot_dimensions_and_bounds(self):
        state = synthetic_option_state()
        network = dnd.evaluate_options(state, model=demonstration_models()[0])
        for dimensions in ((0, 68), (105, -1), (float("nan"), 68)):
            with self.assertRaises(ValueError):
                dnd.plot_option_network(state, network, pitch_length=dimensions[0],
                                        pitch_width=dimensions[1])
        outside = dnd.OptionState((60, 0), ("A",), ((10, 0),), ((0, 0),), carrier_id="carrier")
        with self.assertRaisesRegex(ValueError, "outside"):
            dnd.plot_option_network(
                outside, dnd.evaluate_options(outside, model=demonstration_models()[0]),
                pitch_length=105, pitch_width=68,
            )

    def test_animation_contract(self):
        states = synthetic_option_sequence()
        m0, m1 = demonstration_models()
        animation = dnd.animate_option_network_comparison(
            states, m0_model=m0, m1_model=m1,
            pitch_length=105, pitch_width=68, fps=10,
        )
        self.assertEqual(len(animation._option_network_states), 80)
        self.assertEqual(animation._option_network_fps, 10)
        import matplotlib.pyplot as plt
        animation._draw_was_started = True
        plt.close(animation._fig)
        with self.assertRaises(ValueError):
            dnd.animate_option_network_comparison(
                (), m0_model=m0, m1_model=m1,
                pitch_length=105, pitch_width=68,
            )

    def test_synthetic_sequence_exact_and_aligned(self):
        states = synthetic_option_sequence()
        self.assertEqual(len(states), 80)
        self.assertEqual(states[0], synthetic_option_state())
        self.assertEqual(states[-1].candidate_xy[0], (14.0, 8.0))
        self.assertEqual(states[-1].defender_xy[0], (12.0, -1.0))
        self.assertTrue(all(state.carrier_xy == (0.0, 0.0) for state in states))
        self.assertTrue(all(state.candidate_ids == states[0].candidate_ids for state in states))


class PublicBoundaryTests(unittest.TestCase):
    def test_no_empirical_fitting_acquisition_or_m2_routes(self):
        root = Path(__file__).parents[1]
        paths = [root / name for name in RUNNER.IMPLEMENTATION if name.endswith(".py")]
        imported = set()
        called = set()
        for path in paths:
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(item.name for item in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module)
                elif isinstance(node, ast.Call):
                    function = node.func
                    called.add(function.attr if isinstance(function, ast.Attribute)
                               else function.id if isinstance(function, ast.Name) else "")
        self.assertFalse(any(name.startswith(("requests", "urllib", "scipy.optimize"))
                             for name in imported))
        self.assertTrue({"fit", "minimize", "urlopen", "acquire"}.isdisjoint(called))
        self.assertNotIn("defensive_network_disruption.geometry.attenuation", imported)

    def test_path_firewalls(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(RUNNER, "ROOT", Path(directory).resolve()):
            with self.assertRaises(PermissionError):
                RUNNER.safe("../outside")
            (Path(directory) / "link").symlink_to("/tmp")
            with self.assertRaises(PermissionError):
                RUNNER.safe("link/file")


if __name__ == "__main__":
    unittest.main()
