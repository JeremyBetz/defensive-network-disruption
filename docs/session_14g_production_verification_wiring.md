# Session 14g — Production verification wiring and failure enforcement

## Decision and boundary

**INVALID — EXECUTION OR INTEGRITY FAILURE.** The single governed synthetic
audit caught a `TypeError` during its engineering-check stage and stopped. No
frozen field case or component-reference comparison completed in that audit.
The package is closed as a failure, not as numerical acceptance. Session 14R
remains paused. There was no post-exposure implementation repair or audit rerun.

The failure record retains the exception class but not the active fixture,
traceback or partially completed engineering rows. Consequently, the exact
failing operation is **unavailable from retained execution evidence**. Static
inspection alone cannot establish its historical location. Do not reinterpret
this exception as evidence against the frozen field formulas.

## Authority and chronology

- Starting local, tracking and live GitHub `main`:
  `8ef0a27ebe9f0ac7ca6b4a754cfa7168c8b34ba5`, clean and verified before mutation.
- Release `v0.1.0` target:
  `f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`, unchanged.
- [Prospective protocol](protocols/phase_14g_production_verification_wiring.md):
  commit `885494c7ddb8bab0e39283a19ab12dca79eed42d`.
- Tested implementation and audit execution commit:
  `8fd6de35acad4f5dcd47fddd0c94d01cf2c3820d`.
- Closure is the separate commit containing this report, seven generated public
  files and the appended research-log entry. Ending commit, push synchronization
  and final CI are verified in the delivery handoff, avoiding a self-referential
  commit identifier in this report.

The [contract](../outputs/continuous_occlusion_production_verification/contract.json)
binds protocol and implementation hashes, historical inputs, the environment,
and the unchanged joint-integration rule. The locked environment is Python
3.13.15, NumPy 2.5.3 and SciPy 1.18.1. No dependency was installed or changed.

## What was implemented and tested

One internal entrypoint now runs the existing field evaluation and repaired
switch detection, validates certified enclosure endpoints, and feeds those
partitions into an independent maximum-verification calculation. Every
positive-width piece is included, including adjacent-float enclosures.

The accepted-value path retains the existing uniform joint Simpson calculation,
component ordering and interval ladder through 16,384. Certified partitions do
not alter that calculation. The independent maximum branch applies inherited
piecewise, repeated-adaptive, unsplit-adaptive, direct-Simpson and historical
split-Simpson checks before joint estimates can be accepted. This is implemented
and covered by bounded unit oracles; the full 108-case governed acceptance is
**not established**.

Actual synthetic pipeline failures prevent accepted output: continuity/oracle
failures, detector/root failure, uncertified partitions, missing references,
nonconvergence, warnings, permutation mismatch, nondeterminism and integrity
failure. Exclusive markers reject concurrent invocation and automatic reruns.
The new tests are `unittest`-discoverable and require no pytest dependency.
Historical tests are unchanged.

The focused suite includes 12 injection records: one valid control and eleven
negative cases, including marker collision. Separate tests exercise an actual
Brent exception, incorrect scalar values and a quadrature warning. These are
software-test results, not completed governed acceptance evidence. The governed
injection stage was never reached.

## Governed evidence and unavailable obligations

| Obligation | Retained Session 14g result |
| --- | --- |
| Engineering suite | Stopped with `TypeError`; no per-fixture results returned |
| Frozen maximum cases | 0 of 108 completed; all 108 unavailable |
| Component-reference comparisons | 0 of 366 completed; all 366 unavailable |
| Fixture permutations | 0 of required 399 completed |
| Exact historical joint-vector reproduction | Not executed in the governed audit |
| Full certified piecewise/reference verification | Not executed in the governed audit |
| Governed failure injections | Not executed; unit tests are reported separately |
| Derived readiness | False; unavailable obligations remain false |
| Failure persistence | Execution, failure, access and closure records retained locally |
| Publication validation | Failure schema and existing hashes passed |

The engineering stage was prospectively ordered before the reference sweep and
failure-injection acceptance. Its exception prevented the pipeline from reaching
those stages. The returned empty engineering array does not mean no synthetic
calculations occurred before the exception; the number completed internally was
not retained. This diagnostic limitation is explicitly preserved.

## Historical discrepancies preserved

Session 14e calculated its controlled vector before detecting certified
partitions; those partitions were not consumed by its integration call. Its
failure-injection routine changed readiness booleans instead of testing upstream
failure propagation. Session 14g adds prospective wiring without changing the
historical evidence or retrospectively claiming that it tested this route.

Phase 14f's protocol expressly prohibited test changes. Its report nevertheless
described the later pytest fallback as protocol-permitted. Both records remain
unchanged; that contradiction is not resolved by rewriting history. Its
reported full-suite count of “348 passed and three skips” also differs from the
underlying unittest convention: 348 total with three skips means 345 passed.
Session 14g reports totals and passes separately.

## Validation and qualifications

Post-execution validation, without rerunning the governed audit:

| Check | Result |
| --- | --- |
| Focused Session 14g | 19 run, 19 passed, 0 skipped |
| Relevant Session 14-series discovery | 78 run, 78 passed, 0 skipped |
| Full active unittest suite | 367 run, 364 passed, 3 retained scaffold skips |
| Compilation | Passed for source, scripts and tests |
| Failure-publication check | Passed, exit 0; classification remains INVALID |
| Hashes, finite JSON, LF CSV and cross-file schemas | Passed |
| Historical inputs and append-only history | Passed |
| Documentation links, publication scan and diff checks | Checked before closure commit |

The relevant-suite count includes only tests actually discovered by unittest.
Historical standalone pytest functions do not become executed tests merely
because their module imports successfully. No passing CI or software-test result
can override the governed INVALID outcome.

Two initial ad hoc source privacy scans rejected generic rejection literals
(`/Users/`, `/private/`, and `https://`) inside the publication guard. These were
false positives, not leaked paths or URLs. The implementation commit occurred
before the first failed scan's output was reviewed; this ordering lapse is
recorded. A corrected scan distinguishing bare rejection prefixes from actual
private paths/URLs passed before the governed audit. No source repair was needed.

## Closed package

The seven public files are the contract, wiring checks, reference-comparison CSV,
failure-injection record, readiness, QC and manifest under
[the production-verification output directory](../outputs/continuous_occlusion_production_verification/manifest.json).
The empty reference CSV preserves its frozen header. Generated bytes were not
manually edited. Dense traces, execution/access records and marker files remain
ignored.

Manifest SHA-256:
`7b04ec5d5fff16e949ce072ee799b49906d529e59edc26df5b10e017fad15506`.

All historical Session 14–14f files, field formulas, parameters, references,
released API, package version, lockfile, release tag and claim ledger remain
unchanged. No empirical geometry, provider product, target, model, utility,
option share, protected/withheld/pose data, xT or progression record was accessed.
Accessibility remains **PROXY ONLY** and suppression **NOT SUPPORTABLE**.

## Exactly one next action

Undertake a separately governed, synthetic-only failure-localization and
diagnostic-preservation review of the engineering-check path, retaining the
active fixture, traceback and completed checks before any newly authorized
reproduction. This should establish the exact `TypeError` source before proposing
a numerical or detector repair. Do not resume Session 14R or rerun Session 14g
under the current authority.
