# Session 14i — Signature repair and production-wiring acceptance

## Decision

**PASS — PRODUCTION VERIFICATION WIRING ACCEPTED; SESSION 14R MAY RESUME.**
The minimal `mapped_signature()` repair removed the heterogeneous
`None`/tuple ordering failure, preserved the returned signature records and
numerical results, and allowed the one governed synthetic audit to complete.
This is verification authority only. It does not validate an occlusion or
cover-shadow construct, and Session 14R was not executed.

## Authority and chronology

1. The actual clean synchronized starting authority was
   `79fade89cf28d09a981d1953680c49b4fcfeccf1`; the handoff's earlier expected
   commit was retained as an ancestor rather than restored over the completed
   public-repository audit.
2. Annotated release `v0.1.0` remained at
   `f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`.
3. The [prospective protocol](protocols/phase_14i_signature_repair_and_acceptance.md)
   was committed as `ff9c51344ac57a6c949b1fd54f2e102fea96b0c2`.
4. The tested repair and isolated runner were committed as
   `23a432aadcb2947c8725195966abfa4df9f9b832` before governed execution.
5. Exactly one governed `audit` execution followed a successful preflight. Its
   exclusive marker remains in ignored local storage; no audit rerun occurred.

## Repair and retained semantics

6. Session 14h's localized defect was exact: Python attempted to sort a mapped
   endpoint boundary represented by `None` alongside a certified numeric
   boundary represented by a tuple.
7. The repair supplies a private tagged total-order key: left endpoint, numeric
   boundary, then right endpoint. Returned endpoint fields remain `None`.
8. Nested defender ordinals are still mapped through the inverse permutation
   and numerically sorted. Merged multiway-boundary witness pairs are normalized
   to the first pair from the already retained complete mapped pair set, removing
   a non-semantic input-order artifact without changing detector evidence.
9. Field formulas, scales, switch and certification rules, integration ladders,
   tolerances, references, dependencies, released APIs and package version did
   not change.
10. Regression tests reconstructed the historical `TypeError`, then covered
    left/right/both endpoint forms, isolated and multiple ties, exact and rounded
    plateaus, and all 24 multiway-plateau permutations.

## Governed synthetic evidence

11. All **108 of 108** frozen fixture/candidate maximum cases completed.
12. All **366 of 366** component references were available and passed the
    inherited `1e-6` error bound; maximum absolute error was
    `4.1576548232002963e-08`.
13. Controlled joint Simpson accepted 176 components at 512 intervals, 48 at
    1,024, 96 at 2,048, 36 at 4,096 and 10 at 8,192; none reached the 16,384 cap.
14. All **399 of 399** required fixture permutation comparisons passed.
15. Six engineering fixtures passed, including exact and rounded plateaus and
    the formerly failing multiway plateau. Certified partitions were consumed
    by independent maximum verification while joint Simpson remained unchanged.
16. The valid pipeline control produced one accepted result. All eleven negative
    cases—continuity, discontinuous surrogate, failed root, malformed
    certification, nonconvergence, permutation mismatch, nondeterminism,
    numerical warning, missing reference, integrity failure and marker
    collision—blocked accepted output.
17. Every input to the immutable `VerificationReadiness` conjunction is true;
    its derived `ready` value is true. No report-level override exists.
18. The closed [manifest](../outputs/continuous_occlusion_production_acceptance/manifest.json)
    has SHA-256
    `1c65769260cc6e1b8a79b69129b3b5a227d4a0a41aec93be4533168a042ace88`.

## Interpretation and boundaries

19. Session 14g remains historically **INVALID** and Session 14h remains the
    historical localization authority. Their output bytes and conclusions were
    not rewritten.
20. PASS establishes that the repaired synthetic production-verification route
    is internally accepted under its frozen fixture-scoped contract. The finite
    switch grid still does not prove detection of every mathematically possible
    crossing between grid nodes.
21. The evidence is wholly synthetic. No empirical population, provider product,
    target, model, utility, option share, protected/withheld/pose record, xT or
    progression material was accessed.
22. The claim ledger is unchanged. Accessibility remains **PROXY ONLY** and
    suppression remains **NOT SUPPORTABLE**; causal, interception, attribution
    and defender-value claims remain unsupported.
23. Dense numerical traces, full failure records and execution markers remain
    ignored. Public files contain only synthetic aggregate evidence and bound
    hashes.

## Verification and delivery

24. Focused, relevant, full-suite, compilation, schema/hash, publication/privacy,
    documentation-link, append-only-history, staged-content and diff checks were
    run before closure. Exact observed test totals and CI state are recorded in
    the delivery handoff rather than predicted here.
25. The completed public-repository audit requested ahead of Session 14R was
    already authority at this phase's starting commit; Session 14i preserved it.
26. The single next governed action is **resume Session 14R protocol planning
    under the accepted production-verification contract**. This report does not
    authorize or execute Session 14R itself.
