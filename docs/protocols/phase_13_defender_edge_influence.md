# Phase 13 — Defender-to-edge influence mapping

Prospectively frozen from clean local/tracking/live remote
`b29ef29430e620ae88cb51df3353a2596e0a5d69`. Release `v0.1.0` remains at
`f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`.

## Question, evidence and boundaries

Does state-local defender geometry exhibit recurring multi-edge structure that
M1's two scalar edge minima omit? Unweighted geometry is primary. Frozen M1
option-share weighting of segment top-1/2/3 membership is secondary and circular:
the shares already depend on defensive geometry. It is not independent evidence.

Use only the canonical 7,227-state development population at
`outputs/receiver_ranking_m0_m1/local/population.jsonl`, SHA-256
`cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d`,
with historical match counts 885,801,952,877,861,629,764,734,724. Use only M1
from the frozen final-model artifact, SHA-256
`0383561e45bcd9f8d84eccc7e9733b2409536f61c39193fa87d08c36c6f6fd65`.
Hash inputs before parsing. Project target fields out before analytical records.

No provider products, reserved detail, withheld match, pose, external value
surface, boundary remedy, target/outcome analysis, fitting, M0/M2, prediction
metric or empirical rendering. Session 12b/12c remain parked. Candidate and
defender eligibility are inherited. Coordinates outside field markings remain
valid inputs to finite-segment geometry; this does not resolve value-domain use.

Canonical defenders lack identities. Their array ordinals are anonymous and
state-local only. Never link them across states, publish them, deduplicate equal
coordinates or infer player roles. Preserve all historical claims. Accessibility
is PROXY ONLY and suppression is NOT SUPPORTABLE.

## Frozen relation mathematics

For each carrier a, receiver b and defender d retain separately Euclidean
`distance(d,b)` and distance from d to finite segment a→b. Reuse the existing
projection and its 1e-9 metre floating-point implementation tolerance. Reject
nonfinite or empty geometry. Require exact equality of per-edge minima with M1's
receiver-nearest and segment-nearest feature columns.

Rank ascending distances in blocks anchored at the smallest unused value. Values
within absolute 1e-12 metres, with zero relative tolerance, share a block. If a
block occupies positions a..b, its expected rank is `(a+b)/2`; its fractional
top-k membership is `max(0,min(b,k)-a+1)/(b-a+1)`. Freeze k=1,2,3, capped at the
number of defenders. Array order never breaks ties. This new ranking does not
change the historical minimum helper.

Report first/second/third raw order statistics where available and continuous
d2-d1/d3-d1 gaps. A singleton first block means numerically unique nearest, not
football superiority. Missing order statistics are unavailable.

For both proximity types report nearest-block size, unique-nearest frequency,
distinct defenders in nearest blocks per star, per-defender nearest edge counts,
fractional top-k involvement and edge-normalized involvement, expected-rank and
distance distributions, multi-edge nearest membership (at least two edges), and
maximum involvement. Compare receiver/segment nearest sets using intersection,
exact equality, Jaccard and same-singleton frequency. Compare candidate-edge
pairs through segment top-k support-set Jaccard; every positive fractional member
is included, so ties may enlarge support past k.

Call these edge involvement, multi-edge influence geometry, coverage relationship,
defender-edge footprint and proximity-redundancy descriptors. Do not use ownership,
suppressed option, marginal contribution, functional substitute or player value.

After unweighted geometry, calculate only segment involvement weighted by frozen
M1 shares: `I[d,k]=sum_j p_M1[j]*w[d,j,k]`. Describe higher-share modeled options,
not objectively important options. Do not weight receiver proximity or introduce
a kernel. Check that unweighted involvement sums to edges times effective k and
weighted involvement sums to effective k at a fixed tolerance of
`64*float64_epsilon*max(1,sum(abs(summands)),abs(total))`.

## Aggregation, software and visualization

States receive equal weight within each match and matches equal macro weight.
Edges, defenders and edge pairs receive equal weight within their state for the
respective family; raw distances use match→state→edge→defender weights. Report
counts, explicit denominators, means, extrema and weighted inverse-ECDF
5/25/50/75/95 percentiles. Empty comparisons are unavailable and disclose the
represented-match denominator. No bins, regression, significance test,
practical-effect threshold or post-result metric.

Implement internal immutable `DefenderEdgeRelation` and `DefenderEdgeMap` in the
network namespace. `map_defender_edges(state)` constructs the map;
`summarize_edge_involvement(mapping, network=None)` optionally adds aligned M1
weighting. It composes with `OptionState`/`OptionNetwork`, loads nothing and
changes no public root export, package version, dependency, lockfile or released
semantics.

Runner commands: `preflight`, `prepare`, `analyze`, `render-synthetic`, and
`publication-check`. Preparation projects only geometry and computes no distance,
utility or share. Analysis requires committed authority, clean state and a new
exclusive marker. No acquisition or fit route. Preserve an exposed failure and
stop without repair or automatic rerun.

Synthetic SVG only: carrier (0,0); receivers A (20,-10), B (25,0), C (20,10), D
(-10,5); defenders D1 (5,0), D2 (18,-9), D3 (18,9), D4 (-7,4). Two equal-scale
panels show receiver and segment proximity with rank matrices, first membership
filled and second outlined. Label `SYNTHETIC — GEOMETRIC RELATIONSHIPS, NOT
SUPPRESSION`; include metre scale/attack arrow and no pitch. Render twice and
require byte equality. No fitted shares or empirical state.

## Interpretation, artifacts and stop

Classification A requires recurring, non-degenerate empirical multi-edge and
redundancy patterns across states and matches. Guaranteed information loss from
scalar minima, synthetic counterexamples or M1 weighting alone cannot earn A.
Choose A clear complementary formal structure, B present but limited, C little
additional description, or D blocked/invalid. Execution validity is separate.

Occlusion readiness 1 is unavailable. Use 2 only for one bounded prospective
hypothesis supported by the findings, otherwise 3 representation revision or 4
not justified. Classify software separately as 1 later experimental API ready,
2 useful internal abstraction, 3 revision needed, or 4 invalid.

Outputs under `outputs/defender_edge_influence/`: contract, implementation and
population authority, relation summary, role overlap, multi-edge summary,
redundancy summary, QC, manifest and synthetic SVG. Detailed relations, geometry,
shares, identifiers and execution records stay ignored. Report all 21 requested
handoff items in `docs/session_13_defender_edge_influence_report.md`; append only
the research log and library review.

Commit protocol/contract, tested implementation, prepared authority, then closed
results/report separately. Validate focused/full synthetic tests, compilation,
links, hashes, schemas, publication/privacy, history, staged contents and diff.
Push, verify synchronized heads/tag and stop. Future layers and the sister-project
connection are architecture only. Recommend exactly one next governed phase;
do not execute it.
