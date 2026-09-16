# Session 14R9F — CI-portable retained-authority fixture diagnosis

## Decision

Session 14R9F closes **B — minimal sanitized committed authority fixture required and valid / readiness 1**. The three R9E tests now pass from tracked repository content on local clean-checkout simulation, GitHub Actions Python 3.11, and GitHub Actions Python 3.13. Distribution CI also passes.

The repair adds one hash-only fixture. It contains no geometry or structural values. Empirical identity remains bound to Session 14ar public hashes, while canonical derivation and mutation sensitivity are tested with an explicitly synthetic identity. The runtime adapter compares current geometry and structural semantics with those authorities and retains the original certificate request and full structural-authority hash.

## Handoff

1. Starting HEAD: `0482ce1a20c038f2174bf88223b8b50ff7831e55`.
2. Protocol: [`phase_14r9f_ci_portable_authority_fixtures.md`](protocols/phase_14r9f_ci_portable_authority_fixtures.md), commit `073ff25`, SHA-256 `86b6f10df971be29e970ddb97bb42a3cfa09d739d78b15c81273559ebe9bc164`.
3. Tested repair commit: `39a3e9b31129483802b9465a0709d66ed3dc34a4`.
4. Failing tests: `test_runtime_request_is_derived_from_exact_geometry`, `test_exact_warning_uses_registered_certificate`, and `test_unmatched_warning_blocks`.
5. Observed ignored dependencies: Session 14am selected geometry and Session 14ao warning-piece records.
6. Latent dependency: Session 14am structural record, reached after selected geometry loads.
7. Runtime-request purpose: provenance plus exact authority identity.
8. Exact-warning purpose: certificate orchestration.
9. Unmatched-warning purpose: fail-closed warning handling.
10. Consumed geometry fields were alias, origin, receiver, and defenders; none are tracked.
11. Consumed structure fields were ordered partitions, five onset fields, and eight switch fields; only their projection hash is tracked.
12. Consumed warning content is replaced by the registered warning text and committed warning hash.
13. Existing Session 14ar authority supplies geometry, piece, onset, structure, method, provenance, and tolerance hashes.
14. Portable representation: one canonical hash-only fixture under `tests/authority_fixtures/`.
15. Fixture SHA-256: `84357ed8cee08b6452fe146bcd97eb5a2d3166910aba86e46f2768f358be85f9`.
16. Source manifest SHA-256: `bb3d352e9b43b579f897e36f4f000f3fb770701fe11877f23af76a36668d97b4`.
17. Source structure SHA-256: `791ddcd717c5f08d7c834de127388c81012192c859aa20ce0c96f342fbbe69e6`.
18. No synthetic value carries an empirical authority identifier.
19. Test semantics are preserved through committed empirical identity plus synthetic derivation behavior.
20. Clean tracked-only archive: 13 run, 13 passed, 0 skipped; all three ignored records absent.
21. Focused local: 13 run, 13 passed, 0 skipped.
22. Relevant local: 72 run, 72 passed, 0 skipped.
23. Full local: 959 run, 956 passed, 3 retained skips.
24. GitHub Actions run `35116938392`: Python 3.11, Python 3.13, and distribution all passed.
25. Classification/readiness: **B / 1**.
26. Empirical access and claims: 0 states, 0 edges; claim ledger unchanged; no scientific result.
27. Recommendation: separately govern a fresh R9E empirical execution using the now-CI-portable pre-access tests and existing numerical/publication authority.

The evidence package is bound by the [manifest](../outputs/continuous_occlusion_ci_portability/manifest.json). Historical R9E remains D/readiness 4 and is not retroactively changed.
