# P03 — Receiver-ranking M0/M1 development comparison

Version 1.0, 2026-09-10. Status: **AUTHORIZED AFTER POPULATION FREEZE**.
Authority: Session 2 commit `5fcef6b8b141d636ca5bcf7c41f9e536dd755f03`.
Source: SkillCorner Open Data commit `02a396ffd09b283c9f092fdedeff11da6d535b66`.

## Question and scope

Does transparent defensive geometry add receiver-ranking information beyond
attacking geometry alone in nine development matches? These are development
comparisons, not protected-set or external validation. The target is a useful
vendor target-player label with limitations, not ground-truth or human-observed
intention. Accessibility remains proxy only; suppression is not supportable.

Development allowlist: `1886347`, `1899585`, `1925299`, `1996435`, `2006229`,
`2011166`, `2013725`, `2015213`, `2017461`. Every other match ID is denied before
file open, hash, or parse. No pose, orientation, network feature, vendor option
score, M0+, M2, reserved data, scored passage, or performance-driven tuning is
authorized.

## Population preparation

Before scoring, prepare and freeze a population using production functions. A
pass is a `player_possession` event with populated `pass_outcome` and a valid
provider pass-transition timestamp. The decision state is the latest same-period
tracking timestamp strictly before that transition and no more than 100 ms old.
Parse clocks as integer microseconds. The tolerance is a prospective cadence-based
draft, not a truth claim. Do not interpolate, bridge periods, or tune offsets.
Tracking is an offline extrapolated product; no real-time claim is permitted.

Candidates are established before labels: same carrier team, not the carrier,
active in a verified period-specific metadata interval, present with finite
decision-time coordinates. Include goalkeepers and backward options; impose no
distance or offside filter. Defenders are all active opponents with finite current
coordinates. Do not carry identities through missing frames. Unknown direction,
interval semantics, identity, or geometry blocks the affected state.

Apply this mutually exclusive exclusion waterfall and retain overlapping QC flags:

1. missing, ambiguous, or unusable vendor target;
2. invalid event identity or pass-transition mapping;
3. missing, stale, or ambiguous decision-time frame;
4. invalid carrier identity, team, active state, or coordinate;
5. empty independent candidate set;
6. empty opponent set or non-finite required geometry.

Inspect the one previously observed target/candidate mismatch structurally before
scoring. A valid state with a target outside its independent candidates remains
evaluation-eligible with zero credit for both models and is not fit-eligible. An
invalid state is excluded under its named rule. Record evaluation and fit
eligibility separately, per match and fold, with population hashes.

Transform native coordinates as `x'=s*x, y'=y`, where verified team/period side
metadata supplies `s=+1` for left-to-right attack and `-1` otherwise. Positive x
points toward the attacking goal; y retains the native physical direction.

## Frozen features and model

M0 contains exactly carrier-receiver Euclidean distance, signed longitudinal
displacement, and signed lateral displacement. M1 is the exact M0 matrix plus
nearest-opponent distance to receiver and minimum opponent distance to the finite
carrier-receiver segment. Segment length at or below `1e-9` metres uses point
distance and is flagged; this is only a floating-point implementation tolerance.
No large sentinel represents missing defenders.

Both models use unregularized linear conditional softmax:

`p(i,j) = exp(beta*z[i,j]) / sum(k in C[i]) exp(beta*z[i,k])`.

Minimize negative log likelihood averaged equally within training match and then
equally across the eight training matches. Fit only observations with a unique
target inside the choice set. Unchosen candidates are competitors, not failed or
unavailable passes.

Evaluate nine leave-one-match-out folds. Standardize on fit-eligible training
candidates only, weighted equally by match, attempt, then candidate. Use population
standard deviation; replace a zero scale by one and trigger the identifiability
gate. M0's first three transformed columns must equal M1's exactly.

Use float64, analytic gradient, zero initialization and SciPy L-BFGS-B with
`maxiter=2000`, `maxls=50`, `ftol=1e-12`, `gtol=1e-8`. There is no intercept,
penalty, nonlinear expansion, identity effect, search, fallback, or randomness.
Require finite output, successful termination, and maximum absolute gradient at
most `1e-6`.

Before fitting, check numerical rank on within-choice feature differences using
SVD tolerance `max(shape) * eps * largest_singular_value`. Check complete/quasi
separation by linear feasibility of target-minus-alternative differences. Rank
deficiency, separation, ambiguous feasibility, or optimization failure blocks the
comparison; do not add regularization or remove features afterward.

## Evaluation and outputs

Rank descending linear utility. Form a tie block from consecutive scores within
absolute `1e-12` of the block's highest score, zero relative tolerance. Award the
target expected reciprocal rank and expected Hit@1/3 under uniform order within
its block. IDs and input order do not break score ties. A retained target outside
a nonempty choice set gets zero for both models.

Primary MRR and secondary Hit@1/3 are averaged per attempt within held-out match,
then equally across nine matches. Report pooled MRR descriptively, nine paired MRR
differences, mean, median, and positive/negative/tied counts. No bootstrap,
significance test, effect threshold, NDCG, AUC, MAP, or extra baseline is allowed.

Public outputs under `outputs/receiver_ranking_m0_m1/` are match-level M0/M1 CSVs,
paired CSV, `aggregate_metrics.json`, `qc.json`, and `manifest.json`, using stable
public aliases. Candidate rows, timestamps, coordinates, identities, utilities,
and rankings remain ignored. Record protocol/code/environment hashes, parameters,
fold/population counts, population hashes, and output hashes.

Prepare without scores, reconcile the population, and commit the freeze before
fitting. Close and hash aggregate outputs before interpretation. A discovered
post-score bug requires preserving the exposed result, logging it, and stopping
before rerun.

M2 is deferred. The report describes paired evidence without automatic A/B/C/D
or arbitrary magnitude thresholds. A later M2 proposal requires a specific,
prospectively testable limitation; improvement alone does not authorize M2.

Run synthetic/integration tests, compilation, schema and publication guards,
changed-artifact review, and `git diff --check`. Stop after the Session 3 report.
