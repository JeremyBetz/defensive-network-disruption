"""Synthetic-only observation of the frozen Session 14g engineering path."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import itertools
from pathlib import Path
import traceback
from typing import Callable

import numpy as np

from . import production_verification as production
from .verification_repair import find_verified_envelope, mapped_signature


FIXTURE_ORDER = (
    "constant",
    "crossing",
    "three_constants",
    "rounded_plateau",
    "exact_plateau",
    "multiway_plateau",
)


@dataclass
class ActiveDiagnostic:
    check_index: int = 0
    fixture: str | None = None
    candidate_family: str = "engineering_oracle"
    check_category: str = "envelope_contract"
    stage: str = "fixture_load"
    substage: str = "engineering_functions"
    function: str = "engineering_functions"
    input_summary: dict | None = None
    completed_checks: int = 0


@dataclass(frozen=True)
class DiagnosticFailure:
    exception_class: str
    exception_message: str
    full_traceback: str
    active: dict
    completed_rows: tuple[dict, ...]


def type_summary(value) -> dict:
    """Return bounded structural information without retaining values."""
    result = {"python_type": type(value).__name__, "is_scalar": bool(np.isscalar(value))}
    if isinstance(value, np.ndarray):
        result.update(
            dtype=str(value.dtype),
            shape=list(value.shape),
            ndim=value.ndim,
            finite=bool(np.isfinite(value).all()) if np.issubdtype(value.dtype, np.number) else None,
        )
    elif isinstance(value, (tuple, list, dict, set)):
        result["length"] = len(value)
    return result


def _activate(active: ActiveDiagnostic, stage: str, substage: str, function: str,
              value=None) -> None:
    active.stage = stage
    active.substage = substage
    active.function = function
    active.input_summary = None if value is None else type_summary(value)


def _observed_function(function: Callable, active: ActiveDiagnostic,
                       parent_stage: Callable[[], tuple[str, str, str]]):
    def observed(value):
        previous = (active.stage, active.substage, active.function, active.input_summary)
        stage, substage, name = parent_stage()
        _activate(active, "field_evaluation", f"{stage}:{substage}", name, value)
        try:
            result = function(value)
        except Exception:
            # Preserve the most specific active operation for the failure record.
            raise
        else:
            active.stage, active.substage, active.function, active.input_summary = previous
            return result
    return observed


def capture_failure(error: BaseException, active: ActiveDiagnostic,
                    completed_rows: list[dict]) -> DiagnosticFailure:
    return DiagnosticFailure(
        exception_class=type(error).__name__,
        exception_message=str(error),
        full_traceback="".join(traceback.format_exception(type(error), error, error.__traceback__)),
        active=asdict(active),
        completed_rows=tuple(completed_rows),
    )


def run_engineering_diagnostic(persist: Callable[[dict], None]) -> tuple[list[dict], DiagnosticFailure | None]:
    """Reproduce the frozen engineering body and stop at its first exception."""
    active = ActiveDiagnostic()
    rows: list[dict] = []
    try:
        _activate(active, "fixture_load", "engineering_functions", "engineering_functions")
        functions = production.engineering_functions()
        if tuple(functions) != FIXTURE_ORDER:
            raise ValueError("engineering_fixture_order_changed")
        for index, (name, raw_function) in enumerate(functions.items(), start=1):
            active.check_index = index
            active.fixture = name
            active.completed_checks = len(rows)
            parent = ["switch_detection", "initial_envelope", "find_verified_envelope"]
            function = _observed_function(raw_function, active, lambda: tuple(parent))

            _activate(active, *parent)
            result = find_verified_envelope(function)

            parent[:] = ["enclosure_validation", "certified_partitions_combined",
                          "certified_partitions"]
            _activate(active, *parent, result)
            partitions = production.certified_partitions(function, result)

            parent[:] = ["input_shape_probe", "fixture_midpoint", "fixture_function"]
            probe = np.array([0.5], dtype=np.float64)
            _activate(active, *parent, probe)
            count = function(probe).shape[1]
            identity = tuple(range(count))

            parent[:] = ["signature_construction", "baseline_signature", "mapped_signature"]
            _activate(active, *parent, result)
            signature = mapped_signature(result, identity)
            comparisons = 0
            enclosures = [
                [boundary.outside, boundary.inside]
                for tie in result.tie_intervals
                for boundary in (tie.start, tie.end)
                if boundary is not None
            ]
            for permutation in itertools.permutations(identity):
                if permutation == identity:
                    other = result
                else:
                    parent[:] = ["permutation_switch_detection", "permuted_envelope",
                                  "find_verified_envelope"]
                    _activate(active, *parent, permutation)
                    other = find_verified_envelope(
                        lambda values, selected=permutation: function(values)[:, selected]
                    )
                parent[:] = ["permutation_signature_comparison", "mapped_signature",
                              "mapped_signature"]
                _activate(active, *parent, other)
                observed = mapped_signature(other, permutation)
                if signature != observed:
                    row = {
                        "fixture": name,
                        "passed": False,
                        "reason": "mapped_record_mismatch",
                        "permutations_checked": comparisons + 1,
                        "partition_count": len(partitions),
                        "boundary_enclosures": enclosures,
                        "different_sections": [
                            label
                            for label, before, after in zip(
                                ("switches", "tie_intervals", "maximizing_defenders",
                                 "partitions", "grid"),
                                signature,
                                observed,
                                strict=True,
                            )
                            if before != after
                        ],
                    }
                    _activate(active, "progress_persistence", "completed_fixture",
                              "persist", row)
                    persist(row)
                    rows.append(row)
                    active.completed_checks = len(rows)
                    return rows, None
                comparisons += 1
            row = {
                "fixture": name,
                "passed": True,
                "reason": None,
                "permutations_checked": comparisons,
                "partition_count": len(partitions),
                "boundary_enclosures": enclosures,
                "different_sections": [],
            }
            _activate(active, "progress_persistence", "completed_fixture", "persist", row)
            persist(row)
            rows.append(row)
            active.completed_checks = len(rows)
        return rows, None
    except Exception as error:
        return rows, capture_failure(error, active, rows)


def sanitize_traceback(full_traceback: str, repository: Path) -> tuple[str, list[dict]]:
    """Remove absolute prefixes and retain bounded traceback-frame identity."""
    repository = repository.resolve()
    text = full_traceback.replace(str(repository), "<REPOSITORY>")
    home = Path.home().resolve()
    text = text.replace(str(home), "<HOME>")
    frames = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("File "):
            continue
        # traceback lines are stable: File "path", line N, in function
        parts = stripped.split(", ")
        path = parts[0].removeprefix("File ").strip('"')
        line_number = int(parts[1].removeprefix("line "))
        function = parts[2].removeprefix("in ") if len(parts) > 2 else "<module>"
        frames.append({"file": path, "line": line_number, "function": function})
    return text, frames
