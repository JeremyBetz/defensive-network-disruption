# Phase 14ae — State-lifecycle accounting and publication validation

Prospective authority, 2026-09-12. Start from clean synchronized commit
`3a24f985e2069faff28b5459c6f8f6839e5ba9ce`; preserve release `v0.1.0` at
`f00690c05d8c1c6db308a65bd311c43f9a8ef2fa` and every historical Session 14
artifact.

## Question and boundary

This synthetic orchestration phase asks how preparation, evaluation start,
evaluation completion, edge progress, failure, and access must be represented so
that impossible combinations cannot be produced or published. Session 14R3
remains historically **D — BLOCKED / readiness 3**. Its runner, report, protocol,
manifest, numerical authority, visual, tests, and private stopped records are not
rewritten or rerun.

No development geometry, provider record, target, outcome, model, option share,
protected/reserved/withheld material, pose, xT, progression record, or Session
14R3 partial scientific output may be opened. Numerical formulas, integration,
references, dependencies, released APIs, claims, and field behavior are outside
this phase.

The preserved R3 defect is exact: preparation incremented an incidental row
counter; a failure path passed that value as `states_completed`; and publication
validation checked type and nonnegativity without enforcing the state lifecycle.
One synthetic row was therefore reported as one completed state despite zero
state evaluations, zero edge evaluations, and zero real empirical access.

## Authoritative lifecycle

Each state is registered once with a stable synthetic key and a nonempty,
immutable ordered set of required edge keys. Its processing lifecycle is:

```text
discovered -> prepared -> evaluation_started -> evaluation_completed
```

Each registered edge belongs to exactly one state and follows:

```text
discovered -> evaluation_started -> evaluation_completed
```

Failure is orthogonal terminal evidence attached to the latest reached stage; it
is not a substitute for a successful transition. A failed entity cannot advance.
The public terminal run status is exactly `success`, `failure`, or `blocked`.
An internal active run is not publishable.

A state reaches `evaluation_completed` only at the single lifecycle transition
after every required edge has completed successfully. Entering or leaving a
loop, preparing a row, or starting its first edge never implies completion.
Duplicate, skipped, reversed, or late transitions fail closed.

The single progress object derives these counters from its state and edge
records; callers cannot mutate totals:

- `states_discovered`, `states_prepared`, `states_evaluation_started`,
  `states_completed`;
- `edges_discovered`, `edges_evaluation_started`, `edges_completed`;
- `state_failures`, `edge_failures`;
- `states_opened`, `edges_opened`.

The required ordering is:

```text
states_completed <= states_evaluation_started <= states_prepared <= states_discovered
edges_completed <= edges_evaluation_started <= edges_discovered
```

Failures during state preparation count only preparations already completed.
Failure immediately after preparation leaves evaluation-started and completed
counts at zero. Starting an edge requires its parent evaluation to have started.
Failure during an edge marks that edge and its parent state failed, retains prior
completed edges, and leaves the state incomplete. Failure before an edge is
active marks only the current state when one exists.

## Access and terminal semantics

Access is separate from processing. `states_opened` and `edges_opened` count
actual empirical state or edge records opened after explicit access authorization;
synthetic discovery, preparation, queuing, and evaluation do not increment them.
An opened edge requires its registered parent state to have been opened. Opened
counts cannot exceed discovered counts. Session 14ae's governed audit must retain
zero real state opens and zero real edge opens. Nonzero access examples are
hypothetical isolated oracles and are labeled synthetic.

`success` requires at least one discovered state, every state prepared, started,
and completed, every required edge started and completed, no entity failures,
no active entity, and no exception. `failure` requires a failure stage and
exception. It may preserve fully completed processing only when the failure stage
is publication validation. `blocked` requires a reason and may preserve any
internally consistent partial lifecycle. Neither failure nor blocked status may
invent completion.

An exclusive persistent audit marker is claimed before the governed audit.
Collision or a prior terminal record blocks execution. Any unexpected failure
is atomically preserved with stage, sanitized exception category, private
traceback, lifecycle snapshot, active state/edge, access totals, and completed
work. The governed audit is never resumed or automatically rerun.

## Publication contract

The canonical lifecycle snapshot is the sole source of truth. It uses sorted JSON
with finite values and a trailing LF; its SHA-256 binds every public representation.
QC contains the complete snapshot. The manifest, success evidence, failure
evidence, and report-facing machine summary carry its digest and may not restate
different counters.

The validator requires the exact counter schema and enforces lifecycle ordering,
parent/child completion, failure counts, active-entity consistency, access
authorization and stage consistency, terminal status, and complete success. It
rejects missing or invented counts. In particular, prepared 1 / evaluation
started 0 / completed 1 is invalid. It also rejects completed edges beyond
started edges, success with incomplete work, success with failures, failure
without evidence, access before authorization, and any cross-file digest or
status mismatch. Both success and stopped packages have strict schemas.

## Synthetic authority and stop

Before the one governed audit, discoverable tests cover the exact R3 regression;
preparation-only and every failure stage; partial edge completion; one- and
multi-state success; parent/child and transition rejection; valid and invalid
publication records; synthetic access 0/0, 1/0, and 1/1; cross-file mismatches;
failure preservation; marker collision; rerun rejection; and zero empirical
access spies. Source firewalls must show no numerical, model, acquisition,
target, outcome, scoring, or empirical route.

The governed audit executes the frozen oracle set and one success control once,
then atomically writes and hash-closes exactly the files specified by the Session
14ae handoff under `outputs/session14_state_lifecycle_accounting/`. Publication
checking validates existing bytes and never regenerates or rebinds them. A defect
after exposure is preserved and stops the phase without repair.

Classification is **A — STATE-LIFECYCLE ACCOUNTING AND PUBLICATION VALIDATION
REPAIRED** only when every lifecycle, failure, access, cross-file, and success
gate passes. **B** means counter lifecycle ambiguity; **C** incomplete publication
enforcement; **D** cross-file inconsistency; **E** multiple defects; **F**
unresolved evidence; **G** execution or integrity failure. Readiness 1 requires
A; otherwise readiness 2–4 follows the observed blocker.

On A/readiness 1 the sole recommendation is: **separately govern a fresh Session
14R empirical representation retry using the repaired lifecycle-accounting and
publication-validation contract.** This phase does not execute that retry.
