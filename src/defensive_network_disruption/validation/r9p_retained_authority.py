"""Prospective retained-journal authority for Session 14R9P.

This module has no geometry, field-evaluation, or scientific-summary route.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Mapping

from . import r9j_linear_publication as linear
from .r5_persistence import safe
from .state_lifecycle import LifecycleError, canonical_bytes


_SEAL = object()
_TERMINAL_FIELDS = ("state", "edge", "candidate", "stage", "exception")


@dataclass(frozen=True)
class RetainedJournalDescriptor:
    authority_id: str
    raw_sha256: str
    traceback_sha256: str
    terminal: tuple[str, str, str, str, str]
    selected_state: str
    selected_edge: str

    def __post_init__(self) -> None:
        if not self.authority_id or any(len(value) != 64 for value in (self.raw_sha256, self.traceback_sha256)):
            raise ValueError("descriptor_schema")
        if any(character not in "0123456789abcdef" for value in (self.raw_sha256, self.traceback_sha256) for character in value):
            raise ValueError("descriptor_hash")
        if len(self.terminal) != len(_TERMINAL_FIELDS) or any(not isinstance(value, str) or not value for value in self.terminal):
            raise ValueError("descriptor_terminal")
        if not self.selected_state or not self.selected_edge:
            raise ValueError("descriptor_receipt")


R9I = RetainedJournalDescriptor(
    authority_id="session_14r9i_retained_failure",
    raw_sha256="6f1c2110d20fc0edbfe9d337f231e829a73df9d90eb47f65f6afb2366054ef3c",
    traceback_sha256="a43e4740e2fceaa9a6d02cf335bdbc80f09880d69d0675950705a6aac4b2d369",
    terminal=("4", "7", "constant_width", "onset_adaptive", "GateFailure"),
    selected_state="4",
    selected_edge="7",
)

R9N = RetainedJournalDescriptor(
    authority_id="session_14r9n_retained_failure",
    raw_sha256="ab5600ba8eea54092996bb2f4c613c76a5ba331c25c2c9d2b7bb65fa6e9555db",
    traceback_sha256="6d8cf23e2486fd161878260501975e9ec4409eab27bf91ee811be78e0bc3834c",
    terminal=("5", "8", "expanding", "owner_certification", "VerificationError"),
    selected_state="5",
    selected_edge="8",
)

REGISTRY: Mapping[str, RetainedJournalDescriptor] = {item.authority_id: item for item in (R9I, R9N)}


@dataclass(frozen=True)
class RetainedJournalAuthority:
    _canonical: bytes
    _seal: object

    def __post_init__(self) -> None:
        if self._seal is not _SEAL:
            raise TypeError("verified_stream_required")

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self._canonical).hexdigest()

    def record(self) -> dict:
        import json
        return json.loads(self._canonical)

    @property
    def derived_record_count(self) -> int:
        return self.record()["derived_record_count"]

    @property
    def action_counts(self) -> dict[str, int]:
        return self.record()["action_counts"]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with safe(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def review_registered(
    journal_path: Path,
    traceback_path: Path,
    descriptor: RetainedJournalDescriptor,
) -> RetainedJournalAuthority:
    """Validate and summarize one retained journal in exactly one journal pass."""
    if REGISTRY.get(descriptor.authority_id) != descriptor:
        raise LifecycleError("unregistered_retained_authority")

    journal_path = safe(journal_path)
    traceback_path = safe(traceback_path)
    before = journal_path.stat()
    engine = linear.Replay()
    previous = None
    raw_hash = hashlib.sha256()
    actions: Counter[str] = Counter()
    record_count = 0
    selected_receipt = None
    semantic_error: BaseException | None = None

    with journal_path.open("rb") as handle:
        for line in handle:
            raw_hash.update(line)
            if not line.endswith(b"\n"):
                raise LifecycleError("interrupted_journal_write")
            import json
            record = json.loads(line)
            if canonical_bytes(record) != line:
                raise LifecycleError("journal_encoding")
            if set(record) != {"schema_version", "sequence", "previous", "action", "payload"}:
                raise LifecycleError("journal_schema")
            if record["schema_version"] != 1 or record["sequence"] != record_count or record["previous"] != previous:
                raise LifecycleError("journal_chain")
            previous = linear.digest(record)
            record_count += 1
            actions[record["action"]] += 1
            if semantic_error is None:
                try:
                    engine.step(record)
                    if record["action"] == "projection_materialized":
                        payload = record["payload"]
                        state = engine.base.attempts[payload["attempt"]]["state"]
                        if state == descriptor.selected_state and descriptor.selected_edge in payload["edges"]:
                            selected_receipt = {
                                "state": state,
                                "edge_present": True,
                                "sequence": record["sequence"],
                                "record_sha256": previous,
                                "attempt": payload["attempt"],
                            }
                except BaseException as error:
                    semantic_error = error

    raw = raw_hash.hexdigest()
    if raw != descriptor.raw_sha256:
        raise LifecycleError("retained_raw_hash")
    after = journal_path.stat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
        after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns
    ):
        raise LifecycleError("journal_changed_during_review")
    if semantic_error is not None:
        raise semantic_error
    if _sha256(traceback_path) != descriptor.traceback_sha256:
        raise LifecycleError("traceback_authority")
    result = engine.result()
    failure = engine.failure
    if failure is None or tuple(failure[field] for field in _TERMINAL_FIELDS) != descriptor.terminal:
        raise LifecycleError("terminal_failure_context")
    if failure.get("traceback_sha256") != descriptor.traceback_sha256:
        raise LifecycleError("terminal_traceback_binding")
    if selected_receipt is None:
        raise LifecycleError("selected_materialization_receipt")
    if not result["terminal"]:
        raise LifecycleError("nonterminal_retained_journal")

    snapshot = result["snapshot"]
    record = {
        "schema_version": 1,
        "authority_id": descriptor.authority_id,
        "raw_sha256": raw,
        "chain_head_sha256": previous,
        "derived_record_count": record_count,
        "action_counts": dict(sorted(actions.items())),
        "terminal": {field: failure[field] for field in _TERMINAL_FIELDS},
        "traceback_sha256": descriptor.traceback_sha256,
        "traceback_valid": True,
        "selected_receipt": selected_receipt,
        "lifecycle_snapshot_sha256": linear.digest(snapshot),
        "counters": snapshot["counters"],
        "field_work_by_candidate": snapshot["field_work_by_candidate"],
        "sequence_valid": True,
        "chain_valid": True,
        "canonical_encoding_valid": True,
        "count_role": "CB_DERIVED_CONSISTENCY_FACT",
        "source_bytes": after.st_size,
    }
    return RetainedJournalAuthority(canonical_bytes(record), _SEAL)


def action_delta(earlier: RetainedJournalAuthority, later: RetainedJournalAuthority) -> list[dict]:
    left, right = earlier.action_counts, later.action_counts
    return [
        {"action": action, "r9i_count": left.get(action, 0), "r9n_count": right.get(action, 0),
         "delta": right.get(action, 0) - left.get(action, 0)}
        for action in sorted(set(left) | set(right))
    ]


def validate_expected_delta(rows: list[dict]) -> None:
    expected = {
        "numerical_stage": 226,
        "field_started": 21,
        "field_completed": 21,
        "edge_completed": 10,
        "state_completed": 1,
        "state_evaluation_started": 1,
    }
    observed = {row["action"]: row["delta"] for row in rows if row["delta"]}
    if observed != expected or sum(observed.values()) != 280:
        raise LifecycleError("unexplained_record_delta")
