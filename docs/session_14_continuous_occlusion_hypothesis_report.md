# Session 14 — Bounded continuous occlusion hypothesis study

## Decision and execution status

**Candidate classification D — BLOCKED at the synthetic numerical prerequisite.**
**Cover-shadow readiness 3 — NEEDS REPRESENTATION REVISION**, specifically the
numerical evaluation contract, before candidate comparison can proceed. This is
not evidence that the field formulas are unsuitable, that simple geometry is
better, or that a cover-shadow interpretation is valid.

The frozen 0.25/0.125-metre composite Simpson agreement rule failed on a prescribed
synthetic fixture. Execution stopped before development preparation, all empirical
field evaluation, candidate selection and rendering. The stop is an observed
acceptance-gate failure, not an empirically negative comparison. No sampling
change, tolerance relaxation, field amendment or rerun was performed.

The partial implementation is explicitly a **prerequisite implementation only**:
field primitives, checked edge integration, tests, synthetic gate and immutable
blocked closure. The empirical preparation/analysis and rendering routes are
unavailable guards, not completed capabilities. No released API change is claimed.

## Exact synthetic finding

Origin `(0,0)`, receiver `(20,0)`, single defender `(5,1)`, expanding candidate:

| Frozen check | Observed value |
| --- | ---: |
| Coarse spacing / intervals | 0.25 m / 80 |
| Fine spacing / intervals | 0.125 m / 160 |
| Coarse segment-average estimate | 0.5423405961267106 |
| Fine segment-average estimate | 0.5424947427905844 |
| Absolute difference | 0.00015414666387381093 |
| Maximum permitted difference | 0.000001 |

This difference is between two numerical estimates, not a measured error against
an independently established exact integral. It is sufficient to fail the
prospectively frozen agreement rule. With one defender, individual, union and
maximum fields are mathematically identical; the recorded maximum-difference
component is `individual`. It does not establish a multi-defender overlap defect.

Sixteen fixture–candidate checks passed before this seventeenth check failed.
The completed checks cover all three candidates on four axial fixtures, all
three on the first lateral fixture, and isotropic on the next lateral fixture.
The remaining 91 of 108 planned fixture–candidate checks were not executed after
the stop. In particular, the full depth sweep, equal-minimum comparison and
synthetic-star edge comparisons were not reached. No exact integral or alternate
quadrature was calculated after failure to repair the result.

The one-sided cubic onset is analytically continuously differentiable, but that
does not guarantee that this fixed numerical spacing passes a specific integral
accuracy check. The cause of the failed agreement has not been independently
diagnosed. An implementation or quadrature-contract review must distinguish
these possibilities before any further evaluation.

## Frozen representations

For origin b, defender d and query q, set r=norm(d-b), u=(d-b)/r,
ell=(q-d) dot u and h=abs((q-d)_x*u_y-(q-d)_y*u_x). Scale sigma=2 m, onset a=1 m,
and expansion half-angle alpha=10 degrees are fixed synthetic design conventions.

G(ell) is zero for ell<=0, cubic `3t^2-2t^3` for t=ell/a in (0,1), and one
thereafter. The three formulas are:

- Isotropic: `exp(-norm(q-d)^2/(2*sigma^2))`.
- Expanding: `G(ell)*exp(-h^2/(2*(sigma+max(ell,0)*tan(alpha))^2))`.
- Constant-width: `G(ell)*exp(-h^2/(2*sigma^2))`.

Union `1-product(1-O_d)` is primary; maximum is the comparator. Numerical sorting,
log1p/expm1, exact one handling and preserved multiplicity implement the union.
These are dimensionless strengths, not probabilities. Directional fields have
no longitudinal attenuation and vanish at/before the defender plane. Neither
body dimensions nor behavioral evidence establish those choices.

The internal immutable `CarrierOriginField` evaluates individual/combined points
and attempts normalized segment integration. `EdgeFieldSummary` represents a
successful checked result. Undefined origin–defender direction at <=1e-9 m fails
closed for the common candidate contract; the tolerance has no football meaning.
No package version, root export, dependency or lockfile changed.

The planned empirical origin was the carrier-coordinate proxy, not measured ball
position. The canonical population was neither opened nor newly hashed by this
session because the numerical gate failed first. Its expected historical hash
remains in the contract; no new population-verification claim is made.

## Evidence unavailable after the stop

All development items are **not executed — synthetic prerequisite blocked**:
receiver/segment distributions, correlations, gap correspondence, union-minus-max
sensitivity, top-k field-strength fractions, multi-edge maxima and comparisons
with the isotropic baseline. No candidate winner is selected.

The software tests establish basic invariances, query-point lateral monotonicity,
onset values, stable union behavior and fail-closed integration mechanics. They
do not complete the planned perturbation study or field-family stress tests.
No `smoothness_summary.json`, SVG or GIF exists. Visual QA, double rendering and
Session 13 layout improvements were not reached. Its historical SVG is unchanged.

Session 13's classifications remain historical evidence. Its gap percentiles
are distributions of state-average gaps, not individual-edge gaps. Session 14
has not recomputed or independently confirmed those findings.

## Authority and verification

Starting local/tracking/live main was clean and synchronized at
`9754a03abc5701934313432e815b4bc29e39ee7b`. The
[Phase 14 protocol](protocols/phase_14_continuous_occlusion_hypotheses.md) and
[candidate contract](../outputs/continuous_occlusion_hypotheses/candidate_contract.json)
were committed as `fa45495` before new implementation or evaluation. Tested
prerequisite code was committed as `75c16bb` before the fixed acceptance sequence.
The final commit closes the blocked result. No population-authority checkpoint
was created or implied.

Protocol SHA-256:
`42067b3b68260ef39936405dce1575b57f4e2275221182a5d1c0dc308a057e69`.
Contract SHA-256:
`c19dfad27f9adb1d439ecfd5beb7914d0aadd6ca3bdeec4945525151a42a87df`.

Focused software suite: **17 passed, 0 skipped**. Full active synthetic suite:
**303 passed, 3 retained skips**, 306 total. The distinct scientific acceptance
sequence recorded **16 passed fixture–candidate checks, 1 failed, 91 not reached**.
Passing software tests must not be confused with passing that acceptance gate.

Tests cover fixed parameters, immutability, finite inputs, undefined origins,
radial/onset oracles, lateral/reflection/rotation/translation properties, defender
permutation, duplicate union behavior, tiny strengths, exact polynomial Simpson
integration, degenerate edges, forced quadrature failure without fallback,
output namespace/path/symlink guards, absence of empirical/model routes,
exclusive marker, blocked closure and output tamper detection. Acquisition and
partition-specific projection tests for a future empirical reader are not claimed;
that reader was not implemented and cannot be invoked here.

Compilation, exact manifest/output hashes, failure-state schema checks,
publication scan, links, append-only records, historical preservation, staged
review and `git diff --check` were checked for closure. A first test shell wrapper
used zsh's read-only `status` name after the suite had passed; a corrected wrapper
confirmed successful test exit. This affected no implementation or scientific
evidence. No dependency installation or numerical-environment change occurred.

The [synthetic checks](../outputs/continuous_occlusion_hypotheses/synthetic_checks.json),
[implementation authority](../outputs/continuous_occlusion_hypotheses/implementation_authority.json)
and [QC](../outputs/continuous_occlusion_hypotheses/qc.json) are bound by the
[manifest](../outputs/continuous_occlusion_hypotheses/manifest.json), SHA-256:
`249c4fcb42c472290305356140066383097428432385951aea4803aa39d9e459`.
Publication checks verify existing hashes without rewriting generated artifacts.
Detailed access/execution evidence remains ignored. No empirical records exist.

## Twenty-five handoff items

1. Starting HEAD: `9754a03abc5701934313432e815b4bc29e39ee7b`.
2. Ending HEAD: final delivery handoff, avoiding a recursive commit reference.
3. Protocol: Phase 14, `fa45495`, hash above.
4. Candidates: isotropic, expanding, constant-width; partial synthetic sequence only.
5. Formulas and fixed 2 m / 1 m / 10-degree parameters: above and contract.
6. Combination: bounded union primary, maximum comparator; no probability interpretation.
7. Synthetic invariants: software checks pass; acceptance sequence blocked as recorded.
8. Equal-minimum stress test: not reached.
9. Smoothness: onset formula C1 by construction; full perturbation summary not executed.
10. Receiver-distance correspondence: not executed.
11. Segment-distance correspondence: not executed.
12. Empirical redundancy/overlap sensitivity: not executed; union unit tests only.
13. Empirical multi-edge findings: not executed.
14. Baseline/directional comparison: incomplete; no comparative conclusion.
15. Candidate classification: D — BLOCKED at numerical prerequisite.
16. Cover-shadow readiness: 3 — evaluation/representation contract needs review.
17. Selected candidate: none.
18. Software: internal prerequisite implementation only; later stages unavailable.
19. SVG/GIF: neither produced; static gate not reached, GIF unauthorized.
20. Claim ledger: unchanged.
21. No targets, receiver ranks, model scores, shares or model artifacts accessed.
22. No development rows, reserved detail, withheld, pose or provider products accessed.
23. Checks: 17 focused passes; 303 full passes/3 skips; acceptance failure distinct.
24. Commits: `fa45495`, `75c16bb`, then reviewed failure closure; final push/sync in handoff.
25. One next direction: separately governed synthetic numerical-integration review.

## Limits and one recommendation

Recommend exactly one **bounded synthetic numerical-integration review** of the
failed fixture and frozen Simpson contract before a separately authorized retry.
Determine whether the implementation or the sampling/accuracy contract explains
the disagreement; do not assume a formula or tolerance change in advance. This
review was not executed here.

Future behavioral/pose tests, field→edge→option-network→value architecture and
the sister project's option-funneling→pass→defensive-reallocation link remain
conceptual. No pose, value, sister-project or behavioral work is authorized by
this closure. The ten formerly reserved matches are already spent; they are not
fresh protected validation.

Carrier-origin uncertainty, shared-origin geometry, persistent directional tails,
union saturation, fixed scales and offline extrapolated tracking all remain
limitations if the numerical prerequisite is later resolved. Accessibility is
**PROXY ONLY**; suppression is **NOT SUPPORTABLE**. Session 14 stops here.
