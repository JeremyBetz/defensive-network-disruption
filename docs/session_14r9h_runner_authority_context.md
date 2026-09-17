# Session 14R9H — runner authority-context wiring diagnosis

## Decision

Session 14R9H closes **A — RUNNER AUTHORITY CONTEXT CORRECTLY WIRED; FRESH
EMPIRICAL RETRY AUTHORIZED**, with readiness **1 — READY FOR FRESH EMPIRICAL R9
EXECUTION**.

The actual numerical path does not lose runtime geometry. The R9E runner passes
`alias`, `state`, and `edge` as orchestration metadata while passing origin,
receiver, and defenders as the numerical arguments. Inside the unchanged
evaluator, those numerical arguments are validated as float64 geometry and then
joined with the metadata immediately before `independent_maximum`. The complete
context reaches `_runtime_request`, where `alias`, origin, receiver, and the
ordered defender sequence form the selected-geometry fingerprint.

R9G inspected the earlier metadata-only argument and stopped before observing
this later join. Its historical **D — invalid / blocked, readiness 4** record is
preserved. R9H does not rewrite that execution; it prospectively establishes
that the current runner/verifier route already supplies the required geometry.
No production context object or numerical repair was needed.

## Evidence

The single governed synthetic acceptance observed the actual route through
`evaluate`, intercepted `independent_maximum` without changing the preceding
calculation, and delegated fingerprint construction to the unchanged portable
authority builder. The validated origin, receiver, and defenders matched the
values used by the field calculation exactly. Defender row order was preserved.
The builder received all six context fields: alias, state, edge, origin,
receiver, and defenders.

The provider-free synthetic context correctly failed against the empirical
Session 14ar selected-geometry authority. Independent origin, receiver, defender,
and defender-order mutations each changed the fingerprint. Holding alias, state,
and edge constant while changing geometry did not produce a false match.

At the separately approved retained-observation boundary, the committed Session
14ar request matched exactly, the historical warning remained present, and the
registered certificate produced
`independently_certified_after_roundoff_warning` with one certified warning and
zero blocking warnings. A synthetic interval-identity mutation remained
blocking with `authority_mismatch:interval_identity`; readiness stayed false and
no fallback certificate was used.

Static and dynamic guards found no provider or prepared-geometry loader in the
maximum-verifier authority route. The only historical record names present are
public hash keys validated by the R9F fixture. An injected context-construction
failure preserved its original exception, traceback, false readiness, zero
access, immutable failure evidence, and rerun rejection.

The governed audit opened zero empirical states and zero empirical edges. It did
not evaluate a development edge, rerun the 108/366/399 governed acceptance,
inspect partial scientific products, or modify any numerical, certificate,
field, dependency, API, claim, or release authority.

## Validation

Focused R9H validation ran 10 tests and passed all 10. Relevant R9E/R9F/R9G/R9H
validation ran 32 tests and passed all 32. The full active suite ran 978 tests:
975 passed and three retained tests were skipped. Compilation passed. A clean
tracked Git clone, with ignored/private authority records absent, ran the 32
R9-series tests and passed all 32.

The protocol was committed before implementation. The implementation checkpoint
was pushed for independent Python 3.11, Python 3.13, and distribution CI. Schema,
hash, finite-value, privacy, publication, link, history, staged-file, and diff
checks are part of closure. The exact CI run and final synchronization are
reported in the final handoff after the closure commit.

## Final handoff

1. Starting HEAD: `6385792269c9beb034722d5f01bd74ea391971fd`.
2. Ending HEAD: recorded after the closure commit.
3. Protocol: [`phase_14r9h_runner_authority_context.md`](protocols/phase_14r9h_runner_authority_context.md), commit `70dfca88b8d14dd1fc322f38dbc89116830e3314`, SHA-256 `9bd7933f07e36d1bb5b87b01923182fa93e2aa67f458ee969ca9fa8729b0777d`.
4. Apparent loss interface: `calculate_edge` passes only alias/state/edge in its `authority_context` metadata argument. Actual geometry is carried separately as numerical arguments and is not lost.
5. Required authority fields: alias, validated origin, validated receiver, ordered defenders, candidate, frozen parameters, combination, endpoint bits, partitions, onsets, switches, method, provenance, and tolerance. State/edge remain orchestration identity and are excluded from the selected-geometry fingerprint.
6. Origin source: the exact origin validated by `validate_geometry` and used by field computation.
7. Receiver source: the exact receiver converted by `points(..., one=True)` and used by field computation.
8. Defender source/order: the exact float64 defender matrix returned by `validate_geometry`, preserving input row order.
9. Context object/interface added: none. The existing `evaluate.runtime_context` join was confirmed sufficient; a cosmetic production refactor was prohibited.
10. New geometry source: none. The verifier receives only passed, already validated computation geometry.
11. Numerical-evaluator versus authority-builder geometry: exact identity passed for origin, receiver, defender values/order, and sampled field values.
12. Defender ordering: order-sensitive and preserved; reversing the sequence changed the fingerprint.
13. Origin mutation: changed the fingerprint and rejected exact matching.
14. Receiver mutation: changed the fingerprint and rejected exact matching.
15. Defender mutation: changed the fingerprint and rejected exact matching.
16. Identifier-only false match: rejected with alias/state/edge held constant.
17. Retained certificate exact match: passed; warning preserved, certificate accepted, zero blocking warnings.
18. Unmatched warning: blocked with false readiness and no fallback certificate.
19. Geometry reopening: absent; no provider, prepared-geometry, or private fallback route was used.
20. Runner failure publication: passed with original exception/traceback, zero access, false readiness, immutable evidence, and rerun rejection.
21. Clean checkout: 32/32 R9E/R9F/R9G/R9H tests passed in a tracked Git clone without ignored records.
22. Empirical states/edges accessed: `0 / 0`.
23. Classification: **A — RUNNER AUTHORITY CONTEXT CORRECTLY WIRED; FRESH EMPIRICAL RETRY AUTHORIZED**.
24. Readiness: **1 — READY FOR FRESH EMPIRICAL R9 EXECUTION**.
25. Claim ledger: unchanged; no scientific result was produced.
26. Tests/checks/CI: local results are recorded above; checkpoint and final CI and closure checks are reported in the final delivery.
27. Commits/push: protocol `70dfca8`; tested tooling `44df881`; closure commit and final synchronization recorded after closure.
28. Recommendation: separately govern a fresh empirical R9 execution using the verified runtime authority-context wiring and all existing numerical/publication authority.

The evidence package is bound by the
[manifest](../outputs/continuous_occlusion_runner_authority_context/manifest.json).
No empirical retry was executed.
