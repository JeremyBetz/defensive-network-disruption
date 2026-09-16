# Session 14R9a — Publication-contract diagnosis and schema reconciliation

## Decision

Session 14R9a closes **C — CHECKER / REPRESENTATION ABSTRACTION MISMATCH / readiness 1**.
The bounded prospective repair is complete and validated. Session 14R9 remains
historically **D — BLOCKED / readiness 3**.

R9's protocol and frozen implementation define a nineteen-artifact public
package and assign lifecycle authority to `qc.json.progress_authority`. R9 also
retains a separate `lifecycle_summary.json` inside its private package so the
historical lifecycle validator can check journal-derived evidence. The final
public checker copied the older R7/R8 assertion that the same private record
must also exist publicly. That assertion is unconditional and is not derived
from R9's frozen artifact list.

The R9a validator now checks the authoritative public representation directly.
It requires the exact nineteen-name schema, validates lifecycle and
candidate-work fields from QC, validates output and private-binding hashes,
supports complete success and valid failure packages, accepts a consistent
legacy lifecycle record only as an optional cross-check, and rejects a
conflicting one. It does not modify the historical R9 checker or artifacts.

The one governed review revalidated all existing R9 public hashes and both
available private bindings. It ran no certificate, numerical, rendering,
projection, or empirical path. Empirical access remained zero states and zero
edges.

## 26-item final handoff

1. **Starting HEAD:** `a3b2af244978d60c7e5a32ac573bcdc2d6916a2c`.
2. **Ending HEAD:** the closure commit reported in final delivery.
3. **Protocol:** [Phase 14R9a](protocols/phase_14r9a_publication_contract_reconciliation.md), commit `f96d4fc`, SHA-256 `902fee5e1a253e6bc04c0a6c2335bb209793489f1d41c8bd7cf16f4c8794cb20`.
4. **Exact requirement origin:** [R9 runner](../scripts/session_14r9_occlusion_study.py) `publication_check()`, line 892 in the frozen source, unconditionally loads public `lifecycle_summary.json` after private-package validation.
5. **Historical source:** [R7 execution validation](../src/defensive_network_disruption/validation/r7_execution.py) line 220 requires `lifecycle_summary.json` in its private package; R7/R8 also copied that private record publicly.
6. **Authoritative artifact count:** nineteen.
7. **Exact artifacts:** `preaccess_contract.json`, `retained_observation_certificate_gate.json`, `runner_failure_oracles.json`, `runner_success_oracle.json`, `synthetic_acceptance.json`, `evidence_type_summary.json`, `visual_qa.json`, `candidate_summary.json`, `structural_correspondence.csv`, `candidate_pair_comparison.csv`, `receiver_corridor_ordering.csv`, `union_vs_max.csv`, `overlap_redundancy.csv`, `multi_edge_summary.csv`, `match_summary.csv`, `synthetic_stress_summary.json`, `qc.json`, `manifest.json`, and `synthetic_field_comparison.svg`.
8. **QC lifecycle fields:** package status, validation mode, journal and snapshot hashes, lifecycle snapshot status, access authorization, state/edge counters, candidate-work counters, active context, failure stage/exception, and confirmed-zero exposure. In R9's pre-access failure QC the mode is `pre_access` and the snapshot is correctly uninitialized.
9. **Legacy lifecycle contents:** exactly the same `progress_authority` object already bound in QC and the manifest.
10. **Field mapping:** [the machine-readable mapping](../outputs/continuous_occlusion_empirical_retry_r9a/lifecycle_field_mapping.json) classifies every requested datum and its exact QC path.
11. **Genuinely missing information:** attempt-marker state and exact `states_opened` for partial/failure executions are absent from both QC and the legacy lifecycle file. Pre-access zero exposure remains explicit, and complete success makes state exposure derivable. These omissions do not support requiring `lifecycle_summary.json`.
12. **Precedence verdict:** the committed prospective R9 protocol and frozen nineteen-artifact schema outrank the copied public-checker assertion. Historical private-package validation remains valid only for the private representation.
13. **Classification:** C — CHECKER / REPRESENTATION ABSTRACTION MISMATCH.
14. **Bounded repair:** a new prospective validator reads `qc.json.progress_authority` directly, preserves nineteen artifacts, permits a consistent optional legacy record, and blocks conflicts. No historical R9 file changed.
15. **Publication oracles:** twelve focused tests passed, including nineteen-file success, embedded QC lifecycle, missing/conflicting fields, stale twentieth-file behavior, optional legacy consistency/conflict, manifest mismatch, failure package, incomplete success, and validator-derived success.
16. **Failure package:** the existing R9 failure package validates under the reconciled public contract while retaining status `failure` and unavailable scientific files.
17. **Existing package hashes:** all ten committed R9 outputs listed by its failure manifest matched; both available private evidence bindings matched.
18. **Reconciled validation:** passed with schema ID `session14r9_public_artifacts_v1`, lifecycle source `qc.json.progress_authority`, artifact count 19, and validator-derived result `valid`.
19. **Empirical access:** zero states and zero edges.
20. **Readiness:** 1 — ready for a fresh, separately governed R9 empirical retry.
21. **Numerical gates:** no 108/366/399 replay, certificate orchestration, field evaluation, integration, or visual rendering occurred.
22. **Scientific interpretation:** no scientific output or historical partial result was opened or interpreted.
23. **Claim ledger:** unchanged.
24. **Validation:** focused R9a tests ran 12/12; focused plus relevant publication tests ran 25/25. The full active non-replay suite ran 936 tests, with 933 passed and 3 retained skips; ten explicit 108/366/399 replay tests were excluded under the no-recomputation boundary. CI results are reported in final delivery.
25. **Commits and push:** protocol `f96d4fc`; tested reconciliation `9aa6d31`; closure commit and push are reported in final delivery.
26. **Next action:** separately govern a fresh Session 14R9 empirical execution using the already-passed pre-access scientific/numerical evidence under the reconciled publication contract.

## Limits

R9a establishes publication representation authority only. It does not revive
R9, retroactively turn its failure package into a successful scientific run, or
authorize automatic empirical access. A future execution must separately bind
the prospective R9a validator and preserve truthful failure evidence, including
any exposure facts not represented in a public success package.
