# Session 14ak — Constant-width comparator diagnosis

**Date:** 2026-09-13

**Execution:** INVALID

**Numerical classification:** **H — INVALID EXECUTION**

**Readiness:** **4 — MORE EVIDENCE REQUIRED**

**Publication classification:** **P5 — UNRESOLVED**

Session 14ak froze and tested a bounded diagnostic for the retained R8 failure.
The single governed execution opened only zero-based state 4, receiver 7, and the
`constant_width` candidate. It completed the in-memory numerical probes but
failed while serializing private evidence because a `VerifiedEnvelope` object
was not converted into a JSON-safe representation. The independent emergency
writer preserved the authorized location, exception, traceback and elapsed
time. The protocol forbids post-access repair or rerun, so none occurred.

No in-memory numerical totals are interpreted or reconstructed. Session 14R8
remains D/readiness 3, and its partial scientific summaries remain unopened.

## Forty-item handoff

1. Starting HEAD: `0ace3b79d18cdfa9b2f3dd26a7bf1d201cdbfa1f`.
2. Ending HEAD: reported after the closure commit.
3. Protocol: `docs/protocols/phase_14ak_constant_width_comparator_diagnosis.md`, commit `34651d9`; its final SHA-256 is manifest-bound.
4. Retained authority: state 4, receiver 7, `constant_width` only.
5. Failing R8 gate: `piecewise_unsplit`.
6. Production estimate: unavailable; it was not durably closed.
7. Piecewise estimate: unavailable.
8. Onset-only estimate: unavailable.
9. Gate tolerance: absolute `1e-10` point-to-interval distance.
10. Disagreement magnitude: unavailable.
11. Onset-only topology: unavailable.
12. Certified piece count: unavailable.
13. Partition coverage: unavailable.
14. Piecewise convergence curve: unavailable.
15. Unsplit supplementary Simpson curve: unavailable.
16. Highest-resolution comparison: unavailable.
17. Continuity result: unavailable in this execution; inherited analytical authority was not promoted as a new result.
18. Smoothness/onset result: unavailable.
19. Onset neighborhood: unavailable publicly and not durably retained privately.
20. Piece contributions: unavailable.
21. Production numerical health: unresolved.
22. Runtime: the diagnostic failed after 48.818896 seconds; component timings were not durably closed. R8's approximately 55-minute delay remains unattributed.
23. Synthetic reproduction: not executed, consistent with the documentation-only decision.
24. Numerical result: **H — INVALID EXECUTION**.
25. Readiness: **4 — MORE EVIDENCE REQUIRED**.
26. R8 journal: 30,882 records and 6,533,975 bytes.
27. Historical publication failure point: large-journal replay during failure closure; the exact sub-operation remains unresolved.
28. Static complexity: the implementation reduces every growing prefix, creating quadratic prefix-reduction work; governed timing evidence was not durably closed.
29. Emergency record: valid for last-resort diagnosis, SHA-256 `fda86bc1e35557ee313d47ffe1c54a44f7fa9893434dc1732fb43c92926b91c8`; it is not normal publication authority.
30. Publication result: **P5 — UNRESOLVED**.
31. Prospective repair shape: first repair JSON-safe private-evidence closure and add its regression; only then repeat bounded evidence collection for a streaming/checkpoint design.
32. Exactly one retained empirical edge was inspected.
33. The four completed R8 scientific summaries were not inspected.
34. No target, model, option share, protected, withheld, pose, xT or progression value was accessed.
35. Tests: focused 6/6 passed; 47 relevant historical tests passed. Full-suite status is reported at delivery.
36. Python 3.11 CI: pending closure push.
37. Python 3.13 CI: pending closure push.
38. Distribution CI: pending closure push.
39. Commits and synchronization: reported at delivery.
40. Recommendation: separately govern a bounded diagnostic-evidence serialization repair and regression before any new comparator diagnosis.

The claim ledger, field mathematics, numerical tolerances, released API and
`v0.1.0` are unchanged.
