# Session 14ap — Terminal subdivision and error-evidence review

Date: 2026-09-14. **G — invalid / readiness 4**.

The single retained-evidence review ran without numerical evaluation or empirical
access. It verified 68 Session 14ao records and provisionally reduced them to a
C finding: the retained integrator termination reports roundoff preventing the
requested tolerance, while the returned estimates are stable. Inspection after
output exposure found an implementation defect in the public level table: all
six rows contain the final `2e-15` tolerance instead of the frozen six-level
sequence. The publication checker recomputed the same defective rows and therefore
returned true. Under the prospective precedence rule, this is an execution and
evidence-integrity failure. The provisional C/readiness 2 package is retained as
invalid evidence and is not repaired, regenerated or rerun.

The underlying Session 14ao records remain unchanged and hash-valid. Their
bounded review observations below explain what the failed reviewer saw, but they
are not a valid completed Session 14ap classification.

## Retained observations

Five historical completed-level estimates and a reviewer-derived sum of all nine
warning-level returned piece estimates were available. Exact values remain private
and hash-bound. At the retained-value layer all six aggregates were exactly equal.
The reported aggregate error also remained exactly unchanged. Every level retained
189 callback evaluations, nine terminal intervals and zero subdivision operations.
The callback-node sequences, callback values, per-piece trace hashes, ordered
piece-hash sequences, terminal arrays and level trace hashes were identical across
all adjacent levels.

The warning arose on sanitized terminal interval ordinal 8. It contributed about
36.67% of the retained estimated error; the top three intervals contributed about
86.38%. All nine terminal intervals shared an endpoint with a retained canonical
onset. Exact interval widths, coordinates, errors and estimates remain private.
There was no intra-onset-piece subdivision, no subdivision-limit exhaustion and
no retained switch-adjacency record. Rejected-panel history and intermediate
global estimates were never retained.

The exact retained warning is SciPy `IntegrationWarning`: “The occurrence of
roundoff error is detected, which prevents the requested tolerance from being
achieved. The error may be underestimated.” The wording matches the locked SciPy
1.18.1 source. It establishes the integrator's reported termination condition;
it is not an independent bound on the true error. The warning-level reported
error failed its request, and every aggregate remained outside the retained
reference-agreement gate despite estimate stability. Consequently, valid evidence
would still need to separate estimate stability, reported-error behavior and
successful verifier certification.

## Numbered handoff

1. **Starting HEAD:** `fba26be949b7cbe3ded168222b3a9f8e9ccbddfb`.
2. **Ending HEAD:** the closure commit containing this report; its exact identifier
   and synchronization status are supplied in the delivery response.
3. **Protocol:** [Phase 14ap](protocols/phase_14ap_terminal_error_evidence_review.md),
   commit `d6b7af5`, SHA-256
   `102919c0b60db48961bfa43a14660b784a29193b1f35d6471eee9495feeba633`.
4. **Retained sources:** Session 14ao manifest
   `367cec3ea22163af15c299b96e3792424707603b5920257eed40b3e06e5335f3`,
   private index
   `23b4264f0bce761cc17cb61357cd1fd39b6a418e5bce9938314898f8025d3955`,
   and the exact 68-record selection mapping
   `66061ced1444c9e818263d6ed4651a281eb53bfa1c9fd857e9e966958e4a5d2a`.
5. **Completed estimates:** all five were available and exactly identical; their
   values remain private under the frozen boundary.
6. **Warning-level estimate:** no historical aggregate was returned. All nine
   piece estimates were available and their reviewer-derived `math.fsum` matched
   the completed plateau exactly; the value remains private.
7. **Estimate differences:** all retained adjacent aggregate comparisons were
   exactly equal; exact numerical differences remain private.
8. **Error-estimate behavior:** exact plateau across all six retained records;
   values and differences remain private.
9. **Identical traces:** direct equality covered ordered callback nodes and values,
   per-piece hashes, ordered piece-hash sequences, terminal arrays and level hashes.
10. **Final successful subdivisions:** zero operations; nine active intervals.
11. **Warning-level subdivisions:** zero operations; nine active intervals.
12. **Piece widths:** min/median/max were available but remain private; their
   retained-vector SHA-256 is
   `5c16cec759c4ad758891044b4c2cd655fb016f2fa177d7be65efc09a6955a546`.
13. **Dominant local-error region:** sanitized interval ordinal 8 at every level.
14. **Dominant error shares:** top interval about 36.67%; top three about 86.38%.
15. **Warning:** `IntegrationWarning` with the exact generic message quoted above.
16. **Documented semantics:** locked SciPy reports detected roundoff prevented the
    requested tolerance and the reported error may be underestimated.
17. **Estimate stability:** retained values appear exactly stable under the
    requests made; this does not establish accuracy.
18. **Certification:** failed both the warning-free condition and retained
    reference-agreement condition.
19. **Roundoff/subdivision evidence:** an explicit roundoff termination report,
    no subdivision operations, and no exhaustion of the limit. True error,
    cancellation, local nonsmoothness and machine-scale refinement remain unproved.
20. **Missing numerical evidence:** one independently bounded reference for the
    sanitized warning-producing terminal interval. This was not acquired.
21. **Classification:** G, because the public tolerance sequence is materially
    wrong and the checker shares the defect. The provisional C is not accepted.
22. **Readiness:** 4. No verifier or numerical repair authority was earned.
23. **One recommendation:** separately govern a bounded reviewer-integrity repair
    that fixes per-level tolerance serialization and validates public rows against
    the frozen protocol independently; do not rerun numerical integration.
24. **New numerical computation:** none. Only standard-library arithmetic over
    retained returned values was attempted.
25. **Additional empirical access:** none; `empirical_records_opened=0`.
26. **Scientific interpretation:** none. No Session 14R partial products, targets,
    models, shares or other geometry were opened.
27. **Validation:** focused 33/33 and relevant 65/65 passed before exposure;
    compilation passed. The full suite passed 866 run / 863 passed / 3 retained
    skips. Remaining delivery checks and CI are reported after completion. These
    checks cannot rehabilitate the invalid execution.
28. **Commits/push:** protocol `d6b7af5`, tested tooling `bb1df5d`, and this closure
    commit, exactly three. Push/CI/synchronization are delivery checks only.

## Integrity and preservation

The emitted seven-file package under
`outputs/continuous_occlusion_terminal_error_review/` is preserved byte-for-byte.
Its `qc.json` says C/readiness 2 and its publication checker returns true; both are
explicitly rejected by this later closure because the visible tolerance column is
wrong. The retained package is evidence of the failed execution, not accepted
scientific or numerical authority. Exact private values remain ignored and bound
by private-index SHA-256
`b55cb44e1994a4a10cb5e8e8e268400d02f1c09d3ff94d89aeea39e4b0f63670`.

Session 14ao, the claim ledger, README, dependencies, public API and release are
unchanged. Accessibility remains **PROXY ONLY** and suppression remains
**NOT SUPPORTABLE**. No causal, attribution, value or behavioral claim follows.
