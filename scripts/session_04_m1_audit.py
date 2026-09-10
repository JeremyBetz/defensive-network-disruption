#!/usr/bin/env python3
"""Session 4 audit of the closed static M1 representation; never fits a model."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import statistics
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import scipy
from scipy.stats import pearsonr, spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defensive_network_disruption.data.receiver_choices import (
    ChoiceSet, active_in_period, clock_microseconds,
)
from defensive_network_disruption.data.skillcorner_session2 import DEVELOPMENT_MATCHES, SOURCE_COMMIT
from defensive_network_disruption.validation.m1_audit import (
    coefficient_summary, fold_change_summary, numerical_nondegenerate,
    ordering_disagreement, quantile_summary, segment_order_statistics, utility,
    within_choice_centered_correlation,
)
from defensive_network_disruption.validation.ranking_features import M1_NAMES, choice_features

AUTHORITY = "3e7e517108a782ede32e7bf55e2dfb020f3c841f"
PROTOCOL = ROOT / "docs/protocols/phase_04_m1_failure_mode_audit.md"
SESSION3 = ROOT / "outputs/receiver_ranking_m0_m1"
POPULATION = SESSION3 / "local/population.jsonl"
DATA_ROOT = ROOT / "data/session_02/data/matches"
OUTPUT_ROOT = ROOT / "outputs/m1_failure_mode_audit"
LOCAL_ROOT = OUTPUT_ROOT / "local"
ALIASES = {item: f"development_{index:02d}" for index, item in enumerate(sorted(DEVELOPMENT_MATCHES, key=int), 1)}
PUBLIC = ("coefficient_summary.json", "feature_summary.json", "geometry_diagnostics.json", "manifest.json")
PROJECTED_EVENT_FIELDS = (
    "event_id", "event_type", "pass_outcome", "period", "time_end", "player_id",
    "player_in_possession_id", "player_targeted_id",
)


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_product(match_id, suffix):
    if match_id not in DEVELOPMENT_MATCHES:
        raise PermissionError("match outside Session 4 development allowlist")
    path = DATA_ROOT / match_id / f"{match_id}_{suffix}"
    resolved_root = DATA_ROOT.resolve()
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(resolved_root):
        raise PermissionError("unsafe or missing governed development path")
    return path


def verify_session3():
    manifest = json.loads((SESSION3 / "manifest.json").read_text())
    if manifest["execution_commit"] != "54dc4f81d29b9532e4e0c41a95d4f33980360891":
        raise RuntimeError("unexpected Session 3 execution identity")
    for name, digest in manifest["output_sha256"].items():
        if sha256(SESSION3 / name) != digest:
            raise RuntimeError(f"closed Session 3 artifact changed: {name}")
    freeze = json.loads((SESSION3 / "population_freeze.json").read_text())
    if sha256(POPULATION) != freeze["population_sha256"]:
        raise RuntimeError("closed Session 3 population changed")
    return manifest, freeze


def preflight():
    if subprocess.run(["git", "merge-base", "--is-ancestor", AUTHORITY, "HEAD"], cwd=ROOT).returncode:
        raise RuntimeError("Session 3 authority is not an ancestor")
    git("ls-files", "--error-unmatch", str(PROTOCOL.relative_to(ROOT)))
    if "Amendment 1" not in PROTOCOL.read_text():
        raise RuntimeError("decision-frame access amendment missing")
    verify_session3()
    for match_id in DEVELOPMENT_MATCHES:
        safe_product(match_id, "match.json")
        safe_product(match_id, "tracking_extrapolated.jsonl")
        safe_product(match_id, "dynamic_events.csv")
    for path in (Path(__file__), ROOT / "src/defensive_network_disruption/validation/m1_audit.py"):
        content = path.read_text()
        forbidden_tokens = ("scipy." + "optimize", "fit_" + "conditional_softmax", "mini" + "mize(")
        for forbidden in forbidden_tokens:
            if forbidden in content:
                raise RuntimeError(f"model-fitting token prohibited in Session 4: {forbidden}")
    print("Session 4 preflight passed")


def load_population():
    grouped = {match_id: [] for match_id in DEVELOPMENT_MATCHES}
    with POPULATION.open() as handle:
        for line in handle:
            item = json.loads(line)
            match_id = item["match_id"]
            if match_id not in grouped:
                raise PermissionError("population includes a prohibited match")
            grouped[match_id].append(ChoiceSet(
                match_id=match_id, event_id=item["event_id"], candidate_ids=tuple(item["candidate_ids"]),
                candidate_xy=tuple(tuple(value) for value in item["candidate_xy"]),
                defender_xy=tuple(tuple(value) for value in item["defender_xy"]),
                carrier_xy=tuple(item["carrier_xy"]), target_index=item["target_index"],
                target_outside=item["target_outside"],
            ))
    return grouped


def projected_events(path, eligible_ids):
    result = {}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        indexes = {name: header.index(name) for name in PROJECTED_EVENT_FIELDS}
        for row in reader:
            event_id = row[indexes["event_id"]]
            if event_id not in eligible_ids:
                continue
            item = {name: row[index] for name, index in indexes.items()}
            if item["event_type"] != "player_possession" or not item["pass_outcome"]:
                raise RuntimeError("closed population event no longer satisfies pass definition")
            if event_id in result:
                raise RuntimeError("duplicate event identity")
            result[event_id] = item
    if set(result) != set(eligible_ids):
        raise RuntimeError("event projection did not resolve the closed population")
    return result


def finite_player_projection(frame):
    result = {}
    for item in frame.get("player_data") or []:
        player_id = str(item.get("player_id") or "")
        x, y = item.get("x"), item.get("y")
        if not player_id or x is None or y is None:
            continue
        if not math.isfinite(float(x)) or not math.isfinite(float(y)):
            continue
        if player_id in result:
            raise RuntimeError("duplicate tracking identity")
        result[player_id] = (float(x), float(y), bool(item.get("is_detected")))
    return result


def tracking_provenance(match_id, choices):
    metadata = json.loads(safe_product(match_id, "match.json").read_text())
    roster = {str(item["id"]): item for item in metadata["players"]}
    events = projected_events(safe_product(match_id, "dynamic_events.csv"), {item.event_id for item in choices})
    requests = {1: [], 2: []}
    for choice in choices:
        event = events[choice.event_id]
        period = int(event["period"])
        requests[period].append((clock_microseconds(event["time_end"]), choice.event_id, event))
    for items in requests.values():
        items.sort()
    indexes = {1: 0, 2: 0}
    previous = {1: None, 2: None}
    before_previous = {1: None, 2: None}
    selected = {}

    def resolve_until(period, current_time):
        items = requests[period]
        while indexes[period] < len(items) and items[indexes[period]][0] <= current_time:
            event_time, event_id, event = items[indexes[period]]
            candidate = previous[period]
            if candidate is None or not 0 < event_time - candidate[0] <= 100_000:
                raise RuntimeError("Session 4 could not reproduce frozen decision timing")
            selected[event_id] = (candidate, before_previous[period], event)
            indexes[period] += 1

    with safe_product(match_id, "tracking_extrapolated.jsonl").open() as handle:
        for line in handle:
            frame = json.loads(line)
            period = frame.get("period")
            if period not in requests:
                continue
            timestamp = clock_microseconds(frame["timestamp"])
            resolve_until(period, timestamp)
            before_previous[period], previous[period] = previous[period], (timestamp, int(frame["frame"]), frame)
    for period in (1, 2):
        resolve_until(period, math.inf)
    if len(selected) != len(choices):
        raise RuntimeError("not every closed choice received a decision frame")

    counts = {
        "decision_states": len(choices), "current_defender_instances": 0,
        "current_detected": 0, "current_extrapolated": 0, "past_available": 0,
        "past_unavailable": 0, "detected_detected": 0, "detected_extrapolated": 0,
        "extrapolated_detected": 0, "extrapolated_extrapolated": 0,
    }
    elapsed = []
    for choice in choices:
        current, prior, event = selected[choice.event_id]
        current_time, frame_id, frame = current
        current_players = finite_player_projection(frame)
        prior_players = finite_player_projection(prior[2]) if prior is not None else {}
        carrier = str(event.get("player_id") or event.get("player_in_possession_id") or "")
        carrier_meta = roster.get(carrier)
        if carrier_meta is None:
            raise RuntimeError("closed choice carrier missing from roster")
        carrier_team = str(carrier_meta.get("team_id"))
        defenders = [
            player_id for player_id, player in roster.items()
            if str(player.get("team_id")) != carrier_team and player_id in current_players
            and active_in_period(player, int(event["period"]), frame_id)
        ]
        if len(defenders) != len(choice.defender_xy):
            raise RuntimeError("defender membership did not reproduce closed choice")
        for defender in defenders:
            counts["current_defender_instances"] += 1
            current_detected = current_players[defender][2]
            counts["current_detected" if current_detected else "current_extrapolated"] += 1
            if prior is None or defender not in prior_players:
                counts["past_unavailable"] += 1
                continue
            delta = current_time - prior[0]
            if delta <= 0:
                raise RuntimeError("non-positive prior-frame interval")
            elapsed.append(delta)
            counts["past_available"] += 1
            prior_detected = prior_players[defender][2]
            key = ("detected" if current_detected else "extrapolated") + "_" + (
                "detected" if prior_detected else "extrapolated"
            )
            counts[key] += 1
    counts["past_availability_rate"] = counts["past_available"] / counts["current_defender_instances"]
    counts["elapsed_microseconds"] = quantile_summary(elapsed)
    return counts


def correlations(matrix):
    first, second = matrix[:, 0], matrix[:, 1]
    return {"pearson": float(pearsonr(first, second).statistic),
            "spearman": float(spearmanr(first, second).statistic)}


def describe_features(grouped):
    per_match = {}
    all_m1 = []
    weighted_sets = []
    weighted_weights = []
    match_disagreements = []
    multiplicity_ok = []
    feature_names = list(M1_NAMES) + ["second_segment_distance", "third_segment_distance",
                                     "second_minus_first", "third_minus_first"]
    for match_id in sorted(grouped, key=int):
        attempt_m1 = []
        attempt_extended = []
        disagreement_values = []
        comparable_pairs = 0
        discordant_pairs = 0
        for choice in grouped[match_id]:
            m1, _ = choice_features(choice, "m1")
            extended = []
            for row, receiver in zip(m1, choice.candidate_xy, strict=True):
                first, second, third = segment_order_statistics(choice.defender_xy, choice.carrier_xy, receiver)
                extended.append([*row, second, third, second - first, third - first])
            extended = np.asarray(extended, dtype=np.float64)
            audit = ordering_disagreement(m1[:, 3], m1[:, 4])
            comparable_pairs += audit["comparable_pairs"]
            discordant_pairs += audit["discordant_pairs"]
            if audit["fraction"] is not None:
                disagreement_values.append(audit["fraction"])
            attempt_m1.append(m1)
            attempt_extended.append(extended)
        flat = np.vstack(attempt_extended)
        raw_defense = flat[:, [3, 4]]
        d2_ok, d2_tolerance = numerical_nondegenerate(flat[:, 7])
        d3_ok, d3_tolerance = numerical_nondegenerate(flat[:, 8])
        alias = ALIASES[match_id]
        per_match[alias] = {
            "attempts": len(attempt_extended), "candidate_connections": len(flat),
            "features": {
                name: {"quantiles": quantile_summary(flat[:, index]), "population_variance": float(np.var(flat[:, index]))}
                for index, name in enumerate(feature_names)
            },
            "defensive_feature_correlation": correlations(raw_defense),
            "pass_length_segment_correlation": correlations(flat[:, [0, 4]]),
            "ordering_disagreement": {
                "equal_attempt_fraction": statistics.fmean(disagreement_values),
                "comparable_pairs": comparable_pairs, "discordant_pairs": discordant_pairs,
            },
            "multiplicity_nondegenerate": {
                "second_gap": d2_ok, "third_gap": d3_ok,
                "second_tolerance": d2_tolerance, "third_tolerance": d3_tolerance,
            },
        }
        all_m1.append(raw_defense)
        match_disagreements.append(per_match[alias]["ordering_disagreement"]["equal_attempt_fraction"])
        multiplicity_ok.append(d2_ok and d3_ok)
        attempt_weight = 1.0 / len(grouped) / len(attempt_m1)
        weighted_sets.extend(attempt_m1)
        weighted_weights.extend([attempt_weight] * len(attempt_m1))
    full_corr, full_condition = within_choice_centered_correlation(weighted_sets, weighted_weights)
    defense_corr, defense_condition = within_choice_centered_correlation(
        [item[:, [3, 4]] for item in weighted_sets], weighted_weights,
    )
    aggregate = {
        "pooled_defensive_feature_correlation": correlations(np.vstack(all_m1)),
        "equal_match_ordering_disagreement": statistics.fmean(match_disagreements),
        "within_choice_centered_defensive_pearson": float(defense_corr[0, 1]),
        "within_choice_condition": {"m1": full_condition, "defensive_features": defense_condition},
        "multiplicity_nondegenerate_all_matches": all(multiplicity_ok),
        "equal_match_feature_summary": {
            name: {
                "mean_match_quantiles": {
                    key: statistics.fmean(item["features"][name]["quantiles"][key] for item in per_match.values())
                    for key in ("q05", "q25", "q50", "q75", "q95")
                },
                "mean_match_population_variance": statistics.fmean(
                    item["features"][name]["population_variance"] for item in per_match.values()
                ),
            }
            for name in feature_names
        },
    }
    return {"schema_version": "1.0.0", "per_match": per_match, "aggregate": aggregate}


def synthetic_diagnostics(qc, multiplicity_nondegenerate, velocity_structurally_available):
    aliases = sorted(qc["folds"])
    params = [qc["folds"][alias]["m1"]["parameters"] for alias in aliases]

    def changes(raw, reference):
        return [utility(raw, item["coefficients"], item["mean"], item["scale"])
                - utility(reference, item["coefficients"], item["mean"], item["scale"])
                for item in params]

    receiver = {str(value): fold_change_summary(changes([40, 40, 0, value, 2], [40, 40, 0, 20, 2]))
                for value in (2, 5, 10, 20, 40)}
    segment = {str(value): fold_change_summary(changes([40, 40, 0, 20, value], [40, 40, 0, 20, 20]))
               for value in (0, 1, 2, 5, 10, 20)}
    anchors = (0, 1, 2, 5, 10, 20, 40)
    joint = {f"receiver_{receiver_value}_segment_{segment_value}": fold_change_summary(
        changes([40, 40, 0, receiver_value, segment_value], [40, 40, 0, 20, 20]))
        for receiver_value in anchors for segment_value in anchors if segment_value <= receiver_value}

    one = SimpleNamespace(carrier_xy=(0.0, 0.0), candidate_xy=((20.0, 0.0),), defender_xy=((15.0, 2.0),))
    many = SimpleNamespace(carrier_xy=(0.0, 0.0), candidate_xy=((20.0, 0.0),),
                           defender_xy=((5.0, 2.0), (10.0, 2.0), (15.0, 2.0)))
    one_features = choice_features(one, "m1")[0][0]
    many_features = choice_features(many, "m1")[0][0]
    multiplicity_collapse = bool(np.array_equal(one_features, many_features))
    multiplicity_utility_equal = all(
        utility(one_features, item["coefficients"], item["mean"], item["scale"])
        == utility(many_features, item["coefficients"], item["mean"], item["scale"])
        for item in params
    )
    short = [5, 5, 0, math.sqrt(29), 2]
    long = [30, 30, 0, math.sqrt(29), 2]
    length_changes = changes(long, short)
    defensive_equal = all(
        utility([0, 0, 0, *short[3:]], item["coefficients"], item["mean"], item["scale"])
        == utility([0, 0, 0, *long[3:]], item["coefficients"], item["mean"], item["scale"])
        for item in params
    )
    velocity_equal = all(
        utility([40, 40, 0, 10, 2], item["coefficients"], item["mean"], item["scale"])
        == utility([40, 40, 0, 10, 2], item["coefficients"], item["mean"], item["scale"])
        for item in params
    )
    monotonic_receiver = all(receiver[str(a)]["median"] <= receiver[str(b)]["median"] for a, b in zip((2, 5, 10, 20), (5, 10, 20, 40)))
    monotonic_segment = all(segment[str(a)]["median"] <= segment[str(b)]["median"] for a, b in zip((0, 1, 2, 5, 10), (1, 2, 5, 10, 20)))
    causal_provider_processing = False
    reachability_a = velocity_equal and velocity_structurally_available and causal_provider_processing
    multi_b = (not reachability_a and multiplicity_collapse and multiplicity_utility_equal
               and multiplicity_nondegenerate)
    decision = "B — SPECIFIC MULTI-DEFENDER FAILURE MODE IDENTIFIED" if multi_b else (
        "A — SPECIFIC REACHABILITY FAILURE MODE IDENTIFIED" if reachability_a else
        "D — NO M2 JUSTIFIED YET"
    )
    return {
        "schema_version": "1.0.0",
        "synthetic": {
            "receiver_pressure_utility_change": receiver,
            "segment_obstruction_utility_change": segment,
            "joint_utility_change": joint,
            "monotonic_receiver_distance": monotonic_receiver,
            "monotonic_segment_distance": monotonic_segment,
            "velocity_toward_away_static_utility_identical": velocity_equal,
            "length_5m_vs_30m_utility_change": fold_change_summary(length_changes),
            "length_case_defensive_component_identical": defensive_equal,
            "one_vs_three_features_identical": multiplicity_collapse,
            "one_vs_three_utility_identical": multiplicity_utility_equal,
        },
        "provider_causal_processing": "NOT ESTABLISHED",
        "backward_velocity_structurally_available": velocity_structurally_available,
        "reachability_status": "algorithmically past-only feasibility; strict causal gate blocked",
        "decision": decision,
        "prospective_m2_family": (
            "one continuous summed-defender attenuation over the finite connection; kernel and scale remain unset"
            if multi_b else None
        ),
        "session_5_question": (
            "Does one prospectively specified continuous multi-defender attenuation summary add receiver-ranking information beyond the frozen M1 minima?"
            if multi_b else "No Session 5 model question is authorized."
        ),
    }


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def audit():
    preflight()
    if (OUTPUT_ROOT / "manifest.json").exists():
        raise RuntimeError("a completed Session 4 audit already exists; rerun prohibited")
    session3_manifest, freeze = verify_session3()
    grouped = load_population()
    feature_summary = describe_features(grouped)
    qc = json.loads((SESSION3 / "qc.json").read_text())
    coefficients = {
        "schema_version": "1.0.0", "source": "closed Session 3 QC parameters",
        "interpretation": "standardized association coefficients; not causal importance",
        "fold_count": 9, "models": coefficient_summary(qc),
    }
    provenance = {ALIASES[match_id]: tracking_provenance(match_id, grouped[match_id])
                  for match_id in sorted(grouped, key=int)}
    feature_summary["tracking_provenance"] = provenance
    count_fields = (
        "decision_states", "current_defender_instances", "current_detected", "current_extrapolated",
        "past_available", "past_unavailable", "detected_detected", "detected_extrapolated",
        "extrapolated_detected", "extrapolated_extrapolated",
    )
    provenance_aggregate = {field: sum(item[field] for item in provenance.values()) for field in count_fields}
    provenance_aggregate["past_availability_rate"] = (
        provenance_aggregate["past_available"] / provenance_aggregate["current_defender_instances"]
    )
    provenance_aggregate["current_detected_rate"] = (
        provenance_aggregate["current_detected"] / provenance_aggregate["current_defender_instances"]
    )
    feature_summary["tracking_provenance_aggregate"] = provenance_aggregate
    geometry = synthetic_diagnostics(
        qc,
        feature_summary["aggregate"]["multiplicity_nondegenerate_all_matches"],
        all(item["past_available"] > 0 for item in provenance.values()),
    )
    # Serialize every public result before writing any of them so type/schema
    # failures cannot leave a result package that looks complete.
    rendered = {
        "coefficient_summary.json": json.dumps(coefficients, indent=2, sort_keys=True, allow_nan=False) + "\n",
        "feature_summary.json": json.dumps(feature_summary, indent=2, sort_keys=True, allow_nan=False) + "\n",
        "geometry_diagnostics.json": json.dumps(geometry, indent=2, sort_keys=True, allow_nan=False) + "\n",
    }
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    LOCAL_ROOT.mkdir(parents=True, exist_ok=True)
    for name, content in rendered.items():
        (OUTPUT_ROOT / name).write_text(content)
    write_json(LOCAL_ROOT / "access_ledger.json", {
        "development_match_ids": sorted(DEVELOPMENT_MATCHES, key=int),
        "products": ["closed_population", "closed_qc", "metadata", "projected_dynamic_event_fields", "tracking"],
        "reserved_access": False, "pose_access": False, "model_fit": False,
    })
    outputs = {name: sha256(OUTPUT_ROOT / name) for name in PUBLIC if name != "manifest.json"}
    manifest = {
        "schema_version": "1.0.0", "authority_commit": AUTHORITY,
        "protocol_commit": git("log", "-1", "--format=%H", "--", str(PROTOCOL.relative_to(ROOT))),
        "source_commit": SOURCE_COMMIT, "protocol_sha256": sha256(PROTOCOL),
        "session3_manifest_sha256": sha256(SESSION3 / "manifest.json"),
        "session3_population_sha256": freeze["population_sha256"],
        "session3_output_sha256": session3_manifest["output_sha256"],
        "environment": {"python": sys.version.split()[0], "numpy": np.__version__, "scipy": scipy.__version__},
        "runner_sha256": sha256(Path(__file__)),
        "helper_sha256": sha256(ROOT / "src/defensive_network_disruption/validation/m1_audit.py"),
        "development_match_aliases": sorted(ALIASES.values()), "output_sha256": outputs,
        "model_fit": False, "model_score": False, "passage_selection": False,
        "reserved_access": False, "pose_access": False,
    }
    write_json(OUTPUT_ROOT / "manifest.json", manifest)
    verify_session3()
    print(json.dumps({"decision": geometry["decision"], "session_5_question": geometry["session_5_question"]}))


def publication_check():
    verify_session3()
    manifest = json.loads((OUTPUT_ROOT / "manifest.json").read_text())
    if manifest["runner_sha256"] != sha256(Path(__file__)):
        raise RuntimeError("Session 4 runner hash mismatch")
    if manifest["helper_sha256"] != sha256(ROOT / "src/defensive_network_disruption/validation/m1_audit.py"):
        raise RuntimeError("Session 4 helper hash mismatch")
    for name, digest in manifest["output_sha256"].items():
        if sha256(OUTPUT_ROOT / name) != digest:
            raise RuntimeError(f"Session 4 output hash mismatch: {name}")
    for name in PUBLIC:
        text = (OUTPUT_ROOT / name).read_text()
        if "/Users/" in text or "data/session_02" in text or re.search(r"\b\d{7}\b", text):
            raise RuntimeError(f"private path or provider identifier in {name}")
        for prohibited in ("player_id", "event_id", "candidate_ids", "timestamp"):
            if prohibited in text:
                raise RuntimeError(f"reconstructive field in {name}: {prohibited}")
    if not all(manifest[key] is False for key in ("model_fit", "model_score", "passage_selection", "reserved_access", "pose_access")):
        raise RuntimeError("Session 4 firewall status failed")
    print("Session 4 publication check passed")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "audit", "publication-check"))
    args = parser.parse_args()
    {"preflight": preflight, "audit": audit, "publication-check": publication_check}[args.command]()


if __name__ == "__main__":
    main()
