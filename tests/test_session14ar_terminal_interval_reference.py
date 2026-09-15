import importlib.util
from fractions import Fraction
import json
import math
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "src/defensive_network_disruption/validation/terminal_interval_reference.py"
SPEC = importlib.util.spec_from_file_location("session14ar_test_reference", PATH)
r = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(r)


class Session14arTerminalIntervalReferenceTests(unittest.TestCase):
    def test_restricted_geometry_decodes_only_selected_defender(self):
        text = json.dumps({"alias": "ignored", "carrier": [0, 0], "receiver": [2, 1],
                           "defenders": [[1, 0], "forbidden", [3, 2]]})
        selected = r.restricted_geometry(text, 0)
        self.assertEqual(selected["defender"], (1.0, 0.0))
        self.assertEqual(selected["defender_count"], 3)
        with self.assertRaises(r.ReferenceError):
            r.restricted_geometry(text, 1)

    def test_geometry_schema_and_owner_guards(self):
        good = json.dumps({"alias": "x", "carrier": [0, 0], "receiver": [1, 0], "defenders": [[2, 0]]})
        with self.assertRaises(r.ReferenceError):
            r.restricted_geometry(good, -1)
        with self.assertRaises(r.ReferenceError):
            r.restricted_geometry(json.dumps({"carrier": [0, 0], "receiver": [1, 0], "defenders": [[2, 0]]}), 0)

    def test_exact_lambda_zero_lateral(self):
        rate = r.exact_lambda({"carrier": (0.0, 0.0), "receiver": (4.0, 0.0), "defender": (2.0, 0.0)})
        self.assertEqual(rate, 0)
        result = r.taylor_enclosure(rate, .25, 1.0)
        self.assertEqual(result["order"], 0)
        self.assertLessEqual(result["lower"], .75)
        self.assertGreaterEqual(result["upper"], .75)

    def test_zero_width_exact(self):
        result = r.taylor_enclosure(Fraction(3, 8), .5, .5)
        self.assertEqual(result["width"], 0.0)
        self.assertEqual(result["lower"], 0.0)

    def test_taylor_contains_analytic_erf_value(self):
        rate = Fraction(1, 8)
        result = r.taylor_enclosure(rate, 0.25, 0.75)
        exact = math.sqrt(math.pi) / (2 * math.sqrt(float(rate))) * (
            math.erf(math.sqrt(float(rate)) * .75) - math.erf(math.sqrt(float(rate)) * .25))
        self.assertLessEqual(result["lower"], exact)
        self.assertGreaterEqual(result["upper"], exact)
        self.assertLessEqual(result["width"], r.AGREEMENT)

    def test_order_cap_is_unavailable(self):
        result = r.taylor_enclosure(Fraction(100), 0.0, 1.0, agreement=1e-100, max_order=0)
        self.assertFalse(result["available"])
        self.assertEqual(result["reason"], "order_cap")

    def test_outward_rounding(self):
        value = Fraction(1, 10)
        lower, upper = r.outward_lower(value), r.outward_upper(value)
        self.assertLessEqual(Fraction.from_float(lower), value)
        self.assertGreaterEqual(Fraction.from_float(upper), value)

    def test_interval_distance_and_signed_zero(self):
        self.assertEqual(r.point_interval_distance(-0.0, 0.0, 1.0), 0.0)
        self.assertEqual(r.point_interval_distance(2.0, 0.0, 1.0), 1.0)
        with self.assertRaises(r.ReferenceError):
            r.point_interval_distance(math.nan, 0.0, 1.0)

    def test_compare_requires_narrow_bound(self):
        narrow = {"available": True, "lower": .4, "upper": .4 + 1e-12}
        self.assertTrue(r.compare_retained(.4, 1e-15, narrow)["within_existing_authority"])
        wide = {"available": True, "lower": .3, "upper": .5}
        self.assertFalse(r.compare_retained(.4, 1e-15, wide)["within_existing_authority"])

    def test_reconstruction_mismatch(self):
        with self.assertRaisesRegex(r.ReferenceError, "scalar_reconstruction_mismatch"):
            r.reconstruction_check(Fraction(1), [[.5, .9]])

    def test_structural_authority(self):
        structure = {"switches": [{"first_post_switch": .2, "owners_after": [3]}],
                     "onsets": [{"defender_index": 3, "branch": 1, "first_post_branch": .3}],
                     "envelope": {"tie_intervals": []}}
        onsets = {"partitions": [0.0, .5, 1.0]}
        result = r.structural_authority(structure, onsets, .5, 1.0)
        self.assertEqual(result["owner"], 3)
        changed = json.loads(json.dumps(structure)); changed["switches"].append(
            {"first_post_switch": .75, "owners_after": [4]})
        with self.assertRaisesRegex(r.ReferenceError, "interior_switch"):
            r.structural_authority(changed, onsets, .5, 1.0)

    def test_marker_collision_and_atomic_package_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            r.create_once(root / "marker", {"a": 1})
            with self.assertRaises(FileExistsError):
                r.create_once(root / "marker", {"a": 2})

    def test_no_prohibited_routes_or_numerical_imports(self):
        source = PATH.read_text()
        for forbidden in ("import numpy", "import scipy", "load_model", "target_index",
                          "option_share", "acquire", "summarize_edge", "quad("):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
