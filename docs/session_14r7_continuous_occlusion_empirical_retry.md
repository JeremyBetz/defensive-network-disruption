# Session 14R7 — Continuous occlusion representation retry

## Closed decision

**Scientific D — BLOCKED BEFORE DEVELOPMENT ACCESS. Readiness 3 — representation
implementation requires a bounded aggregation-contract repair.** No empirical
representation comparison occurred and no candidate is selected. This is not
evidence against any field construct.

The R7 numerical adapter passed the complete 108-case / 366-reference /
399-permutation synthetic comparison. Its deterministic 1800×800 visual passed
full-frame review. A subsequent required pre-access aggregation check exposed a
separate inherited defect: pair-summary means use equal state weighting, but
percentiles and extrema are calculated from individual pair indicators rather
than from within-state averages.

For the synthetic oracle, the two states have pair indicators `[0,1]`
and `[1,1]`. The required state averages are `0.5` and `1.0`. Both calculations
produce mean `0.75`, but the inherited median is `1.0` whereas the required
inverse-ECDF median is `0.5`; the inherited minimum is `0` rather than `0.5`.
The R7 collector's syntax tree exactly matches the historical R6 collector.
This is an aggregation-contract mismatch, not a field or integration failure.

The guard rejects this discrepancy before launch. The collector was not repaired,
no new tolerance was introduced, and no empirical retry or additional audit phase
was started. Historical artifacts and implementations remain unchanged.

## Evidence and chronology

1. Protocol commit: `91346ca` froze the scientific specification before numerical
   execution or development access.
2. The initial new wrapper passed nine study tests and twelve enforcement tests;
   its recorded numerical acceptance passed 108/366/399 and machine numerical
   readiness. Synthetic rendering reproduced identical bytes and passed review.
3. The mandatory within-state-first aggregation review then exposed the synthetic
   discrepancy. A launch-blocking regression was added without changing the
   inherited collector. The pre-access zero-history failure path was tested.
4. Tested checkpoint: `9c2ae42dcd6c26df511855b9e6a32b65e1d5a693`, including the
   blocker. The original acceptance record is preserved, not rebound to changed
   wrapper/test bytes. Its exact five source versions can be reconstructed from
   the committed checkpoint using the checked
   [acceptance-source patch](../outputs/continuous_occlusion_retry_14r7/authority/acceptance_source.patch)
   in temporary storage. That reconstruction was verified against all five
   recorded hashes; the patch is never used by production execution.
5. The single failure closure validated actual persisted files and an empty
   journal. No empirical `run` command, authorization callback, population
   preparation, or field evaluation was executed.
6. This report and the append-only research-log entry close the phase. Final
   delivery verifies ordinary CI and synchronization after the closure commit.

The [closed manifest](../outputs/continuous_occlusion_retry_14r7/manifest.json)
has SHA-256 `4cee379c77e9d5dcea11ff5affb4866834ed1abb6e56fa361dac30787860c9cf`.
The [summary-contract evidence](../outputs/continuous_occlusion_retry_14r7/authority/summary_contract.json)
retains expected and observed synthetic statistics and `passed: false`.
Numerical readiness is distinct from overall study authorization; the latter
was never earned. Some inherited console labels still say R6; the R7 namespace,
source hashes, and protocol binding identify the actual execution.

## Forty-two-item handoff

1. **Starting HEAD:** `3bd02c10427bd35d1c45ea1e203c68ccd141bf75`; clean local,
   tracking and live GitHub heads matched before mutation.
2. **Ending HEAD:** the closure commit containing this report; its exact hash and
   live synchronization are reported in final delivery rather than creating a
   self-referential document hash.
3. **Protocol:** [Phase 14R7](protocols/phase_14r7_continuous_occlusion_empirical_retry.md),
   commit `91346ca`, SHA-256
   `51633a23938f7968adbaa83e513a70225d473c87cb1c1bee67e21988981c11ea`.
4. **Launch authority:** unchanged governed launcher, locked project interpreter,
   fixed discoverable prerequisite tests, observed callback-spy enforcement.
   The empirical launcher was not instantiated.
5. **Lifecycle/publication authority:** accepted lifecycle and durable journal
   primitives composed with versioned numerical-event validation. Full-study
   publication rejects diagnostic-only success. The actual zero-access failure
   package passed persisted validation.
6. **Exposure authority:** Session 14ag materialization receipts and unique
   geometric-edge accounting are preserved. Empty persisted history establishes
   zero real exposure; missing counters were not silently treated as zero.
7. **Owner certification:** unchanged Session 14ai structural-region witnesses;
   unsupported coincidence/no-interior-float outcomes remain fail-closed.
8. **Numerical authority:** frozen fields, Simpson ladder, independent maximum
   checks, canonical partitions and bounded-residual intervals are unchanged.
   Degenerate edges retain endpoint behavior. Raw solver provenance remains
   separate; Session 14aa remains historically qualified.
9. **Final-float contract:** exact structure/order/resolution and the unchanged
   finite 64-epsilon comparison; signed-zero bits remain diagnostic.
10. **108/366/399:** all passed through the assembled R7 numerical adapter before
    the separate aggregation blocker was discovered. This does not authorize
    empirical work or turn the failed summary gate into PASS.
11. **Publication/failure gate:** observed controls reject false acceptance,
    mismatched persisted evidence, invalid diagnostic sequencing, unresolved
    exposure, and diagnostic-only scientific closure. The closed pre-access
    package passes publication checking while retaining failure status.
12. **Visual QA:** double-render bytes match, all three equal-aspect panels and
    shared scale are legible, and all four required warnings are visible. No
    empirical image or animation was created.
13. **Population:** expected historical SHA-256
    `cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d`;
    not opened or reverified in R7 because the pre-access gate failed. The
    7,227-state population and nine match counts remain inherited authority.
14. **States discovered/prepared/started/completed:** real execution `0/0/0/0`;
    lifecycle remained uninitialized and the journal is actually empty.
15. **Geometric edges opened/started/completed:** `0/0/0` real edges.
16. **Field evaluations started/completed:** `0/0` empirical calls, separately
    from synthetic acceptance calculations.
17. **Unresolved exposed edges:** zero; unresolved projection attempts also zero.
18. **Empirical numerical failures:** zero; empirical numerical evaluation never
    began. The blocking failure is a pre-access synthetic summary-contract check.
19. **Receiver-distance correspondence:** unavailable; not executed.
20. **Segment-distance correspondence:** unavailable; not executed.
21. **Receiver/corridor ordering:** empirical comparison unavailable. The
    inherited pair aggregation defect must be resolved before these pair-family
    distributions can be accepted.
22. **Equal-minimum stress:** retained synthetic-only acceptance evidence in
    [synthetic stress summary](../outputs/continuous_occlusion_retry_14r7/synthetic_stress_summary.json).
    It supplies no empirical candidate preference.
23. **Union-minus-maximum distribution:** empirical distribution unavailable.
24. **Overlap/redundancy correspondence:** unavailable; not executed.
25. **Multi-edge findings:** no new empirical findings. Session 13 remains the
    historical authority, including its state-average gap percentile semantics.
26. **Isotropic versus expanding:** empirical comparison unavailable.
27. **Isotropic versus constant-width:** empirical comparison unavailable.
28. **Expanding versus constant-width:** empirical comparison unavailable.
29. **Candidate-pair ordering correspondence:** empirical comparison unavailable;
    the synthetic pair aggregation regression is a prerequisite failure.
30. **All-nine-match consistency:** not assessed; no match geometry was opened.
31. **Scientific classification:** D, blocked before access. Numerical acceptance
    and the synthetic picture alone cannot support scientific A, B or C.
32. **Readiness:** 3. A bounded aggregation repair is needed before reconsidering
    a representation execution; no behavioral readiness is asserted.
33. **Selected candidate/specification:** none; no field is frozen for behavior.
34. **Claim ledger:** byte-identical; no promotion. Accessibility remains
    **PROXY ONLY** and suppression remains **NOT SUPPORTABLE**.
35. **Targets/ranks/models/shares:** none accessed. Synthetic projection sentinels
    and explicit geometry tests do not authorize empirical labels.
36. **Reserved/withheld/pose:** none accessed. Formerly reserved matches remain
    spent; withheld and pose evidence remain protected under existing authority.
37. **Tests:** see the observed validation record below; counts distinguish run,
    passed, and retained skips. A passing blocker-regression test verifies denial
    of access, not correctness of the inherited summary calculation.
38. **Python 3.11 CI:** final delivery gate; report the actual closure run result.
39. **Python 3.13 CI:** final delivery gate; report the actual closure run result.
40. **Distribution CI:** final delivery gate; no version, release, dependency or
    package-metadata change. Successful CI cannot override the scientific blocker.
41. **Commits/push:** protocol and tested checkpoint above; this report belongs
    to the third closure commit. Final delivery verifies synchronized heads and
    the unchanged annotated tag target
    `f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`.
42. **Exactly one recommendation:** separately govern a bounded repair of
    within-state pair-summary aggregation and its percentile regression contract
    before authorizing another empirical representation retry. Do not execute
    that repair as part of R7.

## Preservation and availability

The thirteen-name output contract is retained: six files exist, including the
manifest, and seven incomplete scientific files are explicitly unavailable.
Pre-access authority stays separate. Private execution evidence, source-stage
records and failure traceback remain ignored. No scientific partial products
exist for R7. Publication checking validates existing hashes and persisted
records without rebinding them.

The field and integration implementations, historical outputs, README, claim
ledger, dependencies, released API, and release tag remain unchanged. R7 retains
carrier-position proxy uncertainty, shared geometry, fixed scales, persistent
directional tails, union saturation, finite-grid switching limitations, offline
tracking, and the spent status of development/formerly reserved evidence. No
causality, attribution, pass success, interception probability, defensive value,
player ranking, tactical intent, best-pass or validated-cover-shadow claim is
made.

## Observed validation

- Initial full suite: **697 run / 694 passed / 3 retained skips**, 1,208.926 seconds.
- Post-blocker full suite: **698 run / 695 passed / 3 retained skips**, 1,215.493 seconds.
- Relevant Session 13/14 subset of the latter run: **416 run / 416 passed / 0 skipped**.
- Focused enforcement: **13 run / 13 passed / 0 skipped**. This includes the
  empty-history failure oracle added after the post-blocker full suite collected
  its tests. The ordinary CI suite collects the complete final test set.
- Initial focused study: **9 run / 9 passed / 0 skipped**; the later blocker
  regression separately ran **1 / 1 / 0** and is included in the post-blocker full suite.
  Counts above describe separate runs and must not be summed as unique tests.
- The three skips are the retained historical contract placeholders. No new skip
  hides an R7 failure. An early enforcement run exposed a temporary-directory
  symlink in the new synthetic fixtures; resolving those fixture paths corrected
  that setup error before recorded acceptance. Historical code was unchanged.
- Compilation, 93 historical bindings, exact source reconstruction, new public
  artifact privacy scans, local links, append-only preservation, persisted
  publication/hash checks, staged inspection and whitespace checks passed.
- Private validation record SHA-256:
  `e3fa46a0acc28471f518fb5403e99ae0ebdb8eb72a25b9b0b93831dd1d9b795b`. Detailed test logs remain ignored.
- Checkpoint CI is [run 34768860748](https://github.com/JeremyBetz/defensive-network-disruption/actions/runs/34768860748).
  Distribution passed at report preparation; both Python jobs were still running.
  Final delivery verifies all three jobs for the closure commit and records their
  actual result. No pending CI status is represented here as a completed PASS.
