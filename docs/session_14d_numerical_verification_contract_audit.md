# Session 14d — Synthetic verification-contract audit

## Decision

**Execution: VALID.** **Audit result: BLOCKED — Bounded repair required.**

Session 14R remains paused. All 366 component estimates passed the inherited
controlled-Simpson reference check, and all 108 frozen maximum cases passed full
permutation and repeatability checks. However, the verification contract has
implementation and enforcement gaps that require separate repair authority.
This is not a new finding that the continuous field formulas are discontinuous.

The historical Session 14c A/1/1 result remains preserved. This later audit
qualifies what its checks establish and blocks using that result alone as
sufficient authority for an empirical retry. Sessions 14, 14a and 14b also remain
unchanged. No historical output, source, test, protocol or report was rewritten.

## Authority and chronology

Starting clean local `HEAD`, `origin/main` and live GitHub `main` all matched
`d80aa7ff8438568e874263f8273bbe82c35121d4`. The annotated release `v0.1.0` still
peels to `f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`.

The [Phase 14d protocol](protocols/phase_14d_numerical_verification_contract_audit.md)
was committed as `705da7a` before implementation and numerical probes. Tested
internal audit instruments were committed as `1497aff` before the one governed
execution. The final closure commit contains this report and the six public
artifacts; its exact ID is provided in the delivery handoff rather than embedded
recursively in its own bytes.

Planning-time evidence was source inspection only: the continuity inequality
uses slopes computed from the same sampled differences it purports to check.
The numerical step counterexample below was first governed by Phase 14d.
Pre-execution software tests used synthetic engineering fixtures; the full
108-case/366-component evidence was produced once by the committed audit.

## Continuity obligation

Each frozen formula is continuous on its valid domain. For fixed distinct
origin and defender, the axial and perpendicular coordinates are continuous in
the query point. Smoothstep agrees at both endpoints with its adjacent pieces:
G(0)=0, G(1)=1, and the derivative is zero on both sides of each join. Lateral
width is positive (at least two metres). The exponential and all remaining
compositions are continuous. The isotropic Gaussian is continuous as well.
A finite maximum preserves continuity, as follows from
`abs(max(f_i)-max(g_i)) <= max(abs(f_i-g_i))`. Finite-product union is also
continuous. This argument excludes the undefined origin–defender coincidence
and establishes no uniform stability as that geometry is approached.

All **36 independent scalar value oracles** passed the inherited absolute and
relative `1e-12` comparisons across axial and rotated geometry. Ninety-six
perturbation records cover both query axes, onset/axis/lateral locations and
steps from `1e-1` to `1e-4`. These finite differences are implementation
correspondence diagnostics, not mathematical continuity proofs.

The historical `switch_slopes` flag returned **True** for an engineering step
from 0.2 to 0.8 at t=0.5: a known jump of 0.6. The reported left slope was
`600000.0000000001` and right slope `0.0`. Because the inequality bounds each
sampled difference by its own quotient times the step, it cannot independently
distinguish a jump from continuity. The counterexample uses a supplied synthetic
switch record to isolate this check; it does not assert that a frozen field
formula produces that step.

## Switching obligation

All 108 fixture/candidate cases repeated exactly and passed **399 full
permutation comparisons**, including the identity permutations. For each case,
comparison includes root locations, before/at/after owners, crossing pairs,
endpoint/multiway flags, envelope values, tie intervals and maximizing-defender
sets. This extends the historical comparison signature, which omitted some of
those records. No discrepancy appeared within the closed fixture family.

The engineering fixtures found the expected single/multiple and three-way
crossings, excluded non-envelope crossings, preserved all-zero support without
owners, retained duplicate constant fields and deduplicated near-identical root
records. A forced Brent exception was rejected by the actual historical helper.

Two additional limitations were demonstrated:

- **Raw-sign underflow:** a pair with one raw sign-changing bracket at about
  t=0.500001 and values of order `1e-200` caused zero Brent calls. Multiplying
  the consecutive differences underflows to zero, so the `< 0` product test
  loses a raw sign change. These fields are within the numerical ownership tie
  tolerance; this example establishes noncompliance with the raw-bracket scan
  contract, not a materially different maximum integral.
- **Tie boundaries:** a known exact maximal tie interval `[0.251, 0.749]` was
  reported as `[0.251007080078125, 0.748992919921875]`, the inward grid nodes.
  A grid-aligned `[0.25,0.75]` interval was recorded correctly. Sampled equality
  runs do not establish exact boundaries away from nodes.

A separate continuous triangular-bump fixture has two crossings inside one
65,536-grid cell. The historical scan found neither. That deliberately generic
engineering function is not one of the three field formulas. It demonstrates
why success on the finite fixture family is not a theorem that all possible
maximum switches will be detected. No empirical coordinates or parameter search
were used to discover or tune these examples.

## Controlled-Simpson obligation

The audit reproduced the joint vector rule exactly: start with 256 intervals;
double through at most 16,384; accept the first finer vector only when **every
individual, union and maximum component** changes by at most `1e-7`.
A unit fixture verifies that a converged maximum cannot terminate refinement
while an individual component remains unconverged.

All **366 component comparisons across 108 cases passed** the inherited
`1e-6` reference-error bound. References were 362 available Session 14b values
plus the exact four Session 14c piecewise maximum replacements, verified against
committed source hashes and their manifests. No adaptive references were tuned
or regenerated. The largest error was `4.1576548232002963e-08` for expanding
maximum on synthetic star edge 1 (the symmetric case has the same behavior).
Its joint vector accepted 4,096 intervals with worst successive change
`3.9777865279422286e-08`.

Accepted component counts by shared case resolution were 176 at 512 intervals,
48 at 1,024, 96 at 2,048, 36 at 4,096 and 10 at 8,192. These are component
counts, not independent cases. Every case accepted before the cap. The maximum
error exceeds the formerly reported `2.8987435979344056e-08` because the
completed comparison now includes the four formerly unavailable references;
it remains well inside the frozen bound. This is evidence for the finite
synthetic family, not a universal error guarantee.

Session 14c's separate helper had tested maximum-only stopping. This audit
closes that vector-level evidence gap, without modifying the historical helper.
It does not override the switching/enforcement defects.

## Failure-enforcement obligation

The audit extracted the historical runner's actual decision statements into an
isolated synthetic harness. It never invoked the historical review command or
wrote historical results. Warning, unavailable-reference and numerical-agreement
injections were represented by a failed `available` record at the decision
boundary; this does not claim to exercise every upstream exception path.

| Injected condition | Historical classification | Historical retry readiness |
|---|---|---|
| Valid control | A | 1 |
| Warning / unavailable reference / failed numerical agreement | B | 2 |
| Nondeterminism / permutation mismatch | B | 2 |
| Failed continuity diagnostic with otherwise valid records | A | 1 |

None of the six injected failed obligations prevented all readiness-1/2
conclusions. The continuity injection deliberately tests an inconsistent
aggregate record: the decision layer permits A when `all_continuous` is false
but per-case availability is true. The readiness-2 path also does not establish
that its failure is confined to maximum or independently verify the remaining
components before allowing a reduced retry. A separate retirement proposal can
be legitimate, but it cannot silently discharge those missing obligations.

Source inspection also confirms that the historical review has no clean-tree
check. Its committed-file checks protect listed files but do not implement the
broader clean-tree prerequisite. Session 14d's own lifecycle tests verify a
clean-tree gate, exclusive marker, preserved failure record, immutable outputs,
publication tamper rejection and refusal to rerun after failure.

## One recommended next action

Undertake **one separately governed bounded verification repair and synthetic
acceptance audit** before returning to Session 14R planning. Preserve all
historical implementations. The prospective repair should introduce a new
internal verification module and orchestration that:

- detects opposite raw signs without multiplying potentially tiny values;
- distinguishes sampled equality runs from certified tie boundaries, and
  rejects unresolved ownership partitions rather than inventing exact ones;
- uses the analytical continuity argument and independent formula checks,
  retaining slope measurements solely as diagnostics;
- compares complete permutation records and makes every failed required
  obligation block retry readiness, including inconsistent aggregate records;
- requires a clean committed implementation and validates the joint all-component
  Simpson rule against the now-complete reference set;
- explicitly limits finite-grid coverage claims and treats unresolved switching
  evidence as a stop, without changing field formulas or widening tolerances.

Regression fixtures must retain the raw-underflow bracket, off-grid tie plateau,
hidden within-cell crossings, discontinuous step, every injected readiness
failure, full permutations and all 366 joint-vector reference comparisons.
The future protocol must define the exact tie-certification/failure behavior
before implementation. No repair or rerun occurred in Session 14d.

## Verification, publication and limitations

Focused Session 14/14a/14b/14c/14d suite: **59 passed, zero skipped**. Full active
suite: **345 passed, three retained scaffold skips** (348 total). Compilation,
source/input/environment checks, reference bindings, output schemas/hashes,
publication/privacy checks, documentation links, append-only history and staged
inspection, and `git diff --check` passed. Initial pre-commit tests exposed a
macOS temporary-path symlink in the test harness; resolving the synthetic test
root fixed the harness before implementation freeze. No governed audit rerun
or post-exposure code repair occurred.

The manifest in `outputs/continuous_occlusion_verification_audit/` has SHA-256
`1dfe9506aa0e5b10c74877e523f7be779cf75dace9e4ed217bcf50e01c9b6e5d`.
It binds protocol, implementation, input authorities, the locked environment and
all five evidence/QC files. Dense records and the append-only execution ledger
remain ignored. The execution marker remains present and prevents another run.
Final closure and remote synchronization identifiers are in the delivery handoff.

No empirical population, provider product, target, fitted model, utility, option
share, reserved/withheld detail, pose, xT or progression record was accessed.
The full software suite exercises historical model functions on synthetic
fixtures only; no empirical models or historical model artifacts were loaded by
this audit. No acquisition, dependency, package API/version or release change
occurred. Claims remain unchanged: accessibility **PROXY ONLY**, suppression
**NOT SUPPORTABLE**, and no cover-shadow, causal, attribution or value claim.

Future Session 14R retains synthetic-only equal-minimum tests, continuous
union-minus-maximum distributions without practical thresholds, pre-access
visual QA and label-free development scope. Session 14R was not begun.
