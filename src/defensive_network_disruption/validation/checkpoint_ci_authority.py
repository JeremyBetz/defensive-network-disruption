"""Internal checkpoint-CI and pre-access failure authority.

This module is deliberately standard-library only.  Network capture is an
explicit pre-run operation; validation never contacts a remote service.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import traceback
from typing import Callable, Mapping


REQUIRED_JOBS = ("distribution", "test (3.11)", "test (3.13)")
AUTHORITY_ID = "checkpoint_ci_authority_v1"
REPOSITORY = "JeremyBetz/defensive-network-disruption"


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True, allow_nan=False) + "\n").encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1_048_576), b""):
            digest.update(block)
    return digest.hexdigest()


def durable_bytes(path: Path, payload: bytes) -> None:
    path = Path(path)
    if path.exists() or path.is_symlink():
        raise FileExistsError("immutable_record_exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_name("." + path.name + ".pending")
    with pending.open("xb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.link(pending, path)
    pending.unlink()
    directory = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def durable_json(path: Path, value: object) -> None:
    durable_bytes(path, canonical_bytes(value))


@dataclass(frozen=True)
class CIExpectation:
    checkpoint_commit: str
    protocol_sha256: str
    runner_implementation_sha256: str
    lockfile_sha256: str
    workflow_sha256: str
    workflow_path: str = ".github/workflows/ci.yml"
    workflow_name: str = "CI"
    repository: str = REPOSITORY
    required_jobs: tuple[str, ...] = REQUIRED_JOBS


@dataclass(frozen=True)
class VerifiedCIAuthority:
    receipt_sha256: str
    checkpoint_commit: str
    run_id: int
    jobs: tuple[tuple[str, int], ...]
    _seal: object


_SEAL = object()


def _require_string(value: object, name: str) -> str:
    if type(value) is not str or not value:
        raise ValueError("ci_receipt_" + name)
    return value


def _job_record(job: Mapping[str, object]) -> dict:
    expected = {"databaseId", "name", "status", "conclusion", "startedAt", "completedAt", "url"}
    if set(job) != expected:
        raise ValueError("ci_capture_job_schema")
    if type(job["databaseId"]) is not int or job["databaseId"] <= 0:
        raise ValueError("ci_capture_job_id")
    return {
        "completed_at": _require_string(job["completedAt"], "job_completed"),
        "conclusion": _require_string(job["conclusion"], "job_conclusion"),
        "job_id": job["databaseId"],
        "name": _require_string(job["name"], "job_name"),
        "started_at": _require_string(job["startedAt"], "job_started"),
        "status": _require_string(job["status"], "job_status"),
        "url": _require_string(job["url"], "job_url"),
    }


def receipt_from_github(run: Mapping[str, object], expectation: CIExpectation,
                        *, captured_at: str) -> dict:
    expected = {"databaseId", "headSha", "name", "workflowName", "status", "conclusion",
                "createdAt", "updatedAt", "url", "jobs"}
    if set(run) != expected:
        raise ValueError("ci_capture_run_schema")
    if run["headSha"] != expectation.checkpoint_commit:
        raise ValueError("ci_capture_wrong_commit")
    if run["workflowName"] != expectation.workflow_name or run["name"] != expectation.workflow_name:
        raise ValueError("ci_capture_wrong_workflow")
    jobs = tuple(sorted((_job_record(item) for item in run["jobs"]), key=lambda item: item["name"]))
    by_name = {item["name"]: item for item in jobs}
    if len(by_name) != len(jobs) or set(by_name) != set(expectation.required_jobs):
        raise ValueError("ci_capture_required_jobs")
    if run["status"] != "completed" or run["conclusion"] != "success":
        raise ValueError("ci_capture_run_not_successful")
    if any(item["status"] != "completed" or item["conclusion"] != "success" for item in jobs):
        raise ValueError("ci_capture_job_not_successful")
    if type(run["databaseId"]) is not int or run["databaseId"] <= 0:
        raise ValueError("ci_capture_run_id")
    return {
        "authority_id": AUTHORITY_ID,
        "bindings": {
            "lockfile_sha256": expectation.lockfile_sha256,
            "protocol_sha256": expectation.protocol_sha256,
            "runner_implementation_sha256": expectation.runner_implementation_sha256,
            "workflow_sha256": expectation.workflow_sha256,
        },
        "checkpoint_commit": expectation.checkpoint_commit,
        "jobs": list(jobs),
        "provenance": {
            "captured_at": _require_string(captured_at, "capture_timestamp"),
            "method": "authenticated_github_cli",
        },
        "repository": expectation.repository,
        "required_jobs": list(expectation.required_jobs),
        "run": {
            "completed_at": _require_string(run["updatedAt"], "run_completed"),
            "conclusion": _require_string(run["conclusion"], "run_conclusion"),
            "created_at": _require_string(run["createdAt"], "run_created"),
            "run_id": run["databaseId"],
            "status": _require_string(run["status"], "run_status"),
            "url": _require_string(run["url"], "run_url"),
        },
        "schema_version": 1,
        "workflow": {"name": expectation.workflow_name, "path": expectation.workflow_path},
    }


def capture_github_receipt(path: Path, run_id: int, expectation: CIExpectation,
                           *, command: Callable[..., bytes] = subprocess.check_output,
                           captured_at: str | None = None) -> dict:
    raw = command(("gh", "run", "view", str(run_id), "--json",
                   "databaseId,headSha,name,workflowName,status,conclusion,createdAt,updatedAt,url,jobs"))
    if isinstance(raw, bytes):
        raw = raw.decode()
    run = json.loads(raw)
    timestamp = captured_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    receipt = receipt_from_github(run, expectation, captured_at=timestamp)
    durable_json(path, receipt)
    return receipt


def validate_receipt(path: Path, expectation: CIExpectation, *, expected_sha256: str | None = None) -> VerifiedCIAuthority:
    raw = Path(path).read_bytes()
    actual_sha256 = sha256_bytes(raw)
    if expected_sha256 is not None and actual_sha256 != expected_sha256:
        raise ValueError("ci_receipt_hash")
    try:
        receipt = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("ci_receipt_malformed") from error
    if canonical_bytes(receipt) != raw:
        raise ValueError("ci_receipt_noncanonical")
    expected_top = {"authority_id", "bindings", "checkpoint_commit", "jobs", "provenance",
                    "repository", "required_jobs", "run", "schema_version", "workflow"}
    if set(receipt) != expected_top or receipt["schema_version"] != 1 or receipt["authority_id"] != AUTHORITY_ID:
        raise ValueError("ci_receipt_schema")
    if receipt["checkpoint_commit"] != expectation.checkpoint_commit:
        raise ValueError("ci_receipt_wrong_commit")
    if receipt["repository"] != expectation.repository:
        raise ValueError("ci_receipt_wrong_repository")
    if receipt["workflow"] != {"name": expectation.workflow_name, "path": expectation.workflow_path}:
        raise ValueError("ci_receipt_wrong_workflow")
    if receipt["required_jobs"] != list(expectation.required_jobs):
        raise ValueError("ci_receipt_required_jobs")
    if receipt["bindings"] != {
        "lockfile_sha256": expectation.lockfile_sha256,
        "protocol_sha256": expectation.protocol_sha256,
        "runner_implementation_sha256": expectation.runner_implementation_sha256,
        "workflow_sha256": expectation.workflow_sha256,
    }:
        raise ValueError("ci_receipt_binding")
    if set(receipt["provenance"]) != {"captured_at", "method"} or receipt["provenance"]["method"] != "authenticated_github_cli":
        raise ValueError("ci_receipt_provenance")
    _require_string(receipt["provenance"]["captured_at"], "capture_timestamp")
    run = receipt["run"]
    if set(run) != {"completed_at", "conclusion", "created_at", "run_id", "status", "url"}:
        raise ValueError("ci_receipt_run_schema")
    if type(run["run_id"]) is not int or run["run_id"] <= 0:
        raise ValueError("ci_receipt_run_id")
    for key in ("completed_at", "created_at", "url"):
        _require_string(run[key], key)
    if run["status"] != "completed" or run["conclusion"] != "success":
        raise ValueError("ci_receipt_run_not_successful")
    if type(receipt["jobs"]) is not list:
        raise ValueError("ci_receipt_jobs")
    names = []
    job_ids = []
    for item in receipt["jobs"]:
        expected_job = {"completed_at", "conclusion", "job_id", "name", "started_at", "status", "url"}
        if type(item) is not dict or set(item) != expected_job:
            raise ValueError("ci_receipt_job_schema")
        if type(item["job_id"]) is not int or item["job_id"] <= 0:
            raise ValueError("ci_receipt_job_id")
        for key in ("completed_at", "name", "started_at", "url"):
            _require_string(item[key], "job_" + key)
        if item["status"] != "completed" or item["conclusion"] != "success":
            raise ValueError("ci_receipt_job_not_successful")
        names.append(item["name"])
        job_ids.append(item["job_id"])
    if names != sorted(expectation.required_jobs) or len(set(names)) != len(names):
        raise ValueError("ci_receipt_job_set")
    return VerifiedCIAuthority(actual_sha256, receipt["checkpoint_commit"], run["run_id"],
                               tuple(zip(names, job_ids)), _SEAL)


def compare_live(authority: VerifiedCIAuthority, fetch: Callable[[int], Mapping[str, object]]) -> dict:
    if authority._seal is not _SEAL:
        raise TypeError("verified_ci_authority_required")
    try:
        live = fetch(authority.run_id)
    except BaseException as error:
        return {"available": False, "matches": None, "exception": type(error).__name__}
    matches = (live.get("headSha") == authority.checkpoint_commit
               and live.get("status") == "completed" and live.get("conclusion") == "success")
    return {"available": True, "matches": matches, "exception": None}


class FailureController:
    """Create-once original failure and traceback authority."""
    def __init__(self, directory: Path):
        self.directory = Path(directory)
        self.traceback_path = self.directory / "numerical_traceback.txt"
        self.original_path = self.directory / "original_failure.json"
        self.emergency_path = self.directory / "emergency_failure.json"

    def capture(self, error: BaseException, stage: str, *, context: object = None,
                timestamp: str | None = None) -> dict:
        trace = "".join(traceback.format_exception(error)).encode()
        durable_bytes(self.traceback_path, trace)
        trace_hash = sha256_bytes(trace)
        record = {
            "context": context,
            "exception_message": str(error),
            "exception_type": type(error).__name__,
            "journal_stage": "preparation",
            "schema_version": 1,
            "stage": stage,
            "timestamp": timestamp or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "traceback_sha256": trace_hash,
        }
        durable_json(self.original_path, record)
        durable_json(self.emergency_path, {
            "original_failure_sha256": sha256_file(self.original_path),
            "schema_version": 1,
            "status": "failure_preserved",
            "traceback_sha256": trace_hash,
        })
        return record

    def publication_failure(self, error: BaseException, *, timestamp: str | None = None) -> dict:
        trace_path = self.directory / "publication_traceback.txt"
        trace = "".join(traceback.format_exception(error)).encode()
        durable_bytes(trace_path, trace)
        record = {
            "exception_message": str(error),
            "exception_type": type(error).__name__,
            "original_failure_sha256": sha256_file(self.original_path),
            "schema_version": 1,
            "timestamp": timestamp or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "traceback_sha256": sha256_bytes(trace),
        }
        durable_json(self.directory / "publication_failure.json", record)
        return record

    def validate(self) -> dict:
        original = json.loads(self.original_path.read_text())
        emergency = json.loads(self.emergency_path.read_text())
        if canonical_bytes(original) != self.original_path.read_bytes():
            raise ValueError("original_failure_noncanonical")
        if canonical_bytes(emergency) != self.emergency_path.read_bytes():
            raise ValueError("emergency_failure_noncanonical")
        if sha256_file(self.traceback_path) != original["traceback_sha256"]:
            raise ValueError("traceback_binding")
        if emergency != {
            "original_failure_sha256": sha256_file(self.original_path),
            "schema_version": 1,
            "status": "failure_preserved",
            "traceback_sha256": original["traceback_sha256"],
        }:
            raise ValueError("emergency_binding")
        return {"status": "valid", "stage": original["stage"],
                "exception_type": original["exception_type"],
                "traceback_sha256": original["traceback_sha256"]}


__all__ = [
    "AUTHORITY_ID", "CIExpectation", "FailureController", "REPOSITORY", "REQUIRED_JOBS",
    "VerifiedCIAuthority", "canonical_bytes", "capture_github_receipt", "compare_live",
    "durable_bytes", "durable_json", "receipt_from_github", "sha256_file", "validate_receipt",
]
