# Phase 14R9Y — Bounded terminal-cell authority acquisition

## Authority and purpose

This protocol prospectively authorizes one acquisition of the mathematical
authority missing from Session 14R9V's unresolved constant-width terminal cell.
It begins from clean synchronized commit
`c12f86a3b3441f0845fae5a0e9989d00b73e141a`. Distribution, Python 3.11 and
Python 3.13 CI for that commit are green. The annotated `v0.1.0` tag must still
peel to `f00690c05d8c1c6db308a65bd311c43f9a8ef2fa` before access.

R9V remains NF/PA/readiness 3. R9X remains A/readiness 1 with zero empirical
access. R9Y may reopen only R9V's already retained selected-edge copy and must
stop immediately after one immutable `TerminalCellAuthority` is written and
validated. It may not refine or classify the cell, evaluate a field, rerun the
independent reference, diagnose maximality, change numerical code or inspect
another record.

## Frozen lineage and schema

The retained lineage is rooted at R9V private-index SHA-256
`2abe5f916265275a94c157bd1a93c55f96d352863cbdce618a40418af3a2ebc6`.
Within that index, `boundary_capture.json` is
`30a8363749bb07053cdd35f82248535ebc1909441274a9da572ba684de7f597b` and
`selected_edge.json` is
`04bfd87303522ced4968d7953228d2bc8a289a2fab28d823cfd1c7deff8aa51f`.
The ordered partition consists of exactly 81 indexed `reference_reference_cell`
records, with one unresolved record at ordinal 36 and depth 80. The complete
private index binds every record name and byte hash; changing, adding, removing
or reordering authority blocks acquisition.

R9X manifest SHA-256, minimum-schema SHA-256 and synthetic-sufficiency SHA-256
must match their committed bytes. The reference implementation is the committed
R9V constant-width reference source and must match its preflight hash. The
terminal authority uses R9X schema version 1, `canonical-json-v1`, canonical
lowest-terms signed-decimal fractions and formula authority
`031e01934e5a5954a9ef3f2ac4eff536072ccca26db56efbe7d47cd8913ffdc6`.

The authority contains only the cell ordinal and depth; exact rational bounds;
candidate/formula authority; canonical exact `q`, `dot` and `cross2`
coefficient records; pair and competitor coefficient-hash references; the R9V
private-index, boundary-capture, ordered-partition, selected-edge and reference-
implementation hashes; schema/serialization versions; and provenance hash.
Identities, raw coordinates, provider rows, evaluated values, enclosures,
production owners and unrelated metadata are forbidden.

## Acquisition sequence

Before selected-edge contents are read, the tested implementation checkpoint
must have green distribution, Python 3.11 and Python 3.13 CI, a clean synchronized
HEAD, the unchanged release tag, fresh create-once markers and exact inherited
hashes. Failure of any gate stops with zero reopened exposure.

The single governed acquisition then:

1. persists a review receipt for the validated private index and its 81 cells;
2. persists an access attempt, reads only the hash-bound retained selected-edge
   copy and persists its materialization receipt;
3. derives the unresolved leaf bounds from the retained outer interval and the
   complete ordered depth sequence through R9X `derive_leaf_bounds`;
4. converts only the required binary64 geometry to exact rational `q`, `dot`
   and `cross2` coefficient records, deduplicating by canonical hash;
5. creates one immutable version-1 authority and validates it with
   `load_authority`, exact canonical bytes, references, provenance and a
   serialize-load-serialize round trip; and
6. closes publication and stops.

`classify_terminal`, coefficient bounds, field callbacks, refinement and every
TA/TB/TC/TD/TE result are forbidden. Successful materialization records one
previously exposed state and one previously exposed edge reopened, zero new
population exposure, zero candidate evaluations and zero empirical field
computations. Interrupted materialization leaves exposure uncertain and blocks.

## Evidence, decisions and stop rule

Public output is exactly six files in
`outputs/continuous_occlusion_terminal_cell_authority_acquisition/`:
`acquisition_contract.json`, `lineage_validation.json`,
`authority_capture.json`, `sufficiency_validation.json`, `qc.json` and
`manifest.json`. Exact bounds, coefficients and access records remain ignored
and hash-bound. Publication validates existing bytes and cannot regenerate
evidence.

Classification A/readiness 1 requires exact lineage, exact bound derivation,
complete coefficient authority, one valid immutable authority, structural-only
R9X loader acceptance, exact reopened exposure, zero refinement/classification
and green delivery. B/readiness 2 means capture with incomplete validation;
C/readiness 3 means the authority is not derivable within scope; D/readiness 4
means invalid or blocked execution.

Any post-access failure stops without repair, another read or rerun. A successful
phase may recommend only: **separately govern the terminal-cell independent
bound using only the newly retained TerminalCellAuthority, with zero empirical
reopening.** It must not execute that bound.
