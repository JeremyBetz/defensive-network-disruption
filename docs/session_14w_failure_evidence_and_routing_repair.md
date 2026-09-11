# Session 14w — Failure-state evidence and routing repair

Date: 2026-09-11

## Result

**A — ROUTING / FAILURE-EVIDENCE REPAIR SUCCEEDS; MICRO-INTERVAL VERIFIER ACCEPTED.** Retry readiness: **1 — READY FOR A NEW SEPARATELY GOVERNED SESSION 14R RETRY**.

Session 14v failed because it assumed one bounded piece and eleven quadrature pieces before retaining observed routing. Session 14w instead applied the frozen inequality and found two bounded widths: `3.3306690738754696e-15` and `3.4416913763379853e-15`. With 12 pieces, the threshold was `8.333333333333334e-14`; ten pieces used adaptive quadrature and the residual upper bound was `6.772360450213455e-15`.

Failure publication now distinguishes success and failure membership, preserves partial routing evidence, and accepts unavailable success artifacts. Access accounting is stage-derived and its synthetic oracles cover `0/0`, `1/0`, `1/1`, success, and blocked additional access. Session 14v remains historically invalid and unchanged.

## Handoff

1. Start: `348ccdea71df1fc06df04440ef457f2a87daf849`.
2. Protocol: `docs/protocols/phase_14w_failure_evidence_and_routing_repair.md`, commit `79491e9`.
3. Implementation: commit `55815b2`.
4. Session 14v defect: hard-coded `1+11` routing expectation.
5. Publication defect: success-only output membership rejected valid failure closure.
6. Accounting defect: generic failure QC wrote `0/0` after `1/1` access.
7. Routing evidence is persisted before acceptance, privately per piece and publicly in aggregate.
8. Success/failure status is explicit; incomplete failure outputs are valid.
9. Access counts follow actual stage transitions.
10. Synthetic routing oracles passed.
11. Failure-publication oracles passed.
12. Access-accounting oracles passed.
13. Frozen cases: 108/108 passed.
14. References: 366/366 passed.
15. Permutations: 399/399 passed.
16. Historical prepared-byte equivalence passed.
17. Structural pieces: 12; one true switch; zero tie intervals.
18. Threshold: `8.333333333333334e-14`.
19. Bounded widths: `3.3306690738754696e-15`, `3.4416913763379853e-15`.
20. Bounded/quadrature counts: 2/10.
21. Residual upper bound: `6.772360450213455e-15`.
22. Joint Simpson: `0.023058286606118288`, converged deterministically at 2,048 intervals.
23. Independent maximum interval: `[0.023058296207020847, 0.023058296207027627]`; all inherited comparisons passed.
24. Joint-to-interval distance: `9.600902559081526e-09`, within `1e-6`.
25. Integration warnings: zero.
26. Access: one authorized state and one authorized edge; no additional access.
27. Fields, partitions, references, tolerances and production Simpson remained unchanged.
28. No model, target, outcome, share, provider product, protected/withheld data, pose, xT, progression or Session 14R partial result was accessed.
29. Manifest SHA-256: `ee4fd0535a987757c291065fefabc319c5383c04341d105fe2e3efb1c7c4b131`.
30. Claim ledger unchanged; accessibility remains **PROXY ONLY** and suppression **NOT SUPPORTABLE**.
31. Session 14R was not resumed.
32. The sole recommendation is to separately govern a fresh Session 14R empirical representation retry under the repaired micro-interval and failure-publication contracts.

Evidence: [routing](../outputs/continuous_occlusion_routing_repair/failing_edge_routing.json), [edge regression](../outputs/continuous_occlusion_routing_repair/failing_edge_regression.json), [QC](../outputs/continuous_occlusion_routing_repair/qc.json), and [manifest](../outputs/continuous_occlusion_routing_repair/manifest.json).
