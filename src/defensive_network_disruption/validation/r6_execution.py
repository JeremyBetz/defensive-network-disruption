"""Session 14R6 adapter over accepted launch and projection-exposure authorities."""
from __future__ import annotations

import copy
import json
import traceback
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .projection_exposure import progress_view, replay_exposure
from .r5_persistence import (
    CANDIDATES,
    Journal,
    Launch,
    LifecycleError,
    durable_write,
    read_journal,
)
from .launch_enforcement import sha256_file


class _CoreView:
    def __init__(self, progress: "Progress") -> None:
        self._progress = progress

    def snapshot(self) -> dict[str, Any]:
        records, _ = read_journal(self._progress.journal.path)
        return replay_exposure(records)


class Progress:
    """R6 façade whose state is derived entirely from the durable journal."""

    def __init__(self, journal: Journal):
        self.journal = journal
        self.context: tuple[str, str, str] | None = None
        self.before_success: Mapping[str, Any] | None = None
        self._states: dict[str, dict[str, Any]] = {}
        self._attempts: dict[str, str] = {}
        self._fields: set[tuple[str, str, str]] = set()
        self.core = _CoreView(self)
        self.journal.append("initialized")

    def _append(self, action: str, **payload: Any) -> None:
        self.journal.append(action, **payload)

    def transition(self, action: str, *args: Any, **kwargs: Any) -> None:
        if kwargs:
            raise LifecycleError("r6_transition_keywords")
        routes: dict[str, Callable[..., None]] = {
            "authorize_access": self.authorize_access,
            "discover_state": self.discover_state,
            "prepare_state": self.prepare_state,
            "start_state_evaluation": self.start_state,
            "complete_state": self.complete_state,
            "succeed": self.succeed,
        }
        if action not in routes:
            raise LifecycleError("r6_transition_route")
        routes[action](*args)

    def authorize_access(self) -> None:
        self._append("access_authorized")

    def discover_state(self, state: str, edges: Sequence[str]) -> None:
        edge_tuple = tuple(edges)
        if state in self._states or not edge_tuple or len(set(edge_tuple)) != len(edge_tuple):
            raise LifecycleError("state_registration")
        self._states[state] = {"edges": edge_tuple, "opened": set(), "prepared": False,
                               "started": False, "completed": set(), "done": False}
        self._append("state_discovered", state=state, edges=list(edges))

    def begin_projection(self, state: str) -> str:
        attempt = f"projection_{self.journal.count:09d}"
        if state not in self._states or state in self._attempts.values():
            raise LifecycleError("projection_state")
        self._attempts[attempt] = state
        self._append("projection_attempt", attempt=attempt, state=state)
        return attempt

    def project(self, state: str, callback: Callable[[], Any]) -> Any:
        attempt = self.begin_projection(state)
        try:
            result = callback()
        except BaseException:
            self._append("projection_not_materialized", attempt=attempt)
            del self._attempts[attempt]
            raise
        edges = self._states[state]["edges"]
        self._append("projection_materialized", attempt=attempt, edges=list(edges))
        self._states[state]["opened"].update(edges);del self._attempts[attempt]
        return result

    def prepare_state(self, state: str) -> None:
        item=self._states[state]
        if item["opened"] != set(item["edges"]):raise LifecycleError("prepare_without_projection")
        item["prepared"]=True
        self._append("state_prepared", state=state)

    def start_state(self, state: str) -> None:
        item=self._states[state]
        if not item["prepared"] or item["started"]:raise LifecycleError("state_start")
        item["started"]=True
        self._append("state_evaluation_started", state=state)

    def call_start(self, state: str, edge: str, candidate: str) -> None:
        if self.context is not None:
            raise LifecycleError("candidate_context")
        item=self._states[state];key=(state,edge,candidate)
        if not item["started"] or edge not in item["opened"] or key in self._fields:
            raise LifecycleError("field_context")
        index=CANDIDATES.index(candidate)
        if index and (state,edge,CANDIDATES[index-1]) not in self._fields:
            raise LifecycleError("field_order")
        self._append("field_started", state=state, edge=edge, candidate=candidate)
        self.context = (state, edge, candidate)

    def call_complete(self) -> None:
        if self.context is None:
            raise LifecycleError("call_not_started")
        state, edge, candidate = self.context
        self._append("field_completed", state=state, edge=edge, candidate=candidate)
        self._fields.add((state,edge,candidate))
        self.context = None
        if candidate == CANDIDATES[-1]:
            self._append("edge_completed", state=state, edge=edge)
            self._states[state]["completed"].add(edge)

    def complete_state(self, state: str) -> None:
        item=self._states[state]
        if item["completed"] != set(item["edges"]):raise LifecycleError("invalid_state_completion")
        item["done"]=True
        self._append("state_completed", state=state)

    def succeed(self) -> None:
        if self._attempts or not self._states or not all(x["done"] for x in self._states.values()):
            raise LifecycleError("incomplete_success")
        self.before_success = copy.deepcopy(self.core.snapshot())
        self._append("success")

    def failure(self, stage: str, error: BaseException) -> dict[str, Any]:
        before = self.core.snapshot()
        state = before["active"]["state"]
        edge = before["active"]["edge"]
        candidate = before["active"]["candidate"]
        self._append(
            "failure",
            stage=stage,
            exception=type(error).__name__,
            state=state,
            edge=edge,
            candidate=candidate,
        )
        return {
            "pre_failure": before,
            "terminal": self.core.snapshot(),
            "context": self.context,
            "stage": stage,
            "exception": type(error).__name__,
            "traceback": traceback.format_exc(),
        }


def view(path: Path, snapshot: Mapping[str, Any] | None, mode: str, *,
         expected_head: str | None, initialized: bool = True) -> dict[str, Any]:
    if not initialized:
        records, head = read_journal(path, expected_head=expected_head)
        if records:
            raise LifecycleError("forged_preinitialization")
        return {
            "schema_version": 1,
            "mode": "pre_access",
            "journal_sha256": head,
            "snapshot_sha256": None,
            "snapshot": None,
        }
    result = progress_view(path, expected_head=expected_head, mode=mode)
    if snapshot != result["snapshot"]:
        raise LifecycleError("lifecycle_journal_mismatch")
    return result


def exposure_summary(path: Path, *, expected_head: str) -> dict[str, Any]:
    records, head = read_journal(path, expected_head=expected_head)
    snapshot = replay_exposure(records)
    attempts: dict[str, str] = {}
    materialized_states: set[str] = set()
    for record in records:
        payload = record["payload"]
        if record["action"] == "projection_attempt":
            attempts[payload["attempt"]] = payload["state"]
        elif record["action"] == "projection_materialized":
            materialized_states.add(attempts[payload["attempt"]])
    return {
        "schema_version": 1,
        "journal_sha256": head,
        "states_opened": len(materialized_states),
        "edges_opened": snapshot["counters"]["edges_opened"],
        "unresolved_projection_attempts": snapshot["counters"]["unresolved_projection_attempts"],
        "unresolved_exposed_edges": snapshot["counters"]["unresolved_exposed_edges"],
        "field_evaluations_started": snapshot["counters"]["field_evaluations_started"],
        "field_evaluations_completed": snapshot["counters"]["field_evaluations_completed"],
        "field_work_by_candidate": snapshot["field_work_by_candidate"],
    }


def validate_persisted(directory: Path, journal: Path) -> dict[str, Any]:
    directory = Path(directory)
    loaded = {
        name: json.loads((directory / name).read_text())
        for name in ("qc.json", "manifest.json", "lifecycle_summary.json", "evidence.json")
    }
    authority = loaded["lifecycle_summary.json"]
    actual = view(
        journal,
        authority["snapshot"],
        authority["mode"],
        expected_head=authority["journal_sha256"],
        initialized=authority["snapshot"] is not None,
    )
    if authority != actual:
        raise LifecycleError("lifecycle_summary_mismatch")
    for name in ("qc.json", "manifest.json", "evidence.json"):
        record = loaded[name]
        if record.get("schema_version") != 1 or record.get("progress_authority") != actual:
            raise LifecycleError("cross_file_" + name)
    for name, expected in loaded["manifest.json"]["outputs"].items():
        if Path(name).name != name or sha256_file(directory / name) != expected:
            raise LifecycleError("persisted_hash_mismatch")
    return actual


__all__ = [
    "Journal",
    "Launch",
    "Progress",
    "durable_write",
    "exposure_summary",
    "read_journal",
    "validate_persisted",
    "view",
]
