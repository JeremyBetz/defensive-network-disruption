#!/usr/bin/env python3
"""Governed read-only Session 14ap retained-evidence review."""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.metadata
import importlib.util
from pathlib import Path
import re
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "src/defensive_network_disruption/validation/terminal_error_review.py"
SPEC = importlib.util.spec_from_file_location("terminal_error_review", MODULE)
reviewer = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(reviewer)

START = "fba26be949b7cbe3ded168222b3a9f8e9ccbddfb"
TAG = "f00690c05d8c1c6db308a65bd311c43f9a8ef2fa"
PROTOCOL = "docs/protocols/phase_14ap_terminal_error_evidence_review.md"
SOURCES = (PROTOCOL, str(MODULE.relative_to(ROOT)),
           "scripts/session_14ap_terminal_error_evidence_review.py",
           "tests/test_session14ap_terminal_error_review.py")
OLD = ROOT / "outputs/session14ao_onset_only_adaptive_convergence"
OUT = ROOT / "outputs/continuous_occlusion_terminal_error_review"
MANIFEST_HASH = "367cec3ea22163af15c299b96e3792424707603b5920257eed40b3e06e5335f3"
INDEX_HASH = "23b4264f0bce761cc17cb61357cd1fd39b6a418e5bce9938314898f8025d3955"
SELECTION_HASH = "66061ced1444c9e818263d6ed4651a281eb53bfa1c9fd857e9e966958e4a5d2a"
SCIPY_SOURCE_HASH = "c59e4133f23ef272e488204c217caf36a38b5921fe0ffeeb2a8f1b804f5ba0d9"


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
    for name in SOURCES:
        if subprocess.check_output(("git", "show", "HEAD:" + name), cwd=ROOT) != (ROOT / name).read_bytes():
            raise RuntimeError("uncommitted_source")
    history = {}
    for name in git("ls-tree", "-r", "--name-only", START).splitlines():
        old = subprocess.check_output(("git", "show", START + ":" + name), cwd=ROOT)
        now = (ROOT / name).read_bytes()
        if name == "docs/research_log.md":
            if not now.startswith(old):
                raise RuntimeError("research_log_rewritten")
        elif now != old:
            raise RuntimeError("historical_file_changed")
        history[name] = hashlib.sha256(old).hexdigest()
    if reviewer.sha(OLD / "manifest.json") != MANIFEST_HASH:
        raise RuntimeError("retained_manifest_changed")
    if reviewer.sha(OLD / "local/private_index.json") != INDEX_HASH:
        raise RuntimeError("retained_index_changed")
    source, source_hash = scipy_source()
    return {
        "start": START, "implementation_commit": git("rev-parse", "HEAD"),
        "sources": {name: reviewer.sha(ROOT / name) for name in SOURCES},
        "historical_tree_sha256": reviewer.digest(history),
        "retained_manifest_sha256": MANIFEST_HASH,
        "retained_private_index_sha256": INDEX_HASH,
        "retained_selection_sha256": SELECTION_HASH,
        "lock_sha256": reviewer.sha(ROOT / "uv.lock"),
        "scipy_version": importlib.metadata.version("scipy"),
        "scipy_source_sha256": source_hash,
        "scipy_source_relative": "scipy/integrate/_quadpack_py.py",
    }


def scipy_source() -> tuple[Path, str]:
    if importlib.metadata.version("scipy") != "1.18.1":
        raise RuntimeError("scipy_version")
    distribution = importlib.metadata.distribution("scipy")
    source = Path(distribution.locate_file("scipy/integrate/_quadpack_py.py"))
    source_hash = reviewer.sha(source)
    if source_hash != SCIPY_SOURCE_HASH:
        raise RuntimeError("scipy_source_changed")
    return source, source_hash


def retained_records() -> tuple[dict, dict, list[dict], list[list[dict]], list[str], dict[str, str]]:
    manifest = reviewer.strict_load(OLD / "manifest.json")
    if manifest["private_index_sha256"] != INDEX_HASH:
        raise ValueError("manifest_index_binding")
    index = reviewer.strict_load(OLD / "local/private_index.json")
    if set(index) != {"files"} or type(index["files"]) is not dict:
        raise ValueError("private_index_schema")
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
    reference = loaded["000001_reference.json"]
    onsets = loaded["000003_onsets.json"]
    levels = []
    pieces = []
    level_hashes = []
    for level_number in reviewer.LEVEL_NUMBERS:
        level_name = f"{level_number:06d}_level.json"
        comparison_name = f"{level_number + 1:06d}_comparison.json"
        level = loaded[level_name]
        comparison = loaded[comparison_name]
        if set(comparison) != {"anchor_match", "delta", "delta_exceeds_gate", "extra_work",
                              "piecewise_within_gate", "reference_error", "reference_error_decreased",
                              "reference_within_gate", "relative_error", "trace_changed"}:
            raise ValueError("comparison_schema")
        levels.append(level)
        level_hashes.append(selected[level_name])
        pieces.append([loaded[f"{number:06d}_piece.json"]
                       for number in range(level_number - 17, level_number, 2)])
    return reference, onsets, levels, pieces, level_hashes, selected


def warning_source_match(message: str) -> tuple[bool, str]:
    source, source_hash = scipy_source()
    text = source.read_text()
    normalized = " ".join(message.split())
    constants = [node.value for node in ast.walk(ast.parse(text))
                 if isinstance(node, ast.Constant) and isinstance(node.value, str)]
    return normalized in {" ".join(value.split()) for value in constants}, source_hash


def assemble() -> tuple[dict, dict, dict]:
    reference, onsets, levels, pieces, level_hashes, selected = retained_records()
    reviewed = reviewer.review_records(reference, onsets, levels, pieces, level_hashes)
    source_match, source_hash = warning_source_match(reviewed["warning"]["message"])
    public = reviewer.public_package(reviewed, source_match, source_hash)
    private = {"schema_version": 1, "review": reviewed["private"],
               "facts": reviewed["facts"], "width_summary": reviewed["width_summary"]}
    authority = {"retained_records": selected, "scipy_source_sha256": source_hash}
    return public, private, authority


def close(public: dict, private: dict, authority: dict, preflight_authority: dict) -> dict:
    local = OUT / "local"
    reviewer.atomic(local / "review.json", private)
    private_index = {"schema_version": 1,
                     "files": {"review.json": reviewer.sha(local / "review.json")}}
    reviewer.atomic(local / "private_index.json", private_index)
    private_hash = reviewer.sha(local / "private_index.json")
    for name in reviewer.PUBLIC_FILES[:-1]:
        value = public[name]
        reviewer.atomic(OUT / name, value, raw=name.endswith(".csv"))
    qc = {
        "schema_version": 1, "status": "closed", "execution_valid": True,
        "classification": public["classification"], "readiness": public["readiness"],
        "retained_records": 68, "new_numerical_evaluations": 0,
        "empirical_records_opened": 0, "exact_values_public": False,
        "private_index_sha256": private_hash,
    }
    reviewer.atomic(OUT / "qc.json", qc)
    outputs = {name: reviewer.sha(OUT / name) for name in reviewer.PUBLIC_FILES}
    manifest = {"schema_version": 1, "status": "closed", "outputs": outputs,
                "authority": {**preflight_authority, **authority},
                "private_index_sha256": private_hash}
    reviewer.atomic(OUT / "manifest.json", manifest)
    expected = {name: public[name] for name in reviewer.PUBLIC_FILES[:-1]}
    expected["qc.json"] = qc
    reviewer.validate_public(OUT, expected)
    return qc


def review() -> None:
    local = OUT / "local"
    local.mkdir(parents=True, exist_ok=True)
    reviewer.atomic(local / "attempt.marker", {"schema_version": 1, "session": "14ap", "exclusive": True})
    try:
        authority = preflight()
        public, private, bindings = assemble()
        result = close(public, private, bindings, authority)
    except BaseException as error:
        reviewer.atomic(local / "failure.json", {
            "schema_version": 1, "status": "invalid", "exception": type(error).__name__,
            "message": str(error), "traceback": traceback.format_exc(),
            "new_numerical_evaluations": 0, "empirical_records_opened": 0,
        })
        raise
    print(reviewer.canonical(result).decode().strip())


def publication_check() -> bool:
    public, _, _ = assemble()
    expected = {name: public[name] for name in reviewer.PUBLIC_FILES[:-1]}
    expected["qc.json"] = reviewer.strict_load(OUT / "qc.json")
    return reviewer.validate_public(OUT, expected)


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
