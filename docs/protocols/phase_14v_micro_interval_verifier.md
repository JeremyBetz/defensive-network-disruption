# Phase 14v — Independent-verifier micro-interval contract repair

Status: **FROZEN BEFORE REPAIR IMPLEMENTATION OR NUMERICAL EXECUTION**
Date: 2026-09-11

## Authority and bounded question

This phase begins from clean synchronized commit
`cc8cb1a7c5c6706ef9db6e0c74d41c32f7fe54d5`; annotated release `v0.1.0`
must remain at `f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`.
All Session 14-series protocols, implementations, outputs and classifications
remain historical authority. Session 14R remains D/readiness 3 and paused.

Session 14u established that the independent piecewise maximum verifier emits an
`IntegrationWarning` on a valid `3.3306690738754696e-15`-wide structural piece,
while the unchanged joint Simpson estimator converges and six independent
maximum estimates agree within `2.394265341543189e-14`. Session 14v asks only
whether certified machine-scale pieces can be handled by a deterministic bounded
residual contract without changing the production estimator or field.

The authoritative Session 14i, Session 14R and Session 14u manifest SHA-256
values are `1c65769260cc6e1b8a79b69129b3b5a227d4a0a41aec93be4533168a042ace88`,
`8a639f7a2b29a6aec026e176d80d8901b28839b0d2091dd0256751d77b6f70ed`
and `fbcef2b81b9adea67cccd68e9db26990ff3e2825f77ce98a4e37b047b488896d`.
Canonical and prepared population hashes remain
`cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d`
and `15a809060f0ba4a8cb3790011dab8008db3dad6e931c287ccb395f61ef1530b0`.

## Bounded residual contract

The frozen individual fields and both combinations are bounded in `[0,1]`.
Therefore, for the maximum integrand on any normalized piece `[a,b]`,

`0 <= integral_a^b O_max(t) dt <= b-a`.

Freeze the global residual budget at `1e-12`. This is an existing numerical
verification scale and one percent of the strictest independent agreement gate
of `1e-10`; it is not a football or scientific threshold.

For an integral containing `N` positive-width structural pieces, a piece is
bounded-residual eligible exactly when its realized float64 width satisfies

`b - a <= 1e-12 / N`.

Every structural boundary, switch, onset and certified enclosure endpoint is
preserved. Eligible pieces remain structural pieces but are excluded from the
adaptive-quadrature work list. Each contributes the rigorous interval
`[0, b-a]`; no zero, midpoint or point estimate is asserted. Lower and upper
bounds are combined separately with `math.fsum`, ensuring that the total omitted
contribution cannot exceed `1e-12` even when several pieces qualify.

Every other positive-width piece uses the unchanged scalar SciPy quadrature at
`1e-13` and `1e-11`, with the historical work limit. A warning or failure on an
ordinary piece remains blocking. Interval merging is neither implemented nor
evaluated in this phase.

## Interval-aware verification

Let interval distance be zero for overlapping closed intervals and otherwise the
gap between them. Let point-to-interval distance be zero inside the interval and
otherwise the distance to its nearest endpoint.

- Strict and repeat repaired intervals must have interval distance at most
  `1e-10`.
- Onset-only adaptive, direct 65,536-interval Simpson and applicable historical
  split-Simpson estimates must have point-to-interval distance at most their
  unchanged `1e-10`, `1e-9` and `1e-10` gates.
- The unchanged joint Simpson maximum must have point-to-interval distance at
  most the unchanged `1e-6` reference gate.
- The 366-reference synthetic audit retains point comparisons for individual
  and union values. Maximum values use point-to-interval distance and are never
  collapsed to an invented point.

The production joint vector, component order, float64 operations, interval
ladder `256–16384`, first-finer acceptance at `1e-7`, reference values and all
field formulas remain unchanged.

## Synthetic authority and single edge regression

Before governed execution, discoverable tests freeze ordinary, onset-adjacent,
switch-adjacent, endpoint, adjacent and multiple micro-piece fixtures. Boundary
fixtures use realized float64 widths immediately below and above the eligibility
limit via `numpy.nextafter`. Zero, constant-one and bounded analytically
integrable fields verify conservative containment, stable summation,
determinism, structural preservation, ordinary-piece warning propagation,
exclusive markers and failure closure.

The accepted production path must reproduce all 108 frozen cases, 366 component
references and 399 mapped fixture permutations, including unchanged joint
Simpson estimates and accepted interval counts. Commit the tested implementation
before the governed audit.

After those synthetic checks pass, the audit may recover only the already
authorized canonical prepared row ordinal 1, candidate `constant_width`, receiver
ordinal 7, using Session 14u's strict historical-byte equivalence gate. It must
verify the same 12 pieces, one switch, zero tie intervals and zero certified
enclosure endpoints, with the known onset-adjacent micro piece. It must show that
this piece uses the residual interval, all ordinary pieces retain quadrature,
no `IntegrationWarning` occurs, the unchanged joint vector converges at 2,048
intervals and all interval-aware comparisons pass. No other state or edge may be
opened. An unexpected failure is preserved and the audit is not rerun.

## Access, outputs and decision

The runner exposes only `preflight`, `audit` and `publication-check`. It has no
acquisition, model, score, field-search, target, outcome, share, fitting,
rendering or Session 14R route. Detailed geometry, identifiers, traces and
execution records remain ignored. An exclusive persistent marker prevents
concurrent or automatic repeat execution.

Publish under `outputs/continuous_occlusion_micro_interval_verifier/`:

- `contract.json`
- `synthetic_micro_interval_oracles.csv`
- `synthetic_reference_regression.csv`
- `failing_edge_regression.json`
- `residual_summary.json`
- `qc.json`
- `manifest.json`

Choose A only when the bounded-residual repair passes every synthetic obligation
and the single authorized edge without changing the production estimator. D
means evidence is incomplete, E means satisfying the contract requires a
material numerical behavior change, and F means execution or integrity is
invalid. B and C are unavailable because merging is not evaluated. Retry
readiness is 1 only for A; otherwise assign 2–4 from the observed blocker.

Close and hash outputs before interpretation. Preserve three commits: protocol;
tested internal repair; closed evidence/report and append-only research log. Run
focused, relevant and full tests, compilation, numerical regression, schemas,
hashes, privacy, links, history, staged and diff checks, then CI. If and only if
A/readiness 1 is earned, recommend exactly: **separately govern a fresh Session
14R retry under the repaired micro-interval verification contract**. Do not
execute that retry.
