"""Internal lifecycle accounting and publication validation.

This module is deliberately independent of empirical and numerical code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
from typing import Any, Iterable, Mapping


STATE_PHASES = ("discovered", "prepared", "evaluation_started", "evaluation_completed")
EDGE_PHASES = ("discovered", "evaluation_started", "evaluation_completed")
TERMINAL_STATUSES = ("success", "failure", "blocked")
COUNTER_KEYS = (
    "states_discovered", "states_prepared", "states_evaluation_started", "states_completed",
    "edges_discovered", "edges_evaluation_started", "edges_completed",
    "state_failures", "edge_failures", "states_opened", "edges_opened",
)
INTEGRITY_KEYS = (
    "orphan_edges", "completed_states_with_incomplete_edges",
    "failed_completed_states", "failed_completed_edges",
)


class LifecycleError(ValueError):
    """Raised when a lifecycle transition or published record is impossible."""


@dataclass
class _Edge:
    phase: int = 0
    failed: bool = False
    opened: bool = False


@dataclass
class _State:
    edges: tuple[str, ...]
    phase: int = 0
    failed: bool = False
    opened: bool = False
    edge_records: dict[str, _Edge] = field(default_factory=dict)


def canonical_bytes(value: Mapping[str, Any]) -> bytes:
    """Return the finite, sorted, LF-terminated JSON authority representation."""
    _finite(value)
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def snapshot_digest(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _finite(value: Any) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise LifecycleError("nonfinite_value")
    if isinstance(value, Mapping):
        for item in value.values():
            _finite(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _finite(item)


class LifecycleProgress:
    """Own state/edge transitions and derive all public accounting counters."""

    def __init__(self) -> None:
        self._states: dict[str, _State] = {}
        self.status = "active"
        self.stage = "initial"
        self.reason: str | None = None
        self.exception: str | None = None
        self.access_authorized = False
        self.active_state: str | None = None
        self.active_edge: str | None = None

    def _active(self) -> None:
        if self.status != "active":
            raise LifecycleError("terminal_progress")

    def discover_state(self, key: str, edges: Iterable[str]) -> None:
        self._active()
        edge_keys = tuple(edges)
        if not key or key in self._states or not edge_keys or len(set(edge_keys)) != len(edge_keys):
            raise LifecycleError("invalid_state_registration")
        if any(not edge for edge in edge_keys):
            raise LifecycleError("invalid_edge_key")
        self._states[key] = _State(edge_keys, edge_records={edge: _Edge() for edge in edge_keys})
        self.stage = "discovery"

    def prepare_state(self, key: str) -> None:
        self._active(); state = self._state(key)
        if state.phase != 0 or state.failed:
            raise LifecycleError("invalid_prepare_transition")
        state.phase = 1; self.stage = "preparation"; self.active_state = key

    def start_state_evaluation(self, key: str) -> None:
        self._active(); state = self._state(key)
        if state.phase != 1 or state.failed:
            raise LifecycleError("invalid_state_start_transition")
        state.phase = 2; self.stage = "evaluation"; self.active_state = key

    def start_edge(self, state_key: str, edge_key: str) -> None:
        self._active(); state, edge = self._edge(state_key, edge_key)
        if state.phase != 2 or state.failed or edge.phase != 0 or edge.failed:
            raise LifecycleError("invalid_edge_start_transition")
        edge.phase = 1; self.stage = "edge_evaluation"; self.active_state = state_key; self.active_edge = edge_key

    def complete_edge(self, state_key: str, edge_key: str) -> None:
        self._active(); state, edge = self._edge(state_key, edge_key)
        if state.phase != 2 or state.failed or edge.phase != 1 or edge.failed:
            raise LifecycleError("invalid_edge_complete_transition")
        edge.phase = 2; self.active_edge = None

    def complete_state(self, key: str) -> None:
        self._active(); state = self._state(key)
        if state.phase != 2 or state.failed or any(edge.phase != 2 or edge.failed for edge in state.edge_records.values()):
            raise LifecycleError("state_edges_incomplete")
        state.phase = 3; self.active_state = None; self.active_edge = None

    def authorize_access(self) -> None:
        self._active(); self.access_authorized = True

    def open_state(self, key: str) -> None:
        self._active(); state = self._state(key)
        if not self.access_authorized or state.opened:
            raise LifecycleError("invalid_state_access")
        state.opened = True

    def open_edge(self, state_key: str, edge_key: str) -> None:
        self._active(); state, edge = self._edge(state_key, edge_key)
        if not self.access_authorized or not state.opened or edge.opened:
            raise LifecycleError("invalid_edge_access")
        edge.opened = True

    def fail(self, stage: str, exception: str, *, state_key: str | None = None, edge_key: str | None = None) -> None:
        self._active()
        if not stage or not exception:
            raise LifecycleError("missing_failure_evidence")
        if edge_key is not None:
            if state_key is None:
                raise LifecycleError("edge_failure_without_state")
            state, edge = self._edge(state_key, edge_key)
            if edge.phase == 2 or edge.failed:
                raise LifecycleError("invalid_edge_failure")
            edge.failed = True; state.failed = True
            self.active_state = state_key; self.active_edge = edge_key
        elif state_key is not None:
            state = self._state(state_key)
            if state.phase == 3 or state.failed:
                raise LifecycleError("invalid_state_failure")
            state.failed = True; self.active_state = state_key
        self.status = "failure"; self.stage = stage; self.exception = exception

    def block(self, stage: str, reason: str) -> None:
        self._active()
        if not stage or not reason:
            raise LifecycleError("missing_block_evidence")
        self.status = "blocked"; self.stage = stage; self.reason = reason

    def succeed(self) -> None:
        self._active(); candidate = self.snapshot(status_override="success")
        validate_snapshot(candidate)
        self.status = "success"; self.stage = "closure"; self.active_state = None; self.active_edge = None

    def _state(self, key: str) -> _State:
        try: return self._states[key]
        except KeyError as exc: raise LifecycleError("unknown_state") from exc

    def _edge(self, state_key: str, edge_key: str) -> tuple[_State, _Edge]:
        state = self._state(state_key)
        try: return state, state.edge_records[edge_key]
        except KeyError as exc: raise LifecycleError("unknown_edge") from exc

    def _counters(self) -> dict[str, int]:
        states = tuple(self._states.values()); edges = tuple(e for s in states for e in s.edge_records.values())
        return {
            "states_discovered": len(states), "states_prepared": sum(s.phase >= 1 for s in states),
            "states_evaluation_started": sum(s.phase >= 2 for s in states), "states_completed": sum(s.phase >= 3 for s in states),
            "edges_discovered": len(edges), "edges_evaluation_started": sum(e.phase >= 1 for e in edges),
            "edges_completed": sum(e.phase >= 2 for e in edges), "state_failures": sum(s.failed for s in states),
            "edge_failures": sum(e.failed for e in edges), "states_opened": sum(s.opened for s in states),
            "edges_opened": sum(e.opened for e in edges),
        }

    def snapshot(self, *, status_override: str | None = None) -> dict[str, Any]:
        counters = self._counters()
        integrity = {
            "orphan_edges": 0,
            "completed_states_with_incomplete_edges": sum(
                s.phase == 3 and any(e.phase != 2 for e in s.edge_records.values()) for s in self._states.values()),
            "failed_completed_states": sum(s.failed and s.phase == 3 for s in self._states.values()),
            "failed_completed_edges": sum(e.failed and e.phase == 2 for s in self._states.values() for e in s.edge_records.values()),
        }
        status = status_override or self.status
        stage = "closure" if status_override == "success" else self.stage
        return {"schema_version": 1, "status": status, "stage": stage, "reason": self.reason,
                "exception": self.exception, "access_authorized": self.access_authorized,
                "active_state": self.active_state, "active_edge": self.active_edge,
                "counters": counters, "integrity": integrity}


def validate_snapshot(value: Mapping[str, Any], *, terminal: bool = True) -> None:
    expected = {"schema_version", "status", "stage", "reason", "exception", "access_authorized",
                "active_state", "active_edge", "counters", "integrity"}
    if set(value) != expected or value["schema_version"] != 1:
        raise LifecycleError("snapshot_schema")
    _finite(value)
    status = value["status"]
    if terminal and status not in TERMINAL_STATUSES:
        raise LifecycleError("terminal_status")
    if not terminal and status not in (*TERMINAL_STATUSES, "active"):
        raise LifecycleError("status")
    if not isinstance(value["stage"], str) or not value["stage"]:
        raise LifecycleError("stage")
    counters = value["counters"]
    if set(counters) != set(COUNTER_KEYS) or any(type(counters[k]) is not int or counters[k] < 0 for k in COUNTER_KEYS):
        raise LifecycleError("counter_schema")
    if not (counters["states_completed"] <= counters["states_evaluation_started"] <= counters["states_prepared"] <= counters["states_discovered"]):
        raise LifecycleError("state_lifecycle_order")
    if not (counters["edges_completed"] <= counters["edges_evaluation_started"] <= counters["edges_discovered"]):
        raise LifecycleError("edge_lifecycle_order")
    if counters["state_failures"] > counters["states_discovered"] or counters["edge_failures"] > counters["edges_discovered"]:
        raise LifecycleError("failure_count")
    if counters["states_completed"] + counters["state_failures"] > counters["states_discovered"]:
        raise LifecycleError("state_terminal_count")
    if counters["edges_completed"] + counters["edge_failures"] > counters["edges_discovered"]:
        raise LifecycleError("edge_terminal_count")
    if counters["states_opened"] > counters["states_discovered"] or counters["edges_opened"] > counters["edges_discovered"]:
        raise LifecycleError("access_count")
    if (counters["states_opened"] or counters["edges_opened"]) and not value["access_authorized"]:
        raise LifecycleError("access_without_authority")
    if counters["edges_opened"] and not counters["states_opened"]:
        raise LifecycleError("edge_access_without_state")
    integrity = value["integrity"]
    if set(integrity) != set(INTEGRITY_KEYS) or any(type(integrity[k]) is not int or integrity[k] != 0 for k in INTEGRITY_KEYS):
        raise LifecycleError("parent_child_integrity")
    if value["active_edge"] is not None and value["active_state"] is None:
        raise LifecycleError("active_edge_without_state")
    complete = (counters["states_discovered"] > 0 and
                counters["states_completed"] == counters["states_discovered"] and
                counters["states_prepared"] == counters["states_discovered"] and
                counters["states_evaluation_started"] == counters["states_discovered"] and
                counters["edges_completed"] == counters["edges_discovered"] and
                counters["edges_evaluation_started"] == counters["edges_discovered"] and
                counters["state_failures"] == counters["edge_failures"] == 0)
    if status == "success":
        if not complete or value["exception"] is not None or value["reason"] is not None or value["active_state"] is not None or value["active_edge"] is not None:
            raise LifecycleError("incomplete_success")
    elif status == "failure":
        if not isinstance(value["exception"], str) or not value["exception"] or value["reason"] is not None:
            raise LifecycleError("failure_evidence")
        if complete and value["stage"] != "publication_validation":
            raise LifecycleError("failure_after_complete_wrong_stage")
    elif status == "blocked":
        if not isinstance(value["reason"], str) or not value["reason"] or value["exception"] is not None:
            raise LifecycleError("blocked_evidence")


def validate_cross_file(qc: Mapping[str, Any], manifest: Mapping[str, Any], evidence: Mapping[str, Any], report: Mapping[str, Any]) -> None:
    if set(qc) != {"schema_version", "status", "classification", "readiness", "real_access", "lifecycle", "lifecycle_sha256"}:
        raise LifecycleError("qc_schema")
    validate_snapshot(qc["lifecycle"])
    digest = snapshot_digest(qc["lifecycle"])
    if qc["lifecycle_sha256"] != digest:
        raise LifecycleError("qc_lifecycle_digest")
    if qc["status"] != qc["lifecycle"]["status"]:
        raise LifecycleError("qc_status_mismatch")
    if qc["real_access"] != {"states_opened": 0, "edges_opened": 0}:
        raise LifecycleError("real_access")
    for name, record in (("manifest", manifest), ("evidence", evidence), ("report", report)):
        if record.get("lifecycle_sha256") != digest or record.get("status") != qc["status"]:
            raise LifecycleError(name + "_lifecycle_mismatch")

