# Session 14u — Prepared-row equivalence repair and resumed warning diagnosis

Date: 2026-09-11
Status: **CLOSED — B / repair readiness 1**

## Decision

**B — PIECEWISE VERIFIER CONTRACT TOO STRICT / NUMERICALLY FRAGILE.** The
strict prepared-row byte gate passed, and the preserved Session 14R warning was
reproduced on the originally authorized state and edge. The unchanged joint
Simpson production estimator converged, remained finite and repeated exactly.
The independent maximum methods agreed closely, but SciPy warned while applying
the strict `1e-13` adaptive demand to an extremely narrow positive-width piece
ending at a directional onset.

**Repair readiness 1 — READY FOR BOUNDED VERIFIER-CONTRACT REPAIR.** The
evidence supports changing only how the independent verifier treats a warning
on a numerically negligible partition after every existing independent agreement,
continuity, partition and production check passes. No field, partition,
production estimator or scientific result is repaired here.

## Equivalence-gate result

The repair compares the UTF-8 bytes produced by the exact historical expression
`json.dumps(row, sort_keys=True, allow_nan=False) + "\n"` with the preserved
Session 14R prepared line. It performs no tuple/list normalization, scalar
coercion, sequence reordering or tolerance comparison.

The ordinal-1 reconstruction and preserved line both had SHA-256
`4e896a6174ea54902a9eeeff813951d49fd53299273a3f6b63a30744edd5a52b`.
The regression confirms that tuple/list Python equality is false while exact
historical-byte equality passes. Numeric, sequence-order, missing-field,
signed-zero and scalar changes all fail the gate. The canonical projection,
prepared population and historical serialization remain unchanged.

## Warning diagnosis

The first reproduced warning occurred for the `constant_width` maximum field on
zero-based receiver ordinal 7 of neutral state
`development_01_state_000002`. This is the same ordinal-1 authority selected by
the Session 14R `states_completed=1` failure record. The warning stage was
`strict_piecewise_maximum`:

> Extremely bad integrand behavior occurs at some points of the integration interval.

The edge had 11 defenders, seven onset points, one envelope switch, no tie
intervals, no certified enclosure endpoints and 12 integration pieces. Normalized
piece widths had minimum `3.3306690738754696e-15`, median
`0.029108729827679147` and maximum `0.4435386821485226`. The problematic piece
was index 5, from `0.8938785182578289` to `0.8938785182578323`, with the minimum
width. It was not an adjacent-float interval. Its upper boundary was an onset;
neither endpoint was a switch or tie-enclosure boundary.

Strict quadrature used `epsabs=epsrel=1e-13`, `limit=1000`. On the warning piece
it returned estimate `5.427883770296851e-22`, error estimate
`7.809892280742993e-36`, 63 evaluations and two subdivisions, while retaining
the warning. The same warning occurred on two pieces at both the strict and
`1e-11` repeat settings. Onset-only unsplit adaptive integration emitted no
warning.

The audited independent oracle passed with maximum error
`1.7470054537119944e-21`; the maximum remained continuous around the problematic
boundaries. The largest two-sided finite-step change was
`9.846758011831241e-21`. Slopes were not used as continuity evidence. Partition
construction was valid.

Joint Simpson converged at 2,048 intervals with maximum component change
`2.342180060316279e-08`; its maximum estimate was
`0.023058286606118288`. The approved independent estimates were:

- strict piecewise adaptive: `0.02305829620702085`;
- repeated piecewise adaptive: `0.02305829620702085`;
- onset-only unsplit adaptive: `0.02305829620701374`;
- direct 65,536-interval Simpson: `0.023058296206996908`;
- switch-split Simpson 32,768: `0.02305829620702171`;
- switch-split Simpson 65,536: `0.023058296207020903`.

The largest difference among those independent methods was
`2.394265341543189e-14`. The accepted joint-Simpson maximum differed from strict
piecewise by `9.600902562550973e-09`, well inside its inherited `1e-6`
independent-maximum verification bound. Warning emission therefore did not
demonstrate inaccurate maximum integration or production nonconvergence.

## Thirty-one-item handoff

1. **Starting HEAD:** `ed411671920163ec302f3a8cb92a19b8f42ba576`.
2. **Ending HEAD:** recorded by the closure commit and synchronized verification.
3. **Protocol:** `docs/protocols/phase_14u_equivalence_gate_repair.md`, committed
   as `8d32121`; SHA-256
   `d53b0ec2e01b0afa012a1124256ef6a1486039624d449a815cd10b73e5fddb8e`.
4. **Repaired rule:** exact UTF-8 equality at the historical sorted-JSON line
   layer.
5. **Tuple/list regression:** Python equality false; historical bytes identical;
   repaired gate passed.
6. **Ordinal-1 authority:** exact byte equality passed with matching
   `4e896a…a52b` line hashes.
7. **Historical authority:** Session 14R code, failure, prepared population and
   outputs remained unchanged.
8. **Failing edge:** stable alias `development_01`, neutral state 000002,
   `constant_width`, receiver ordinal 7, maximum combination.
9. **Warning:** SciPy `IntegrationWarning` with the preserved exact message shown
   above.
10. **Verifier stage:** strict piecewise maximum adaptive quadrature.
11. **Joint Simpson:** finite, deterministic, converged at 2,048 intervals under
    the all-component `1e-7` rule.
12. **Partition count:** 12 positive-width pieces.
13. **Switch/tie counts:** one switch, zero tie intervals, zero certified
    enclosure endpoints.
14. **Piece widths:** min `3.3306690738754696e-15`, median
    `0.029108729827679147`, max `0.4435386821485226`.
15. **Problematic piece:** index 5; width `3.3306690738754696e-15`; ends at an
    onset and is not adjacent-float.
16. **Continuity:** analytical obligation and independent oracle passed;
    partition valid.
17. **Piecewise estimate:** `0.02305829620702085`.
18. **Unsplit adaptive estimate:** `0.02305829620701374`, with no warning.
19. **Direct Simpson estimate:** `0.023058296206996908`.
20. **Switch-split estimates:** `0.02305829620702171` at 32,768 and
    `0.023058296207020903` at 65,536 nominal spacing.
21. **Maximum disagreement:** `2.394265341543189e-14` among independent methods;
    `9.600902562550973e-09` including accepted joint Simpson versus piecewise.
22. **Mechanism:** strict adaptive verification over a valid but extremely narrow
    onset-adjacent partition emits a warning despite mutually agreeing estimates.
23. **Classification:** B — piecewise verifier contract too strict/numerically
    fragile.
24. **Repair readiness:** 1 — bounded verifier-contract repair.
25. **Bounded repair:** make warning acceptance conditional on all existing
    partition, continuity, strict/repeat, unsplit, direct, split-Simpson and
    production-joint agreement gates; retain the warning as a diagnostic.
26. **State scope:** exactly the authorized ordinal-1 state; no other state.
27. **Scientific scope:** no Session 14R partial scientific result was opened or
    interpreted.
28. **Access scope:** no targets, outcomes, models, shares, provider products,
    protected/reserved/withheld data, pose, xT or progression material.
29. **Verification:** focused, relevant and full-suite counts plus compilation,
    schema/hash, privacy, link, history, staged, diff and CI results are recorded
    at closure. Focused Session 14u tests ran 8/8; relevant Session 14R/14s/14t
    tests ran 49/49; the full suite ran 462 tests with 459 passes and three
    retained scaffold skips.
30. **Delivery:** three commits were reviewed and pushed; local, tracking and live
    heads and the release tag were verified after CI.
31. **Recommendation:** separately govern the bounded independent-verifier
    warning-contract repair described below; do not resume Session 14R yet.

## Exact repair boundary and sole next action

The separately governed repair should affect only the independent maximum
warning gate. A warning may cease to be automatically fatal only when the
partition is certified and positive-width, the independent continuity oracle
passes, strict and repeated piecewise estimates meet `1e-10`, onset-only adaptive
meets `1e-10`, direct Simpson meets `1e-9`, inherited split-Simpson checks pass,
and the accepted joint maximum meets `1e-6`. Every other warning or failed gate
must remain blocking. Regression fixtures must include this exact narrow-onset
topology, a warning with disagreeing estimators, invalid partitions and production
nonconvergence.

The one recommended next governed action is to implement and synthetically audit
that bounded independent-verifier warning contract. Session 14R remains paused.
