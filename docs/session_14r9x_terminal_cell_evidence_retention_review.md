# Session 14R9X — Terminal-cell evidence-retention authority review

## Decision

Session 14R9X closes **A — sufficient private terminal-cell authority defined / readiness 1**. The governed review was metadata-only: it accessed **0 empirical states and 0 empirical edges**, performed no field evaluation, and did not open prepared data or the retained selected-edge contents. R9V remains **NF / PA / readiness 3**. The uncommitted R9W read-only stop is recorded as **TE / NF / readiness 4**.

The sole recommendation is: **separately govern one bounded retained-edge evidence-acquisition phase that captures only the missing terminal-cell mathematical authority, then stop before refinement.** This recommendation was not executed.

## Evidence-loss trace

Static source tracing and the hash-validated R9V categorical records establish the loss boundary. During R9V, `Cell.left`, `Cell.right`, the `FieldAuthority` objects, pair authority, and computed enclosures existed in memory. The `reference_cell` sink reduced each leaf to ordinal, depth, pair status, and maximum status. The 81 retained records therefore preserve 36 maximum, 44 dominated, and one unresolved classification, but do not preserve the mathematical inputs required to refine the unresolved cell.

Exact leaf bounds are prospectively derivable from the retained outer plateau bounds and the complete ordered leaf-depth sequence. R9W correctly declined to reconstruct them because no prospective derivation contract then existed. Field authority is not derivable from the cell records. It must be recreated from the already retained selected-edge copy, so a future acquisition must report one previously exposed state and one previously exposed edge reopened.

## Minimum immutable authority

The versioned private `TerminalCellAuthority` stores the cell ordinal and depth; exact rational lower and upper bounds; constant-width formula authority; canonical coefficient records containing exact `q`, `dot`, and `cross2`; pair and competitor references by coefficient-record hash; the R9V private-index, boundary-capture, ordered-partition, selected-edge, and independent-reference implementation hashes; a serialization version; and a provenance hash.

The required fields are exact cell bounds, candidate/formula authority, coefficient records, pair and competitor references, source hashes, and schema version. Square-root/alpha/beta quantities, onset branch state, value and derivative bounds, and refinement starting state are derived. Prior enclosures, parent-cell contents, production-owner decisions, and duplicated derived coefficients are redundant. Identities, raw coordinates, tracking rows, provider records, and unrelated source metadata are prohibited.

## Synthetic sufficiency and privacy

The geometry-free loader discards source geometry before reloading the authority. Twelve synthetic controls passed: the five required outcomes—pair maximality, third-defender dominance, dominance switching, interior equality, and unresolved evidence—and seven tampering controls. Altered coefficients or bounds, missing competitors or required fields, wrong source hashes, noncanonical fractions, nonfinite data, and unsupported versions all block. Public artifacts contain only schemas, classifications, flags, counts, and hashes. Exact synthetic coefficients remain test fixtures.

## Bounded future acquisition

The prospective phase is limited to five steps: validate the existing R9V authority; read only the retained selected-edge copy; derive constant-width coefficient authorities without evaluating field values; derive leaf bounds from the validated outer interval and ordered depth partition; write and validate one immutable authority; then stop. Prepared population files, provider data, refinement, classification, and repair remain forbidden. The phase records **1 previously exposed state / 1 previously exposed edge reopened** and **0 new population states / 0 new population edges**.

## Validation and delivery

Focused R9X tests passed **15/15**. Relevant R9R–R9V and publication regressions passed **183/183**. The active suite ran **1,287 tests: 1,284 passed and 3 retained skips**. The corrected tracked-only checkout repeated the same **1,287 / 1,284 / 3** result. Compilation, deterministic serialization, schema/hash closure, finite JSON, privacy guards, documentation links, historical-byte checks, and diff checks passed.

The planned three-commit sequence became four commits without rewriting published history. Commit 1 froze the protocol. Commit 2 added the authority and review tooling. Its tracked-only run exposed one test portability defect: a test read ignored R9V private files directly. Commit 3 was a bounded test-only correction that replaced that dependency with synthetic metadata authority; checkpoint distribution, Python 3.11, and Python 3.13 CI then passed on that exact corrected commit. Commit 4 closes the evidence, report, and log. The correction preceded the governed review and changed neither the retention contract nor the observed R9V evidence.

The eight public artifacts are hash-closed by the [manifest](../outputs/continuous_occlusion_terminal_cell_evidence_retention/manifest.json). The governed package passed its persisted publication check with classification A, readiness 1, and execution validity true.
