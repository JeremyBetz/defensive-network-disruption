import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from defensive_network_disruption.validation.r5_persistence import Journal
from defensive_network_disruption.validation.r7_execution import Progress
from defensive_network_disruption.validation import r9j_linear_publication as linear
from defensive_network_disruption.validation import r9o_terminal as old
from defensive_network_disruption.validation import r9v_publication_ownership as new
from defensive_network_disruption.validation import r9u_study


def failed_progress(folder):
    journal = Journal(folder / "journal.jsonl")
    progress = Progress(journal)
    progress.authorize_access()
    progress.discover_state("state", ("edge",))
    progress.project("state", lambda: None)
    progress.prepare_state("state")
    progress.start_state("state")
    for candidate in ("isotropic", "expanding"):
        progress.call_start("state", "edge", candidate)
        for stage in ("geometry", "joint_simpson", "envelope", "owner_certification",
                      "partition_construction"):
            progress.numerical_stage(stage=stage)
        progress.numerical_stage(stage="routing", pieces=1, bounded=0, quadrature=1)
        for stage in ("strict_piecewise", "repeat_piecewise", "onset_adaptive",
                      "direct_simpson", "accepted"):
            progress.numerical_stage(stage=stage)
        progress.call_complete()
    progress.call_start("state", "edge", "constant_width")
    for stage in ("geometry", "joint_simpson", "envelope", "owner_certification"):
        progress.numerical_stage(stage=stage)
    return journal, progress


class PublicationOwnershipTests(unittest.TestCase):
    def test_complete_publication_control_matrix(self):
        with tempfile.TemporaryDirectory() as name:
            rows = new.controls(Path(name).resolve())
        self.assertEqual(len(rows), 9)
        self.assertTrue(all(row["passed"] for row in rows), rows)
        self.assertEqual(sum(row["reviews"] for row in rows), 8)

    def test_historical_collision_is_reproduced(self):
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name).resolve()
            journal, progress = failed_progress(folder)
            closure = old.TerminalClosure(progress, folder)
            try:
                with patch.object(r9u_study, "ROOT", folder), patch.object(r9u_study, "LOCAL", Path(".")):
                    with self.assertRaisesRegex(FileExistsError, "immutable_record_exists"):
                        closure.fail(ValueError("original"), "analysis",
                            lambda authority, trace: r9u_study.retain_authority(authority))
            finally:
                journal.close()

    def test_single_writer_and_read_only_publisher(self):
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name).resolve()
            journal, progress = failed_progress(folder)
            observed = {}
            try:
                with patch.object(linear, "review", wraps=linear.review) as review:
                    result = new.TerminalClosure(progress, folder).fail(
                        ValueError("original"), "analysis",
                        lambda authority, descriptor, trace: observed.update(
                            authority=new.validate_persisted(descriptor, authority),
                            trace=trace) or "published")
                self.assertEqual(result, "published")
                self.assertEqual(review.call_count, 1)
                self.assertTrue(observed["trace"].exists())
                self.assertTrue((folder / "linear_authority.json").exists())
            finally:
                journal.close()

    def test_tampering_second_owner_and_repeat_block(self):
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name).resolve()
            journal, progress = failed_progress(folder)
            saved = {}
            closure = new.TerminalClosure(progress, folder)
            try:
                closure.fail(ValueError("original"), "analysis",
                    lambda authority, descriptor, trace: saved.update(
                        authority=authority, descriptor=descriptor))
                with self.assertRaises(PermissionError):
                    new.write_package_file(folder / "linear_authority.json", {},
                                           saved["authority"], saved["descriptor"])
                (folder / "linear_authority.json").write_text("{}\n")
                with self.assertRaisesRegex(ValueError, "persisted_authority"):
                    new.validate_persisted(saved["descriptor"], saved["authority"])
                with self.assertRaises(RuntimeError):
                    closure.fail(ValueError("second"), "analysis", lambda *_: None)
            finally:
                journal.close()
