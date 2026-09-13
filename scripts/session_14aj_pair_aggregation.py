#!/usr/bin/env python3
"""Synthetic-only Session 14aj within-state pair aggregation audit."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defensive_network_disruption.validation.pair_aggregation import (  # noqa: E402
    StatePairRecord, aggregate_pair_family, aggregate_states,
    inverse_ecdf_summary, reduce_categories_within_state,
    reduce_pairs_within_state,
)
from defensive_network_disruption.geometry.representation_study import weighted_summary  # noqa: E402

OUT = ROOT / "outputs" / "session14_pair_aggregation"
LOCAL = OUT / "local"
PROTOCOL = ROOT / "docs/protocols/phase_14aj_within_state_pair_aggregation.md"
IMPLEMENTATION = ROOT / "src/defensive_network_disruption/validation/pair_aggregation.py"
TEST = ROOT / "tests/test_session14aj_pair_aggregation.py"
STARTING_HEAD = "be8de6996c7a2dd79ec0ae2714bf445617e64741"
CLASSIFICATION = "A — WITHIN-STATE PAIR AGGREGATION REPAIRED"
READINESS = 1
PUBLIC_FILES = (
    "aggregation_contract.json", "pair_family_inventory.csv",
    "adversarial_pair_count_oracles.csv", "percentile_oracles.csv",
    "match_weighting_oracles.csv", "ordering_category_oracles.csv",
    "unavailable_oracles.csv", "non_pair_invariance.json", "r7_regression.json",
    "qc.json",
)
HISTORICAL = {
    "scripts/session_14r7_occlusion_study.py": "2bb467f03fc78b44a51ee13fb654813aac58f623c5a14c9f7ebffd42e5f3e00e",
    "outputs/continuous_occlusion_retry_14r7/manifest.json": "4cee379c77e9d5dcea11ff5affb4866834ed1abb6e56fa361dac30787860c9cf",
    "src/defensive_network_disruption/geometry/representation_study.py": "d0957593d9aa092160b5e890c49987ca6096c1429dfc0a7b9d2daa0388c033c9",
}

INVENTORY = (
    ("candidate_field_difference", "aligned_edge_pair", "state_pair_mean", "match", "macro_match", "B", "state arithmetic mean", "state summaries", "audited"),
    ("candidate_pair_spearman", "state", "state", "match", "macro_match", "B", "already one state correlation", "state correlations", "audited"),
    ("candidate_ordering_categories", "unordered_edge_pair", "state_pair_proportion", "match", "macro_match", "C", "five state proportions", "state proportions", "audited"),
    ("opposing_raw_distance_order", "eligible_distance_pair", "state_pair_proportion", "match", "macro_match", "C", "state disagreement proportion", "state proportions", "audited"),
    ("opposing_field_order", "opposing_distance_pair", "state_pair_proportion", "match", "macro_match", "C", "three state proportions", "state proportions", "audited"),
    ("endpoint_segment_ordering", "unordered_edge_pair", "state_pair_proportion", "match", "macro_match", "C", "five state proportions", "state proportions", "audited"),
    ("endpoint_segment_spearman", "state", "state", "match", "macro_match", "B", "already one state correlation", "state correlations", "audited"),
    ("session13_support_jaccard", "unordered_receiver_pair", "state_pair_mean", "match", "macro_match", "B", "already reduced in state descriptor", "state means", "audited"),
    ("overlap_redundancy_spearman", "state_descriptors", "match", "match", "macro_match", "B", "already one match correlation", "match correlations", "audited"),
    ("empty_or_constant_family", "none", "unavailable", "unavailable", "unavailable", "D", "excluded without zero imputation", "none", "audited"),
)


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, text=True,
                          capture_output=True).stdout.strip()


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            value.update(chunk)
    return value.hexdigest()


def canonical(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, sort_keys=True, allow_nan=False,
                       separators=(",", ":")) + "\n").encode()


def atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_name("." + path.name + ".pending")
    with pending.open("xb") as handle:
        handle.write(content); handle.flush(); os.fsync(handle.fileno())
    os.replace(pending, path)


def write_json(name: str, value: Mapping[str, Any]) -> None:
    atomic(OUT / name, canonical(value))


def write_csv(name: str, fields: Iterable[str], rows: list[dict[str, Any]]) -> None:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=tuple(fields), lineterminator="\n")
    writer.writeheader(); writer.writerows(rows)
    atomic(OUT / name, stream.getvalue().encode())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def preflight() -> None:
    require(not git("status", "--porcelain"), "dirty_tree")
    for path in (PROTOCOL, IMPLEMENTATION, TEST, Path(__file__)):
        relative = str(path.relative_to(ROOT))
        require(path.is_file() and bool(git("ls-files", "--error-unmatch", relative)),
                "uncommitted_authority")
    require({name: sha256(ROOT / name) for name in HISTORICAL} == HISTORICAL,
            "historical_authority_changed")
    print("Session 14aj preflight passed; synthetic aggregation only")


def row(records: tuple[StatePairRecord, ...], alias: str = "macro") -> dict[str, object]:
    return next(item for item in aggregate_pair_family(records) if item["alias"] == alias)


def pair_count_oracles() -> list[dict[str, Any]]:
    records = (StatePairRecord("match_a", "state_a", (0.0,)),
               StatePairRecord("match_a", "state_b", (1.0,) * 100))
    result = row(records, "match_a")
    return [{"oracle": "one_vs_one_hundred", "state_first": result["mean"],
             "raw_pair_pooled": 100 / 101, "expected": 0.5,
             "source_pairs": result["source_observations"],
             "state_summaries": result["observations"], "passed": result["mean"] == 0.5}]


def percentile_oracles() -> list[dict[str, Any]]:
    records = (StatePairRecord("match_a", "state_a", (0.0, 1.0)),
               StatePairRecord("match_a", "state_b", (1.0, 1.0)))
    result = row(records, "match_a")
    expected = {"minimum": 0.5, "q05": 0.5, "q25": 0.5, "q50": 0.5,
                "q75": 1.0, "q95": 1.0, "maximum": 1.0}
    return [{"oracle": "r7_percentile_support", "metric": key,
             "observed": result[key], "expected": value,
             "passed": result[key] == value} for key, value in expected.items()]


def match_oracles() -> list[dict[str, Any]]:
    records = [StatePairRecord("small", "s0", (0.0,))]
    records.extend(StatePairRecord("large", f"s{i:03d}", (1.0,)) for i in range(100))
    result = row(tuple(records))
    return [{"oracle": "unequal_match_state_counts", "macro_mean": result["mean"],
             "pooled_state_mean": 100 / 101, "expected_macro_mean": 0.5,
             "represented_matches": result["represented_matches"],
             "states_assessable": result["states_assessable"],
             "passed": result["mean"] == 0.5 and result["q50"] == 0.0}]


def ordering_oracles() -> list[dict[str, Any]]:
    reduced = reduce_categories_within_state((
        ("match_a", "state_many", ("agreement",) * 100),
        ("match_a", "state_one", ("strict_reversal",)),
    ), ("agreement", "strict_reversal"))
    rows = []
    for category, summaries in reduced.items():
        result = next(x for x in aggregate_states(
            (("match_a", "state_many"), ("match_a", "state_one")), summaries)
                      if x["alias"] == "match_a")
        rows.append({"oracle": "unequal_category_counts", "category": category,
                     "state_equal_mean": result["mean"],
                     "raw_pair_proportion": 100 / 101 if category == "agreement" else 1 / 101,
                     "expected": 0.5, "passed": result["mean"] == 0.5})
    return rows


def unavailable_oracles() -> list[dict[str, Any]]:
    records = (StatePairRecord("match_a", "empty", ()),
               StatePairRecord("match_a", "single", (0.25,)),
               StatePairRecord("match_a", "multiple", (0.0, 1.0)))
    result = row(records, "match_a")
    return [{"oracle": "empty_single_multiple", "states_total": result["states_total"],
             "states_assessable": result["states_assessable"],
             "states_unavailable": result["states_unavailable"],
             "observations": result["observations"],
             "source_observations": result["source_observations"],
             "single_pair_value": reduce_pairs_within_state((records[1],))[0].value,
             "expected_mean": 0.375, "observed_mean": result["mean"],
             "passed": result["mean"] == 0.375 and result["states_unavailable"] == 1}]


def non_pair_invariance() -> dict[str, Any]:
    values = [0.0, 0.5, 1.0, 1.0]
    weights = [0.25, 0.25, 0.25, 0.25]
    historical = weighted_summary(values, weights)
    independent = inverse_ecdf_summary(values, weights)
    return {"schema_version": 1, "families": ["endpoint_field", "segment_average_field",
        "union_minus_maximum", "state_multi_edge", "session13_direct_state",
        "non_pair_candidate_metrics"], "synthetic_historical": historical,
        "synthetic_repaired_path": independent, "exact": historical == independent,
        "historical_source_sha256": HISTORICAL["src/defensive_network_disruption/geometry/representation_study.py"]}


def r7_regression() -> dict[str, Any]:
    records = (StatePairRecord("match_a", "state_0", (0.0, 1.0)),
               StatePairRecord("match_a", "state_1", (1.0, 1.0)))
    repaired = row(records, "match_a")
    historical = weighted_summary([0.0, 1.0, 1.0, 1.0], [0.25] * 4)
    expected = inverse_ecdf_summary([0.5, 1.0], [0.5, 0.5])
    return {"schema_version": 1, "fixture": "two_state_pair_average",
            "historical": historical, "repaired": {key: repaired[key] for key in expected},
            "expected": expected, "historical_differs": historical != expected,
            "repaired_passed": {key: repaired[key] for key in expected} == expected,
            "pair_eligibility_unchanged": repaired["source_observations"] == 4,
            "state_summaries": repaired["observations"]}


def audit() -> None:
    preflight()
    marker = LOCAL / "audit.marker"
    require(not marker.exists() and not (OUT / "manifest.json").exists(), "closed_no_rerun")
    atomic(marker, canonical({"stage": "audit", "status": "claimed"}))
    pair_rows = pair_count_oracles(); percentile_rows = percentile_oracles()
    match_rows = match_oracles(); ordering_rows = ordering_oracles()
    unavailable_rows = unavailable_oracles(); invariant = non_pair_invariance()
    regression = r7_regression()
    passed = (all(row["passed"] for rows in (pair_rows, percentile_rows, match_rows,
              ordering_rows, unavailable_rows) for row in rows) and invariant["exact"] and
              regression["repaired_passed"] and regression["pair_eligibility_unchanged"])
    require(passed, "governed_oracle_failure")

    write_json("aggregation_contract.json", {"schema_version": 1, "status": "success",
        "hierarchy": ["equal_match", "equal_state_within_match", "average_eligible_pairs_within_state"],
        "percentile": "weighted_inverse_ecdf_first_cumulative_weight",
        "units": ["edge", "state", "state_pair_mean", "state_pair_proportion", "match", "macro_match"],
        "raw_pair_public_families": [], "classification": CLASSIFICATION, "readiness": READINESS})
    inventory_fields = ("family", "raw_unit", "state_unit", "match_unit", "macro_unit",
                        "classification", "reducer", "percentile_input", "status")
    write_csv("pair_family_inventory.csv", inventory_fields,
              [dict(zip(inventory_fields, item)) for item in INVENTORY])
    write_csv("adversarial_pair_count_oracles.csv", pair_rows[0].keys(), pair_rows)
    write_csv("percentile_oracles.csv", percentile_rows[0].keys(), percentile_rows)
    write_csv("match_weighting_oracles.csv", match_rows[0].keys(), match_rows)
    write_csv("ordering_category_oracles.csv", ordering_rows[0].keys(), ordering_rows)
    write_csv("unavailable_oracles.csv", unavailable_rows[0].keys(), unavailable_rows)
    write_json("non_pair_invariance.json", invariant)
    write_json("r7_regression.json", regression)
    write_json("qc.json", {"schema_version": 1, "status": "success",
        "classification": CLASSIFICATION, "readiness": READINESS,
        "pair_families_audited": len(INVENTORY), "oracles_passed": sum(len(x) for x in
        (pair_rows, percentile_rows, match_rows, ordering_rows, unavailable_rows)) + 2,
        "pair_eligibility_invariant": True, "ordering_semantics_invariant": True,
        "non_pair_invariant": True, "r7_regression_passed": True,
        "real_states_opened": 0, "real_edges_opened": 0, "scientific_results": False,
        "historical": HISTORICAL})
    output_hashes = {name: sha256(OUT / name) for name in PUBLIC_FILES}
    write_json("manifest.json", {"schema_version": 1, "status": "success",
        "starting_head": STARTING_HEAD, "implementation_commit": git("rev-parse", "HEAD"),
        "protocol_sha256": sha256(PROTOCOL), "implementation_sha256": sha256(IMPLEMENTATION),
        "test_sha256": sha256(TEST), "historical": HISTORICAL, "outputs": output_hashes,
        "classification": CLASSIFICATION, "readiness": READINESS})
    print("Session 14aj governed synthetic audit passed and closed")


def publication_check() -> None:
    manifest = json.loads((OUT / "manifest.json").read_text())
    require(set(manifest) == {"schema_version", "status", "starting_head", "implementation_commit",
        "protocol_sha256", "implementation_sha256", "test_sha256", "historical", "outputs",
        "classification", "readiness"}, "manifest_schema")
    require(manifest["status"] == "success" and manifest["classification"] == CLASSIFICATION and
            manifest["readiness"] == READINESS, "manifest_decision")
    require(manifest["protocol_sha256"] == sha256(PROTOCOL) and
            manifest["implementation_sha256"] == sha256(IMPLEMENTATION) and
            manifest["test_sha256"] == sha256(TEST), "authority_hash")
    require(manifest["historical"] == HISTORICAL and
            {name: sha256(OUT / name) for name in PUBLIC_FILES} == manifest["outputs"], "output_hash")
    require(set(path.name for path in OUT.iterdir() if path.is_file()) == set(PUBLIC_FILES) | {"manifest.json"},
            "public_membership")
    for name in (*PUBLIC_FILES, "manifest.json"):
        content = (OUT / name).read_text()
        require("/Users/" not in content and "target_index" not in content and
                "event_id" not in content and "provider" not in content.lower(), "publication_content")
    qc = json.loads((OUT / "qc.json").read_text())
    require(qc["real_states_opened"] == qc["real_edges_opened"] == 0 and
            qc["r7_regression_passed"] and qc["non_pair_invariant"], "qc")
    print("Session 14aj publication package validated")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "audit", "publication-check"))
    args = parser.parse_args()
    {"preflight": preflight, "audit": audit, "publication-check": publication_check}[args.command]()


if __name__ == "__main__":
    main()
