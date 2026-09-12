# Session 14ad — Launch and prerequisite enforcement

## Result

**A — LAUNCH / PREREQUISITE CONTRACT REPAIRED; readiness 1.** The governed
synthetic audit established one environment-bound, fail-closed launch path. All
fifteen environment and prerequisite failure oracles stopped before the
downstream synthetic callback, access authorization callback, or access marker.
The valid control followed the exact six-state success path and reached only an
authorization sentinel. It opened zero data handles, zero empirical states, and
zero empirical edges.

This is an orchestration result, not a scientific result. Session 14R2 remains
historically **D — BLOCKED / readiness 3**. No empirical retry occurred.

## Thirty-one-item handoff

1. **Starting HEAD:** `2fa75d2b96c5e02d83e0eb5f22c554a3c1c25ad8`.
   Local, tracking, and live GitHub `main` agreed before mutation.
2. **Ending HEAD:** recorded in the delivery handoff after the closure commit and
   remote verification.
3. **Protocol:** [Phase 14ad](protocols/phase_14ad_launch_prerequisite_enforcement.md),
   commit `677e3749a0977dcc274391fa4a0798f6d8f5b9cb`, SHA-256
   `11e9aefb834fcb5dc0f22ec4b23dfbe83d29b97c8f78bf36ef270d25650024ba`.
4. **Exact Session 14R2 sequence:** an ad-hoc prerequisite producer used system
   Python and failed; a separately scheduled locked-environment
   `verify-production` command still started; it claimed its marker and completed
   108/366/399 synthetic work; only then did it read the missing prerequisite and
   close with `FileNotFoundError`.
5. **System-Python cause:** the interpreter lacked the locked NumPy dependency,
   producing `ModuleNotFoundError: numpy` before `authority/tests.json` existed.
6. **Authoritative entrypoint:** `uv run --locked python` in the repository
   project virtual environment. The audit additionally binds `uv.lock`, Python,
   implementation, and the installed NumPy/SciPy versions.
7. **Prerequisite contract:** the atomic record binds producer, command,
   protocol, implementation, lock, environment, test totals/status/output hash,
   and `failure_enforcement_passed=true`. Its exact fourteen fields are listed in
   [launch_contract.json](../outputs/session14_launch_enforcement/launch_contract.json).
8. **State machine:** `INITIAL → ENVIRONMENT_VERIFIED → PREREQUISITE_CREATED →
   PREREQUISITE_VALIDATED → SYNTHETIC_READINESS_VERIFIED →
   EMPIRICAL_ACCESS_AUTHORIZED`; every failure terminates at `FAILED_CLOSED`.
9. **Repair:** a single `GovernedLauncher.run()` call now owns environment
   verification, prerequisite production and validation, readiness, and the
   authorization sentinel. No shell-level independent continuation exists.
10. **Single top-level launcher:** adopted. Its public commands are only
    `preflight`, `audit`, and `publication-check`; there is no empirical command.
11. **Direct-entry guard:** passed. Access requires an opaque one-use context,
    matching environment and prerequisite digest, expected state, and exclusive
    access marker.
12. **Wrong environment:** system Python, missing environment marker, missing
    SciPy, changed lock hash, and stale environment fingerprint all closed at the
    environment gate with zero producer/downstream/access calls.
13. **Missing prerequisite:** closed after one producer call with zero downstream
    and access calls and no access marker.
14. **Malformed/stale prerequisite:** malformed JSON, unexpected schema, wrong
    implementation hash, wrong environment, stale protocol, failed status,
    unreadable path, and deleted record all closed before downstream reachability.
15. **Producer failure:** the injected producer exception closed immediately;
    downstream and access spy counts remained zero.
16. **Downstream spies:** zero for all fifteen failed cases.
17. **Empirical-access spies:** zero for all fifteen failed cases; no failed case
    created an access marker.
18. **Failure publication:** deterministic terminal state, sanitized category,
    call counts, access-marker status, and zero states/edges were retained. The
    closed QC asserts all failure cases were fail-closed.
19. **Success control:** one downstream readiness call and one authorization
    sentinel call followed the exact state order. It opened no data handle.
20. **Audit access:** zero empirical states and zero empirical edges.
21. **Classification:** **A — LAUNCH / PREREQUISITE CONTRACT REPAIRED**.
22. **Readiness:** **1 — ready for a separately governed fresh retry**.
23. **Numerical/scientific contracts:** unchanged. The new module contains launch
    governance only and calls no field, integration, model, or scoring code.
24. **Empirical access:** none. Development geometry and provider records were
    neither opened nor hashed.
25. **Session 14R2 partial scientific outputs:** not inspected. Only its bounded
    launch/failure records and committed public authority were used.
26. **Tests:** focused Session 14ad: 7 run, 7 passed, 0 skipped. Relevant
    orchestration subset: 61 run, 61 passed, 0 skipped. Full active suite: 529
    run, 526 passed, 3 retained skips. Subset totals overlap the full suite.
27. **Python 3.11 CI:** final status recorded in delivery after the closure push.
28. **Python 3.13 CI:** final status recorded in delivery after the closure push.
29. **Distribution CI:** final status recorded in delivery after the closure push.
30. **Commits/push:** protocol `677e374`, tested implementation `9b3aeb7`, and
    the closure commit are kept separate; final push and synchronization are
    recorded in delivery.
31. **Exactly one recommendation:** **separately govern a fresh Session 14R
    empirical representation retry using the repaired single fail-closed launch
    path.** This report does not authorize or execute it.

## Evidence and qualifications

The governed audit used five environment oracles and ten prerequisite failure
injections. The missing and unreadable cases both resolve to absence at the
mandatory `is_file()` gate; neither permits validation. The private successful
prerequisite was produced by the verified interpreter running the fixed,
discoverable Session 14ad prerequisite test class. Its content was validated
again immediately before the access marker was claimed.

The one-use context is an orchestration capability, not a security boundary
against malicious modification of repository code. Committed hashes, a clean
future protocol, ordinary CI, and repository governance remain necessary before
any empirical retry. The repair prevents the demonstrated accidental launch
sequence and direct command bypass under the governed software path.

The [manifest](../outputs/session14_launch_enforcement/manifest.json) SHA-256 is
`a6e6f191c1c34275f1eee4f38e55a5afeb1cfc54a057acb5b85a48f84fb18ea1`.
It binds the protocol, implementation, sanitized environment, preserved Session
14R2 hashes, and all seven evidence files. Publication checking validated those
existing bytes without regenerating or rebinding them.

Phase 14f's protocol prohibited test changes while its later report described a
test-only fallback as permitted. Both records remain unchanged; the discrepancy
is recorded as historical context and supplies no authority for Session 14ad.

The claim ledger is unchanged. Accessibility remains **PROXY ONLY** and
suppression remains **NOT SUPPORTABLE**. No field candidate, cover-shadow claim,
causal effect, attribution, value, or behavioral conclusion is established.
