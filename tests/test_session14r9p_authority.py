"""Synthetic tests for the prospective R9P retained-journal contract."""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from defensive_network_disruption.validation import r9j_linear_publication as linear
from defensive_network_disruption.validation.r9p_retained_authority import (
    REGISTRY,
    RetainedJournalAuthority,
    RetainedJournalDescriptor,
    action_delta,
    review_registered,
)
from defensive_network_disruption.validation.state_lifecycle import LifecycleError, canonical_bytes


class RetainedAuthorityTests(unittest.TestCase):
    def fixture(self, folder: Path):
        rows = linear.fixture("failure")
        journal = folder / "journal.jsonl"
        trace = folder / "traceback.txt"
        linear.write_records(journal, rows)
        trace.write_bytes(linear.TRACE)
        raw = hashlib.sha256(journal.read_bytes()).hexdigest()
        trace_hash = hashlib.sha256(linear.TRACE).hexdigest()
        descriptor = RetainedJournalDescriptor(
            "synthetic_retained_failure", raw, trace_hash,
            ("0", "1", "constant_width", "onset_adaptive", "GateFailure"), "0", "0"
        )
        return rows, journal, trace, descriptor

    def review(self, journal, trace, descriptor):
        with patch.dict(REGISTRY, {descriptor.authority_id: descriptor}):
            return review_registered(journal, trace, descriptor)

    def test_valid_authority_is_immutable_and_count_is_derived(self):
        with tempfile.TemporaryDirectory() as name:
            rows, journal, trace, descriptor = self.fixture(Path(name).resolve())
            authority = self.review(journal, trace, descriptor)
            self.assertEqual(authority.derived_record_count, len(rows))
            self.assertEqual(sum(authority.action_counts.values()), len(rows))
            self.assertTrue(authority.record()["chain_valid"])
            with self.assertRaises(TypeError):
                RetainedJournalAuthority(b"{}\n", object())

    def test_same_count_wrong_hash_blocks(self):
        with tempfile.TemporaryDirectory() as name:
            rows, journal, trace, descriptor = self.fixture(Path(name).resolve())
            changed = json.loads(journal.read_text().splitlines()[0])
            changed["payload"]["extra"] = "synthetic"
            lines = journal.read_bytes().splitlines(keepends=True)
            lines[0] = canonical_bytes(changed)
            journal.write_bytes(b"".join(lines))
            with self.assertRaisesRegex(LifecycleError, "retained_raw_hash|journal_chain"):
                self.review(journal, trace, descriptor)
            self.assertEqual(len(journal.read_bytes().splitlines()), len(rows))

    def test_truncation_append_and_broken_chain_block(self):
        for kind in ("truncated", "appended", "chain"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as name:
                rows, journal, trace, descriptor = self.fixture(Path(name).resolve())
                lines = journal.read_bytes().splitlines(keepends=True)
                if kind == "truncated":
                    journal.write_bytes(b"".join(lines[:-1]))
                elif kind == "appended":
                    journal.write_bytes(b"".join(lines) + lines[-1])
                else:
                    record = json.loads(lines[1])
                    record["previous"] = "0" * 64
                    lines[1] = canonical_bytes(record)
                    journal.write_bytes(b"".join(lines))
                updated = replace(descriptor, raw_sha256=hashlib.sha256(journal.read_bytes()).hexdigest())
                with self.assertRaises(LifecycleError):
                    self.review(journal, trace, updated)

    def test_terminal_traceback_and_receipt_mismatches_block(self):
        changes = (
            {"terminal": ("0", "1", "constant_width", "routing", "GateFailure")},
            {"traceback_sha256": "0" * 64},
            {"selected_edge": "missing"},
        )
        for values in changes:
            with self.subTest(values=values), tempfile.TemporaryDirectory() as name:
                _, journal, trace, descriptor = self.fixture(Path(name).resolve())
                changed = replace(descriptor, **values)
                with self.assertRaises(LifecycleError):
                    self.review(journal, trace, changed)

    def test_unregistered_and_count_override_block(self):
        with tempfile.TemporaryDirectory() as name:
            _, journal, trace, descriptor = self.fixture(Path(name).resolve())
            with self.assertRaisesRegex(LifecycleError, "unregistered"):
                review_registered(journal, trace, descriptor)
            with patch.dict(REGISTRY, {descriptor.authority_id: descriptor}):
                with self.assertRaises(TypeError):
                    review_registered(journal, trace, descriptor, expected_count=1)

    def test_action_delta_is_safe_metadata(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            _, left_path, left_trace, left_descriptor = self.fixture(Path(first).resolve())
            _, right_path, right_trace, right_descriptor = self.fixture(Path(second).resolve())
            left = self.review(left_path, left_trace, left_descriptor)
            right = self.review(right_path, right_trace, right_descriptor)
            self.assertTrue(all(row["delta"] == 0 for row in action_delta(left, right)))

    def test_module_has_no_geometry_or_numerical_routes(self):
        source = Path(__file__).parents[1] / "src/defensive_network_disruption/validation/r9p_retained_authority.py"
        text = source.read_text()
        for prohibited in ("project_prepared_edge", "evaluate_edge", "numpy", "scipy", "target", "model", "share"):
            self.assertNotIn(prohibited, text.lower())


if __name__ == "__main__":
    unittest.main()
