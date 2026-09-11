# Session 14y — Switch projection repair and reproducibility rerun

Date: 2026-09-11

## Result

**H — UNRESOLVED. Readiness 4 — MORE EVIDENCE REQUIRED.**

The diagnostic projection repair succeeded. The single local run reproduced all 108 historical vectors and 366 components bit for bit. The single GitHub Actions Python 3.13 computation also completed successfully, but its 314,834-byte base64 record was emitted as one log line. GitHub omitted that oversized line from the downloadable log while retaining the end marker. The declared CI hash and payload were therefore unavailable, and the cross-platform comparison failed closed without another dispatch.

This is a CI evidence-transport failure. It does not establish benign drift, algorithmic drift, or an overstrict historical equality contract. Session 14x remains historically H/4 and Session 14R remains paused.

## Handoff

1. Starting HEAD: `890c9142f59e5c3c760d70090e8d18ccc7e0b974`.
2. Ending HEAD: the closure commit containing this report.
3. Protocol: `docs/protocols/phase_14y_switch_projection_repair_and_reproducibility.md`; commit `2665d97e116563947df9478bd827c90af20611cf`; SHA-256 `6fa9bb40e22979f5d83cc446cfaf6e24aaae3234a68446676baeb338cfd8f92e`.
4. Session 14x defect: its routing serializer requested nonexistent `left_owners` and `right_owners`.
5. Repair: a separate diagnostic projection reads and labels `owners_before`, `owners_at`, and `owners_after`, plus the real switch metadata, with deterministic diagnostic-only ordering.
6. Real schema: `location`, `owners_before`, `owners_at`, `owners_after`, `crossing_pairs`, `endpoint`, `multiway`, and `envelope_value`.
7. Regression: ordinary, exact-switch, multiway, identical-side, ownerless-side, and permutation-mapped projections passed; the fixture explicitly confirms the old attributes do not exist.
8. Numerical preservation: production files were unchanged; both historical acceptance tests passed; local diagnostics matched all 366 historical floats and bits exactly.
9. Historical test one: `test_session14v_micro_interval.Session14vMicroIntervalTests.test_complete_historical_synthetic_acceptance`.
10. Historical test two: `test_session14w_failure_evidence.Session14wMicroIntervalTests.test_complete_historical_synthetic_acceptance`.
11. Equality semantics: Python integer equality for accepted intervals and Python dictionary equality for parsed float estimates.
12. Local environment: macOS 26.6.2 arm64, CPython 3.13.15, NumPy 2.5.3, SciPy 1.18.1, Accelerate BLAS/LAPACK, uv editable sync.
13. CI environment: Ubuntu 24.04 image `20260907.300`, x86_64, CPython 3.13.15, NumPy 2.5.3, SciPy 1.18.1, uv editable sync; CI BLAS/LAPACK metadata is unavailable because the diagnostic payload was not retained.
14. Dependency difference: Python, NumPy, SciPy and lock hash match; OS, architecture and numerical backend differ, with the CI backend unresolved.
15. Local accepted resolutions: 512 for 55 vectors, 1,024 for 13, 2,048 for 30, 4,096 for 8, and 8,192 for 2.
16. CI accepted resolutions: unavailable.
17. First divergent ladder resolution: unavailable.
18. Partition/switch equality: unavailable cross-platform.
19. `owners_before`/`owners_at`/`owners_after` equality: unavailable cross-platform.
20. Micro-interval routing equality: unavailable cross-platform.
21. Residual-bound equality: unavailable cross-platform.
22. Differing local-versus-CI components: unavailable. Local versus historical: zero of 366.
23. Maximum absolute difference: unavailable cross-platform. Local versus historical: zero.
24. Maximum relative difference: unavailable cross-platform. Local versus historical: zero.
25. Maximum ULP distance: unavailable cross-platform. Local versus historical: zero.
26. Signed-zero findings: no local-versus-historical signed-zero difference; CI unavailable.
27. Algorithmic reproducibility: unresolved.
28. Bitwise reproducibility: unresolved.
29. Numerical reproducibility: unresolved.
30. Historical equality contract: unresolved; no replacement tolerance was selected.
31. Classification: H — unresolved.
32. Readiness: 4 — more evidence required.
33. Exact bounded repair needed: transport the already bounded diagnostic as deterministic chunks or a hash-verified workflow artifact, with reconstruction tests and no numerical changes, then conduct a new governed audit.
34. No empirical state, target, outcome, model, option share, protected/reserved/withheld data, pose, xT, progression or provider product was accessed.
35. No Session 14R partial scientific output was inspected.
36. Tests: focused/relevant 29/29 passed; full suite 491 run, 488 passed and 3 retained skips; compilation, hashes, privacy, links, history, staged-content and diff checks passed.
37. Governed CI diagnostic: run `34655637144` succeeded once; its begin envelope and payload were absent from the 40,593-byte downloaded log, whose SHA-256 is `035fb06bd697868eb41a80cbd76a9ddd3793b8924c79b2482d14f8fbecc845db`.
38. Ordinary CI at the tested repair commit passed all jobs in run `34655623242`; final closure CI is verified after push.
39. Recommendation: separately govern a bounded CI diagnostic-evidence transport repair, then perform a fresh cross-platform reproducibility audit. Do not alter historical equality or authorize Session 14R first.

The manifest SHA-256 is `befaaa173cb4377f57781a238d4b2ed0823aa1ff7fe8043a53d7913af023a6c4`. Evidence is in [the Session 14y package](../outputs/cross_platform_vector_reproducibility_14y/manifest.json).
