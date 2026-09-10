# Session 2 decision brief

Date: 2026-09-10. Protocol commit: `d76068e`. Source commit:
`02a396ffd09b283c9f092fdedeff11da6d535b66`.

## Decision

**Tier B — useful vendor-target receiver benchmark feasible with limitations.**
The nine development matches support a receiver-ranking observation table with
independently constructed candidates and a timestamp-restricted pre-pass state.
The label is not established as a human-observed intended receiver, so Tier A is
not justified. Accessibility remains **PROXY ONLY** pending construct validation;
suppression remains **NOT SUPPORTABLE**.

No model or ranking was implemented, fit, scored, or inspected. The compact
counts below are structural diagnostics on development data.

## Data and compatibility

All nine allowlisted metadata, Dynamic Events, and tracking products were
acquired from the pinned source. Git identities, all nine tracking LFS SHA-256
values, and declared sizes passed. The development files use SkillCorner V3
JSONL tracking with 583,437 records, periods 1–2, sequential frame IDs, and a
verified 10 Hz timestamp cadence. Recorded pitch sizes are 104×68, 105×68, and
106×68 metres; coordinates are pitch-centred metres. Observed coordinates can
extend beyond nominal pitch boundaries and must not be clipped silently.

Tracking records contain frame, timestamp, period, player coordinates and
`is_detected`, three-dimensional ball data and `is_detected`, possession, and
image-projection fields. Only 56.86% of player observations and 53.50% of ball
observations are detected rather than extrapolated/missing under the native flag.
The provider's extrapolation process has not been shown to avoid future frames;
use is therefore restricted to an offline timestamp-limited benchmark.

Kloppy 3.19.0 loaded the fixed 5,400-frame sample. With
`coordinates="skillcorner"`, player sets and player/ball coordinates matched the
native records exactly on that sample, with no ball-presence mismatch. Kloppy
does not preserve native detection flags, possession-player identity, or image
projection in the compared frame objects. Verdict: **SAFE WITH NATIVE SIDECAR**.

## Event and target labels

Two Dynamic Events schemas occur: 294 and 322 columns. A pass attempt is
operationally a `player_possession` row with populated `pass_outcome`; its event
end frame/time marks the product's pass transition. This yielded 7,292 attempts:
5,849 successful, 1,415 unsuccessful, and 28 offside.

`player_targeted_id` is present for 7,237 attempts (99.25%): 5,835/5,849
successful, 1,374/1,415 unsuccessful, and 28/28 offside. All target player IDs
resolve to match metadata. `targeted_passing_option_event_id` is present and
resolves uniquely to a Passing Option event for 6,757 attempts (92.66%). Event
IDs contain no duplicates. The extra target-player coverage without an option
link shows why the player target and option-event link must remain distinct.

Vendor documentation says targeted receivers receive an option event regardless
of the model threshold, but it does not establish independent human annotation of
pass intention. Classification: **USEFUL VENDOR TARGET LABEL WITH LIMITATIONS**.
Receipt and pass outcome are labels only; Passing Option scores, one-touch/future
derivations, receipt state, outcome state, and post-pass tracking are prohibited
features.

## Alignment and candidate feasibility

For every pass, `time_end` equals the tracking timestamp at `frame_end`. The
strictly previous same-period frame is exactly 100 ms earlier for all 7,292
attempts. The proposed rule remains: latest same-period frame strictly before
documented pass initiation, maximum age 100 ms. This is a prospective draft from
the verified 10 Hz cadence, not a truth claim. Coarse or shifted timestamps in
future data must yield **alignment blocked**, not a relaxed threshold.

Candidates are created before the target join: same carrier team, not the
carrier, active according to metadata, present with finite coordinates at the
chosen frame. Goalkeepers and backward options remain included; there is no
distance limit; offside filtering is deferred. There are ten candidates in
7,283 attempts and zero in nine frames. Of 7,237 labeled attempts, 7,227 targets
are candidates (99.86%); nine are absent because their coordinate is missing and
one has a team/validity mismatch. There are 298 goalkeeper targets and 2,926
backward targets among covered labels. These frequencies support inclusion and
show that either exclusion would inject tactical selection into the population.

Active status should require both the metadata playing interval and current
tracking presence. Do not carry identities across missing frames. Red-card and
substitution semantics remain dependent on the metadata intervals. Offside is
observable in principle from direction, ball, candidate, and second-last defender,
but extrapolation quality and referee semantics make **DEFER OFFSIDE FILTERING**
the narrowest defensible rule.

## Design prepared for the October 2 gate

M0 remains unimplemented: distance plus signed longitudinal/lateral displacement
in a verified attacking frame. M0+ is justified only as normalized carrier pitch
position to represent field context; it is optional and must not be selected from
performance. M1 geometry is computationally feasible using receiver-nearest
defender distance and finite-segment defender distance. Synthetic projection,
endpoint, tie, empty, non-finite, zero, and near-zero tests pass. The `1e-9` metre
threshold is solely a floating-point implementation tolerance.

MRR is structurally feasible for uniquely labeled attempts, averaged within match
then equally across matches. Hit@1 and Hit@3 are secondary. Tied score blocks use
expected reciprocal-rank/Hit@k credit under uniform ordering. Missing or ambiguous
labels and empty sets are exclusions; a unique target outside a valid nonempty
candidate set receives zero. Compare models on identical attempts/candidates and
start with paired match-level descriptive uncertainty; do not split adjacent
frames or add NDCG without graded relevance.

The remaining blockers before an M0 implementation are an explicit October 2
protocol freeze, final decision on the 55 unlabeled attempts and nine empty-frame
states, resolution or declared handling of the single team/validity mismatch,
and acceptance that extrapolated tracking is offline rather than proven causal.
Tier A additionally requires stronger intended-receiver annotation provenance.

## Governance and stop

Session 1 checkpoint `2925065` and reservation verdict A remain unchanged, with
the L004 over-read qualification carried forward. No reserved or unresolved value
was requested or opened in Session 2. Raw and detailed development records remain
ignored. The October 2 section in P02 is visibly provisional and does not authorize
model execution.
