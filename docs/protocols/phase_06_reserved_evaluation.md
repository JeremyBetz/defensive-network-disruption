# Phase 06 protocol: one protected evaluation of M0/M1/M2

**Status:** FROZEN FOR ONE PROTECTED EXECUTION

**Starting authority:** `74ff7b2d29caf1b1f1cb57e3c8770f6f36075849`

**SkillCorner source:** `02a396ffd09b283c9f092fdedeff11da6d535b66`

## Questions and reservation

Primary: does frozen M1 improve receiver ranking over frozen M0 in the ten
reserved matches? Secondary: does frozen M2 improve ranking over frozen M1?
This is protected evaluation, not model development.

Reserved matches are exactly `1874553`, `1927964`, `1959846`, `1986691`,
`1996436`, `2006363`, `2007448`, `2007721`, `2010085`, and `2016236`.
Withheld match `1953632` must remain unopened. Process reserved matches in
ascending numeric order and publish only aliases `reserved_01` through
`reserved_10`.

> Prospectively reserved from this project stage forward. Session 1 schema
> inventory mechanically over-read post-header bytes into process memory, but
> no evidence indicates value-level content was surfaced, persisted, or used
> analytically.

Preserve all closed Session 2/3/4/5/6a artifacts. The required chronology is:
this protocol commit; tested implementation and final development-model commit;
reserved structural-population commit; one protected scoring execution; result
commit and push. Do not amend or squash these checkpoints.

## Products, projection, and identity contract

Only match metadata, Dynamic Events, and extrapolated tracking are permitted.
Phases, pose, physical aggregates, vendor Passing Option scores, other products,
and the withheld match are prohibited. Before each request or open, enforce the
partition/product allowlist and reject traversal, symlinks, unapproved redirects,
and substituted revisions. Verify ordinary Git object IDs and sizes, the actual
tracking LFS pointer object, and LFS payload SHA-256 and declared size.

Acquire complete authorized products as opaque bytes into ignored storage. Do
not use the complete mixed-content twenty-match manifest to obtain source
identities. Only these fields may enter parsed application records:

- Metadata: `home_team.id`, `away_team.id`, `home_team_side`, `players[].id`,
  `players[].team_id`, and
  `players[].playing_time.by_period[].{name,start_frame,end_frame}`.
- Dynamic Events: `event_id`, `event_type`, `pass_outcome`, `period`, `time_end`,
  `player_id`, `player_in_possession_id`, and `player_targeted_id`.
- Tracking: `frame`, `period`, `timestamp`, and
  `player_data[].{player_id,x,y}`.

Input-contract failures stop the session: invalid required identity forms;
whitespace or padding requiring repair; duplicate declared-team, roster, or
tracking identities; roster teams outside the declared pair; unresolved tracking
identities; conflicting populated carrier references on a pass attempt; unknown
direction; malformed interval structure; or unsupported schema/clock form.
Never trim, normalize, repair, or guess a mapping.

Optional event references may be empty. A populated `player_id` is the carrier;
use `player_in_possession_id` only when it is empty. A valid fallback is allowed,
but a populated conflict stops before population construction. Preserve
match-wide invalidation for duplicate nonempty event IDs. Missing period
intervals mean inactive; never infer or bridge them.

Established observation cases retain the frozen waterfall rather than becoming
new convenience exclusions. Record access immediately in an ignored append-only
ledger with time, phase, command, committed protocol/implementation, alias,
product, and completion or failure. Reserved structural access spends the
protected set even before performance is computed.

## Population contract

A pass attempt is a `player_possession` event with populated `pass_outcome` and
valid event identity. The direct provider target-player field is a useful vendor
label with limitations, not ground-truth or human-observed intention. Passing
Option linkage and scores are neither required nor used.

Select the latest valid same-period tracking frame strictly before the provider
pass-transition timestamp, aged at most 100 ms, using integer microseconds. The
100 ms value is a prospective cadence-based draft, not a truth claim. Do not use
a future frame, interpolation, period bridging, offset optimization, or an
`event_frame - 1` shortcut.

Use `x'=s*x`, `y'=y`, where verified team-period direction determines `s`, so
positive x is goalward and y retains physical lateral sign. Candidates are
same-team, non-carrier players active in the exact period interval and present
with finite coordinates in the decision frame. Include goalkeepers and backward
options; use no distance cutoff or offside filter. Defenders are all active,
currently tracked opponents with finite coordinates, including the goalkeeper.
Construct candidates before and independently of target, receipt, vendor-option,
and outcome values.

Apply this mutually exclusive waterfall and retain overlapping QC separately:

1. Missing, ambiguous, or unusable target label.
2. Invalid event identity or unresolved transition.
3. Missing, stale, or ambiguous decision-time frame.
4. Invalid carrier identity, team, active state, or coordinate.
5. Empty independent candidate set.
6. Empty valid opponent set or nonfinite required geometry.

A unique otherwise valid target outside the independent candidate set remains
evaluation-eligible with zero credit for every model and is not fit-eligible.
Report its frozen structural reason; never add the target or drop the attempt.
A match with no eligible evaluation observations blocks the ten-match result.

Before reserved access, a separate Session 6 adapter must reproduce the original
Session 3 development population byte-for-byte, including separate evaluation
and fit totals of 7,227, all per-match counts/exclusions/order/hashes, and combined
SHA-256 `cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d`.
Use the original authoritative population for final training.

## Frozen models and final development training

M0 contains carrier-receiver Euclidean distance, signed longitudinal displacement,
and signed lateral displacement. M1 is exact M0 plus nearest-defender distance to
the receiver and minimum defender distance to the finite connection segment. M2
is exact M1 plus `sum_j exp(-d_j/5.0)`, where each `d_j` is defender distance to
that segment. Sort numeric distances and combine with `math.fsum`; do not
normalize defender count or change the 5.0 m scale. The `1e-9` m degenerate-
segment threshold is only a floating-point implementation tolerance.

Fit exactly one final M0, M1, and M2 on all nine frozen development matches.
Use independent unregularized conditional softmax fits, no intercept, identities,
regularization, nonlinear expansion, interaction, feature selection, randomness,
or fallback. The loss is averaged equally within each match then across matches.

Fit preprocessing only on development fit-eligible candidates with equal
match-attempt-candidate weighting, population standard deviation, and frozen
zero-scale behavior. Require exact shared raw, mean, scale, and standardized
columns across nested models.

Use float64, zero initialization, analytic gradients, and SciPy L-BFGS-B with
`maxiter=2000`, `maxls=50`, `ftol=1e-12`, `gtol=1e-8`. Require successful finite
termination and maximum absolute gradient at most `1e-6`. Apply the frozen
within-choice SVD rank and complete/quasi-separation rules with conclusive solver
states. Rank deficiency, separation, numerical ambiguity, absent within-choice
M2 information, or fit failure stops without penalty or fallback.

Commit final means, scales, coefficients, QC, population identity, implementation
hashes, and environment before reserved access. These are full-development fits;
do not compare them for equality with eight-match LOMO coefficients and do not
rerun development performance.

## Reserved preparation and protected scoring

The runner exposes `preflight`, `verify-development`, `train-final`,
`prepare-reserved`, `score`, and `publication-check`. No command may cross a
required commit boundary automatically.

`prepare-reserved` requires the committed protocol, committed implementation and
final models, intact development replay, and absent reserved population/results.
It acquires/verifies the ten authorized product triplets, enforces the frozen
contract, and produces only structural counts, eligibility, waterfall and
overlapping QC, target completeness, target-outside reasons, candidate-count
summaries, and population hashes. It has no scoring or fitting path. Keep detailed
population, identities, aliases, coordinates, times, and access records ignored.
Commit its compact structural identity before scoring.

`score` requires a clean tree, committed intact protocol/models/population,
exactly ten nonempty evaluation groups, absent results, and an atomic persistent
execution marker. It cannot fit, acquire, or parse provider products. Apply fixed
development preprocessing and coefficients once to identical observations for
M0/M1/M2. A marker prevents concurrent or automatic repeat execution.

Rank descending utility. Use the frozen absolute `1e-12` block-high tie rule and
expected reciprocal-rank/Hit@1/Hit@3 credit within tied blocks. IDs and row order
never resolve ties. Average attempts within each reserved match, then average all
ten matches equally.

Primary outputs are M0/M1 match-macro MRR, M1-minus-M0, ten paired differences,
mean, median, sign counts, and Hit@1/3. Secondary outputs repeat that structure
for M2-minus-M1. Do not report a pooled headline, p-value, bootstrap, confidence
interval, practical-effect threshold, or new metric.

Write outputs atomically, validate schemas/cardinality/finiteness and cross-file
consistency, then hash and close the package before displaying performance. A
post-exposure defect preserves the package and records a deviation; do not patch
and rescore without separate authorization.

## Outputs, interpretation, and stop rule

Public output paths are:

- `outputs/reserved_evaluation/final_development_models.json`;
- `outputs/reserved_evaluation/population_summary.json`;
- `outputs/reserved_evaluation/m0_match_metrics.csv`;
- `outputs/reserved_evaluation/m1_match_metrics.csv`;
- `outputs/reserved_evaluation/m2_match_metrics.csv`;
- `outputs/reserved_evaluation/m1_m0_paired.csv`;
- `outputs/reserved_evaluation/m2_m1_paired.csv`;
- `outputs/reserved_evaluation/aggregate_metrics.json`;
- `outputs/reserved_evaluation/qc.json`;
- `outputs/reserved_evaluation/manifest.json`.

Use only stable aliases, aggregate counts, model parameters, QC, and hashes.
Never publish raw products, source mappings, provider/player/event identities,
coordinates, timestamps, candidates, per-attempt utilities/ranks, or access data.
Record the manifest's own hash in
`docs/session_06_reserved_evaluation_decision_brief.md` rather than recursively.

Classify M1 versus M0 as A replication, B mixed replication, C no replication,
or D invalid. Classify M2 versus M1 separately as 1 replication, 2 mixed,
3 no replication, or 4 invalid. Base each reasoned conclusion on magnitude,
paired direction, mean/median, Hit@1/3 agreement, and QC; a tiny positive does not
automatically pass.

Even if ranking replicates, accessibility remains **PROXY ONLY**, suppression
remains **NOT SUPPORTABLE**, and extrapolated tracking remains an offline input.
Do not claim true intention, best available pass, interception probability,
pitch control, causation, or generalization beyond these matches.

Test identity rejection, valid fallback/conflict handling, field projection,
firewalls/redirects/symlinks, timing, intervals, candidate independence,
target-outside eligibility, feature/preprocessing nesting, numerical gates,
attenuation, metrics, aggregation, output schemas, and execution states. Include
a synthetic end-to-end rehearsal proving preparation cannot score and scoring
cannot fit. Before and after execution, verify closed authorities, focused/full
tests, compilation, schemas/hashes, publication and changed-artifact guards,
staged contents, and `git diff --check`.

The final report maps all 62 requested items to evidence and recommends exactly
one later direction: development-only construct/practitioner review after primary
replication; development-only governed error/passage audit after mixed/null
primary evidence; or integrity review after invalid execution.

Stop after Session 6. Do not inspect protected passages, tune, add orientation,
pose, velocity, reachability, network/GNN features, or begin Session 7.
