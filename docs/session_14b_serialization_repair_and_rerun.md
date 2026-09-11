# Session 14b serialization repair and exact synthetic rerun

## Result

**Execution:** VALID

**Numerical classification:** **F — UNRESOLVED**

**Retry readiness:** **4 — NOT READY / ABANDON CANDIDATE**

The serialization-only repair worked and the exact Session 14a synthetic review
closed successfully. The same four maximum-envelope references remained
unavailable under the unchanged fine-grid agreement rule. That prevents the
complete reference-backed conclusion required by Phase 14a and selects F under
the frozen decision logic. “Not ready” is the operative interpretation of
readiness 4; this review does not independently establish that every continuous
field candidate must be permanently abandoned.

Session 14 remains historically **D — BLOCKED**, readiness 3. Session 14a remains
historically **F — UNRESOLVED**, readiness 2 after its serialization failure.
Neither result was rewritten or replaced.

## Authority and repair

The clean starting `HEAD`, local tracking branch and live GitHub `main` were
`d7151243ec10ea2d455977c5432d0dcc74f33dea`. Annotated `v0.1.0` remained at
`f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`.

The [Phase 14b protocol](protocols/phase_14b_serialization_repair_and_rerun.md)
was committed at `aa12115` before implementation. The tested repair was committed
at `2e2adc8` before the rerun.

The defect was confined to JSON output: a nested `np.bool_` reached
`json.dumps`, which does not treat it as a native Python boolean. The new internal
normalizer recursively converts NumPy booleans, integers and floating scalars to
native `bool`, `int` and `float`; preserves ordinary values and `None`; converts
tuples to JSON arrays; rejects nonfinite and unsupported values; and leaves the
underlying arrays and numerical calculations unchanged. Sorted-key,
newline-terminated deterministic JSON remains the output contract.

The Session 14b runner's numerical `review`, diagnostic and component-evaluation
bodies were tested as structurally identical to Session 14a. A separate
output-validation correction permits governed unavailable references only when
their count matches QC and the classification is F. It does not change reference
availability.

## Exact reproduction and integrator checks

The historical `lateral_x5_y1` expanding individual field reproduced exactly:

- 80 intervals: `0.5423405961267106`;
- 160 intervals: `0.5424947427905844`;
- absolute difference: `0.00015414666387381093`.

All 32 production Simpson polynomial oracles passed with maximum absolute error
`0.0`. Constant, linear, quadratic and cubic functions were checked across
`16,32,64,128,256,512,1024,2048` intervals. The Simpson implementation is
correct for its frozen uniform-domain contract.

The complete rerun produced 2,928 convergence rows for 36 fixtures, three
candidates and 366 individual/union/maximum components. The Session 14b
convergence file is byte-identical to the retained Session 14a table, confirming
that serialization repair did not alter the numerical calculations.

## Reference availability and convergence

References used locked SciPy `1.18.1` scalar `integrate.quad` with
`epsabs=epsrel=1e-13`, `limit=1000`, analytical directional onset breakpoints,
and an independent `1e-11` run. Simpson cross-checks used
`4096,8192,16384,32768,65536` intervals.

Of 366 component references, 362 were available. The same four maximum-envelope
references remained unavailable, each solely because the 32,768-to-65,536
Simpson change exceeded the frozen `1e-10` rule:

- `equal_minimum_three`, expanding maximum;
- `equal_minimum_three`, constant-width maximum;
- `star_edge_1`, expanding maximum;
- `star_edge_3`, expanding maximum.

Their strict and repeated adaptive estimates agreed closely, and the finest-grid
values remained within the separate `1e-9` adaptive/fine bound. Those facts do
not override the prospectively frozen fine-grid agreement requirement.

For available components, maximum absolute reference error at 2,048 intervals
was:

- isotropic: `1.2155761397458775e-09` across 122 references;
- expanding: `2.4338563386905321e-08` across 119 references;
- constant-width: `2.4338563386905321e-08` across 121 references.

Across available components, the maximum 160-interval reference error was
`2.308164949507696e-05`. For the historical failing component specifically, the
planning and closed diagnostics give a 160-interval error of
`1.1295819455581224e-05`; its 2,048-interval error was
`7.57481488644629e-09`.

## Numerical-behavior interpretation

The expanding field is continuous and C1 at its smoothstep activation
boundaries; higher derivatives change at the piece boundaries. For the failing
fixture those boundaries occur at normalized edge positions `0.26` and
`0.31099019513592785`, an onset interval about `0.0509901951` wide. Whole-edge
uniform Simpson sampling can therefore converge unevenly when piece boundaries
fall between nodes. No value discontinuity, singularity or Simpson misuse was
found.

Maximum combination adds envelope switches between defender fields. Those kinks
explain why selected maximum summaries are more demanding for a whole-grid
cross-check, but the frozen review does not establish a complete alternative
reference contract.

The governed verdict on the historical `1e-6` gate is **poorly specified**.
Successive-estimate disagreement is not actual reference error. In the failing
case the gate was conservative, while the 160-interval estimate was also less
accurate than `1e-6`; thus the gate caught an inaccurate estimate without being
a well-designed direct error measure. This review does not establish `1e-6` as
the correct tolerance for future work.

The generated method summary records a prospective controlled-Simpson candidate:
start at 256 intervals, double until every component changes by at most `1e-7`,
cap at 16,384, and fail closed. It showed maximum reference error
`2.8987435979344056e-08` among available references. Because four mandatory
references were unavailable, this report does **not** adopt that candidate as a
supported future integration contract.

The complete review took approximately `28.9054` seconds in the locked local
environment. This establishes practical synthetic execution only; it is not an
empirical-scale performance claim.

## Required 25-item handoff

1. **Starting HEAD:** `d7151243ec10ea2d455977c5432d0dcc74f33dea`.
2. **Ending HEAD:** the closure commit containing this report; exact ID in the
   final handoff.
3. **Protocol:** Phase 14b, commit `aa12115`; SHA-256 in the manifest.
4. **Repair:** recursive NumPy-to-native scalar normalization at JSON output.
5. **Regression tests:** nested type/value round trips and rejection cases pass.
6. **Historical reproduction:** exact values and difference reproduced.
7. **Resolution ladder:** completed for all 36 fixtures and three candidates.
8. **References:** 362 available, 4 unavailable.
9. **Isotropic maximum error:** `1.2155761397458775e-09` at 2,048 intervals.
10. **Expanding maximum error:** `2.4338563386905321e-08` among available
    references at 2,048 intervals.
11. **Constant-width maximum error:** `2.4338563386905321e-08` among available
    references at 2,048 intervals.
12. **Previously unavailable references:** all four remain unavailable solely
    under the frozen fine-grid-delta rule.
13. **Simpson verdict:** implementation correct; 32/32 polynomial oracles exact.
14. **Field behavior:** continuous and C1; piece boundaries and maximum-envelope
    switches create slower or uneven uniform-grid convergence.
15. **Historical gate:** poorly specified, although it blocked an inaccurate
    historical fine estimate.
16. **Classification:** **F — UNRESOLVED**.
17. **Retry readiness:** **4 — NOT READY / ABANDON CANDIDATE**.
18. **Future contract:** none supported; the generated controlled-refinement
    candidate remains unapproved.
19. **Cost:** approximately 28.9054 seconds for the synthetic review.
20. **Session 14:** remains historically D/readiness 3.
21. **Access:** no empirical data or models accessed.
22. **Claims:** claim ledger unchanged; no validated occlusion, cover shadow,
    suppression, interception probability or defensive value.
23. **Checks:** 35 focused tests passed with no skips; the full active suite ran
    324 tests, with 321 passed and 3 retained skips. Compilation, numerical
    reference validation, output hashes, publication/privacy checks,
    documentation links, history preservation and diff checks passed.
24. **Commits/push:** protocol `aa12115`, repair `2e2adc8`, closure commit and
    synchronization recorded in the final handoff.
25. **One next action:** a separately governed synthetic reference-contract
    review focused on maximum envelopes and their switching points. It must
    resolve reference availability before any Session 14 empirical retry.

## Outputs and boundaries

The closed package is under
`outputs/continuous_occlusion_numerics_14b/`. Its manifest SHA-256 is
`8858b4bfd2717dae1d250e1647742cc467813170cd2bba9c5b47d407de0990a3`.
All six requested artifacts exist and pass their publication checker.

No canonical development state, target, model, coefficient, utility, option
share, provider product, reserved or withheld material, pose, external xT or
progression record was opened. No candidate formula, scientific claim, package
version, dependency, historical output or release tag changed. No Session 14
empirical retry occurred.
