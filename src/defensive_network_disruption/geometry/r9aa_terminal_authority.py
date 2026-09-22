"""Version-2 terminal-cell authority with independent tied functions.

This internal module is synthetic-only.  It has no geometry loader, empirical
identifier, field callback, localization route, or acquisition entrypoint.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F
from typing import Mapping

from . import r9x_terminal_authority as v1
from .r9j_reference import Bounds

SCHEMA_VERSION = 2
SERIALIZATION = "canonical-json-v2"
TIE_SCHEMA_VERSION = 1
RELATIONS = frozenset(("symbolic_identity", "common_inactive_branch",
                       "tolerance_certified"))


@dataclass(frozen=True)
class LoadedTerminalAuthority:
    source_version: int
    cell: Mapping[str, object]
    pair: tuple[v1.Coefficients, v1.Coefficients]
    competitors: tuple[v1.Coefficients, ...]
    relation_type: str
    tie_authority: Mapping[str, object] | None
    record: Mapping[str, object]


def _hash(value: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(
            item not in "0123456789abcdef" for item in value):
        raise ValueError("authority_hash")
    return value


def create_tie_authority(*, relation_type: str,
                         pair_left_ref: str, pair_right_ref: str,
                         tolerance_authority_sha256: str,
                         structural_tie_lineage_sha256: str,
                         boundary_authority_sha256: str,
                         interval_authority_sha256: str) -> dict:
    left, right = _hash(pair_left_ref), _hash(pair_right_ref)
    if relation_type not in RELATIONS:
        raise ValueError("tie_relation")
    if relation_type == "symbolic_identity":
        if left != right:
            raise ValueError("symbolic_identity_refs")
    elif left == right:
        raise ValueError("distinct_relation_refs")
    base = {
        "schema_version": TIE_SCHEMA_VERSION,
        "scope": "cell_interval",
        "relation_type": relation_type,
        "pair_left_ref": left,
        "pair_right_ref": right,
        "tolerance_authority_sha256": _hash(tolerance_authority_sha256),
        "structural_tie_lineage_sha256": _hash(structural_tie_lineage_sha256),
        "boundary_authority_sha256": _hash(boundary_authority_sha256),
        "interval_authority_sha256": _hash(interval_authority_sha256),
    }
    return {**base, "provenance_sha256": v1.digest(base)}


def create_authority_v2(*, ordinal: int, depth: int, left: F, right: F,
                        pair: tuple[v1.Coefficients, v1.Coefficients],
                        competitors: tuple[v1.Coefficients, ...], source: dict,
                        relation_type: str, tolerance_authority_sha256: str,
                        structural_tie_lineage_sha256: str,
                        boundary_authority_sha256: str,
                        interval_authority_sha256: str) -> dict:
    if type(ordinal) is not int or ordinal < 0 or type(depth) is not int or depth < 0:
        raise ValueError("cell_identity")
    left, right = F(left), F(right)
    if not F(0) <= left < right <= F(1):
        raise ValueError("cell_bounds")
    if not isinstance(pair, tuple) or len(pair) != 2 or not all(
            isinstance(item, v1.Coefficients) for item in pair):
        raise ValueError("pair_schema")
    if not isinstance(competitors, tuple) or not competitors or not all(
            isinstance(item, v1.Coefficients) for item in competitors):
        raise ValueError("competitors_required")
    if set(source) != set(v1.SOURCE_KEYS):
        raise ValueError("source_schema")
    source = {key: _hash(source[key]) for key in v1.SOURCE_KEYS}
    coefficients = {item.authority_sha256: item for item in (*pair, *competitors)}
    ordered = [coefficients[key].record() for key in sorted(coefficients)]
    left_ref, right_ref = (item.authority_sha256 for item in pair)
    tie = create_tie_authority(
        relation_type=relation_type, pair_left_ref=left_ref,
        pair_right_ref=right_ref,
        tolerance_authority_sha256=tolerance_authority_sha256,
        structural_tie_lineage_sha256=structural_tie_lineage_sha256,
        boundary_authority_sha256=boundary_authority_sha256,
        interval_authority_sha256=interval_authority_sha256)
    base = {
        "schema_version": SCHEMA_VERSION,
        "serialization": SERIALIZATION,
        "candidate": "constant_width",
        "formula_authority_sha256": v1.FORMULA_SHA256,
        "cell": {"ordinal": ordinal, "depth": depth,
                 "left": v1.fraction_record(left), "right": v1.fraction_record(right)},
        "coefficients": ordered,
        "pair_left_ref": left_ref,
        "pair_right_ref": right_ref,
        "competitors": sorted({item.authority_sha256 for item in competitors}),
        "tie_authority": tie,
        "source_authority": source,
    }
    return {**base, "provenance_sha256": v1.digest(base)}


def _load_v2(value: Mapping[str, object]) -> LoadedTerminalAuthority:
    required = {"schema_version", "serialization", "candidate",
                "formula_authority_sha256", "cell", "coefficients",
                "pair_left_ref", "pair_right_ref", "competitors",
                "tie_authority", "source_authority", "provenance_sha256"}
    if not isinstance(value, Mapping) or set(value) != required:
        raise ValueError("terminal_authority_schema")
    if value["schema_version"] != SCHEMA_VERSION or value["serialization"] != SERIALIZATION:
        raise ValueError("terminal_authority_version")
    if value["candidate"] != "constant_width" or value["formula_authority_sha256"] != v1.FORMULA_SHA256:
        raise ValueError("terminal_formula_authority")
    cell = value["cell"]
    if not isinstance(cell, Mapping) or set(cell) != {"ordinal", "depth", "left", "right"}:
        raise ValueError("terminal_cell_schema")
    if type(cell["ordinal"]) is not int or cell["ordinal"] < 0 or type(cell["depth"]) is not int or cell["depth"] < 0:
        raise ValueError("terminal_cell_values")
    left, right = v1.parse_fraction(cell["left"]), v1.parse_fraction(cell["right"])
    if not F(0) <= left < right <= F(1):
        raise ValueError("terminal_cell_values")
    if not isinstance(value["source_authority"], Mapping) or set(value["source_authority"]) != set(v1.SOURCE_KEYS):
        raise ValueError("terminal_source_schema")
    for item in value["source_authority"].values():
        _hash(item)
    records = value["coefficients"]
    if not isinstance(records, list) or not records:
        raise ValueError("terminal_coefficients")
    parsed = [v1.Coefficients.from_record(item) for item in records]
    lookup = {item.authority_sha256: item for item in parsed}
    if len(lookup) != len(parsed) or list(lookup) != sorted(lookup):
        raise ValueError("terminal_coefficient_order")
    left_ref, right_ref = _hash(value["pair_left_ref"]), _hash(value["pair_right_ref"])
    competitors = value["competitors"]
    if not isinstance(competitors, list) or not competitors or competitors != sorted(set(competitors)):
        raise ValueError("terminal_competitor_schema")
    try:
        pair = (lookup[left_ref], lookup[right_ref])
        competitor_values = tuple(lookup[_hash(item)] for item in competitors)
    except KeyError as error:
        raise ValueError("terminal_coefficient_reference") from error
    tie = value["tie_authority"]
    if not isinstance(tie, Mapping):
        raise ValueError("tie_authority_schema")
    tie_required = {"schema_version", "scope", "relation_type", "pair_left_ref",
                    "pair_right_ref", "tolerance_authority_sha256",
                    "structural_tie_lineage_sha256", "boundary_authority_sha256",
                    "interval_authority_sha256", "provenance_sha256"}
    if set(tie) != tie_required or tie["schema_version"] != TIE_SCHEMA_VERSION or tie["scope"] != "cell_interval":
        raise ValueError("tie_authority_schema")
    recreated_tie = create_tie_authority(
        relation_type=tie["relation_type"], pair_left_ref=left_ref,
        pair_right_ref=right_ref,
        tolerance_authority_sha256=tie["tolerance_authority_sha256"],
        structural_tie_lineage_sha256=tie["structural_tie_lineage_sha256"],
        boundary_authority_sha256=tie["boundary_authority_sha256"],
        interval_authority_sha256=tie["interval_authority_sha256"])
    if dict(tie) != recreated_tie:
        raise ValueError("tie_authority_binding")
    base = {key: value[key] for key in required - {"provenance_sha256"}}
    if _hash(value["provenance_sha256"]) != v1.digest(base):
        raise ValueError("terminal_provenance")
    recreated = create_authority_v2(
        ordinal=cell["ordinal"], depth=cell["depth"], left=left, right=right,
        pair=pair, competitors=competitor_values, source=dict(value["source_authority"]),
        relation_type=tie["relation_type"],
        tolerance_authority_sha256=tie["tolerance_authority_sha256"],
        structural_tie_lineage_sha256=tie["structural_tie_lineage_sha256"],
        boundary_authority_sha256=tie["boundary_authority_sha256"],
        interval_authority_sha256=tie["interval_authority_sha256"])
    if v1.canonical(value) != v1.canonical(recreated):
        raise ValueError("terminal_noncanonical")
    return LoadedTerminalAuthority(
        2, {"ordinal": cell["ordinal"], "depth": cell["depth"],
            "left": left, "right": right}, pair, competitor_values,
        tie["relation_type"], dict(tie), value)


def load_authority(value: Mapping[str, object]) -> LoadedTerminalAuthority:
    if not isinstance(value, Mapping) or type(value.get("schema_version")) is not int:
        raise ValueError("terminal_authority_version")
    if value["schema_version"] == 1:
        cell, pair, competitors = v1.load_authority(value)
        return LoadedTerminalAuthority(1, cell, pair, competitors,
                                       "historical_v1_exact_identity", None, value)
    if value["schema_version"] == 2:
        return _load_v2(value)
    raise ValueError("terminal_authority_version")


def _maximum(first: Bounds, second: Bounds) -> Bounds:
    return Bounds(max(first.lo, second.lo), max(first.hi, second.hi))


def bound_terminal(value: Mapping[str, object]) -> dict:
    loaded = load_authority(value)
    left, right = loaded.cell["left"], loaded.cell["right"]
    pair_bounds = tuple(item.bounds(left, right)[0] for item in loaded.pair)
    pair_maximum = _maximum(*pair_bounds)
    competitor_bounds = tuple(item.bounds(left, right)[0] for item in loaded.competitors)
    comparisons = tuple(tuple(member - competitor for competitor in competitor_bounds)
                        for member in pair_bounds)
    if all(pair_maximum.lo > item.hi for item in competitor_bounds):
        status = "complete_dominance"
    elif any(item.lo > pair_maximum.hi for item in competitor_bounds):
        status = "competitor_dominance"
    else:
        endpoint = []
        for point in (left, right):
            pair_at = _maximum(*(item.bounds(point, point)[0] for item in loaded.pair))
            competitor_at = tuple(item.bounds(point, point)[0] for item in loaded.competitors)
            if all(pair_at.lo > item.hi for item in competitor_at):
                endpoint.append(1)
            elif any(item.lo > pair_at.hi for item in competitor_at):
                endpoint.append(-1)
            else:
                endpoint.append(0)
        status = "mixed" if endpoint[0] * endpoint[1] == -1 else "unresolved"
    return {
        "status": status,
        "source_version": loaded.source_version,
        "relation_type": loaded.relation_type,
        "pair_functions_bounded": 2,
        "competitor_functions_bounded": len(loaded.competitors),
        "pair_competitor_comparisons": sum(len(row) for row in comparisons),
        "representative_substitution": False,
    }


__all__ = ["LoadedTerminalAuthority", "bound_terminal", "create_authority_v2",
           "create_tie_authority", "load_authority"]
