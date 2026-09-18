# Session 14R9M — Pre-access authority and traceback repair

2026-09-18. Synthetic-only prospective repair; zero empirical access.

## Decision

**A — BOTH PRE-ACCESS DEFECTS REPAIRED. Readiness 1 — FRESH EMPIRICAL RETRY MAY BE GOVERNED.**

R9L remains historically **D / readiness 4**. R9M did not replace its QC,
manifest or failure evidence and did not reserve an empirical attempt. R9J
remains publication authority PA; R9K remains numerical authority A/readiness 1.

## Findings and repair

R9L's required `verify_ci()` called `gh run list` and `gh run view` inside the
governed launch callback after its exact checkpoint CI had already passed. The
second lookup was therefore a network-dependent repetition of established
authority. Its connection failure stopped before access, as required, but made
network availability part of scientific access authorization.

R9M separates authenticated acquisition from run-time validation. After the
exact implementation checkpoint passes CI, a create-once local receipt binds the
commit, workflow and workflow hash, run identity, all three job identities and
terminal conclusions, timestamps, protocol, runner, lockfile and authenticated
CLI provenance. The governed gate validates canonical receipt bytes and their
frozen SHA-256 against exact local `HEAD` and source bindings without contacting
GitHub. A live comparison is diagnostic only. The accepted receipt for corrected
checkpoint `3605334eeae6bf427690339b177332cb8a997fa4` binds Actions run
`35402000325`; its SHA-256 is
`313ac49557978900dc0cb1453657317d532df9a11245b1ec091b537c4c12141b`.

R9L had already persisted `numerical_traceback.txt`, and its journal correctly
bound that file's hash, but normal publication invoked the R9J validator with
`traceback_path=None`. R9M's standard-library failure controller durably writes
the traceback first, binds it into immutable original and emergency records,
then passes that same file through lifecycle failure and linear publication.
The precise outer stage is retained while the unchanged R9J pre-access journal
stage remains `preparation`. A publisher failure receives a separate traceback
and record without changing the original failure chain.

The R9L-style prospective control retained `preaccess_authority` externally,
retained `preparation` in the compatibility journal, opened zero states and
edges, and returned a valid R9J publication receipt. All 11 traceback controls
preserved stage, exception, traceback hash and independent emergency evidence.

## CI capture qualification

The first authenticated receipt acquisition, after checkpoint `b1593bd`, found
a pre-audit source-shape defect: `gh run view --json jobs` includes a `steps`
array, while the strict acquisition parser expected only summary fields. It
raised before any receipt or audit marker was written. The governed audit was
therefore unspent. The parser was corrected narrowly to require and ignore the
typed steps array, committed as `3605334`, and subjected to a fresh exact-commit
CI run before receipt acquisition and the one audit. This preserved the failed
attempt and required one additional implementation correction commit rather
than rewriting pushed history.

## Controls and validation

The offline valid receipt passed. Missing, wrong-commit, wrong-workflow,
pending, failed, cancelled, missing-job, altered-binding, content-tampered and
noncanonical receipts all blocked. DNS, connection and timeout failures cannot
affect a valid local authority. No caller-provided success boolean is accepted.

Focused R9M tests ran 32 and passed 32. The combined R9M/R9L/R9K/R9J and launch,
lifecycle and exposure set ran 109 and passed 109 from a tracked-only checkout.
The earlier equivalent local relevant set ran 108 and passed 108 before the
payload-shape test was added. The full active suite ran **1,081** tests:
**1,078 passed and 3 retained skips**. Compilation, schemas, hashes, finite JSON,
privacy, documentation links, historical hashes and diff checks passed.
Checkpoint CI run `35402000325` passed distribution, Python 3.11 and Python
3.13. The audit publication check validated all eight public artifacts.

## Handoff

1. Starting HEAD: `9e5f122b0954dd19a373f627beea4ffb525e51cb`.
2. Protocol commit: `25cbb87`.
3. Tested implementation commit: `b1593bd`.
4. Preserved capture-compatibility correction: `3605334`.
5. R9L defect: mandatory live GitHub lookup inside the pre-access callback.
6. Traceback defect: `validate_linear_public` received no traceback path.
7. CI authority: canonical create-once exact-commit receipt, validated offline.
8. Network-offline valid-receipt result: pass.
9. Missing, wrong and altered receipt results: blocked.
10. Traceback matrix: 11/11 pass.
11. R9L-style failure publication: valid.
12. Empirical exposure: 0 states / 0 edges; no empirical marker reserved.
13. R9J/R9K: unchanged at PA and A/readiness 1.
14. Classification/readiness: A/1.
15. Claim ledger, API, dependencies, numerics and release: unchanged.

The sole recommendation is to **separately govern one fresh empirical R9 retry
using the frozen local checkpoint-CI authority, hardened traceback binding, R9K
comparator, and R9J linear validator.**
