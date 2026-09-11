# Session 14c maximum-envelope switching-point review

## Result

**Execution:** VALID

**Numerical classification:** **A — SWITCHING POINTS EXPLAIN THE
MAXIMUM-ENVELOPE REFERENCE FAILURES**

**Maximum decision:** **1 — RETAIN MAXIMUM WITH THE PIECEWISE CONTRACT**

**Session 14 retry readiness:** **1 — READY FOR A SEPARATELY FROZEN SESSION 14
RETRY**

All four maximum-envelope cases left unresolved by Session 14b contain true
interior changes in the maximizing defender. Deterministic partitioning at those
switches produced stable references for all four. All 104 controls also passed
the same piecewise contract. This establishes a numerical explanation and a
future integration contract; it does not reopen Session 14 or validate an
occlusion representation.

Sessions 14, 14a and 14b remain unchanged historical closures. Session 14
remains blocked before empirical access, and no retry occurred here.

## Authority and scope

The clean starting `HEAD`, tracking branch and live GitHub `main` were
`0918fc7425078269e6d39117af95965971b31561`. Annotated `v0.1.0` remained at
`f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`.

The [Phase 14c protocol](protocols/phase_14c_maximum_envelope_switching_review.md)
was committed as `14da49e` before implementation. The isolated switching,
piecewise-integration and test implementation was committed as `9ba9453` before
the governed review. The implementation reused the exact Session 14 fixtures,
field functions, parameters, maximum definition, directional onset points and
float64 behavior.

This review was synthetic only. It opened no empirical population, canonical
state, provider product, target, model, coefficient, utility, option share,
protected or withheld material, pose, external xT or progression record. It
added no root export, dependency, package version, release or field formula.

## Switching evidence

The review scanned 65,536 uniform intervals for each of 108 maximum envelopes.
Pairwise sign changes were solved with the frozen `brentq` contract and checked
against the envelope-owner sets on either side. Across the full fixture set, 14
true interior switches were found. There were no endpoint switches or maximal
tie intervals; one switch was multiway. Switching was deterministic across
repeat execution and invariant to defender permutation after ordinal mapping.

The four historical failures contained six switches:

- the expanding three-defender equal-minimum case had two switches;
- the constant-width three-defender equal-minimum case had two switches;
- each symmetric expanding star-edge case had one switch.

The other 104 controls contained eight switches: 97 controls had none, six had
one and one had two. All switch probes were value-continuous. Their reported
one-sided slope changes ranged from `0.0007775218698843526` to
`22.073825058588348` per normalized edge parameter. These values describe
derivative kinks; no football sharpness threshold was applied.

## Piecewise reference results

The unchanged maximum function was partitioned at endpoints, analytical
directional onset points, verified switches and any maximal tie boundaries.
Scalar SciPy quadrature was run independently on each nonzero-width piece at
`1e-13` and repeated at `1e-11`; piece totals were combined with `math.fsum`.

For the four historical failures:

| Fixture and field | Piecewise reference | Piecewise–unsplit difference | Piecewise–direct 65,536 difference | Split 32,768–65,536 difference |
|---|---:|---:|---:|---:|
| Three defenders, expanding | `0.37006331847771207` | `3.4416913763379853e-15` | `7.361096177049831e-10` | `1.1102230246251565e-16` |
| Three defenders, constant width | `0.2710505198910037` | `2.609024107869118e-15` | `4.009197973608991e-10` | `2.7755575615628914e-16` |
| Synthetic star edge 1, expanding | `0.20875990789799737` | `4.163336342344337e-16` | `2.3414234440188864e-10` | `1.3877787807814457e-16` |
| Synthetic star edge 3, expanding | `0.20875990789799737` | `4.163336342344337e-16` | `2.3414234440188864e-10` | `1.3877787807814457e-16` |

The largest strict/repeated piecewise difference among those cases was `0.0`.
All satisfy the frozen `1e-10` repeated and unsplit-adaptive comparisons, the
`1e-9` direct-Simpson comparison and the `1e-10` switch-split Simpson rule.

Among controls, the largest piecewise/direct difference was
`1.135333493884616e-11`, the largest piecewise/unsplit difference was
`1.4988010832439613e-15`, the largest strict/repeated difference was
`2.220446049250313e-16`, and the largest split-Simpson difference was
`3.3306690738754696e-16`. Every control passed.

The historical whole-grid changes were largest when a grid crossed unsplit
kinks. Switch-to-grid distances at 65,536 intervals ranged from exact alignment
to `5.399263822147837e-06` in normalized `t`. The unresolved cases show that
distance alone is not a monotone error predictor: one switch only
`1.3554150590788794e-07` from a node still belonged to a case with a
`4.009197973608991e-10` final direct error, while other locations and kink slopes
also varied. The deterministic relationship is that unsplit grids sample
piecewise-smooth sections across owner-change locations; no statistical or
causal explanation was claimed.

## Numerical contract and interpretation

Maximum remains eligible as a later empirical comparator under this exact
reference contract:

1. locate switches with the frozen 65,536-interval scan, root solver, owner
   probes, tie handling and permutation check;
2. partition at directional onsets, envelope switches and tie boundaries;
3. integrate every piece at `1e-13`, repeat at `1e-11`, and block unless the
   totals agree within `1e-10`;
4. require the unsplit adaptive comparator within `1e-10` and direct 65,536
   Simpson within `1e-9`;
5. block rather than widen a tolerance when any root, ownership, warning,
   finiteness, repeatability or agreement check fails.

The prior controlled-Simpson candidate was already supported by the 362
available Session 14b component references, with a maximum demonstrated error
of `2.8987435979344056e-08`. Session 14c checked the controlled sequence against
all 108 maximum cases using the new piecewise references, including the four
formerly unavailable cases. Together those authorities cover all 366 component
references and satisfy the readiness-1 condition. Piecewise integration is the
reference method for maximum; controlled Simpson remains the prospective
finite-work evaluation method subject to a separate retry protocol.

The result concerns numerical integration only. It does not select isotropic,
expanding or constant-width geometry; validate a cover shadow; establish
suppression; or support interception, attribution, causality or defensive value.
The primary union field was never implicated by this repair.

## Required 25-item handoff

1. **Starting authority:** `0918fc7425078269e6d39117af95965971b31561`, clean
   and synchronized at execution start.
2. **Release authority:** annotated `v0.1.0` remains at
   `f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`.
3. **Protocol:** Phase 14c, commit `14da49e`, frozen before implementation.
4. **Implementation:** internal switching and piecewise helpers plus a
   synthetic-only runner, commit `9ba9453`.
5. **Fixture authority:** all 36 closed fixtures and three candidates, yielding
   108 maximum cases.
6. **Historical unresolved group:** four exact Session 14b cases recovered.
7. **Controls:** all 104 resolved historical cases analyzed.
8. **Grid:** 65,536 intervals and 65,537 evaluation points per detection scan.
9. **Root contract:** frozen Brent tolerances, residual check and deduplication
   all passed.
10. **True switches:** 14 total; six in historical failures and eight in
    controls.
11. **Owner behavior:** deterministic and permutation-stable; no arbitrary tied
    owner selected.
12. **Tie behavior:** zero maximal tie intervals, zero endpoint switches and one
    multiway interior switch.
13. **Continuity:** all interior switches passed value-continuity probes; slope
    changes are reported without a materiality threshold.
14. **Piecewise references:** 108/108 available.
15. **Former failures:** all four became stable piecewise references.
16. **Adaptive comparison:** all piecewise/unsplit differences passed `1e-10`.
17. **Direct comparison:** all piecewise/direct 65,536 differences passed
    `1e-9`.
18. **Split Simpson:** every formerly unresolved case passed the frozen
    `1e-10` 32,768/65,536 agreement rule.
19. **Controlled Simpson:** verified across all maximum cases and, together with
    the prior 362-reference authority, across all 366 components.
20. **Classification:** **A — switching points explain the failures**.
21. **Maximum decision:** **1 — retain maximum with the piecewise contract**.
22. **Retry readiness:** **1 — ready for a separately frozen Session 14 retry**.
23. **Access:** synthetic only; empirical states, targets and models read were
    each zero.
24. **Claims/history:** claim ledger and Sessions 14/14a/14b remain unchanged;
    closure commit, checks and synchronization are recorded in the final handoff.
25. **One next action:** freeze a separate Session 14 retry using the verified
    numerical contract. This review does not execute it.

## Outputs and preservation

The seven public artifacts are under
`outputs/continuous_occlusion_max_switching/`. The manifest SHA-256 is
`ee280e8ef0dc589091eada9b143e484922ef64d8a9519e6560141065ba32b717`.
Dense arrays and execution records remain ignored. The publication checker
validates already-bound hashes and does not rebind outputs.

No optional diagnostic plot was needed. No package surface, dependency, lock,
release, claim ledger, field implementation or historical numerical artifact
changed.

Focused Session 14/14a/14b/14c verification ran 47 tests: 47 passed and none
were skipped. The full active suite ran 336 tests: 333 passed and three retained
scaffold tests were skipped. Compilation, deterministic-root checks, numerical
agreement rules, schemas, bound output hashes, publication/privacy guards,
documentation links, append-only history, staged-file inspection and
`git diff --check` passed.
