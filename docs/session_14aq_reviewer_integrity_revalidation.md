# Session 14aq — Reviewer-integrity repair and retained-evidence revalidation

Date: 2026-09-14. **C — roundoff/subdivision limitation identified / readiness 2**.

Session 14aq repaired the isolated Session 14ap public-row defect without
changing or rerunning the underlying numerical experiment. The new package
contains the correct six requested tolerances, and a separately implemented
validator derived expected rows directly from the retained Session 14ao records.
It rejected the historical all-`2e-15` corruption and every frozen row-corruption
oracle before accepting the persisted package.

The corrected evidence supports a bounded C conclusion. Five historically
completed aggregates and the distinctly labeled reviewer-derived sum of the
warning level's nine returned pieces are exactly stable across the retained
requests. Reported aggregate errors also plateau. Every level contains 189
callback evaluations, nine terminal intervals and zero subdivision operations;
callback nodes and values, per-piece trace hashes, ordered piece-hash sequences,
terminal arrays, subdivision topology and level trace hashes are identical.
Exact estimates, errors, differences, widths, coordinates and traces remain
private and hash-bound.

The sixth retained request reports SciPy `IntegrationWarning`: “The occurrence
of roundoff error is detected, which prevents the requested tolerance from being
achieved. The error may be underestimated.” This matches the locked SciPy 1.18.1
source. It identifies the integrator's reported roundoff termination condition;
it does not independently prove true error or accuracy. The warning-free and
reference-agreement conditions remain unsatisfied.

## Historical defect and repair

The defect was in `review_records` in
`src/defensive_network_disruption/validation/terminal_error_review.py`. Its first
validation loop bound `tolerance`; its later public-row loop omitted that value
from its `zip` and serialized the ambient variable. The final loop value,
`2e-15`, was copied into all six Session 14ap rows. Six tolerance cells used the
wrong derivation; five displayed a wrong number, while the sixth coincidentally
matched its true request. No broader corruption is inferred.

The Session 14aq reviewer maps each retained level's own `level["tolerance"]`
into its row. The validator is a separate module and does not import the reviewer
or call its row/public-package helpers. It maps raw retained levels and pieces
directly to the frozen schema, then checks persisted files and hashes.

The historical-defect oracle was rejected on rows 0–4. Swapped and duplicated
tolerances, a missing level, shifted numbering, an incorrect warning row, stale
estimate and error fields, and a malformed unavailable marker were also rejected
with localized failures. The accepted control validated all six rows.

## Numbered handoff

1. **Starting HEAD:** `2f3d9d4099a4c057d68c20a3231cc8a5e64c4d97`.
2. **Ending HEAD:** the closure commit containing this report; its exact identifier
   is supplied in the delivery response.
3. **Protocol:** [Phase 14aq](protocols/phase_14aq_reviewer_integrity_repair.md),
   commit `153eb68`, SHA-256
   `2a467795c60d5942a2c4400c5b38c4cea1b3715a7775c713d7445b63ce9db5b7`.
4. **Exact defect:** stale local `tolerance` from the validation loop was consumed
   by the later row loop in historical `review_records`.
5. **Corrupted Session 14ap rows:** all six used the stale source; rows 0–4 were
   numerically wrong and row 5 matched only by coincidence.
6. **Correct source:** each validated retained level record's own `tolerance`.
7. **Separation:** reviewer and validator are separate modules; shared elements
   are immutable schemas/constants, strict parsing, canonical encoding and hashes.
8. **Stale-variable control:** rejected with five localized mismatches on rows
   0–4 and no accepted classification.
9. **Other corruptions:** swapped, duplicated, missing, shifted, wrong-warning,
   stale-estimate, wrong-error and malformed-unavailable cases all rejected.
10. **Retained hashes:** manifest
    `367cec3ea22163af15c299b96e3792424707603b5920257eed40b3e06e5335f3`,
    private index
    `23b4264f0bce761cc17cb61357cd1fd39b6a418e5bce9938314898f8025d3955`,
    selection mapping
    `66061ced1444c9e818263d6ed4651a281eb53bfa1c9fd857e9e966958e4a5d2a`.
11. **Completed tolerances:** `1e-13`, `5e-14`, `2e-14`, `1e-14`, `5e-15`.
12. **Completed estimates:** five available and exactly equal; exact values are
    private and hash-bound.
13. **Warning level:** tolerance `2e-15`; historical aggregate unavailable. The
    reviewer-derived nine-piece sum is private and distinctly labeled.
14. **Estimate differences:** all adjacent aggregate comparisons are exactly
    equal; exact differences remain private.
15. **Error progression:** reported aggregate errors exactly plateau across all
    six requests; exact errors remain private.
16. **Trace identity:** equality covers ordered callback nodes and values,
    per-piece hashes, ordered piece hashes, initialized arrays, topology and level
    hashes.
17. **Terminal evidence:** 189 evaluations, nine active terminal intervals and
    zero subdivision operations at every level; sanitized interval 8 dominates
    retained reported error.
18. **Warning:** SciPy `IntegrationWarning` with the generic message quoted above.
19. **Warning semantics:** locked source reports detected roundoff prevented the
    requested tolerance and the reported error may be underestimated.
20. **Estimate stability:** exactly stable over retained requests; stability alone
    does not establish accuracy.
21. **Roundoff/subdivision verdict:** termination metadata and locked source
    identify reported roundoff; no subdivision-limit exhaustion occurred.
22. **Missing evidence:** one independently bounded reference for sanitized
    warning-producing terminal interval 8.
23. **Classification:** **C — roundoff/subdivision limitation identified**.
24. **Readiness:** **2 — ready for one specific additional numerical evidence run**.
25. **Recommendation:** separately govern acquisition of one independently bounded
    reference for sanitized warning-producing terminal interval 8; do not rerun
    the full edge or alter the comparator automatically.
26. **Numerical recomputation:** none. Only standard-library arithmetic over
    retained returned values was performed.
27. **Empirical access:** none; zero state or edge records were opened.
28. **Scientific products:** none opened or interpreted; Session 14R remains paused.
29. **Validation:** focused Session 14aq 8/8 and focused plus relevant Session
    14ap 41/41 passed. The full suite passed 874 run / 871 passed / 3 retained
    skips. CI status is supplied after delivery checks finish.
30. **Commits/push:** protocol `153eb68`, implementation `12ca6ac`, and this
    closure commit, exactly three; push and synchronization are delivery gates.

## Integrity and scope

The eight-file public package is under
`outputs/continuous_occlusion_terminal_error_revalidation/`; its manifest
SHA-256 before the closure commit is
`90c000da20f0ce7afd1a626518173a8cc3aeabdcd31681670d3f747a39739eee`.
Exact private evidence remains ignored under private-index SHA-256
`b55cb44e1994a4a10cb5e8e8e268400d02f1c09d3ff94d89aeea39e4b0f63670`.

Session 14ap remains historically invalid. The claim ledger, scientific
summaries, numerical implementation, public API, dependencies and release are
unchanged. No football, accessibility, suppression, attribution or value claim
follows from this reviewer-integrity result.
