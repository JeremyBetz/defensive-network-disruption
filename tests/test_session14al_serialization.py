import dataclasses
import hashlib
import json
import math
from pathlib import Path
import tempfile
import unittest

import numpy as np

from defensive_network_disruption.geometry.diagnostic_serialization import (
    DiagnosticSerializationError, canonical_bytes, emergency_write,
    project_evidence, project_verified_envelope, semantic_envelope_equal,
)
from defensive_network_disruption.geometry.micro_interval_verifier import IntegralInterval
from defensive_network_disruption.geometry.root_partition_determinism import CertifiedOnset, CertifiedRootTransition
from defensive_network_disruption.geometry.verification_repair import (
    CertifiedBoundary, CertifiedTieInterval, VerifiedEnvelope, VerifiedSwitch,
)


def fixture():
    start = CertifiedBoundary(0.24, np.nextafter(0.24, 1.0), "entry", (1, 0), (1, 0))
    end = CertifiedBoundary(0.76, np.nextafter(0.76, 0.0), "exit", (0, 1), (0, 1))
    tie = CertifiedTieInterval(start, end, (1, 0), ((1, 0),))
    switch = VerifiedSwitch(0.5, (0,), (1, 0), (1,), ((1, 0),), False, False, 0.75)
    return VerifiedEnvelope((switch,), (tie,), (1, 0), (0.0, 0.5, 1.0), 65536)


def historical_plain(value):
    if isinstance(value, dict):
        return {str(key): historical_plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [historical_plain(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def payload():
    envelope = fixture()
    onset = CertifiedOnset(0, 1, 0.25, np.nextafter(0.25, 0.0), 0.25)
    transition = CertifiedRootTransition(0.5, np.nextafter(0.5, 0.0), None, None,
                                         0.5, (0,), (0, 1), (1,), ((0, 1),))
    interval = IntegralInterval(0.2, 0.2000000000001, 1e-13, 3, 2, 1)
    return {"production": {"intervals": 512, "estimates": {"maximum": np.float64(0.2)}},
            "strict": interval, "repeat": interval, "partitions": (0.0, 0.5, 1.0),
            "onsets": (onset,), "switches": (transition,), "envelope": envelope,
            "piece_contributions": [{"piece": 0, "integral": interval}],
            "onset_neighborhood": [{"owners": [0, 1], "finite": True}],
            "uniform_curve": [{"intervals": 256, "estimate": 0.2}],
            "piecewise_curve": [{"intervals": 256, "estimate": 0.2}]}


class Session14alSerializationTests(unittest.TestCase):
    def test_pre_repair_failure_is_reproduced(self):
        with self.assertRaisesRegex(TypeError, "VerifiedEnvelope.*JSON serializable"):
            json.dumps(historical_plain({"envelope": fixture()}), allow_nan=False)

    def test_standalone_projection_and_semantic_equivalence(self):
        result = project_verified_envelope(fixture())
        self.assertEqual(result["type"], "verified_envelope")
        self.assertEqual(result["maximizing_defenders"], [0, 1])
        self.assertEqual(result["switches"][0]["crossing_pairs"], [[0, 1]])
        self.assertTrue(semantic_envelope_equal(fixture(), result))

    def test_full_payload_and_nested_types_serialize(self):
        result = project_evidence(payload())
        self.assertEqual(result["strict"]["type"], "integral_interval")
        self.assertEqual(result["onsets"][0]["type"], "certified_onset")
        self.assertEqual(result["switches"][0]["type"], "certified_root_transition")
        json.loads(canonical_bytes(payload()))

    def test_bytes_owner_order_and_hash_are_deterministic(self):
        first = canonical_bytes(payload())
        second = canonical_bytes(payload())
        self.assertEqual(first, second)
        self.assertEqual(hashlib.sha256(first).hexdigest(), hashlib.sha256(second).hexdigest())
        self.assertIn(b'"owners":[0,1]', first)

    def test_nonfinite_unsupported_and_unordered_fail_closed(self):
        for value in (math.nan, math.inf, object(), {1, 2}):
            with self.subTest(value=type(value).__name__):
                with self.assertRaises(DiagnosticSerializationError):
                    canonical_bytes({"value": value})

    def test_malformed_owner_and_missing_field_fail_closed(self):
        bad = dataclasses.replace(fixture(), maximizing_defenders=(0, 0))
        with self.assertRaisesRegex(DiagnosticSerializationError, "malformed"):
            project_verified_envelope(bad)
        with self.assertRaises(TypeError):
            VerifiedEnvelope(switches=(), tie_intervals=(), maximizing_defenders=(), partitions=())

    def test_mapping_and_scalar_contract(self):
        with self.assertRaises(DiagnosticSerializationError):
            canonical_bytes({1: "not-string"})
        with self.assertRaises(DiagnosticSerializationError):
            canonical_bytes({"bad": np.array([1.0])})
        self.assertEqual(json.loads(canonical_bytes({"n": np.int64(2)})), {"n": 2})

    def test_emergency_preserves_primary_failure_and_no_success_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            try:
                canonical_bytes({"bad": object()})
            except DiagnosticSerializationError as error:
                emergency_write(root / "emergency.json", error, stage="synthetic_publication")
            record = json.loads((root / "emergency.json").read_text())
            self.assertEqual(record["exception"], "DiagnosticSerializationError")
            self.assertIn("unsupported_type", record["traceback"])
            self.assertFalse((root / "manifest.json").exists())

    def test_runner_has_no_empirical_or_numerical_route(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "scripts/session_14al_verified_envelope_serialization.py").read_text()
        for forbidden in ("prepared.jsonl", "population.jsonl", "CarrierOriginField(",
                          "controlled_vector(", "adaptive_maximum(", "load_model(", "target"):
            self.assertNotIn(forbidden, source)
        suite = unittest.defaultTestLoader.discover(str(root / "tests"),
                                                    pattern="test_session14al_serialization.py")
        self.assertGreater(suite.countTestCases(), 0)


if __name__ == "__main__":
    unittest.main()
