"""Frozen Session 14R8 aggregation-family registry and state-first adapter."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

from .pair_aggregation import PAIR_UNITS


PAIR_PROPORTION_METRICS = frozenset({
    "raw_order_disagreement", "endpoint_following", "corridor_following", "tied",
    "agreement", "strict_reversal", "tie_creation", "tie_removal", "both_tied",
})
PAIR_MEAN_METRICS = frozenset({"paired_difference"})
PUBLIC_UNITS = frozenset({"edge", "state", "match", *PAIR_UNITS})


@dataclass(frozen=True)
class FamilySpec:
    file: str
    candidate: str
    comparison: str
    summary: str
    combination: str
    metric: str
    unit: str

    def __post_init__(self) -> None:
        if self.unit not in PUBLIC_UNITS:
            raise ValueError("unsupported_public_unit")
        expected = unit_for(self.metric, self.unit)
        if expected != self.unit:
            raise ValueError("family_unit_mismatch")


def unit_for(metric: str, requested: str) -> str:
    """Return the only permitted public unit for a collected family."""
    if metric in PAIR_MEAN_METRICS:
        if requested not in {"edge", "pair", "state_pair_mean"}:
            raise ValueError("paired_mean_source_unit")
        return "state_pair_mean"
    if metric in PAIR_PROPORTION_METRICS:
        if requested not in {"pair", "state_pair_proportion"}:
            raise ValueError("pair_proportion_source_unit")
        return "state_pair_proportion"
    if requested in PAIR_UNITS or requested == "pair":
        raise ValueError("unregistered_pair_family")
    if requested not in PUBLIC_UNITS:
        raise ValueError("unsupported_public_unit")
    return requested


def state_first(values: Iterable[float], unit: str) -> tuple[float, ...]:
    """Reduce pair-derived observations to one state value; keep empty unavailable."""
    items = tuple(float(value) for value in values)
    if not all(math.isfinite(value) for value in items):
        raise ValueError("nonfinite_metric")
    if unit in PAIR_UNITS:
        return () if not items else (math.fsum(items) / len(items),)
    return items


def registry_record(spec: FamilySpec) -> dict[str, str]:
    return {
        "file": spec.file, "candidate": spec.candidate,
        "comparison": spec.comparison, "summary": spec.summary,
        "combination": spec.combination, "metric": spec.metric, "unit": spec.unit,
    }


__all__ = [
    "FamilySpec", "PAIR_MEAN_METRICS", "PAIR_PROPORTION_METRICS",
    "PUBLIC_UNITS", "registry_record", "state_first", "unit_for",
]
