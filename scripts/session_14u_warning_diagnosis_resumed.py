#!/usr/bin/env python3
"""Strict prepared-byte repair and resumed one-edge warning diagnosis."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import scipy

from defensive_network_disruption.data.prepared_equivalence_gate import require_historical_prepared_bytes
from defensive_network_disruption.data.representation_projection import project_line
from defensive_network_disruption.geometry import production_verification as production
from defensive_network_disruption.geometry.max_warning_diagnosis import (
    WarningLocated, continuity_diagnostic, controlled_diagnostic, locate_warning,
    maximum_function, method_diagnostic, width_summary,
)
from defensive_network_disruption.geometry.occlusion_fields import CANDIDATES
from defensive_network_disruption.geometry.representation_study import evaluate_edge


START = "ed411671920163ec302f3a8cb92a19b8f42ba576"
TAG = "f00690c05d8c1c6db308a65bd311c43f9a8ef2fa"
PROTOCOL = Path("docs/protocols/phase_14u_equivalence_gate_repair.md")
OUT = Path("outputs/continuous_occlusion_warning_diagnosis_resumed")
LOCAL = OUT / "local"
R14R = Path("outputs/continuous_occlusion_retry")
R14S = Path("outputs/continuous_occlusion_max_warning_diagnosis")
R14T = Path("outputs/continuous_occlusion_row_equivalence")
POPULATION = Path("outputs/receiver_ranking_m0_m1/local/population.jsonl")
PREPARED = R14R / "local/prepared.jsonl"
EXPECTED = {
    "session14r_manifest": "8a639f7a2b29a6aec026e176d80d8901b28839b0d2091dd0256751d77b6f70ed",
    "session14s_manifest": "9bdb96a97e447f834068ca941453d537082a91fcb9653fef1c428ddadc78a61b",
    "session14t_manifest": "0228ea02567606634c0e6dac3c0004145aa15939e6085c102abe9c07637dc118",
    "canonical_population": "cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d",
    "prepared_population": "15a809060f0ba4a8cb3790011dab8008db3dad6e931c287ccb395f61ef1530b0",
}
CODE = (
    Path("scripts/session_14u_warning_diagnosis_resumed.py"),
    Path("src/defensive_network_disruption/data/prepared_equivalence_gate.py"),
    Path("tests/test_session14u_equivalence_repair.py"),
)
PUBLIC = ("equivalence_repair.json", "failure_authority.json", "partition_summary.json",
          "warning_diagnostics.json", "method_comparison.json", "qc.json")
EXACT_MESSAGE = ("Extremely bad integrand behavior occurs at some points of the\n"
                 "  integration interval.")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def safe(relative: Path | str) -> Path:
    relative = Path(relative)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("unsafe_path")
    path = ROOT / relative
    if any(item.is_symlink() for item in (path, *path.parents)):
        raise ValueError("symlink_rejected")
    if not path.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError("path_escape")
    return path


def digest(relative: Path | str) -> str:
    handle = hashlib.sha256()
    with safe(relative).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            handle.update(block)
    return handle.hexdigest()


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def read_json(relative: Path | str):
    return json.loads(safe(relative).read_text(), object_pairs_hook=no_duplicates,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite_json")))


def encoded(value) -> str:
    return json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"


def atomic_json(name: str, value, private: bool = False) -> None:
    destination = safe((LOCAL if private else OUT) / name)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError("output_exists")
    temporary = destination.with_name("." + destination.name + ".tmp")
    with temporary.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(encoded(value))
    temporary.replace(destination)


def committed(relative: Path | str) -> None:
    if safe(relative).read_bytes() != subprocess.check_output(
            ["git", "show", f"HEAD:{relative}"], cwd=ROOT):
        raise ValueError("uncommitted_authority")


def one_line(relative: Path | str, ordinal: int) -> str:
    if ordinal != 1:
        raise PermissionError("only_ordinal_1_authorized")
    with safe(relative).open(encoding="utf-8") as stream:
        for index, line in enumerate(stream):
            if index == ordinal:
                return line
    raise ValueError("ordinal_1_unavailable")


def source_hashes() -> dict[str, str]:
    return {
        "session14r_manifest": digest(R14R / "manifest.json"),
        "session14s_manifest": digest(R14S / "manifest.json"),
        "session14t_manifest": digest(R14T / "manifest.json"),
        "canonical_population": digest(POPULATION),
        "prepared_population": digest(PREPARED),
    }


def verify_sources():
    if source_hashes() != EXPECTED:
        raise ValueError("source_authority_changed")
    failure = read_json(R14R / "local/failure.json")
    if (failure.get("exception") != "IntegrationWarning" or
            failure.get("message") != EXACT_MESSAGE or failure.get("states_completed") != 1):
        raise ValueError("session14r_failure_authority_changed")
    if read_json(R14T / "authority_summary.json")["classification"] != "B":
        raise ValueError("session14t_authority_changed")
    return failure


def preservation() -> None:
    git("merge-base", "--is-ancestor", START, "HEAD")
    if git("rev-parse", "v0.1.0^{}") != TAG:
        raise ValueError("release_tag_changed")
    changed = set(git("diff", "--name-only", START).splitlines())
    allowed = {str(PROTOCOL), *map(str, CODE),
               "docs/session_14u_equivalence_repair_and_warning_diagnosis.md",
               "docs/research_log.md"}
    if any(path not in allowed and not path.startswith(str(OUT) + "/") for path in changed):
        raise ValueError("historical_file_changed")
    original = subprocess.check_output(["git", "show", f"{START}:docs/research_log.md"], cwd=ROOT)
    if not safe("docs/research_log.md").read_bytes().startswith(original):
        raise ValueError("research_log_rewritten")


def code_hashes() -> dict[str, str]:
    return {str(path): digest(path) for path in CODE}


def environment() -> dict[str, str]:
    return {"python": platform.python_version(), "numpy": np.__version__,
            "scipy": scipy.__version__, "lock_sha256": digest("uv.lock")}


def preflight() -> None:
    if git("status", "--porcelain"):
        raise ValueError("clean_tree_required")
    committed(PROTOCOL)
    for path in CODE:
        committed(path)
    if subprocess.run(["git", "check-ignore", "-q", str(LOCAL / "probe")], cwd=ROOT).returncode:
        raise ValueError("local_storage_not_ignored")
    preservation()
    verify_sources()
    print("Session 14u preflight passed; ordinal 1 and numerical path not opened")


def ledger(status: str) -> None:
    path = safe(LOCAL / "access.jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps({"time": datetime.now(timezone.utc).isoformat(),
                                 "stage": "diagnose", "status": status,
                                 "head": git("rev-parse", "HEAD")}) + "\n")


def claim_marker() -> None:
    marker = safe(LOCAL / "diagnose.marker")
    marker.parent.mkdir(parents=True, exist_ok=True)
    with marker.open("x", encoding="utf-8") as stream:
        stream.write("execution_claimed\n")


def load_authorized_state():
    canonical_text = one_line(POPULATION, 1)
    prepared_text = one_line(PREPARED, 1)
    key, reconstructed = project_line(canonical_text)
    preserved = prepared_text.encode("utf-8")
    reproduced = require_historical_prepared_bytes(reconstructed, preserved)
    decoded = json.loads(prepared_text, object_pairs_hook=no_duplicates,
                         parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite_json")))
    alias, event_key = key
    neutral = f"{alias}_state_{2:06d}"
    integrity = hashlib.sha256((alias + "\0" + event_key).encode()).hexdigest()
    return neutral, integrity, decoded, reproduced, preserved


def association(value: float, onset, envelope) -> dict[str, bool]:
    switches = [item.location for item in envelope.switches]
    boundaries = [number for tie in envelope.tie_intervals for boundary in (tie.start, tie.end)
                  if boundary is not None for number in (boundary.outside, boundary.inside)]
    return {"onset": value in onset, "switch": value in switches,
            "tie_enclosure": value in boundaries}


def classify(warning_reproduced: bool, controlled: dict, continuity: dict,
             partition_valid: bool, maximum_disagreement: float) -> tuple[str, int]:
    if not warning_reproduced:
        return "G", 4
    production_healthy = all((controlled.get("converged"), controlled.get("finite"),
                              controlled.get("deterministic")))
    continuity_healthy = bool(continuity.get("oracle_comparison_passed"))
    if not production_healthy:
        return "D", 3
    if not continuity_healthy:
        return "E", 3
    if not partition_valid:
        return "C", 2
    if maximum_disagreement <= 1e-9:
        return "A", 1
    return "B", 1


def finite(value) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("nonfinite_public_value")
    if isinstance(value, dict):
        for item in value.values():
            finite(item)
    elif isinstance(value, list):
        for item in value:
            finite(item)


def close_manifest(status: str) -> None:
    existing = [name for name in PUBLIC if safe(OUT / name).exists()]
    atomic_json("manifest.json", {
        "schema_version": 1, "status": status, "start": START,
        "protocol_sha256": digest(PROTOCOL), "implementation": code_hashes(),
        "environment": environment(), "sources": EXPECTED,
        "outputs": {name: digest(OUT / name) for name in existing},
        "unavailable": [name for name in PUBLIC if name not in existing],
    })


def diagnose() -> None:
    preflight()
    if safe(OUT / "manifest.json").exists():
        raise FileExistsError("closed_no_rerun")
    claim_marker()
    ledger("started")
    try:
        historical = verify_sources()
        neutral, integrity, row, reproduced, preserved = load_authorized_state()
        atomic_json("equivalence_repair.json", {
            "schema_version": 1, "status": "passed", "zero_based_row_ordinal": 1,
            "neutral_state_key": neutral, "reproduced_line_sha256": hashlib.sha256(reproduced).hexdigest(),
            "preserved_line_sha256": hashlib.sha256(preserved).hexdigest(),
            "exact_historical_byte_equality": reproduced == preserved,
            "comparison_layer": "historical_sorted_json_utf8_bytes",
            "tuple_list_normalization": False, "numeric_tolerance": None,
        })

        try:
            locate_warning(CANDIDATES, row["carrier"], row["receivers"], row["defenders"],
                           evaluate_edge, production)
        except WarningLocated as caught:
            warning = caught.record
        else:
            raise ValueError("historical_warning_not_reproduced")
        if warning.category != historical["exception"] or warning.message != historical["message"]:
            raise ValueError("warning_identity_mismatch")

        receiver = row["receivers"][warning.receiver_ordinal]
        field, _, _, defenders, individual, onset, envelope, partitions = maximum_function(
            warning.candidate, row["carrier"], receiver, row["defenders"])
        widths = width_summary(partitions)
        active_index = next((index for index, (lower, upper) in enumerate(
            zip(partitions[:-1], partitions[1:], strict=True))
            if lower == warning.lower and upper == warning.upper), None)
        if active_index is None:
            raise ValueError("active_piece_not_recovered")

        controlled, controlled_values = controlled_diagnostic(
            field, row["carrier"], receiver, row["defenders"])
        methods, differences, strict_parts, repeat_parts, unsplit_parts, split_evals = method_diagnostic(
            individual, onset, partitions)
        continuity = continuity_diagnostic(warning.candidate, row["carrier"], receiver,
                                           row["defenders"], partitions,
                                           (warning.lower, warning.upper))
        active = strict_parts[active_index]
        joint_difference = (abs(controlled_values["maximum"] - methods["piecewise_strict"])
                            if controlled.get("converged") else None)
        required_differences = (
            abs(methods["piecewise_strict"] - methods["piecewise_repeat"]),
            abs(methods["piecewise_strict"] - methods["unsplit_adaptive"]),
            abs(methods["piecewise_strict"] - methods["direct_simpson_65536"]),
            abs(methods["split_simpson_32768"] - methods["split_simpson_65536"]),
            joint_difference if joint_difference is not None else math.inf,
        )
        maximum_disagreement = max(required_differences)
        category, readiness = classify(True, controlled, continuity, True, maximum_disagreement)
        lower_association = association(warning.lower, onset, envelope)
        upper_association = association(warning.upper, onset, envelope)

        atomic_json("failure_authority.json", {
            "schema_version": 1, "session14r_failure_sha256": digest(R14R / "local/failure.json"),
            "stable_alias": row["alias"], "neutral_state_key": neutral,
            "state_integrity_key_sha256": integrity, "zero_based_row_ordinal": 1,
            "candidate": warning.candidate, "receiver_ordinal": warning.receiver_ordinal,
            "neutral_edge_key": f"{neutral}_receiver_{warning.receiver_ordinal + 1:02d}",
            "stage": "strict_piecewise_maximum", "combination": "maximum",
        })
        atomic_json("partition_summary.json", {
            "schema_version": 1, "defender_count": len(defenders),
            "onset_count": len(onset), "switch_count": len(envelope.switches),
            "tie_interval_count": len(envelope.tie_intervals),
            "certified_enclosure_endpoint_count": sum(
                boundary is not None for tie in envelope.tie_intervals
                for boundary in (tie.start, tie.end)),
            "piece_width_normalized_t": widths,
            "problematic_piece": {"index": active_index, "lower": warning.lower,
                                  "upper": warning.upper, "width": warning.upper - warning.lower,
                                  "adjacent_float": float(np.nextafter(warning.lower, warning.upper)) == warning.upper,
                                  "lower_association": lower_association,
                                  "upper_association": upper_association},
            "partition_valid": True, "continuity": continuity,
        })
        atomic_json("warning_diagnostics.json", {
            "schema_version": 1, "category": warning.category, "message": warning.message,
            "stage": "strict_piecewise_maximum", "stack_location": "geometry/production_verification.py:adaptive_maximum",
            "quad": {"epsabs": 1e-13, "epsrel": 1e-13, "limit": 1000},
            "returned_estimate": warning.value, "returned_error": warning.error,
            "full_output": {"estimate": active.value, "error": active.error,
                            "evaluations": active.evaluations,
                            "subdivisions": active.subdivisions,
                            "termination_message": active.message},
        })
        atomic_json("method_comparison.json", {
            "schema_version": 1, "joint_simpson": controlled,
            "joint_simpson_maximum": controlled_values.get("maximum"),
            "methods": methods, "pairwise_absolute_differences": differences,
            "joint_vs_piecewise_absolute_difference": joint_difference,
            "maximum_required_method_disagreement": maximum_disagreement,
            "split_simpson_evaluations": list(split_evals),
            "piecewise_strict_warning_pieces": sum(item.message is not None for item in strict_parts),
            "piecewise_repeat_warning_pieces": sum(item.message is not None for item in repeat_parts),
            "unsplit_warning_pieces": sum(item.message is not None for item in unsplit_parts),
        })
        atomic_json("qc.json", {
            "schema_version": 1, "status": "closed", "classification": category,
            "repair_readiness": readiness, "ordinal_1_byte_gate_passed": True,
            "warning_reproduced": True, "empirical_states_opened": 1,
            "additional_states_opened": 0, "empirical_edges_diagnosed": 1,
            "scientific_partial_results_interpreted": False,
            "targets_outcomes_models_shares_accessed": False,
            "protected_or_withheld_access": False, "failure": None,
        })
        atomic_json("diagnostic_trace.json", {
            "candidate": warning.candidate, "receiver_ordinal": warning.receiver_ordinal,
            "partitions": list(partitions), "onsets": list(onset),
            "switches": [item.location for item in envelope.switches],
            "state_integrity_key_sha256": integrity,
        }, private=True)
        close_manifest("closed")
        ledger("closed")
        print(f"Session 14u diagnosis closed: {category}, readiness {readiness}")
    except Exception as error:
        atomic_json("failure.json", {"type": type(error).__name__, "message": str(error),
                                     "traceback": traceback.format_exc()}, private=True)
        if not safe(OUT / "qc.json").exists():
            atomic_json("qc.json", {"schema_version": 1, "status": "unresolved",
                "classification": "G", "repair_readiness": 4,
                "ordinal_1_byte_gate_passed": safe(OUT / "equivalence_repair.json").exists(),
                "warning_reproduced": False, "empirical_states_opened": 1,
                "additional_states_opened": 0, "empirical_edges_diagnosed": 0,
                "scientific_partial_results_interpreted": False,
                "targets_outcomes_models_shares_accessed": False,
                "protected_or_withheld_access": False, "failure": type(error).__name__})
        close_manifest("unresolved")
        ledger("failed")
        raise


def publication_check() -> None:
    preservation()
    verify_sources()
    for path in (PROTOCOL, *CODE):
        committed(path)
    manifest = read_json(OUT / "manifest.json")
    required = {"schema_version", "status", "start", "protocol_sha256", "implementation",
                "environment", "sources", "outputs", "unavailable"}
    if set(manifest) != required or manifest["protocol_sha256"] != digest(PROTOCOL):
        raise ValueError("manifest_authority")
    if manifest["implementation"] != code_hashes() or manifest["sources"] != EXPECTED:
        raise ValueError("manifest_binding")
    if set(manifest["outputs"]) | set(manifest["unavailable"]) != set(PUBLIC):
        raise ValueError("manifest_membership")
    for name, expected in manifest["outputs"].items():
        if digest(OUT / name) != expected:
            raise ValueError("output_hash_changed")
        value = read_json(OUT / name)
        finite(value)
        text = safe(OUT / name).read_text()
        for forbidden in ("/Users/", "/private/", "event_id", "carrier_xy", "candidate_xy",
                          "defender_xy", "target_index", "access_token", "X-Amz-Signature"):
            if forbidden in text:
                raise ValueError("publication_boundary")
    qc = read_json(OUT / "qc.json")
    if qc["empirical_states_opened"] != 1 or qc["additional_states_opened"] != 0:
        raise ValueError("state_scope")
    print(f"Session 14u publication checks passed: {manifest['status']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "diagnose", "publication-check"))
    command = parser.parse_args().command
    {"preflight": preflight, "diagnose": diagnose,
     "publication-check": publication_check}[command]()


if __name__ == "__main__":
    main()
