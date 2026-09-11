# Session 14a synthetic numerical integration review

## Result

**Execution status:** INVALID AFTER SYNTHETIC OUTPUT EXPOSURE

**Numerical classification:** **F — UNRESOLVED**

**Retry readiness:** **2 — READY AFTER SMALL IMPLEMENTATION REPAIR**

Session 14a reproduced the historical Session 14 failure and completed the
frozen numerical matrix in memory, but failed while serializing the reference
summary. A NumPy boolean reached the standard-library JSON encoder and raised
`TypeError: Object of type bool is not JSON serializable`. The convergence CSV
had already been written, so the protocol's post-exposure stop rule applies.
The implementation was not repaired and the review was not rerun.

Session 14 remains historically closed as **D — BLOCKED**, readiness 3. No
candidate was selected and no empirical Session 14 work was reopened.

## Authority and chronology

1. Starting `HEAD`, local `origin/main`, and live GitHub `main` were all
   `2a2ebe571aa85c0c850dc4139ebcd01350856dae`.
2. Annotated `v0.1.0` still peeled to
   `f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`.
3. Protocol commit: `906b1a2`.
4. Initial implementation commit: `f23e35d`.
5. Its first preflight exposed a self-referential source guard before review or
   numerical output. The syntax-tree correction was committed at `f449ab0`.
6. The one governed review began from `f449ab0` and was not rerun.

Protocol: [Phase 14a](protocols/phase_14a_synthetic_numerical_integration_review.md).
Its SHA-256 is recorded in the failure-closure manifest. The manifest SHA-256
is `4581de83a6d5bec7c39418578b5ea80e2eed26d0739804f69cc93195666a2859`.

## Numerical evidence retained

The historical `lateral_x5_y1` expanding individual-field calculation passed
the exact reproduction gate in the locked environment:

- 80 intervals: `0.5423405961267106`;
- 160 intervals: `0.5424947427905844`;
- absolute difference: `0.00015414666387381093`.

The production Simpson helper passed all 32 frozen polynomial checks across the
eight ordinary resolutions: constant, linear, quadratic and cubic integrals
were exact within `32 × float64 epsilon`. Interval parity, endpoint weighting,
normalization and float64 behavior were also covered by the focused tests.

The preserved [convergence table](../outputs/continuous_occlusion_numerics/convergence.csv)
contains 2,928 rows over all 36 Session 14 fixtures, all three candidates and
366 component references. It covers the frozen interval ladder
`16,32,64,128,256,512,1024,2048`. The table's SHA-256 is
`fab91419fca9731430baef5f372c6e7eb30e1291b1e06d636520e09b91fff49f`.

For the historical failing component, absolute error against the adaptive
reference recorded in the table fell from `0.012612545191396873` at 16 intervals
to `7.57481488644629e-09` at 2,048. At 256 intervals it was
`1.0400930554599341e-06`; at 512 it was `5.628486395847787e-07`; at 1,024 it was
`4.799040742575755e-08`. The 160-interval absolute reference error,
`1.1295819455581224e-05`, was seen in the disclosed pre-protocol planning probe,
not retained as a governed convergence row.

Among components whose references passed the frozen availability contract, the
maximum 2,048-interval absolute errors were:

- isotropic: `1.2155761397458775e-09`;
- expanding: `2.4338563386905321e-08`;
- constant-width: `2.4338563386905321e-08`.

Four maximum-envelope references were marked unavailable: the expanding and
constant-width fields for `equal_minimum_three`, and the expanding field for
`star_edge_1` and `star_edge_3`. Their adaptive/fine-grid diagnostic reasons
were held in memory but were not serialized, so the precise failed comparison
is unavailable. This prevents a complete field-wide convergence conclusion.

## Reference method and numerical interpretation

The governed method used locked SciPy `1.18.1` scalar `integrate.quad` with
`epsabs=epsrel=1e-13`, `limit=1000`, analytical directional gate breakpoints,
and a second `1e-11` run. Independent Simpson estimates at
`4096,8192,16384,32768,65536` supplied the cross-check. A reference required
adaptive agreement within `1e-10`, final-grid agreement within `1e-10`, and
fine/adaptive agreement within `1e-9`.

The prior planning probe localized the failing field's directional gate changes
to normalized edge positions `0.26` and `0.31099019513592785`. Formula inspection
shows continuous value and first derivative at the smoothstep boundaries, with
higher derivatives changing across pieces. That can slow whole-interval Simpson
convergence when the breakpoints fall between samples. The governed diagnostic
CSV and continuity summary were not written before the serialization failure,
so this remains qualified mechanism evidence rather than a closed Session 14a
diagnosis.

The original `abs(S80-S160)<=1e-6` rule cannot be given a final governed verdict.
The retained and prior evidence shows that successive-estimate disagreement is
not the same quantity as reference error. In this fixture it was conservative,
but it also correctly blocked a 160-interval estimate whose planning-probe
reference error exceeded `1e-6`. “Poorly specified but directionally protective
in the failed case” is a preliminary observation, not a replacement contract.

No exact future numerical contract is supported because four required
references remained unavailable and the summary failed closure. Fixed higher
resolution, controlled refinement and adaptive quadrature therefore remain
unselected prospective remedies.

The complete matrix and adaptive work reached the serialization stage in about
29 seconds of wall time on the locked local environment. Each edge/candidate
used 131,311 fixed-grid query locations across the ordinary, historical and
fine-grid resolutions, plus adaptive evaluations. This is an engineering cost
observation only.

## Required 23-item handoff

1. **Starting HEAD:** `2a2ebe571aa85c0c850dc4139ebcd01350856dae`.
2. **Ending HEAD:** the closure commit containing this report; its exact hash is
   reported in the final handoff because a commit cannot contain its own ID.
3. **Protocol:** Phase 14a, commit `906b1a2`; hash in the manifest.
4. **Historical discrepancy:** reproduced exactly as listed above.
5. **Integrator oracles:** 32/32 passed before field interpretation.
6. **Reference:** locked SciPy adaptive quadrature plus independent fine grids.
7. **Resolution ladder:** `16` through `2048` by doubling; fine grids through
   `65536`.
8. **Expanding convergence:** demonstrated on retained available components,
   but three expanding maximum references were unavailable.
9. **Isotropic convergence:** all 122 component references available; maximum
   2,048-interval error `1.2155761397458775e-09`.
10. **Constant-width convergence:** retained available components converged;
    one maximum reference was unavailable.
11. **Errors:** retained in the convergence CSV; complete reference summary is
    unavailable.
12. **Failure localization:** planning evidence identifies directional onset
    breakpoints and piecewise higher-derivative changes; governed diagnostic
    closure is unavailable.
13. **Continuity:** analytically continuous and C1 at the smoothstep boundaries;
    the requested closed numerical probe is unavailable.
14. **Original gate:** final verdict unavailable; preliminary evidence calls it
    an indirect and conservative proxy in the historical case.
15. **Classification:** **F — UNRESOLVED**.
16. **Retry readiness:** **2 — READY AFTER SMALL IMPLEMENTATION REPAIR**.
17. **Future contract:** unavailable; selecting one now would exceed the closed
    evidence.
18. **Cost:** approximately 29 seconds through attempted serialization, with
    fixed-grid work described above.
19. **Access:** zero empirical states, targets and models; synthetic inputs only.
20. **Claims:** claim ledger unchanged; no occlusion or cover-shadow validation.
21. **Checks:** 28 focused tests passed with no skips; the full active suite
    passed 317 tests with 3 retained skips. Compilation, documentation links,
    failure-package hashes, publication safety, history preservation and diff
    checks passed. The success-only Session 14a publication command is
    unavailable for this intentionally incomplete package.
22. **Commits/push:** protocol `906b1a2`, implementation `f23e35d`, pre-review
    guard correction `f449ab0`, and the closure commit containing this report;
    push and synchronization are reported in the final handoff.
23. **One next direction:** a separately governed Session 14a implementation
    repair and synthetic rerun that fixes JSON scalar normalization and retains
    the same formulas, fixtures and numerical contract.

## Boundaries and closure

The public failure package contains the generated convergence table plus a QC
record and hash-bound failure manifest. `reference_summary.json`,
`failing_fixture_diagnostic.csv`, and `method_summary.json` are explicitly
unavailable. The empty temporary reference file was retained in ignored local
failure storage. The append-only ignored ledger records start and failure.

No development or protected population, provider product, target, model,
coefficient, utility, option share, reserved or withheld material, pose, xT or
progression data was opened. No formula, historical Session 14 artifact,
release tag or claim status changed. No Session 14 retry or behavioral analysis
occurred.
