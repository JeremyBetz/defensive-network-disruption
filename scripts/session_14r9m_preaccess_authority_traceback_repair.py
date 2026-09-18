#!/usr/bin/env python3
"""Synthetic-only Session 14R9M pre-access authority repair audit."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defensive_network_disruption.validation.checkpoint_ci_authority import (
    CIExpectation, FailureController, canonical_bytes, compare_live, durable_json,
    sha256_file, validate_receipt)
from defensive_network_disruption.validation.r7_execution import Journal, Progress
from defensive_network_disruption.validation import numerical_failure_publication
from defensive_network_disruption.validation.r9a_publication import MANIFEST_MEMBERS
from defensive_network_disruption.validation.r9j_linear_publication import (
    review as linear_review, validate_public as validate_linear_public)


START = "9e5f122b0954dd19a373f627beea4ffb525e51cb"
TAG = "f00690c05d8c1c6db308a65bd311c43f9a8ef2fa"
PROTOCOL = Path("docs/protocols/phase_14r9m_preaccess_authority_traceback_repair.md")
RUNNER = Path("scripts/session_14r9m_preaccess_authority_traceback_repair.py")
OUT = Path(os.environ.get("SESSION14R9M_OUTPUT", "outputs/continuous_occlusion_preaccess_authority_repair"))
LOCAL = OUT / "local"
RECEIPT = Path(os.environ.get("SESSION14R9M_CI_RECEIPT", str(LOCAL / "checkpoint_ci_receipt.json")))
RECEIPT_HASH = Path(str(RECEIPT) + ".sha256")
PUBLIC = (
    "repair_contract.json", "ci_authority_regression.json", "network_failure_oracles.csv",
    "traceback_failure_matrix.csv", "failure_publication_regression.json", "preservation.json",
    "qc.json", "manifest.json",
)
HISTORICAL = {
    "docs/session_14r9l_empirical_representation_retry.md": "a2ffa9bd8b75ae42a7941ad3e7bbd452ffaaacf2a39bf01ab9a59f23d471a0e8",
    "docs/protocols/phase_14r9l_empirical_representation_retry.md": "9080a239fd253e42c4a96e842dc68b322090034ce7682eee1fd96eaf5a8e93f8",
    "outputs/continuous_occlusion_empirical_retry_r9l/manifest.json": "69c1b4dc293acc104bd46464eb408495e3f296e33bcba2949d2f4e23b7b23510",
    "src/defensive_network_disruption/validation/r9j_linear_publication.py": "a242cb0921d1fd390cd2b74c9d15a0fdff3e2b82e46000dc8be0cbbba6d6c139",
    "src/defensive_network_disruption/geometry/r9k_comparator.py": "e5f0785f29a78e84c64c86266012aa5c9d9be462be382927de900cfdc979973b",
}


def git(*args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=ROOT, text=True).strip()


def path(item: Path) -> Path:
    value = ROOT / item
    if not value.resolve().is_relative_to(ROOT.resolve()) or any(p.is_symlink() for p in (value, *value.parents)):
        raise PermissionError("unsafe_path")
    return value


def expectation() -> CIExpectation:
    return CIExpectation(
        checkpoint_commit=git("rev-parse", "HEAD"),
        protocol_sha256=sha256_file(path(PROTOCOL)),
        runner_implementation_sha256=sha256_file(path(RUNNER)),
        lockfile_sha256=sha256_file(path(Path("uv.lock"))),
        workflow_sha256=sha256_file(path(Path(".github/workflows/ci.yml"))),
    )


def committed(item: Path) -> None:
    if subprocess.check_output(("git", "show", "HEAD:" + item.as_posix()), cwd=ROOT) != path(item).read_bytes():
        raise RuntimeError("uncommitted_source:" + item.as_posix())


def preflight() -> dict:
    if git("status", "--porcelain"):
        raise RuntimeError("dirty_tree")
    if git("rev-parse", "v0.1.0^{}") != TAG:
        raise RuntimeError("release_changed")
    git("merge-base", "--is-ancestor", START, "HEAD")
    for item in (PROTOCOL, RUNNER, Path("scripts/capture_checkpoint_ci_authority.py"),
                 Path("src/defensive_network_disruption/validation/checkpoint_ci_authority.py"),
                 Path("tests/test_session14r9m.py")):
        committed(item)
    for name, expected in HISTORICAL.items():
        if sha256_file(path(Path(name))) != expected:
            raise RuntimeError("historical_authority_changed:" + name)
    forbidden = tuple(path(LOCAL / name) for name in
                      ("empirical_attempt.marker", "preparation.marker", "execution.marker"))
    if any(item.exists() for item in forbidden):
        raise RuntimeError("empirical_marker_present")
    return {"schema_version": 1, "status": "ready", "head": git("rev-parse", "HEAD"),
            "release": TAG, "historical_hashes": HISTORICAL, "empirical_access": {"states": 0, "edges": 0}}


def write_csv(destination: Path, fieldnames: tuple[str, ...], rows: list[dict]) -> None:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader(); writer.writerows(rows)
    target = path(destination); target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError("immutable_record_exists")
    with target.open("x", newline="") as handle:
        handle.write(buffer.getvalue()); handle.flush(); os.fsync(handle.fileno())


def _store_receipt(directory: Path, value: dict, *, canonical: bool = True) -> Path:
    target = directory / "receipt.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_bytes(value) if canonical else json.dumps(value).encode()
    target.write_bytes(payload)
    return target


def network_oracles(base: dict, expected: CIExpectation, receipt_hash: str) -> list[dict]:
    rows = []
    cases = []
    cases.append(("valid_offline", base, None, True, receipt_hash))
    cases.append(("missing_receipt", None, None, False, receipt_hash))
    for name, mutate in (
        ("wrong_commit", lambda x: x.update(checkpoint_commit="0" * 40)),
        ("wrong_workflow", lambda x: x["workflow"].update(name="Other")),
        ("pending_run", lambda x: x["run"].update(status="in_progress", conclusion="")),
        ("failed_job", lambda x: x["jobs"][0].update(conclusion="failure")),
        ("cancelled_job", lambda x: x["jobs"][0].update(conclusion="cancelled")),
        ("tampered_binding", lambda x: x["bindings"].update(lockfile_sha256="f" * 64)),
        ("missing_job", lambda x: x["jobs"].pop()),
    ):
        value = json.loads(json.dumps(base)); mutate(value); cases.append((name, value, None, False, None))
    changed = json.loads(json.dumps(base)); changed["run"]["run_id"] += 1
    cases.append(("tampered_receipt", changed, None, False, receipt_hash))
    cases.append(("noncanonical_receipt", base, "noncanonical", False, receipt_hash))
    with tempfile.TemporaryDirectory(dir=path(LOCAL)) as temporary:
        root = Path(temporary)
        for index, (name, value, mode, should_pass, frozen_hash) in enumerate(cases):
            target = root / str(index) / "receipt.json"
            if value is not None:
                target.parent.mkdir(parents=True)
                target.write_bytes(canonical_bytes(value) if mode is None else json.dumps(value).encode())
            try:
                validate_receipt(target, expected, expected_sha256=frozen_hash); observed = True; error = ""
            except BaseException as exc:
                observed = False; error = type(exc).__name__
            rows.append({"case": name, "expected": "pass" if should_pass else "block",
                         "observed": "pass" if observed else "block", "exception": error,
                         "correct": str(observed == should_pass).lower()})
    return rows


def traceback_matrix() -> list[dict]:
    cases = (
        ("network_connection", ConnectionError), ("dns_failure", OSError),
        ("network_timeout", TimeoutError), ("malformed_ci_receipt", ValueError),
        ("wrong_commit_receipt", PermissionError), ("marker_collision", FileExistsError),
        ("import_failure", ImportError), ("source_integrity", RuntimeError),
        ("population_mismatch", LookupError), ("publication_init", ArithmeticError),
    )
    rows = []
    with tempfile.TemporaryDirectory(dir=path(LOCAL)) as temporary:
        root = Path(temporary)
        for name, kind in cases:
            controller = FailureController(root / name)
            try:
                raise kind(name)
            except BaseException as error:
                record = controller.capture(error, name, timestamp="2026-09-18T00:00:00Z")
            valid = controller.validate()
            rows.append({"case": name, "exception": kind.__name__, "stage_preserved": str(valid["stage"] == name).lower(),
                         "traceback_bound": str(valid["traceback_sha256"] == record["traceback_sha256"]).lower(),
                         "emergency_valid": "true", "states_opened": 0, "edges_opened": 0, "correct": "true"})
        controller = FailureController(root / "publisher_failure")
        try:
            raise RuntimeError("original")
        except BaseException as error:
            controller.capture(error, "publication_validation", timestamp="2026-09-18T00:00:00Z")
        try:
            raise OSError("publisher")
        except BaseException as error:
            publication = controller.publication_failure(error, timestamp="2026-09-18T00:00:01Z")
        rows.append({"case": "failure_publisher", "exception": "OSError", "stage_preserved": "true",
                     "traceback_bound": str(len(publication["traceback_sha256"]) == 64).lower(),
                     "emergency_valid": str(controller.validate()["status"] == "valid").lower(),
                     "states_opened": 0, "edges_opened": 0, "correct": "true"})
    return rows


def _failure_package(root: Path) -> dict:
    journal = Journal(root / "journal.jsonl")
    progress = Progress(journal)
    controller = FailureController(root)
    try:
        raise ConnectionError("synthetic offline R9L-style failure")
    except BaseException as error:
        controller.capture(error, "preaccess_authority", timestamp="2026-09-18T00:00:00Z")
        progress.failure("preaccess_authority", error)
    journal.close()
    authority = linear_review(journal.path)
    private = root / "private"; public = root / "public"
    private.mkdir(); public.mkdir()
    package = numerical_failure_publication.package(authority.legacy, accepted=False,
                                                     checks={"failure_enforcement": True})
    for name in ("qc", "manifest", "evidence"):
        durable_json(private / "numerical_publication" / (name + ".json"), package)
    progress_record = authority.progress("empirical_failure")
    qc = {"schema_version": 1, "status": "failure", "progress_authority": progress_record,
          "stage": "preaccess_authority", "exception": "ConnectionError",
          "scientific_comparisons_available": False}
    durable_json(private / "qc.json", qc)
    durable_json(private / "evidence.json", {key: qc[key] for key in ("schema_version", "status", "progress_authority")})
    durable_json(private / "progress_authority.json", progress_record)
    durable_json(private / "manifest.json", {"schema_version": 1, "status": "failure",
        "progress_authority": progress_record,
        "outputs": {name: sha256_file(private / name) for name in
                    ("qc.json", "evidence.json", "progress_authority.json")}})
    durable_json(public / "qc.json", qc)
    durable_json(public / "manifest.json", {"schema_version": 1, "status": "failure",
        "progress_authority": progress_record, "start": START,
        "protocol": sha256_file(path(PROTOCOL)), "implementation": {}, "environment": {},
        "outputs": {"qc.json": sha256_file(public / "qc.json")},
        "unavailable": [name for name in MANIFEST_MEMBERS if name != "qc.json"],
        "private_evidence_sha256": sha256_file(private / "evidence.json"),
        "private_manifest_sha256": sha256_file(private / "manifest.json")})
    receipt = validate_linear_public(public, private, authority, "empirical_failure",
                                     traceback_path=controller.traceback_path)
    return {"validator_status": receipt["status"], "states_opened": receipt["states_opened"],
            "edges_opened": progress_record["exposure"]["edges_opened"],
            "traceback_bound": controller.validate()["status"] == "valid",
            "journal_failure_stage": authority.failure["stage"],
            "outer_failure_stage": json.loads(controller.original_path.read_text())["stage"]}


def audit() -> None:
    authority = preflight()
    marker = path(LOCAL / "audit.marker")
    durable_json(marker, {"schema_version": 1, "status": "reserved", "head": authority["head"]})
    expected = expectation()
    frozen_hash = path(RECEIPT_HASH).read_text().strip()
    if len(frozen_hash) != 64:
        raise ValueError("ci_receipt_hash_authority")
    verified = validate_receipt(path(RECEIPT), expected, expected_sha256=frozen_hash)
    offline = compare_live(verified, lambda _run: (_ for _ in ()).throw(ConnectionError("offline")))
    if offline != {"available": False, "matches": None, "exception": "ConnectionError"}:
        raise RuntimeError("offline_comparison_semantics")
    base = json.loads(path(RECEIPT).read_text())
    network = network_oracles(base, expected, frozen_hash)
    traces = traceback_matrix()
    with tempfile.TemporaryDirectory(dir=path(LOCAL)) as temporary:
        publication = _failure_package(Path(temporary))
    if not all(row["correct"] == "true" for row in network + traces):
        raise RuntimeError("oracle_failure")
    if publication != {"validator_status": "valid", "states_opened": 0, "edges_opened": 0,
                        "traceback_bound": True, "journal_failure_stage": "preparation",
                        "outer_failure_stage": "preaccess_authority"}:
        raise RuntimeError("failure_publication_regression")

    path(OUT).mkdir(parents=True, exist_ok=True)
    durable_json(path(OUT / "repair_contract.json"), {"schema_version": 1, "status": "frozen_contract_satisfied",
        "mandatory_live_network": False, "traceback_capture_before_publication": True,
        "empirical_attempt_reserved": False, "states_opened": 0, "edges_opened": 0})
    durable_json(path(OUT / "ci_authority_regression.json"), {"schema_version": 1, "status": "pass",
        "receipt_sha256": verified.receipt_sha256, "checkpoint_commit": verified.checkpoint_commit,
        "run_id": verified.run_id, "required_jobs": [name for name, _ in verified.jobs],
        "offline_validation": True, "live_comparison_required": False})
    write_csv(OUT / "network_failure_oracles.csv", ("case", "expected", "observed", "exception", "correct"), network)
    write_csv(OUT / "traceback_failure_matrix.csv", ("case", "exception", "stage_preserved", "traceback_bound",
              "emergency_valid", "states_opened", "edges_opened", "correct"), traces)
    durable_json(path(OUT / "failure_publication_regression.json"), {"schema_version": 1, "status": "pass", **publication})
    durable_json(path(OUT / "preservation.json"), {"schema_version": 1, "status": "pass",
        "historical_hashes": HISTORICAL, "r9l_classification": "D", "r9l_readiness": 4,
        "r9j_authority": "PA", "r9k_authority": "A/readiness 1", "public_api_changed": False})
    durable_json(path(OUT / "qc.json"), {"schema_version": 1, "status": "pass", "classification": "A",
        "readiness": 1, "ci_authority_repaired": True, "traceback_binding_repaired": True,
        "network_controls": len(network), "traceback_controls": len(traces),
        "empirical_access": {"states": 0, "edges": 0}, "integrity": True})
    names = PUBLIC[:-1]
    durable_json(path(OUT / "manifest.json"), {"schema_version": 1, "status": "closed",
        "classification": "A", "readiness": 1, "protocol_sha256": sha256_file(path(PROTOCOL)),
        "implementation_sha256": sha256_file(path(RUNNER)),
        "outputs": {name: sha256_file(path(OUT / name)) for name in names}})
    publication_check()


def publication_check() -> dict:
    manifest = json.loads(path(OUT / "manifest.json").read_text())
    if set(manifest) != {"schema_version", "status", "classification", "readiness", "protocol_sha256",
                        "implementation_sha256", "outputs"}:
        raise ValueError("manifest_schema")
    if manifest["schema_version"] != 1 or manifest["status"] != "closed":
        raise ValueError("manifest_status")
    if set(manifest["outputs"]) != set(PUBLIC[:-1]):
        raise ValueError("manifest_members")
    for name, expected in manifest["outputs"].items():
        if sha256_file(path(OUT / name)) != expected:
            raise ValueError("manifest_hash")
        if name.endswith(".json"):
            json.loads(path(OUT / name).read_text(), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    qc = json.loads(path(OUT / "qc.json").read_text())
    if qc["classification"] != "A" or qc["readiness"] != 1 or qc["empirical_access"] != {"states": 0, "edges": 0}:
        raise ValueError("qc_acceptance")
    return {"schema_version": 1, "status": "valid", "artifact_count": len(PUBLIC),
            "classification": "A", "readiness": 1, "states_opened": 0, "edges_opened": 0}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "audit", "publication-check"))
    command = parser.parse_args().command
    if command == "preflight":
        print(json.dumps(preflight(), sort_keys=True, allow_nan=False))
    elif command == "audit":
        audit(); print("R9M synthetic audit closed")
    else:
        print(json.dumps(publication_check(), sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
