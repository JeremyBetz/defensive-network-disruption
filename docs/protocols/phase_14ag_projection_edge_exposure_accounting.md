# Phase 14ag — Projection-to-edge exposure accounting repair

Prospective protocol, 2026-09-12. Starting authority is clean local, tracking,
and live `main` `0a673cf7277e6f6c62da18e24ff0bdb1c95ff2ee`. Preserve annotated
`v0.1.0` at peeled target `f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`.
This protocol is committed before implementation or governed synthetic audit.

## Question and boundary

Session 14R5 closed **D — BLOCKED / readiness 3** before empirical execution.
Its required synthetic interruption check projected a row containing two
receiver geometries, then interrupted after state registration but before the
later per-edge receipts. The published failure package reported zero opened
edges and zero unresolved edge exposure, and the persisted validator accepted
it. The current `project_line()` materializes the complete receiver tuple before
state registration, so access accounting began after the actual exposure.

Session 14ag asks only: at what transition does a carrier-to-receiver geometric
edge become exposed, and can every interruption from projection through
completion be published truthfully? This is synthetic accounting and publication
work. It accesses no development geometry, provider record, target, outcome,
model, option share, protected/reserved/withheld material, pose, xT, progression,
or Session 14R5 scientific output. It changes no field formula, numerical
contract, dependency, released API, claim, or historical Session 14 artifact.

## Geometric edge and exposure contract

One carrier-to-receiver connection is one geometric edge. Isotropic, expanding,
and constant-width fields are three evaluations of that same edge and never
three edges.

The prospective edge sequence is `discovered -> projection attempted -> geometry
projected/opened -> evaluation started -> evaluation completed`. An edge becomes
opened when its receiver-edge geometry has been successfully materialized from
an empirical row and made available to downstream work. It does not wait for a
field calculation.

The row projection transaction records an attempt before invoking the projection
callback. A failure before return records `not_materialized` and opens no edge.
After a successful return, it synchronously persists one materialization receipt
containing the complete, unique receiver-ordinal set before registration or any
downstream callback. If execution ends after return but before that receipt, the
attempt remains unresolved; publication must not claim confirmed zero exposure.
The batch receipt records every materialized edge exactly once while keeping the
individual edge identities private.

The append-only journal is authoritative for attempts and successfully opened
edges. Lifecycle records are authoritative for evaluation starts and completion.
Opened edges are the unique edge keys in materialization receipts. Unresolved
exposed edges are the opened edge set minus the completed edge set. Unresolved
projection attempts are a separate uncertainty and block a success or confirmed-
zero claim. Public counters are derived and cannot override these records.

## Field work and completion

Track field-evaluation starts and completions separately, both in total and by
the three frozen candidate names. Candidate order remains isotropic, expanding,
constant-width. A field call never increments edge access. An edge completes
only after each candidate has started and completed exactly once and all required
per-edge verification has succeeded. A state completes only after every required
edge completes.

Partial failure retains the projected/opened edge set, unresolved exposure,
candidate work, active state/edge/candidate, lifecycle snapshot, failure stage,
exception category, private traceback, and journal head. An exclusive immutable
marker rejects concurrent execution and automatic rerun.

## Frozen synthetic oracles

The exact R5 regression is two projected receivers, zero field starts, zero edge
completions, and interruption after registration. Required output is two opened
edges and two unresolved exposed edges. A package reporting zero/zero is invalid.

Exercise interruptions: before discovery; after discovery before projection;
during projection before materialization; immediately after projection; after
the first field starts; after one field completes; after two fields complete;
after all three fields complete but before edge completion; after edge completion;
and after multiple edges with one unresolved edge. Also exercise projection
failure, a final-field failure, one complete three-field edge, and multi-state
success. Synthetic wrapper compatibility follows launch, preparation, projection,
interruption, and failure publication without real access.

The real cross-file validator must reject at least: projected/opened disagreement;
negative or inconsistent unresolved exposure; completion exceeding exposure;
completion without all field completions; candidate calls counted as edges;
state completion with an unresolved required edge; journal/public disagreement;
QC/manifest disagreement; exposure reset during failure; and missing required
active context. It must accept no-exposure, projected-only, one-field, two-field,
completed-edge, partial-state, completed-state, and multi-state controls when
their records are internally consistent.

## Evidence and execution

The separate runner exposes only `preflight`, `audit`, and `publication-check`.
It has no empirical, acquisition, model, scoring, or numerical-field route. The
single governed audit runs only after this protocol and tested implementation
are committed. It runs the R5 regression, interruption table, invalid injections,
valid controls, wrapper compatibility, and success control, then atomically
hash-closes evidence. Any unexpected post-exposure defect is preserved without
repair or rerun.

Public evidence under `outputs/session14_projection_edge_exposure/` is exactly:
`exposure_contract.json`, `edge_lifecycle_oracles.csv`, `field_work_oracles.csv`,
`r5_regression.json`, `invalid_package_injections.csv`,
`valid_package_controls.csv`, `wrapper_compatibility.json`,
`access_journal_summary.json`, `qc.json`, and `manifest.json`. Private journals,
keys, tracebacks, and execution records remain ignored. Outputs use strict finite
schemas, LF CSV, atomic writes, sanitized fixture names, and hash-bound closure.

## Decision and stop

Return **A — PROJECTION-TO-EDGE EXPOSURE ACCOUNTING REPAIRED** only if the
boundary is explicit, the R5 regression and every interruption oracle pass,
geometric edges and field work remain distinct, exposure derives truthfully,
invalid packages are rejected, valid controls pass, and real state/edge access
is zero. Otherwise use B ambiguous boundary, C conflated work accounting, D
incomplete failure preservation, E incomplete cross-file validation, F multiple
issues, G unresolved, or H invalid execution. Readiness 1 requires A; otherwise
assign readiness 2–4 from the observed blocker.

Preserve three commits: protocol; tested implementation; closed evidence/report
and append-only research-log entry. Run focused, relevant and full tests,
compilation, schemas/hashes, privacy/publication checks, links, historical-byte
comparison, staged inspection and `git diff --check`; require green Python 3.11,
Python 3.13 and distribution CI after push. Stop without empirical retry.

On A/readiness 1, recommend exactly: **separately govern a fresh Session 14R
empirical representation retry using the repaired projection-to-edge exposure
accounting contract.**
