# Phase 05 protocol: one M2 multi-defender attenuation comparison

**Status:** FROZEN FOR ONE DEVELOPMENT EXECUTION

**Starting authority:** `746357d0c358062df49ec6641a9ac20c7eba97fc`

**SkillCorner source:** `02a396ffd09b283c9f092fdedeff11da6d535b66`

## Question and claim boundary

Does one continuous summary of distributed static defensive obstruction add
receiver-ranking information beyond M1's minimum-distance representation?

This is a development-only comparison. Accessibility remains **PROXY ONLY** and
suppression remains **NOT SUPPORTABLE**. The feature is not interception
probability, pitch control, calibrated accessibility, or causal defensive effect.

## Data and population authority

Use only development matches `1886347`, `1899585`, `1925299`, `1996435`,
`2006229`, `2011166`, `2013725`, `2015213`, and `2017461`. Reject all other
match identifiers before opening a path. In particular, prohibit reserved
matches `1874553`, `1927964`, `1959846`, `1986691`, `1996436`, `2006363`,
`2007448`, `2007721`, `2010085`, `2016236`, and withheld match `1953632`.

Use the ignored Session 3 population verbatim. Its required SHA-256 is
`cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d`,
with 7,227 evaluation-eligible and fit-eligible attempts. Do not regenerate or
readjudicate it. Candidate, label, timing, fit/evaluation eligibility, target-
outside zero-credit, attacking-direction, and defender-validity rules remain
unchanged. No raw provider acquisition is authorized.

Pose/skeletal data, vendor Passing Option scores, future tracking, external
provider data, reachability, orientation, network features, scored passages,
and reserved or withheld values are prohibited.

## Frozen feature

For carrier endpoint `a`, receiver endpoint `b`, valid defender positions
`d_j`, and fixed scale `h = 5.0` metres:

\[
A(a,b)=\sum_j \exp\{-\operatorname{dist}(d_j,[a,b])/5.0\}.
\]

Distance is Euclidean distance to the same finite segment used by M1. Use the
existing projection and `1e-9` metre degenerate-segment implementation tolerance,
which has no football meaning. Sort numeric distances in nondecreasing order,
independently of identity, and combine contributions with `math.fsum`.

The 5 metre scale is a prospective transparent local decay scale, small relative
to pitch dimensions. It is not learned, tuned, or interpreted as a tactical
threshold or interception radius. Contributions at 0, 5, 10, and 15 metres are
respectively `1`, `exp(-1)`, `exp(-2)`, and `exp(-3)`.

Reject empty defenders and nonfinite coordinates. Finite exponential underflow
to zero is valid. Do not normalize defender count, select top-k defenders, use a
soft minimum, compare kernels or scales, or add pass-length interactions.

## Models and preprocessing

M1 retains exactly: carrier-receiver distance, signed longitudinal displacement,
signed lateral displacement, nearest-defender distance to receiver, and minimum
defender distance to the finite connection segment. M2 is the exact M1 matrix
plus `summed_segment_attenuation`. M0 is not rerun.

Fit M1 and M2 independently with the unchanged Session 3 unregularized
conditional-softmax objective, no intercept, identities, nonlinear expansion,
regularization, randomness, feature selection, or tuning. Use the same nine
leave-one-match-out folds and SciPy L-BFGS-B configuration: float64, zero
initialization, `maxiter=2000`, `maxls=50`, `ftol=1e-12`, and `gtol=1e-8`.
Require successful finite termination and maximum absolute gradient at most
`1e-6`.

Fit preprocessing on fit-eligible training candidates only, weighting equally
by match, attempt, and candidate, with population standard deviations. A zero-
variance column uses scale one but blocks at identifiability. Require exact
equality of M1's five raw columns, training means/scales, and standardized values
inside M2.

## Replay and identifiability gates

Before M2 scoring, reproduce the authoritative Session 3 M1 fold means, scales,
coefficients, per-match metrics, and match-macro MRR/Hit@1/Hit@3 exactly. These
values are committed in Session 3 QC and metric artifacts and hash-bound by its
manifest. Iteration counts and other ancillary optimizer diagnostics are
diagnostic unless an existing convergence gate fails. An authoritative mismatch
blocks M2 without tolerance tuning or corrective model changes.

Apply a Session 5 fail-closed wrapper without changing the Session 3 fitter.
Use its within-choice difference matrix, numerical SVD tolerance, and complete
and quasi-separation formulations. Require conclusive successful solver states
for both feasibility problems. Solver error or ambiguity, insufficient rank,
complete or quasi separation, zero within-choice attenuation information, or a
nonfinite design blocks execution. Do not add a penalty, drop a feature, or use
a fallback.

## Metrics and outputs

Primary evaluation is MRR within each held-out match and the equal mean across
nine matches. Secondary metrics are Hit@1 and Hit@3 on identical observations.
Use Session 3's expected-credit tie blocks with absolute `1e-12` tolerance from
the block's highest score. Retained target-outside observations receive zero
credit. Report nine M2-minus-M1 MRR differences, their mean and median, and exact
positive/negative/zero counts. No bootstrap, p-value, effect threshold, or extra
metric is authorized.

Public outputs are limited to `docs/session_05_m2_attenuation_decision_brief.md`
and `outputs/receiver_ranking_m2/{m1_match_metrics.csv,m2_match_metrics.csv,
paired_comparison.csv,aggregate_metrics.json,qc.json,manifest.json}`. Use stable
match aliases. Keep coordinates, timestamps, identities, candidate rows,
per-attempt features/utilities/rankings, alias maps, preparation details, and the
access ledger ignored. Hash closed outputs; record the manifest hash in the brief
rather than recursively inside the manifest.

## Chronology, failure, and interpretation

The runner exposes `preflight`, `prepare`, `run`, and `publication-check`.
Commit this protocol first. Then implement and test, prepare a score-free design,
and commit the implementation before the single `run`. `run` requires a clean
tree, intact authority and preparation hashes, no prior scored outputs, and a
persistent execution marker created before fitting.

Write outputs atomically and close aggregate results before interpretation. If
a bug, replay mismatch, partial failure, or scientific gate occurs after score
exposure, preserve the exposure and stop. No automatic corrective rerun is
authorized.

Choose one descriptive conclusion: A, distributed static defense adds incremental
information; B, attenuation adds little or mixed information; C, frozen
attenuation does not improve M1; or D, execution invalid. Use paired MRR direction,
mean/median, secondary metrics, and scientific QC without an automatic numerical
threshold.

If valid evidence supports retaining M2, recommend a separately frozen protected
evaluation of M0/M1/M2. If mixed or null, recommend a prospectively governed
model-error/passage audit. If invalid, recommend resolving the execution failure.
Do not execute the recommendation. Stop after the reviewed Session 5 package.
