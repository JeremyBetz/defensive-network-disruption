"""Internal empirical-capable lifecycle and publication authority.

This module wraps the preserved Session 14ae lifecycle.  It adds an append-only
access journal, explicit publication contexts, and cross-file validation without
changing the historical implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import math
import traceback as traceback_module
from typing import Any, Callable, Mapping, Sequence

from .state_lifecycle import (
    COUNTER_KEYS,
    LifecycleError,
    LifecycleProgress,
    canonical_bytes,
    snapshot_digest,
    validate_snapshot,
)


class ValidationMode(str, Enum):
    PRE_ACCESS = "pre_access"
    EMPIRICAL_PARTIAL = "empirical_partial"
    EMPIRICAL_FAILURE = "empirical_failure"
    EMPIRICAL_SUCCESS = "empirical_success"


VIEW_FIELDS = {
    "schema_version", "validation_mode", "status", "lifecycle_initialized",
    "lifecycle", "lifecycle_sha256", "journal_sha256", "access",
    "active_state", "active_edge", "failure_stage", "traceback_preserved",
    "traceback_sha256",
}


def _digest(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _finite(value: object) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise LifecycleError("nonfinite_authority")
    if isinstance(value, Mapping):
        for item in value.values():
            _finite(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _finite(item)


class EmpiricalLifecycle:
    """Session 14ae lifecycle plus a private hash-chained transition journal."""

    def __init__(self) -> None:
        self.progress = LifecycleProgress()
        self._journal: list[dict[str, Any]] = []
        self._record("initialized")

    @property
    def journal(self) -> tuple[dict[str, Any], ...]:
        return tuple(json.loads(json.dumps(item)) for item in self._journal)

    def _record(self, action: str, *, state: str | None = None, edge: str | None = None) -> None:
        snapshot = self.progress.snapshot()
        entry = {
            "schema_version": 1,
            "index": len(self._journal),
            "action": action,
            "state": state,
            "edge": edge,
            "previous_sha256": _digest(self._journal[-1]) if self._journal else None,
            "snapshot": snapshot,
            "snapshot_sha256": snapshot_digest(snapshot),
        }
        self._journal.append(entry)

    def discover_state(self, key: str, edges: Sequence[str]) -> None:
        self.progress.discover_state(key, edges); self._record("discover_state", state=key)

    def prepare_state(self, key: str) -> None:
        self.progress.prepare_state(key); self._record("prepare_state", state=key)

    def start_state_evaluation(self, key: str) -> None:
        self.progress.start_state_evaluation(key); self._record("start_state_evaluation", state=key)

    def start_edge(self, state: str, edge: str) -> None:
        self.progress.start_edge(state, edge); self._record("start_edge", state=state, edge=edge)

    def complete_edge(self, state: str, edge: str) -> None:
        self.progress.complete_edge(state, edge); self._record("complete_edge", state=state, edge=edge)

    def complete_state(self, key: str) -> None:
        self.progress.complete_state(key); self._record("complete_state", state=key)

    def authorize_access(self) -> None:
        self.progress.authorize_access(); self._record("authorize_access")

    def open_state(self, key: str) -> None:
        self.progress.open_state(key); self._record("open_state", state=key)

    def open_edge(self, state: str, edge: str) -> None:
        self.progress.open_edge(state, edge); self._record("open_edge", state=state, edge=edge)

    def fail(self, stage: str, exception: str, *, state: str | None = None, edge: str | None = None) -> None:
        self.progress.fail(stage, exception, state_key=state, edge_key=edge)
        self._record("fail", state=state, edge=edge)

    def block(self, stage: str, reason: str) -> None:
        self.progress.block(stage, reason); self._record("block")

    def succeed(self) -> None:
        self.progress.succeed(); self._record("succeed")

    def snapshot(self) -> dict[str, Any]:
        return self.progress.snapshot()


def validate_journal(journal: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if not journal:
        raise LifecycleError("journal_empty")
    previous: str | None = None
    prior_counters: dict[str, int] | None = None
    opened_states: set[str] = set()
    opened_edges: set[tuple[str, str]] = set()
    for index, raw in enumerate(journal):
        entry = dict(raw)
        expected = {"schema_version", "index", "action", "state", "edge", "previous_sha256", "snapshot", "snapshot_sha256"}
        if set(entry) != expected or entry["schema_version"] != 1 or entry["index"] != index:
            raise LifecycleError("journal_schema")
        if entry["previous_sha256"] != previous:
            raise LifecycleError("journal_chain")
        validate_snapshot(entry["snapshot"], terminal=False)
        if entry["snapshot_sha256"] != snapshot_digest(entry["snapshot"]):
            raise LifecycleError("journal_snapshot_digest")
        counters = entry["snapshot"]["counters"]
        if prior_counters is not None and any(counters[key] < prior_counters[key] for key in COUNTER_KEYS):
            raise LifecycleError("journal_counter_reset")
        prior_counters = dict(counters)
        action, state, edge = entry["action"], entry["state"], entry["edge"]
        if action == "open_state":
            if not isinstance(state, str) or state in opened_states:
                raise LifecycleError("journal_state_open")
            opened_states.add(state)
        elif action == "open_edge":
            key = (state, edge)
            if not isinstance(state, str) or not isinstance(edge, str) or state not in opened_states or key in opened_edges:
                raise LifecycleError("journal_edge_open")
            opened_edges.add(key)
        previous = _digest(entry)
    final = dict(journal[-1]["snapshot"])
    counters = final["counters"]
    if counters["states_opened"] != len(opened_states) or counters["edges_opened"] != len(opened_edges):
        raise LifecycleError("journal_access_mismatch")
    return {
        "journal_sha256": _digest(list(journal)),
        "states_opened": len(opened_states),
        "edges_opened": len(opened_edges),
        "final_snapshot": final,
    }


def make_progress_view(
    authority: EmpiricalLifecycle,
    mode: ValidationMode | str,
    *,
    traceback_text: str | None = None,
) -> dict[str, Any]:
    mode = ValidationMode(mode)
    snapshot = authority.snapshot()
    journal_result = validate_journal(authority.journal)
    trace_hash = hashlib.sha256(traceback_text.encode()).hexdigest() if traceback_text is not None else None
    view = {
        "schema_version": 1,
        "validation_mode": mode.value,
        "status": snapshot["status"],
        "lifecycle_initialized": True,
        "lifecycle": snapshot,
        "lifecycle_sha256": snapshot_digest(snapshot),
        "journal_sha256": journal_result["journal_sha256"],
        "access": {
            "states_opened": journal_result["states_opened"],
            "edges_opened": journal_result["edges_opened"],
        },
        "active_state": snapshot["active_state"],
        "active_edge": snapshot["active_edge"],
        "failure_stage": snapshot["stage"] if snapshot["status"] == "failure" else None,
        "traceback_preserved": traceback_text is not None,
        "traceback_sha256": trace_hash,
    }
    validate_progress_view(view, authority.journal)
    return view


def make_preinitialization_failure(stage: str, exception: BaseException, traceback_text: str) -> dict[str, Any]:
    if not stage or not traceback_text:
        raise LifecycleError("preinitialization_failure_evidence")
    return {
        "schema_version": 1,
        "validation_mode": ValidationMode.PRE_ACCESS.value,
        "status": "failure",
        "lifecycle_initialized": False,
        "lifecycle": None,
        "lifecycle_sha256": None,
        "journal_sha256": _digest([]),
        "access": {"states_opened": 0, "edges_opened": 0},
        "active_state": None,
        "active_edge": None,
        "failure_stage": stage,
        "traceback_preserved": True,
        "traceback_sha256": hashlib.sha256(traceback_text.encode()).hexdigest(),
    }


def validate_progress_view(view: Mapping[str, Any], journal: Sequence[Mapping[str, Any]] | None = None) -> None:
    if set(view) != VIEW_FIELDS or view["schema_version"] != 1:
        raise LifecycleError("progress_view_schema")
    _finite(view)
    try:
        mode = ValidationMode(view["validation_mode"])
    except (TypeError, ValueError) as exc:
        raise LifecycleError("validation_mode") from exc
    access = view["access"]
    if set(access) != {"states_opened", "edges_opened"} or any(type(access[key]) is not int or access[key] < 0 for key in access):
        raise LifecycleError("access_schema")
    if not view["lifecycle_initialized"]:
        if mode is not ValidationMode.PRE_ACCESS or view["status"] != "failure" or view["lifecycle"] is not None or view["lifecycle_sha256"] is not None:
            raise LifecycleError("preinitialization_mode")
        if access != {"states_opened": 0, "edges_opened": 0} or view["active_state"] is not None or view["active_edge"] is not None:
            raise LifecycleError("preinitialization_access")
        if not view["traceback_preserved"] or not isinstance(view["traceback_sha256"], str):
            raise LifecycleError("preinitialization_traceback")
        return
    snapshot = view["lifecycle"]
    validate_snapshot(snapshot)
    if view["lifecycle_sha256"] != snapshot_digest(snapshot):
        raise LifecycleError("lifecycle_digest")
    if view["status"] != snapshot["status"] or view["active_state"] != snapshot["active_state"] or view["active_edge"] != snapshot["active_edge"]:
        raise LifecycleError("lifecycle_view_mismatch")
    counters = snapshot["counters"]
    if access != {"states_opened": counters["states_opened"], "edges_opened": counters["edges_opened"]}:
        raise LifecycleError("access_view_mismatch")
    if journal is not None:
        result = validate_journal(journal)
        if result["journal_sha256"] != view["journal_sha256"] or result["final_snapshot"] != snapshot:
            raise LifecycleError("journal_view_mismatch")
        if access != {"states_opened": result["states_opened"], "edges_opened": result["edges_opened"]}:
            raise LifecycleError("journal_access_mismatch")
    if mode is ValidationMode.PRE_ACCESS and access != {"states_opened": 0, "edges_opened": 0}:
        raise LifecycleError("pre_access_nonzero")
    if mode is ValidationMode.EMPIRICAL_PARTIAL and view["status"] not in {"blocked", "failure"}:
        raise LifecycleError("partial_status")
    if mode is ValidationMode.EMPIRICAL_FAILURE and view["status"] != "failure":
        raise LifecycleError("failure_status")
    if mode is ValidationMode.EMPIRICAL_SUCCESS:
        if view["status"] != "success":
            raise LifecycleError("success_status")
        if access["states_opened"] != counters["states_discovered"] or access["edges_opened"] != counters["edges_discovered"]:
            raise LifecycleError("success_access_incomplete")
    if view["status"] == "failure":
        if view["failure_stage"] != snapshot["stage"] or not view["traceback_preserved"] or not isinstance(view["traceback_sha256"], str) or len(view["traceback_sha256"]) != 64:
            raise LifecycleError("failure_view_evidence")
    else:
        if view["failure_stage"] is not None or view["traceback_preserved"] or view["traceback_sha256"] is not None:
            raise LifecycleError("unexpected_failure_evidence")


def package_record(view: Mapping[str, Any], **fields: Any) -> dict[str, Any]:
    record = {"schema_version": 1, "status": view["status"], "progress_authority": json.loads(json.dumps(view))}
    record.update(fields)
    return record


def validate_cross_file_package(
    *,
    mode: ValidationMode | str,
    qc: Mapping[str, Any],
    manifest: Mapping[str, Any],
    evidence: Mapping[str, Any],
    report: Mapping[str, Any],
    journal: Sequence[Mapping[str, Any]] | None,
) -> None:
    if journal is None:
        raise LifecycleError("journal_required")
    expected_view = qc.get("progress_authority")
    if not isinstance(expected_view, Mapping):
        raise LifecycleError("qc_progress_authority")
    validate_progress_view(expected_view, journal)
    if expected_view["validation_mode"] != ValidationMode(mode).value or qc.get("status") != expected_view["status"]:
        raise LifecycleError("qc_mode_status")
    for name, record in (("manifest", manifest), ("evidence", evidence), ("report", report)):
        if record.get("status") != expected_view["status"]:
            raise LifecycleError(name + "_status_mismatch")
        if record.get("progress_authority") != expected_view:
            raise LifecycleError(name + "_progress_mismatch")


@dataclass(frozen=True)
class FailureCapture:
    pre_failure_snapshot: Mapping[str, Any]
    terminal_snapshot: Mapping[str, Any]
    traceback_text: str
    progress_view: Mapping[str, Any]


def capture_unexpected_failure(
    authority: EmpiricalLifecycle,
    callback: Callable[[], None],
    *,
    stage: str,
) -> FailureCapture:
    try:
        callback()
    except Exception as exc:
        before = authority.snapshot()
        state, edge = before["active_state"], before["active_edge"]
        trace = traceback_module.format_exc()
        authority.fail(stage, type(exc).__name__, state=state, edge=edge)
        terminal = authority.snapshot()
        view = make_progress_view(authority, ValidationMode.EMPIRICAL_FAILURE, traceback_text=trace)
        return FailureCapture(before, terminal, trace, view)
    raise LifecycleError("unexpected_failure_not_raised")
