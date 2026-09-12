# Session 14ac — Cross-platform final-float equivalence contract review

## Decision

**A — FINAL-FLOAT NUMERICAL EQUIVALENCE CONTRACT JUSTIFIED AND VALIDATED.**

**Readiness 1 — READY FOR A FRESH SESSION 14R RETRY under separate prospective authority.**

Canonical structure remains exact. Final production components now use the prospectively frozen comparison

`abs(actual - expected) <= 64 * epsilon64 * max(1, abs(actual), abs(expected))`.

The rule is an existing governed project scale, was selected independently of the observed drift, rejects all 19 frozen negative controls, and is more than seven orders of magnitude tighter than the controlled-Simpson convergence gate. It accepts the four supported-platform one-ULP differences without changing a production calculation, reference value, accepted resolution or scientific numerical tolerance.

## Thirty-one-item handoff

1. **Starting HEAD:** `df7dca7b83aaaa3b2fbce965af1a81be5abecd93`.
2. **Ending HEAD:** recorded after the closure commit and final push.
3. **Protocol:** [`phase_14ac_final_float_equivalence_contract.md`](protocols/phase_14ac_final_float_equivalence_contract.md), commit `f2bca625f07b0b3b16ac102f85233de3fe76cc88`, SHA-256 recorded in the manifest.
4. **Old equality semantics:** `verify_case()` required exact Python integer equality for `intervals` and Python dictionary equality for parsed float `estimates`; any one-ULP value difference raised `historical_vector_changed`.
5. **Divergent authority:** four rows are retained in [`divergent_components.csv`](../outputs/final_float_equivalence_contract/divergent_components.csv): `equal_minimum_three/isotropic/union`, and `star_edge_4/constant_width` individual 4, union and maximum.
6. **Maximum ULP drift:** 1.
7. **Maximum absolute drift:** `5.551115123125783e-17`; maximum relative drift is approximately `1.3e-16`.
8. **Governed accuracy authority:** every controlled-Simpson component delta must be at most `1e-7`; production/reference error must be at most `1e-6`.
9. **Reference-error distribution:** across 366 components, minimum `0`, p05 `0`, p25 `4.5086157030027607e-13`, median `4.059642162365651e-11`, p75 `2.8292931886220174e-09`, p95 `8.330824713669721e-09`, and maximum `4.1576548232002963e-08`. Candidate/family breakdowns are in [`reference_error_summary.json`](../outputs/final_float_equivalence_contract/reference_error_summary.json).
10. **Scale ratio:** maximum platform drift divided by maximum reference error is `1.3351553602164814e-09`.
11. **Candidates:** exact bits, 64-epsilon scale-aware comparison, the `1e-7` convergence bound, and the `1e-6` reference bound.
12. **Selected contract:** 64-epsilon scale-aware comparison. It predates the four differences, passes supported-platform evidence, and retains much higher regression sensitivity than the scientific acceptance gates.
13. **Signed zero:** `+0.0` and `-0.0` are numerically equivalent; sign bits remain diagnostic. NaN and infinity are always rejected.
14. **Structural policy:** accepted resolution, component identity/order, canonical onsets/switches, partitions, owners, tie enclosures, routing and residual bounds remain exact.
15. **Negative controls:** all 19 passed. They cover nonfinite values, float changes outside the selected bound, convergence/reference-scale changes, altered field/Simpson values, dropped/reordered components, changed resolution, partition, canonical root, routing, residual and owner authority.
16. **Regression sensitivity:** plausible wrong-coefficient, dropped-component, routing, resolution, ordering and field-value regressions are rejected.
17. **Historical tests changed:** yes, only the two named Session 14v/14w complete historical acceptance tests plus shared test support.
18. **Exact test-only change:** each test suppresses only the obsolete internal exact-float historical argument, executes the unchanged 108-vector calculation, then compares intervals, ordered component names and returned values through the explicit helper.
19. **Production code:** unchanged. The three bound production hashes equal the starting hashes in [`authority_summary.json`](../outputs/final_float_equivalence_contract/authority_summary.json).
20. **108-vector regression:** passed; every vector completed with unchanged accepted resolution and calculation path.
21. **366-component regression:** passed under the selected contract; all per-environment production values and the reference authority remain unchanged.
22. **Local suite:** 506 tests run; 503 passed and 3 retained skips. The relevant Session 14 suite ran and passed 217 tests; the focused Session 14ac suite passed 3 tests.
23. **Python 3.11 CI:** passed in ordinary CI run [`34667647370`](https://github.com/JeremyBetz/defensive-network-disruption/actions/runs/34667647370).
24. **Python 3.13 CI:** passed in the same ordinary run, including both formerly failing historical-vector tests.
25. **Distribution CI:** passed.
26. **Classification:** A — final-float numerical equivalence contract justified and validated.
27. **Readiness:** 1 — ready for a separately governed fresh Session 14R retry.
28. **One recommendation:** separately govern a fresh Session 14R empirical representation retry.
29. **Empirical access:** none. No development, provider, target, outcome, model, share, protected, withheld, pose, xT or progression material was accessed.
30. **Session 14R partial outputs:** not inspected.
31. **Commits and push:** protocol `f2bca62`, tooling `ff29ae2`, derived authority `0206a45`, test repair `29f45f0`, and closure-validator `d17d79d` preceded this report. Final synchronization is recorded after closure.

## Interpretation

Exact final bits were stronger than the supported scientific and software requirement once canonical structure had been made deterministic. The replacement rule does not reinterpret integration accuracy: the production estimator still converges under `1e-7` and remains governed by the unchanged `1e-6` reference gate. It only defines when two supported environments have reproduced the same historical production vector closely enough for regression purposes.

The closed evidence package is bound by [`manifest.json`](../outputs/final_float_equivalence_contract/manifest.json), SHA-256 `546f31982b59cb152468d7f2164910f64f057cef8dea6d89bf4a3ce6cb0359da`.

This is synthetic numerical-contract evidence, not a scientific result. The claim ledger remains unchanged, and Session 14R has not been resumed.
