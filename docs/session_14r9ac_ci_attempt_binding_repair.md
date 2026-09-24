# Session 14R9AC-CI2 — Checkpoint CI attempt-binding repair

Planning: ON
Turbo: OFF
Model: Astra Medium

The prospective v2 contract binds an explicit workflow attempt. Both R9AC
receipt gates now require it. Historical R9M v1 code, capture entrypoint,
receipts and behavior remain unchanged. No R9AC governed execution occurred.

The single CI2 validation capture selected run **35878553378, attempt 2**, at
historical checkpoint `34e44aab799075f52bfe2ea346db87139f3b8a5b`.
Its receipt SHA-256 is
`649c19d978c9e82a069ce2f431b5d42ee9641d39f66e47600e35faab1ba8d2e6`.
It validated offline and rejected the newer repair checkpoint. It is private
CI2 validation evidence, not operational R9AC authority. Attempt 1 remains
cancelled; neither its cancelling actor nor its cause is established.

## Authority and chronology

The [frozen protocol](protocols/phase_14r9ac_ci_attempt_binding_repair.md)
has SHA-256 `a449055be95856616ddf61310c047c88014d7d407889701ccdc73fc6452cb227`.

1. `ddf77ab0abea689f5d2c81832c205f18be3b25de` —
   `research: freeze checkpoint attempt-binding repair`.
2. `c3f18c8154606907f5f7eba30eb55057dc90a04f` —
   `fix: bind checkpoint CI authority to workflow attempt`.
3. The commit containing this report and closed package —
   `research: close checkpoint attempt-binding repair`.

No history was rewritten. The implementation checkpoint passed
[CI run 35928015839](https://github.com/JeremyBetz/defensive-network-disruption/actions/runs/35928015839)
before authenticated capture or synthetic audit. Required jobs were distribution
`107407646591`, test (3.11) `107407647008`, and test (3.13) `107407647202`, all
completed successfully. Final closure CI must also pass before final delivery;
checkpoint CI is not a substitute for that gate.

## Contract and acceptance

The internal module uses frozen expectation and verified-authority objects,
integer schema version 2 and authority ID `checkpoint_ci_authority_v2`.
Canonical bytes, an external whole-file hash and provenance hash bind the
receipt to authenticated source metadata. Capture queries the explicit attempt
and paginated attempt-specific jobs endpoint. Run, attempt, commit, repository,
workflow, job identities, terminal success and timestamp chronology must agree.
Protocol, runner, workflow and lockfile bytes come from the requested
checkpoint's Git objects, not current working files.

Offline validation performs no network request. An immutable selection record
supplies the run and attempt independently of the receipt and binds its hash.
R9AC preflight requires current-HEAD bindings; persisted publication validation
requires the checkpoint recorded at execution. Both paths reject v1 authority.
Historical bytes are never silently upgraded.

The historical capture retained these exact successful attempt-2 jobs:

| Job | Job ID |
| --- | --- |
| test (3.11) | 107278457283 |
| test (3.13) | 107278457058 |
| distribution | 107278457488 |

All 15 governed synthetic control methods passed, including mutation subcases
for absent/cancelled/mixed attempts, wrong bindings, unsuccessful jobs, malformed
timestamps and pagination, source/provenance tampering, interruptions, duplicate
writes, v1 compatibility, both R9AC gates, stale authority and access/network
tripwires. Subcases are not inflated into additional test counts. The persisted
R9AC gate test accepts the synthetic v2 receipt up to the next deliberately
absent authority record; it does not claim a real R9AC package was produced.

## Validation and preservation

| Validation | Run | Passed | Retained skips |
| --- | ---: | ---: | ---: |
| Focused v2 | 15 | 15 | 0 |
| R9M regressions | 32 | 32 | 0 |
| R9AC regressions | 38 | 38 | 0 |
| Local full suite | 1,369 | 1,366 | 3 |
| Clean tracked-checkout full suite | 1,369 | 1,366 | 3 |
| Checkpoint CI Python 3.11 | 1,369 | 1,366 | 3 |
| Checkpoint CI Python 3.13 | 1,369 | 1,366 | 3 |
| Governed CI2 audit | 15 | 15 | 0 |

These are separate runs, not additive unique coverage. Tracked-checkout imports
were asserted to originate in that checkout's `src` tree. Compilation,
schema/hash/canonical-byte validation, finite JSON, privacy, links, preservation,
staged review and diff checks passed before closure. Numerical suite replays
are validation only, not a governed numerical acceptance.

The [manifest](../outputs/continuous_occlusion_checkpoint_attempt_binding_repair/manifest.json)
hash-closes exactly six public artifacts and private capture, source, selection,
controls, preservation and validation records. Publication checking reads
persisted records without recapture or test execution.

The only edits to existing implementation files are the two approved receipt
gates and their test mock. R9M v1, numerical/scientific code, dependencies, public
API, release metadata and historical evidence remain unchanged. The research
log receives one append-only entry. Release `v0.1.0` remains at
`f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`.

## Fifteen-item handoff map

| Item | Evidence or result |
| --- | --- |
| 1. Starting authority | Clean synchronized `34e44aab799075f52bfe2ea346db87139f3b8a5b`; unchanged release. |
| 2. Protocol and chronology | Protocol hash and three commits above; final containing-commit identity supplied in delivery handoff. |
| 3. Defect | V1 cannot encode workflow attempts and cannot satisfy a v2-required gate. |
| 4. Schema | Immutable objects, canonical schema 2, provenance and whole-file hashes. |
| 5. Capture | Explicit authenticated attempt and paginated jobs; historical Git source bindings. |
| 6. Offline validation | Strict source/receipt consistency, independently selected run/attempt and implementation bindings; no network. |
| 7. Integration | Both R9AC receipt paths require v2; numerical behavior unchanged. |
| 8. Compatibility | Historical valid v1 remains valid through its unchanged path only. |
| 9. Negative controls | All 15 control methods passed, including mutation subcases and expected rejection. |
| 10. Authenticated receipt | One historical attempt-2 capture with the three required IDs and hash above. |
| 11. Stale authority | Historical receipt cannot authorize the newer repair checkpoint. |
| 12. Access | Zero empirical records/states/edges opened or reopened; zero retained authority decodings and bound invocations. No R9AC attempt marker or operational receipt. |
| 13. Validation | Separate run/pass/skip counts above; six-file persisted package valid; private evidence hash-bound. |
| 14. Delivery | Checkpoint green; final CI, synchronized clean heads and unchanged tag mandatory before final handoff. |
| 15. Decision | Technical acceptance A/readiness 1; final delivery remains conditional on final CI. Sole next action below. |

After final delivery gates pass, CI2 closes **A / readiness 1 / execution
valid**. Future R9AC resumption needs fresh v2 authority for its then-current
green checkpoint. The historical validation receipt cannot substitute for it.

**Resume R9AC at v2 checkpoint-receipt capture and frozen preflight, then execute
the single terminal-cell bound if all gates pass.**

That recommendation was not executed in CI2.
