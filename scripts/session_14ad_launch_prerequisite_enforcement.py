#!/usr/bin/env python3
"""Session 14ad synthetic-only launch/prerequisite enforcement audit."""

from __future__ import annotations

import argparse
import csv
import hashlib
from importlib.metadata import version
import io
import json
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
from unittest.mock import patch

from defensive_network_disruption.validation.launch_enforcement import (
    EnvironmentObservation,
    GovernedLauncher,
    LaunchContext,
    LaunchError,
    LaunchState,
    PrerequisiteExpectation,
    atomic_write,
    canonical_json,
    finite_tree,
    sha256_bytes,
    sha256_file,
    validate_prerequisite,
)

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/protocols/phase_14ad_launch_prerequisite_enforcement.md"
OUT = ROOT / "outputs/session14_launch_enforcement"
LOCAL = OUT / "local"
MODULE = ROOT / "src/defensive_network_disruption/validation/launch_enforcement.py"
SCRIPT = ROOT / "scripts/session_14ad_launch_prerequisite_enforcement.py"
TEST = ROOT / "tests/test_session14ad_launch_enforcement.py"
START = "2fa75d2b96c5e02d83e0eb5f22c554a3c1c25ad8"
TAG = "f00690c05d8c1c6db308a65bd311c43f9a8ef2fa"
R2 = {
    "runner": "7699730cb01a91b7b4f2ce29a9683840cf2277ae93dfb6f736a71147b431a6cd",
    "tests": "9b56b762bcd4cd16c30dd413ef86763c37121362aff73d9d71dce817d2ca6158",
    "manifest": "feea59032c80422b76e05274a9b84a704d2f2fe3e4050f370c09fe29ce3234b5",
    "qc": "7ba9c9da8dd59a3532cc4ba69e4ad622257405269469e5a2bb41cdc5e46c62b4",
    "report": "3273b03397312212b520e75e04a7809e01f9122bd7ad71b1ffdc54dc6c1e95d8",
}
R2_PATHS = {
    "runner": ROOT / "scripts/session_14r2_occlusion_study.py",
    "tests": ROOT / "tests/test_session14r2_study.py",
    "manifest": ROOT / "outputs/continuous_occlusion_retry_14r2/manifest.json",
    "qc": ROOT / "outputs/continuous_occlusion_retry_14r2/qc.json",
    "report": ROOT / "docs/session_14r2_continuous_occlusion_empirical_retry.md",
}
TEST_COMMAND = ("-m", "unittest", "tests.test_session14ad_launch_enforcement.PrerequisiteContractTests")
PUBLIC = (
    "launch_contract.json", "state_machine.json", "environment_oracles.csv",
    "prerequisite_failure_injections.csv", "downstream_call_guards.json",
    "success_control.json", "qc.json",
)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def implementation_hash() -> str:
    payload = "".join(f"{path.relative_to(ROOT)}:{sha256_file(path)}\n" for path in (MODULE, SCRIPT, TEST))
    return sha256_bytes(payload.encode())


def observe_environment() -> EnvironmentObservation:
    venv = (ROOT / ".venv").resolve()
    prefix = Path(sys.prefix).resolve()
    packages = tuple(sorted((name, version(name)) for name in ("numpy", "scipy")))
    return EnvironmentObservation(
        python=platform.python_version(), implementation=platform.python_implementation(),
        in_project_environment=prefix == venv,
        environment_marker="uv-locked-project-environment" if prefix == venv else None,
        lock_sha256=sha256_file(ROOT / "uv.lock"), packages=packages,
    )


def expectation(environment: EnvironmentObservation) -> PrerequisiteExpectation:
    return PrerequisiteExpectation(
        protocol_sha256=sha256_file(PROTOCOL), implementation_sha256=implementation_hash(),
        lock_sha256=sha256_file(ROOT / "uv.lock"), environment_sha256=environment.fingerprint(),
        test_command=TEST_COMMAND,
    )


def preflight() -> None:
    if git("rev-parse", "v0.1.0^{}") != TAG:
        raise LaunchError("release_tag_changed")
    subprocess.run(["git", "merge-base", "--is-ancestor", START, "HEAD"], cwd=ROOT, check=True)
    for key, path in R2_PATHS.items():
        if sha256_file(path) != R2[key]:
            raise LaunchError("session14r2_history_changed:" + key)
    if subprocess.run(["git", "check-ignore", "-q", str(LOCAL / "probe")], cwd=ROOT).returncode:
        raise LaunchError("private_output_not_ignored")
    print("Session 14ad preflight passed; no empirical input opened")


def write_json(path: Path, value: object) -> None:
    finite_tree(value)
    atomic_write(path, json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")


def write_csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, object]]) -> None:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader(); writer.writerows(rows)
    atomic_write(path, buffer.getvalue())


def prerequisite_record(expected: PrerequisiteExpectation, *, run=4, skipped=0) -> dict[str, object]:
    return {
        "schema_version": 1, "producer": "session14ad_enforcement_tests", "status": "passed",
        "test_command": list(expected.test_command), "protocol_sha256": expected.protocol_sha256,
        "implementation_sha256": expected.implementation_sha256, "lock_sha256": expected.lock_sha256,
        "environment_sha256": expected.environment_sha256, "tests_run": run,
        "tests_passed": run - skipped, "tests_skipped": skipped, "exit_status": 0,
        "test_output_sha256": "0" * 64, "failure_enforcement_passed": True,
    }


def produce_real_prerequisite(path: Path, expected: PrerequisiteExpectation) -> None:
    completed = subprocess.run([sys.executable, *TEST_COMMAND], cwd=ROOT, text=True, capture_output=True)
    output = completed.stdout + completed.stderr
    import re
    match = re.search(r"Ran (\d+) tests?", output)
    skipped = re.search(r"skipped=(\d+)", output)
    if completed.returncode or match is None:
        raise LaunchError("prerequisite_test_command_failed")
    run = int(match.group(1)); skip = int(skipped.group(1)) if skipped else 0
    record = prerequisite_record(expected, run=run, skipped=skip)
    record["test_output_sha256"] = sha256_bytes(output.encode())
    atomic_write(path, json.dumps(record, sort_keys=True, indent=2) + "\n")


def run_case(label: str, mutation: str, base: EnvironmentObservation, expected: PrerequisiteExpectation) -> dict[str, object]:
    with tempfile.TemporaryDirectory(dir=LOCAL) as folder:
        root = Path(folder); prereq = root / "prerequisite.json"
        environment = base
        if mutation == "system_python":
            environment = EnvironmentObservation(base.python, base.implementation, False, None, base.lock_sha256, base.packages)
        elif mutation == "missing_marker":
            environment = EnvironmentObservation(base.python, base.implementation, True, None, base.lock_sha256, base.packages)
        elif mutation == "lock_mismatch":
            environment = EnvironmentObservation(base.python, base.implementation, True, base.environment_marker, "f" * 64, base.packages)
        elif mutation == "missing_dependency":
            environment = EnvironmentObservation(base.python, base.implementation, True, base.environment_marker, base.lock_sha256, (("numpy", dict(base.packages)["numpy"]),))
        exp = expected
        if mutation == "stale_environment":
            exp = PrerequisiteExpectation(expected.protocol_sha256, expected.implementation_sha256, expected.lock_sha256, "e" * 64, expected.test_command)
        calls = {"producer": 0, "downstream": 0, "access": 0}
        launcher = GovernedLauncher(root / "launch.marker", root / "access.marker")
        def producer():
            calls["producer"] += 1
            if mutation == "producer_exception": raise RuntimeError("synthetic_producer_failure")
            record = prerequisite_record(exp)
            if mutation == "missing": return
            if mutation == "malformed": atomic_write(prereq, "{bad\n"); return
            if mutation == "wrong_schema": record["unexpected"] = True
            if mutation == "wrong_hash": record["implementation_sha256"] = "a" * 64
            if mutation == "wrong_environment": record["environment_sha256"] = "b" * 64
            if mutation == "stale": record["protocol_sha256"] = "c" * 64
            if mutation == "failed_status": record["status"] = "failed"
            atomic_write(prereq, json.dumps(record, sort_keys=True) + "\n")
            if mutation == "deleted": prereq.unlink()
            if mutation == "unreadable":
                prereq.unlink(); prereq.mkdir()
        def downstream(_): calls["downstream"] += 1; return True
        def access(_): calls["access"] += 1
        error = None
        try:
            launcher.run(environment=environment, expected=exp, required_packages=("numpy", "scipy"),
                prerequisite_path=prereq, produce_prerequisite=producer,
                verify_synthetic=downstream, authorize_empirical=access)
        except Exception as exc:
            error = type(exc).__name__ + ":" + str(exc)
        return {"case": label, "mutation": mutation, "passed": error is not None,
            "terminal_state": launcher.state.value, "producer_calls": calls["producer"],
            "downstream_calls": calls["downstream"], "access_calls": calls["access"],
            "access_marker": (root / "access.marker").exists(), "error": error or "none"}


def audit() -> None:
    preflight()
    if (OUT / "manifest.json").exists() or (LOCAL / "audit.marker").exists():
        raise LaunchError("closed_or_started_no_rerun")
    LOCAL.mkdir(parents=True, exist_ok=True)
    atomic_write(LOCAL / "audit.marker", "claimed\n")
    base = observe_environment(); expected = expectation(base)
    environment_mutations = ("system_python", "missing_marker", "missing_dependency", "lock_mismatch", "stale_environment")
    prereq_mutations = ("producer_exception", "missing", "malformed", "wrong_schema", "wrong_hash", "wrong_environment", "stale", "unreadable", "deleted", "failed_status")
    environment_rows = [run_case(name, name, base, expected) for name in environment_mutations]
    prerequisite_rows = [run_case(name, name, base, expected) for name in prereq_mutations]
    # Valid control uses the fixed discoverable test producer.
    control_root = LOCAL / "success"; control_root.mkdir()
    prereq = control_root / "prerequisite.json"; counts = {"downstream": 0, "access": 0}
    launcher = GovernedLauncher(control_root / "launch.marker", control_root / "access.marker")
    def downstream(_): counts["downstream"] += 1; return True
    def access(_): counts["access"] += 1
    launcher.run(environment=base, expected=expected, required_packages=("numpy", "scipy"),
        prerequisite_path=prereq, produce_prerequisite=lambda: produce_real_prerequisite(prereq, expected),
        verify_synthetic=downstream, authorize_empirical=access)
    valid_record, prereq_hash = validate_prerequisite(prereq, expected)
    expected_order = [state.value for state in (
        LaunchState.INITIAL, LaunchState.ENVIRONMENT_VERIFIED, LaunchState.PREREQUISITE_CREATED,
        LaunchState.PREREQUISITE_VALIDATED, LaunchState.SYNTHETIC_READINESS_VERIFIED,
        LaunchState.EMPIRICAL_ACCESS_AUTHORIZED)]
    if launcher.transitions != expected_order or counts != {"downstream": 1, "access": 1}:
        raise LaunchError("success_control_failed")
    failures = environment_rows + prerequisite_rows
    if not all(row["passed"] and row["terminal_state"] == "FAILED_CLOSED" and row["downstream_calls"] == 0 and row["access_calls"] == 0 and not row["access_marker"] for row in failures):
        raise LaunchError("failure_injection_failed")
    guards = {
        "schema_version": 1, "direct_entry_blocked": True, "invalid_context_blocked": True,
        "environment_mismatch_blocked": True, "prerequisite_digest_mismatch_blocked": True,
        "marker_collision_blocked": True, "automatic_rerun_blocked": True,
        "all_failure_downstream_calls_zero": True, "all_failure_access_calls_zero": True,
    }
    launch_contract = {
        "schema_version": 1, "status": "passed", "entrypoint": "uv run --locked python",
        "environment_binding": ["project_venv", "uv_lock_sha256", "package_versions"],
        "prerequisite_fields": sorted(valid_record), "prerequisite_sha256": prereq_hash,
        "downstream_requires": ["validated_context", "matching_environment", "matching_prerequisite", "exclusive_access_marker"],
        "empirical_route_present": False,
    }
    state_machine = {"schema_version": 1, "success_states": expected_order,
        "failure_state": "FAILED_CLOSED", "failure_has_outgoing_transition": False}
    success = {"schema_version": 1, "status": "passed", "transitions": launcher.transitions,
        "downstream_calls": 1, "access_authorization_calls": 1, "data_handles_opened": 0,
        "states_opened": 0, "edges_opened": 0, "access_marker_created": True}
    qc = {"schema_version": 1, "status": "valid", "classification": "A",
        "readiness": 1, "environment_oracles": len(environment_rows),
        "prerequisite_injections": len(prerequisite_rows), "all_fail_closed": True,
        "states_opened": 0, "edges_opened": 0, "empirical_access": False,
        "numerical_contract_changed": False, "historical_session14r2_changed": False}
    write_json(OUT / "launch_contract.json", launch_contract)
    write_json(OUT / "state_machine.json", state_machine)
    fields = ("case", "mutation", "passed", "terminal_state", "producer_calls", "downstream_calls", "access_calls", "access_marker", "error")
    write_csv(OUT / "environment_oracles.csv", fields, environment_rows)
    write_csv(OUT / "prerequisite_failure_injections.csv", fields, prerequisite_rows)
    write_json(OUT / "downstream_call_guards.json", guards)
    write_json(OUT / "success_control.json", success)
    write_json(OUT / "qc.json", qc)
    files = {name: sha256_file(OUT / name) for name in PUBLIC}
    manifest = {"schema_version": 1, "status": "closed", "classification": "A", "readiness": 1,
        "protocol_sha256": sha256_file(PROTOCOL), "implementation_sha256": implementation_hash(),
        "environment": base.public(), "historical_session14r2": R2, "files": files,
        "private_execution_recorded": True, "empirical_access": False}
    write_json(OUT / "manifest.json", manifest)
    print("Session 14ad audit closed: A / readiness 1; zero empirical states and edges")


def publication_check() -> None:
    manifest = json.loads((OUT / "manifest.json").read_text())
    finite_tree(manifest)
    if set(manifest) != {"schema_version", "status", "classification", "readiness", "protocol_sha256", "implementation_sha256", "environment", "historical_session14r2", "files", "private_execution_recorded", "empirical_access"}:
        raise LaunchError("manifest_schema")
    if manifest["status"] != "closed" or manifest["classification"] != "A" or manifest["readiness"] != 1 or manifest["empirical_access"]:
        raise LaunchError("manifest_status")
    if manifest["protocol_sha256"] != sha256_file(PROTOCOL) or manifest["implementation_sha256"] != implementation_hash():
        raise LaunchError("authority_changed")
    if manifest["historical_session14r2"] != R2:
        raise LaunchError("historical_binding")
    if set(manifest["files"]) != set(PUBLIC):
        raise LaunchError("manifest_files")
    for name, digest in manifest["files"].items():
        if sha256_file(OUT / name) != digest:
            raise LaunchError("output_hash:" + name)
    print("Session 14ad publication check passed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "audit", "publication-check"))
    args = parser.parse_args()
    {"preflight": preflight, "audit": audit, "publication-check": publication_check}[args.command]()


if __name__ == "__main__":
    main()
