#!/usr/bin/env python3
"""One frozen Session 5 M1-versus-M2 development comparison."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import statistics
import subprocess
import sys
from pathlib import Path

import numpy as np
import scipy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defensive_network_disruption.data.receiver_choices import ChoiceSet
from defensive_network_disruption.data.skillcorner_session2 import DEVELOPMENT_MATCHES, SOURCE_COMMIT
from defensive_network_disruption.validation.choice_model import weighted_standardization
from defensive_network_disruption.validation.ranking_metrics import expected_credits, match_macro
from defensive_network_disruption.validation.session5 import (
    M2_NAMES, choice_features_m1_m2, fit_with_fail_closed_gate,
)
from defensive_network_disruption.validation.ranking_features import M1_NAMES


START_AUTHORITY = "746357d0c358062df49ec6641a9ac20c7eba97fc"
SESSION3_EXECUTION = "54dc4f81d29b9532e4e0c41a95d4f33980360891"
POPULATION_SHA256 = "cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d"
PROTOCOL = ROOT / "docs/protocols/phase_05_m2_multi_defender_attenuation.md"
SESSION3 = ROOT / "outputs/receiver_ranking_m0_m1"
SESSION4 = ROOT / "outputs/m1_failure_mode_audit"
POPULATION = SESSION3 / "local/population.jsonl"
OUTPUT_ROOT = ROOT / "outputs/receiver_ranking_m2"
LOCAL_ROOT = OUTPUT_ROOT / "local"
PREPARATION = LOCAL_ROOT / "preparation.json"
EXECUTION_MARKER = LOCAL_ROOT / "execution_state.json"
ALIASES = {item: f"development_{index:02d}" for index, item in enumerate(sorted(DEVELOPMENT_MATCHES, key=int), 1)}
PUBLIC_FILES = (
    "m1_match_metrics.csv", "m2_match_metrics.csv", "paired_comparison.csv",
    "aggregate_metrics.json", "qc.json", "manifest.json",
)
EXECUTION_FILES = (
    "scripts/session_05_m2.py",
    "src/defensive_network_disruption/geometry/attenuation.py",
    "src/defensive_network_disruption/validation/session5.py",
    "src/defensive_network_disruption/validation/choice_model.py",
    "src/defensive_network_disruption/validation/ranking_features.py",
    "src/defensive_network_disruption/validation/ranking_metrics.py",
)


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_text(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)


def json_text(value):
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def committed_sha256(commit, relative):
    content = subprocess.run(
        ["git", "show", f"{commit}:{relative}"], cwd=ROOT, check=True, capture_output=True,
    ).stdout
    return hashlib.sha256(content).hexdigest()


def verify_closed_authority():
    if subprocess.run(["git", "merge-base", "--is-ancestor", START_AUTHORITY, "HEAD"], cwd=ROOT).returncode:
        raise RuntimeError("Session 5 starting authority is not an ancestor")
    git("ls-files", "--error-unmatch", str(PROTOCOL.relative_to(ROOT)))
    if sha256(PROTOCOL) != committed_sha256("HEAD", str(PROTOCOL.relative_to(ROOT))):
        raise RuntimeError("Phase 5 protocol differs from its committed version")

    session3_manifest = json.loads((SESSION3 / "manifest.json").read_text())
    if session3_manifest["execution_commit"] != SESSION3_EXECUTION:
        raise RuntimeError("unexpected Session 3 execution identity")
    for name, digest in session3_manifest["output_sha256"].items():
        if sha256(SESSION3 / name) != digest:
            raise RuntimeError(f"closed Session 3 artifact changed: {name}")
    freeze = json.loads((SESSION3 / "population_freeze.json").read_text())
    if freeze["population_sha256"] != POPULATION_SHA256 or freeze["evaluation_eligible"] != 7227 or freeze["fit_eligible"] != 7227:
        raise RuntimeError("Session 3 population authority mismatch")

    session4_manifest = json.loads((SESSION4 / "manifest.json").read_text())
    for name, digest in session4_manifest["output_sha256"].items():
        if sha256(SESSION4 / name) != digest:
            raise RuntimeError(f"closed Session 4 artifact changed: {name}")
    return session3_manifest, freeze, session4_manifest


def safe_population_path():
    expected_root = (SESSION3 / "local").resolve()
    if POPULATION.is_symlink() or not POPULATION.is_file() or not POPULATION.resolve().is_relative_to(expected_root):
        raise PermissionError("unsafe or missing governed population path")
    if sha256(POPULATION) != POPULATION_SHA256:
        raise RuntimeError("population bytes do not match Session 3 authority")
    return POPULATION


def preflight():
    verify_closed_authority()
    safe_population_path()
    if set(DEVELOPMENT_MATCHES) != {
        "1886347", "1899585", "1925299", "1996435", "2006229",
        "2011166", "2013725", "2015213", "2017461",
    }:
        raise RuntimeError("development allowlist changed")
    print("Session 5 preflight passed")


def load_population():
    path = safe_population_path()
    grouped = {match_id: [] for match_id in DEVELOPMENT_MATCHES}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            item = json.loads(line)
            match_id = item["match_id"]
            if match_id not in grouped:
                raise PermissionError("population contains a prohibited match")
            choice = ChoiceSet(
                match_id=match_id, event_id=item["event_id"],
                candidate_ids=tuple(item["candidate_ids"]),
                candidate_xy=tuple(tuple(value) for value in item["candidate_xy"]),
                defender_xy=tuple(tuple(value) for value in item["defender_xy"]),
                carrier_xy=tuple(item["carrier_xy"]), target_index=item["target_index"],
                target_outside=item["target_outside"],
            )
            if choice.target_index is None or choice.target_outside:
                raise RuntimeError("frozen Session 5 population must be fully fit eligible")
            grouped[match_id].append(choice)
    if sum(map(len, grouped.values())) != 7227 or any(not rows for rows in grouped.values()):
        raise RuntimeError("population count or match coverage mismatch")
    return grouped


def build_design(grouped):
    raw = {"m1": {}, "m2": {}}
    degenerate = 0
    defender_counts = {}
    for match_id in sorted(DEVELOPMENT_MATCHES, key=int):
        raw["m1"][match_id], raw["m2"][match_id] = [], []
        counts = []
        for choice in grouped[match_id]:
            m1, m2, count = choice_features_m1_m2(choice)
            raw["m1"][match_id].append(m1)
            raw["m2"][match_id].append(m2)
            degenerate += count
            counts.append(len(choice.defender_xy))
        defender_counts[ALIASES[match_id]] = {
            "minimum": min(counts), "maximum": max(counts),
            "distinct_counts": sorted(set(counts)),
        }
    return raw, degenerate, defender_counts


def matrix_digest(rows):
    digest = hashlib.sha256()
    for matrix in rows:
        contiguous = np.ascontiguousarray(matrix, dtype=np.float64)
        digest.update(np.asarray(contiguous.shape, dtype=np.int64).tobytes())
        digest.update(contiguous.tobytes())
    return digest.hexdigest()


def implementation_hashes_from_worktree():
    return {path: sha256(ROOT / path) for path in EXECUTION_FILES}


def prepare():
    preflight()
    if EXECUTION_MARKER.exists() or any((OUTPUT_ROOT / name).exists() for name in PUBLIC_FILES):
        raise RuntimeError("Session 5 execution or scored output already exists")
    grouped = load_population()
    raw, degenerate, defender_counts = build_design(grouped)
    preparation = {
        "schema_version": "1.0.0", "performance_computed": False,
        "protocol_sha256": sha256(PROTOCOL), "population_sha256": sha256(POPULATION),
        "attempt_count": sum(map(len, grouped.values())),
        "development_match_aliases": sorted(ALIASES.values()),
        "feature_names": {"m1": list(M1_NAMES), "m2": list(M2_NAMES)},
        "feature_sha256": {
            model: {ALIASES[match]: matrix_digest(rows) for match, rows in raw[model].items()}
            for model in ("m1", "m2")
        },
        "implementation_file_sha256": implementation_hashes_from_worktree(),
        "strict_raw_nesting": all(
            np.array_equal(m1, m2[:, :5])
            for match in DEVELOPMENT_MATCHES
            for m1, m2 in zip(raw["m1"][match], raw["m2"][match], strict=True)
        ),
        "degenerate_segments": degenerate, "defender_count_qc": defender_counts,
    }
    if not preparation["strict_raw_nesting"]:
        raise RuntimeError("M1 and M2 are not strictly nested")
    atomic_text(PREPARATION, json_text(preparation))
    print(json.dumps({"attempt_count": preparation["attempt_count"], "strict_raw_nesting": True}))


def standardize_group(features, mean, scale):
    return {match: [(matrix - mean) / scale for matrix in rows] for match, rows in features.items()}


def metric_row(alias, credits):
    return {
        "match_alias": alias, "evaluation_eligible": len(credits),
        "heldout_fit_eligible": len(credits), "target_outside_zero_credit": 0,
        "mrr": sum(item["rr"] for item in credits) / len(credits),
        "hit_at_1": sum(item["hit1"] for item in credits) / len(credits),
        "hit_at_3": sum(item["hit3"] for item in credits) / len(credits),
        "tied_target_blocks": sum(item["tied"] for item in credits),
    }


def read_metric_rows(path):
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return {
        row["match_alias"]: {
            key: (int(value) if key in {"evaluation_eligible", "heldout_fit_eligible", "target_outside_zero_credit", "tied_target_blocks"} else float(value))
            if key != "match_alias" else value
            for key, value in row.items()
        }
        for row in rows
    }


def atomic_csv(path, rows, fields):
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.parent.mkdir(parents=True, exist_ok=True)
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def validate_preparation(raw):
    if not PREPARATION.is_file() or PREPARATION.is_symlink():
        raise RuntimeError("score-free preparation is missing or unsafe")
    preparation = json.loads(PREPARATION.read_text())
    if preparation["performance_computed"] is not False or preparation["population_sha256"] != POPULATION_SHA256:
        raise RuntimeError("score-free preparation authority mismatch")
    if preparation["implementation_file_sha256"] != implementation_hashes_from_worktree():
        raise RuntimeError("implementation differs from score-free preparation")
    current = {
        model: {ALIASES[match]: matrix_digest(rows) for match, rows in raw[model].items()}
        for model in ("m1", "m2")
    }
    if current != preparation["feature_sha256"]:
        raise RuntimeError("prepared design hash mismatch")
    execution_commit = git("rev-parse", "HEAD")
    for path, digest in preparation["implementation_file_sha256"].items():
        if committed_sha256(execution_commit, path) != digest:
            raise RuntimeError("Session 5 implementation is not frozen in HEAD")
    return preparation, execution_commit


def fit_fold(model, heldout, grouped, raw, authoritative_qc=None):
    training = [match for match in sorted(DEVELOPMENT_MATCHES, key=int) if match != heldout]
    train_raw = {match: raw[model][match] for match in training}
    targets = {match: [choice.target_index for choice in grouped[match]] for match in training}
    mean, scale, zero = weighted_standardization(train_raw)
    if np.any(zero):
        raise RuntimeError(f"zero-variance {model} column blocks comparison")
    standardized = standardize_group(train_raw, mean, scale)
    beta, fit_qc = fit_with_fail_closed_gate(standardized, targets)
    if authoritative_qc is not None:
        parameters = authoritative_qc["parameters"]
        for name, observed, expected in (
            ("mean", mean, parameters["mean"]),
            ("scale", scale, parameters["scale"]),
            ("coefficients", beta, parameters["coefficients"]),
        ):
            if not np.array_equal(observed, np.asarray(expected, dtype=np.float64)):
                raise RuntimeError(f"authoritative M1 {name} replay mismatch for {ALIASES[heldout]}")
    heldout_features = [(matrix - mean) / scale for matrix in raw[model][heldout]]
    credits = [
        expected_credits(matrix @ beta, choice.target_index)
        for matrix, choice in zip(heldout_features, grouped[heldout], strict=True)
    ]
    return metric_row(ALIASES[heldout], credits), {
        "feature_names": list(M1_NAMES if model == "m1" else M2_NAMES),
        "fit": fit_qc, "parameters": {"coefficients": beta.tolist(), "mean": mean.tolist(), "scale": scale.tolist()},
        "training_fit_eligible": sum(len(grouped[item]) for item in training),
        "heldout_evaluation_eligible": len(grouped[heldout]),
        "standardization_zero_variance": [bool(value) for value in zero],
    }


def run():
    preflight()
    if git("status", "--porcelain"):
        raise RuntimeError("Session 5 run requires a clean committed implementation")
    if EXECUTION_MARKER.exists() or any((OUTPUT_ROOT / name).exists() for name in PUBLIC_FILES):
        raise RuntimeError("Session 5 is single-run; execution state or scored output already exists")
    grouped = load_population()
    raw, degenerate, defender_counts = build_design(grouped)
    preparation, execution_commit = validate_preparation(raw)
    atomic_text(EXECUTION_MARKER, json_text({
        "state": "started", "execution_commit": execution_commit,
        "population_sha256": POPULATION_SHA256,
    }))

    session3_qc = json.loads((SESSION3 / "qc.json").read_text())
    authoritative_rows = read_metric_rows(SESSION3 / "m1_match_metrics.csv")
    m1_rows, fold_qc = [], {}
    for heldout in sorted(DEVELOPMENT_MATCHES, key=int):
        alias = ALIASES[heldout]
        row, qc = fit_fold("m1", heldout, grouped, raw, session3_qc["folds"][alias]["m1"])
        if row != authoritative_rows[alias]:
            raise RuntimeError(f"authoritative M1 metric replay mismatch for {alias}")
        m1_rows.append(row)
        fold_qc[alias] = {"m1": qc}
    authoritative_aggregate = json.loads((SESSION3 / "aggregate_metrics.json").read_text())["models"]["m1"]["match_macro"]
    reproduced = {field: match_macro({row["match_alias"]: row for row in m1_rows}, field)
                  for field in ("mrr", "hit_at_1", "hit_at_3")}
    if reproduced != authoritative_aggregate:
        raise RuntimeError("authoritative M1 aggregate replay mismatch")

    m2_rows = []
    for heldout in sorted(DEVELOPMENT_MATCHES, key=int):
        alias = ALIASES[heldout]
        row, qc = fit_fold("m2", heldout, grouped, raw)
        m1_parameters = fold_qc[alias]["m1"]["parameters"]
        if not np.array_equal(qc["parameters"]["mean"][:5], m1_parameters["mean"]):
            raise RuntimeError("M1/M2 shared preprocessing means differ")
        if not np.array_equal(qc["parameters"]["scale"][:5], m1_parameters["scale"]):
            raise RuntimeError("M1/M2 shared preprocessing scales differ")
        m2_rows.append(row)
        fold_qc[alias]["m2"] = qc

    paired = []
    for m1, m2 in zip(m1_rows, m2_rows, strict=True):
        paired.append({
            "match_alias": m1["match_alias"],
            "m1_mrr": m1["mrr"], "m2_mrr": m2["mrr"], "mrr_difference_m2_minus_m1": m2["mrr"] - m1["mrr"],
            "m1_hit_at_1": m1["hit_at_1"], "m2_hit_at_1": m2["hit_at_1"],
            "hit_at_1_difference_m2_minus_m1": m2["hit_at_1"] - m1["hit_at_1"],
            "m1_hit_at_3": m1["hit_at_3"], "m2_hit_at_3": m2["hit_at_3"],
            "hit_at_3_difference_m2_minus_m1": m2["hit_at_3"] - m1["hit_at_3"],
        })
    differences = [row["mrr_difference_m2_minus_m1"] for row in paired]
    models = {
        model: {field: match_macro({row["match_alias"]: row for row in rows}, field)
                for field in ("mrr", "hit_at_1", "hit_at_3")}
        for model, rows in (("m1", m1_rows), ("m2", m2_rows))
    }
    aggregate = {
        "comparison": "development_only_leave_one_match_out", "models": models,
        "m2_minus_m1": {
            field: models["m2"][field] - models["m1"][field]
            for field in ("mrr", "hit_at_1", "hit_at_3")
        } | {
            "paired_mrr_mean": statistics.fmean(differences),
            "paired_mrr_median": statistics.median(differences),
            "positive_matches": sum(value > 0 for value in differences),
            "negative_matches": sum(value < 0 for value in differences),
            "tied_matches": sum(value == 0 for value in differences),
        },
        "interpretation_constraints": {
            "accessibility": "PROXY ONLY", "suppression": "NOT SUPPORTABLE",
            "significance_test": None, "practical_effect_threshold": None,
        },
    }
    metric_fields = list(m1_rows[0])
    atomic_csv(OUTPUT_ROOT / "m1_match_metrics.csv", m1_rows, metric_fields)
    atomic_csv(OUTPUT_ROOT / "m2_match_metrics.csv", m2_rows, metric_fields)
    atomic_csv(OUTPUT_ROOT / "paired_comparison.csv", paired, list(paired[0]))
    atomic_text(OUTPUT_ROOT / "aggregate_metrics.json", json_text(aggregate))
    qc = {
        "schema_version": "1.0.0", "population_sha256": POPULATION_SHA256,
        "attempt_count": 7227, "development_match_count": 9,
        "strict_raw_nesting": preparation["strict_raw_nesting"],
        "degenerate_segments": degenerate, "defender_count_qc": defender_counts,
        "m1_authoritative_replay": True, "tie_tolerance": 1e-12,
        "attenuation_scale_metres": 5.0, "folds": fold_qc,
    }
    atomic_text(OUTPUT_ROOT / "qc.json", json_text(qc))
    atomic_text(LOCAL_ROOT / "fitted_parameters.json", json_text({
        alias: {model: fold_qc[alias][model]["parameters"] for model in ("m1", "m2")}
        for alias in sorted(fold_qc)
    }))
    output_hashes = {name: sha256(OUTPUT_ROOT / name) for name in PUBLIC_FILES if name != "manifest.json"}
    manifest = {
        "schema_version": "1.0.0", "starting_authority": START_AUTHORITY,
        "session3_execution_commit": SESSION3_EXECUTION,
        "session4_manifest_sha256": sha256(SESSION4 / "manifest.json"),
        "protocol_commit": git("log", "-1", "--format=%H", "--", str(PROTOCOL.relative_to(ROOT))),
        "protocol_sha256": sha256(PROTOCOL), "execution_commit": execution_commit,
        "execution_file_sha256": preparation["implementation_file_sha256"],
        "source_commit": SOURCE_COMMIT, "population_sha256": POPULATION_SHA256,
        "development_match_aliases": sorted(ALIASES.values()), "attempt_count": 7227,
        "feature": {"name": "summed_segment_attenuation", "formula": "sum_j exp(-d_j / 5.0)", "scale_metres": 5.0},
        "models": {"m1": list(M1_NAMES), "m2": list(M2_NAMES), "conditional_softmax": "unregularized"},
        "folding": "leave_one_match_out", "environment": {
            "python": sys.version.split()[0], "numpy": np.__version__, "scipy": scipy.__version__,
        },
        "output_sha256": output_hashes,
        "firewalls": {"reserved_access": False, "pose_access": False, "vendor_score_access": False,
                      "velocity_or_reachability": False, "network_features": False, "passage_inspection": False,
                      "alternate_m2": False, "h_tuning": False},
    }
    atomic_text(OUTPUT_ROOT / "manifest.json", json_text(manifest))
    atomic_text(EXECUTION_MARKER, json_text({
        "state": "completed", "execution_commit": execution_commit,
        "population_sha256": POPULATION_SHA256,
        "manifest_sha256": sha256(OUTPUT_ROOT / "manifest.json"),
    }))
    print(json.dumps(aggregate["m2_minus_m1"], sort_keys=True))


def publication_check():
    expected_aliases = set(ALIASES.values())
    forbidden_headers = {"match_id", "event_id", "player_id", "candidate_id", "timestamp", "x", "y", "score", "rank"}
    for name in ("m1_match_metrics.csv", "m2_match_metrics.csv", "paired_comparison.csv"):
        path = OUTPUT_ROOT / name
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if forbidden_headers.intersection(reader.fieldnames or []):
                raise RuntimeError(f"reconstructive field in {name}")
            rows = list(reader)
        if {row["match_alias"] for row in rows} != expected_aliases or len(rows) != 9:
            raise RuntimeError(f"unexpected public aliases in {name}")
        if any(re.search(r"\b\d{7}\b", json.dumps(row)) for row in rows):
            raise RuntimeError(f"provider identifier in {name}")
    manifest = json.loads((OUTPUT_ROOT / "manifest.json").read_text())
    for name, digest in manifest["output_sha256"].items():
        if sha256(OUTPUT_ROOT / name) != digest:
            raise RuntimeError(f"closed output hash mismatch: {name}")
    for name in PUBLIC_FILES:
        content = (OUTPUT_ROOT / name).read_text()
        if "/Users/" in content or "data/session_02" in content:
            raise RuntimeError(f"private path in {name}")
    if manifest["population_sha256"] != POPULATION_SHA256 or manifest["attempt_count"] != 7227:
        raise RuntimeError("public population identity mismatch")
    print("Session 5 publication check passed")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "prepare", "run", "publication-check"))
    command = parser.parse_args().command
    if command == "preflight":
        preflight()
    elif command == "prepare":
        prepare()
    elif command == "run":
        run()
    else:
        publication_check()


if __name__ == "__main__":
    main()
