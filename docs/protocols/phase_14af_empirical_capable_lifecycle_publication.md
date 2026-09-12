# Phase 14af — Empirical-capable lifecycle and publication authority

Prospective authority, 2026-09-12. Start from clean synchronized commit
`010bc8876c2abad227ff969c8e2655d96a3f397e`; preserve release `v0.1.0` at
`f00690c05d8c1c6db308a65bd311c43f9a8ef2fa` and every historical Session 14
artifact.

## Question, qualification, and boundary

This synthetic orchestration phase asks whether the Session 14ae lifecycle can
support empirical packages with nonzero access, preserve partial progress after
unexpected failure, and reject actual cross-file inconsistencies. Session 14R4
remains paused.

Session 14ae remains historically **A — STATE-LIFECYCLE ACCOUNTING AND
PUBLICATION VALIDATION REPAIRED / readiness 1**. Prospectively, its result is
qualified as follows: **Session 14ae established a valid synthetic lifecycle
model and zero-access pre-empirical accounting behavior, but did not fully
establish empirical-capable cross-file publication validation or
partial-progress preservation under unexpected nonzero-access failure.** Its
files are not rewritten or downgraded.

The three bounded gaps are frozen:

1. its governed cross-file rejection evidence recorded fixed expected strings
   rather than executing every mutation through the real validator;
2. its general `validate_cross_file()` requires zero state and edge access and
   therefore rejects legitimate empirical partial or complete packages; and
3. its unexpected-failure path retained a traceback and generic zero-access
   constants rather than the active lifecycle snapshot, completed work, active
   context, and access already incurred.

No development or provider data, empirical geometry, target, outcome, model,
option share, protected/reserved/withheld material, pose, xT, progression data,
or Session 14R partial scientific output may be opened. Field formulas,
integration, numerical references, dependencies, released APIs, claims, and
scientific authorities are outside this phase.

## Lifecycle and access authority

The unchanged Session 14ae processing lifecycle remains:

```text
state: discovered -> prepared -> evaluation_started -> evaluation_completed
edge:  discovered -> evaluation_started -> evaluation_completed
```

A state completes only after all registered required edges complete. Failure is
orthogonal terminal evidence and does not imply completion. The progress object
derives all counters and enforces:

```text
states_completed <= states_evaluation_started <= states_prepared <= states_discovered
edges_completed <= edges_evaluation_started <= edges_discovered
```

Access is an independent historical fact. Successful state and edge opens are
appended to a private, hash-chained journal. Public open counts are derived from
that journal and the lifecycle records; callers cannot set them. An edge open
requires its parent state to have opened. Failure cannot reset an open event.
The validator rejects a package whose public counters disagree with the journal,
including a consistently rewritten public `0/0` view after nonzero access.

The journal is append-only, has deterministic canonical JSON entries, binds each
entry to its predecessor, and is retained privately. Public packages bind the
journal digest and bounded derived counts without publishing state or edge keys.

## Explicit validation contexts

Package type is explicit and is never inferred only from access counts:

- `pre_access` requires zero opened states and edges and an internally valid
  terminal lifecycle.
- `empirical_partial` validates an internally consistent incomplete checkpoint
  or blocked package. It may retain nonzero access but cannot be published as a
  successful closure.
- `empirical_failure` requires terminal failure evidence, the reached lifecycle,
  failure stage, preserved traceback in private evidence, access history, and
  active state or edge when the failure occurred during an active operation.
- `empirical_success` requires nonempty complete state and edge work, zero
  failures, no active item, and access consistent with the completed empirical
  work.

Nonzero access is valid in empirical contexts when the journal, lifecycle, and
package views agree. Pre-access remains strictly zero-access. The generic
contract does not hard-code a future population size.

## Failure preservation

After lifecycle initialization, an unexpected-failure boundary captures the
canonical pre-failure snapshot, marks the actual active state or edge failed,
and captures the terminal snapshot. It retains the failure stage, sanitized
exception category, completed work, open counts, journal digest, and a private
traceback. It never reconstructs progress from a loop counter or exception
location. Failure after an edge completes but before its state completes retains
that completed edge and the active state without inventing an active edge.

Failure before lifecycle initialization is a distinct pre-initialization record:
it has no invented lifecycle, zero access derived from an empty journal, and a
private traceback. Exclusive markers reject concurrent invocation and automatic
rerun.

## Canonical publication contract

The canonical lifecycle snapshot remains the processing source of truth. Its
sorted finite JSON SHA-256 binds every reporting view. The journal independently
binds access history. QC, manifest, evidence, and report-facing machine views
must carry an identical progress authority comprising validation mode, status,
initialization state, lifecycle snapshot and digest, journal digest, derived
open counts, active context, and failure stage.

The cross-file validator recomputes the lifecycle digest from the actual
snapshot and recomputes journal integrity and access counts from the supplied
private journal. It compares actual common fields across all files. It rejects
changed status, lifecycle, counters, access, active state, active edge, failure
stage, lifecycle hash, journal hash, success claims paired with failure evidence,
pre-access nonzero access, and any access reset hidden behind mutually consistent
public files. Missing totals or unavailable evidence cannot become PASS.

Every frozen invalid cross-file case is constructed and passed to this real
validator during the governed audit. Expected-result strings are insufficient.

## Synthetic controls and R4 compatibility

Before the governed audit, discoverable tests cover mode semantics; access
journaling; zero and nonzero access; partial failure and complete success;
hash, status, counter, active-context, failure-stage, and access mismatches;
failure before and after initialization; unexpected failure after completed and
partial work; access reset rejection; exclusive markers; and cross-file
consistency.

The audit executes exactly once after the tested implementation is committed.
It runs these controls without real data:

1. a valid pre-access package with prepared synthetic states and `0/0` opens;
2. a valid three-state empirical failure with one completed state, a second
   active state and edge, prior completed edges, and nonzero opens;
3. a valid complete multi-state empirical success with nonzero opens;
4. the actual unexpected-failure boundary after partial synthetic progress;
5. all frozen invalid cross-file mutations through the real validator; and
6. an R4-style sequence from fail-closed launch through authorization,
   lifecycle initialization, nonzero synthetic access, partial evaluation,
   unexpected failure, and accepted failure publication.

The R4 compatibility control may use synthetic callbacks and temporary
authority files only. It opens no population, data handle, field route, model,
or scientific summary. Session 14af's real audit reports zero real states and
edges opened even though isolated controls simulate nonzero access.

## Outputs, decision, and stop

The runner exposes `preflight`, `audit`, and `publication-check`. It writes the
frozen public files under `outputs/session14_empirical_lifecycle_publication/`
atomically with strict schemas, LF CSV, finite values, sanitized identifiers,
and a hash-bound manifest. Private journals, tracebacks, tokens, and execution
records remain ignored. Publication checking validates existing bytes and never
recreates or rebinds evidence.

Classification is **A — EMPIRICAL-CAPABLE LIFECYCLE / PUBLICATION AUTHORITY
ESTABLISHED** only when the governed invalid packages are actually rejected,
valid pre-access, partial-failure, and success packages are accepted,
unexpected failure preserves progress/access/context/traceback, R4-style
compatibility passes, and real access stays zero. **B** means access accounting
remains incomplete; **C** failure preservation remains incomplete; **D**
cross-file validation remains incomplete; **E** the validator cannot support
empirical packages; **F** multiple issues; **G** unresolved; and **H** invalid
or failed execution. Readiness 1 requires A; readiness 2–4 follows the observed
blocker.

A defect after governed output exposure is preserved and stops the phase without
repair or rerun. On A/readiness 1 the sole recommendation is: **separately govern
a fresh Session 14R empirical representation retry using the empirical-capable
lifecycle/publication authority.** This phase does not execute that retry.
