# Session 14ag — Projection-to-edge exposure accounting repair

## Decision

**A — PROJECTION-TO-EDGE EXPOSURE ACCOUNTING REPAIRED**

**Readiness 1 — ready for a fresh, separately governed Session 14R empirical
representation retry**

Session 14ag repaired the synthetic accounting defect that blocked Session
14R5. It did not reopen R5 or access development geometry. The repaired contract
counts a carrier-to-receiver connection once when its receiver geometry is
successfully materialized. The isotropic, expanding and constant-width calls
remain three separate evaluations of that one edge.

The exact R5 regression now reports two opened edges, zero edge-evaluation
starts, zero completed edges and two unresolved exposed edges. Ten interruption
oracles passed, ten invalid packages were rejected by the actual cross-file
validator, and eight valid stopped/success controls passed. The governed audit
opened zero real states and zero real edges. Closed evidence is bound by the
[manifest](../outputs/session14_projection_edge_exposure/manifest.json).

## Authority and repair

The starting local, tracking and live GitHub `main` was
`0a673cf7277e6f6c62da18e24ff0bdb1c95ff2ee`. Annotated `v0.1.0` remained at
peeled target `f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`.

The [Phase 14ag protocol](protocols/phase_14ag_projection_edge_exposure_accounting.md)
was committed before implementation and synthetic execution. It preserved the
R5 report, runner, persistence module, Session 14ae lifecycle, Session 14af
publication adapter and all historical output bytes. Their pre-execution hashes
are recorded in QC and the manifest and were rechecked by the publication guard.

The historical defect arose because the unchanged R5 `project_line()` returned
the complete receiver tuple before state registration. R5 recorded the state
open, registered the state, and only then emitted per-edge receipts. Registration
removed its state-level uncertainty even though no edge receipt existed, so the
failure package claimed zero edge exposure.

The new internal adapter records a projection attempt before its callback. A
failed callback records that geometry did not materialize. A successful callback
is followed immediately by a synchronized batch receipt containing the complete
required receiver-ordinal set. That receipt precedes preparation, evaluation or
another downstream callback. A crash before the receipt leaves an unresolved
projection attempt and cannot support confirmed zero exposure.

The journal is authoritative for materialization. Lifecycle events are
authoritative for evaluation and completion. Public edge exposure is the unique
set in materialization receipts; unresolved exposure is that set minus completed
edges. Candidate-call starts and completions are derived separately by field
family. Public packages cannot override these facts.

## Requested handoff

1. **Starting HEAD:** `0a673cf7277e6f6c62da18e24ff0bdb1c95ff2ee`.
2. **Ending HEAD:** the closure commit is reported in the final execution handoff.
3. **Protocol:** [Phase 14ag](protocols/phase_14ag_projection_edge_exposure_accounting.md), commit `c4728f4`, SHA-256 `5fe31a01057ca057603fcdd323e280d2364422f6ab0077fc8ae47b7e66f218f1`.
4. **Exact R5 defect:** two receiver geometries were materialized; zero edge opens and zero unresolved exposures were reported and accepted.
5. **Geometric edge:** one carrier-to-receiver connection, independent of the number of field candidates.
6. **Exposure boundary:** successful receiver-edge geometry materialization from the projected row.
7. **Edge lifecycle:** discovered, projection attempted, geometry projected/opened, evaluation started, evaluation completed.
8. **Field lifecycle:** each frozen candidate starts and completes separately in isotropic, expanding, constant-width order.
9. **Journal semantics:** attempts precede projection; successful materialization is one synchronized batch receipt containing every unique edge ordinal.
10. **Unresolved exposure:** unique projected/opened edges minus completed edges; unresolved projection attempts are reported separately.
11. **Implementation:** new internal `projection_exposure` replay, authority, failure capture and cross-file validation, plus a bounded Session 14ag runner.
12. **R5 regression:** passed with opened `2`, evaluation-started `0`, completed `0`, unresolved exposed `2`.
13. **Projection failure:** failure before materialization opened `0` edges and left no successful exposure.
14. **Projected-only interruption:** one projected edge remained one unresolved exposed edge with zero field starts.
15. **One-field partial:** one opened edge, one field start/completion and one unresolved edge.
16. **Two-field partial:** one opened edge, two field starts/completions and one unresolved edge.
17. **Three-field completion:** one opened/completed edge, three field starts/completions and no unresolved exposure.
18. **Field failure:** constant-width failed after isotropic and expanding completed; starts `3`, completions `2`, unresolved edges `1`.
19. **Multi-edge partial:** two opened edges, one completed edge and one unresolved edge.
20. **Invalid packages:** all `10/10` actual mutations were rejected.
21. **Valid controls:** all `8/8` no-exposure, partial, completed and multi-state packages were accepted.
22. **Cross-file validation:** recomputed the journal-backed view and rejected QC, manifest, evidence or report disagreement.
23. **Failure preservation:** projected edges, field work and active context survived terminal failure.
24. **Unique-edge counting:** three candidate evaluations produced one opened geometric edge.
25. **Field-work counters:** totals and per-candidate starts/completions were derived independently of edge counts.
26. **Real states opened:** `0`.
27. **Real edges opened:** `0`.
28. **Classification:** A — projection-to-edge exposure accounting repaired.
29. **Readiness:** 1.
30. **Session 14R5 preservation:** historical runner, persistence code, interruption evidence and manifest hashes were unchanged.
31. **Numerical/scientific contracts:** unchanged; the new route contains no field or numerical evaluator.
32. **Empirical access:** none.
33. **Session 14R5 scientific output:** not inspected.
34. **Tests:** focused `12/12`; relevant Session 14ag/14af/R5 `43/43`; full suite `629` run, `626` passed, `3` retained skips.
35. **Python 3.11 CI:** reported after the closure push.
36. **Python 3.13 CI:** reported after the closure push.
37. **Distribution CI:** reported after the closure push.
38. **Commits and push:** protocol `c4728f4`; tested implementation `64c11a5`; closure and push are reported in the final execution handoff.
39. **Recommendation:** separately govern a fresh Session 14R empirical representation retry using the repaired projection-to-edge exposure accounting contract.

## Interpretation and limits

This result establishes accounting and publication behavior only. It supplies
no evidence about isotropic or directional fields, cover shadows, accessibility,
suppression, causality, attribution or defensive value. Accessibility remains
**PROXY ONLY** and suppression remains **NOT SUPPORTABLE**. The claim ledger is
unchanged.

The contract requires a future retry to establish edge identities before
coordinate materialization, then persist the successful batch receipt before
downstream processing. That future protocol must integrate the new adapter; this
phase does not modify or resume the historical R5 runner.
