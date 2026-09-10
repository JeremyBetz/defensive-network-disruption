#!/usr/bin/env python3
"""Frozen Session 6 development training and one protected evaluation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import platform
import re
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defensive_network_disruption.data.identity_compatibility import ChoiceSet
from defensive_network_disruption.data.session6_population import (
    load_projected_match_session6,
    prepare_match_session6,
    rendered_population,
)
from defensive_network_disruption.data.session6_source import (
    SOURCE_COMMIT,
    acquire_product,
)
from defensive_network_disruption.data.skillcorner_session2 import DEVELOPMENT_MATCHES
from defensive_network_disruption.validation.choice_model import weighted_standardization
from defensive_network_disruption.validation.ranking_features import M0_NAMES, M1_NAMES, choice_features
from defensive_network_disruption.validation.ranking_metrics import expected_credits, match_macro
from defensive_network_disruption.validation.session5 import M2_NAMES, choice_features_m1_m2, fit_with_fail_closed_gate

START = "74ff7b2d29caf1b1f1cb57e3c8770f6f36075849"
PROTOCOL_COMMIT = "903b8a02fdcbff2ef0d2a35a480f6358d8bbd358"
POPULATION_SHA = "cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d"
RESERVED = frozenset({
    "1874553", "1927964", "1959846", "1986691", "1996436",
    "2006363", "2007448", "2007721", "2010085", "2016236",
})
WITHHELD = "1953632"
PROTOCOL = ROOT / "docs/protocols/phase_06_reserved_evaluation.md"
SESSION3 = ROOT / "outputs/receiver_ranking_m0_m1"
SESSION4 = ROOT / "outputs/m1_failure_mode_audit"
SESSION5 = ROOT / "outputs/receiver_ranking_m2"
SESSION6A = ROOT / "outputs/identity_compatibility"
DEV_DATA = ROOT / "data/session_02"
RESERVED_DATA = ROOT / "data/session_06"
OUTPUT = ROOT / "outputs/reserved_evaluation"
LOCAL = OUTPUT / "local"
DEV_REPLAY = LOCAL / "development_replay.jsonl"
RESERVED_POPULATION = LOCAL / "reserved_population.jsonl"
SOURCE_IDENTITIES = LOCAL / "source_identities.json"
ALIAS_MAP = LOCAL / "alias_map.json"
ACCESS_LEDGER = LOCAL / "access_ledger.jsonl"
EXECUTION_MARKER = LOCAL / "execution_state.json"
FINAL_MODELS = OUTPUT / "final_development_models.json"
POPULATION_SUMMARY = OUTPUT / "population_summary.json"
RESULT_FILES = (
    "m0_match_metrics.csv", "m1_match_metrics.csv", "m2_match_metrics.csv",
    "m1_m0_paired.csv", "m2_m1_paired.csv", "aggregate_metrics.json",
    "qc.json", "manifest.json",
)
IMPLEMENTATION_FILES = (
    "scripts/session_06_reserved.py",
    "src/defensive_network_disruption/data/session6_population.py",
    "src/defensive_network_disruption/data/session6_source.py",
    "src/defensive_network_disruption/data/identity_compatibility.py",
    "src/defensive_network_disruption/data/receiver_choices.py",
    "src/defensive_network_disruption/geometry/attenuation.py",
    "src/defensive_network_disruption/geometry/segment.py",
    "src/defensive_network_disruption/validation/choice_model.py",
    "src/defensive_network_disruption/validation/ranking_features.py",
    "src/defensive_network_disruption/validation/ranking_metrics.py",
    "src/defensive_network_disruption/validation/session5.py",
    "tests/test_session6_reserved.py",
)
DEV_ALIASES = {item: f"development_{index:02d}" for index, item in enumerate(sorted(DEVELOPMENT_MATCHES, key=int), 1)}
RESERVED_ALIASES = {item: f"reserved_{index:02d}" for index, item in enumerate(sorted(RESERVED, key=int), 1)}


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def committed_sha(commit: str, relative: str) -> str:
    content = subprocess.run(["git", "show", f"{commit}:{relative}"], cwd=ROOT, check=True, capture_output=True).stdout
    return hashlib.sha256(content).hexdigest()


def json_text(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"


def atomic_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)


def create_execution_marker(path: Path, content: str) -> None:
    """Create the one-run marker with an exclusive filesystem operation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        # The marker intentionally remains after any failure.
        raise


def atomic_csv(path: Path, rows: list[dict], fields: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def append_access(alias: str, product: str, status: str) -> None:
    LOCAL.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "phase": "reserved_structural_preparation",
        "command": "prepare-reserved",
        "protocol_commit": PROTOCOL_COMMIT,
        "implementation_commit": git("rev-parse", "HEAD"),
        "match_alias": RESERVED_ALIASES.get(alias, alias),
        "product": product,
        "status": status,
        "protected_value_access": True,
    }
    with ACCESS_LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True, separators=(",", ":")) + "\n")


def verify_output_manifest(directory: Path) -> None:
    manifest = json.loads((directory / "manifest.json").read_text())
    for name, digest in manifest["output_sha256"].items():
        if sha(directory / name) != digest:
            raise RuntimeError(f"closed artifact changed: {directory.name}/{name}")


def verify_authorities() -> None:
    if git("rev-parse", PROTOCOL_COMMIT) != PROTOCOL_COMMIT:
        raise RuntimeError("Phase 6 protocol commit is unavailable")
    for commit in (
        "5fcef6b8b141d636ca5bcf7c41f9e536dd755f03",
        "3e7e517108a782ede32e7bf55e2dfb020f3c841f",
        "12d78f768ad97a19814e85ef7bc8796cee18d5fa",
        "3cd72c1509bf2ca08d6b41a236b80e065156668d",
        START,
        PROTOCOL_COMMIT,
    ):
        if subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=ROOT).returncode:
            raise RuntimeError(f"closed authority is not an ancestor: {commit}")
    if sha(PROTOCOL) != committed_sha(PROTOCOL_COMMIT, str(PROTOCOL.relative_to(ROOT))):
        raise RuntimeError("Phase 6 protocol changed")
    verify_output_manifest(SESSION3)
    verify_output_manifest(SESSION4)
    verify_output_manifest(SESSION5)
    verify_output_manifest(SESSION6A)
    freeze = json.loads((SESSION3 / "population_freeze.json").read_text())
    authority_population = SESSION3 / "local/population.jsonl"
    if authority_population.is_symlink() or sha(authority_population) != POPULATION_SHA:
        raise RuntimeError("Session 3 population authority changed")
    if freeze["evaluation_eligible"] != 7227 or freeze["fit_eligible"] != 7227:
        raise RuntimeError("Session 3 population totals changed")
    if SOURCE_COMMIT != "02a396ffd09b283c9f092fdedeff11da6d535b66":
        raise RuntimeError("source revision changed")
    if set(DEVELOPMENT_MATCHES) != {
        "1886347", "1899585", "1925299", "1996435", "2006229",
        "2011166", "2013725", "2015213", "2017461",
    } or len(RESERVED) != 10 or WITHHELD in RESERVED:
        raise RuntimeError("partition contract changed")


def safe_local(path: Path, root: Path, *, required: bool = True) -> Path:
    if path.is_symlink() or (required and not path.is_file()):
        raise PermissionError("local artifact is missing or unsafe")
    resolved_root = root.resolve()
    if not path.resolve(strict=False).is_relative_to(resolved_root):
        raise PermissionError("local artifact escapes governed root")
    return path


def preflight() -> None:
    verify_authorities()
    if any(item.exists() for item in (RESERVED_DATA, RESERVED_POPULATION, POPULATION_SUMMARY, EXECUTION_MARKER)):
        raise RuntimeError("reserved access or execution state already exists")
    if any((OUTPUT / name).exists() for name in RESULT_FILES):
        raise RuntimeError("protected result already exists")
    print("Session 6 preflight passed")


def load_population(path: Path, allowlist: frozenset[str]) -> dict[str, list[ChoiceSet]]:
    groups = {match: [] for match in allowlist}
    with safe_local(path, path.parent).open(encoding="utf-8") as handle:
        for line in handle:
            item = json.loads(line)
            match_id = str(item["match_id"])
            if match_id not in groups:
                raise PermissionError("population contains a prohibited match")
            groups[match_id].append(ChoiceSet(
                match_id=match_id,
                event_id=item["event_id"],
                candidate_ids=tuple(item["candidate_ids"]),
                candidate_xy=tuple(tuple(value) for value in item["candidate_xy"]),
                defender_xy=tuple(tuple(value) for value in item["defender_xy"]),
                carrier_xy=tuple(item["carrier_xy"]),
                target_index=item["target_index"],
                target_outside=item["target_outside"],
            ))
    return groups


def verify_development() -> dict:
    verify_authorities()
    freeze = json.loads((SESSION3 / "population_freeze.json").read_text())
    all_choices: list[ChoiceSet] = []
    matches: dict[str, dict] = {}
    for match_id in sorted(DEVELOPMENT_MATCHES, key=int):
        projected = load_projected_match_session6(DEV_DATA, match_id, allowlist=DEVELOPMENT_MATCHES)
        choices, qc, contract = prepare_match_session6(match_id, projected, allowlist=DEVELOPMENT_MATCHES)
        content = rendered_population(choices)
        alias = DEV_ALIASES[match_id]
        expected = freeze["matches"][alias]
        comparisons = {
            "evaluation_eligible": qc["evaluation_eligible"] == expected["evaluation_eligible"],
            "fit_eligible": qc["fit_eligible"] == expected["fit_eligible"],
            "exclusions": qc["exclusions"] == expected["exclusions"],
            "target_outside": qc["target_outside"] == expected["target_outside"],
            "target_outside_reasons": qc["target_outside_reasons"] == expected["target_outside_reasons"],
            "population_sha256": hashlib.sha256(content).hexdigest() == expected["population_sha256"],
        }
        if not all(comparisons.values()):
            raise RuntimeError(f"development replay mismatch: {alias}")
        matches[alias] = {
            "evaluation_eligible": qc["evaluation_eligible"],
            "fit_eligible": qc["fit_eligible"],
            "population_sha256": hashlib.sha256(content).hexdigest(),
            "authority_match": comparisons,
            "contract": contract,
        }
        all_choices.extend(choices)
    replay = rendered_population(all_choices)
    authority = (SESSION3 / "local/population.jsonl").read_bytes()
    if replay != authority or hashlib.sha256(replay).hexdigest() != POPULATION_SHA:
        raise RuntimeError("combined development replay mismatch")
    atomic_text(DEV_REPLAY, replay.decode())
    result = {
        "evaluation_eligible": sum(item["evaluation_eligible"] for item in matches.values()),
        "fit_eligible": sum(item["fit_eligible"] for item in matches.values()),
        "population_sha256": hashlib.sha256(replay).hexdigest(),
        "byte_equal": replay == authority,
        "matches": matches,
    }
    atomic_text(LOCAL / "development_replay_qc.json", json_text(result))
    print(json.dumps({key: result[key] for key in ("evaluation_eligible", "fit_eligible", "population_sha256", "byte_equal")}))
    return result


def raw_features(groups: dict[str, list[ChoiceSet]]) -> dict[str, dict[str, list[np.ndarray]]]:
    result = {model: {} for model in ("m0", "m1", "m2")}
    for match in sorted(groups):
        result["m0"][match], result["m1"][match], result["m2"][match] = [], [], []
        for choice in groups[match]:
            m1, m2, _ = choice_features_m1_m2(choice)
            m0, _ = choice_features(choice, "m0")
            if not np.array_equal(m0, m1[:, :3]) or not np.array_equal(m1, m2[:, :5]):
                raise RuntimeError("raw feature nesting failed")
            result["m0"][match].append(m0)
            result["m1"][match].append(m1)
            result["m2"][match].append(m2)
    return result


def fit_final_models(groups: dict[str, list[ChoiceSet]]) -> tuple[dict, dict]:
    if set(groups) != set(DEVELOPMENT_MATCHES):
        raise RuntimeError("final fitting requires exactly nine development matches")
    fit_groups = {
        match: [choice for choice in choices if choice.target_index is not None]
        for match, choices in groups.items()
    }
    if any(len(fit_groups[match]) != len(groups[match]) for match in groups):
        raise RuntimeError("authoritative development population unexpectedly contains evaluation-only observations")
    features = raw_features(fit_groups)
    targets = {match: [choice.target_index for choice in fit_groups[match]] for match in fit_groups}
    models: dict[str, dict] = {}
    transformed: dict[str, dict[str, list[np.ndarray]]] = {}
    for model, names in (("m0", M0_NAMES), ("m1", M1_NAMES), ("m2", M2_NAMES)):
        mean, scale, zero = weighted_standardization(features[model])
        if np.any(zero):
            raise RuntimeError(f"zero-variance development column: {model}")
        transformed[model] = {
            match: [(matrix - mean) / scale for matrix in rows]
            for match, rows in features[model].items()
        }
        beta, fit_qc = fit_with_fail_closed_gate(transformed[model], targets)
        models[model] = {
            "feature_names": list(names),
            "mean": mean.tolist(), "scale": scale.tolist(),
            "coefficients": beta.tolist(), "fit_qc": fit_qc,
            "training_match_count": 9,
            "training_evaluation_eligible": sum(len(rows) for rows in groups.values()),
            "training_fit_eligible": sum(len(rows) for rows in fit_groups.values()),
        }
    for left, right, count in (("m0", "m1", 3), ("m1", "m2", 5)):
        if models[left]["mean"] != models[right]["mean"][:count] or models[left]["scale"] != models[right]["scale"][:count]:
            raise RuntimeError("nested preprocessing is not exact")
        for match in transformed[left]:
            for a, b in zip(transformed[left][match], transformed[right][match], strict=True):
                if not np.array_equal(a, b[:, :count]):
                    raise RuntimeError("standardized nesting is not exact")
    return models, {"raw_nesting": True, "preprocessing_nesting": True, "standardized_nesting": True}


def implementation_hashes() -> dict[str, str]:
    return {path: sha(ROOT / path) for path in IMPLEMENTATION_FILES}


def train_final() -> None:
    preflight()
    if FINAL_MODELS.exists():
        raise RuntimeError("final development model authority already exists")
    replay = verify_development()
    groups = load_population(SESSION3 / "local/population.jsonl", DEVELOPMENT_MATCHES)
    models, nesting = fit_final_models(groups)
    artifact = {
        "schema_version": "1.0.0",
        "performance_computed": False,
        "source_commit": SOURCE_COMMIT,
        "protocol_commit": PROTOCOL_COMMIT,
        "protocol_sha256": sha(PROTOCOL),
        "starting_authority": START,
        "development_population": {
            "evaluation_eligible": replay["evaluation_eligible"],
            "fit_eligible": replay["fit_eligible"],
            "population_sha256": replay["population_sha256"],
            "byte_equal_session3": replay["byte_equal"],
        },
        "model_class": "unregularized conditional softmax",
        "objective_weighting": "equal match then attempt",
        "preprocessing_weighting": "equal match then attempt then candidate",
        "optimizer": {"method": "L-BFGS-B", "maxiter": 2000, "maxls": 50, "ftol": 1e-12, "gtol": 1e-8},
        "nesting": nesting,
        "models": models,
        "implementation_sha256": implementation_hashes(),
        "environment": {
            "python": platform.python_version(), "platform": platform.platform(),
            "numpy": np.__version__, "scipy": scipy.__version__,
            "uv_lock_sha256": sha(ROOT / "uv.lock"),
        },
    }
    atomic_text(FINAL_MODELS, json_text(artifact))
    print(json.dumps({"models": list(models), "development_fit_eligible": replay["fit_eligible"], "nesting": nesting}))


def require_committed(path: Path) -> str:
    relative = str(path.relative_to(ROOT))
    git("ls-files", "--error-unmatch", relative)
    if sha(path) != committed_sha("HEAD", relative):
        raise RuntimeError(f"artifact is not intact at HEAD: {relative}")
    return sha(path)


def verify_final_authority() -> dict:
    verify_authorities()
    require_committed(FINAL_MODELS)
    artifact = json.loads(FINAL_MODELS.read_text())
    if (
        artifact.get("schema_version") != "1.0.0"
        or artifact.get("performance_computed") is not False
        or artifact.get("source_commit") != SOURCE_COMMIT
        or artifact.get("protocol_commit") != PROTOCOL_COMMIT
        or artifact.get("development_population", {}).get("population_sha256") != POPULATION_SHA
        or artifact.get("development_population", {}).get("evaluation_eligible") != 7227
        or artifact.get("development_population", {}).get("fit_eligible") != 7227
    ):
        raise RuntimeError("final development authority invalid")
    expected_names = {"m0": list(M0_NAMES), "m1": list(M1_NAMES), "m2": list(M2_NAMES)}
    if set(artifact.get("models", {})) != set(expected_names):
        raise RuntimeError("final development model set invalid")
    for model, names in expected_names.items():
        authority = artifact["models"][model]
        if authority.get("feature_names") != names:
            raise RuntimeError(f"final feature authority invalid: {model}")
        arrays = (authority.get("mean"), authority.get("scale"), authority.get("coefficients"))
        if any(not isinstance(values, list) or len(values) != len(names) for values in arrays):
            raise RuntimeError(f"final parameter shape invalid: {model}")
        if not all(math.isfinite(float(value)) for values in arrays for value in values):
            raise RuntimeError(f"nonfinite final parameter: {model}")
        if any(float(value) <= 0 for value in authority["scale"]):
            raise RuntimeError(f"invalid final preprocessing scale: {model}")
        fit_qc = authority.get("fit_qc", {})
        if (
            fit_qc.get("rank") != len(names)
            or fit_qc.get("columns") != len(names)
            or fit_qc.get("complete_separation") is not False
            or fit_qc.get("quasi_separation") is not False
            or fit_qc.get("complete_solver_status") not in {0, 2}
            or fit_qc.get("quasi_solver_status") != 0
            or not math.isfinite(float(fit_qc.get("objective", math.inf)))
            or float(fit_qc.get("max_abs_gradient", math.inf)) > 1e-6
            or not isinstance(fit_qc.get("iterations"), int)
            or fit_qc["iterations"] < 0
        ):
            raise RuntimeError(f"final fitting gate invalid: {model}")
    if (
        artifact["models"]["m0"]["mean"] != artifact["models"]["m1"]["mean"][:3]
        or artifact["models"]["m0"]["scale"] != artifact["models"]["m1"]["scale"][:3]
        or artifact["models"]["m1"]["mean"] != artifact["models"]["m2"]["mean"][:5]
        or artifact["models"]["m1"]["scale"] != artifact["models"]["m2"]["scale"][:5]
    ):
        raise RuntimeError("final model preprocessing nesting invalid")
    if artifact["implementation_sha256"] != implementation_hashes():
        raise RuntimeError("Session 6 implementation changed after final training")
    expected_environment = {
        "python": platform.python_version(), "platform": platform.platform(),
        "numpy": np.__version__, "scipy": scipy.__version__,
        "uv_lock_sha256": sha(ROOT / "uv.lock"),
    }
    if artifact.get("environment") != expected_environment:
        raise RuntimeError("frozen Session 6 environment changed")
    if git("status", "--porcelain"):
        raise RuntimeError("committed final authority requires a clean tree")
    return artifact


def summarize_counts(values: list[int]) -> dict[str, float | int]:
    if not values:
        return {"count": 0, "minimum": 0, "median": 0.0, "mean": 0.0, "maximum": 0}
    return {
        "count": len(values), "minimum": min(values),
        "median": statistics.median(values), "mean": sum(values) / len(values),
        "maximum": max(values),
    }


def github_token() -> str:
    token = subprocess.run(["gh", "auth", "token"], check=True, capture_output=True, text=True).stdout.strip()
    if not token:
        raise RuntimeError("GitHub authentication token unavailable")
    return token


def prepare_reserved() -> None:
    models = verify_final_authority()
    if RESERVED_DATA.exists() or RESERVED_POPULATION.exists() or POPULATION_SUMMARY.exists():
        raise RuntimeError("reserved preparation already started")
    if any((OUTPUT / name).exists() for name in RESULT_FILES) or EXECUTION_MARKER.exists():
        raise RuntimeError("protected execution already exists")
    token = github_token()
    identities: dict[str, dict] = {}
    for match in sorted(RESERVED, key=int):
        alias = RESERVED_ALIASES[match]
        identities[alias] = {}
        for product in ("metadata", "events", "tracking"):
            identities[alias][product] = acquire_product(
                RESERVED_DATA, match, product, RESERVED, token,
                access_hook=append_access,
            )
    atomic_text(SOURCE_IDENTITIES, json_text(identities))
    atomic_text(ALIAS_MAP, json_text(RESERVED_ALIASES))

    all_choices: list[ChoiceSet] = []
    all_candidate_counts: list[int] = []
    matches: dict[str, dict] = {}
    for match in sorted(RESERVED, key=int):
        alias = RESERVED_ALIASES[match]
        projected = load_projected_match_session6(RESERVED_DATA, match, allowlist=RESERVED)
        choices, qc, contract = prepare_match_session6(match, projected, allowlist=RESERVED)
        if not choices:
            raise RuntimeError(f"reserved match has no evaluation observations: {alias}")
        content = rendered_population(choices)
        matches[alias] = {
            "raw_pass_attempts": qc["raw_pass_attempts"],
            "evaluation_eligible": qc["evaluation_eligible"],
            "fit_eligible": qc["fit_eligible"],
            "exclusions": qc["exclusions"],
            "target_outside": qc["target_outside"],
            "target_outside_reasons": qc["target_outside_reasons"],
            "target_qc": qc["target_qc"],
            "carrier_qc": qc["carrier_qc"],
            "candidate_count_summary": summarize_counts(qc["candidate_counts"]),
            "defender_count_summary": summarize_counts(qc["defender_counts"]),
            "population_sha256": hashlib.sha256(content).hexdigest(),
            "input_contract": contract,
        }
        all_candidate_counts.extend(qc["candidate_counts"])
        all_choices.extend(choices)
    population = rendered_population(all_choices)
    atomic_text(RESERVED_POPULATION, population.decode())
    aggregate_exclusions = {
        name: sum(item["exclusions"][name] for item in matches.values())
        for name in next(iter(matches.values()))["exclusions"]
    }
    aggregate_target_qc = {
        name: sum(item["target_qc"][name] for item in matches.values())
        for name in next(iter(matches.values()))["target_qc"]
    }
    aggregate_carrier_qc = {
        name: sum(item["carrier_qc"][name] for item in matches.values())
        for name in next(iter(matches.values()))["carrier_qc"]
    }
    summary = {
        "schema_version": "1.0.0", "performance_computed": False,
        "reservation": "Prospectively reserved from this project stage forward. Session 1 schema inventory mechanically over-read post-header bytes into process memory, but no evidence indicates value-level content was surfaced, persisted, or used analytically.",
        "source_commit": SOURCE_COMMIT, "reserved_match_count": 10,
        "reserved_aliases": sorted(RESERVED_ALIASES.values()),
        "products": ["metadata", "Dynamic Events", "extrapolated tracking"],
        "source_integrity": {"ordinary_git_objects_verified": 20, "lfs_pointer_objects_verified": 10, "lfs_payloads_verified": 10},
        "raw_pass_attempts": sum(item["raw_pass_attempts"] for item in matches.values()),
        "evaluation_eligible": sum(item["evaluation_eligible"] for item in matches.values()),
        "fit_eligible": sum(item["fit_eligible"] for item in matches.values()),
        "exclusions": aggregate_exclusions,
        "target_qc": aggregate_target_qc,
        "carrier_qc": aggregate_carrier_qc,
        "target_outside": sum(item["target_outside"] for item in matches.values()),
        "target_outside_reasons": {
            reason: sum(item["target_outside_reasons"].get(reason, 0) for item in matches.values())
            for reason in sorted({reason for item in matches.values() for reason in item["target_outside_reasons"]})
        },
        "candidate_count_summary": summarize_counts(all_candidate_counts),
        "population_sha256": hashlib.sha256(population).hexdigest(),
        "final_development_models_sha256": sha(FINAL_MODELS),
        "implementation_commit": git("rev-parse", "HEAD"),
        "matches": matches,
    }
    atomic_text(POPULATION_SUMMARY, json_text(summary))
    print(json.dumps({key: summary[key] for key in ("raw_pass_attempts", "evaluation_eligible", "fit_eligible", "target_outside", "population_sha256")}))


def validate_population_authority() -> tuple[dict, dict]:
    models = verify_final_authority()
    require_committed(POPULATION_SUMMARY)
    summary = json.loads(POPULATION_SUMMARY.read_text())
    if (
        summary.get("schema_version") != "1.0.0"
        or summary.get("performance_computed") is not False
        or summary.get("source_commit") != SOURCE_COMMIT
        or summary.get("reserved_match_count") != 10
        or summary.get("final_development_models_sha256") != sha(FINAL_MODELS)
        or summary.get("implementation_commit")
        != git("log", "-1", "--format=%H", "--", str(FINAL_MODELS.relative_to(ROOT)))
    ):
        raise RuntimeError("reserved structural authority invalid")
    if sha(RESERVED_POPULATION) != summary["population_sha256"]:
        raise RuntimeError("reserved population hash mismatch")
    if (
        set(summary.get("reserved_aliases", [])) != set(RESERVED_ALIASES.values())
        or set(summary.get("matches", {})) != set(RESERVED_ALIASES.values())
        or summary.get("evaluation_eligible", 0) <= 0
        or summary.get("evaluation_eligible")
        != sum(item["evaluation_eligible"] for item in summary["matches"].values())
        or summary.get("fit_eligible")
        != sum(item["fit_eligible"] for item in summary["matches"].values())
        or summary.get("target_outside")
        != sum(item["target_outside"] for item in summary["matches"].values())
    ):
        raise RuntimeError("reserved structural coverage invalid")
    for alias, item in summary["matches"].items():
        if item["evaluation_eligible"] <= 0 or item["fit_eligible"] > item["evaluation_eligible"]:
            raise RuntimeError(f"reserved match eligibility invalid: {alias}")
    return models, summary


def metric_row(alias: str, credits: list[dict], fit_eligible: int, target_outside: int) -> dict:
    return {
        "match_alias": alias, "evaluation_eligible": len(credits),
        "fit_eligible": fit_eligible, "target_outside_zero_credit": target_outside,
        "mrr": sum(item["rr"] for item in credits) / len(credits),
        "hit_at_1": sum(item["hit1"] for item in credits) / len(credits),
        "hit_at_3": sum(item["hit3"] for item in credits) / len(credits),
        "tied_target_blocks": sum(item["tied"] for item in credits),
    }


def paired_summary(rows: list[dict], difference: str) -> dict:
    values = [row[difference] for row in rows]
    return {
        "mean": sum(values) / len(values), "median": statistics.median(values),
        "positive": sum(value > 0 for value in values),
        "negative": sum(value < 0 for value in values),
        "zero": sum(value == 0 for value in values),
    }


def validate_result_contents(summary: dict) -> None:
    aliases = sorted(RESERVED_ALIASES.values())
    metrics: dict[str, dict[str, dict[str, float | int | str]]] = {}
    metric_fields = {
        "match_alias", "evaluation_eligible", "fit_eligible",
        "target_outside_zero_credit", "mrr", "hit_at_1", "hit_at_3",
        "tied_target_blocks",
    }
    for model in ("m0", "m1", "m2"):
        rows = read_csv_rows(OUTPUT / f"{model}_match_metrics.csv")
        if len(rows) != 10 or set(rows[0]) != metric_fields or [row["match_alias"] for row in rows] != aliases:
            raise RuntimeError(f"metric schema or alias order invalid: {model}")
        metrics[model] = {}
        for row in rows:
            alias = row["match_alias"]
            authority = summary["matches"][alias]
            integers = {
                "evaluation_eligible": int(row["evaluation_eligible"]),
                "fit_eligible": int(row["fit_eligible"]),
                "target_outside_zero_credit": int(row["target_outside_zero_credit"]),
                "tied_target_blocks": int(row["tied_target_blocks"]),
            }
            if (
                integers["evaluation_eligible"] != authority["evaluation_eligible"]
                or integers["fit_eligible"] != authority["fit_eligible"]
                or integers["target_outside_zero_credit"] != authority["target_outside"]
                or integers["tied_target_blocks"] < 0
            ):
                raise RuntimeError(f"metric denominator or tie count invalid: {model}/{alias}")
            values = {field: float(row[field]) for field in ("mrr", "hit_at_1", "hit_at_3")}
            if any(not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in values.values()):
                raise RuntimeError(f"metric value invalid: {model}/{alias}")
            metrics[model][alias] = {**integers, **values, "match_alias": alias}

    pair_specs = (
        ("m1_m0_paired.csv", "m0", "m1", "m1_minus_m0"),
        ("m2_m1_paired.csv", "m1", "m2", "m2_minus_m1"),
    )
    paired_rows: dict[str, list[dict[str, float | str]]] = {}
    for filename, left, right, prefix in pair_specs:
        rows = read_csv_rows(OUTPUT / filename)
        expected_fields = {
            "match_alias", f"{left}_mrr", f"{right}_mrr", f"{prefix}_mrr",
            f"{prefix}_hit_at_1", f"{prefix}_hit_at_3",
        }
        if len(rows) != 10 or set(rows[0]) != expected_fields or [row["match_alias"] for row in rows] != aliases:
            raise RuntimeError(f"paired schema or alias order invalid: {filename}")
        converted = []
        for row in rows:
            alias = row["match_alias"]
            numeric = {field: float(value) for field, value in row.items() if field != "match_alias"}
            expected = {
                f"{left}_mrr": metrics[left][alias]["mrr"],
                f"{right}_mrr": metrics[right][alias]["mrr"],
                f"{prefix}_mrr": metrics[right][alias]["mrr"] - metrics[left][alias]["mrr"],
                f"{prefix}_hit_at_1": metrics[right][alias]["hit_at_1"] - metrics[left][alias]["hit_at_1"],
                f"{prefix}_hit_at_3": metrics[right][alias]["hit_at_3"] - metrics[left][alias]["hit_at_3"],
            }
            if numeric != expected or any(not math.isfinite(value) for value in numeric.values()):
                raise RuntimeError(f"paired values invalid: {filename}/{alias}")
            converted.append({"match_alias": alias, **numeric})
        paired_rows[prefix] = converted

    aggregate = json.loads((OUTPUT / "aggregate_metrics.json").read_text())
    expected_models = {
        model: {
            field: sum(float(metrics[model][alias][field]) for alias in aliases) / len(aliases)
            for field in ("mrr", "hit_at_1", "hit_at_3")
        }
        for model in ("m0", "m1", "m2")
    }
    if aggregate.get("models") != expected_models:
        raise RuntimeError("aggregate model metrics are inconsistent")
    for left, right, prefix in (("m0", "m1", "m1_minus_m0"), ("m1", "m2", "m2_minus_m1")):
        expected_difference = {
            field: expected_models[right][field] - expected_models[left][field]
            for field in ("mrr", "hit_at_1", "hit_at_3")
        }
        if aggregate.get(prefix) != expected_difference:
            raise RuntimeError(f"aggregate difference is inconsistent: {prefix}")
        if aggregate.get(f"paired_{prefix}_mrr") != paired_summary(paired_rows[prefix], f"{prefix}_mrr"):
            raise RuntimeError(f"paired summary is inconsistent: {prefix}")

    qc = json.loads((OUTPUT / "qc.json").read_text())
    if (
        qc.get("reserved_match_count") != 10
        or qc.get("evaluation_eligible") != summary["evaluation_eligible"]
        or qc.get("fit_eligible") != summary["fit_eligible"]
        or qc.get("target_outside_zero_credit") != summary["target_outside"]
        or qc.get("identical_model_populations") is not True
        or qc.get("reserved_fitting") is not False
        or qc.get("post_access_tuning") is not False
    ):
        raise RuntimeError("protected result QC is inconsistent")


def score() -> None:
    verify_authorities()
    models, summary = validate_population_authority()
    if git("status", "--porcelain"):
        raise RuntimeError("protected scoring requires a clean committed tree")
    if EXECUTION_MARKER.exists() or any((OUTPUT / name).exists() for name in RESULT_FILES):
        raise RuntimeError("protected scoring has already started")
    for path, digest in models["implementation_sha256"].items():
        if sha(ROOT / path) != digest:
            raise RuntimeError("frozen implementation changed")
    groups = load_population(RESERVED_POPULATION, RESERVED)
    if set(groups) != set(RESERVED) or any(not rows for rows in groups.values()):
        raise RuntimeError("protected scoring requires ten nonempty matches")
    features = raw_features(groups)
    if sum(len(rows) for rows in groups.values()) != summary["evaluation_eligible"]:
        raise RuntimeError("reserved evaluation denominator mismatch")
    create_execution_marker(EXECUTION_MARKER, json_text({
        "status": "started", "timestamp": datetime.now(timezone.utc).isoformat(),
        "population_sha256": sha(RESERVED_POPULATION),
        "implementation_commit": git("rev-parse", "HEAD"),
    }))

    rows_by_model: dict[str, list[dict]] = {model: [] for model in ("m0", "m1", "m2")}
    for model in ("m0", "m1", "m2"):
        model_authority = models["models"][model]
        mean = np.asarray(model_authority["mean"], dtype=np.float64)
        scale = np.asarray(model_authority["scale"], dtype=np.float64)
        beta = np.asarray(model_authority["coefficients"], dtype=np.float64)
        for match in sorted(RESERVED, key=int):
            credits = [
                expected_credits(((matrix - mean) / scale) @ beta, choice.target_index)
                for matrix, choice in zip(features[model][match], groups[match], strict=True)
            ]
            alias = RESERVED_ALIASES[match]
            item = summary["matches"][alias]
            rows_by_model[model].append(metric_row(alias, credits, item["fit_eligible"], item["target_outside"]))

    metric_fields = (
        "match_alias", "evaluation_eligible", "fit_eligible",
        "target_outside_zero_credit", "mrr", "hit_at_1", "hit_at_3",
        "tied_target_blocks",
    )
    for model in ("m0", "m1", "m2"):
        atomic_csv(OUTPUT / f"{model}_match_metrics.csv", rows_by_model[model], metric_fields)
    paired_m1 = [{
        "match_alias": left["match_alias"], "m0_mrr": left["mrr"],
        "m1_mrr": right["mrr"], "m1_minus_m0_mrr": right["mrr"] - left["mrr"],
        "m1_minus_m0_hit_at_1": right["hit_at_1"] - left["hit_at_1"],
        "m1_minus_m0_hit_at_3": right["hit_at_3"] - left["hit_at_3"],
    } for left, right in zip(rows_by_model["m0"], rows_by_model["m1"], strict=True)]
    paired_m2 = [{
        "match_alias": left["match_alias"], "m1_mrr": left["mrr"],
        "m2_mrr": right["mrr"], "m2_minus_m1_mrr": right["mrr"] - left["mrr"],
        "m2_minus_m1_hit_at_1": right["hit_at_1"] - left["hit_at_1"],
        "m2_minus_m1_hit_at_3": right["hit_at_3"] - left["hit_at_3"],
    } for left, right in zip(rows_by_model["m1"], rows_by_model["m2"], strict=True)]
    atomic_csv(OUTPUT / "m1_m0_paired.csv", paired_m1, tuple(paired_m1[0]))
    atomic_csv(OUTPUT / "m2_m1_paired.csv", paired_m2, tuple(paired_m2[0]))
    aggregate_models = {
        model: {field: match_macro({row["match_alias"]: row for row in rows}, field) for field in ("mrr", "hit_at_1", "hit_at_3")}
        for model, rows in rows_by_model.items()
    }
    aggregate = {
        "schema_version": "1.0.0", "headline_weighting": "equal mean across ten reserved matches",
        "models": aggregate_models,
        "m1_minus_m0": {
            field: aggregate_models["m1"][field] - aggregate_models["m0"][field]
            for field in ("mrr", "hit_at_1", "hit_at_3")
        },
        "m2_minus_m1": {
            field: aggregate_models["m2"][field] - aggregate_models["m1"][field]
            for field in ("mrr", "hit_at_1", "hit_at_3")
        },
        "paired_m1_minus_m0_mrr": paired_summary(paired_m1, "m1_minus_m0_mrr"),
        "paired_m2_minus_m1_mrr": paired_summary(paired_m2, "m2_minus_m1_mrr"),
    }
    atomic_text(OUTPUT / "aggregate_metrics.json", json_text(aggregate))
    qc = {
        "schema_version": "1.0.0", "reserved_match_count": 10,
        "evaluation_eligible": summary["evaluation_eligible"],
        "fit_eligible": summary["fit_eligible"],
        "target_outside_zero_credit": summary["target_outside"],
        "identical_model_populations": all(
            [row["evaluation_eligible"] for row in rows_by_model[model]]
            == [row["evaluation_eligible"] for row in rows_by_model["m0"]]
            for model in ("m1", "m2")
        ),
        "tie_policy": {"absolute_tolerance": 1e-12, "block_reference": "highest score in block", "expected_credit": True},
        "tied_target_blocks": {model: sum(row["tied_target_blocks"] for row in rows) for model, rows in rows_by_model.items()},
        "reserved_fitting": False, "post_access_tuning": False,
        "pose_or_orientation_access": False, "network_or_gnn_work": False,
        "scored_passage_inspection": False,
    }
    atomic_text(OUTPUT / "qc.json", json_text(qc))
    validate_result_contents(summary)
    output_hashes = {name: sha(OUTPUT / name) for name in RESULT_FILES if name != "manifest.json"}
    manifest = {
        "schema_version": "1.0.0", "status": "closed",
        "source_commit": SOURCE_COMMIT, "starting_authority": START,
        "protocol_commit": PROTOCOL_COMMIT, "protocol_sha256": sha(PROTOCOL),
        "implementation_commit": summary["implementation_commit"],
        "reserved_population_commit": git("log", "-1", "--format=%H", "--", str(POPULATION_SUMMARY.relative_to(ROOT))),
        "implementation_sha256": models["implementation_sha256"],
        "environment": models["environment"],
        "development_population_sha256": POPULATION_SHA,
        "final_development_models_sha256": sha(FINAL_MODELS),
        "population_summary_sha256": sha(POPULATION_SUMMARY),
        "reserved_population_sha256": sha(RESERVED_POPULATION),
        "reserved_match_aliases": sorted(RESERVED_ALIASES.values()),
        "model_features": {model: models["models"][model]["feature_names"] for model in ("m0", "m1", "m2")},
        "metrics": ["mrr", "hit_at_1", "hit_at_3"],
        "output_sha256": output_hashes,
    }
    atomic_text(OUTPUT / "manifest.json", json_text(manifest))
    atomic_text(EXECUTION_MARKER, json_text({
        "status": "closed", "timestamp": datetime.now(timezone.utc).isoformat(),
        "manifest_sha256": sha(OUTPUT / "manifest.json"),
    }))
    print(json.dumps({
        "m0_mrr": aggregate_models["m0"]["mrr"],
        "m1_mrr": aggregate_models["m1"]["mrr"],
        "m1_minus_m0": aggregate["m1_minus_m0"]["mrr"],
        "m2_mrr": aggregate_models["m2"]["mrr"],
        "m2_minus_m1": aggregate["m2_minus_m1"]["mrr"],
    }))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def publication_check() -> None:
    verify_authorities()
    models = json.loads(FINAL_MODELS.read_text())
    population = json.loads(POPULATION_SUMMARY.read_text()) if POPULATION_SUMMARY.exists() else None
    if models["schema_version"] != "1.0.0" or models["performance_computed"] is not False:
        raise RuntimeError("final model schema invalid")
    if population is not None:
        if population["schema_version"] != "1.0.0" or population["performance_computed"] is not False:
            raise RuntimeError("population summary schema invalid")
        if set(population["matches"]) != set(RESERVED_ALIASES.values()):
            raise RuntimeError("population alias coverage invalid")
    if (OUTPUT / "manifest.json").exists():
        manifest = json.loads((OUTPUT / "manifest.json").read_text())
        if manifest["status"] != "closed" or set(manifest["reserved_match_aliases"]) != set(RESERVED_ALIASES.values()):
            raise RuntimeError("result manifest invalid")
        for name, digest in manifest["output_sha256"].items():
            if sha(OUTPUT / name) != digest:
                raise RuntimeError(f"closed result hash mismatch: {name}")
        if population is None or manifest.get("population_summary_sha256") != sha(POPULATION_SUMMARY):
            raise RuntimeError("result manifest does not bind the structural authority")
        validate_result_contents(population)
    public = [path for path in OUTPUT.glob("*") if path.is_file()]
    prohibited = re.compile(
        r"(?i)(candidate_ids|candidate_xy|defender_xy|carrier_xy|timestamp\s*[:=]|"
        r"/users/|data/session_0[26]|\b(?:1874553|1927964|1959846|1986691|1996436|"
        r"2006363|2007448|2007721|2010085|2016236|1953632)\b)"
    )
    for path in public:
        if prohibited.search(path.read_text()):
            raise RuntimeError(f"publication guard rejected {path.name}")
    if git("status", "--porcelain", "--", "data/session_02", "outputs/receiver_ranking_m0_m1/local"):
        raise RuntimeError("closed development data or population changed")
    print("Session 6 publication check passed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=(
        "preflight", "verify-development", "train-final", "prepare-reserved",
        "score", "publication-check",
    ))
    command = parser.parse_args().command
    functions = {
        "preflight": preflight,
        "verify-development": verify_development,
        "train-final": train_final,
        "prepare-reserved": prepare_reserved,
        "score": score,
        "publication-check": publication_check,
    }
    functions[command]()


if __name__ == "__main__":
    main()
