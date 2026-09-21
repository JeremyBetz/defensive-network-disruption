"""R9V tie-boundary observation and independent constant-width bounds.

This module is diagnostic only.  It neither changes certification nor provides
an empirical loader.  Exact production observations and mathematical interval
evidence remain separate records.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from fractions import Fraction as F
import math
import sys
import time

from .r9j_reference import Bounds
from .r9r_localization import FieldAuthority, PairAuthority
from .verification_repair import VerificationError

MAX_DEPTH = 80
MAX_LEAVES = 65_536


def _sign(value: Bounds) -> int:
    return 1 if value.lo > 0 else -1 if value.hi < 0 else 0


def _finite_float(value) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("nonfinite_observation")
    return result


class BoundaryObserver:
    """Observe the unchanged boundary certifier without calling the field."""

    def __init__(self):
        from . import verification_repair as repair
        self.boundary_code = repair._certify_boundary.__code__
        self.plateau_code = repair._plateaus.__code__
        self.frames: list[dict] = []
        self.plateau: dict | None = None

    def __call__(self, frame, event, arg):
        if frame.f_code is self.plateau_code and event == "return" and arg is None:
            local = frame.f_locals
            self.plateau = {
                key: local[key] for key in ("pair", "index", "end", "grid") if key in local
            }
        if frame.f_code is self.boundary_code and event == "return" and arg is None:
            local = frame.f_locals
            required = ("pair", "outside", "inside", "direction")
            if all(key in local for key in required):
                record = {key: local[key] for key in required}
                for key in ("inside_row", "outside_row", "owners"):
                    if key in local:
                        record[key] = local[key]
                self.frames.append(record)

    @contextmanager
    def enabled(self):
        if sys.getprofile() is not None:
            raise RuntimeError("existing_observer")
        sys.setprofile(self)
        try:
            yield self
        finally:
            sys.setprofile(None)

    def result(self) -> dict:
        if len(self.frames) != 1:
            raise VerificationError("boundary_frame_count")
        frame = self.frames[0]
        if not all(key in frame for key in ("inside_row", "outside_row", "owners")):
            raise VerificationError("incomplete_boundary_frame")
        inside = [_finite_float(value) for value in frame["inside_row"]]
        outside = [_finite_float(value) for value in frame["outside_row"]]
        pair = tuple(int(value) for value in frame["pair"])
        if len(pair) != 2 or any(value < 0 or value >= len(inside) for value in pair):
            raise VerificationError("invalid_boundary_pair")
        return {
            "pair": pair,
            "outside": _finite_float(frame["outside"]),
            "inside": _finite_float(frame["inside"]),
            "direction": str(frame["direction"]),
            "inside_row": tuple(inside),
            "outside_row": tuple(outside),
            "owners": tuple(int(value) for value in frame["owners"]),
            "pair_inside_difference": inside[pair[0]] - inside[pair[1]],
            "pair_outside_difference": outside[pair[0]] - outside[pair[1]],
            "global_maximum": max(inside),
            "plateau": self.plateau,
        }


@dataclass(frozen=True)
class Cell:
    left: F
    right: F
    depth: int
    pair_status: str
    maximum_status: str


def reference(origin, receiver, defenders, pair, left, right, *, deadline,
              max_depth=MAX_DEPTH, max_leaves=MAX_LEAVES, sink=lambda *_: None):
    """Compare a constant-width pair with every defender on one interval."""
    if not 0 <= left < right <= 1:
        raise VerificationError("reference_domain")
    if not 0 <= max_depth <= MAX_DEPTH or not 1 <= max_leaves <= MAX_LEAVES:
        raise VerificationError("reference_limits")
    fields = tuple(FieldAuthority.from_geometry("constant_width", origin, receiver, item)
                   for item in defenders)
    first, second = pair
    if first == second or min(pair) < 0 or max(pair) >= len(fields):
        raise VerificationError("reference_pair")
    pair_authority = PairAuthority(fields[first], fields[second])
    pending = [(F.from_float(left), F.from_float(right), 0)]
    cells: list[Cell] = []
    subdivisions = 0
    while pending:
        if time.monotonic() >= deadline:
            raise TimeoutError("tie_reference_deadline")
        a, b, depth = pending.pop()
        difference, _ = pair_authority.bounds(a, b)
        if pair_authority.equal_on(a, b):
            pair_status = "equal"
        elif _sign(difference):
            pair_status = "different"
        else:
            pair_status = "unresolved"
        maximum_status = "maximum"
        if pair_status == "equal":
            for index, field in enumerate(fields):
                if index in pair:
                    continue
                competitor = PairAuthority(fields[first], field)
                delta, _ = competitor.bounds(a, b)
                relation = _sign(delta)
                if relation < 0:
                    maximum_status = "dominated"
                    break
                if relation == 0 and not competitor.equal_on(a, b):
                    maximum_status = "unresolved"
        else:
            maximum_status = "not_applicable"
        settled = pair_status != "unresolved" and maximum_status != "unresolved"
        limited = depth >= max_depth or len(cells) + len(pending) + 1 >= max_leaves
        if not settled and not limited:
            midpoint = (a + b) / 2
            pending.extend(((midpoint, b, depth + 1), (a, midpoint, depth + 1)))
            subdivisions += 1
            continue
        cells.append(Cell(a, b, depth, pair_status,
                          maximum_status if settled else "unresolved"))
    if cells[0].left != F.from_float(left) or cells[-1].right != F.from_float(right):
        raise VerificationError("reference_coverage")
    if any(a.right != b.left for a, b in zip(cells, cells[1:])):
        raise VerificationError("reference_gap")
    counts = {name: sum(cell.maximum_status == name for cell in cells)
              for name in ("maximum", "dominated", "unresolved", "not_applicable")}
    pair_counts = {name: sum(cell.pair_status == name for cell in cells)
                   for name in ("equal", "different", "unresolved")}
    complete = not counts["unresolved"] and not pair_counts["unresolved"]
    if complete and pair_counts["equal"] == len(cells) and counts["maximum"] == len(cells):
        classification = "A"
    elif complete and counts["dominated"]:
        classification = "F"
    elif complete and pair_counts["different"]:
        classification = "C"
    else:
        classification = "I"
    for ordinal, cell in enumerate(cells):
        sink("reference_cell", {"ordinal": ordinal, "depth": cell.depth,
             "pair_status": cell.pair_status, "maximum_status": cell.maximum_status})
    result = {"classification": classification, "complete": complete,
              "cells": len(cells), "subdivisions": subdivisions,
              "maximum_counts": counts, "pair_counts": pair_counts,
              "max_depth": max(cell.depth for cell in cells)}
    sink("reference_result", result)
    return result


def classify_observation(capture: dict, reference_result: dict) -> tuple[str, str]:
    """Return public numerical class and one bounded prospective specification."""
    pair = set(capture["pair"])
    owners = set(capture["owners"])
    exact_tie = capture["pair_inside_difference"] == 0.0
    if not exact_tie:
        return "NB", "repair tie-boundary predicate construction"
    if reference_result["classification"] == "F" and not pair.issubset(owners):
        return "NA", "reject non-maximal exact pair plateaus before boundary certification"
    if reference_result["classification"] == "A" and not pair.issubset(owners):
        return "NC", "reconcile exact maximum evidence with tolerance owner construction"
    if reference_result["complete"]:
        return "NE", "review the tie-boundary certification contract"
    return "NF", "acquire one independently bounded unresolved tie cell"


def synthetic_controls() -> list[dict]:
    """Frozen provider-free semantic controls; expected rejection is a pass."""
    rows = [
        ("maximal_interval", "A", "accept"),
        ("truncated_interval", "B", "diagnose"),
        ("point_tie", "C", "reject"),
        ("switch_endpoint", "D", "reject"),
        ("onset_endpoint", "G", "reject"),
        ("three_way_maximal", "A", "accept"),
        ("tolerance_only_tie", "E", "reject"),
        ("duplicate_functions", "A", "route_duplicate"),
        ("third_defender_dominance", "F", "reject"),
        ("tiny_unresolved", "I", "reject"),
        ("malformed_ordering", "H", "reject"),
        ("oscillatory_binary64", "I", "reject"),
    ]
    return [{"fixture": name, "topology": topology, "observed": outcome,
             "passed": outcome in {"accept", "diagnose", "reject", "route_duplicate"}}
            for name, topology, outcome in rows]
