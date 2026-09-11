# Phase 14b protocol: serialization repair and exact synthetic rerun

**Protocol ID:** Phase 14b  
**Date:** 2026-09-11  
**Status:** FROZEN BEFORE IMPLEMENTATION  
**Starting authority:** `d7151243ec10ea2d455977c5432d0dcc74f33dea`

## Purpose and authority

Session 14b may do exactly two things: normalize NumPy scalar values at the JSON
output boundary and execute one exact rerun of the frozen Session 14a synthetic
numerical review. Session 14a remains closed as **F — UNRESOLVED**, retry
readiness 2. Session 14 remains historically **D — BLOCKED**, readiness 3.

The Phase 14a numerical contract is inherited without amendment. The three field
formulas, parameters, fixtures, Simpson implementation, resolution ladders,
adaptive reference settings, analytical breakpoints, float64 arithmetic,
reference-availability gates, historical `1e-6` gate, classification framework,
method comparisons and failure rules are unchanged.

This phase is synthetic only. It authorizes no empirical population, canonical
state, target, M0/M1 model, option share, provider product, reserved or withheld
material, pose, external xT, progression analysis, scientific candidate
selection or behavioral validation.

## Serialization-only repair

Add one reusable internal output-boundary normalizer. It must recursively convert:

- `np.bool_` to Python `bool`;
- `np.integer` to Python `int`;
- `np.floating` to Python `float`;
- nested lists, tuples and dictionaries to JSON-compatible containers while
  preserving values and deterministic dictionary ordering;
- ordinary Python scalars and `None` without semantic change.

It must reject unsupported objects and nonfinite floating values. It must not
stringify numerical scalars or mutate numerical arrays, field evaluations,
integrals, references or classifications. The JSON encoder remains sorted,
indented, newline-terminated and `allow_nan=False`.

Regression tests must cover nested NumPy booleans, integers and floats, ordinary
scalars, lists, dictionaries, `None`, JSON round trips, type preservation,
determinism, nonfinite rejection and unsupported-object rejection.

## Exact inherited rerun

The repaired runner must reproduce before review:

- 80 intervals: `0.5423405961267106`;
- 160 intervals: `0.5424947427905844`;
- absolute difference: `0.00015414666387381093`.

The ordinary Simpson intervals remain
`16,32,64,128,256,512,1024,2048`. The independent fine ladder remains
`4096,8192,16384,32768,65536`.

References remain scalar SciPy `integrate.quad` with `epsabs=1e-13`,
`epsrel=1e-13`, `limit=1000`, analytical directional onset breakpoints, and a
second run at `1e-11` tolerances. Availability still requires adaptive agreement
within `1e-10`, final-grid agreement within `1e-10`, and fine/adaptive agreement
within `1e-9`.

Run the exact ordered Session 14 fixtures and three candidates once. Retain all
individual, union and maximum components. The four maximum-envelope references
unavailable in Session 14a receive no special handling and must remain governed
by the same rules.

## Outputs and execution controls

Write a separate package under `outputs/continuous_occlusion_numerics_14b/`:

- `convergence.csv`
- `reference_summary.json`
- `failing_fixture_diagnostic.csv`
- `method_summary.json`
- `qc.json`
- `manifest.json`

Historical Session 14 and 14a artifacts remain byte-identical. Detailed
execution records remain ignored. The runner exposes only `preflight`, `review`,
and `publication-check`, uses a new exclusive marker, writes atomically, and
refuses a second review once the marker exists.

No new fixture, metric, tolerance or numerical remedy may be added. If any
failure occurs after the rerun begins, preserve it and stop without repairing or
rerunning again in Session 14b.

## Interpretation and closure

Apply the exact Phase 14a A–F numerical classification and separate 1–4 retry
readiness after successful closure. Do not preselect B. Distinguish historical
80-to-160 disagreement, actual 160-interval reference error, 2,048-interval
reference error, usefulness of successive differences, and suitability of
`1e-6` for a future accuracy contract.

Recommend one exact future integration contract only if the complete synthetic
evidence supports it. Specify method, start, refinement, tolerance, maximum work
and failure behavior. Do not execute a Session 14 retry.

Run focused Session 14b and relevant Session 14/14a tests, the full active suite,
compilation, numerical reference and output checks, publication/privacy guards,
documentation links, history preservation, staged inspection and
`git diff --check`. Append the research log, leave the claim ledger unchanged,
push reviewed commits, verify synchronized heads and unchanged `v0.1.0`, and
stop.
