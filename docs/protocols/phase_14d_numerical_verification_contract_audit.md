# Phase 14d — Synthetic verification-contract audit

Frozen 2026-09-11 before implementation or numerical probes. Starting local,
tracking and live main: `d80aa7ff8438568e874263f8273bbe82c35121d4`.
Release tag target: `f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`.

## Question, prior exposure and boundaries

Does the verification supporting a Session 14R retry establish its claimed
numerical obligations? Session 14c remains a historical A/1/1 closure; all
Sessions 14–14c code, reports, protocols and output bytes remain immutable.

Planning inspected source only and found that `switch_slopes` compares field
differences with slopes computed from those differences. That inequality is
self-satisfying up to rounding and is not an independent continuity test.
No new numerical counterexample was run during planning.

Only committed synthetic fixtures, published numerical references, source and
environment records are inputs. No empirical, provider, target, model, share,
protected, withheld, pose, threat or progression access. No acquisition,
formula, tolerance, dependency, public API, version or release changes.

## Frozen obligations and engineering fixtures

### Continuity

Give an analytical argument: smoothstep matches values and first derivatives at
0 and 1; positive lateral width prevents division singularities; exponentials,
affine coordinates and norms are continuous for valid fixed origin/defenders.
Finite maxima of continuous functions are continuous. This argument is local to
the valid domain excluding origin–defender coincidence; it proves no uniform
stability as that excluded geometry is approached.

Compare production fields with an independent scalar formula, using origin
(0,0), defender (5,0), queries (4,0), (5,0), (5.5,0), (6,0), (10,0), (10,2).
Also use the same local-axis offsets for origin (1,-2), defender (4,2).
Use absolute and relative 1e-12 agreement, inherited numerical tolerances.
At onset 0/1 and lateral/axis positions, record differences for displacements
1e-1, 1e-2, 1e-3, 1e-4. Finite probes are diagnostics, not proofs.

Exercise the unchanged historical continuity helper on an explicit step:
constant 0.2 before t=0.5 and 0.8 at/after it (plus a zero second column), using
an explicitly supplied synthetic switch. A True flag is an expected audit
finding, not evidence of continuity or a reason to change the helper.

### Switching

Use the frozen 65,536-interval scan and unchanged tolerances. Engineering
fixtures: [t,1-t]; [0.5+0.2*sin(4*pi*t),0.5]; non-envelope crossing
[0.2+0.1*t,0.3-0.1*t,0.8]; endpoint tie [0.5+0.4*t,0.5-0.1*t];
all zero; duplicate constants [0.7,0.7,0.2]; and [t,1-t,0.5] three-way tie.
Tie interval [0.25,0.75]: fields 0.6 and 0.6-0.1*max(0.25-t,t-0.75,0).
Freeze a non-node tie boundary variant [0.251,0.749] to distinguish sampled
equality runs from exact boundaries.

Coverage stressors: opposite signs of size 1e-200 about root 0.500001;
and two crossings strictly inside one grid cell using baseline 0.4 and a
triangular bump of height 0.2 over baseline 0.3, centre
(32768.5)/65536 and half-width 0.4/65536. The latter demonstrates finite-grid
limitations only and is not asserted to be one of the football field formulas.
Test duplicate-root removal directly and a forced Brent exception. Do not fix
the historical sign-product implementation or infer completeness from fixtures.

For all 108 frozen fixture/candidate cases, repeat detection and apply every
defender permutation (at most 24). Compare complete results after inverse
mapping: switches/locations, before/at/after owner sets, crossing pairs,
endpoint/multiway flags, envelope values, tie intervals and maximizing sets.
Record failures as evidence; do not alter roots to obtain equality.

### Controlled Simpson

For all 108 fixture/candidate cases, calculate all individual, union and maximum
components jointly. Start at 256 intervals, double to at most 16,384; accept the
first finer vector for which every component changes by at most 1e-7. No
component-specific early acceptance. Compare all 366 accepted component values
with the published references. Use Session 14b references for its 362 available
components and Session 14c piecewise values for the exact four formerly
unavailable maximum cases. Require unique exact key sets and hash validation.
Report acceptance count, worst successive change and each reference error.
Use the inherited 1e-6 reference-error bound, not a new practical tolerance.
Cap exhaustion or unavailable reference remains a failed obligation.

### Enforcement

Exercise the actual historical decision AST in an isolated synthetic harness
(no call to its review runner and no output writes) using valid records and
one injected defect at a time: warning/unavailable case, failed numerical
agreement, nondeterminism, permutation mismatch and failed continuity. Record
classification and retry readiness independently; readiness 1 or 2 is not
permitted when a required obligation is unresolved. Exercise a failed root
through the actual helper. Inspect missing clean-tree checks and verify the new
audit's own exclusive marker, failure ledger, closure and no-rerun behavior.
This harness measures historical enforcement; it does not repair it.

## Execution and outputs

Add an isolated internal audit helper and
`scripts/session_14d_verification_audit.py` with `preflight`, `audit`,
`publication-check`. Commit protocol first and tested implementation second.
No governed audit until both are committed and the tree is clean.

Public namespace `outputs/continuous_occlusion_verification_audit/` contains
exactly `verification_obligations.json`, `oracle_results.json`,
`controlled_integration.csv`, `switching_coverage.csv`, `qc.json`, `manifest.json`.
JSON rejects unexpected schema keys, duplicate keys and nonfinite values;
CSV uses fixed headers, LF and exact keys/counts. Bind historical inputs,
protocol, implementation, environment and outputs in the manifest; place its
own hash in the report. Detailed state and execution records remain under
ignored `local/`; no provider records exist in this audit.

Exclusive marker precedes audit calculation. Log stages immediately; atomically
write files and validate all before closing the manifest or displaying results.
Expected counterexample failures are audit findings and permit completing the
other frozen obligations. An unexpected execution defect preserves partial
artifacts, records INVALID and stops without patching or rerunning. Failure
publication supports absent artifacts explicitly; never rebind closed hashes.

## Decisions, validation and closure

PASS only if all obligations support the retry with at most documentary
qualification. BLOCKED if demonstrated verification/implementation defects need
new code; UNRESOLVED if evidence is insufficient without a demonstrated defect;
INVALID if this audit fails execution/integrity. A successful controlled vector
comparison cannot override a switching or enforcement defect.

Run focused and inherited Session 14-series tests, full active synthetic suite,
compilation, schemas/hashes, source firewalls, links, publication/staged scans,
append-only research-log and history checks, and git diff --check. Record passes
and retained skips separately. Third commit closes outputs/report and one log
entry. Push; verify clean local/tracking/live heads and unchanged tag; stop.

Recommend exactly one later action: resume 14R planning on PASS or a separately
governed bounded repair/evidence review otherwise. No historical code repair,
empirical retry or claim promotion is authorized. Future 14R retains synthetic-
only equal-minimum cases, continuous overlap summaries, pre-access visual QA
and label-free development scope.
