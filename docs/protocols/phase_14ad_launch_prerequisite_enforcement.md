# Phase 14ad — Launch and prerequisite enforcement

Prospectively frozen 2026-09-12 from clean synchronized commit
`2fa75d2b96c5e02d83e0eb5f22c554a3c1c25ad8`. Release `v0.1.0` remains at
`f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`.

## Question, authority, and boundaries

This synthetic-only orchestration phase asks whether a mandatory prerequisite
failure can be made to close a governed launch before verification, empirical
initialization, or an access marker becomes reachable. Session 14R2 remains
historically **D — BLOCKED / readiness 3**. Its numerical authority, failed
execution, code, tests, outputs, and partial private records are not repaired or
rerun here.

No development geometry, provider product, target, outcome, model, option share,
protected/reserved/withheld material, pose, xT, progression record, or Session
14R2 partial scientific output may be opened. No numerical formula, tolerance,
reference, integration path, dependency, release API, or claim may change.

The authoritative governed launch form is:

```text
uv run --locked python scripts/session_14ad_launch_prerequisite_enforcement.py <command>
```

The launcher must verify that it is running in the repository project virtual
environment, that `uv.lock` matches its frozen digest, and that the required
installed packages can be identified. System Python and ambiguous interpreter
paths are invalid launch environments. Python 3.11 and 3.13 may both exercise
the software tests, but a prerequisite and its consumer must have the identical
recorded environment fingerprint.

## Preserved Session 14R2 failure

The ignored `launch_observation.json`, failure record, access ledger, public QC,
manifest, runner, and report establish this sequence:

1. An ad-hoc prerequisite-record creation command was invoked with system
   `python`; importing the Session 14R2 runner failed with
   `ModuleNotFoundError: numpy`.
2. A separately scheduled command then invoked
   `.venv/bin/python scripts/session_14r2_occlusion_study.py verify-production`.
   The shell operations had no conditional dependency, so the first failure did
   not suppress the second launch.
3. `verify-production` claimed its persistent marker and completed its synthetic
   108-case, 366-reference, 399-permutation calculation before reading the
   prerequisite.
4. The absent `outputs/continuous_occlusion_retry_14r2/authority/tests.json` was
   detected at that late read and closed the attempt with `FileNotFoundError`,
   zero empirical states, and zero empirical edges.

This phase also records, without altering either document, that Phase 14f
prohibited test changes while its report described a test-only fallback as
permitted. That historical discrepancy cannot supply authority here.

## Mandatory prerequisite artifact

The single top-level launcher owns prerequisite creation and consumption. Its
fixed producer runs a discoverable Session 14ad enforcement test command through
the already verified `sys.executable`. A successful atomic record contains only:

- schema version, producer name, creation status, and exact test command;
- protocol and implementation SHA-256 bindings;
- `uv.lock` SHA-256 and sanitized environment fingerprint;
- tests run, passed, skipped, exit status, and output SHA-256;
- the observed failure-enforcement result.

Creation requires a verified project environment and successful test exit.
Validation requires the exact schema, finite/nonnegative counts, passed equals
run minus skipped, successful status, matching protocol/implementation/lock and
environment bindings, matching command, and `failure_enforcement_passed=true`.
The record is ignored, immutable after creation, and must be validated before a
downstream callback, numerical work, access marker, or empirical handle exists.

## State machine and capability guard

The permitted ordered states are:

```text
INITIAL
  -> ENVIRONMENT_VERIFIED
  -> PREREQUISITE_CREATED
  -> PREREQUISITE_VALIDATED
  -> SYNTHETIC_READINESS_VERIFIED
  -> EMPIRICAL_ACCESS_AUTHORIZED
```

Every exception or failed condition transitions directly to terminal
`FAILED_CLOSED`. No transition leaves that state. Repeated or out-of-order
transitions fail. A persistent exclusive launch marker prevents replay.

Successful prerequisite validation constructs a private one-use launch context
bound to the environment and prerequisite digest. The guarded downstream route
requires that context, exact bindings, the expected state, and an unclaimed
authorization marker. Direct CLI invocation exposes no empirical command. Tests
may inject callbacks, but production callers cannot request later states
individually. The Session 14ad success callback is a sentinel only: it increments
an authorization spy and opens no data.

On failure, public evidence must record the failed stage, sanitized exception
category, environment and prerequisite status, downstream and empirical-access
spy counts, marker status, and zero states/edges. Private traceback and execution
details remain ignored. Readiness remains false and automatic rerun is forbidden.

## Frozen audit and failure injections

Before the one governed audit, discoverable tests must cover the correct project
environment; system Python; missing dependency or environment marker; lock and
environment mismatch; producer exception; missing, unreadable, deleted,
malformed, stale, wrong-schema, wrong-hash, and wrong-environment records;
out-of-order/direct entry; context, digest, and marker mismatch; marker collision;
warning/failure propagation; deterministic closure; and automatic-rerun rejection.
Every prerequisite injection must leave downstream and empirical-access spies at
zero. Tests must assert the exact successful transition order and a successful
sentinel authorization without data access. Source firewalls must show no
empirical, acquisition, model, scoring, target, or outcome route.

After the protocol and tested implementation commits, execute exactly one
governed synthetic audit. It runs all frozen injections and one successful
control. An unexpected post-exposure defect is preserved and closes the phase;
there is no repair or second audit under this authority.

## Outputs, decision, and closure

Publish exactly these files under `outputs/session14_launch_enforcement/`:

- `launch_contract.json`
- `state_machine.json`
- `environment_oracles.csv`
- `prerequisite_failure_injections.csv`
- `downstream_call_guards.json`
- `success_control.json`
- `qc.json`
- `manifest.json`

Use fixed schemas, finite JSON, LF CSV, stable synthetic labels, atomic writes,
and a manifest binding protocol, implementation, environment, historical
Session 14R2 hashes, and output hashes. Private tokens, raw interpreter paths,
test output, traces, and execution records remain ignored. Publication checking
validates existing bytes and never regenerates or rebinds them.

Classification is **A** only if the environment is unambiguous, prerequisite
creation and validation precede all downstream reachability, every failure
injection closes with zero downstream/access calls, direct entry is guarded, and
the success sentinel alone reaches authorization. **B** is environment ambiguity;
**C** a remaining bypass; **D** defective propagation/publication; **E** multiple
defects; **F** insufficient evidence; **G** execution/integrity failure.
Readiness 1 requires A; otherwise assign readiness 2–4 from the observed blocker.

Preserve three commits: protocol; tested implementation; closed evidence/report
and append-only research-log entry. Run focused and relevant Session 14 tests,
the full suite, compilation, schemas/hashes, privacy/publication guards, links,
history preservation, staged inspection, `git diff --check`, and ordinary Python
3.11, Python 3.13, and distribution CI. Push only reviewed commits and verify
clean synchronized heads and the unchanged tag.

On A/readiness 1 recommend exactly: **separately govern a fresh Session 14R
empirical representation retry using the repaired single fail-closed launch
path.** Do not execute it.
