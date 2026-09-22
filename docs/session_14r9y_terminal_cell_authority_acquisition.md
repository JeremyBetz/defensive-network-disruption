# Session 14R9Y — Bounded terminal-cell authority acquisition

## Decision

Session 14R9Y closes **D — execution blocked / readiness 4**. The one governed
acquisition validated the retained R9V lineage, reopened exactly one previously
exposed state and edge, derived the unresolved cell bounds, and then stopped
while constructing the private authority with `ValueError: pair_authority`.
No `TerminalCellAuthority` was created. The execution performed zero field
evaluations, zero refinements, zero empirical classifications, and exposed zero
new population states or edges. The acquisition was not repaired or repeated.

The sole recommendation is: **separately govern one bounded diagnosis of the
terminal-cell pair-authority identity mismatch using the retained R9Y evidence,
with zero further empirical reopening.** This recommendation was not executed.

## Frozen authority and checkpoint

The protocol was frozen before retained access at commit `dfb6f33`. The tested
tooling commit `cf5eb24` passed 1,292 tests in both the working repository and a
clean tracked checkout. Its first offline preflight exposed a pre-access-only
receipt-sidecar naming mismatch. No marker or retained read existed. Published
history was preserved; corrective commit `dbe65cd` changed only the runner's
receipt name and its focused regression test. Distribution, Python 3.11, and
Python 3.13 CI then passed on that exact corrected commit, and the content-bound
offline receipt validated before the governed acquisition.

## Governed acquisition

The retained private index, boundary capture, ordered 81-leaf partition,
selected-edge copy, unresolved cell identity, and reference implementation all
passed their frozen checks. Durable access-attempt and materialization receipts
were written before and after reading the allowlisted selected-edge copy. This
records one previously exposed state and edge reopened, with no new population
exposure.

The tool derived exact cell bounds and coefficient records without evaluating
the field. Authority construction then rejected the tied-pair references because
the implementation required the pair's coefficient records to satisfy an exact
symbolic-identity invariant. That requirement was not established by the frozen
R9Y plan for a tolerance-certified tied pair. The runner also lacked a complete
exception-capture path for this stage, so the original exception type, message,
and stage were preserved while the exact traceback is explicitly unavailable.
These are execution-integrity defects, so the result is D/readiness 4 rather
than a claim that the required mathematical authority cannot exist.

## Evidence and privacy

The six public artifacts contain only sanitized hashes, statuses, counts, and
flags. The selected geometry, exact fractions, coefficients, pair references,
access records, and lineage details remain ignored and hash-bound. The persisted
package validates with one reopened state, one reopened edge, zero new states,
zero new edges, zero field evaluations, no refinement, and no classification.
R9V and R9X files remain unchanged.

## Validation and chronology

Focused R9Y/R9X tests passed 20/20 before checkpointing; relevant R9V–R9Y tests
passed 35/35. The active suite and clean tracked checkout each ran **1,292 tests:
1,289 passed and 3 retained skips**. The corrective regression ran 6/6. Both
checkpoint CI runs passed distribution, Python 3.11, and Python 3.13; only the
corrected exact-commit receipt authorized access. Compilation, diff checks,
canonical serialization, schema/hash checks, privacy guards, historical
preservation, and persisted publication validation passed.

The final chronology contains four commits without rewriting published history:

1. `research: freeze terminal-cell authority acquisition`
2. `research: capture retained terminal-cell authority`
3. `fix: align R9Y checkpoint receipt sidecar`
4. `research: close terminal-cell authority acquisition`

The [manifest](../outputs/continuous_occlusion_terminal_cell_authority_acquisition/manifest.json)
hash-closes the blocked six-file package.
