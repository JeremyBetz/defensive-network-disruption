"""Synthetic acceptance for the R9AA pair-schema and traceback repair."""
from __future__ import annotations

import copy
from fractions import Fraction as F
import json
from pathlib import Path
from typing import Mapping

from defensive_network_disruption.geometry import r9aa_terminal_authority as v2
from defensive_network_disruption.geometry import r9x_terminal_authority as v1
from .checkpoint_ci_authority import sha256_file
from .r9aa_failure import AcquisitionFailureBoundary

HASHES = {name: v1.digest(("synthetic:" + name).encode()) for name in
          ("tolerance", "lineage", "boundary", "interval")}
SOURCE = {key: v1.digest(("synthetic:" + key).encode()) for key in v1.SOURCE_KEYS}


def coefficient(dot, cross2):
    return v1.Coefficients(F(1), F(dot), F(cross2))


def authority(left, right, relation="tolerance_certified", *, competitors=None):
    return v2.create_authority_v2(
        ordinal=1, depth=2, left=F(1, 2), right=F(1),
        pair=(left, right), competitors=tuple(competitors or (coefficient(4, 16),)),
        source=SOURCE, relation_type=relation,
        tolerance_authority_sha256=HASHES["tolerance"],
        structural_tie_lineage_sha256=HASHES["lineage"],
        boundary_authority_sha256=HASHES["boundary"],
        interval_authority_sha256=HASHES["interval"])


def _accepted(value):
    try:
        v2.load_authority(value)
    except (KeyError, TypeError, ValueError):
        return False
    return True


def schema_controls():
    first, second = coefficient(4, 8), coefficient(4, 9)
    duplicate = authority(first, first, "symbolic_identity")
    distinct = authority(first, second)
    common = authority(first, second, "common_inactive_branch")
    rows = []
    def add(name, expected, observed):
        rows.append({"control": name, "expected": expected, "observed": observed,
                     "passed": expected == observed})
    add("exact_duplicate_v2", "accepted", "accepted" if _accepted(duplicate) else "blocked")
    add("distinct_tolerance_v2", "accepted", "accepted" if _accepted(distinct) else "blocked")
    add("distinct_common_branch_v2", "accepted", "accepted" if _accepted(common) else "blocked")
    changed = copy.deepcopy(distinct); changed["tie_authority"]["scope"] = "point"
    add("point_tie_only", "blocked", "accepted" if _accepted(changed) else "blocked")
    changed = copy.deepcopy(distinct); changed["tie_authority"].pop("structural_tie_lineage_sha256")
    add("missing_tie_lineage", "blocked", "accepted" if _accepted(changed) else "blocked")
    changed = copy.deepcopy(distinct); changed["tie_authority"]["tolerance_authority_sha256"] = "0" * 63
    add("wrong_tolerance_hash", "blocked", "accepted" if _accepted(changed) else "blocked")
    changed = copy.deepcopy(distinct); changed["pair_left_ref"], changed["pair_right_ref"] = changed["pair_right_ref"], changed["pair_left_ref"]
    add("reordered_pair_refs", "blocked", "accepted" if _accepted(changed) else "blocked")
    changed = copy.deepcopy(distinct); changed["coefficients"][0]["dot"] = v1.fraction_record(F(99))
    add("tampered_coefficient", "blocked", "accepted" if _accepted(changed) else "blocked")
    changed = copy.deepcopy(distinct); changed["competitors"] = []
    add("missing_competitor", "blocked", "accepted" if _accepted(changed) else "blocked")
    changed = copy.deepcopy(distinct); changed["schema_version"] = 3
    add("unsupported_version", "blocked", "accepted" if _accepted(changed) else "blocked")
    legacy = v1.create_authority(ordinal=1, depth=2, left=F(1, 2), right=F(1),
                                 pair=(first, first), competitors=(coefficient(4, 16),),
                                 source=SOURCE)
    loaded = v2.load_authority(json.loads(v1.canonical(legacy)))
    add("historical_v1_exact_duplicate", "accepted",
        "accepted" if loaded.relation_type == "historical_v1_exact_identity" else "blocked")
    add("v2_deterministic_round_trip", "accepted",
        "accepted" if v1.canonical(distinct) == v1.canonical(copy.deepcopy(distinct)) else "blocked")
    bound = v2.bound_terminal(distinct)
    add("geometry_free_distinct_pair_bound", "accepted",
        "accepted" if bound["pair_functions_bounded"] == 2 and
        not bound["representative_substitution"] and
        bound["pair_competitor_comparisons"] == 2 else "blocked")
    outcomes = (
        ("complete_dominance", coefficient(10, 0), coefficient(10, 0), coefficient(10, 1000)),
        ("competitor_dominance", coefficient(10, 1000), coefficient(10, 1000), coefficient(10, 0)),
        ("mixed", coefficient(3, F(4, 5)), coefficient(3, F(4, 5)), coefficient(4, 16)),
        ("unresolved", coefficient(4, 8), coefficient(4, F(8) + F(1, 10**30)), coefficient(4, 8)),
    )
    for expected, left, right, competitor in outcomes:
        relation = "symbolic_identity" if left == right else "tolerance_certified"
        observed = v2.bound_terminal(
            authority(left, right, relation, competitors=(competitor,)))["status"]
        add("bound_outcome_" + expected, expected, observed)
    return rows, {"legacy_relation": loaded.relation_type, "bound": bound,
                  "v1_bytes_preserved": v1.canonical(legacy) == v1.canonical(json.loads(v1.canonical(legacy)))}


def compatibility_matrix():
    return (
        {"version": "v1", "pair_relation": "exact_duplicate", "result": "accepted_unchanged"},
        {"version": "v1", "pair_relation": "distinct", "result": "blocked_unchanged"},
        {"version": "v2", "pair_relation": "distinct_with_interval_authority", "result": "accepted"},
    )


def failure_controls(folder: Path):
    folder = Path(folder); folder.mkdir(parents=True, exist_ok=True)
    stages = ("lineage_review", "materialization", "coefficient_derivation",
              "authority_construction", "validation", "publication_initialization")
    rows = []
    private = []
    for ordinal, stage in enumerate(stages):
        place = folder / f"stage_{ordinal:02d}"
        boundary = AcquisitionFailureBoundary(place); order = []
        try:
            raise RuntimeError("synthetic_" + stage)
        except RuntimeError as error:
            result = boundary.close(
                error, stage, timestamp="2026-09-22T00:00:00Z",
                write_blocked_qc=lambda captured: order.append(("qc", captured.traceback_sha256)),
                publish=lambda captured: order.append(("publication", captured.traceback_sha256)))
        valid = boundary.controller.validate()
        passed = (result["events"] == ("traceback_captured", "capture_validated",
                  "blocked_qc", "publication") and len(order) == 2 and
                  order[0][1] == order[1][1] == valid["traceback_sha256"])
        rows.append({"control": stage, "expected": "capture_qc_publish",
                     "observed": "capture_qc_publish" if passed else "invalid", "passed": passed})
        private.append({"control": stage, "traceback_sha256": valid["traceback_sha256"],
                        "events": list(result["events"])})
    for name, failing_callback in (("blocked_qc_failure", "qc"), ("publisher_failure", "publication")):
        place = folder / name; boundary = AcquisitionFailureBoundary(place); called = []
        def qc(captured):
            called.append("qc")
            if failing_callback == "qc": raise OSError("synthetic_qc")
        def publish(captured):
            called.append("publication")
            if failing_callback == "publication": raise OSError("synthetic_publication")
        try: raise RuntimeError("synthetic_original")
        except RuntimeError as error:
            result = boundary.close(error, name, timestamp="2026-09-22T00:00:00Z",
                                    write_blocked_qc=qc, publish=publish)
        valid = boundary.controller.validate()
        passed = (result["publication_error"] == "OSError" and
                  (place / "publication_failure.json").is_file() and
                  valid["exception_type"] == "RuntimeError" and
                  called == (["qc"] if failing_callback == "qc" else ["qc", "publication"]))
        rows.append({"control": name, "expected": "secondary_preserved",
                     "observed": "secondary_preserved" if passed else "invalid", "passed": passed})
        private.append({"control": name, "traceback_sha256": valid["traceback_sha256"],
                        "events": list(result["events"])})
    place = folder / "reraise"; boundary = AcquisitionFailureBoundary(place); observed = None
    try:
        try: raise ValueError("synthetic_reraise")
        except ValueError as error:
            boundary.close(error, "reraise", timestamp="2026-09-22T00:00:00Z",
                           write_blocked_qc=lambda _: None, publish=lambda _: None,
                           reraise=True)
    except ValueError as error:
        observed = (type(error).__name__, str(error))
    valid = boundary.controller.validate(); passed = observed == ("ValueError", "synthetic_reraise")
    rows.append({"control": "reraise", "expected": "original_reraised",
                 "observed": "original_reraised" if passed else "invalid", "passed": passed})
    private.append({"control": "reraise", "traceback_sha256": valid["traceback_sha256"]})
    return rows, private


def historical_hashes(root: Path, expected: Mapping[str, str]):
    return {name: sha256_file(Path(root) / name) == value for name, value in expected.items()}


__all__ = ["compatibility_matrix", "failure_controls", "historical_hashes",
           "schema_controls"]
