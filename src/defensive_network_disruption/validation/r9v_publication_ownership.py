"""Prospective single-writer ownership for immutable linear authority.

Terminal closure is the sole writer.  Publishers receive a content-bound
descriptor and may only validate the already persisted authority.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from . import r9j_evidence as evidence
from . import r9j_linear_publication as linear
from .checkpoint_ci_authority import FailureController


@dataclass(frozen=True)
class PersistedAuthority:
    path: Path
    sha256: str
    record_sha256: str

    def __post_init__(self):
        if not self.path.name == "linear_authority.json":
            raise ValueError("authority_path")
        for value in (self.sha256, self.record_sha256):
            if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
                raise ValueError("authority_hash")


def _canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def _digest_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def persist_authority(directory, authority) -> PersistedAuthority:
    """The one authorized immutable write."""
    path = Path(directory) / "linear_authority.json"
    raw = _canonical(authority.record())
    evidence.put_bytes(path, raw)
    return PersistedAuthority(path, evidence.sha(path), _digest_bytes(raw))


def validate_persisted(descriptor: PersistedAuthority, authority) -> dict:
    """Read-only validation; never creates or replaces authority evidence."""
    raw = descriptor.path.read_bytes()
    expected = _canonical(authority.record())
    if _digest_bytes(raw) != descriptor.sha256:
        raise ValueError("persisted_authority_hash")
    if _digest_bytes(expected) != descriptor.record_sha256 or raw != expected:
        raise ValueError("persisted_authority_content")
    return json.loads(raw)


class TerminalClosure:
    """One terminal event, one review, one authority owner."""

    def __init__(self, progress, directory):
        self.progress = progress
        self.directory = Path(directory)
        self.controller = FailureController(self.directory)
        self.closed = False

    def _claim(self):
        if self.closed:
            raise RuntimeError("terminal_already_closed")
        evidence.put(self.directory / "terminal.marker", {"reserved": True})
        self.closed = True

    def _publish(self, authority, traceback_path, publisher):
        descriptor = persist_authority(self.directory, authority)
        validate_persisted(descriptor, authority)
        return publisher(authority, descriptor, traceback_path)

    def fail(self, error, stage, publisher):
        self._claim()
        original = self.controller.capture(error, stage, context=self.progress.context)
        try:
            state, edge, candidate = self.progress.context or (None, None, None)
            journal_stage = self.progress.numerical_context if self.progress.context else "preparation"
            if journal_stage is None:
                journal_stage = "geometry"
            self.progress.journal.append(
                "failure", stage=journal_stage, exception=type(error).__name__,
                state=state, edge=edge, candidate=candidate,
                traceback_sha256=original["traceback_sha256"])
            authority = linear.review(self.progress.journal.path,
                                      expected_head=self.progress.journal.previous)
            return self._publish(authority, self.controller.traceback_path, publisher)
        except BaseException as publication_error:
            self.controller.publication_failure(publication_error)
            raise

    def succeed(self, publisher):
        self._claim()
        p = self.progress
        if p.context is not None or p._attempts or not p._states or not all(
                value["done"] for value in p._states.values()):
            raise ValueError("incomplete_success")
        p.journal.append("success")
        authority = linear.review(p.journal.path, expected_head=p.journal.previous)
        return self._publish(authority, None, publisher)


def write_package_file(path, value, authority, descriptor):
    """Package writers own package paths only and must validate authority first."""
    validate_persisted(descriptor, authority)
    if Path(path).resolve() == descriptor.path.resolve():
        raise PermissionError("second_authority_owner")
    evidence.put(path, value)


def controls(folder):
    """Exercise real journals and the prospective ownership boundary."""
    from unittest.mock import patch
    from . import numerical_failure_publication as legacy
    from . import r7_execution as execution
    from .r5_persistence import Journal

    rows = []
    for fixture in ("success", "pre_access_failure", "numerical_failure",
                    "publication_initialization_failure", "publisher_failure"):
        place = Path(folder) / fixture
        journal = Journal(place / "journal.jsonl")
        progress = execution.Progress(journal)
        closure = TerminalClosure(progress, place)
        reviews = []
        try:
            if fixture in ("success", "numerical_failure"):
                progress.authorize_access()
                progress.discover_state("state", ("edge",))
                progress.project("state", lambda: None)
                progress.prepare_state("state")
                progress.start_state("state")
                candidates = ("isotropic", "expanding", "constant_width")
                for candidate in candidates:
                    progress.call_start("state", "edge", candidate)
                    stages = ("geometry", "joint_simpson", "envelope", "owner_certification",
                              "partition_construction")
                    for stage in stages:
                        progress.numerical_stage(stage=stage)
                    if fixture == "numerical_failure":
                        break
                    progress.numerical_stage(stage="routing", pieces=1, bounded=0, quadrature=1)
                    for stage in ("strict_piecewise", "repeat_piecewise", "onset_adaptive",
                                  "direct_simpson", "accepted"):
                        progress.numerical_stage(stage=stage)
                    progress.call_complete()
                if fixture == "success":
                    progress.retain_and_complete_edges("state")
                    progress.complete_state("state")

            def publisher(authority, descriptor, trace):
                validate_persisted(descriptor, authority)
                if fixture in ("publication_initialization_failure", "publisher_failure"):
                    raise RuntimeError(fixture)
                target = place / "package.json"
                write_package_file(target, {"status": fixture, "trace": trace is not None},
                                   authority, descriptor)
                return evidence.sha(target)

            with patch.object(linear, "review", wraps=linear.review) as review, \
                 patch.object(execution.Progress, "failure", side_effect=AssertionError("legacy_replay")), \
                 patch.object(execution._CoreView, "snapshot", side_effect=AssertionError("legacy_replay")), \
                 patch.object(legacy, "replay", side_effect=AssertionError("legacy_replay")):
                try:
                    if fixture == "success":
                        closure.succeed(publisher)
                    else:
                        closure.fail(ValueError("synthetic_original"), "synthetic_test", publisher)
                except RuntimeError as error:
                    if fixture not in ("publication_initialization_failure", "publisher_failure") or str(error) != fixture:
                        raise
                reviews.append(review.call_count)
            valid = closure.controller.validate()["status"] == "valid" if fixture != "success" else True
            publication_failure = (place / "publication_failure.json").exists()
            passed = reviews == [1] and valid and (
                publication_failure == (fixture in ("publication_initialization_failure", "publisher_failure")))
            rows.append({"fixture": fixture, "passed": passed, "reviews": reviews[0],
                         "authority_sha256": evidence.sha(place / "linear_authority.json")})
        finally:
            journal.close()

    # Negative ownership controls do not create another review.
    base = Path(folder) / "ownership_negatives"
    base.mkdir(parents=True, exist_ok=True)
    for fixture in ("repeated_closure", "preexisting_authority", "tampering", "namespace_collision"):
        passed = False
        place = base / fixture
        place.mkdir(parents=True, exist_ok=True)
        journal = Journal(place / "journal.jsonl")
        progress = execution.Progress(journal)
        closure = TerminalClosure(progress, place)
        try:
            if fixture == "preexisting_authority":
                evidence.put(place / "linear_authority.json", {"stale": True})
                try:
                    closure.fail(ValueError("original"), "startup", lambda *_: None)
                except FileExistsError:
                    passed = True
            else:
                saved = {}
                closure.fail(ValueError("original"), "startup",
                    lambda authority, descriptor, trace: saved.update(
                        authority=authority, descriptor=descriptor))
                if fixture == "repeated_closure":
                    try:
                        closure.fail(ValueError("second"), "startup", lambda *_: None)
                    except RuntimeError:
                        passed = True
                elif fixture == "tampering":
                    saved["descriptor"].path.write_text("{}\n")
                    try:
                        validate_persisted(saved["descriptor"], saved["authority"])
                    except ValueError:
                        passed = True
                else:
                    try:
                        write_package_file(saved["descriptor"].path, {}, saved["authority"],
                                           saved["descriptor"])
                    except PermissionError:
                        passed = True
            rows.append({"fixture": fixture, "passed": passed,
                         "reviews": 0 if fixture == "preexisting_authority" else 1,
                         "authority_sha256": (evidence.sha(place / "linear_authority.json")
                                               if (place / "linear_authority.json").exists() else "0" * 64)})
        finally:
            journal.close()
    return rows
