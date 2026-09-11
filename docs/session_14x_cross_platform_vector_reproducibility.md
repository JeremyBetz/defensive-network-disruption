# Session 14x — Cross-platform historical-vector reproducibility audit

Date: 2026-09-11

## Result

**H — UNRESOLVED. Readiness 4 — MORE EVIDENCE REQUIRED.**

The single governed local diagnostic did not complete. While serializing the first encountered switch record, the new Session 14x adapter requested `VerifiedSwitch.left_owners` and `right_owners`; the preserved production type instead exposes `owners_before`, `owners_at`, and `owners_after`. Python raised `AttributeError` before the local vector record was persisted. The protocol forbids repairing and rerunning after an unexpected governed failure, so no GitHub Actions diagnostic was dispatched.

This is a defect in the new diagnostic adapter. It is not evidence about the historical production vector, the Session 14w numerical result, or the earlier Python 3.13 CI discrepancy. Session 14w remains preserved with its local A/1 result and incomplete cross-platform closure.

## Handoff

1. **Starting HEAD:** `749dcd2856e846d87e7f4f74e9f6b7f97bfd72c7`.
2. **Ending HEAD:** the closure commit containing this report.
3. **Protocol:** `docs/protocols/phase_14x_cross_platform_vector_reproducibility.md`; commit `474bf8d9a7977e304529a1a43f4dbce2ab849daa`; SHA-256 `42fbcaafd7323613b76da187900037e7a10f7bcb228d2c36d7e265b8c1940add`.
4. **Failing test one:** `test_session14v_micro_interval.Session14vMicroIntervalTests.test_complete_historical_synthetic_acceptance`.
5. **Failing test two:** `test_session14w_failure_evidence.Session14wMicroIntervalTests.test_complete_historical_synthetic_acceptance`.
6. **Historical equality:** accepted interval uses Python integer equality; estimates use Python dictionary equality over parsed floats.
7. **Historical authority:** `outputs/continuous_occlusion_production_acceptance/reference_comparison.csv`, SHA-256 `c0f7935a4b728598126f0b5701ad36dedf0981ab20c73b6d5879d9ee38981e56`; 366 rows grouped into 108 vectors.
8. **Local environment:** macOS 26.6.2 arm64, Python 3.13.15, NumPy 2.5.3, SciPy 1.18.1, Accelerate BLAS/LAPACK, uv editable sync.
9. **CI Python 3.13 environment:** unavailable from a governed diagnostic because dispatch did not occur. The preceding Session 14w CI established Ubuntu x86_64 with lock-resolved NumPy 2.5.3 and SciPy 1.18.1, but Session 14x does not substitute that historical log for its planned evidence.
10. **Backend comparison:** unavailable; governed CI backend metadata was not collected.
11. **Local vector:** unavailable because the complete record was not persisted.
12. **CI vector:** unavailable.
13. **Differing components:** unavailable.
14. **Maximum absolute difference:** unavailable.
15. **Maximum relative difference:** unavailable.
16. **Maximum ULP difference:** unavailable.
17. **Signed-zero findings:** unavailable.
18. **Local accepted resolution:** unavailable in retained governed evidence.
19. **CI accepted resolution:** unavailable.
20. **First divergent resolution:** unavailable.
21. **Partition and switch equality:** unavailable. The diagnostic stopped while reading a switch object for serialization.
22. **Micro-interval routing equality:** unavailable.
23. **Residual-bound equality:** unavailable.
24. **Algorithmic reproducibility:** unresolved.
25. **Bitwise reproducibility:** unresolved.
26. **Numerical reproducibility:** unresolved.
27. **Exact-equality contract:** unresolved; no replacement tolerance was selected.
28. **Classification:** H — unresolved.
29. **Readiness:** 4 — more evidence required.
30. **Failure mechanism:** Session 14x used nonexistent switch attributes; the actual immutable fields are `owners_before`, `owners_at`, and `owners_after`.
31. **Access boundary:** no empirical state, edge, target, outcome, model, share, provider product, protected/withheld data, pose, xT, progression, or Session 14R partial scientific output was accessed.
32. **Checks:** focused/relevant tests 26/26 passed; full suite 488 run, 485 passed and 3 retained skips; compilation, output hash validation, publication scan and diff checks passed.
33. **Governed CI diagnostic:** not dispatched because the required local diagnostic failed first. The one-run CI budget remains unspent but is not used under this failed authority.
34. **Commits and push:** protocol `474bf8d`, tested diagnostics `33f165e`, and the final closure commit; synchronization is verified after push.
35. **Recommendation:** separately govern one bounded repair of the Session 14x switch-record projection, then perform a fresh cross-platform reproducibility audit. Do not repair the historical equality contract or authorize Session 14R before that audit closes.

The manifest SHA-256 is `ee717cddef216ef0a0b1152e64c9192f4d2981f696c6ebb027b3e43f86e30ccb`. Evidence is in [the output package](../outputs/cross_platform_vector_reproducibility/manifest.json).
