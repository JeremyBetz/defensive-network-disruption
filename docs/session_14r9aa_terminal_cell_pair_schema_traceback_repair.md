# Session 14R9AA — Terminal-cell pair-authority schema and failure-traceback repair

## Decision

Session 14R9AA closes **A / readiness 1 / execution valid**. The prospective,
synthetic-only repair supports distinct tied-function authority while preserving
the historical version-1 contract, and it captures and validates an original
traceback before any blocked-QC or publication callback can run.

The sole recommendation is: **separately govern one bounded
TerminalCellAuthority acquisition using the repaired pair schema, then stop
before terminal-cell refinement.** This acquisition was not executed.

## Version-2 pair authority

The new internal `TerminalCellAuthority` version 2 uses integer schema version
`2` and serialization identifier `canonical-json-v2`. It preserves the existing
cell, coefficient, competitor, formula and source-authority fields while adding
ordered `pair_left_ref` and `pair_right_ref` values and a separately hash-closed,
interval-scoped `tie_authority`.

The supported relations are `symbolic_identity`, `common_inactive_branch` and
`tolerance_certified`. Symbolic identity requires identical coefficient hashes.
The other relations require distinct ordered references and complete tolerance,
structural-lineage, boundary and interval authority hashes. Point-only ties,
missing lineage, changed order, altered coefficients, noncanonical fractions,
unsupported versions and forged provenance all block. Hash equality is not the
general definition of a tie.

The compatibility loader dispatches historical version-1 records through the
unchanged R9X loader and labels accepted records
`historical_v1_exact_identity`. It neither rewrites nor upgrades version-1
bytes. Distinct-pair authority requires version 2.

The geometry-free terminal bound evaluates the left and right pair functions
independently and compares both with every competitor. The tie relation remains
provenance; only validated symbolic identity permits identical-value treatment.
Synthetic controls exercised all four bounded outcomes: complete dominance,
competitor dominance, mixed behavior and unresolved evidence.

## Failure-traceback boundary

The new acquisition-failure boundary wraps the existing R9M failure controller.
It captures exception type, message, stage, context and traceback; durably
creates and synchronizes the traceback; binds that hash into immutable original
and emergency records; validates the sealed descriptor; and only then calls
blocked-QC and publication handlers. Callback failures are retained as separate
publication-failure evidence and cannot alter the original record. Re-raise
controls preserve the original exception and traceback.

Nine synthetic controls covered lineage review, materialization, coefficient
derivation, authority construction, validation, publication initialization,
blocked-QC failure, publisher failure and re-raise. Every control passed, and
all observed callback sequences placed validated capture first. The historical
R9Y traceback remains unavailable and was not recreated.

## Governed acceptance and preservation

The protocol was frozen at commit
`e6d4e4366114857606dd03fc2d52b2b23d9e656e`; its SHA-256 is
`67ab53650bf1c483cea322156b74313806df173b2f914dba697198c6c662aba4`.
The tested implementation was committed at
`c2347c5fe93f77413301e24d2626aa97d4f7b91b` and pushed before acceptance.
GitHub Actions run `35797328120` passed distribution, Python 3.11 and Python
3.13 for that exact commit. Its canonical create-once offline receipt has
SHA-256 `dd38c4eb9be276a404d6a3d5860bcfee1383d6690e892169e41fea92299e4a72`.

One governed synthetic audit then ran. All 17 schema, compatibility, negative
and geometry-free-bound controls passed. All nine traceback controls passed.
The audit produced exactly the eight frozen public artifacts, and persisted
publication validation returned A/readiness 1 with all hashes and cross-file
relationships valid.

Historical R9X, R9Y and R9Z evidence and the version-1 implementation remain
unchanged. Sixteen bound historical files matched their frozen hashes. No
dependency, released API, numerical formula, tolerance, certificate or release
metadata changed.

## Access and claim boundaries

R9AA reopened **0 states and 0 edges**. It performed zero acquisitions, field
evaluations, refinements, maximality classifications and empirical
computations. Access tripwires excluded retained-edge, boundary,
prepared-population, provider, field-evaluation, refinement and classification
routes. The work produces no scientific result and makes no claim-ledger
change.

## Validation and chronology

Focused R9AA validation passed 11/11 tests. The relevant R9X, R9Y, R9Z, R9M
and R9J regression set passed 114/114 tests. The active suite and a clean
tracked-only clone each ran **1,310 tests: 1,307 passed and 3 retained skips**.
Compilation, deterministic serialization, schemas and hashes, finite JSON,
privacy and access guards, documentation links, historical-byte preservation,
staged inspection and `git diff --check` passed. Checkpoint CI passed
distribution, Python 3.11 and Python 3.13; final CI is reported after the
closure commit.

The preserved chronology is:

1. `research: freeze terminal-cell pair-schema repair`
2. `fix: support distinct tied-function authority and preserve tracebacks`
3. `research: close terminal-cell pair-schema repair`

The [manifest](../outputs/continuous_occlusion_terminal_cell_pair_schema_repair/manifest.json)
hash-closes the eight-file public package.
