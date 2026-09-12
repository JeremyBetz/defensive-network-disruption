"""Canonical-versus-provenance comparison for synthetic Session 14 diagnostics."""
from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Mapping

from .vector_reproducibility import float_bits, ulp_distance


def canonical_route(route: Mapping) -> dict:
    """Project only production-relevant structural fields from a route record."""
    result = copy.deepcopy(dict(route))
    for onset in result.get("onsets", ()):
        onset.pop("raw", None)
    for switch in result.get("switches", ()):
        switch.pop("raw", None)
    return result


def raw_provenance(record: Mapping) -> dict:
    """Retain raw roots/onsets and their bits independently of canonical state."""
    rows = []
    for item in record["records"]:
        for kind in ("onsets", "switches"):
            for ordinal, value in enumerate(item["routing"].get(kind, ())):
                raw = float(value["raw"])
                rows.append({"fixture": item["fixture"], "candidate": item["candidate"],
                             "kind": kind[:-1], "ordinal": ordinal, "raw": raw,
                             "raw_bits": float_bits(raw)})
    return {"environment": copy.deepcopy(record["environment"]), "roots": rows}


@dataclass(frozen=True)
class CanonicalComparison:
    canonical_structural_equal: bool
    partitions_equal: bool
    ownership_equal: bool
    routing_equal: bool
    residual_bounds_equal: bool
    accepted_resolutions_equal: bool
    component_order_equal: bool
    final_components_bitwise_equal: bool


def compare_records(local: Mapping, remote: Mapping) -> CanonicalComparison:
    left = {(x["fixture"], x["candidate"]): x for x in local["records"]}
    right = {(x["fixture"], x["candidate"]): x for x in remote["records"]}
    if tuple(left) != tuple(right):
        return CanonicalComparison(False, False, False, False, False, False, False, False)
    partitions = ownership = routing = residuals = resolutions = order = components = True
    for key, first in left.items():
        second = right[key]
        a, b = canonical_route(first["routing"]), canonical_route(second["routing"])
        partitions &= a.get("partition_bits") == b.get("partition_bits") and a.get("partitions") == b.get("partitions")
        ownership &= [(x.get("owners_before"), x.get("owners_at"), x.get("owners_after"), x.get("crossing_pairs")) for x in a.get("switches", ())] == [(x.get("owners_before"), x.get("owners_at"), x.get("owners_after"), x.get("crossing_pairs")) for x in b.get("switches", ())]
        residuals &= a.get("residual_bound") == b.get("residual_bound")
        routing &= a == b
        resolutions &= first["accepted"]["intervals"] == second["accepted"]["intervals"]
        left_components = first["comparison"]; right_components = second["comparison"]
        order &= [x["component"] for x in left_components] == [x["component"] for x in right_components]
        components &= all(x["actual_bits"] == y["actual_bits"] for x, y in zip(left_components, right_components, strict=True))
    structural = all((partitions, ownership, routing, residuals, resolutions, order, components))
    return CanonicalComparison(structural, partitions, ownership, routing, residuals, resolutions, order, components)


def compare_raw_provenance(local: Mapping, remote: Mapping) -> dict:
    left, right = raw_provenance(local), raw_provenance(remote)
    if [(x["fixture"], x["candidate"], x["kind"], x["ordinal"]) for x in left["roots"]] != [(x["fixture"], x["candidate"], x["kind"], x["ordinal"]) for x in right["roots"]]:
        return {"raw_solver_provenance_equal": False, "record_order_equal": False, "differences": []}
    differences = []
    for first, second in zip(left["roots"], right["roots"], strict=True):
        if first["raw_bits"] != second["raw_bits"]:
            differences.append({"fixture": first["fixture"], "candidate": first["candidate"],
                                "kind": first["kind"], "ordinal": first["ordinal"],
                                "local": first["raw"], "ci": second["raw"],
                                "local_bits": first["raw_bits"], "ci_bits": second["raw_bits"],
                                "ulp_distance": ulp_distance(first["raw"], second["raw"])})
    return {"raw_solver_provenance_equal": not differences, "record_order_equal": True,
            "differences": differences, "local_environment": left["environment"],
            "ci_environment": right["environment"]}
