"""Session 14aq retained-evidence reviewer with explicit per-level data flow."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
from typing import Any, Mapping, Sequence

_HISTORICAL_PATH = Path(__file__).with_name("terminal_error_review.py")
_HISTORICAL_SPEC = importlib.util.spec_from_file_location(
    "session14aq_historical_terminal_error_review", _HISTORICAL_PATH
)
historical = importlib.util.module_from_spec(_HISTORICAL_SPEC)
assert _HISTORICAL_SPEC.loader is not None
_HISTORICAL_SPEC.loader.exec_module(historical)

LEVEL_FIELDS = historical.LEVEL_FIELDS
ERROR_FIELDS = historical.ERROR_FIELDS
LEVEL_NUMBERS = historical.LEVEL_NUMBERS
TOLERANCES = historical.TOLERANCES
PUBLIC_FILES = (
    "level_summary.csv",
    "terminal_subdivision_summary.json",
    "error_contribution_summary.csv",
    "warning_semantics.json",
    "missing_evidence.json",
    "publication_validation.json",
    "qc.json",
)

canonical = historical.canonical
digest = historical.digest
sha = historical.sha
strict_load = historical.strict_load
atomic = historical.atomic
csv_bytes = historical.csv_bytes
selected_names = historical.selected_names


def reviewed_level_row(retained_level: Mapping[str, Any], reduced_row: Mapping[str, Any]) -> dict[str, Any]:
    """Bind a public row directly to its own validated retained level."""
    if "tolerance" not in retained_level:
        raise ValueError("missing_retained_tolerance")
    row = dict(reduced_row)
    row["tolerance"] = retained_level["tolerance"]
    return row


def review_records(reference: Mapping[str, Any], onsets: Mapping[str, Any],
                   levels: Sequence[Mapping[str, Any]],
                   pieces_by_level: Sequence[Sequence[Mapping[str, Any]]],
                   evidence_hashes: Sequence[str]) -> dict[str, Any]:
    """Reuse historical reductions, repairing only explicit tolerance provenance."""
    if len(levels) != len(TOLERANCES):
        raise ValueError("level_count")
    for retained, frozen in zip(levels, TOLERANCES):
        if retained.get("tolerance") != frozen:
            raise ValueError("retained_tolerance")
    reduced = deepcopy(historical.review_records(
        reference, onsets, levels, pieces_by_level, evidence_hashes
    ))
    reduced["level_rows"] = [
        reviewed_level_row(retained, row)
        for retained, row in zip(levels, reduced["level_rows"])
    ]
    return reduced


def public_package(review: Mapping[str, Any], source_match: bool,
                   source_sha256: str) -> dict[str, Any]:
    package = historical.public_package(review, source_match, source_sha256)
    return package
