#!/usr/bin/env python3
"""Frozen Session 3 population preparation and M0/M1 benchmark."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import statistics
import subprocess
import sys
from pathlib import Path

import numpy as np
import scipy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defensive_network_disruption.data.receiver_choices import ChoiceSet, prepare_match
from defensive_network_disruption.data.skillcorner_session2 import DEVELOPMENT_MATCHES, SOURCE_COMMIT
from defensive_network_disruption.validation.choice_model import fit_conditional_softmax, weighted_standardization
from defensive_network_disruption.validation.ranking_features import M0_NAMES, M1_NAMES, choice_features
from defensive_network_disruption.validation.ranking_metrics import expected_credits, match_macro

AUTHORITY = "5fcef6b8b141d636ca5bcf7c41f9e536dd755f03"
PROTOCOL = ROOT / "docs/protocols/phase_03_receiver_ranking_m0_m1.md"
DATA_ROOT = ROOT / "data/session_02"
OUTPUT_ROOT = ROOT / "outputs/receiver_ranking_m0_m1"
LOCAL_ROOT = OUTPUT_ROOT / "local"
POPULATION = LOCAL_ROOT / "population.jsonl"
ALIASES = {match_id: f"development_{index:02d}" for index, match_id in enumerate(sorted(DEVELOPMENT_MATCHES, key=int), 1)}
PUBLIC_FILES = (
    "m0_match_metrics.csv", "m1_match_metrics.csv", "paired_comparison.csv",
    "aggregate_metrics.json", "qc.json", "manifest.json",
)
EXECUTION_FILES = (
    "scripts/session_03_benchmark.py",
    "src/defensive_network_disruption/data/receiver_choices.py",
    "src/defensive_network_disruption/validation/choice_model.py",
    "src/defensive_network_disruption/validation/ranking_features.py",
    "src/defensive_network_disruption/validation/ranking_metrics.py",
)


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def preflight():
    if subprocess.run(["git", "merge-base", "--is-ancestor", AUTHORITY, "HEAD"], cwd=ROOT).returncode:
        raise RuntimeError("Session 2 authority missing")
    if not PROTOCOL.is_file() or not DATA_ROOT.is_dir():
        raise RuntimeError("protocol or governed development data missing")
    for match_id in DEVELOPMENT_MATCHES:
        for suffix in ("match.json", "tracking_extrapolated.jsonl", "dynamic_events.csv"):
            path = DATA_ROOT / "data/matches" / match_id / f"{match_id}_{suffix}"
            if not path.is_file() or path.is_symlink():
                raise RuntimeError("authorized development product missing or unsafe")


def choice_record(choice):
    return {
        "match_id": choice.match_id, "event_id": choice.event_id,
        "candidate_ids": choice.candidate_ids, "candidate_xy": choice.candidate_xy,
        "defender_xy": choice.defender_xy, "carrier_xy": choice.carrier_xy,
        "target_index": choice.target_index, "target_outside": choice.target_outside,
    }


def prepare():
    preflight()
    LOCAL_ROOT.mkdir(parents=True, exist_ok=True)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    summaries = {}
    all_lines = []
    for match_id in sorted(DEVELOPMENT_MATCHES, key=int):
        choices, qc = prepare_match(match_id, DATA_ROOT)
        lines = [json.dumps(choice_record(choice), sort_keys=True, separators=(",", ":")) for choice in choices]
        all_lines.extend(lines)
        summaries[ALIASES[match_id]] = {
            "raw_pass_attempts": qc["raw_pass_attempts"], "exclusions": qc["exclusions"],
            "evaluation_eligible": qc["evaluation_eligible"], "fit_eligible": qc["fit_eligible"],
            "target_outside": qc["target_outside"], "target_outside_reasons": qc["target_outside_reasons"],
            "population_sha256": hashlib.sha256(("\n".join(lines) + "\n").encode()).hexdigest(),
        }
    rendered = "\n".join(all_lines) + "\n"
    POPULATION.write_text(rendered)
    aggregate_exclusions = {}
    aggregate_outside_reasons = {}
    for summary in summaries.values():
        for name, count in summary["exclusions"].items():
            aggregate_exclusions[name] = aggregate_exclusions.get(name, 0) + count
        for name, count in summary["target_outside_reasons"].items():
            aggregate_outside_reasons[name] = aggregate_outside_reasons.get(name, 0) + count
    freeze = {
        "schema_version": "1.0.0", "source_commit": SOURCE_COMMIT,
        "protocol_sha256": hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
        "development_match_count": 9, "raw_pass_attempts": sum(x["raw_pass_attempts"] for x in summaries.values()),
        "evaluation_eligible": sum(x["evaluation_eligible"] for x in summaries.values()),
        "fit_eligible": sum(x["fit_eligible"] for x in summaries.values()),
        "target_outside_zero_credit": sum(x["target_outside"] for x in summaries.values()),
        "target_outside_reasons": aggregate_outside_reasons,
        "exclusions": aggregate_exclusions, "matches": summaries,
        "population_sha256": hashlib.sha256(rendered.encode()).hexdigest(),
        "performance_computed": False,
    }
    (OUTPUT_ROOT / "population_freeze.json").write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n")
    (LOCAL_ROOT / "alias_map.json").write_text(json.dumps(ALIASES, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: freeze[key] for key in ("raw_pass_attempts", "evaluation_eligible", "fit_eligible", "target_outside_zero_credit")}))


def load_population():
    choices = []
    with POPULATION.open() as handle:
        for line in handle:
            item = json.loads(line)
            choices.append(ChoiceSet(
                match_id=item["match_id"], event_id=item["event_id"],
                candidate_ids=tuple(item["candidate_ids"]),
                candidate_xy=tuple(tuple(x) for x in item["candidate_xy"]),
                defender_xy=tuple(tuple(x) for x in item["defender_xy"]),
                carrier_xy=tuple(item["carrier_xy"]), target_index=item["target_index"],
                target_outside=item["target_outside"],
            ))
    return choices


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def committed_sha256(commit, path):
    content = subprocess.run(
        ["git", "show", f"{commit}:{path}"], cwd=ROOT, check=True, capture_output=True,
    ).stdout
    return hashlib.sha256(content).hexdigest()


def standardize_group(features, mean, scale):
    return {match: [(x - mean) / scale for x in rows] for match, rows in features.items()}


def metric_row(alias, credits, fit_eligible, target_outside):
    if not credits:
        raise RuntimeError(f"{alias} has no eligible evaluation observations")
    return {
        "match_alias": alias,
        "evaluation_eligible": len(credits),
        "heldout_fit_eligible": fit_eligible,
        "target_outside_zero_credit": target_outside,
        "mrr": sum(item["rr"] for item in credits) / len(credits),
        "hit_at_1": sum(item["hit1"] for item in credits) / len(credits),
        "hit_at_3": sum(item["hit3"] for item in credits) / len(credits),
        "tied_target_blocks": sum(item["tied"] for item in credits),
    }


def write_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run():
    preflight()
    freeze_path = OUTPUT_ROOT / "population_freeze.json"
    if not freeze_path.is_file() or not POPULATION.is_file():
        raise RuntimeError("committed population freeze and ignored population detail are required")
    freeze = json.loads(freeze_path.read_text())
    if freeze.get("performance_computed") is not False or freeze.get("population_sha256") != sha256(POPULATION):
        raise RuntimeError("population does not match the frozen score-free artifact")
    status = git("status", "--porcelain")
    if status:
        raise RuntimeError("benchmark execution requires a clean committed implementation")
    if any((OUTPUT_ROOT / name).exists() for name in PUBLIC_FILES):
        raise RuntimeError("scored outputs already exist; corrective reruns are prohibited")

    choices = load_population()
    by_match = {match_id: [] for match_id in DEVELOPMENT_MATCHES}
    for choice in choices:
        if choice.match_id not in by_match:
            raise PermissionError("population contains a match outside the development allowlist")
        by_match[choice.match_id].append(choice)
    raw_features = {"m0": {}, "m1": {}}
    degenerate = 0
    for model in ("m0", "m1"):
        for match_id, match_choices in by_match.items():
            raw_features[model][match_id] = []
            for choice in match_choices:
                matrix, count = choice_features(choice, model)
                raw_features[model][match_id].append(matrix)
                if model == "m1":
                    degenerate += count

    model_rows = {"m0": [], "m1": []}
    paired_rows = []
    fold_qc = {}
    local_parameters = {}
    for heldout in sorted(DEVELOPMENT_MATCHES, key=int):
        training = [match_id for match_id in sorted(DEVELOPMENT_MATCHES, key=int) if match_id != heldout]
        fit_indices = {
            match_id: [index for index, choice in enumerate(by_match[match_id]) if choice.target_index is not None]
            for match_id in training
        }
        targets = {
            match_id: [by_match[match_id][index].target_index for index in fit_indices[match_id]]
            for match_id in training
        }
        fit_raw = {
            model: {
                match_id: [raw_features[model][match_id][index] for index in fit_indices[match_id]]
                for match_id in training
            } for model in ("m0", "m1")
        }
        m0_mean, m0_scale, m0_zero = weighted_standardization(fit_raw["m0"])
        m1_mean, m1_scale, m1_zero = weighted_standardization(fit_raw["m1"])
        if not np.array_equal(m0_mean, m1_mean[:3]) or not np.array_equal(m0_scale, m1_scale[:3]):
            raise RuntimeError("M0 preprocessing columns are not exactly nested inside M1")
        if np.any(m0_zero) or np.any(m1_zero):
            raise RuntimeError("zero-variance column blocks the comparison")

        fold_details = {}
        heldout_rows = {}
        for model, names, mean, scale in (
            ("m0", M0_NAMES, m0_mean, m0_scale),
            ("m1", M1_NAMES, m1_mean, m1_scale),
        ):
            standardized_train = standardize_group(fit_raw[model], mean, scale)
            beta, fit_qc = fit_conditional_softmax(standardized_train, targets)
            evaluation_features = [(x - mean) / scale for x in raw_features[model][heldout]]
            credits = [
                expected_credits(matrix @ beta, choice.target_index)
                for matrix, choice in zip(evaluation_features, by_match[heldout], strict=True)
            ]
            alias = ALIASES[heldout]
            heldout_fit = sum(choice.target_index is not None for choice in by_match[heldout])
            outside = sum(choice.target_index is None for choice in by_match[heldout])
            row = metric_row(alias, credits, heldout_fit, outside)
            model_rows[model].append(row)
            heldout_rows[model] = row
            fold_details[model] = {
                "feature_names": list(names), "fit": fit_qc,
                "parameters": {"coefficients": beta.tolist(), "mean": mean.tolist(), "scale": scale.tolist()},
                "training_evaluation_eligible": sum(len(by_match[item]) for item in training),
                "training_fit_eligible": sum(len(fit_indices[item]) for item in training),
                "heldout_evaluation_eligible": len(by_match[heldout]),
                "heldout_fit_eligible": heldout_fit,
                "standardization_zero_variance": [bool(value) for value in (m0_zero if model == "m0" else m1_zero)],
            }
            local_parameters[f"{alias}_{model}"] = {
                "coefficients": beta.tolist(), "mean": mean.tolist(), "scale": scale.tolist()
            }
        paired_rows.append({
            "match_alias": ALIASES[heldout],
            "m0_mrr": heldout_rows["m0"]["mrr"], "m1_mrr": heldout_rows["m1"]["mrr"],
            "mrr_difference_m1_minus_m0": heldout_rows["m1"]["mrr"] - heldout_rows["m0"]["mrr"],
            "m0_hit_at_1": heldout_rows["m0"]["hit_at_1"], "m1_hit_at_1": heldout_rows["m1"]["hit_at_1"],
            "m0_hit_at_3": heldout_rows["m0"]["hit_at_3"], "m1_hit_at_3": heldout_rows["m1"]["hit_at_3"],
        })
        fold_qc[ALIASES[heldout]] = fold_details

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    metric_fields = ["match_alias", "evaluation_eligible", "heldout_fit_eligible", "target_outside_zero_credit",
                     "mrr", "hit_at_1", "hit_at_3", "tied_target_blocks"]
    write_csv(OUTPUT_ROOT / "m0_match_metrics.csv", model_rows["m0"], metric_fields)
    write_csv(OUTPUT_ROOT / "m1_match_metrics.csv", model_rows["m1"], metric_fields)
    write_csv(OUTPUT_ROOT / "paired_comparison.csv", paired_rows, list(paired_rows[0]))
    differences = [row["mrr_difference_m1_minus_m0"] for row in paired_rows]
    def pooled(rows, field):
        denominator = sum(row["evaluation_eligible"] for row in rows)
        return sum(row[field] * row["evaluation_eligible"] for row in rows) / denominator
    aggregate = {
        "comparison": "development_only_leave_one_match_out",
        "models": {
            model: {
                "match_macro": {field: match_macro({row["match_alias"]: row for row in rows}, field)
                                for field in ("mrr", "hit_at_1", "hit_at_3")},
                "pooled_descriptive": {field: pooled(rows, field) for field in ("mrr", "hit_at_1", "hit_at_3")},
            }
            for model, rows in model_rows.items()
        },
        "m1_minus_m0": {
            "mrr": match_macro({row["match_alias"]: {"value": row["mrr_difference_m1_minus_m0"]}
                                for row in paired_rows}, "value"),
            "hit_at_1": match_macro({row["match_alias"]: {"value": row["m1_hit_at_1"] - row["m0_hit_at_1"]}
                                     for row in paired_rows}, "value"),
            "hit_at_3": match_macro({row["match_alias"]: {"value": row["m1_hit_at_3"] - row["m0_hit_at_3"]}
                                     for row in paired_rows}, "value"),
            "paired_mrr_mean": statistics.fmean(differences),
            "paired_mrr_median": statistics.median(differences),
            "positive_matches": sum(value > 0 for value in differences),
            "negative_matches": sum(value < 0 for value in differences),
            "tied_matches": sum(value == 0 for value in differences),
        },
        "interpretation_constraints": {
            "practical_effect_threshold": None, "significance_test": None,
            "accessibility": "PROXY ONLY", "suppression": "NOT SUPPORTABLE",
            "m2": "deferred pending a specific prospective hypothesis",
        },
    }
    (OUTPUT_ROOT / "aggregate_metrics.json").write_text(json.dumps(aggregate, indent=2, sort_keys=True) + "\n")
    qc = {
        "development_match_count": 9, "population_sha256": freeze["population_sha256"],
        "degenerate_segments": degenerate, "tie_tolerance": 1e-12,
        "optimizer": {"method": "L-BFGS-B", "maxiter": 2000, "maxls": 50,
                      "ftol": 1e-12, "gtol": 1e-8, "regularization": None},
        "folds": fold_qc,
    }
    (OUTPUT_ROOT / "qc.json").write_text(json.dumps(qc, indent=2, sort_keys=True) + "\n")
    LOCAL_ROOT.mkdir(parents=True, exist_ok=True)
    (LOCAL_ROOT / "fitted_parameters.json").write_text(json.dumps(local_parameters, indent=2, sort_keys=True) + "\n")

    output_hashes = {name: sha256(OUTPUT_ROOT / name) for name in PUBLIC_FILES if name != "manifest.json"}
    execution_commit = git("rev-parse", "HEAD")
    manifest = {
        "schema_version": "1.0.0", "authority_commit": AUTHORITY, "execution_commit": execution_commit,
        "source_commit": SOURCE_COMMIT, "protocol_sha256": sha256(PROTOCOL),
        "population_sha256": freeze["population_sha256"], "development_match_aliases": sorted(ALIASES.values()),
        "model_specification": {"m0": list(M0_NAMES), "m1": list(M1_NAMES), "m0_plus": "omitted",
                                "conditional_softmax": "unregularized", "folding": "leave_one_match_out"},
        "environment": {"python": sys.version.split()[0], "numpy": np.__version__, "scipy": scipy.__version__},
        "execution_file_sha256": {path: committed_sha256(execution_commit, path) for path in EXECUTION_FILES},
        "output_sha256": output_hashes,
    }
    (OUTPUT_ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(aggregate["m1_minus_m0"], sort_keys=True))


def finalize_existing():
    """Complete required aggregate metadata from the preserved scored outputs; never refit."""
    archive = LOCAL_ROOT / "initial_scored_outputs"
    if not archive.is_dir() or not (LOCAL_ROOT / "fitted_parameters.json").is_file():
        raise RuntimeError("preserved initial outputs and fitted parameters are required")
    initial_hashes = {path.name: sha256(path) for path in sorted(archive.iterdir()) if path.is_file()}
    rows_by_model = {}
    for model in ("m0", "m1"):
        with (OUTPUT_ROOT / f"{model}_match_metrics.csv").open(newline="", encoding="utf-8") as handle:
            rows_by_model[model] = list(csv.DictReader(handle))
    aggregate = json.loads((OUTPUT_ROOT / "aggregate_metrics.json").read_text())
    if "postscore_completion" in aggregate:
        raise RuntimeError("existing outputs were already finalized")
    for model, rows in rows_by_model.items():
        macro = aggregate["models"][model]
        denominator = sum(int(row["evaluation_eligible"]) for row in rows)
        pooled = {
            field: sum(float(row[field]) * int(row["evaluation_eligible"]) for row in rows) / denominator
            for field in ("mrr", "hit_at_1", "hit_at_3")
        }
        aggregate["models"][model] = {"match_macro": macro, "pooled_descriptive": pooled}
    aggregate["postscore_completion"] = (
        "Pooled summaries and public preprocessing/model parameters were derived from preserved outputs; "
        "no model was refit or rescored."
    )
    (OUTPUT_ROOT / "aggregate_metrics.json").write_text(json.dumps(aggregate, indent=2, sort_keys=True) + "\n")

    parameters = json.loads((LOCAL_ROOT / "fitted_parameters.json").read_text())
    qc = json.loads((OUTPUT_ROOT / "qc.json").read_text())
    for alias, fold in qc["folds"].items():
        for model in ("m0", "m1"):
            fold[model]["parameters"] = parameters[f"{alias}_{model}"]
    qc["initial_scored_output_sha256"] = initial_hashes
    qc["corrective_rerun"] = False
    (OUTPUT_ROOT / "qc.json").write_text(json.dumps(qc, indent=2, sort_keys=True) + "\n")

    manifest_path = OUTPUT_ROOT / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["environment"]["scipy"] = scipy.__version__
    execution_commit = manifest["execution_commit"]
    manifest["execution_file_sha256"] = {
        path: committed_sha256(execution_commit, path) for path in EXECUTION_FILES
    }
    manifest["postscore_completion"] = "aggregate/metadata completion only; no refit or rescore"
    manifest["initial_scored_output_sha256"] = initial_hashes
    manifest["output_sha256"] = {
        name: sha256(OUTPUT_ROOT / name) for name in PUBLIC_FILES if name != "manifest.json"
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print("existing scored outputs finalized without refit or rescore")


def publication_check():
    """Validate compact outputs and reject reconstructive provider material."""
    expected_aliases = set(ALIASES.values())
    forbidden_headers = {"match_id", "event_id", "player_id", "candidate_id", "timestamp", "x", "y", "score", "rank"}
    for name in ("m0_match_metrics.csv", "m1_match_metrics.csv", "paired_comparison.csv"):
        path = OUTPUT_ROOT / name
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if forbidden_headers.intersection(reader.fieldnames or []):
                raise RuntimeError(f"reconstructive field in {name}")
            rows = list(reader)
        if {row["match_alias"] for row in rows} != expected_aliases:
            raise RuntimeError(f"incomplete or unexpected aliases in {name}")
        if any(re.search(r"\b\d{7}\b", json.dumps(row)) for row in rows):
            raise RuntimeError(f"provider match identifier in {name}")
    manifest = json.loads((OUTPUT_ROOT / "manifest.json").read_text())
    for name, digest in manifest["output_sha256"].items():
        if sha256(OUTPUT_ROOT / name) != digest:
            raise RuntimeError(f"closed output hash mismatch: {name}")
    freeze = json.loads((OUTPUT_ROOT / "population_freeze.json").read_text())
    if freeze["performance_computed"] is not False or freeze["population_sha256"] != manifest["population_sha256"]:
        raise RuntimeError("population freeze integrity failure")
    for name in PUBLIC_FILES:
        text = (OUTPUT_ROOT / name).read_text()
        if "/Users/" in text or "data/session_02" in text:
            raise RuntimeError(f"private path in {name}")
    print("publication check passed")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "run", "finalize-existing", "publication-check"))
    args = parser.parse_args()
    if args.command == "prepare":
        prepare()
    elif args.command == "run":
        run()
    elif args.command == "finalize-existing":
        finalize_existing()
    else:
        publication_check()


if __name__ == "__main__":
    main()
