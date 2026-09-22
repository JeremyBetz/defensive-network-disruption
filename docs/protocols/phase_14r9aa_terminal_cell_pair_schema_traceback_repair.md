# Phase 14R9AA — Terminal-cell pair-schema and traceback repair

## Authority and purpose

This protocol authorizes a prospective synthetic-only repair from synchronized
commit `931206e5cda16117778a3df4ffd504f1f7194b38`. Session 14R9Z closed **A /
readiness 1 / execution valid** after establishing two defects: version-1
`TerminalCellAuthority` creation and loading require identical coefficient
hashes despite the frozen two-reference schema, and Session 14R9Y re-raised its
blocked acquisition failure without synchronizing the original traceback.

The annotated `v0.1.0` tag must remain at
`f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`. The R9V–R9Z protocols, reports,
manifests and relevant implementations are hash-bound in private R9AA evidence.
Historical files, including the R9Y runner and unavailable historical traceback,
remain unchanged.

R9AA may access no selected-edge record, boundary geometry, prepared population,
provider data, scientific summary, empirical coefficient or field evaluator. It
performs no acquisition, refinement, terminal classification or empirical
calculation and records zero opened states and edges.

## TerminalCellAuthority version 2

Version 2 is a new internal canonical schema; version 1 remains unchanged. Its
serialization is `canonical-json-v2`. It retains the existing cell, formula,
coefficient, competitor and source-authority data and replaces the ambiguous
pair list with ordered `pair_left_ref` and `pair_right_ref` fields.

Every v2 record includes a separately hash-closed tie authority with:

- schema version 1 and scope `cell_interval`;
- ordered left and right coefficient references;
- relation type `symbolic_identity`, `common_inactive_branch` or
  `tolerance_certified`;
- tolerance-contract, structural-lineage, boundary and interval authority
  hashes; and
- provenance over the complete tie-authority payload.

All v2 authority hashes are lowercase SHA-256 strings. Symbolic identity requires
identical pair references. Common-inactive-branch and tolerance-certified
relations require distinct references. Point-only scope, incomplete lineage,
wrong or reordered references, noncanonical fractions, altered coefficient
records, missing competitors, nonfinite inputs, unsupported versions and forged
provenance fail closed. Hash equality is never treated as the general definition
of a tie.

A compatibility loader dispatches on schema version. Version 1 values are passed
unchanged to the historical R9X loader and exposed to callers as
`historical_v1_exact_identity`; they are not rewritten or upgraded. Distinct
pair references require version 2.

## Geometry-free bound contract

A synthetic-only bound routine accepts only a validated loaded authority. It
bounds the two pair functions independently on the authorized cell, compares
each with every competitor and constructs a conservative interval for their
maximum. It never replaces a distinct pair with one representative and never
uses the tie relation as numerical equality. It returns one of
`complete_dominance`, `competitor_dominance`, `mixed` or `unresolved`, along
with work counts and tie provenance. This is validation of future evidence
sufficiency, not empirical terminal-cell analysis and not a change to R9X
classification.

## Prospective failure boundary

The repair composes the existing R9M `FailureController` through a sealed
captured-failure descriptor. For every future acquisition exception it must:

1. durably create and synchronize the traceback;
2. bind its SHA-256 into create-once original and emergency records;
3. validate those records before any blocked-QC or publication callback;
4. invoke blocked-QC before normal publication;
5. preserve publication or QC failures through the separate R9M publication
   failure path without changing original evidence; and
6. re-raise the original exception with its original traceback only after the
   preceding steps.

The sealed descriptor is required by downstream callbacks and cannot be
constructed by callers. The historical R9Y traceback remains unavailable; the
repair is prospective only.

## Synthetic acceptance and evidence

Schema controls cover duplicate pairs, distinct common-branch and
tolerance-certified pairs, point-only authority, missing lineage, wrong
tolerance hashes, reference reordering, coefficient tampering, missing
competitors, unsupported versions, deterministic v2 round trips, historical v1
loading and a geometry-free distinct-pair bound. Failure controls cover lineage,
materialization, coefficient derivation, authority construction, validation,
publication initialization, blocked-QC, publisher and re-raise failures. All
negative controls must fail closed.

The isolated runner exposes only `preflight`, `audit` and `publication-check`.
Commit 2 must pass distribution, Python 3.11 and Python 3.13 CI before a
create-once offline receipt authorizes one governed synthetic audit. The runner
contains tripwires against empirical and numerical routes.

Public output is exactly eight files under
`outputs/continuous_occlusion_terminal_cell_pair_schema_repair/`:

- `repair_contract.json`
- `schema_v2.json`
- `compatibility_matrix.csv`
- `synthetic_pair_controls.csv`
- `traceback_controls.csv`
- `historical_preservation.json`
- `qc.json`
- `manifest.json`

Exact synthetic coefficients and tracebacks remain ignored and hash-bound.
Publication checking reads persisted evidence only and cannot rerun controls.

## Decisions, validation and stop rules

Classification **A / readiness 1** requires the v2 contract, v1 compatibility,
independent distinct-pair bound, all negative controls, ordered traceback
capture, historical preservation, zero access and all delivery gates. **B /
readiness 2** means only the schema repair is complete. **C / readiness 2**
means only traceback repair is complete. **D / readiness 4** means execution or
integrity is incomplete or invalid.

Validation includes focused R9AA, R9X, R9Y, R9Z, R9M and R9J tests; full active
and clean tracked-only suites; compilation; canonical schemas and hashes; finite
JSON; privacy and access guards; documentation links; historical-byte checks;
staged inspection; and `git diff --check`. Final distribution, Python 3.11 and
Python 3.13 CI must pass.

The commit chronology is protocol, tested repair and closed evidence. An
unexpected governed-audit failure is preserved without repair or repetition.
No acquisition follows R9AA.

On A/readiness 1, recommend exactly: **separately govern one bounded
TerminalCellAuthority acquisition using the repaired pair schema, then stop
before terminal-cell refinement.** Do not execute that acquisition.
