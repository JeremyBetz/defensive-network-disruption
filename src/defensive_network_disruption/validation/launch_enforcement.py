"""Internal fail-closed launch orchestration for governed research sessions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import math
from pathlib import Path
import secrets
from typing import Callable, Mapping


class LaunchError(RuntimeError):
    """Raised when a governed launch obligation is not satisfied."""


class LaunchState(str, Enum):
    INITIAL = "INITIAL"
    ENVIRONMENT_VERIFIED = "ENVIRONMENT_VERIFIED"
    PREREQUISITE_CREATED = "PREREQUISITE_CREATED"
    PREREQUISITE_VALIDATED = "PREREQUISITE_VALIDATED"
    SYNTHETIC_READINESS_VERIFIED = "SYNTHETIC_READINESS_VERIFIED"
    EMPIRICAL_ACCESS_AUTHORIZED = "EMPIRICAL_ACCESS_AUTHORIZED"
    FAILED_CLOSED = "FAILED_CLOSED"


ORDER = (
    LaunchState.INITIAL,
    LaunchState.ENVIRONMENT_VERIFIED,
    LaunchState.PREREQUISITE_CREATED,
    LaunchState.PREREQUISITE_VALIDATED,
    LaunchState.SYNTHETIC_READINESS_VERIFIED,
    LaunchState.EMPIRICAL_ACCESS_AUTHORIZED,
)


@dataclass(frozen=True)
class EnvironmentObservation:
    python: str
    implementation: str
    in_project_environment: bool
    environment_marker: str | None
    lock_sha256: str
    packages: tuple[tuple[str, str], ...]

    def public(self) -> dict[str, object]:
        return {
            "python": self.python,
            "implementation": self.implementation,
            "environment_kind": "project_venv" if self.in_project_environment else "other",
            "environment_marker_present": self.environment_marker is not None,
            "lock_sha256": self.lock_sha256,
            "packages": dict(self.packages),
        }

    def fingerprint(self) -> str:
        return sha256_bytes(canonical_json(self.public()).encode())


@dataclass(frozen=True)
class PrerequisiteExpectation:
    protocol_sha256: str
    implementation_sha256: str
    lock_sha256: str
    environment_sha256: str
    test_command: tuple[str, ...]


_CAPABILITY = object()


class LaunchContext:
    """Opaque, one-use capability returned only after prerequisite validation."""

    __slots__ = ("_authority", "_prerequisite", "_token")

    def __init__(self, authority: str, prerequisite: str, token: str, guard: object):
        if guard is not _CAPABILITY:
            raise LaunchError("launch_context_must_be_issued_by_launcher")
        self._authority = authority
        self._prerequisite = prerequisite
        self._token = token


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    if path.exists() or temporary.exists():
        raise FileExistsError(path)
    with temporary.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
    temporary.replace(path)


def claim_marker(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write("claimed\n")


def verify_environment(
    observed: EnvironmentObservation,
    *,
    expected_lock: str,
    required_packages: tuple[str, ...],
) -> str:
    if not observed.in_project_environment:
        raise LaunchError("environment_not_project_venv")
    if observed.environment_marker != "uv-locked-project-environment":
        raise LaunchError("environment_marker_missing")
    if observed.lock_sha256 != expected_lock:
        raise LaunchError("lock_hash_mismatch")
    installed = dict(observed.packages)
    missing = [name for name in required_packages if not installed.get(name)]
    if missing:
        raise LaunchError("missing_required_package:" + ",".join(missing))
    return observed.fingerprint()


PREREQUISITE_FIELDS = {
    "schema_version",
    "producer",
    "status",
    "test_command",
    "protocol_sha256",
    "implementation_sha256",
    "lock_sha256",
    "environment_sha256",
    "tests_run",
    "tests_passed",
    "tests_skipped",
    "exit_status",
    "test_output_sha256",
    "failure_enforcement_passed",
}


def validate_prerequisite(
    path: Path,
    expected: PrerequisiteExpectation,
) -> tuple[Mapping[str, object], str]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise LaunchError("prerequisite_unreadable") from exc
    try:
        pairs = json.loads(raw, object_pairs_hook=lambda pairs: pairs)
        if not isinstance(pairs, list) or any(not isinstance(x, tuple) for x in pairs):
            raise ValueError
        keys = [key for key, _ in pairs]
        if len(keys) != len(set(keys)):
            raise LaunchError("prerequisite_duplicate_key")
        record = dict(pairs)
    except LaunchError:
        raise
    except Exception as exc:
        raise LaunchError("prerequisite_malformed") from exc
    if set(record) != PREREQUISITE_FIELDS:
        raise LaunchError("prerequisite_schema")
    exact = {
        "schema_version": 1,
        "producer": "session14ad_enforcement_tests",
        "status": "passed",
        "test_command": list(expected.test_command),
        "protocol_sha256": expected.protocol_sha256,
        "implementation_sha256": expected.implementation_sha256,
        "lock_sha256": expected.lock_sha256,
        "environment_sha256": expected.environment_sha256,
        "exit_status": 0,
        "failure_enforcement_passed": True,
    }
    for key, value in exact.items():
        if record[key] != value:
            raise LaunchError(f"prerequisite_binding:{key}")
    counts = [record[key] for key in ("tests_run", "tests_passed", "tests_skipped")]
    if any(type(value) is not int or value < 0 for value in counts):
        raise LaunchError("prerequisite_test_counts")
    if record["tests_run"] != record["tests_passed"] + record["tests_skipped"]:
        raise LaunchError("prerequisite_test_counts")
    output_hash = record["test_output_sha256"]
    if not isinstance(output_hash, str) or len(output_hash) != 64:
        raise LaunchError("prerequisite_output_hash")
    return record, sha256_bytes(raw)


class GovernedLauncher:
    """Enforce ordered prerequisites before a one-use authorization sentinel."""

    def __init__(self, launch_marker: Path, access_marker: Path):
        self.launch_marker = launch_marker
        self.access_marker = access_marker
        self.state = LaunchState.INITIAL
        self.transitions = [self.state.value]
        self._issued_token: str | None = None
        self._used = False

    def _advance(self, target: LaunchState) -> None:
        current = ORDER.index(self.state)
        if current + 1 >= len(ORDER) or ORDER[current + 1] is not target:
            raise LaunchError(f"invalid_transition:{self.state.value}:{target.value}")
        self.state = target
        self.transitions.append(target.value)

    def _close(self) -> None:
        if self.state is not LaunchState.FAILED_CLOSED:
            self.state = LaunchState.FAILED_CLOSED
            self.transitions.append(self.state.value)

    def run(
        self,
        *,
        environment: EnvironmentObservation,
        expected: PrerequisiteExpectation,
        required_packages: tuple[str, ...],
        prerequisite_path: Path,
        produce_prerequisite: Callable[[], None],
        verify_synthetic: Callable[[LaunchContext], bool],
        authorize_empirical: Callable[[LaunchContext], None],
    ) -> LaunchContext:
        try:
            claim_marker(self.launch_marker)
            authority = verify_environment(
                environment,
                expected_lock=expected.lock_sha256,
                required_packages=required_packages,
            )
            if authority != expected.environment_sha256:
                raise LaunchError("environment_fingerprint_mismatch")
            self._advance(LaunchState.ENVIRONMENT_VERIFIED)
            produce_prerequisite()
            if not prerequisite_path.is_file():
                raise LaunchError("prerequisite_missing")
            self._advance(LaunchState.PREREQUISITE_CREATED)
            _, prerequisite_hash = validate_prerequisite(prerequisite_path, expected)
            self._advance(LaunchState.PREREQUISITE_VALIDATED)
            token = secrets.token_hex(32)
            self._issued_token = token
            context = LaunchContext(authority, prerequisite_hash, token, _CAPABILITY)
            if verify_synthetic(context) is not True:
                raise LaunchError("synthetic_readiness_false")
            self._advance(LaunchState.SYNTHETIC_READINESS_VERIFIED)
            self.authorize(context, environment, expected, prerequisite_path, authorize_empirical)
            return context
        except Exception:
            self._close()
            raise

    def authorize(
        self,
        context: LaunchContext,
        environment: EnvironmentObservation,
        expected: PrerequisiteExpectation,
        prerequisite_path: Path,
        callback: Callable[[LaunchContext], None],
    ) -> None:
        if self.state is not LaunchState.SYNTHETIC_READINESS_VERIFIED:
            raise LaunchError("access_before_readiness")
        if not isinstance(context, LaunchContext) or context._token != self._issued_token:
            raise LaunchError("invalid_launch_context")
        if self._used:
            raise LaunchError("launch_context_already_used")
        if context._authority != environment.fingerprint():
            raise LaunchError("access_environment_mismatch")
        _, prerequisite_hash = validate_prerequisite(prerequisite_path, expected)
        if context._prerequisite != prerequisite_hash:
            raise LaunchError("access_prerequisite_mismatch")
        claim_marker(self.access_marker)
        self._used = True
        callback(context)
        self._advance(LaunchState.EMPIRICAL_ACCESS_AUTHORIZED)


def finite_tree(value: object) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise LaunchError("nonfinite_output")
    if isinstance(value, dict):
        for item in value.values():
            finite_tree(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            finite_tree(item)
