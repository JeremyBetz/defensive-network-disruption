"""Small single-pass lifecycle authority for the R9AB acquisition."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from .r5_persistence import Journal, LifecycleError, canonical_bytes, digest

EVENTS = ("lineage_review", "access_attempt", "materialization",
          "authority_persistence", "structural_validation", "terminal_success",
          "terminal_failure")
_SEAL = object()


@dataclass(frozen=True)
class Authority:
    _bytes: bytes
    _seal: object
    def __post_init__(self):
        if self._seal is not _SEAL:
            raise TypeError("verified_stream_required")
    def record(self):
        return json.loads(self._bytes)


class _State:
    def __init__(self):
        self.stage = 0; self.terminal = False; self.failure = None
        self.exposure = {"states_reopened": 0, "edges_reopened": 0,
                         "new_population_states": 0, "new_population_edges": 0,
                         "exposure_uncertain": False}
    def step(self, action, payload):
        if action not in EVENTS or self.terminal:
            raise LifecycleError("acquisition_event")
        if action == "terminal_failure":
            if set(payload) != {"stage", "exception", "traceback_sha256"}:
                raise LifecycleError("failure_schema")
            if len(payload["traceback_sha256"]) != 64:
                raise LifecycleError("traceback_hash")
            self.failure = payload; self.terminal = True; return
        expected = EVENTS[self.stage]
        if action != expected:
            raise LifecycleError("acquisition_order")
        if action == "lineage_review" and not payload.get("valid"):
            raise LifecycleError("lineage_invalid")
        if action == "access_attempt":
            self.exposure["exposure_uncertain"] = True
        elif action == "materialization":
            if payload != {"previously_exposed_states": 1, "previously_exposed_edges": 1,
                           "new_population_states": 0, "new_population_edges": 0}:
                raise LifecycleError("materialization_schema")
            self.exposure.update(states_reopened=1, edges_reopened=1,
                                 exposure_uncertain=False)
        elif action in ("authority_persistence", "structural_validation"):
            if not payload.get("valid"):
                raise LifecycleError("authority_invalid")
        elif action == "terminal_success":
            if payload or self.stage != 5:
                raise LifecycleError("terminal_success")
            self.terminal = True; self.stage += 1; return
        self.stage += 1
    def result(self):
        if not self.terminal:
            raise LifecycleError("unterminated_acquisition")
        return {"schema_version": 1, "status": "failure" if self.failure else "success",
                "stage_index": self.stage, "exposure": self.exposure,
                "failure": self.failure,
                "candidate_evaluations": 0, "field_evaluations": 0,
                "refinements": 0, "maximality_classifications": 0}


def review(path, *, expected_head=None):
    state = _State(); previous = None; raw = hashlib.sha256(); count = 0
    with Path(path).open("rb") as handle:
        for line in handle:
            raw.update(line)
            if not line.endswith(b"\n"):
                raise LifecycleError("interrupted_journal_write")
            record = json.loads(line)
            if canonical_bytes(record) != line or set(record) != {
                    "schema_version", "sequence", "previous", "action", "payload"}:
                raise LifecycleError("journal_encoding")
            if record["schema_version"] != 1 or record["sequence"] != count or record["previous"] != previous:
                raise LifecycleError("journal_chain")
            previous = digest(record); count += 1
            state.step(record["action"], record["payload"])
    if expected_head is not None and previous != expected_head:
        raise LifecycleError("journal_head")
    result = {**state.result(), "records": count, "journal_head_sha256": previous,
              "journal_file_sha256": raw.hexdigest()}
    return Authority(canonical_bytes(result), _SEAL)


__all__ = ["Authority", "Journal", "review"]
