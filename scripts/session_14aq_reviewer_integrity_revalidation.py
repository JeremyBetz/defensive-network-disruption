#!/usr/bin/env python3
"""Governed Session 14aq retained-evidence revalidation."""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.metadata
import importlib.util
from pathlib import Path
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
REVIEWER_PATH = ROOT / "src/defensive_network_disruption/validation/terminal_error_revalidation.py"
VALIDATOR_PATH = ROOT / "src/defensive_network_disruption/validation/terminal_error_publication_validator.py"


def _load(name: str, path: Path):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    assert specification.loader is not None
    specification.loader.exec_module(module)
    return module


reviewer = _load("session14aq_reviewer", REVIEWER_PATH)
validator = _load("session14aq_validator", VALIDATOR_PATH)

START = "2f3d9d4099a4c057d68c20a3231cc8a5e64c4d97"
TAG = "f00690c05d8c1c6db308a65bd311c43f9a8ef2fa"
PROTOCOL = "docs/protocols/phase_14aq_reviewer_integrity_repair.md"
SOURCES = (
    PROTOCOL,
    "src/defensive_network_disruption/validation/terminal_error_revalidation.py",
    "src/defensive_network_disruption/validation/terminal_error_publication_validator.py",
    "scripts/session_14aq_reviewer_integrity_revalidation.py",
    "tests/test_session14aq_reviewer_integrity_revalidation.py",
)
OLD = ROOT / "outputs/session14ao_onset_only_adaptive_convergence"
OUT = ROOT / "outputs/continuous_occlusion_terminal_error_revalidation"
MANIFEST_HASH = "367cec3ea22163af15c299b96e3792424707603b5920257eed40b3e06e5335f3"
INDEX_HASH = "23b4264f0bce761cc17cb61357cd1fd39b6a418e5bce9938314898f8025d3955"
SELECTION_HASH = "66061ced1444c9e818263d6ed4651a281eb53bfa1c9fd857e9e966958e4a5d2a"
SCIPY_SOURCE_HASH = "c59e4133f23ef272e488204c217caf36a38b5921fe0ffeeb2a8f1b804f5ba0d9"
AP_MANIFEST_HASH = "a3462a0ad83397d268bdf1e3e82d224bf0e95585ac4b222a9c34b8333b8aa99a"


def git(*arguments: str) -> str:
    return subprocess.check_output(("git", *arguments), cwd=ROOT, text=True).strip()


def scipy_source() -> tuple[Path, str]:
    if importlib.metadata.version("scipy") != "1.18.1":
        raise RuntimeError("scipy_version")
    distribution = importlib.metadata.distribution("scipy")
    source = Path(distribution.locate_file("scipy/integrate/_quadpack_py.py"))
    source_hash = reviewer.sha(source)
    if source_hash != SCIPY_SOURCE_HASH:
        raise RuntimeError("scipy_source_changed")
    return source, source_hash


def preflight() -> dict:
    if git("status", "--porcelain"):
        raise RuntimeError("dirty_tree")
    git("merge-base", "--is-ancestor", START, "HEAD")
    if git("rev-parse", "v0.1.0^{}") != TAG:
        raise RuntimeError("release_changed")
    if Path(sys.prefix).resolve() != (ROOT / ".venv").resolve():
        raise RuntimeError("project_interpreter")
    for name in SOURCES:
        if subprocess.check_output(("git", "show", "HEAD:" + name), cwd=ROOT) != (ROOT / name).read_bytes():
            raise RuntimeError("uncommitted_source")
    if reviewer.sha(OLD / "manifest.json") != MANIFEST_HASH:
        raise RuntimeError("retained_manifest_changed")
    if reviewer.sha(OLD / "local/private_index.json") != INDEX_HASH:
        raise RuntimeError("retained_index_changed")
    if reviewer.sha(ROOT / "outputs/continuous_occlusion_terminal_error_review/manifest.json") != AP_MANIFEST_HASH:
        raise RuntimeError("session14ap_changed")
    _, source_hash = scipy_source()
    return {
        "start": START,
        "implementation_commit": git("rev-parse", "HEAD"),
        "sources": {name: reviewer.sha(ROOT / name) for name in SOURCES},
        "retained_manifest_sha256": MANIFEST_HASH,
        "retained_private_index_sha256": INDEX_HASH,
        "retained_selection_sha256": SELECTION_HASH,
        "session14ap_manifest_sha256": AP_MANIFEST_HASH,
        "lock_sha256": reviewer.sha(ROOT / "uv.lock"),
        "scipy_version": "1.18.1",
        "scipy_source_sha256": source_hash,
    }


def retained_records() -> tuple[dict, dict, list[dict], list[list[dict]], list[str], dict[str, str]]:
    manifest = reviewer.strict_load(OLD / "manifest.json")
    if manifest["private_index_sha256"] != INDEX_HASH:
        raise ValueError("manifest_index_binding")
    index = reviewer.strict_load(OLD / "local/private_index.json")
    names = reviewer.selected_names()
    selected = {name: index["files"][name] for name in names}
    if len(selected) != 68 or reviewer.digest(selected) != SELECTION_HASH:
        raise ValueError("retained_selection")
    loaded = {}
    for name, expected_hash in selected.items():
        path = OLD / "local" / name
        if reviewer.sha(path) != expected_hash:
            raise ValueError("retained_record_changed")
        loaded[name] = reviewer.strict_load(path)
    levels, pieces, hashes = [], [], []
    for number in reviewer.LEVEL_NUMBERS:
        level_name = f"{number:06d}_level.json"
        comparison_name = f"{number + 1:06d}_comparison.json"
        if comparison_name not in loaded:
            raise ValueError("comparison_missing")
        levels.append(loaded[level_name])
        hashes.append(selected[level_name])
        pieces.append([loaded[f"{piece_number:06d}_piece.json"]
                       for piece_number in range(number - 17, number, 2)])
    return loaded["000001_reference.json"], loaded["000003_onsets.json"], levels, pieces, hashes, selected


def warning_source_match(message: str) -> tuple[bool, str]:
    source, source_hash = scipy_source()
    constants = [node.value for node in ast.walk(ast.parse(source.read_text()))
                 if isinstance(node, ast.Constant) and isinstance(node.value, str)]
    normalized = " ".join(message.split())
    return normalized in {" ".join(value.split()) for value in constants}, source_hash


def corruption_oracles(correct_rows: list[dict[str, str]], expected_rows: list[dict[str, str]]) -> list[dict]:
    cases: list[tuple[str, list[dict[str, str]]]] = []
    stale = [dict(row, tolerance="2e-15") for row in correct_rows]
    cases.append(("historical_stale_variable", stale))
    swapped = [dict(row) for row in correct_rows]
    swapped[1]["tolerance"], swapped[2]["tolerance"] = swapped[2]["tolerance"], swapped[1]["tolerance"]
    cases.append(("swapped_tolerance", swapped))
    duplicated = [dict(row) for row in correct_rows]
    duplicated[2]["tolerance"] = duplicated[1]["tolerance"]
    cases.append(("duplicated_tolerance", duplicated))
    cases.append(("missing_level", [dict(row) for row in correct_rows[:-1]]))
    shifted = [dict(row, level=str(index + 1)) for index, row in enumerate(correct_rows)]
    cases.append(("shifted_level", shifted))
    wrong_warning = [dict(row) for row in correct_rows]
    wrong_warning[4]["warning"], wrong_warning[5]["warning"] = wrong_warning[5]["warning"], wrong_warning[4]["warning"]
    cases.append(("wrong_warning_row", wrong_warning))
    stale_estimate = [dict(row) for row in correct_rows]
    stale_estimate[1]["estimate_equal_previous"] = "False"
    cases.append(("stale_estimate_flag", stale_estimate))
    wrong_error = [dict(row) for row in correct_rows]
    wrong_error[1]["error_behavior"] = "shrink"
    cases.append(("wrong_error_behavior", wrong_error))
    malformed = [dict(row) for row in correct_rows]
    malformed[0]["estimate_equal_previous"] = "unavailable"
    cases.append(("malformed_unavailable", malformed))
    results = []
    for name, rows in cases:
        failures = validator.compare_level_rows(rows, expected_rows)
        if not failures:
            raise AssertionError("corruption_not_detected:" + name)
        results.append({"case": name, "rejected": True, "failure_count": len(failures),
                        "failing_rows": sorted({item["row"] for item in failures if item["row"] is not None})})
    return results


def assemble() -> tuple[dict, dict, dict, list[dict], list[list[dict]], list[str]]:
    reference, onsets, levels, pieces, hashes, selected = retained_records()
    reviewed = reviewer.review_records(reference, onsets, levels, pieces, hashes)
    source_match, source_hash = warning_source_match(reviewed["warning"]["message"])
    public = reviewer.public_package(reviewed, source_match, source_hash)
    expected_rows = validator.expected_level_rows(levels, pieces, hashes)
    actual_rows = validator.parse_level_csv(public["level_summary.csv"])
    failures = validator.compare_level_rows(actual_rows, expected_rows)
    if failures:
        raise ValueError("reviewer_validator_disagreement")
    oracles = corruption_oracles(actual_rows, expected_rows)
    public["publication_validation.json"] = {
        "schema_version": 1, "accepted": True, "failure_count": 0,
        "validated_levels": 6, "independent_derivation": True,
        "reviewer_row_builder_called": False,
        "corruption_oracles": oracles,
    }
    private = {"schema_version": 1, "review": reviewed["private"],
               "facts": reviewed["facts"], "width_summary": reviewed["width_summary"]}
    authority = {"retained_records": selected, "scipy_source_sha256": source_hash}
    return public, private, authority, levels, pieces, hashes


def close(public: dict, private: dict, bindings: dict, authority: dict,
          levels: list[dict], pieces: list[list[dict]], hashes: list[str]) -> dict:
    local = OUT / "local"
    reviewer.atomic(local / "review.json", private)
    private_index = {"schema_version": 1, "files": {"review.json": reviewer.sha(local / "review.json")}}
    reviewer.atomic(local / "private_index.json", private_index)
    private_hash = reviewer.sha(local / "private_index.json")
    for name in reviewer.PUBLIC_FILES[:-1]:
        reviewer.atomic(OUT / name, public[name], raw=name.endswith(".csv"))
    qc = {
        "schema_version": 1, "status": "closed", "execution_valid": True,
        "classification": public["classification"], "readiness": public["readiness"],
        "retained_records": 68, "corrected_tolerance_rows": 6,
        "new_numerical_evaluations": 0, "empirical_records_opened": 0,
        "scientific_products_opened": 0, "exact_values_public": False,
        "independent_publication_validation": True,
        "private_index_sha256": private_hash,
    }
    reviewer.atomic(OUT / "qc.json", qc)
    outputs = {name: reviewer.sha(OUT / name) for name in reviewer.PUBLIC_FILES}
    manifest = {"schema_version": 1, "status": "closed", "outputs": outputs,
                "authority": {**authority, **bindings}, "private_index_sha256": private_hash}
    reviewer.atomic(OUT / "manifest.json", manifest)
    validator.validate_package(OUT, levels, pieces, hashes)
    return qc


def review() -> None:
    local = OUT / "local"
    local.mkdir(parents=True, exist_ok=True)
    reviewer.atomic(local / "attempt.marker", {"schema_version": 1, "session": "14aq", "exclusive": True})
    try:
        authority = preflight()
        public, private, bindings, levels, pieces, hashes = assemble()
        result = close(public, private, bindings, authority, levels, pieces, hashes)
    except BaseException as error:
        reviewer.atomic(local / "failure.json", {
            "schema_version": 1, "status": "invalid", "exception": type(error).__name__,
            "message": str(error), "traceback": traceback.format_exc(),
            "new_numerical_evaluations": 0, "empirical_records_opened": 0,
        })
        raise
    print(reviewer.canonical(result).decode().strip())


def publication_check() -> bool:
    _, _, levels, pieces, hashes, _ = retained_records()
    validator.validate_package(OUT, levels, pieces, hashes)
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "review", "publication-check"))
    command = parser.parse_args().command
    if command == "preflight":
        print(reviewer.canonical(preflight()).decode().strip())
    elif command == "review":
        review()
    else:
        print("publication-check:", publication_check())


if __name__ == "__main__":
    main()
