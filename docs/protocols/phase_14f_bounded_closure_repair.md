# Phase 14f — Bounded closure repair

## Authority and purpose

This protocol starts from local `8ccbd79fc53579a8e759f703b554e0213ec72e9d`,
which preserves the three unpushed Session 14e commits above remote
`9188222c4270ba1a89963ae1bbdb9003b0bf9f1e`. Session 14e remains historically
**INVALID — REPAIR/AUDIT EXECUTION FAILURE** because its final range-level
`git diff --check` detected one extra blank line at EOF after governed synthetic
output exposure.

Session 14f answers only whether that closure defect can be removed without
changing Python semantics and whether the already exposed Session 14e evidence
may be inherited under a new authority. It does not rerun the governed numerical
acceptance audit. It accesses no empirical data, provider product, target,
model, option share, protected or withheld data, pose, xT, or progression work.
Session 14R remains paused.

## Exact permitted patch

The sole implementation file is
`src/defensive_network_disruption/geometry/verification_repair.py`. The sole
permitted change is deletion of the final empty line after the
`independent_continuity` return statement. No other whitespace normalization,
formatting, import change, refactor, docstring change, test change, formula,
tolerance, fixture, reference, verification semantic, or readiness change is
authorized.

The pre-repair file SHA-256 is
`4af39780b23e13f98a6ec54102b1aba4071d3a72b599ee3ca7ecc820f37118a2`.
The before bytes are retained from commit `d22f459`; the repaired bytes will be
recorded prospectively by the Session 14f closure metadata.

## Semantic-equivalence contract

The staged textual diff must contain exactly one deletion: the empty EOF line.
The before and after source must parse to identical Python ASTs when positional
attributes are excluded. Recursively compared compiled module code objects must
have identical executable bytecode, constants (including nested code objects),
names, variable names, flags, argument counts, free/cell variables, and exception
tables. Source-position tables and source-file metadata are excluded because the
change is after the final statement. Module import must succeed before and after,
and the public/internal symbol set and runtime-visible constants must match.

Any semantic difference stops the repair. The historical Session 14e outputs
must not be reused in that case.

## Evidence inheritance and governance

All Session 14e numerical files, readiness output, failure injections, QC,
manifest, and report remain byte-identical. The historical manifest continues
to identify the producing source hash and is not overwritten or rebound.
Session 14f creates a distinct closure manifest binding:

- the historical implementation and evidence hashes;
- the repaired implementation hash;
- the exact one-line diff;
- AST, compiled-code, import, constant, and symbol equivalence results;
- repository validation and history preservation.

For this closure-only phase, evidence inheritance is permitted when the exact
patch is proven non-semantic by every frozen equivalence check, all inherited
evidence hashes remain unchanged, and all repository validation gates pass.
This later authority does not rewrite Session 14e's invalid status; it establishes
that its preserved numerical evidence remains applicable to the semantically
identical repaired implementation. If any condition is absent or unclear,
inheritance is blocked or unresolved and no numerical rerun occurs.

## Validation and outputs

Validation comprises `git diff --check`, focused tests, the relevant Session 14
series, the documented full active suite, compilation, semantic equivalence,
existing Session 14e schema/hash and publication checks, privacy and link checks,
append-only history, staged inspection, and CI after push. These are validation
checks, not a new governed numerical execution.

The new public namespace is
`outputs/continuous_occlusion_closure_repair/` and contains exactly
`repair_summary.json`, `semantic_equivalence.json`, `inherited_evidence.json`,
`qc.json`, and `manifest.json`. Outputs must be finite, schema-checked,
publication-safe, atomically written, and hash-bound. Detailed temporary compiled
objects and execution records remain ignored.

The result is **PASS — CLOSURE REPAIR VALID; SESSION 14e ACCEPTANCE EVIDENCE MAY
BE INHERITED** only when the patch is exact, semantic equivalence is established,
all evidence hashes are unchanged, every repository gate passes, and inheritance
is authorized above. Otherwise return BLOCKED, INVALID, or UNRESOLVED as frozen
in the handoff. PASS permits only resuming Session 14R under the repaired and
audited contract; this phase does not execute it.

## Chronology and stop rule

Commit this protocol before touching the offending file. Then apply the single
deletion, run equivalence and validation, and commit the repair plus closure
evidence without amending any Session 14e commit. Push the three preserved
Session 14e commits and new Session 14f commits only after all checks pass.
Verify clean synchronized local/tracking/live heads and the unchanged release
tag, then stop. A failed bound or integrity check is preserved without expanding
the patch or silently rerunning Session 14e.
