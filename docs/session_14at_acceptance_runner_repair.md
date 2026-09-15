# Session 14at — Governed acceptance-runner repair and synthetic contract acceptance

Date: 2026-09-15. **A — governed acceptance runner repaired; certificate
contract accepted. Session 14R readiness 1.**

Session 14at repaired the bounded execution defect that invalidated Session
14as. The governed runner now imports the frozen synthetic authority through
its installed package context. It no longer loads a package-relative module as
a standalone source file. The repaired runner also validates strict success and
failure publication from its actual path.

The one governed acceptance completed 108 synthetic cases, 366 component
references, and 399 mapped permutations. The Session 14ar certificate
regression, positive controls, negative controls, ordinary quadrature,
micro-residual behavior, conservative aggregation, and derived readiness all
passed. The historical roundoff warning remains present and independently
certified; it was not relabeled warning-free. Zero empirical states and edges
were accessed.

## Numbered handoff

1. **Starting HEAD:** `c4078ac585fa293b695b4f1112c7716fc380c7b2`.
2. **Ending HEAD:** the closure commit containing this report; its identifier is
   supplied in the delivery response.
3. **Protocol:** [Phase 14at](protocols/phase_14at_acceptance_runner_repair.md),
   commit `2cb4286`, SHA-256
   `ae97cee5ff82f68ebfa39a57a92e9a4fd2461f2e15642915aa0c858ff4686134`.
4. **Exact Session 14as defect:** its runner used
   `spec_from_file_location` on `onset_owner_acceptance.py`. The standalone
   module lacked package context, and `from ..geometry ...` raised
   `ImportError: attempted relative import with no known parent package`.
5. **Approved loading:** normal installed-package import of
   `defensive_network_disruption.validation.onset_owner_acceptance` under
   `uv run --locked python`.
6. **Package-context regression:** passed in focused tests, pre-exposure replay,
   and governed acceptance.
7. **Direct-file negative control:** reproduced the exact historical relative-
   import failure outside the package context.
8. **Certificate semantics:** unchanged; the Session 14as verifier source was
   not modified.
9. **Session 14ar certificate regression:** passed from committed authority,
   with no numerical recomputation.
10. **Positive oracles:** all passed, including registered, below-boundary,
    equal-boundary, mixed aggregation, and deterministic serialization cases.
11. **Negative controls:** all blocked as required.
12. **Ordinary and micro-residual regression:** unchanged and passed.
13. **Aggregation identity:** unchanged `math.fsum` plus one final outward
    `nextafter` per side; the governed bounds are recorded in
    [readiness.json](../outputs/continuous_occlusion_acceptance_runner_repair/readiness.json).
14. **Success publication:** passed independent schema and manifest-hash
    validation against the actual eight-file package.
15. **Failure publication:** package-import, certificate-authority, synthetic-
    regression, and publication-stage failures passed strict validation in
    isolated runner tests.
16. **Historical ImportError preservation:** passed; the runner caught and
    preserved a controlled exact instance with false readiness, marker state,
    completed obligations, traceback, and zero access.
17. **Cases:** 108/108 passed.
18. **References:** 366/366 passed.
19. **Mapped permutations:** 399/399 passed.
20. **Final readiness:** the unchanged prospective readiness object derived
    `ready=true`, with one adaptive warning, one independent certification, and
    zero blocking warnings.
21. **Empirical access:** zero states and zero edges.
22. **Classification:** **A — GOVERNED ACCEPTANCE RUNNER REPAIRED; CERTIFICATE
    CONTRACT ACCEPTED**.
23. **Session 14R readiness:** **1 — READY FOR A FRESH SEPARATELY GOVERNED
    SESSION 14R RETRY**.
24. **Claim ledger:** unchanged; this work establishes no scientific result.
25. **Tests and checks:** focused 20/20 passed. The full suite passed 907 run /
    904 passed / 3 retained skips. Compilation, schemas, hashes, success and
    failure publication validators, finite JSON, privacy, links, history, and
    diff checks passed. Staged inspection and CI are delivery gates.
26. **Commits and push:** protocol `2cb4286`, implementation `0a6cff5`, and the
    closure commit, exactly three. Push and synchronization are delivery gates.
27. **Recommendation:** separately govern a fresh Session 14R empirical
    representation retry under the accepted independent-certificate verifier
    contract.

## Interpretation and boundaries

The retained adaptive estimate remains the estimator. The certificate neither
replaces it nor broadens warning eligibility. The exact SciPy warning remains
recorded with message SHA-256
`3f2b9b58ff1c98b7c27fff799d18b42a6dd19e50c2b5f6b60a0b80bfb2798ab3`.
Session 14ar remains the sole certificate authority. No Taylor derivation,
quadrature, certificate generation, tolerance change, field calculation on
empirical geometry, or Session 14R execution occurred.

Session 14as remains historically invalid. Session 14at establishes only that
the unchanged certificate contract can run and close through a governed package
entrypoint with valid success and failure publication.
