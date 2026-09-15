#!/usr/bin/env python3
"""Governed Session 14ar terminal-interval reference calculation."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import math
from pathlib import Path
import subprocess
import sys
import traceback


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "src/defensive_network_disruption/validation/terminal_interval_reference.py"


def _load():
    specification = importlib.util.spec_from_file_location("session14ar_reference", MODULE_PATH)
    module = importlib.util.module_from_spec(specification)
    assert specification.loader is not None
    specification.loader.exec_module(module)
    return module


ref = _load()
START = "03c8d889e5f210af413a77628c302b5e2e411ccf"
TAG = "f00690c05d8c1c6db308a65bd311c43f9a8ef2fa"
PROTOCOL = ROOT / "docs/protocols/phase_14ar_terminal_interval_reference.md"
SELECTED = ROOT / "outputs/session14am_constant_width_comparator_diagnosis/local/000010_selected_geometry.json"
STRUCTURE = ROOT / "outputs/session14am_constant_width_comparator_diagnosis/local/000020_structure.json"
PIECE = ROOT / "outputs/session14ao_onset_only_adaptive_convergence/local/000121_piece.json"
ONSETS = ROOT / "outputs/session14ao_onset_only_adaptive_convergence/local/000003_onsets.json"
AO_MANIFEST = ROOT / "outputs/session14ao_onset_only_adaptive_convergence/manifest.json"
AO_INDEX = ROOT / "outputs/session14ao_onset_only_adaptive_convergence/local/private_index.json"
AQ_MANIFEST = ROOT / "outputs/continuous_occlusion_terminal_error_revalidation/manifest.json"
OUT = ROOT / "outputs/continuous_occlusion_terminal_interval_reference"
HASHES = {
    SELECTED: "fe39401fee30c197082e5513d376308cdfe3eb8fbf35b7bbc7ddb7a749f41d2e",
    STRUCTURE: "791ddcd717c5f08d7c834de127388c81012192c859aa20ce0c96f342fbbe69e6",
    PIECE: "5d86b9e849cdb6708962a2aae47c33b281712fea45b09fb2dc1634c4171abb08",
    ONSETS: "e4944e3cbe1905dbb5c169cb14ffd7b4775692375bc24bf15e5887a0af6dce26",
    AO_MANIFEST: "367cec3ea22163af15c299b96e3792424707603b5920257eed40b3e06e5335f3",
    AO_INDEX: "23b4264f0bce761cc17cb61357cd1fd39b6a418e5bce9938314898f8025d3955",
    AQ_MANIFEST: "90c000da20f0ce7afd1a626518173a8cc3aeabdcd31681670d3f747a39739eee",
    ROOT / "uv.lock": "c9e4da0781770b9e72b8a5b10a7c514f2259b7e63dc1b67604ee481934db0a0c",
}
SOURCES = (
    PROTOCOL, MODULE_PATH, Path(__file__).resolve(),
    ROOT / "tests/test_session14ar_terminal_interval_reference.py",
)


def git(*arguments: str) -> str:
    return subprocess.check_output(("git", *arguments), cwd=ROOT, text=True).strip()


def preflight() -> dict:
    if git("status", "--porcelain"):
        raise RuntimeError("dirty_tree")
    git("merge-base", "--is-ancestor", START, "HEAD")
    if git("rev-parse", "v0.1.0^{}") != TAG:
        raise RuntimeError("release_changed")
    if Path(sys.prefix).resolve() != (ROOT / ".venv").resolve():
        raise RuntimeError("project_interpreter")
    for path, expected in HASHES.items():
        if ref.sha(path) != expected:
            raise RuntimeError("authority_hash_changed:" + path.name)
    for path in SOURCES:
        relative = path.relative_to(ROOT).as_posix()
        if subprocess.check_output(("git", "show", "HEAD:" + relative), cwd=ROOT) != path.read_bytes():
            raise RuntimeError("uncommitted_source:" + relative)
    return {"start": START, "implementation_commit": git("rev-parse", "HEAD"),
            "release_target": TAG, "authority_hashes": {p.relative_to(ROOT).as_posix(): h for p, h in HASHES.items()},
            "source_hashes": {p.relative_to(ROOT).as_posix(): ref.sha(p) for p in SOURCES}}


def _fraction_record(value):
    return {"numerator": str(value.numerator), "denominator": str(value.denominator),
            "sha256": hashlib.sha256(f"{value.numerator}/{value.denominator}".encode()).hexdigest()}


def assemble():
    bindings = preflight()
    piece = ref.strict_load(PIECE)
    if set(piece) != {"a", "alist", "b", "blist", "callback_count", "elist", "estimate",
                         "exception", "exhausted", "last", "limit", "message", "neval", "normal",
                         "reported_error", "rlist", "seconds", "tolerance", "trace", "trace_sha256", "warnings"}:
        raise ref.ReferenceError("piece_schema")
    left, right = float(piece["a"]), float(piece["b"])
    structure = ref.strict_load(STRUCTURE)
    onsets = ref.strict_load(ONSETS)
    topology = ref.structural_authority(structure, onsets, left, right)
    geometry = ref.restricted_geometry(SELECTED.read_text(), topology["owner"])
    rate = ref.exact_lambda(geometry)
    reconstruction = ref.reconstruction_check(rate, piece["trace"])
    enclosure = ref.taylor_enclosure(rate, left, right)
    comparison = ref.compare_retained(piece["estimate"], piece["reported_error"], enclosure)
    if not enclosure["available"]:
        classification, readiness = "F", 4
        verdict = "independent_bound_unavailable"
    elif comparison["within_existing_authority"]:
        classification, readiness = "A", 1
        verdict = "roundoff_prevented_adaptive_certification_despite_independently_bounded_accuracy"
    elif enclosure["width"] > ref.AGREEMENT:
        classification, readiness = "B", 2
        verdict = "bound_too_wide"
    else:
        classification, readiness = "C", 3
        verdict = "retained_estimate_outside_existing_authority"
    public = {
        "interval_authority.json": {
            "schema_version": 1, "status": "verified", "sanitized_interval_ordinal": 8,
            "normalized_left": left, "normalized_right": right, "normalized_width": right-left,
            "field_family": "constant_width", "sigma_metres": 2.0, "onset_metres": 1.0,
            "combination": "maximum", "single_owner": topology["single_owner"],
            "owner_fully_active": topology["fully_active"],
            "interior_onset_count": topology["interior_onsets"],
            "interior_switch_count": topology["interior_switches"],
            "interior_tie_interval_count": topology["interior_ties"],
            "retained_role": "warning_producing_terminal_interval",
            "full_edge_recomputed": False,
            "record_hashes": {path.name: HASHES[path] for path in (SELECTED, STRUCTURE, PIECE, ONSETS)},
        },
        "reference_method.json": {
            "schema_version": 1, "method": "exact_rational_integrated_exponential_taylor_enclosure",
            "integrand": "exp(-lambda*t^2)", "coordinate_arithmetic": "Fraction.from_float",
            "remainder": "integrated_lagrange_absolute_remainder",
            "orders": {"first": 0, "last": ref.MAX_ORDER, "selection": "first_qualifying"},
            "existing_agreement_authority": ref.AGREEMENT,
            "fallback": None, "confirmation_method": None,
            "uses_scipy": False, "uses_numpy": False, "uses_adaptive_quadrature": False,
            "uses_production_integrator": False, "independent": True,
        },
        "reference_result.json": {
            "schema_version": 1, "status": "available" if enclosure["available"] else "unavailable",
            "accepted_order": enclosure["order"], "lower": enclosure["lower"], "upper": enclosure["upper"],
            "bound_width": enclosure["width"], "bound_width_to_authority_ratio": enclosure["width"] / ref.AGREEMENT,
            "classification": classification, "readiness": readiness,
            "exact_lower_sha256": hashlib.sha256(f"{enclosure['exact_lower'].numerator}/{enclosure['exact_lower'].denominator}".encode()).hexdigest(),
            "exact_upper_sha256": hashlib.sha256(f"{enclosure['exact_upper'].numerator}/{enclosure['exact_upper'].denominator}".encode()).hexdigest(),
        },
        "retained_comparison.json": {
            "schema_version": 1, **comparison,
            "warning_category": piece["warnings"][0]["category"],
            "warning_message_sha256": hashlib.sha256(piece["message"].encode()).hexdigest(),
            "roundoff_certification_verdict": verdict,
        },
    }
    private = {
        "schema_version": 1,
        "geometry": geometry,
        "owner_ordinal": topology["owner"],
        "lambda": _fraction_record(rate),
        "exact_lower": _fraction_record(enclosure["exact_lower"]),
        "exact_upper": _fraction_record(enclosure["exact_upper"]),
        "exact_remainder": _fraction_record(enclosure["remainder"]),
        "reconstruction": reconstruction,
        "retained_trace_sha256": piece["trace_sha256"],
    }
    return bindings, public, private, classification, readiness


def close(bindings, public, private, classification, readiness):
    local = OUT / "local"
    ref.atomic(local / "exact_reference.json", private)
    private_index = {"schema_version": 1, "files": {"exact_reference.json": ref.sha(local / "exact_reference.json")}}
    ref.atomic(local / "private_index.json", private_index)
    private_hash = ref.sha(local / "private_index.json")
    for name, value in public.items():
        ref.atomic(OUT / name, value)
    qc = {"schema_version": 1, "status": "closed", "execution_valid": True,
          "classification": classification, "readiness": readiness,
          "intervals_evaluated": 1, "full_edges_recomputed": 0,
          "additional_states_or_edges": 0, "scientific_products_opened": 0,
          "prohibited_accesses": 0, "private_index_sha256": private_hash}
    ref.atomic(OUT / "qc.json", qc)
    outputs = {name: ref.sha(OUT / name) for name in ref.PUBLIC_FILES}
    manifest = {"schema_version": 1, "status": "closed", "authority": bindings,
                "outputs": outputs, "private_index_sha256": private_hash}
    ref.atomic(OUT / "manifest.json", manifest)
    return ref.validate_public_package(OUT)


def reference():
    local = OUT / "local"
    ref.create_once(local / "attempt.marker", {"schema_version": 1, "session": "14ar", "exclusive": True})
    try:
        result = close(*assemble())
    except BaseException as error:
        ref.create_once(local / "failure.json", {
            "schema_version": 1, "status": "invalid", "exception": type(error).__name__,
            "message": str(error), "traceback": traceback.format_exc(),
            "intervals_evaluated": 0, "full_edges_recomputed": 0,
            "additional_states_or_edges": 0, "scientific_products_opened": 0,
        })
        raise
    print(ref.canonical(result).decode().strip())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "reference", "publication-check"))
    command = parser.parse_args().command
    if command == "preflight":
        print(ref.canonical(preflight()).decode().strip())
    elif command == "reference":
        reference()
    else:
        print("publication-check:", bool(ref.validate_public_package(OUT)))


if __name__ == "__main__":
    main()
