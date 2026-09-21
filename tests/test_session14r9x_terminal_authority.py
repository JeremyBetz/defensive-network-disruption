import copy
from fractions import Fraction as F
import unittest

from defensive_network_disruption.geometry import r9x_terminal_authority as authority


SOURCE = {key: authority.digest(key.encode()) for key in authority.SOURCE_KEYS}


def coeff(dot, cross2):
    return authority.Coefficients(F(1), F(dot), F(cross2))


def record(pair, competitors, *, left=F(1, 2), right=F(1), ordinal=1, depth=2):
    return authority.create_authority(
        ordinal=ordinal, depth=depth, left=left, right=right,
        pair=(pair, pair), competitors=tuple(competitors), source=SOURCE)


class TerminalAuthorityTests(unittest.TestCase):
    def test_round_trip_is_deterministic_and_geometry_free(self):
        value = record(coeff(4, 8), (coeff(4, 16),))
        loaded = authority.load_authority(copy.deepcopy(value))
        self.assertEqual(loaded[0]["left"], F(1, 2))
        self.assertEqual(authority.canonical(value), authority.canonical(copy.deepcopy(value)))
        text = authority.canonical(value).decode()
        for prohibited in ("carrier", "receiver", "defender", "alias", "coordinate"):
            self.assertNotIn(prohibited, text)

    def test_partition_bounds_derive_from_ordered_depths(self):
        self.assertEqual(authority.derive_leaf_bounds(F(0), F(1), (1, 2, 2), 1),
                         (F(1, 2), F(3, 4)))
        with self.assertRaisesRegex(ValueError, "partition_coverage"):
            authority.derive_leaf_bounds(F(0), F(1), (2, 2), 0)

    def test_pair_globally_maximal(self):
        result = authority.classify_terminal(record(coeff(4, 8), (coeff(4, 16),)))
        self.assertEqual(result["classification"], "TA")
        self.assertTrue(result["complete"])

    def test_third_defender_dominant(self):
        result = authority.classify_terminal(record(coeff(4, 16), (coeff(4, 8),)))
        self.assertEqual(result["classification"], "TB")
        self.assertTrue(result["complete"])

    def test_dominance_switch(self):
        pair = coeff(3, F(4, 5))
        competitor = coeff(4, 16)
        result = authority.classify_terminal(record(pair, (competitor,)))
        self.assertEqual(result["classification"], "TC")
        self.assertTrue(result["complete"])

    def test_interior_equality_authority(self):
        pair = coeff(4, 8)
        result = authority.classify_terminal(record(pair, (pair,)))
        self.assertEqual(result["classification"], "TD")
        self.assertTrue(result["complete"])

    def test_unresolved_limit(self):
        pair = coeff(4, 8)
        close = coeff(4, F(8) + F(1, 10**30))
        result = authority.classify_terminal(record(pair, (close,)), max_depth=0)
        self.assertEqual(result["classification"], "TE")
        self.assertFalse(result["complete"])

    def test_tampering_and_missing_fields_block(self):
        base = record(coeff(4, 8), (coeff(4, 16),))
        cases = []
        changed = copy.deepcopy(base); changed["cell"]["left"] = {"numerator": "2", "denominator": "4"}; cases.append(changed)
        changed = copy.deepcopy(base); changed["coefficients"][0]["dot"] = {"numerator": "5", "denominator": "1"}; cases.append(changed)
        changed = copy.deepcopy(base); changed["source_authority"][authority.SOURCE_KEYS[0]] = "0" * 64; cases.append(changed)
        changed = copy.deepcopy(base); changed.pop("competitors"); cases.append(changed)
        changed = copy.deepcopy(base); changed["schema_version"] = 2; cases.append(changed)
        for changed in cases:
            with self.subTest(changed=changed):
                with self.assertRaises(ValueError):
                    authority.load_authority(changed)

    def test_nonfinite_and_invalid_coefficients_block(self):
        with self.assertRaises(ValueError):
            authority.Coefficients(F(0), F(1), F(1))
        with self.assertRaises(ValueError):
            F(float("nan"))


if __name__ == "__main__":
    unittest.main()
