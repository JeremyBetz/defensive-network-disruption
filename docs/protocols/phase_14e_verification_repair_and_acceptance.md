# Phase 14e — Verification repair and synthetic acceptance audit

## Authority and scope

This protocol is prospective authority for one synthetic-only repair and
acceptance audit starting from `9188222c4270ba1a89963ae1bbdb9003b0bf9f1e`.
It preserves the `v0.1.0` release target and every Session 14–14d artifact and
implementation. Session 14R remains paused. No empirical population, provider
product, target, fitted model, utility, option share, protected or withheld
record, pose, xT, or progression record may be accessed.

Only four Session 14d defects may be repaired in a new internal module:
non-independent continuity verification, raw-sign loss through floating-point
multiplication, sampled rather than certified tie-interval boundaries, and
readiness paths that do not fail closed. Field formulas, parameters, candidate
families, reference values, integration methods, and numerical tolerances are
frozen.

## Independent continuity contract

The isotropic Gaussian is continuous. For directional fields, smoothstep agrees
in value and first derivative at `ell=0` and `ell=1`; directional width remains
strictly positive; affine coordinates, norms, and exponentials are continuous
on the valid domain. Finite maximum and finite-product union preserve
continuity. Origin–defender distances at or below `1e-9` metres remain excluded,
without a uniform-stability claim near that exclusion.

Production values will be compared with an independently implemented scalar
oracle using absolute and relative tolerance `1e-12`. Frozen metric approach
distances are `1e-1` through `1e-6` metres around formula branches. Frozen
maximum switches use normalized steps `1e-3` through `1e-7`, capped at one
quarter of adjacent partition distance. Independent individual values form the
maximum oracle. A deliberate `0.2 -> 0.8` step must fail because its analytical
one-sided limits differ. Slopes are diagnostic only.

## Switching and tie certification

The new raw-sign detector brackets only when both values are nonzero and their
`signbit` values differ. Exact zero nodes and structural all-zero support remain
separate. It adds no magnitude epsilon. Brent uses the existing absolute
`1e-14`, relative `8 * float64 epsilon`, 100-iteration, `1e-12` residual, and
`1e-12` owner-block rules.

Bracketing oracles use `+/-1e-8`, `+/-1e-12`, `+/-1e-15`, and `+/-1e-200`, plus
same-sign tiny values, exact zero, structural zero, and a crossing adjacent to a
grid-node root. Bracket discovery and envelope-owner confirmation are distinct.

Isolated equality roots are distinct from nonzero-width exact plateaus.
Candidate plateaus arise from contiguous exact-equality grid nodes. Each entry
and exit brackets an exact-zero/nonzero transition; bisection of the exact-zero
predicate continues until the outside and inside points are adjacent float64
values. The certified enclosure retains both points, direction, defender pair,
and maximal owner set. The inside must have exact equality, positive maximal
support, and consistent ownership; the outside must be unequal with compatible
neighboring ownership. Both enclosure endpoints become integration partitions.
Ambiguous topology or a wider-than-adjacent-float enclosure fails closed.
Coincident enclosures deduplicate under `1e-12`; multiway owners are preserved.

Synthetic tests cover isolated and endpoint ties, exact and off-grid plateaus,
three-way and neighboring plateaus, nested non-envelope equality, zero support,
and the frozen `[0.251, 0.749]` oracle. Its mathematical boundary must lie in the
certified enclosure. Complete records must map under every defender permutation.
The 65,536-grid scan remains fixture-scoped; the known two-crossings-within-one-
cell example remains an explicit global-completeness limitation.

## Integration and readiness contract

The prospective Session 14R path is field evaluation, individual values,
union/maximum, certified maximum partitions, joint vector integration,
convergence/reference checks, then machine readiness. Controlled Simpson uses
intervals `256, 512, 1024, 2048, 4096, 8192, 16384`, one joint vector containing
every individual, union, and maximum component, and accepts the first finer
vector only when every component changes by at most `1e-7`. Cap exhaustion
fails. All 366 accepted values must match the 362 Session 14b and four Session
14c references within the inherited `1e-6` error bound. Session 14c root,
ownership, and piecewise tolerances remain unchanged.

`VerificationReadiness` is immutable. Its `ready` property is the conjunction of
continuity, switching, controlled integration, complete references, permutation
equivalence, determinism, failure enforcement, absence of blocking warnings,
and integrity. Callers cannot set or override `ready`. Each obligation is
independently injected with a failure, including a discontinuous surrogate,
missed tiny sign, uncertified tie, root failure, unavailable reference,
non-convergence, permutation mismatch, nondeterminism, blocking warning,
integrity failure, and marker collision. Every failure must yield false and the
valid control true. PASS may derive only from this object.

## Execution, outputs, and stop rule

The separate runner exposes `preflight`, `audit`, and `publication-check`. It
has no empirical, acquisition, model, fitting, or rendering route. Before its
single governed audit, tests must reproduce 108 frozen maximum cases, four
historical maximum references, and 399 full permutation comparisons. The audit
creates an exclusive persistent marker and cannot rerun after exposure.

Public output is limited to the ten named files in
`outputs/continuous_occlusion_verification_repair/`. Schemas are strict; JSON is
finite; CSV uses LF; writes are atomic; and the manifest binds protocol,
implementation, historical inputs, environment, and closed outputs. Dense
arrays, root traces, and execution records remain ignored.

The result is PASS only when derived readiness is true; otherwise it is BLOCKED,
UNRESOLVED, or INVALID according to demonstrated defect, insufficient evidence,
or execution/integrity failure. A failure after audit start is preserved and is
not repaired or rerun. Three commits preserve protocol, tested repair, and
closure/report/log chronology. Claims remain unchanged. PASS recommends exactly
resuming Session 14R under this audited contract; it does not execute Session
14R.
