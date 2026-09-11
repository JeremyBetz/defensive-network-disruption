# Phase 14a protocol: synthetic numerical integration review

**Protocol ID:** Phase 14a  
**Date:** 2026-09-11  
**Status:** FROZEN BEFORE GOVERNED REVIEW  
**Starting authority:** `2a2ebe571aa85c0c850dc4139ebcd01350856dae`

## Question and scope

This synthetic-only prerequisite asks whether Session 14's expanding-field
integral was numerically unreliable under its composite-Simpson implementation,
or whether the frozen 80/160-interval agreement gate was an inappropriate
accuracy contract for the unchanged field.

Session 14 remains closed as **D — BLOCKED**, readiness 3. This protocol does
not authorize its empirical population, targets, models, shares, provider
products, reserved or withheld material, pose, external xT, the Session 12
progression branch, scientific candidate selection, or an empirical rerun.
The three Session 14 formulas, parameters, combinations and edge-summary
semantics remain unchanged.

## Prior exposure qualification

Before this protocol was written, planning inspection ran one uncommitted,
synthetic probe of the already published failing fixture. It used the existing
field evaluator, the proposed Simpson ladder, and SciPy adaptive quadrature. It
surfaced the historical 80/160 values, analytical onset locations, an adaptive
estimate, and selected ladder estimates for that one fixture. These observations
are prior exploratory evidence. They must be recorded in the final report and
must not be represented as prospectively produced Session 14a findings.

The governed review still executes the complete fixture/candidate matrix under
the fixed rules below. No fixture, resolution, reference method, threshold or
classification may be changed in response to the governed outputs.

## Frozen inputs

The implementation must import, without modifying:

- `CarrierOriginField`, `combine`, and `simpson_average` from the committed
  Session 14 geometry module;
- the exact ordered fixture generator in the committed Session 14 runner;
- candidates `isotropic`, `expanding`, and `constant_width`;
- `sigma=2.0` metres, onset `a=1.0` metre, half-angle `10` degrees, and the
  `1e-9` metre origin tolerance;
- float64 evaluation and the Session 14 union and maximum definitions.

The historical failure must reproduce before the wider review:

- fixture `lateral_x5_y1`, origin `(0,0)`, receiver `(20,0)`, defender `(5,1)`;
- expanding individual field;
- 80 intervals: `0.5423405961267106`;
- 160 intervals: `0.5424947427905844`;
- absolute difference: `0.00015414666387381093`.

Exact equality is required in the locked environment. Failure is an authority
or reproducibility failure and stops the review.

## Integration and reference contract

The ordinary resolution ladder is the fixed even interval sequence
`16,32,64,128,256,512,1024,2048`, giving one more evaluation point at each
resolution. The independent fine-grid sequence is
`4096,8192,16384,32768,65536` intervals.

For every frozen edge, candidate, individual-defender component, union, and
maximum component:

1. Evaluate composite Simpson on the complete ordinary and fine-grid ladders.
2. Establish a scalar adaptive reference with the already locked SciPy
   `integrate.quad`, `epsabs=1e-13`, `epsrel=1e-13`, and `limit=1000`.
3. Repeat adaptive integration with `epsabs=1e-11`, `epsrel=1e-11`, and the same
   limit.
4. For directional fields, supply all analytical locations in `(0,1)` at which
   any defender has `ell=0` or `ell=1`. Deduplicate and sort these locations
   numerically; isotropic fields have no directional onset points.
5. Treat the strict adaptive estimate as the reference only when both adaptive
   estimates differ by at most `1e-10`, the 32768/65536 Simpson estimates differ
   by at most `1e-10`, and the 65536 estimate differs from the strict adaptive
   estimate by at most `1e-9`. These are numerical reference-availability rules,
   not football thresholds.
6. If any required reference is unavailable, retain the diagnostics and classify
   the affected result as unresolved. Do not raise limits or change methods.

For every ordinary-ladder estimate, report the previous-resolution difference,
absolute reference error, and relative reference error when
`abs(reference)>1e-12`. Otherwise relative error is unavailable. All integrals
are segment averages over normalized `t in [0,1]`.

## Integrator and formula diagnostics

Before field-level interpretation, verify the production Simpson helper using
constant, linear, quadratic, and cubic functions at every ordinary resolution.
Require absolute error at most `32*float64_epsilon` for each oracle. Also verify
interval parity, endpoints, weights, normalization, dtype, deterministic output,
and invalid-shape rejection. Oracle failure selects implementation-defect status
and stops before remedy selection.

Use unchanged formulas for zero-field and analytically tractable special cases
where available. Do not manufacture a closed form.

For the historical failing fixture, retain a bounded diagnostic grid containing
only normalized `t`, individual field value, `ell`, `h`, gate and width. Record
the exact `ell=0` and `ell=1` positions, peak location on the fixed 65536 grid,
and the width in `t` of the onset interval. Probe the field at offsets
`1e-1,1e-2,1e-3,1e-4` around the activation boundaries, central ray, lateral
locations and defender location. Report one-sided value differences and whether
the unchanged field is continuous. Higher-derivative changes must be described
separately from value discontinuity.

## Gate review, remedies and decisions

The historical rule `abs(S80-S160)<=1e-6` remains evidence under review. Compare
its difference with each estimate's actual reference error, field magnitude,
ladder behavior, and float64 scale. Classify it as justified, overstrict,
understrict, poorly specified, or unresolved. Do not silently replace it.

Compare only these prospective remedy families:

- fixed higher-resolution composite Simpson;
- doubling, convergence-controlled composite Simpson;
- deterministic adaptive quadrature with analytical onset points;
- retention or rejection of the expanding candidate.

Report evaluation counts and approximate single-process synthetic runtimes.
Runtime is an engineering observation, not a performance claim. No remedy is
applied to Session 14 here.

Choose exactly one numerical classification:

- **A — CURRENT FIELD IS NUMERICALLY SOUND; ORIGINAL GATE WAS INAPPROPRIATE**
- **B — FIELD IS SOUND BUT REQUIRES HIGHER/CONTROLLED RESOLUTION**
- **C — INTEGRATION IMPLEMENTATION DEFECT**
- **D — EXPANDING-FIELD FORMULA CREATES PROBLEMATIC NUMERICAL BEHAVIOR**
- **E — MULTIPLE ISSUES**
- **F — UNRESOLVED**

Decision precedence is: oracle failure selects C unless a separate formula issue
also establishes E; an actual field discontinuity or stable-reference failure
selects D/F as supported; otherwise a continuous stable field whose 160-interval
estimate exceeds `1e-6` reference error selects B; a 160-interval estimate within
`1e-6` despite failing the agreement proxy selects A. Complete evidence may
select E where independent issues coexist.

Separately choose retry readiness 1–4 exactly as requested. An exact future
contract may be recommended only if one tested method meets a stated synthetic
reference-error bound for every required frozen component. It must specify the
method, resolution or refinement rule, tolerance, maximum work and fail-closed
behavior. No retry occurs.

## Implementation, outputs and stop rules

New code remains internal and adds no root export, dependency, version, release,
model or data route. The runner exposes only `preflight`, `review`, and
`publication-check`. It uses a persistent exclusive marker, atomic public writes,
an ignored append-only execution ledger, strict schemas, and immutable hashes.

Public outputs under `outputs/continuous_occlusion_numerics/` are limited to:

- `convergence.csv`
- `reference_summary.json`
- `failing_fixture_diagnostic.csv`
- `method_summary.json`
- `qc.json`
- `manifest.json`

High-resolution arrays and execution records remain ignored. Any authority,
oracle, reference, output-integrity, or publication failure preserves available
evidence and stops without changing Session 14 or rerunning under a revised rule.

Run focused and full active tests, compilation, numerical oracles, schema/hash
checks, documentation links, publication guards, history preservation, staged
inspection, and `git diff --check`. Append the research log without changing the
claim ledger. Recommend exactly one later action and stop.
