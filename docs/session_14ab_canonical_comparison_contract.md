# Session 14ab — Canonical structural comparison contract repair

## Decision

**C — COMPARATOR REPAIR REVEALS A REAL FINAL-VECTOR DIFFERENCE.**

**Readiness 3 — numerical/final-float contract work remains required.**

The bounded comparator repair succeeded. Canonical structural equality is now separate from raw solver provenance, and all canonical partitions, owner records, routing decisions, residual bounds and accepted Simpson resolutions agree exactly across the governed local and Python 3.13 CI records. The raw Brent return remains preserved and differs by one ULP as expected.

Full deterministic success was not reproduced. Four of 366 accepted final components differ by one ULP, with maximum absolute difference `5.551115123125783e-17`. Because Session 14ab prospectively required bitwise equality for every final component, `canonical_structural_equal` is false and classification C applies. No tolerance or equality rule was changed after exposure.

## Thirty-one-item handoff

1. **Starting HEAD:** `69b0ef4749cbb151f0f0dad5825165e911dc8bcb`.
2. **Ending HEAD:** recorded after the closure commit and push.
3. **Protocol:** [`phase_14ab_canonical_comparison_contract.md`](protocols/phase_14ab_canonical_comparison_contract.md), committed before comparator changes.
4. **Session 14aa defect:** whole-routing-record equality included the intentionally retained raw Brent result, even though certified canonical roots had already replaced it before partition construction.
5. **Canonical contract:** exact equality covers canonical onsets/switches, certified enclosures, owners, ties, ordered partitions, routing, residuals, accepted resolution, component order and final value bits.
6. **Provenance contract:** raw solver/onset values, their bits and source environment remain diagnostic evidence and do not define canonical production structure.
7. **Session 14aa regression:** passed. A one-ULP raw-root difference with identical canonical production fields yields `raw_solver_provenance_equal=false` and passes the canonical structural projection before the final-vector gate.
8. **Negative controls:** canonical partition coordinate/bit, owner set, routing count, residual bound, accepted resolution and final-component bit differences each make canonical equality false.
9. **Provenance retained:** raw values and bits remain in both diagnostic files and [`provenance_comparison.json`](../outputs/cross_platform_canonical_comparison/provenance_comparison.json).
10. **Local diagnostic:** 108 vectors, 366 components, 341,844 bytes, SHA-256 `18483740fa8b8cb7e34d5e71ac38ea933e9e3a3e178ccd68aac3557649d780ee`.
11. **CI diagnostic:** 108 vectors, 366 components, 342,023 bytes, SHA-256 `6fb4457947fc0101b68b7183fc1104fe7c49126d2eef6db8a913d6b62d3397f6`.
12. **Artifact integrity:** the CI declaration and single downloaded artifact hash match exactly.
13. **Canonical partitions:** exact and bitwise equal for all 108 vectors.
14. **Ownership:** `owners_before`, `owners_at`, `owners_after` and crossing pairs are equal.
15. **Routing:** bounded/quadrature selection and piece records are equal after the explicit provenance projection.
16. **Residual bounds:** equal for every vector.
17. **Accepted resolutions:** equal for every vector; the frozen distribution remains 55 at 512, 13 at 1,024, 30 at 2,048, 8 at 4,096 and 2 at 8,192 intervals.
18. **Final components:** 362 of 366 are bitwise equal; four differ by one ULP.
19. **Raw solver provenance:** unequal for one record.
20. **Raw solver difference:** local `0.14285714285714282` versus CI `0.14285714285714285`, one ULP; both certify canonical `0.14285714285714285`.
21. **Algorithmic reproducibility:** pass for canonical partitions, ownership, routing, residuals and accepted resolutions.
22. **Final-vector bitwise reproducibility:** fail under the frozen all-366 requirement.
23. **Differing components:** `equal_minimum_three/isotropic/union`, plus `star_edge_4/constant_width` individual 4, union and maximum.
24. **Numerical scale:** maximum absolute difference `5.551115123125783e-17`; maximum ULP distance 1. Existing numerical gates are not changed or reinterpreted here.
25. **Historical-test cause:** the two `historical_vector_changed` tests compare current controlled-Simpson estimate dictionaries exactly against platform-specific historical expected floats. They do not consume raw roots; their failure is a separate exact historical-vector contract issue.
26. **Governed CI:** [run 34665208888](https://github.com/JeremyBetz/defensive-network-disruption/actions/runs/34665208888) succeeded; one dispatch and one authenticated retrieval.
27. **Ordinary CI:** recorded after the final push and reported separately below.
28. **Classification/readiness:** C, readiness 3. Canonical structure is exact, but the prospectively required final-vector equality failed.
29. **Access:** no empirical data, provider product, target, outcome, model, share, protected/withheld material, pose, xT or progression material was accessed. No Session 14R partial output was inspected.
30. **Validation:** focused and inherited tests, full suite, compilation, schemas/hashes, privacy, links, history preservation, staged inspection and diff checks are recorded after closure.
31. **One next action:** separately govern a final-float equivalence-contract review that addresses the four one-ULP production-vector differences without weakening canonical structural checks or changing production numerics.

## Interpretation

Session 14ab resolves Session 14aa's comparator defect: raw solver provenance can differ without falsely implying different canonical partitions. It also demonstrates why that repair cannot by itself authorize Session 14R. A fresh governed CI execution reproduced the four one-ULP component differences previously seen in Session 14z, rather than Session 14aa's transient bitwise-final-vector result. The numerical differences remain far inside the existing `1e-6` reference authority, but this protocol deliberately required bitwise equality and did not authorize a replacement equivalence rule.

The claim ledger remains unchanged. This synthetic reproducibility audit says nothing about empirical occlusion structure, cover shadows, accessibility, suppression, attribution or value. Session 14R remains paused.

The closed evidence package is bound by [`manifest.json`](../outputs/cross_platform_canonical_comparison/manifest.json), SHA-256 `2a96d048256db30300415d644e456d2d5885dc3b1f8f9609e3de91ff8475e379`.
