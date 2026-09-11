#!/usr/bin/env python3
"""Governed bounded diagnosis of the preserved Session 14R numerical warning."""
from __future__ import annotations

import argparse
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

from defensive_network_disruption.data.representation_projection import project_line
from defensive_network_disruption.geometry import production_verification as production
from defensive_network_disruption.geometry.max_warning_diagnosis import (
    WarningLocated, continuity_diagnostic, controlled_diagnostic, locate_warning,
    maximum_function, method_diagnostic, quad_diagnostic, width_summary,
)
from defensive_network_disruption.geometry.occlusion_fields import CANDIDATES
from defensive_network_disruption.geometry.representation_study import evaluate_edge


START = "3f3952d99987ebb0e753484adc82825d884fe383"
TAG = "f00690c05d8c1c6db308a65bd311c43f9a8ef2fa"
PROTOCOL = Path("docs/protocols/phase_14s_independent_max_warning_diagnosis.md")
OUT = Path("outputs/continuous_occlusion_max_warning_diagnosis")
LOCAL = OUT / "local"
SESSION14R = Path("outputs/continuous_occlusion_retry")
POPULATION = Path("outputs/receiver_ranking_m0_m1/local/population.jsonl")
PREPARED = SESSION14R / "local/prepared.jsonl"
EXPECTED = {
    "session14r_manifest": "8a639f7a2b29a6aec026e176d80d8901b28839b0d2091dd0256751d77b6f70ed",
    "population": "cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d",
    "prepared": "15a809060f0ba4a8cb3790011dab8008db3dad6e931c287ccb395f61ef1530b0",
}
CODE = (
    Path("scripts/session_14s_independent_max_warning_diagnosis.py"),
    Path("src/defensive_network_disruption/geometry/max_warning_diagnosis.py"),
    Path("tests/test_session14s_diagnosis.py"),
)
PUBLIC = ("failure_authority.json", "partition_summary.json", "method_comparison.json",
          "warning_diagnostics.json", "qc.json")
SCHEMAS = {
    "failure_authority.json": {"schema_version", "session14r_failure_sha256", "stable_alias",
        "neutral_state_key", "state_integrity_key_sha256", "zero_based_row_ordinal",
        "candidate", "receiver_ordinal", "neutral_edge_key", "stage", "combination"},
    "partition_summary.json": {"schema_version", "defender_count", "onset_count",
        "true_switch_count", "tie_interval_count", "certified_enclosure_endpoint_count",
        "piece_width_normalized_t", "problematic_piece_width_normalized_t",
        "problematic_piece_is_adjacent_float", "continuity", "synthetic_topology_control"},
    "method_comparison.json": {"schema_version", "production_joint_simpson",
        "joint_maximum_matches_piecewise_within_1e_6", "methods",
        "pairwise_absolute_differences", "maximum_pairwise_difference",
        "split_simpson_evaluations", "piecewise_strict_termination_messages",
        "piecewise_repeat_termination_messages", "unsplit_termination_messages"},
    "warning_diagnostics.json": {"schema_version", "category", "message", "stack_location",
        "quadrature", "active_piece_index", "active_piece_width",
        "warning_call_returned_estimate", "warning_call_returned_error", "full_output"},
    "qc.json": {"schema_version", "status", "empirical_states_opened",
        "empirical_edges_diagnosed", "warning_reproduced",
        "scientific_partial_results_interpreted", "prohibited_access", "classification", "failure"},
}
EXACT_MESSAGE = ("Extremely bad integrand behavior occurs at some points of the\n"
                 "  integration interval.")


def git(*args):
    return subprocess.check_output(["git", *map(str, args)], cwd=ROOT, text=True).strip()


def safe(relative):
    relative = Path(relative)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("unsafe_path")
    path = ROOT / relative
    if any(item.is_symlink() for item in (path, *path.parents)):
        raise ValueError("symlink_rejected")
    if not path.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError("path_escape")
    return path


def digest(relative):
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


def read_json(relative):
    return json.loads(safe(relative).read_text(), object_pairs_hook=no_duplicates,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite_json")))


def encoded(value):
    return json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"


def write_json(name, value):
    destination = safe(OUT / name)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError("output_exists")
    temporary = destination.with_name("." + destination.name + ".tmp")
    with temporary.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(encoded(value))
    temporary.replace(destination)


def write_private(name, value):
    destination = safe(LOCAL / name)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError("private_record_exists")
    temporary = destination.with_name("." + destination.name + ".tmp")
    with temporary.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(encoded(value))
    temporary.replace(destination)


def committed(relative):
    current = safe(relative).read_bytes()
    stored = subprocess.check_output(["git", "show", f"HEAD:{relative}"], cwd=ROOT)
    if current != stored:
        raise ValueError("uncommitted_authority")


def code_hashes():
    return {str(path): digest(path) for path in CODE}


def environment():
    return {"python": platform.python_version(), "numpy": np.__version__,
            "scipy": scipy.__version__, "lock_sha256": digest("uv.lock")}


def preservation():
    git("merge-base", "--is-ancestor", START, "HEAD")
    if git("rev-parse", "v0.1.0^{}") != TAG:
        raise ValueError("release_tag_changed")
    changed = set(git("diff", "--name-only", START).splitlines())
    allowed = {str(PROTOCOL), *map(str, CODE),
               "docs/session_14s_independent_max_warning_diagnosis.md",
               "docs/research_log.md"}
    if any(item not in allowed and not item.startswith(str(OUT) + "/") for item in changed):
        raise ValueError("historical_file_changed")
    original = subprocess.check_output(["git", "show", f"{START}:docs/research_log.md"], cwd=ROOT)
    if not safe("docs/research_log.md").read_bytes().startswith(original):
        raise ValueError("research_log_rewritten")


def verify_sources():
    actual = {
        "session14r_manifest": digest(SESSION14R / "manifest.json"),
        "population": digest(POPULATION), "prepared": digest(PREPARED),
    }
    if actual != EXPECTED:
        raise ValueError("source_identity_changed")
    failure = read_json(SESSION14R / "local/failure.json")
    if (failure.get("exception") != "IntegrationWarning" or
            failure.get("message") != EXACT_MESSAGE or failure.get("states_completed") != 1):
        raise ValueError("failure_authority_changed")
    return failure


def failing_row_ordinal(failure):
    completed = failure.get("states_completed")
    if isinstance(completed, bool) or not isinstance(completed, int) or completed < 0:
        raise ValueError("invalid_completed_state_count")
    return completed


def preflight():
    if git("status", "--porcelain"):
        raise ValueError("clean_tree_required")
    committed(PROTOCOL)
    for path in CODE:
        committed(path)
    if subprocess.run(["git", "check-ignore", "-q", str(LOCAL / "probe")], cwd=ROOT).returncode:
        raise ValueError("local_storage_not_ignored")
    preservation()
    verify_sources()
    print("Session 14s preflight passed; failing geometry not opened")


def ledger(stage, status):
    path = safe(LOCAL / "access.jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps({"time": datetime.now(timezone.utc).isoformat(),
                                 "stage": stage, "status": status,
                                 "head": git("rev-parse", "HEAD")}) + "\n")


def one_line(relative, ordinal):
    with safe(relative).open(encoding="utf-8") as stream:
        for index, line in enumerate(stream):
            if index == ordinal:
                return line
    raise ValueError("failing_row_unavailable")


def load_failing_state():
    ordinal = failing_row_ordinal(verify_sources())
    canonical_text = one_line(POPULATION, ordinal)
    key, canonical = project_line(canonical_text)
    prepared = json.loads(one_line(PREPARED, ordinal), object_pairs_hook=no_duplicates)
    if canonical != prepared:
        raise ValueError("prepared_geometry_mismatch")
    alias, event_key = key
    neutral = f"{alias}_state_{ordinal + 1:06d}"
    integrity = hashlib.sha256((alias + "\0" + event_key).encode()).hexdigest()
    return ordinal, neutral, integrity, prepared


def finite(value):
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("nonfinite_output")
    if isinstance(value, dict):
        for item in value.values():
            finite(item)
    elif isinstance(value, list):
        for item in value:
            finite(item)


def validate_public(name, value):
    if set(value) != SCHEMAS[name]:
        raise ValueError("public_schema")
    finite(value)


def synthetic_topology_control(partitions):
    widths = width_summary(partitions)
    if widths["adjacent_float_pieces"] == 0:
        return {"used": False, "reason": "no_adjacent_float_piece"}
    constant = lambda _: 0.5
    records = [quad_diagnostic(constant, a, b, 1e-13)
               for a, b in zip(partitions[:-1], partitions[1:], strict=True)]
    return {"used": True, "reason": "adjacent_float_topology_present",
            "termination_messages": sum(item.message is not None for item in records),
            "piece_count": len(records)}


def close_manifest(status):
    existing = [name for name in PUBLIC if safe(OUT / name).exists()]
    manifest = {
        "schema_version": 1, "status": status, "start": START,
        "protocol_sha256": digest(PROTOCOL), "implementation": code_hashes(),
        "environment": environment(), "sources": EXPECTED,
        "outputs": {name: digest(OUT / name) for name in existing},
        "unavailable": [name for name in PUBLIC if name not in existing],
    }
    write_json("manifest.json", manifest)


def diagnose():
    preflight()
    marker = safe(LOCAL / "diagnose.marker")
    production.claim_execution(marker)
    if safe(OUT / "manifest.json").exists():
        raise FileExistsError("closed_no_rerun")
    ledger("diagnose", "started")
    try:
        historical = verify_sources()
        ordinal, neutral, integrity, row = load_failing_state()
        try:
            located = locate_warning(CANDIDATES, row["carrier"], row["receivers"],
                                     row["defenders"], evaluate_edge, production)
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
        active_index = next((index for index, (a, b) in enumerate(
            zip(partitions[:-1], partitions[1:], strict=True))
            if a == warning.lower and b == warning.upper), None)
        if active_index is None:
            raise ValueError("active_piece_not_recovered")

        controlled, controlled_values = controlled_diagnostic(
            field, row["carrier"], receiver, row["defenders"])
        methods, differences, strict_parts, repeat_parts, unsplit_parts, split_evals = method_diagnostic(
            individual, onset, partitions)
        active = strict_parts[active_index]
        continuity = continuity_diagnostic(warning.candidate, row["carrier"], receiver,
                                           row["defenders"], partitions,
                                           (warning.lower, warning.upper))
        control = synthetic_topology_control(partitions)

        write_private("diagnostic_trace.json", {
            "neutral_state_key": neutral, "state_integrity_key_sha256": integrity,
            "candidate": warning.candidate, "receiver_ordinal": warning.receiver_ordinal,
            "active_subinterval": [warning.lower, warning.upper],
            "partitions": list(partitions), "onsets": list(onset),
            "switches": [item.location for item in envelope.switches],
            "tie_intervals": len(envelope.tie_intervals),
            "strict_piece_messages": [item.message for item in strict_parts],
            "repeat_piece_messages": [item.message for item in repeat_parts],
            "unsplit_messages": [item.message for item in unsplit_parts],
        })

        write_json("failure_authority.json", {
            "schema_version": 1, "session14r_failure_sha256": digest(SESSION14R / "local/failure.json"),
            "stable_alias": row["alias"], "neutral_state_key": neutral,
            "state_integrity_key_sha256": integrity, "zero_based_row_ordinal": ordinal,
            "candidate": warning.candidate, "receiver_ordinal": warning.receiver_ordinal,
            "neutral_edge_key": f"{neutral}_receiver_{warning.receiver_ordinal + 1:02d}",
            "stage": "strict_piecewise_maximum", "combination": "maximum",
        })
        write_json("partition_summary.json", {
            "schema_version": 1, "defender_count": len(defenders), "onset_count": len(onset),
            "true_switch_count": len(envelope.switches), "tie_interval_count": len(envelope.tie_intervals),
            "certified_enclosure_endpoint_count": sum(
                boundary is not None for tie in envelope.tie_intervals for boundary in (tie.start, tie.end)),
            "piece_width_normalized_t": widths,
            "problematic_piece_width_normalized_t": warning.upper - warning.lower,
            "problematic_piece_is_adjacent_float": float(np.nextafter(warning.lower, warning.upper)) == warning.upper,
            "continuity": continuity, "synthetic_topology_control": control,
        })
        write_json("method_comparison.json", {
            "schema_version": 1, "production_joint_simpson": controlled,
            "joint_maximum_matches_piecewise_within_1e_6": (
                controlled["converged"] and abs(controlled_values["maximum"] - methods["piecewise_strict"]) <= 1e-6),
            "methods": methods, "pairwise_absolute_differences": differences,
            "maximum_pairwise_difference": max(differences.values()),
            "split_simpson_evaluations": list(split_evals),
            "piecewise_strict_termination_messages": sum(item.message is not None for item in strict_parts),
            "piecewise_repeat_termination_messages": sum(item.message is not None for item in repeat_parts),
            "unsplit_termination_messages": sum(item.message is not None for item in unsplit_parts),
        })
        write_json("warning_diagnostics.json", {
            "schema_version": 1, "category": warning.category, "message": warning.message,
            "stack_location": "geometry/production_verification.py:97 adaptive_maximum",
            "quadrature": {"epsabs": 1e-13, "epsrel": 1e-13, "limit": 1000},
            "active_piece_index": active_index, "active_piece_width": warning.upper - warning.lower,
            "warning_call_returned_estimate": warning.value, "warning_call_returned_error": warning.error,
            "full_output": {"estimate": active.value, "error": active.error,
                            "evaluations": active.evaluations, "subdivisions": active.subdivisions,
                            "termination_message": active.message},
        })
        write_json("qc.json", {
            "schema_version": 1, "status": "diagnosis_complete", "empirical_states_opened": 1,
            "empirical_edges_diagnosed": 1, "warning_reproduced": True,
            "scientific_partial_results_interpreted": False, "prohibited_access": False,
            "classification": "pending_closed_evidence_interpretation", "failure": None,
        })
        for name in PUBLIC:
            validate_public(name, read_json(OUT / name))
        close_manifest("closed")
        ledger("diagnose", "closed")
        print("Session 14s diagnostic evidence closed; interpret only public bounded outputs")
    except Exception as error:
        private = safe(LOCAL / "failure.json")
        private.parent.mkdir(parents=True, exist_ok=True)
        private.write_text(encoded({"type": type(error).__name__, "message": str(error),
                                    "traceback": traceback.format_exc()}))
        if not safe(OUT / "qc.json").exists():
            write_json("qc.json", {"schema_version": 1, "status": "unresolved",
                "empirical_states_opened": 1, "empirical_edges_diagnosed": 0,
                "warning_reproduced": False, "scientific_partial_results_interpreted": False,
                "prohibited_access": False, "classification": "G", "failure": type(error).__name__})
        close_manifest("unresolved")
        ledger("diagnose", "failed")
        raise


def publication_check():
    preservation()
    verify_sources()
    for path in (PROTOCOL, *CODE):
        committed(path)
    manifest = read_json(OUT / "manifest.json")
    required = {"schema_version", "status", "start", "protocol_sha256", "implementation",
                "environment", "sources", "outputs", "unavailable"}
    if set(manifest) != required:
        raise ValueError("manifest_schema")
    if manifest["protocol_sha256"] != digest(PROTOCOL) or manifest["implementation"] != code_hashes():
        raise ValueError("manifest_authority")
    if set(manifest["outputs"]) | set(manifest["unavailable"]) != set(PUBLIC):
        raise ValueError("manifest_membership")
    for name, expected in manifest["outputs"].items():
        if digest(OUT / name) != expected:
            raise ValueError("output_hash_changed")
        value = read_json(OUT / name)
        validate_public(name, value)
        text = safe(OUT / name).read_text()
        for forbidden in ("/Users/", "/private/", "event_id", "carrier_xy", "candidate_xy",
                          "defender_xy", "target_index", "access_token", "X-Amz-Signature"):
            if forbidden in text:
                raise ValueError("publication_boundary")
    print(f"Session 14s publication checks passed: {manifest['status']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "diagnose", "publication-check"))
    args = parser.parse_args()
    {"preflight": preflight, "diagnose": diagnose,
     "publication-check": publication_check}[args.command]()


if __name__ == "__main__":
    main()
