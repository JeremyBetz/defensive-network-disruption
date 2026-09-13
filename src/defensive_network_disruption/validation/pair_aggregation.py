"""Internal state-first aggregation for pair-derived representation summaries.

This module has no data, model, field, or execution routes.  Raw pair values are
reduced to one value per state before distribution summaries are calculated.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from collections.abc import Iterable, Mapping, Sequence


QUANTILES = (0.05, 0.25, 0.50, 0.75, 0.95)
SUMMARY_KEYS = ("mean", "minimum", "maximum", "q05", "q25", "q50", "q75", "q95")
PAIR_UNITS = frozenset(("state_pair_mean", "state_pair_proportion"))


@dataclass(frozen=True)
class StatePairRecord:
    """Raw eligible pair values for one state and one scalar family."""

    match: str
    state: str
    values: tuple[float, ...]

    def __post_init__(self) -> None:
        if not self.match or not self.state:
            raise ValueError("state_pair_key")
        if not all(math.isfinite(value) for value in self.values):
            raise ValueError("nonfinite_pair_value")


@dataclass(frozen=True)
class StateSummary:
    """One state-equal scalar derived from eligible raw pairs."""

    match: str
    state: str
    value: float
    source_observations: int
    unit: str

    def __post_init__(self) -> None:
        if self.unit not in PAIR_UNITS:
            raise ValueError("unsupported_pair_unit")
        if not math.isfinite(self.value) or self.source_observations < 1:
            raise ValueError("invalid_state_summary")


def _mean(values: Sequence[float]) -> float:
    return math.fsum(values) / len(values)


def reduce_pairs_within_state(
    records: Iterable[StatePairRecord], *, unit: str = "state_pair_mean",
) -> tuple[StateSummary, ...]:
    """Return one arithmetic mean per state; empty states remain unavailable."""
    if unit not in PAIR_UNITS:
        raise ValueError("unsupported_pair_unit")
    output: list[StateSummary] = []
    keys: set[tuple[str, str]] = set()
    for record in records:
        if not isinstance(record, StatePairRecord):
            raise TypeError("records must contain StatePairRecord")
        key = (record.match, record.state)
        if key in keys:
            raise ValueError("duplicate_state_key")
        keys.add(key)
        if record.values:
            output.append(StateSummary(record.match, record.state, _mean(record.values),
                                       len(record.values), unit))
    return tuple(output)


def reduce_categories_within_state(
    records: Iterable[tuple[str, str, Sequence[str]]], categories: Sequence[str],
) -> Mapping[str, tuple[StateSummary, ...]]:
    """Convert exclusive raw categories to one proportion per state/category."""
    names = tuple(categories)
    if not names or len(set(names)) != len(names) or any(not name for name in names):
        raise ValueError("invalid_categories")
    staged: dict[str, list[StatePairRecord]] = {name: [] for name in names}
    seen: set[tuple[str, str]] = set()
    for match, state, observations in records:
        key = (match, state)
        if key in seen:
            raise ValueError("duplicate_state_key")
        seen.add(key)
        values = tuple(observations)
        if any(value not in staged for value in values):
            raise ValueError("unknown_category")
        for name in names:
            staged[name].append(StatePairRecord(match, state,
                tuple(float(value == name) for value in values)))
    return {name: reduce_pairs_within_state(rows, unit="state_pair_proportion")
            for name, rows in staged.items()}


def inverse_ecdf_summary(values: Sequence[float], weights: Sequence[float]) -> dict[str, float | None]:
    """Summarize finite values with the frozen first-cumulative-weight quantiles."""
    if len(values) != len(weights):
        raise ValueError("summary_alignment")
    if not values:
        return {key: None for key in SUMMARY_KEYS}
    pairs = [(float(value), float(weight), index)
             for index, (value, weight) in enumerate(zip(values, weights))]
    if not all(math.isfinite(value) and math.isfinite(weight) and weight > 0
               for value, weight, _ in pairs):
        raise ValueError("invalid_summary_values")
    pairs.sort(key=lambda item: (item[0], item[2]))
    total = math.fsum(weight for _, weight, _ in pairs)
    quantile_values: list[float] = []
    for quantile in QUANTILES:
        cumulative = 0.0
        selected = pairs[-1][0]
        for value, weight, _ in pairs:
            cumulative = math.fsum((cumulative, weight))
            if cumulative / total >= quantile:
                selected = value
                break
        quantile_values.append(selected)
    return {
        "mean": math.fsum(value * weight for value, weight, _ in pairs) / total,
        "minimum": pairs[0][0], "maximum": pairs[-1][0],
        **dict(zip(("q05", "q25", "q50", "q75", "q95"), quantile_values)),
    }


def aggregate_states(
    discovered: Iterable[tuple[str, str]], summaries: Iterable[StateSummary],
) -> tuple[dict[str, object], ...]:
    """Create match rows and one equal-match macro row from state summaries."""
    all_states = tuple(discovered)
    if len(set(all_states)) != len(all_states):
        raise ValueError("duplicate_discovered_state")
    rows = tuple(summaries)
    keys = [(row.match, row.state) for row in rows]
    if len(set(keys)) != len(keys) or any(key not in all_states for key in keys):
        raise ValueError("summary_state_membership")
    units = {row.unit for row in rows}
    if len(units) > 1:
        raise ValueError("mixed_summary_units")
    aliases = tuple(dict.fromkeys(match for match, _ in all_states))
    output: list[dict[str, object]] = []
    for group in (*aliases, "macro"):
        selected_states = all_states if group == "macro" else tuple(x for x in all_states if x[0] == group)
        selected = rows if group == "macro" else tuple(row for row in rows if row.match == group)
        counts = {alias: sum(row.match == alias for row in selected) for alias in aliases}
        represented = tuple(alias for alias in aliases if counts[alias])
        weights = ([1.0 / counts[row.match] / len(represented) for row in selected]
                   if group == "macro" and represented else [1.0] * len(selected))
        stats = inverse_ecdf_summary([row.value for row in selected], weights)
        output.append({
            "alias": group,
            "unit": (next(iter(units)) if units else "state_pair_mean"),
            "aggregation_unit": "macro_match" if group == "macro" else "match",
            "represented_matches": len(represented) if group == "macro" else int(bool(selected)),
            "states_total": len(selected_states), "states_assessable": len(selected),
            "states_unavailable": len(selected_states) - len(selected),
            "observations": len(selected),
            "source_observations": sum(row.source_observations for row in selected),
            "unavailable_reason": ("no_states" if not selected_states else
                                   "no_eligible_pairs" if len(selected) < len(selected_states) else "none"),
            **stats,
        })
    return tuple(output)


def aggregate_pair_family(
    records: Iterable[StatePairRecord], *, unit: str = "state_pair_mean",
) -> tuple[dict[str, object], ...]:
    """Convenience path from raw pair records through state-first aggregation."""
    source = tuple(records)
    discovered = tuple((row.match, row.state) for row in source)
    return aggregate_states(discovered, reduce_pairs_within_state(source, unit=unit))
