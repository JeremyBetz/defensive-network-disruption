"""Bounded R9AB construction of one version-2 terminal-cell authority."""
from __future__ import annotations

from fractions import Fraction as F
import json

from .r9aa_terminal_authority import create_authority_v2, load_authority
from .r9x_terminal_authority import canonical, derive_leaf_bounds, digest
from .r9y_acquisition import coefficients

ORDINAL = 36
DEPTH = 80
RELATION = "common_inactive_branch"


def authority_hashes(*, lineage: dict, boundary: dict, left: F, right: F,
                     pair_indices: tuple[int, int], private_index_sha256: str,
                     reference_implementation_sha256: str,
                     verifier_sha256: str, onset_owner_sha256: str) -> dict:
    cell = lineage["cells"][ORDINAL]
    if cell != {"ordinal": ORDINAL, "depth": DEPTH, "pair_status": "equal",
                "maximum_status": "unresolved"}:
        raise ValueError("unresolved_identity")
    outer = {
        "schema_version": 1,
        "grid_start": boundary["plateau"]["grid"][boundary["plateau"]["index"]],
        "grid_end": boundary["plateau"]["grid"][boundary["plateau"]["end"]],
        "boundary_authority_sha256": lineage["boundary_capture_sha256"],
    }
    interval = {
        "schema_version": 1, "ordinal": ORDINAL, "depth": DEPTH,
        "left": {"numerator": str(left.numerator), "denominator": str(left.denominator)},
        "right": {"numerator": str(right.numerator), "denominator": str(right.denominator)},
        "outer_interval_source_sha256": digest(outer),
        "ordered_partition_sha256": lineage["ordered_partition_sha256"],
    }
    structural = {
        "schema_version": 1, "equal_cell_record": cell,
        "ordered_pair_indices": list(pair_indices),
        "reference_implementation_sha256": reference_implementation_sha256,
        "r9v_private_index_sha256": private_index_sha256,
    }
    tolerance = {
        "schema_version": 1, "maximum_owner_absolute_tolerance": "1e-12",
        "verifier_implementation_sha256": verifier_sha256,
        "onset_owner_implementation_sha256": onset_owner_sha256,
    }
    return {
        "boundary_authority_sha256": lineage["boundary_capture_sha256"],
        "interval_authority_sha256": digest(interval),
        "structural_tie_lineage_sha256": digest(structural),
        "tolerance_authority_sha256": digest(tolerance),
        "outer_interval_source_sha256": digest(outer),
    }


def construct(*, lineage: dict, boundary: dict, selected: dict,
              private_index_sha256: str, reference_implementation_sha256: str,
              verifier_sha256: str, onset_owner_sha256: str) -> tuple[dict, dict]:
    plateau = boundary.get("plateau")
    if not isinstance(plateau, dict) or set(plateau) != {"pair", "index", "end", "grid"}:
        raise ValueError("boundary_schema")
    grid, start, end = plateau["grid"], plateau["index"], plateau["end"]
    if not isinstance(grid, list) or not (0 <= start < end < len(grid)):
        raise ValueError("boundary_order")
    depths = tuple(item["depth"] for item in lineage["cells"])
    left, right = derive_leaf_bounds(F.from_float(grid[start]), F.from_float(grid[end]),
                                     depths, ORDINAL)
    if set(selected) != {"alias", "carrier", "receiver", "defenders"}:
        raise ValueError("selected_schema")
    defenders = selected["defenders"]
    derived = tuple(coefficients(selected["carrier"], selected["receiver"], item)
                    for item in defenders)
    pair_indices = tuple(plateau["pair"])
    if len(pair_indices) != 2 or pair_indices[0] == pair_indices[1] or any(
            type(item) is not int or not 0 <= item < len(derived) for item in pair_indices):
        raise ValueError("pair_indices")
    pair = tuple(derived[item] for item in pair_indices)
    if pair[0].authority_sha256 == pair[1].authority_sha256:
        raise ValueError("common_branch_requires_distinct_pair")
    competitor_positions = tuple(i for i in range(len(derived)) if i not in pair_indices)
    competitors = tuple(derived[i] for i in competitor_positions)
    if not competitors or len(competitor_positions) != len(defenders) - 2:
        raise ValueError("competitor_completeness")
    hashes = authority_hashes(
        lineage=lineage, boundary=boundary, left=left, right=right,
        pair_indices=pair_indices, private_index_sha256=private_index_sha256,
        reference_implementation_sha256=reference_implementation_sha256,
        verifier_sha256=verifier_sha256, onset_owner_sha256=onset_owner_sha256)
    source = {
        "r9v_private_index_sha256": private_index_sha256,
        "boundary_capture_sha256": lineage["boundary_capture_sha256"],
        "ordered_partition_sha256": lineage["ordered_partition_sha256"],
        "selected_edge_sha256": lineage["selected_edge_sha256"],
        "reference_implementation_sha256": reference_implementation_sha256,
    }
    value = create_authority_v2(
        ordinal=ORDINAL, depth=DEPTH, left=left, right=right, pair=pair,
        competitors=competitors, source=source, relation_type=RELATION,
        tolerance_authority_sha256=hashes["tolerance_authority_sha256"],
        structural_tie_lineage_sha256=hashes["structural_tie_lineage_sha256"],
        boundary_authority_sha256=hashes["boundary_authority_sha256"],
        interval_authority_sha256=hashes["interval_authority_sha256"])
    loaded = load_authority(json.loads(canonical(value)))
    if loaded.source_version != 2 or loaded.relation_type != RELATION:
        raise ValueError("compatibility_load")
    if loaded.pair[0].authority_sha256 == loaded.pair[1].authority_sha256:
        raise ValueError("ordered_distinct_pair")
    if canonical(value) != canonical(loaded.record):
        raise ValueError("round_trip")
    receipt = {
        "schema_version": 1, "source_defender_count": len(defenders),
        "ordered_pair_positions": list(pair_indices), "excluded_pair_count": 2,
        "competitor_position_count": len(competitor_positions),
        "unique_coefficient_count": len(value["coefficients"]),
        "unique_competitor_count": len(value["competitors"]),
        "pair_refs_distinct": value["pair_left_ref"] != value["pair_right_ref"],
        "competitor_complete": len(competitor_positions) == len(defenders) - 2,
        "relation": RELATION, **hashes,
    }
    return value, receipt


__all__ = ["construct", "authority_hashes", "ORDINAL", "DEPTH", "RELATION"]
