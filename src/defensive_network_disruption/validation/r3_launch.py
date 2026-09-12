"""Internal R3 boundary around the unchanged governed launcher; no data routes."""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import re
import warnings

from .launch_enforcement import (
    GovernedLauncher, LaunchError, LaunchState, PrerequisiteExpectation,
    atomic_write, canonical_json, sha256_file, validate_prerequisite,
)

TEST_COMMAND = ('-m', 'unittest', 'discover', '-s', 'tests', '-p',
                'test_session14r3_enforcement.py')


def strict_prerequisite(path, expected):
    record, digest = validate_prerequisite(path, expected)
    if record['tests_passed'] <= 0 or record['tests_run'] <= 0:
        raise LaunchError('empty_test_collection')
    for key in ('schema_version', 'exit_status'):
        if type(record[key]) is not int:
            raise LaunchError('prerequisite_integer_type')
    if record['failure_enforcement_passed'] is not True:
        raise LaunchError('enforcement_not_observed')
    if not re.fullmatch('[0-9a-f]{64}', record['test_output_sha256']):
        raise LaunchError('test_output_digest')
    return record, digest


def test_record(expected, output, returncode):
    """Parse an actual unittest discovery result; imports alone cannot pass."""
    matches = re.findall(r'^Ran (\d+) tests? in ', output, re.MULTILINE)
    if returncode != 0 or len(matches) != 1 or not re.search(r'^OK(?: \(skipped=\d+\))?\s*$', output, re.MULTILINE):
        raise LaunchError('enforcement_tests_failed')
    count = int(matches[0]); skip = re.search(r'^OK \(skipped=(\d+)\)', output, re.MULTILINE)
    skipped = int(skip[1]) if skip else 0
    if count - skipped <= 0:
        raise LaunchError('empty_test_collection')
    import hashlib
    return dict(schema_version=1, producer='session14ad_enforcement_tests',
        status='passed', test_command=list(expected.test_command),
        protocol_sha256=expected.protocol_sha256,
        implementation_sha256=expected.implementation_sha256,
        lock_sha256=expected.lock_sha256, environment_sha256=expected.environment_sha256,
        tests_run=count, tests_passed=count-skipped, tests_skipped=skipped,
        exit_status=returncode, test_output_sha256=hashlib.sha256(output.encode()).hexdigest(),
        failure_enforcement_passed=True)


class R3Launch:
    """One attempt, guarded callbacks and durable failure counts, including startup."""

    def __init__(self, directory: Path):
        self.directory = directory
        self.core = GovernedLauncher(directory/'launch.marker', directory/'access.marker')
        self.stage = 'startup'
        self.downstream_calls = 0
        self.access_calls = 0
        self.record = None

    def execute(self, *, discover, expected, produce, verify, access):
        try:
            if (self.directory/'failure.json').exists():
                raise LaunchError('failed_attempt_cannot_resume')
            self.stage = 'environment_discovery'
            with warnings.catch_warnings():
                warnings.simplefilter('error')
                env = discover()
                exp = expected(env)
                path = self.directory/'prerequisite.json'

                def producer():
                    self.stage = 'prerequisite_production'
                    produce(path, exp)
                    self.stage = 'prerequisite_validation'
                    strict_prerequisite(path, exp)

                def downstream(context):
                    self.stage = 'synthetic_authority_validation'
                    strict_prerequisite(path, exp)
                    if (context._authority != env.fingerprint() or
                        context._prerequisite != sha256_file(path)):
                        raise LaunchError('downstream_context_binding')
                    self.downstream_calls += 1
                    return verify(context)

                def guarded(context):
                    self.stage = 'guarded_access'
                    strict_prerequisite(path, exp)
                    self.access_calls += 1
                    access(context)

                self.core.run(environment=env, expected=exp, required_packages=('numpy','scipy'),
                    prerequisite_path=path, produce_prerequisite=producer,
                    verify_synthetic=downstream, authorize_empirical=guarded)
                self.stage = 'complete'
                self.record = self.observation(None)
                atomic_write(self.directory/'success.json', canonical_json(self.record)+'\n')
                return self.record
        except Exception as exc:
            self.record = self.observation(type(exc).__name__)
            self.record['status'] = 'failed_closed'
            self.directory.mkdir(parents=True, exist_ok=True)
            if not (self.directory/'failure.json').exists():
                atomic_write(self.directory/'failure.json', canonical_json(self.record)+'\n')
            raise

    def observation(self, exception):
        return dict(schema_version=1, status='passed' if exception is None else 'failed_closed',
            stage=self.stage, exception=exception, downstream_calls=self.downstream_calls,
            access_calls=self.access_calls, access_marker=(self.directory/'access.marker').exists(),
            core_state=self.core.state.value, transitions=list(self.core.transitions))
