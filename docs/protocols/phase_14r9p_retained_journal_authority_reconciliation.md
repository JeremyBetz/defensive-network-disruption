# Phase 14R9P — R9N retained-journal authority reconciliation

**Frozen 2026-09-19 before governed reconciliation.** Starting authority is
clean synchronized commit `88e9e2d2d0d95f7da8574dd23b21ac015251e74d`;
annotated `v0.1.0` remains
`f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`.

## Question and boundary

R9P asks why R9O expected 30,881 retained R9N journal records while its single
linear review observed 31,161, and which content-bound facts should authorize a
future retained-edge diagnosis. R9O remains **NF / PD / readiness 4**. R9P is a
metadata-only authority reconciliation: it may read canonical journal records,
safe lifecycle action names, materialization receipts, terminal context and
traceback bindings. It may not decode prepared rows, reconstruct geometry,
evaluate a field, inspect scientific summaries, or run a numerical diagnosis.
Empirical exposure must remain zero states and zero edges.

Planning inspection established these pre-existing facts, which the governed
review must verify rather than assume:

- 30,881 is the retained R9I journal count recorded in the R9I report and R9J
  authority. R9O copied it into its prospective count gate.
- The R9N protocol and report bind the retained R9N journal by raw SHA-256 but do
  not assert 30,881 as its record count.
- The hash-bound R9N journal contains 31,161 records. Its 280-record increase
  over R9I consists of 226 numerical-stage records, 21 candidate starts, 21
  candidate completions, 10 edge completions, one state completion and one state
  evaluation start.

These observations do not retroactively validate R9O or authorize its numerical
branch. One create-once governed reconciliation must establish their integrity.

## Frozen authority

The following committed and retained authorities are immutable inputs:

```json
{"docs/protocols/phase_14r9i_empirical_execution.md":"3f043780b14a518235b94c86ba9d5323b05156b7214ebc5b654bbfcb2b0586a7","docs/protocols/phase_14r9j_r9i_blocker_diagnosis.md":"8c205e768840260dc81ea7bb000d8edaa143de75eb0158d3a80bb7f3e43de9dd","docs/protocols/phase_14r9m_preaccess_authority_traceback_repair.md":"4c17117ae483ffddcaa4859de292cba795a8682754f15474df811b007c7b1e28","docs/protocols/phase_14r9n_empirical_representation_retry.md":"d4d21e0a37a240c6bd88f240aa57cc5acd4361a6b4f9157a6d625589204037be","docs/protocols/phase_14r9o_switch_equality_failure_diagnosis.md":"58d7f9e17f8566802b425585f89bafced3c68b1d891276cfb964321bc8ed3eb8","docs/session_14r9i_empirical_execution.md":"63e0b2d0758685cfbcaa921978028f5c2ae43346411ed4fe270c791b8d9dfd0f","docs/session_14r9j_r9i_blocker_diagnosis.md":"7b1f4a2ddd0c4b8dc3030aa156c7a4fe058298b0132a3934bf0a95c767af2465","docs/session_14r9m_preaccess_authority_traceback_repair.md":"995378793b2bcd20a553190c7227fed42de8655273de956c5739c303d331baf2","docs/session_14r9n_empirical_representation_retry.md":"d86a62a7284ac8617a826a1b723f4015c52f2fb88a29563e8b50759b29d7db0a","docs/session_14r9o_switch_equality_failure_diagnosis.md":"2346b04119a3f18582c8f6b1949b4bf8cfcca91bc9919b80edaa3a7381d49d93","outputs/continuous_occlusion_preaccess_authority_repair/manifest.json":"222364223e3c6a9b4b9a91605794593d4ddacf2a42ba3cf509c2bd4ad0f41e26","outputs/continuous_occlusion_r9i_blocker_diagnosis/manifest.json":"cbe421fe0fec781e2456e811806e437ad0dc711f958f05a0d9f1ed7d13602a96","outputs/continuous_occlusion_r9n_blocker_diagnosis/manifest.json":"c95ad1567d0343a4bfdb618707d8d1a338035032d1673808b35b0819c9d076ae","src/defensive_network_disruption/validation/r9j_linear_publication.py":"a242cb0921d1fd390cd2b74c9d15a0fdff3e2b82e46000dc8be0cbbba6d6c139"}
```

Retained R9I journal authority is raw SHA-256
`6f1c2110d20fc0edbfe9d337f231e829a73df9d90eb47f65f6afb2366054ef3c`
with terminal `GateFailure` at state 4, edge 7, candidate `constant_width`, stage
`onset_adaptive`, and traceback SHA-256
`a43e4740e2fceaa9a6d02cf335bdbc80f09880d69d0675950705a6aac4b2d369`.

Retained R9N journal authority is raw SHA-256
`ab5600ba8eea54092996bb2f4c613c76a5ba331c25c2c9d2b7bb65fa6e9555db`
with terminal `VerificationError` at state 5, edge 8, candidate `expanding`,
stage `owner_certification`, and traceback SHA-256
`6d8cf23e2486fd161878260501975e9ec4409eab27bf91ee811be78e0bc3834c`.

## Prospective retained-journal contract

An immutable session-specific descriptor binds the session ID, raw journal
SHA-256, expected terminal failure/context, traceback SHA-256, and required
materialization receipt. The unchanged R9J linear reviewer must validate
canonical encoding, sequence continuity, the hash chain, lifecycle semantics,
exposure accounting and the descriptor in one pass. The returned record count is
persisted as a derived consistency fact. No caller may supply a count as an
independent authorization condition.

The authority is exact raw hash plus valid chain and sequence plus expected
terminal failure/context and traceback plus required materialization receipt.
Count role is prospectively frozen as **CB — DERIVED CONSISTENCY FACT**. A correct
count with the wrong hash, any changed record, truncation, append, broken chain,
wrong terminal evidence or missing receipt blocks. R9I and R9N use distinct
descriptors; no authority is reused across sessions.

## Governed execution and evidence

The isolated runner exposes only `preflight`, `reconcile` and
`publication-check`. A synchronized create-once marker reserves the one governed
metadata review and grants no data access. Complete private review receipts are
create-once and ignored. Public evidence contains only hashes, safe action counts,
terminal flags, decisions and classifications.

The governed review validates R9I and R9N once each, records their safe action
histograms, verifies the exact 280-record delta, runs frozen negative controls,
and hash-closes exactly these public files beneath
`outputs/continuous_occlusion_retained_journal_authority/`:

- `reconciliation_contract.json`
- `count_provenance.json`
- `journal_structure_delta.csv`
- `r9n_validation.json`
- `r9i_regression.json`
- `negative_controls.csv`
- `qc.json`
- `manifest.json`

Publication checking reads persisted evidence and hashes without rereading a
retained journal or regenerating missing evidence. Any unexpected governed
failure is preserved and closes the session without repair or rerun.

## Tests, decisions and stop rules

Before governed reconciliation, test exact R9I/R9N descriptors, deterministic
serialization, wrong-hash same-count input, tampering, truncation, append,
sequence/chain corruption, terminal/context/traceback mismatch, missing receipt,
attempted supplied-count override, marker collision, interrupted review, failed
closure, rerun rejection and absence of geometry/numerical/scientific routes.

R9O mismatch classification is A only if 30,881 is proven to belong to R9I and
not prior R9N authority, 31,161 is derived from the exact hash-bound R9N journal,
all terminal evidence matches, and the 280 records contain no unexplained action
or duplication. Otherwise use B for unexpected extra records, C for distinct
valid stages, D for ambiguity, or E for invalid evidence.

R9P classification is **A — authority reconciled; R9N journal valid for
retained-edge diagnosis** only when all exact authority, delta, regression,
negative-control, zero-access, publication, validation and CI gates pass. Use B
when reconciliation succeeds but diagnosis authority does not, C for partial
reconciliation, and D for invalid/unresolved evidence. Readiness 1 is available
only with A; otherwise use 2, 3 or 4 according to the remaining authority defect.

Preserve three commits: protocol; tested prospective repair; closed evidence,
report and append-only research-log entry. Push the tested implementation and
require green Python 3.11, Python 3.13 and distribution CI before the governed
review. Push closure, require final green CI, verify clean synchronized heads and
the unchanged tag, then stop. On A/readiness 1 recommend exactly: **separately
govern the bounded R9N expanding-field switch-equality diagnosis using the
reconciled retained-journal authority.** Do not execute that diagnosis.
