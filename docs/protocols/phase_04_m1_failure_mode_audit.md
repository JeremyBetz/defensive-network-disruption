# P04 — M1 model-behavior and failure-mode audit

Version 1.0, 2026-09-10. Status: **AUTHORIZED AFTER COMMIT**.
Authority: Session 3 commit `3e7e517108a782ede32e7bf55e2dfb020f3c841f`.
Source: SkillCorner Open Data commit
`02a396ffd09b283c9f092fdedeff11da6d535b66`.

Amendment 1, committed before new event-row access: the closed population omits
decision-frame keys, so the runner may project `event_id`, `event_type`,
`pass_outcome`, `period`, `time_end`, `player_id`,
`player_in_possession_id`, and `player_targeted_id` from the same nine development
Dynamic Events files solely to reproduce the frozen population and recover its
decision-frame key. No other event field or event-derived diagnostic is permitted.

## Question and claim boundary

Determine whether the closed static M1 representation has one specific,
football-relevant limitation that justifies a separately prospective M2. This is
a model-behavior and feature-geometry audit, not model development or protected
validation. Session 3 metrics, folds, coefficients, population, and interpretation
remain closed. Accessibility is **PROXY ONLY** and suppression is
**NOT SUPPORTABLE**.

The nine retained coefficient vectors are already public in the closed Session 3
QC artifact. Their inspection during Session 4 planning is recorded as prior
closed-result exposure. This protocol must be committed before any new row-level
development geometry or tracking provenance is inspected.

## Access and prohibitions

Development allowlist: `1886347`, `1899585`, `1925299`, `1996435`, `2006229`,
`2011166`, `2013725`, `2015213`, `2017461`. All other match IDs are rejected
before file open. In particular, the ten reserved matches and withheld match
`1953632` remain prohibited.

Permitted local inputs are the closed Session 3 population and QC artifacts plus
the pinned development metadata, projected Dynamic Events fields listed in
Amendment 1, and `tracking_extrapolated.jsonl` products already acquired in
Session 2. Permitted tracking fields are
`frame`, `period`, `timestamp`, and player `player_id`, `x`, `y`, and
`is_detected`, solely for aggregate past-frame availability and provenance.

Do not access pose, skeletal products, vendor Passing Option scores, new provider
data, reserved or withheld values, individual prediction errors, scored passages,
utilities tied to real attempts, or rankings. Do not refit or rescore M0/M1, call
an optimizer, add a feature to a fitted model, run an ablation, tune a threshold,
or alter the frozen population. No row-level derived data may be committed.

## Frozen diagnostics

Read standardized coefficients and preprocessing parameters from the closed QC
artifact. For every M0/M1 feature report positive, negative, and zero fold counts,
minimum, median, and maximum. Coefficient magnitude is not causal importance.

For every independent candidate connection, reproduce the frozen M1 feature
geometry and calculate the second- and third-nearest opponent distances to the
same finite carrier-receiver segment. Use the analytic clipped projection and its
`1e-9` metre floating-point implementation tolerance. It has no football meaning.

Report stable-alias aggregates:

- equal-match 5th, 25th, 50th, 75th, and 95th percentiles and per-match variance;
- pooled and per-match Pearson and Spearman correlations between the two M1
  defensive features;
- Pearson correlation after centering features within each choice set, weighted
  equally by match, attempt, and candidate;
- pairwise candidate-order disagreement within each choice set, omitting pairs
  tied within absolute `1e-12` in either feature and weighting equally by match
  and then attempt;
- feature-only within-choice covariance rank and condition numbers;
- continuous `d2-d1` and `d3-d1` distributions; and
- pass-length/segment-distance association, current detection provenance, and
  immediately prior-frame structural availability.

No defender-radius count is authorized. Multiplicity is non-degenerate in a match
only when both gap distributions have range above
`max(n, 1) * float64_epsilon * max(absolute_value, 1)`.

Past-frame availability requires the same identity in the immediately preceding
same-period tracking record, finite coordinates at both records, and positive
elapsed time. Report counts by current/previous `is_detected` combination. Do not
calculate or publish velocity values. A future velocity may use backward
difference only. Under the strict gate, timestamp-causal computation does not
prove causal provider processing; A requires authoritative evidence that the
coordinates themselves exclude future-aware smoothing or extrapolation.

## Frozen synthetic cases

Use a carrier at `(0,0)` and receiver at `(40,0)` unless a case specifies another
length. Raw anchors are `0, 1, 2, 5, 10, 20, 40` metres. Transform features with
each retained fold's M1 training mean and scale and calculate utility changes only.
Report median and full fold range; do not call these probabilities.

1. Receiver sweep: segment distance 2 m; receiver distances 2, 5, 10, 20,
   and 40 m; reference 20 m.
2. Segment sweep: receiver distance 20 m; segment distances 0, 1, 2, 5, 10,
   and 20 m; reference 20 m.
3. Joint surface: all anchor pairs with segment distance no greater than receiver
   distance; reference `(20,20)`.
4. Velocity blind spot: identical static positions with equal-magnitude motion
   normal to the lane, once toward and once away; M1 utility must be identical.
5. Length interaction: 5 m and 30 m longitudinal connections with identical
   defender features; identify additive length handling and absence of a
   length-by-obstruction term.
6. Multiplicity: on a 20 m connection compare one defender at `(15,2)` with
   defenders at `(5,2)`, `(10,2)`, and `(15,2)`; M1 features and utility must be
   identical.

## Decision rule

Apply the first satisfied category:

1. **A — SPECIFIC REACHABILITY FAILURE MODE IDENTIFIED** only if the velocity
   blind spot passes, backward velocity is structurally available, and causal
   provider processing is established.
2. **B — SPECIFIC MULTI-DEFENDER FAILURE MODE IDENTIFIED** if A is unavailable,
   the multiplicity collapse passes, and both gap distributions are non-degenerate
   in all nine matches.
3. **C — ORIENTATION IS THE CLEARER NEXT HYPOTHESIS** only if A and B fail and no
   more direct static-defense limitation is established.
4. **D — NO M2 JUSTIFIED YET** otherwise.

If A is selected, draft one past-only time-to-intercept hypothesis and enumerate
ball-speed, defender-motion, reaction-time, trajectory, and interception
assumptions. If B is selected, draft one continuous summed-attenuation family
without choosing a kernel or tuning parameter. Do not implement either.

The bounded reuse audit is restricted to Floodlight backward differentiation,
DataBallPy velocity-aware summed influence, Dick/Link/Brefeld receiver
availability, and DEFCON as a broader downstream framework. No installation,
code import, external parameters, or broader literature search is authorized.

## Execution, artifacts, and stop

Run exactly:

`uv run python scripts/session_04_m1_audit.py preflight`

`uv run python scripts/session_04_m1_audit.py audit`

`uv run python scripts/session_04_m1_audit.py publication-check`

Public outputs are `coefficient_summary.json`, `feature_summary.json`,
`geometry_diagnostics.json`, and `manifest.json` under
`outputs/m1_failure_mode_audit/`, using stable aliases. Detailed diagnostics and
an access ledger remain under ignored `outputs/m1_failure_mode_audit/local/`.
Also produce `docs/session_04_m1_failure_mode_audit.md` and bounded append-only
updates to the research log, data dictionary, and library review.

Verify Session 3 hashes before and after execution, deterministic aggregates,
synthetic tests, access firewalls, import safety, compilation, public schemas and
hashes, staged publication safety, and `git diff --check`. Stop after one A/B/C/D
decision and an exact Session 5 question. Do not implement M2, refit M1, inspect
passages, access pose/reserved data, build network features, or begin Session 5.
