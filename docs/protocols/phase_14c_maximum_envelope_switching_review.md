# Phase 14c protocol: maximum-envelope switching-point review

**Protocol ID:** Phase 14c  
**Date:** 2026-09-11  
**Status:** FROZEN BEFORE IMPLEMENTATION  
**Starting authority:** `0918fc7425078269e6d39117af95965971b31561`

## Question and boundaries

This synthetic-only prerequisite asks whether the four maximum-envelope
references unresolved in Session 14b arise from derivative kinks where the
maximizing defender changes, and whether deterministic piecewise integration
resolves them.

Sessions 14, 14a and 14b remain closed and immutable. This protocol authorizes
no empirical population, canonical state, provider product, target, model,
option share, reserved or withheld material, pose, external xT, progression
work, behavioral validation or scientific field selection.

The exact 36 Session 14 fixtures and three candidate fields produce 108 maximum
cases. The four references marked unavailable in the committed Session 14b
reference summary are the historical unresolved group; the remaining 104 are
controls. No fixture or method may be added after execution begins.

## Unchanged field contract

For edge parameter `t in [0,1]`, individual fields remain the exact committed
Session 14 functions `O_d(t)` and the envelope remains
`M(t)=max_d O_d(t)`. Field formulas, parameters, onset semantics, maximum and
union definitions, coordinate handling and float64 arithmetic are unchanged.

The review distinguishes field continuity, envelope differentiability,
argmax-owner sets and numerical integration. Maximum is a geometric comparator,
not a probability, defender contribution or defensive value. The primary union
candidate is outside the repair target.

## Switching-point contract

Evaluate every individual field on 65,536 equal intervals. Exact all-zero
directional support has no owner and produces no switch. For every defender pair:

1. Detect raw sign changes and exact-zero grid nodes in the pairwise difference.
2. Solve sign-changing brackets with SciPy `brentq`, `xtol=1e-14`,
   `rtol=8*float64_epsilon`, and `maxiter=100`.
3. Require absolute pairwise residual at the root at most `1e-12`.
4. Deduplicate roots within `1e-12` normalized `t`.
5. Determine envelope owner sets with the existing absolute `1e-12` block-high
   rule. A true interior switch requires different nonempty maximal-owner sets
   immediately before and after the root and the crossing defenders tied in the
   maximal block at the root.
6. Probe ownership at `min(1e-7, one quarter of the distance to the neighboring
   partition boundary)`. A nonpositive probe distance blocks the case.

Contiguous exact pairwise-equality grid regions are retained as tie intervals
only when the tied fields are maximal and the envelope is nonzero. They are not
expanded into many roots. Endpoint ties are recorded separately. Three or more
maximal defenders at a root form a multiway switch; no unique owner is invented.
Zero-width and duplicate partitions are removed only under the `1e-12`
deduplication rule.

Switch locations and owner transitions must reproduce exactly. Defender
permutation must preserve switch locations, multiplicities and mapped owner
sets after applying the inverse permutation.

## Piecewise integration contract

Partition `[0,1]` at its endpoints, all analytical directional `ell=0` and
`ell=1` onset points, true envelope switches and maximal tie-interval boundaries.
Integrate the unchanged maximum field over each positive-width piece with scalar
SciPy `quad`, `epsabs=epsrel=1e-13`, and `limit=1000`; repeat at `1e-11`.
Combine piece integrals with `math.fsum`.

Availability requires:

- strict and repeated piecewise estimates within `1e-10`;
- piecewise and the Session 14b unsplit-with-respect-to-envelope-switches
  adaptive estimate within `1e-10`;
- piecewise and direct 65,536-interval Simpson within `1e-9`;
- no warning, nonfinite result, root failure, ownership ambiguity or
  nondeterminism.

Also calculate switch-split Simpson estimates at nominal 32,768 and 65,536
whole-edge spacing. Within each piece use
`max(2,2*ceil(nominal_intervals*piece_length/2))` intervals. Report actual
interval and evaluation totals. For each historical unresolved case, require
the two split estimates to agree within `1e-10`.

The unsplit adaptive and direct Simpson values remain independent comparators;
the piecewise result is not assumed to be truth merely because it is split.
Do not adjust grids to align with observed switches.

## Kink and convergence diagnostics

For every true switch, report the envelope value, owner sets, and one-sided
slopes using normalized step
`min(1e-6, one quarter of adjacent partition spacing)`. Report slope differences
without a categorical sharpness threshold. Confirm value continuity under the
`1e-12` field-value rule. An envelope jump is a deeper defect.

For all 108 cases report switch count, number of maximizing defenders, minimum
switch spacing, endpoint switches, multiway switches, tie intervals, direct-grid
distance to the nearest switch, historical fine-grid change and piecewise
agreement. Summarize controls and unresolved cases separately. No significance
test or empirical interpretation is authorized.

## Decisions

Choose exactly one result:

- **A — SWITCHING POINTS EXPLAIN THE MAXIMUM-ENVELOPE REFERENCE FAILURES** only
  if all four unresolved cases contain true switches, become stable piecewise
  references, pass split-Simpson agreement and behave consistently with controls.
- **B — SWITCHING POINTS CONTRIBUTE BUT DO NOT FULLY EXPLAIN FAILURES** when only
  some cases satisfy A's mechanism and resolution conditions.
- **C — MAXIMUM ENVELOPE IS NUMERICALLY VALID BUT DISPROPORTIONATELY COMPLEX**
  when all integrals are valid but switching is not the specific explanation and
  the comparator requires disproportionate machinery.
- **D — MAXIMUM-ENVELOPE REPRESENTATION / IMPLEMENTATION HAS A DEEPER NUMERICAL
  PROBLEM** for discontinuity, unstable switching or deeper defects.
- **E — MULTIPLE ISSUES** for independently established problems.
- **F — UNRESOLVED** when required evidence remains unavailable.

Retain maximum for future empirical comparison only if all 108 cases pass the
piecewise contract, switch detection is deterministic and permutation-stable,
and all comparison tolerances pass. Otherwise retire maximum from future
empirical Session 14 work without changing the primary union field.

Maximum decision: 1 retain with piecewise contract; 2 synthetic-only; 3 retire
from future empirical work; 4 unresolved. Session 14 retry readiness: 1 only for
A plus decision 1 and verification of the prior controlled-Simpson candidate on
all 366 references; 2 when maximum is retired and the remaining 362 references
support a newly frozen retry; 3 for partial/complex/unresolved evidence; 4 for a
deeper continuous-field defect.

## Implementation, outputs and stop rule

New switching helpers remain internal. Add no root export, dependency, version,
release or empirical route. The runner exposes only `preflight`, `review`, and
`publication-check`, with a new exclusive marker, atomic writes, immutable
hashes and an ignored append-only ledger.

Write only these public files under
`outputs/continuous_occlusion_max_switching/`:

- `switch_summary.csv`
- `unresolved_case_comparison.csv`
- `control_case_comparison.csv`
- `convergence_by_switch_count.csv`
- `method_summary.json`
- `qc.json`
- `manifest.json`

Dense arrays remain ignored. No public diagnostic plot is required. If any
failure occurs after governed review begins, preserve it and stop without repair
or rerun in Session 14c.

Run focused and relevant Session 14-series tests, the full active suite,
compilation, deterministic roots, piecewise/reference checks, schemas and
hashes, publication/privacy guards, documentation links, history preservation,
staged inspection and `git diff --check`. Append the research log, leave the
claim ledger unchanged, recommend one later governed action and stop.
