"""Bounded R9Y acquisition of a coefficient-only terminal-cell authority."""
from __future__ import annotations

from fractions import Fraction as F
from pathlib import Path
import json

from .r9x_terminal_authority import Coefficients, canonical, create_authority, derive_leaf_bounds, digest, load_authority


def coefficients(origin, receiver, defender) -> Coefficients:
    """Derive exact constant-width coefficients without field evaluation."""
    points = []
    for point in (origin, receiver, defender):
        if not isinstance(point, (list, tuple)) or len(point) != 2:
            raise ValueError("point_schema")
        values = tuple(F.from_float(value) for value in point)
        points.append(values)
    b, r, d = points
    ux, uy = r[0] - b[0], r[1] - b[1]
    vx, vy = d[0] - b[0], d[1] - b[1]
    return Coefficients(vx * vx + vy * vy, ux * vx + uy * vy,
                        (ux * vy - uy * vx) ** 2)


def load_lineage(directory: Path, *, expected_index_sha256: str) -> dict:
    """Validate the indexed R9V metadata without opening selected-edge contents."""
    directory = Path(directory)
    index_path = directory / "private_index.json"
    if digest(index_path.read_bytes()) != expected_index_sha256:
        raise ValueError("private_index_hash")
    index = json.loads(index_path.read_bytes())
    if set(index) != {"schema_version", "files"} or index["schema_version"] != 1:
        raise ValueError("private_index_schema")
    files = index["files"]
    required = {"boundary_capture.json", "selected_edge.json"}
    if not required <= set(files):
        raise ValueError("lineage_files")
    cells = []
    for name, expected in files.items():
        if not name.startswith("reference_reference_cell_"):
            continue
        path = directory / name
        if digest(path.read_bytes()) != expected:
            raise ValueError("cell_hash")
        value = json.loads(path.read_bytes())
        if set(value) != {"ordinal", "depth", "pair_status", "maximum_status"}:
            raise ValueError("cell_schema")
        cells.append(value)
    cells.sort(key=lambda item: item["ordinal"])
    if len(cells) != 81 or [item["ordinal"] for item in cells] != list(range(81)):
        raise ValueError("cell_order")
    unresolved = [item for item in cells if item["maximum_status"] == "unresolved"]
    if unresolved != [{"ordinal": 36, "depth": 80, "pair_status": "equal",
                       "maximum_status": "unresolved"}]:
        raise ValueError("unresolved_identity")
    partition_hash = digest(cells)
    return {"files": files, "cells": cells, "ordered_partition_sha256": partition_hash,
            "selected_edge_sha256": files["selected_edge.json"],
            "boundary_capture_sha256": files["boundary_capture.json"]}


def acquire(*, lineage: dict, boundary: dict, selected: dict,
            private_index_sha256: str, reference_implementation_sha256: str) -> dict:
    plateau = boundary.get("plateau")
    if not isinstance(plateau, dict) or set(plateau) != {"pair", "index", "end", "grid"}:
        raise ValueError("boundary_schema")
    grid, start, end = plateau["grid"], plateau["index"], plateau["end"]
    if not isinstance(grid, list) or not (0 <= start < end < len(grid)):
        raise ValueError("boundary_order")
    depths = tuple(item["depth"] for item in lineage["cells"])
    left, right = derive_leaf_bounds(F.from_float(grid[start]), F.from_float(grid[end]), depths, 36)
    if set(selected) != {"alias", "carrier", "receiver", "defenders"}:
        raise ValueError("selected_schema")
    derived = tuple(coefficients(selected["carrier"], selected["receiver"], item)
                    for item in selected["defenders"])
    pair_indices = tuple(plateau["pair"])
    if len(pair_indices) != 2 or any(type(item) is not int or not 0 <= item < len(derived)
                                     for item in pair_indices):
        raise ValueError("pair_indices")
    pair = tuple(derived[item] for item in pair_indices)
    competitors = tuple(item for ordinal, item in enumerate(derived)
                        if ordinal not in pair_indices)
    source = {
        "r9v_private_index_sha256": private_index_sha256,
        "boundary_capture_sha256": lineage["boundary_capture_sha256"],
        "ordered_partition_sha256": lineage["ordered_partition_sha256"],
        "selected_edge_sha256": lineage["selected_edge_sha256"],
        "reference_implementation_sha256": reference_implementation_sha256,
    }
    value = create_authority(ordinal=36, depth=80, left=left, right=right,
                             pair=pair, competitors=competitors, source=source)
    loaded = load_authority(json.loads(canonical(value)))
    if canonical(value) != canonical(create_authority(
            ordinal=loaded[0]["ordinal"], depth=loaded[0]["depth"],
            left=loaded[0]["left"], right=loaded[0]["right"], pair=loaded[1],
            competitors=loaded[2], source=value["source_authority"])):
        raise ValueError("round_trip")
    return value
