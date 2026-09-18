# Phase 14R9M — Pre-access CI authority and failure traceback repair

**Frozen 2026-09-18 before implementation.** Starting authority is clean and
synchronized commit `9e5f122b0954dd19a373f627beea4ffb525e51cb`;
`v0.1.0` remains `f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`.

## Authority and scope

Session 14R9L remains **D — invalid/blocked, readiness 4**. Its checkpoint
`2ead963fed5ba135407863444f2007aafa86b164` passed the required Python 3.11,
Python 3.13 and distribution jobs in GitHub Actions run `35366489405`. The one
governed attempt then stopped before access because `verify_ci()` performed a
second live `api.github.com` lookup inside the launch callback and the lookup
raised `CalledProcessError`. Zero states, edges and candidate calls were opened.
Normal failure publication subsequently called the R9J validator without the
persisted `numerical_traceback.txt`; the validator correctly rejected the
package as `traceback_missing`. Independent emergency evidence retained both
exceptions.

R9M repairs only those two prospective execution defects. It does not alter or
retroactively validate R9L. R9J remains publication authority PA and R9K remains
numerical authority A/readiness 1. No empirical geometry, population row,
scientific output, target, model, share, outcome, provider product or protected
material may be opened. No empirical-attempt marker may be reserved. Numerical
code, fields, tolerances, certificates, dependencies, public API, claims,
release metadata and every historical artifact remain unchanged.

## Frozen checkpoint-CI authority

The mandatory run-time gate uses a locally frozen, create-once checkpoint-CI
receipt rather than a live network query. Receipt acquisition is a distinct
authenticated step after the exact implementation commit has passed CI and
before governed execution. Acquisition queries the exact commit and workflow;
it accepts no caller-supplied success boolean.

Canonical receipt schema binds:

- schema version, authority ID and repository identity;
- exact checkpoint commit and current workflow-file SHA-256;
- workflow name, run ID, URL, status, conclusion, creation and completion time;
- exactly the required jobs `test (3.11)`, `test (3.13)` and `distribution`,
  including job IDs, status, conclusion, start and completion times;
- protocol SHA-256, runner implementation SHA-256 and lockfile SHA-256;
- authenticated GitHub CLI provenance and capture timestamp.

The private canonical bytes are synchronized and immutable. Public evidence
contains only their SHA-256 and sanitized run/job metadata. Validation requires
canonical encoding, the exact schema and field set, exact repository/workflow,
exact `HEAD`, exact implementation/protocol/lock/workflow hashes, a completed
successful run, and each required job completed successfully. Missing,
noncanonical, stale, wrong-commit, wrong-workflow, altered, pending, failed,
cancelled, duplicated or incomplete authority blocks. The frozen receipt is
content-bound evidence under this protocol, not an arbitrary declaration.

No governed run-time access decision may call GitHub or depend on network
availability. A separately invoked live comparison may diagnose drift but has
no authority to grant access and is not called by the audit. Network unavailability
with a valid receipt must pass; it cannot weaken the requirement that the
checkpoint CI actually succeeded.

## Frozen failure and traceback contract

A standard-library controller exists before optional package imports and
governed startup. Each exception is formatted once and durably persists a
private traceback before journal mutation or normal publication. The immutable
original-failure record binds schema, exact outer stage, exception type and
message, timestamp, traceback SHA-256 and available context. An independent
emergency record binds the original-failure and traceback hashes.

When a lifecycle journal exists, the compatible R9J failure event uses that
same traceback file. R9J's frozen pre-access journal stage remains
`preparation`; the outer record preserves the precise stage and explicitly
records the compatibility mapping. Normal validation receives the exact
traceback path. It never regenerates traceback text.

If normal publication fails, the original exception and traceback remain
valid. A separate immutable publication-failure record and traceback bind the
publication exception to the original-failure hash. Startup, dependency import,
inherited-authority, CI-authority, marker, source/population, publication-init
and publication-validation exceptions all obey this contract. A path without
an initialized empirical journal closes through the independent pre-access
failure schema; it does not manufacture lifecycle progress.

## Synthetic audit and controls

After the tested implementation commit passes required CI, acquire its receipt
once and execute one governed synthetic audit with network calls forced to fail.
The audit creates no empirical marker or handle. It covers:

- valid receipt offline; missing, malformed, altered and wrong-commit receipts;
- wrong workflow, pending, failed, cancelled, duplicate or missing jobs;
- local HEAD, implementation, protocol, lock and workflow mismatches;
- DNS, connection and timeout failures isolated from the mandatory gate;
- import, inherited-source, marker, synthetic-population and publication-init
  failures;
- normal failure-publication success, publisher failure, cross-file mismatch,
  immutable emergency evidence and rerun rejection; and
- an R9L-style network exception with exact traceback binding, valid prospective
  failure closure and zero empirical access.

Every failure control requires the original exception, precise stage and exact
traceback hash to survive. When normal publication is healthy, the R9J linear
validator must accept the persisted failure package. When publication fails,
the independent emergency chain must remain valid. No control reads the real
population or historical private geometry.

## Evidence, decisions and stop rules

Public evidence is written under
`outputs/continuous_occlusion_preaccess_authority_repair/` as
`repair_contract.json`, `ci_authority_regression.json`,
`network_failure_oracles.csv`, `traceback_failure_matrix.csv`,
`failure_publication_regression.json`, `preservation.json`, `qc.json` and
`manifest.json`. Private receipts, tracebacks and detailed failure records remain
ignored and hash-bound. The report is
`docs/session_14r9m_preaccess_authority_traceback_repair.md`; one bounded entry
is appended to the research log. Publication checks validate existing bytes and
never recreate missing evidence.

Classify **A** only when both defects are repaired, offline receipt validation
passes, every negative control blocks, every exception retains its traceback,
the R9L-style failure closes normally, R9J/R9K and R9L bytes are unchanged,
empirical exposure is 0/0 and delivery checks pass. **B** means only CI authority
is repaired; **C** only traceback binding; **D** incomplete or invalid repair.
Readiness is 1 only with A, 2 with one remaining defect, 3 with multiple defects
and 4 for invalid execution.

Unexpected governed-audit failure is preserved without repair or rerun. Preserve
three commits: protocol; tested implementation; closed evidence/report/log.
Run focused R9M and R9L tests, R9J/R9K and relevant orchestration/lifecycle
tests, the full active suite, tracked-only validation, compilation, schema/hash,
finite-JSON, privacy, links, history, staged and diff checks. Require green
Python 3.11, Python 3.13 and distribution CI, synchronized clean heads and the
unchanged tag.

On **A/readiness 1**, recommend exactly: **separately govern one fresh empirical
R9 retry using the frozen local checkpoint-CI authority, hardened traceback
binding, R9K comparator, and R9J linear validator.** Do not execute that retry.
