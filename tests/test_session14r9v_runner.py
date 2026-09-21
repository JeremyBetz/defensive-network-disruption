import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from defensive_network_disruption.validation import r9v_evidence as e

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "r9v_runner", ROOT / "scripts/session_14r9v_tie_boundary_publication_diagnosis.py")
r = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(r)


def invalid_package(folder, *, attempt=False, receipt=False):
    local = folder / "local"; local.mkdir(parents=True)
    records = e.empty()
    if attempt: r.put(local / "access_attempt.json", {"synthetic": True})
    if receipt:
        r.put(local / "selected_edge.json", {"synthetic": True})
        r.put(local / "access_materialized.json", {"synthetic": True})
    return e.close(folder, {"synthetic": True}, records, [], [], {
        "status": "partial", "execution_valid": False, "numerical": "NF",
        "publication": "PD", "readiness": 4, "states_reopened": int(receipt),
        "edges_reopened": int(receipt), "exposure_uncertain": attempt and not receipt})


class RunnerTests(unittest.TestCase):
    def test_selective_projection_skips_other_rows_and_receivers(self):
        from defensive_network_disruption.data.representation_projection import ALIASES
        with tempfile.TemporaryDirectory() as name:
            path = Path(name).resolve() / "prepared"
            row = {"alias": ALIASES[0], "carrier": [0., 0.],
                   "defenders": [[3., 1.]],
                   "receivers": ["FORBIDDEN", "FORBIDDEN", [8., 0.], "FORBIDDEN"]}
            path.write_text("UNDECODABLE\n" * 10 + json.dumps(row) + "\nUNDECODABLE\n")
            selected = r.lexical_selected(path)
            self.assertEqual(selected["receiver"], (8., 0.))
            self.assertNotIn("receivers", selected)

    def test_strict_inventory_and_tampering(self):
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name).resolve(); result = invalid_package(folder)
            self.assertTrue(result["valid"]); self.assertEqual(result["files"], 11)
            (folder / "qc.json").write_text("{}")
            with self.assertRaises(ValueError): e.publication_check(folder)

    def test_uncertain_and_materialized_access_accounting(self):
        for attempt, receipt in ((True, False), (True, True)):
            with self.subTest(attempt=attempt, receipt=receipt), tempfile.TemporaryDirectory() as name:
                folder = Path(name).resolve(); invalid_package(folder, attempt=attempt, receipt=receipt)
                qc = e.load(folder / "qc.json")
                self.assertEqual(qc["edges_reopened"], int(receipt))
                self.assertEqual(qc["exposure_uncertain"], attempt and not receipt)

    def test_preflight_blocks_dirty_before_retained_access(self):
        with patch.object(r, "git", return_value="dirty"), \
             patch.object(r, "review_retained", side_effect=AssertionError("retained access")) as access:
            with self.assertRaisesRegex(RuntimeError, "dirty_tree"): r.preflight()
            access.assert_not_called()

    def test_collision_evidence_matches_retained_traceback(self):
        trace = "r9o_terminal.py retain_authority linear_authority.json immutable_record_exists"
        observed = r.collision_semantics(trace, first_write_valid=True,
                                         original_failure_preserved=True)
        self.assertTrue(all(observed[key] for key in (
            "reproduced", "first_write_valid", "second_write_blocked",
            "original_failure_preserved")))
        self.assertEqual(observed["authority_writers"], 2)

    def test_public_schema_rejects_private_fields_and_nan(self):
        record = e.empty()["authority.json"]
        record["evidence_sha256"] = "0" * 64
        e.validate_record("authority.json", record)
        record["geometry"] = [1, 2]
        with self.assertRaises(ValueError): e.validate_record("authority.json", record)
        with self.assertRaises(ValueError): e.canonical({"bad": float("nan")})
