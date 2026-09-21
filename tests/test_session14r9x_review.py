import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from defensive_network_disruption.geometry import r9x_terminal_authority as authority
from defensive_network_disruption.validation import r9x_evidence as evidence


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/session_14r9x_terminal_cell_evidence_retention_review.py"
SPEC = importlib.util.spec_from_file_location("r9x_runner", SCRIPT)
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class RetentionReviewTests(unittest.TestCase):
    def test_metadata_review_never_opens_selected_edge(self):
        original = Path.open

        def guarded(path, *args, **kwargs):
            if Path(path).name == "selected_edge.json":
                raise AssertionError("selected_edge_opened")
            return original(path, *args, **kwargs)

        with patch.object(Path, "open", guarded):
            result = runner._metadata_review()
        self.assertEqual(result["cells"], 81)
        self.assertEqual(result["counts"], {"maximum": 36, "dominated": 44,
                                             "unresolved": 1})

    def test_loss_trace_names_every_missing_authority(self):
        names = {row["datum"] for row in runner._loss_entries()}
        self.assertEqual(names, {
            "cell_lower_bound", "cell_upper_bound", "function_coefficients",
            "pair_authority", "competitor_authority", "branch_onset_state",
            "pair_value_enclosure", "pair_competitor_enclosure",
            "derivative_enclosure", "refinement_provenance",
        })
        self.assertTrue(all(row["in_memory"] and not row["retained"]
                            for row in runner._loss_entries()))

    def test_field_dispositions_are_complete_and_disjoint(self):
        rows = runner._field_rows()
        self.assertEqual(len({row["field"] for row in rows}), len(rows))
        self.assertEqual({row["disposition"] for row in rows},
                         {"REQUIRED", "DERIVABLE", "REDUNDANT", "TOO_EMPIRICAL"})

    def test_runner_has_no_empirical_or_numerical_entrypoint(self):
        source = SCRIPT.read_text()
        for prohibited in ("lexical_selected", "evaluate_edge(", "project_prepared_edge",
                           "r9t_adapter", "owner_certification"):
            self.assertNotIn(prohibited, source)

    def test_strict_eight_file_package_and_tampering(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "outputs") as temporary:
            folder = Path(temporary)
            local = folder / "local"
            evidence.put(local / "review.marker", {"reserved": True})
            index_placeholder = "0" * 64
            records = {
                "retention_contract.json": {"schema_version": 1, "status": "complete",
                    "flags": {"metadata_only": True}, "counts": {"new_edges": 0},
                    "authority": {"head": index_placeholder}},
                "evidence_loss_trace.json": {"schema_version": 1, "status": "complete",
                    "entries": [{"datum": "bounds", "retained": False}]},
                "minimum_schema.json": {"schema_version": 1, "status": "complete",
                    "required": ["bounds"], "derivable": [], "redundant": [],
                    "prohibited": [], "field_schema": {"version": 1}},
                "prospective_acquisition.json": {"schema_version": 1, "status": "complete",
                    "flags": {"scope_exact": True},
                    "counts": {"previously_exposed_states_reopened": 1},
                    "steps": ["stop"], "recommendation": "bounded"},
            }
            fields = [{"field": "bounds", "disposition": "REQUIRED", "reason": "domain"}]
            synthetic = [{"fixture": "pair", "expected": "TA", "observed": "TA",
                          "source_discarded": True, "passed": True}]
            qc = {"status": "complete", "execution_valid": True,
                  "classification": "A", "readiness": 1, "states_accessed": 0,
                  "edges_accessed": 0, "empirical_computation": False}
            result = evidence.close(folder, {"head": index_placeholder}, records,
                                    fields, synthetic, qc)
            self.assertEqual(result, {"valid": True, "files": 8,
                                      "classification": "A", "readiness": 1})
            manifest = json.loads((folder / "manifest.json").read_text())
            changed = json.loads((folder / "qc.json").read_text())
            changed["states_accessed"] = 1
            (folder / "qc.json").write_text(json.dumps(changed) + "\n")
            with self.assertRaisesRegex(ValueError, "public_hash"):
                evidence.publication_check(folder)
            self.assertEqual(set(manifest["outputs"]), set(evidence.NAMES) - {"manifest.json"})

    def test_every_synthetic_and_negative_control_passes(self):
        rows = authority.synthetic_sufficiency()
        self.assertEqual(len(rows), 12)
        self.assertTrue(all(row["passed"] and row["source_discarded"] for row in rows))
        self.assertEqual(sum(row["expected"] == "blocked" for row in rows), 7)


if __name__ == "__main__":
    unittest.main()
