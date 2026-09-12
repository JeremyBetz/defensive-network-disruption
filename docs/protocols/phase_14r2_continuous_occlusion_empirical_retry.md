# Phase 14R2 — Label-free continuous occlusion representation study

Prospectively frozen 2026-09-12. Starting clean local/tracking/live main:
`a7899efeff488866203be5310b2c08af0ca02067`. Release v0.1.0 remains at
`f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`.

## Authority, question and boundaries

Inherit [Session 13](../session_13_defender_edge_influence_report.md),
[Phase 14](phase_14_continuous_occlusion_hypotheses.md), and the complete
14a–14i sequence, ending with [Session 14i acceptance](../session_14i_signature_repair_and_acceptance.md).
The latter manifest SHA-256 is
`1c65769260cc6e1b8a79b69129b3b5a227d4a0a41aec93be4533168a042ace88`.
Earlier invalid results and the Phase 14f test-change discrepancy remain historical.
Session 13 gap percentiles are distributions of state-average gaps.

Question: do fixed directional fields add complementary structural description
beyond isotropic proximity, and does one merit later behavioral validation?
Only spent development geometry is allowed. No targets, outcomes, target ranks,
models, utilities, option shares, provider acquisition, reserved detail, withheld,
pose, xT, progression, sister-project access or empirical rendering. No claim,
README, release, API, dependency or historical implementation change.
Empirical origins are carrier-position proxies for ball origin, not measured
ball positions or an assertion of carrier/ball colocation.

## Frozen field and numerical contract

Reuse exact production formulas and constants: sigma=2 m, onset a=1 m,
alpha=10 degrees, float64. For b,d,q, u=(d-b)/norm(d-b), ell=(q-d) dot u,
h=abs(cross(q-d,u)); G=0 at ell<=0, 3t^2-2t^3 for t=ell/a in (0,1),
and 1 at ell>=a. Isotropic exp(-norm(q-d)^2/(2*sigma^2)); expanding
G*exp(-h^2/(2*(sigma+max(ell,0)*tan(alpha))^2)); constant_width
G*exp(-h^2/(2*sigma^2)). No longitudinal decay. Directional tails are assumptions.
Origin-defender separation <=1e-9 m blocks the entire common population.
Coincident defenders remain distinct contributors. Primary stable sorted
union 1-product(1-Od); maximum comparator max(Od); neither is probability.

Synthetic acceptance replays the accepted production path in this phase's own
namespace, never rerunning a historical runner or altering its marker. Require
108/108 cases, 366/366 references, 399/399 permutations, engineering fixtures,
actual failure propagation and immutable conjunction-only readiness true.
Historical four failing maximum cases retain their split-Simpson checks.

The separate empirical adapter consumes unchanged numerical primitives. It does
not run factorial permutations or invent stored empirical reference values.
For each candidate/edge, controlled uniform joint Simpson covers every individual,
union and maximum component at 256,512,1024,2048,4096,8192,16384 intervals;
accept first finer vector when every change <=1e-7. Cap exhaustion stops.
Independently certify maximum partitions using endpoints, onsets, switches and
both adjacent-float enclosure endpoints, without tolerance deduplication.
Scalar adaptive integration uses epsabs=epsrel 1e-13 and 1e-11, limit=1000;
require repeat and onset-only adaptive agreement <=1e-10 and direct 65536
Simpson agreement <=1e-9. Joint maximum must agree with independent maximum
within 1e-6. Degenerate edges <=1e-9 m use endpoint fields. Historical fixed-
spacing summarize_edge is not called. Independent empirical individual/union
references are not claimed. Numerical warnings, failed roots/certification,
nonfinite values, disagreement or nondeterminism stop without fallback.

## Population projection and preparation

Only canonical population SHA-256
`cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d`
is authorized: 7227 states, alias-order counts 885,801,952,877,861,629,764,734,724.
Use the existing nine development membership authority; no invented mappings.
Hash before parsing. Selectively decode match identity, integrity-only event
identity, candidate identities, carrier/candidate/defender XY; skip target values
lexically before creating records. Event keys only support duplicate validation
and are discarded. Replace candidate identities with local ordinal labels after
integrity checks; never link anonymous defenders across states. Unknown keys,
unsafe paths, symlinks, unauthorized membership, invalid/empty geometry or count
mismatch stop. Preparation computes no fields, utility or distances beyond
geometric validity. No clipping, exclusions, rebuilding or coordinate repair.

## Summaries and frozen extension

For each of isotropic, expanding, constant_width and union/maximum: endpoint
(receiver) field and normalized segment-average integral over t in [0,1]. Retain
individual endpoint and segment-average values privately. Endpoint and segment
union-minus-maximum use abs 1e-12 numerical equality only. No materiality bins.

Inherit Session 13 pure relation map and unweighted involvement definitions;
never construct an OptionNetwork or pass network shares. Per state Spearman
with average exact-tie ranks: endpoint versus negative nearest-receiver distance;
segment versus negative nearest-segment distance; segment union-minus-maximum
versus d2-d1 and d3-d1. Constants/insufficient edges are unavailable.

Individual field maximum blocks use descending 1e-12 block-anchor ties; exact
all-zero edges are ownerless. Report distinct maximum-block defenders per star,
any defender occupying blocks on multiple edges, maximum edge involvement,
intersection/Jaccard with geometric receiver/segment-nearest sets, and fraction
of individual field strength carried by fractional geometric top-1/2/3 membership
for receiver and segment distance separately. Zero total strength is unavailable.

Bounded extension, frozen before exposure:
- Pairs in order isotropic->expanding, isotropic->constant_width,
  expanding->constant_width: second-minus-first distributions and within-state
  Spearman for both summaries and combinations.
- Candidate-edge pair orders: same strict order, strict reversal, tie creation,
  tie removal, both tied; descending field block-anchor tolerance 1e-12.
- Receiver/corridor nearest-set intersection, equality and Jaccard. Opposing
  candidate-edge distance orders exclude raw-distance ties (ascending 1e-12
  block-anchor). On discordant pairs classify field order as endpoint-following,
  corridor-following, tied. Stronger/weaker refers only to relative edge order.
- Within each match, across-state Spearman between mean segment overlap and
  mean d2-d1, mean d3-d1, top-1/2/3 support-set Jaccard, distinct top-k involved
  defenders and maximum unweighted fractional top-k involvement. No other
  associations, composite score, empirical matching or fitted statistic.

Equal match->state->edge weighting; pair frequencies average eligible pairs
within state, then represented states within match, then represented matches.
Means, min/max and weighted inverse-ECDF 5/25/50/75/95 percentiles; median is q50.
Correlations average assessable states within match then represented matches.
All nine aliases and unavailable/assessable denominators are explicit. Empty
states/groups are never zero-filled. Stable alias public outputs only.

## Visual, interfaces and chronology

Separate runner: preflight, verify-production, render-synthetic, prepare,
analyze, publication-check. Each stage hashes its prerequisites; no automatic
commit boundary crossing. Pre-access numerical tests and visual QA may expose
synthetic fields, never empirical states. Freeze synthetic fixtures from Phase
14 including equal-minimum one/three and star. Render 1800x800 SVG, origin (0,0),
defenders (5,0),(18,-9),(18,9),(-7,4), receivers (20,-10),(25,0),(20,10),(-10,5),
extent [-15,35]x[-20,20], equal aspect, three panels, union, common [0,1] scale.
Labels: SYNTHETIC / CARRIER-ORIGIN GEOMETRIC OCCLUSION HYPOTHESIS /
NOT VALIDATED COVER SHADOW / NOT SUPPRESSION. Locked Matplotlib metadata/hash
salt; render twice byte-identically and inspect full frame before geometry access.
No pitch boundaries, animation or empirical diagram. Fix layout pre-access only.

Four checkpoints: protocol; tested implementation with complete synthetic
acceptance and approved visual; prepared population authority; closed empirical
outputs/report. Pre-access and population authorities live in an authority/
subdirectory, separately from final artifacts. All stages use ignored append-only
ledgers and exclusive persistent markers. Analyze requires clean committed inputs,
source hashes and absent result files. No automatic rerun after exposure.

## Outputs, failure and interpretation

Public root outputs under outputs/continuous_occlusion_retry_14r2: candidate_summary.json,
structural_correspondence.csv, receiver_segment_divergence.csv, union_vs_max.csv,
multi_edge_summary.csv, match_summary.csv, synthetic_stress_summary.json, qc.json,
manifest.json, synthetic_field_comparison.svg. Strict fixed schemas, finite JSON,
LF CSV, aggregate aliases and hashes. Details/tracebacks/coordinates/markers stay
ignored. Validate all results before atomic manifest closure or displaying them.
Publication checks validate existing hashes, never rebind outputs. A failed stage
preserves completed synthetic artifacts, private partial work and explicit
unavailable outputs; closes as D without invented empty empirical conclusions.
Any post-access implementation defect stops without repair/rerun.

Use all ten dimensions: interpretability, smoothness, carrier-relative behavior,
composability, multi-edge behavior, Session13 correspondence, equal-minimum
synthetic discrimination, distinction from isotropic, software simplicity and
visual usefulness. No weights. A one candidate has coherent complementary
advantage; B both remain plausible; C little added description; D blocked/invalid.
No automatic winner from higher correlation, algebraic information or aesthetics.
Readiness 1 separately governed behavioral test of one frozen field; 2 geometric
descriptor only; 3 needs revision; 4 not justified. Numerical blockage leaves
scientific comparison unavailable; readiness 3 identifies unresolved execution,
not established field failure. Only A freezes a later candidate specification.

Report all 34 requested handoff items with unavailable evidence explicit. Append
research log only; claims unchanged. Accessibility PROXY ONLY, suppression NOT
SUPPORTABLE, no causality/interception/value/best-pass/tactical-intent claims.
Former reserved matches are spent. Run focused/relevant/full active tests,
compile, links, publication/privacy, historical/staged/diff checks and CI.
Push reviewed commits and verify synchronized clean heads and tag. One next
action: behavioral test for A/readiness1; bounded discrimination for B; retain
simple geometry for C; blocker diagnosis for D. Execute none automatically.

## Superseding R2 numerical wiring and evidence contract

This new execution preserves historical 14R as blocked. Bind Phase 14i, 14v/14w,
14aa, 14ab and 14ac protocols, reports and manifests at the starting commit.
14aa remains historically H (its generated D bytes are preserved); 14ab separated
canonical structure from raw solver provenance. 14ac establishes the final-float
comparison contract, not a change to production evaluation. These later rules
supersede the independent point-reference wording above for this new execution.

The new adapter consumes deterministic_directional_onsets and
deterministic_partitions directly. Keep certified tie endpoints and canonical
first-post-switch coordinates. Raw scalar/Brent records are provenance only.
Pass the resulting partitions directly to bounded_adaptive_maximum at 1e-13 and
1e-11. For N positive pieces, width <= 1e-12/N qualifies for [0,width] residual
accounting under 0 <= maximum <= 1. Preserve every piece; no merging. Use inherited
interval_distance <= 1e-10, onset-only point_interval_distance <= 1e-10, direct
65536 Simpson distance <= 1e-9, and joint maximum distance <= 1e-6. Historical
four synthetic split-Simpson cases retain 32768/65536 checks at 1e-10. No empirical
historical-reference or factorial-permutation requirement is invented.

The assembled synthetic path must pass 108 cases, 366 references, 399 permutations,
independent continuity and engineering checks, actual failure propagation and
derived machine readiness. Compare exact canonical records, component order and
accepted intervals; only finite final floats use abs(a-b) <=
64*epsilon64*max(1,abs(a),abs(b)). Signed zero is numerically equivalent with bits
retained diagnostically. Do not reuse historical execution markers or runtime
patch historical modules. An additional numerical defect outside orchestration
scope stops R2; no repair is authorized here.

Add direct receiver-field versus segment-average-field Spearman and five-category
order comparisons for each candidate and combination. Candidate-pair output is
separate candidate_pair_comparison.csv; second-minus-first follows frozen order.
Use Spearman only, no Pearson. All other statistics inherit the preceding exact
rules. Field summaries and geometrical bookkeeping remain label-free.

Before every risky edge stage persist ignored state/edge/candidate/stage records,
then observed partition/routing counts before integration. Exact warning and
tracebacks stay private. Public failure evidence retains sanitized stage and counts,
and marks all unavailable results explicitly. Failure closure supports pre-access
failure with no population authority or empirical outputs. No result file is
manually edited or rehashed by publication checking.

Pre-access CI must exercise the assembled adapter on Python 3.11 and 3.13 before
population access. Four intended commits: protocol; tested implementation with
synthetic acceptance and approved SVG; prepared authority; closure/report/log.
If a prerequisite blocks, omit unearned later authorities, preserve the failure,
and report the actual shortened chronology. No empirical retry follows failure.
The 34-item handoff follows the authorized R2 request. Readiness 3 on numerical
blockage does not establish a defective football construct. Exactly one next
action: behavioral validation beyond M1 for A/readiness 1; bounded candidate
discrimination for B; retain simpler geometry for C; blocker diagnosis for D.
