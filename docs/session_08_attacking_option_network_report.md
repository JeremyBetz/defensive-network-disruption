# Session 8 — Local attacking-option networks

## Decision and scope

**Network A — complementary formal descriptive structure beyond leading-option summaries is demonstrated**, with a narrow mathematical meaning.
The two frozen synthetic tail distributions have identical rankings and leading
shares but different entropy and effective option counts. These summaries expose
tail structure that the leading shares alone omit. A carrier-centred directed
star adds **no information beyond its complete edge vector**. Development
correlations show considerable redundancy with simpler summaries; this result
is not evidence of incremental predictive value or analyst usefulness.

**Software 1 — ready for a provider-independent experimental core.** Immutable
states, explicit model arguments, neutral edge semantics, numerical summaries,
and a tested optional Kloppy adapter establish the narrow contract. This is not
a hardened package release or evidence of cross-provider empirical validity.

**Execution: valid aggregate analysis, closed once.** All 7,227 canonical
observations across nine development matches were included. M0 and M1 only were
computed. No targets were analyzed. These are label-free, in-sample descriptions
of models fitted on the same development matches, not another replication.
The synthetic SVG passed XML and deterministic-render checks. The native preview
tool cropped its thumbnail; a browser preview was unavailable under its local-file
policy. Full-viewport visual confirmation is therefore a delivery qualification,
not a numerical execution failure. No generated image or result was edited.

## Frozen quantities and findings

Shares are **model-implied receiver-option shares under the fitted conditional-choice
model**, obtained with temperature-one, maximum-subtracted float64 softmax.
They are neither calibrated accessibility nor true pass probabilities.
Rankings and top sets come from canonical utilities with the frozen absolute
`1e-12` block-high tie rule, including when small shares underflow. Candidate
correspondence is identical across models. M1 changes include altered shared
feature coefficients as well as defensive features: use **defense-conditioned
option change**, without causal attribution.

States have equal weight within matches; the nine matches have equal total
weight. Percentiles use the frozen weighted inverse empirical CDF. The following
are match-macro state means; effective counts are averaged after exponentiating
each state's entropy, not obtained by exponentiating the aggregate entropy.

| Quantity | M0 | M1 | M1−M0 |
| --- | ---: | ---: | ---: |
| Top-one share | 0.272247929 | 0.369706531 | +0.097458602 |
| Top-two cumulative share | 0.469902285 | 0.573288157 | +0.103385872 |
| Entropy | 1.958687535 | 1.738362169 | −0.220325366 |
| Normalized entropy | 0.850647188 | 0.754961098 | −0.095686091 |
| Effective option count | 7.165293607 | 5.980391018 | −1.184902588 |
| Utility range | 3.618951942 | 4.129900339 | +0.510948396 |

M1 is more concentrated on average in every match, but not in every state.
The effective-count change has weighted 5/25/50/75/95 percentiles of
−3.689416704, −1.993435641, −1.064694228, −0.201792962 and +0.796869684.
Its full range is −6.504323582 to +2.475051720. No bins or empirical thresholds
were introduced. Entropy and effective count are transformations of one quantity,
not independent corroborating evidence.

| Match | States | Effective-count change | Top-set change fraction | Pair reversal fraction |
| --- | ---: | ---: | ---: | ---: |
| development_01 | 885 | −1.197395957 | 0.589830508 | 0.185511613 |
| development_02 | 801 | −1.101914128 | 0.545568040 | 0.169593564 |
| development_03 | 952 | −1.376244520 | 0.550420168 | 0.185760971 |
| development_04 | 877 | −1.184408729 | 0.529076397 | 0.183808438 |
| development_05 | 861 | −1.194567180 | 0.536585366 | 0.168357207 |
| development_06 | 629 | −1.104030766 | 0.527821940 | 0.173679562 |
| development_07 | 764 | −1.174289587 | 0.569371728 | 0.183915067 |
| development_08 | 734 | −1.107460573 | 0.603542234 | 0.168755677 |
| development_09 | 724 | −1.223811854 | 0.533149171 | 0.171884592 |

The match-macro top-set change fraction is **0.553929506**. The within-choice
pair reversal fraction, averaged by state and then match, is **0.176807410**.
Tie creation and removal are both zero in this population; synthetic tests cover
those cases. Empty pair sets are unassessable rather than zero disagreement.
All full per-match distributions and denominators are retained in the
[aggregate summary](../outputs/attacking_option_network/network_summary.json),
with means in the [comparison CSV](../outputs/attacking_option_network/m0_m1_network_comparison.csv).

Per-match Pearson correlation ranges between effective count and the simpler
views are:

| Comparator | M0 range | M1 range |
| --- | --- | --- |
| Top-one share | −0.881229 to −0.825134 | −0.915807 to −0.897139 |
| Top-two cumulative share | −0.947431 to −0.926155 | −0.975887 to −0.966845 |
| Utility range | −0.734772 to −0.645776 | −0.848052 to −0.817978 |

All 54 comparisons were assessable. Strong correlations, especially with the
top-two share, caution against presenting effective count as a new information
source. They do not erase the mathematical tail distinction, establish a
predictive benefit, or answer whether practitioners would use it.

## Contract, synthetic illustration and reuse

The [software contract](../outputs/attacking_option_network/software_contract.json)
is implemented in the existing package namespaces. `OptionState` carries immutable
metric geometry and candidate identity, with explicit coordinate semantics;
the canonical carrier is anonymous. `evaluate_options(state, model=...)` requires
an explicit frozen model. `OptionNetwork` exposes edges, utility-derived tie
blocks, model-implied shares, top options, summary and detached records.
No model or competition data is loaded by the numerical API. Plotting and
adapter logic remain outside the core. There are no whole-team connections,
invented carrier identities, timestamps or ball positions.

The [single synthetic SVG](../outputs/attacking_option_network/synthetic_options.svg)
uses frozen identical positions, equal metric scales, anonymous receivers,
a carrier label, a metre scale and attacking arrow. Line width is fixed at
`0.5 + 8 × share`; its annotations report top share and effective count. It has
no pitch boundary and does not depict an empirical observation. Separate uniform,
concentrated, tied, singleton and equal-leading-share/different-tail fixtures
establish formal behavior only.

The optional Kloppy 3.19.0 adapter uses actual Frame/Player abstractions in
synthetic tests. Explicit eligible candidates/opponents and caller-verified
centred metric context are required; conversion preserves `x'=s*x, y'=y`.
It rejects unsupported or missing context rather than guessing coordinates or
eligibility. NumPy remains the locked numerical implementation. mplsoccer is
preferred later when pitch dimensions are supplied; matplotvideo is deferred
because no video/temporal workflow is authorized. No dependency or lockfile
changed. Reviewed licenses, versions and limitations are in the append-only
[library review](../references/library_review.md). No concrete upstream gap was
established and no upstream PR was opened.

## Verification and preservation

Focused production-path tests: **19 passed, 0 skipped**. Full active synthetic
suite: **198 passed, 3 skipped, 201 total**. The skips are retained historical
scaffold placeholders; none is a Session 8 test. Tests cover immutable membership,
permutations, exact frozen features/utilities, nesting, stable softmax, shift
invariance, underflow ordering, ties, singleton/invalid states, distribution
behavior, weighting, real synthetic Kloppy frames, target independence,
allowlist/path/symlink rejection, exclusive markers, preserved failure,
schema rejection, CSV consistency and synthetic command closure.

Publication schemas, finite values, aliases/counts, CSV cross-file equality,
manifest hashes and authority checks passed before aggregate closure and again
following synthetic rendering. Compilation, documentation links, staged privacy
review, append-only history checks and diff checks passed before commit;
the final handoff records commit and synchronization outcomes. Existing protocols, models,
scientific outputs, source modules, tests and package metadata remain byte-identical;
only the research log and library review receive append-only entries. No empirical
analysis was repeated during verification: tests use synthetic fixtures.

The public package is closed. Its manifest SHA-256 is
`7e0ed5e6185bbd4403b6abe153777e11f1794b5f3b333b109fe405ad512b3dc5`.
Population and model identities remain respectively
`cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d` and
`0383561e45bcd9f8d84eccc7e9733b2409536f61c39193fa87d08c36c6f6fd65`.
The [manifest](../outputs/attacking_option_network/manifest.json) binds the
protocol, implementation/environment authority, inputs and generated output hashes.
Detailed empirical records and execution/access evidence remain ignored.

## Twenty-three handoff evidence items

1. **Starting authority:** clean local/live-remote checkpoint
   `54b56a9900b96a1be0e9e51087a978ffeef6d4f1` verified before work.
2. **Question:** formal compression beyond leading shares, not beyond complete edges.
3. **Protocol:** [Phase 08](protocols/phase_08_attacking_option_network.md), committed as `dfbf7cf` before implementation or analysis.
4. **Contract:** committed with the protocol; explicit state/model/network semantics.
5. **Implementation:** `2e0032fe17cc2e77a8a7cda63c9bc270399b7f51`, tested and committed before analysis.
6. **Environment:** [implementation authority](../outputs/attacking_option_network/implementation_authority.json) binds locked versions and inherited helper hashes.
7. **Population:** 7,227 states, all nine matches, original hash verified before parsing.
8. **Targets:** projected out before computation; no outcomes, target ranks or joins.
9. **Models:** frozen M0/M1 only; unchanged coefficients/preprocessing; no fit or M2 route.
10. **Transformation:** temperature-one softmax, no smoothing or threshold.
11. **Ordering:** canonical utilities and block-high ties, independent of share underflow.
12. **Summary definitions:** six frozen quantities and changes, no extra network metrics.
13. **Aggregation:** state then equal match, inverse-CDF percentiles, explicit counts.
14. **Formal counterexamples:** fixed synthetic fixtures with leading-share equality and tail difference.
15. **Empirical distributions:** all nine match distributions and macro in network summary.
16. **Ordering evidence:** top-set changes, strict reversals, separate tie creation/removal.
17. **Comparators:** per-match Pearson coefficients and constant-variable handling.
18. **Adapter/reuse:** Kloppy synthetic checks, NumPy reuse, conditional/deferred rendering libraries.
19. **Visual:** one clearly synthetic SVG, no empirical rendering; preview qualification above.
20. **Tests and guards:** pass/skip counts, schemas, hashes, firewalls and preserved authority.
21. **Decisions:** network A, software 1, valid closed aggregate execution with visual-preview qualification.
22. **Result delivery:** separate result commit follows aggregate closure, report and staged review; final Git commit/push/synchronization identifiers are in the handoff to avoid a self-referential commit hash.
23. **Bound and next direction:** recommendation below; no automatic continuation.

## Limits and one recommendation

C09/C10 remain SUPPORTED WITHIN SCOPE, C01/C02 remain IN PROGRESS.
Accessibility remains **PROXY ONLY** and suppression **NOT SUPPORTABLE**.
Vendor targets have Tier B limitations; upstream tracking is offline/extrapolated.
Session 8 does not establish best-pass judgments, availability, defensive
attribution, causal effects, player value or network value. Attacking structure,
tactical preferences and defender positioning are dependent; these model shares
cannot separate their causal roles. No practitioner or human-review evidence
exists here. No raw-provider files, reserved detail, withheld/pose, temporal context,
external football data or new predictive evaluation were accessed.

Recommend exactly one separately governed **synthetic-only usability review of the
experimental state/network contract and tail summaries**. This would test whether
the API and compression are understandable before expanding network scope; it
would not validate football accessibility. Do not execute it in Session 8.
