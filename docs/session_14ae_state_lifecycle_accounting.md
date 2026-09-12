# Session 14ae — State-lifecycle accounting and publication-validation repair

## Decision

**A — STATE-LIFECYCLE ACCOUNTING AND PUBLICATION VALIDATION REPAIRED**

**Readiness 1 — ready for a separately governed retry protocol**

Session 14ae was synthetic and orchestration-only. It changed no field formula,
integration rule, reference, model, scientific output, claim, dependency, or
released API. It opened zero real empirical states and zero real empirical
edges. Session 14R3 remains preserved as **D — BLOCKED / readiness 3**.

The closed evidence is bound by the [manifest](../outputs/session14_state_lifecycle_accounting/manifest.json),
whose SHA-256 is `0bc787859ce4c7322cbb97be5d6859341a9c25b16ce476400b2027d58893fa01`.

## What was repaired

R3 preparation incremented a row counter and its failure path supplied that
number as `states_completed`. The validator accepted nonnegative independent
fields, so the synthetic preparation-failure record could say one state was
prepared and completed although no state or edge evaluation ran.

The repair introduces one internal progress object. A state moves through
`discovered`, `prepared`, `evaluation_started`, and `evaluation_completed`; an
edge moves through `discovered`, `evaluation_started`, and
`evaluation_completed`. The object owns transitions and derives counters from
its state and edge records. A state completes only after all of its required
edges complete. Failure is terminal evidence attached to the reached stage and
cannot advance an entity. Access remains separately counted.

The publication validator now enforces lifecycle ordering, parent/child
completion, terminal-status rules, access authority, failure evidence, complete
success, and exact counter presence. QC contains the canonical lifecycle
snapshot. Its SHA-256 must agree with the manifest, success/failure evidence,
and report-facing machine summary. A mismatch in any view rejects publication.

## Requested handoff

1. **Starting HEAD:** `3a24f985e2069faff28b5459c6f8f6839e5ba9ce`.
2. **Ending HEAD:** supplied after the closure commit.
3. **Protocol:** [Phase 14ae](protocols/phase_14ae_state_lifecycle_accounting.md), commit `814fc4a`, SHA-256 `d500317a01afc30766974132623140e9ebd1de54cb1ae149869260195d54e232`.
4. **Exact R3 defect:** a preparation row count was passed as completion and cross-field validation was absent.
5. **State lifecycle:** discovered → prepared → evaluation started → evaluation completed.
6. **Edge lifecycle:** discovered → evaluation started → evaluation completed.
7. **Counter semantics:** all eleven counters are derived from registered lifecycle and access records; callers cannot set totals.
8. **Implementation repair:** internal transition-owned progress, strict snapshot validation, canonical snapshot hashing, and cross-file validation; historical R3 files are unchanged.
9. **R3 regression:** accepted with discovered 1, prepared 1, evaluation started 0, completed 0, and edge started/completed 0/0.
10. **Preparation-only:** accepted as blocked with prepared 1 and zero evaluation/completion.
11. **Evaluation-start failure:** evaluation started 1, state completed 0, edge started/completed 0/0.
12. **Mid-edge failure:** state started 1/completed 0; edge started 1/completed 0; state and edge failures each 1.
13. **Partial-edge completion:** two edges started, one completed, and the state remained incomplete.
14. **Successful state:** one state and two required edges discovered, started, and completed exactly once.
15. **Invalid publication oracles:** all ten were rejected, including the exact R3 combination, reversed lifecycle counts, incomplete success, unauthorized access, missing counters, and parent/child inconsistency.
16. **Valid publication oracles:** all four were accepted: preparation-only blocked, mid-evaluation failure, publication failure after complete processing, and complete success.
17. **Access accounting:** synthetic oracle results were 0/0, 1/0, and 1/1; governed real access stayed 0/0.
18. **Cross-file validation:** valid control accepted; QC, manifest, evidence-status, and report-digest mismatch controls all rejected.
19. **Failure preservation:** six injected stages retained reached counters without inventing later completion.
20. **Success publication:** accepted only after all required states and edges completed with no failures or active entity.
21. **Single source of truth:** achieved; QC holds the snapshot and every other view binds its canonical SHA-256 `dac7f8e21f233423dd589f4f0eb2f304c07f29310611ba0b3e0c4b00926f1224`.
22. **Real states opened:** `0`.
23. **Real edges opened:** `0`.
24. **Classification:** A — state-lifecycle accounting and publication validation repaired.
25. **Readiness:** 1.
26. **Numerical/scientific contracts:** unchanged.
27. **Empirical data:** not accessed.
28. **R3 scientific outputs:** no partial scientific output was inspected.
29. **Focused/full tests:** 12 focused passed; 34 relevant R3/14ad tests passed; full suite 568 passed with 3 retained skips.
30. **Python 3.11 CI:** required after the closure commit; report in the final execution handoff.
31. **Python 3.13 CI:** required after the closure commit; report in the final execution handoff.
32. **Distribution CI:** required after the closure commit; report in the final execution handoff.
33. **Commits and push:** protocol `814fc4a`; implementation `f648697`; closure commit and push reported after completion.
34. **Recommendation:** separately govern a fresh Session 14R empirical representation retry using the repaired lifecycle-accounting and publication-validation contract.

## Validation and limits

The exact R3 runner, protocol, report, and manifest hashes were rechecked against
their starting values. Focused, relevant, and full tests passed; compilation and
the publication checker passed. Three initialization-era scaffold tests remain
skipped because their old contracts are intentionally undefined. Documentation,
privacy, history, schema/hash, staged-content, and whitespace checks accompany
the closure commit.

This result establishes an orchestration and evidence-validation contract. It
does not answer the continuous-occlusion question and supplies no evidence for
field validity, accessibility, suppression, attribution, or value.
