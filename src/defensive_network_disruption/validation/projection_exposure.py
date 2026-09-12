"""Synthetic projection-to-edge exposure accounting.

This internal module is intentionally independent of field and empirical code.
It records durable projection receipts, geometric-edge progress, and candidate
work without changing the historical Session 14 lifecycle implementations.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .r5_persistence import Journal, digest, read_journal
from .state_lifecycle import LifecycleError


CANDIDATES = ("isotropic", "expanding", "constant_width")
MODES = ("pre_access", "empirical_partial", "empirical_failure", "empirical_success")


def _edge_key(state: str, edge: str) -> tuple[str, str]:
    if not isinstance(state, str) or not state or not isinstance(edge, str) or not edge:
        raise LifecycleError("invalid_edge_identity")
    return state, edge


def _expected_fields() -> dict[str, int]:
    return {candidate: 0 for candidate in CANDIDATES}


def replay_exposure(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Replay journal records and derive the complete public accounting view."""
    states: dict[str, dict[str, Any]] = {}
    attempts: dict[str, dict[str, Any]] = {}
    opened: set[tuple[str, str]] = set()
    edge_started: set[tuple[str, str]] = set()
    edge_completed: set[tuple[str, str]] = set()
    field_started: set[tuple[str, str, str]] = set()
    field_completed: set[tuple[str, str, str]] = set()
    active_state = active_edge = active_candidate = None
    authorized = initialized = False
    status = "active"
    failure_stage = exception = None

    for record in records:
        action = record["action"]
        payload = record["payload"]
        if status != "active" and action not in ("failure_evidence",):
            raise LifecycleError("event_after_terminal")
        if action == "initialized":
            if initialized:
                raise LifecycleError("duplicate_initialization")
            initialized = True
        elif action == "access_authorized":
            if not initialized or authorized:
                raise LifecycleError("invalid_authorization")
            authorized = True
        elif action == "state_discovered":
            state = payload.get("state"); edges = tuple(payload.get("edges", ()))
            if not authorized or not isinstance(state, str) or not state or state in states:
                raise LifecycleError("invalid_state_discovery")
            if not edges or len(set(edges)) != len(edges) or any(not isinstance(e, str) or not e for e in edges):
                raise LifecycleError("invalid_required_edges")
            states[state] = {"edges": edges, "prepared": False, "evaluation_started": False,
                             "completed": False, "failed": False}
            active_state = state
        elif action == "projection_attempt":
            attempt = payload.get("attempt"); state = payload.get("state")
            if not authorized or state not in states or not isinstance(attempt, str) or attempt in attempts:
                raise LifecycleError("invalid_projection_attempt")
            if any(item["state"] == state and item["status"] == "pending" for item in attempts.values()):
                raise LifecycleError("overlapping_projection_attempt")
            attempts[attempt] = {"state": state, "status": "pending"}
            active_state = state
        elif action in ("projection_not_materialized", "projection_materialized"):
            attempt = payload.get("attempt")
            if attempt not in attempts or attempts[attempt]["status"] != "pending":
                raise LifecycleError("unmatched_projection_receipt")
            state = attempts[attempt]["state"]
            if action == "projection_not_materialized":
                attempts[attempt]["status"] = "not_materialized"
            else:
                edges = tuple(payload.get("edges", ()))
                if edges != states[state]["edges"]:
                    raise LifecycleError("projection_edge_mismatch")
                keys = {_edge_key(state, edge) for edge in edges}
                if opened.intersection(keys):
                    raise LifecycleError("duplicate_edge_materialization")
                opened.update(keys); attempts[attempt]["status"] = "materialized"
        elif action == "state_prepared":
            state = payload.get("state"); item = states.get(state)
            required = {_edge_key(state, edge) for edge in item["edges"]} if item else set()
            if item is None or item["prepared"] or not required.issubset(opened):
                raise LifecycleError("invalid_state_preparation")
            item["prepared"] = True; active_state = state
        elif action == "state_evaluation_started":
            state = payload.get("state"); item = states.get(state)
            if item is None or not item["prepared"] or item["evaluation_started"]:
                raise LifecycleError("invalid_state_evaluation_start")
            item["evaluation_started"] = True; active_state = state
        elif action == "field_started":
            state, edge, candidate = payload.get("state"), payload.get("edge"), payload.get("candidate")
            key = _edge_key(state, edge); item = states.get(state)
            call = (state, edge, candidate)
            if item is None or not item["evaluation_started"] or key not in opened or edge not in item["edges"]:
                raise LifecycleError("field_without_open_edge")
            if candidate not in CANDIDATES or call in field_started or active_candidate is not None:
                raise LifecycleError("invalid_field_start")
            position = CANDIDATES.index(candidate)
            if any((state, edge, prior) not in field_completed for prior in CANDIDATES[:position]):
                raise LifecycleError("field_order")
            field_started.add(call); edge_started.add(key)
            active_state, active_edge, active_candidate = state, edge, candidate
        elif action == "field_completed":
            state, edge, candidate = payload.get("state"), payload.get("edge"), payload.get("candidate")
            call = (state, edge, candidate)
            if call not in field_started or call in field_completed or (state, edge, candidate) != (active_state, active_edge, active_candidate):
                raise LifecycleError("invalid_field_completion")
            field_completed.add(call); active_candidate = None
        elif action == "edge_completed":
            state, edge = payload.get("state"), payload.get("edge"); key = _edge_key(state, edge)
            if key not in edge_started or key in edge_completed or any((state, edge, c) not in field_completed for c in CANDIDATES):
                raise LifecycleError("invalid_edge_completion")
            edge_completed.add(key); active_edge = active_candidate = None
        elif action == "state_completed":
            state = payload.get("state"); item = states.get(state)
            required = {_edge_key(state, edge) for edge in item["edges"]} if item else set()
            if item is None or not item["evaluation_started"] or item["completed"] or not required.issubset(edge_completed):
                raise LifecycleError("invalid_state_completion")
            item["completed"] = True; active_state = active_edge = active_candidate = None
        elif action == "failure":
            failure_stage, exception = payload.get("stage"), payload.get("exception")
            if not isinstance(failure_stage, str) or not failure_stage or not isinstance(exception, str) or not exception:
                raise LifecycleError("failure_evidence")
            status = "failure"
            state, edge, candidate = payload.get("state"), payload.get("edge"), payload.get("candidate")
            if state is not None: active_state = state
            if edge is not None: active_edge = edge
            if candidate is not None: active_candidate = candidate
            if active_state in states: states[active_state]["failed"] = True
        elif action == "blocked":
            if not payload.get("stage") or not payload.get("reason"):
                raise LifecycleError("blocked_evidence")
            status = "blocked"; failure_stage = payload["stage"]
        elif action == "success":
            status = "success"; active_state = active_edge = active_candidate = None
        elif action != "failure_evidence":
            raise LifecycleError("unknown_exposure_event")

    if not initialized:
        raise LifecycleError("journal_not_initialized")
    unresolved_attempts = sum(item["status"] == "pending" for item in attempts.values())
    unresolved_edges = opened - edge_completed
    state_completed = sum(item["completed"] for item in states.values())
    state_prepared = sum(item["prepared"] for item in states.values())
    state_evaluated = sum(item["evaluation_started"] for item in states.values())
    field_by_candidate = {
        candidate: {"started": sum(call[2] == candidate for call in field_started),
                    "completed": sum(call[2] == candidate for call in field_completed)}
        for candidate in CANDIDATES
    }
    counters = {
        "states_discovered": len(states), "states_prepared": state_prepared,
        "states_evaluation_started": state_evaluated, "states_completed": state_completed,
        "edges_discovered": sum(len(item["edges"]) for item in states.values()),
        "edges_opened": len(opened), "edges_evaluation_started": len(edge_started),
        "edges_completed": len(edge_completed), "unresolved_exposed_edges": len(unresolved_edges),
        "projection_attempts": len(attempts), "unresolved_projection_attempts": unresolved_attempts,
        "field_evaluations_started": len(field_started),
        "field_evaluations_completed": len(field_completed),
        "state_failures": sum(item["failed"] for item in states.values()),
    }
    if not (counters["edges_completed"] <= counters["edges_evaluation_started"] <= counters["edges_opened"] <= counters["edges_discovered"]):
        raise LifecycleError("edge_counter_order")
    if counters["unresolved_exposed_edges"] != counters["edges_opened"] - counters["edges_completed"]:
        raise LifecycleError("unresolved_exposure_mismatch")
    if status == "success":
        if (not states or unresolved_attempts or counters["unresolved_exposed_edges"] or
                counters["states_completed"] != counters["states_discovered"] or
                counters["field_evaluations_completed"] != 3 * counters["edges_completed"]):
            raise LifecycleError("incomplete_success")
    return {
        "schema_version": 1, "status": status, "access_authorized": authorized,
        "counters": counters, "field_work_by_candidate": field_by_candidate,
        "active": {"state": active_state, "edge": active_edge, "candidate": active_candidate},
        "failure_stage": failure_stage, "exception": exception,
        "confirmed_zero_exposure": counters["edges_opened"] == 0 and unresolved_attempts == 0,
    }


class ExposureAuthority:
    """Mutating façade whose facts remain fully replayable from its journal."""

    def __init__(self, journal_path: Path):
        self.journal = Journal(journal_path)
        self.journal.append("initialized")

    def _append(self, action: str, **payload: Any) -> None:
        records, head = read_journal(self.journal.path)
        proposed = {"schema_version": 1, "sequence": self.journal.count,
                    "previous": head, "action": action, "payload": payload}
        replay_exposure((*records, proposed))
        self.journal.append(action, **payload)

    def authorize_access(self) -> None: self._append("access_authorized")
    def discover_state(self, state: str, edges: Sequence[str]) -> None:
        self._append("state_discovered", state=state, edges=list(edges))
    def begin_projection(self, state: str) -> str:
        attempt = f"projection_{self.journal.count:06d}"
        self._append("projection_attempt", attempt=attempt, state=state)
        return attempt
    def materialized(self, attempt: str, edges: Sequence[str]) -> None:
        self._append("projection_materialized", attempt=attempt, edges=list(edges))
    def not_materialized(self, attempt: str) -> None:
        self._append("projection_not_materialized", attempt=attempt)
    def project(self, state: str, callback: Callable[[], Any]) -> Any:
        attempt = self.begin_projection(state)
        try:
            result = callback()
        except BaseException:
            self.not_materialized(attempt)
            raise
        records = read_journal(self.journal.path)[0]
        required = next(tuple(r["payload"]["edges"]) for r in records if r["action"] == "state_discovered" and r["payload"]["state"] == state)
        self.materialized(attempt, required)
        return result
    def prepare_state(self, state: str) -> None: self._append("state_prepared", state=state)
    def start_state(self, state: str) -> None: self._append("state_evaluation_started", state=state)
    def start_field(self, state: str, edge: str, candidate: str) -> None:
        self._append("field_started", state=state, edge=edge, candidate=candidate)
    def complete_field(self, state: str, edge: str, candidate: str) -> None:
        self._append("field_completed", state=state, edge=edge, candidate=candidate)
    def complete_edge(self, state: str, edge: str) -> None: self._append("edge_completed", state=state, edge=edge)
    def complete_state(self, state: str) -> None: self._append("state_completed", state=state)
    def fail(self, stage: str, exception: BaseException, *, state: str | None = None,
             edge: str | None = None, candidate: str | None = None) -> None:
        self._append("failure", stage=stage, exception=type(exception).__name__, state=state,
                     edge=edge, candidate=candidate)
    def block(self, stage: str, reason: str) -> None: self._append("blocked", stage=stage, reason=reason)
    def succeed(self) -> None: self._append("success")
    def close(self) -> None: self.journal.close()


def progress_view(journal_path: Path, *, expected_head: str, mode: str) -> dict[str, Any]:
    if mode not in MODES:
        raise LifecycleError("publication_mode")
    records, head = read_journal(journal_path, expected_head=expected_head)
    snapshot = replay_exposure(records)
    if mode == "pre_access" and not snapshot["confirmed_zero_exposure"]:
        raise LifecycleError("pre_access_not_confirmed_zero")
    if mode == "empirical_success" and snapshot["status"] != "success":
        raise LifecycleError("success_status")
    if mode == "empirical_failure" and snapshot["status"] != "failure":
        raise LifecycleError("failure_status")
    if mode == "empirical_partial" and snapshot["status"] not in ("failure", "blocked"):
        raise LifecycleError("partial_status")
    return {"schema_version": 1, "mode": mode, "journal_sha256": head,
            "snapshot_sha256": digest(snapshot), "snapshot": snapshot}


def package_record(view: Mapping[str, Any], **extra: Any) -> dict[str, Any]:
    result = {"schema_version": 1, "status": view["snapshot"]["status"],
              "progress_authority": json.loads(json.dumps(view))}
    result.update(extra)
    return result


def validate_cross_file_package(*, journal_path: Path, expected_head: str, mode: str,
                                qc: Mapping[str, Any], manifest: Mapping[str, Any],
                                evidence: Mapping[str, Any], report: Mapping[str, Any]) -> dict[str, Any]:
    actual = progress_view(journal_path, expected_head=expected_head, mode=mode)
    for name, record in (("qc", qc), ("manifest", manifest), ("evidence", evidence), ("report", report)):
        if record.get("schema_version") != 1 or record.get("status") != actual["snapshot"]["status"]:
            raise LifecycleError(name + "_status")
        if record.get("progress_authority") != actual:
            raise LifecycleError(name + "_progress_authority")
    return actual


@dataclass(frozen=True)
class FailureEvidence:
    pre_failure: Mapping[str, Any]
    terminal: Mapping[str, Any]


def capture_failure(authority: ExposureAuthority, *, stage: str, exception: BaseException,
                    state: str | None = None, edge: str | None = None,
                    candidate: str | None = None) -> FailureEvidence:
    before = replay_exposure(read_journal(authority.journal.path)[0])
    authority.fail(stage, exception, state=state, edge=edge, candidate=candidate)
    after = replay_exposure(read_journal(authority.journal.path)[0])
    return FailureEvidence(before, after)
