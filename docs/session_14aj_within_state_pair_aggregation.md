# Session 14aj — Within-state pair-summary aggregation repair

## Decision

Session 14aj closes **A — WITHIN-STATE PAIR AGGREGATION REPAIRED** with
**readiness 1 — READY FOR A FRESH SEPARATELY GOVERNED SESSION 14R EMPIRICAL
RETRY**. This is a synthetic aggregation result, not a scientific field result.

The repair reduces every eligible pair-derived scalar or category to one state
value before match distributions, inverse-ECDF percentiles and equal-match
macro summaries. It leaves edge eligibility, ordering semantics, Spearman,
non-pair summaries, field mathematics, integration and all execution controls
unchanged. Session 14R7 remains historically **D / readiness 3** and was not
reopened.

The closed evidence is in
[the Session 14aj output package](../outputs/session14_pair_aggregation/manifest.json).
Its manifest binds the protocol, tested implementation, frozen R7 authority and
all ten evidence files.

## 36-item final handoff

1. **Starting HEAD:**
   `be8de6996c7a2dd79ec0ae2714bf445617e64741`, initially clean and equal to
   local `origin/main` and live GitHub `main`.
2. **Ending HEAD:** the third closure commit reported in final delivery after it
   is pushed and verified.
3. **Protocol:**
   [Phase 14aj](protocols/phase_14aj_within_state_pair_aggregation.md), commit
   `930a96bea58ba720f6dad5af12ac34e08f4d7a9c`, SHA-256
   `32d7c1ad2e98563fc498fbb7f5db797d304c9117b7a2932e8b986d62a975cbd0`.
4. **Exact R7 defect:** the inherited collector assigned each pair a fraction of
   its state's weight, which preserved the mean, but calculated extrema and
   inverse-ECDF percentiles over individual pair values rather than over the
   required state means. States `[0,1]` and `[1,1]` therefore produced median
   `1.0` and minimum `0.0`, instead of `0.5` and `0.5`.
5. **Weighting hierarchy:** equal match → equal state within match → arithmetic
   mean of eligible pairs within state.
6. **Pair-family inventory:** ten families were traced in
   [pair_family_inventory.csv](../outputs/session14_pair_aggregation/pair_family_inventory.csv):
   candidate field differences; candidate Spearman; candidate ordering;
   opposing raw-distance order; opposing field order; endpoint/segment
   ordering; endpoint/segment Spearman; Session 13 support Jaccard;
   overlap/redundancy Spearman; and unavailable/constant groups.
7. **Unit classifications:** candidate differences and support Jaccard are
   `state_pair_mean`; ordering indicators become `state_pair_proportion`;
   within-state Spearman remains `state`; across-state Spearman remains
   `match`; empty groups remain unavailable. No R7 public family is retained as
   a raw-pair distribution.
8. **Within-state rule:** finite eligible scalar values use `math.fsum(values) /
   len(values)`. Exclusive category indicators use the same reducer and become
   proportions. Raw values are retained only while forming that state value.
9. **Percentile rule:** one eligible state value enters the existing inverse
   empirical CDF; the 5/25/50/75/95 percentile is the first ordered value whose
   cumulative normalized weight reaches the requested probability.
10. **Match aggregation:** assessable state summaries have equal weight inside
    their match. Match means are means of state summaries, and match
    percentiles use the state-summary distribution.
11. **Macro aggregation:** represented matches have equal weight. The macro
    mean is the mean of represented match means. Macro percentiles weight each
    state `1 / represented matches / assessable states in its match`.
12. **Unavailable states:** zero eligible pairs means unavailable, with no zero
    imputation. Total, assessable and unavailable state denominators remain
    explicit.
13. **Helper implementation:** the unreleased
    [pair aggregation module](../src/defensive_network_disruption/validation/pair_aggregation.py)
    supplies immutable raw/state records, scalar and categorical state
    reduction, inverse-ECDF summaries and match/macro aggregation. The
    [synthetic runner](../scripts/session_14aj_pair_aggregation.py) inventories,
    audits, closes and verifies the package.
14. **Unequal-pair-count oracle:** one state with one `0` pair and one with one
    hundred `1` pairs returns equal-state mean `0.5`; raw pooling would return
    `0.9900990099009901`. Source pairs remain `101`; published state summaries
    are `2`.
15. **Percentile adversarial oracle:** state values `[0.5,1.0]` return minimum,
    q05, q25 and q50 `0.5`; q75, q95 and maximum `1.0`. All seven checks passed.
16. **Unequal-match-size oracle:** one `0` state in the small match and one
    hundred `1` states in the large match return macro mean `0.5`, rather than
    pooled-state mean `100/101`. Both matches are represented equally.
17. **Ordering-category oracle:** a hundred agreement pairs in one state and one
    reversal pair in another produce mean state proportions `0.5` for each
    category, rather than raw proportions `100/101` and `1/101`.
18. **Unavailable-state oracle:** among an empty, a one-pair and a multiple-pair
    state, totals are `3 / 2 assessable / 1 unavailable`; no zero is inserted.
19. **Single-pair oracle:** the one pair at `0.25` becomes state value `0.25`
    exactly. Together with the `[0,1]` state mean, the assessable mean is
    `0.375`.
20. **Pair eligibility invariance:** the reducer never selects pairs. The R7
    regression retains all four raw pairs while publishing two state summaries;
    all synthetic count checks agree before and after reduction.
21. **Non-pair invariance:** endpoint, segment-average, union-minus-maximum,
    state multi-edge, Session 13 direct-state and non-pair candidate summary
    oracles reproduce the historical summary dictionary exactly, including
    mean `0.625` and every percentile.
22. **Tie/order invariance:** exact ties, the inherited absolute `1e-12`
    block-anchor rule, candidate order and the five ordering categories remain
    unchanged. Spearman remains a within-state correlation with average exact
    tie ranks; constant inputs remain unavailable.
23. **Exact R7 regression:** the historical and repaired means both equal
    `0.75`. The repaired minimum/q05/q25/q50 are `0.5`; historical values were
    `0/0/0/1`. Repaired output equals the prospectively frozen expected summary.
24. **All-family audit:** all ten inventoried paths record raw, state, match,
    macro and percentile-input units. Scalar pair distributions and categorical
    pair distributions must pass through state reduction; already-state and
    already-match correlations are not re-reduced.
25. **Classification:** **A — WITHIN-STATE PAIR AGGREGATION REPAIRED**. All
    fourteen governed evidence checks passed, along with inventory, pair-count,
    ordering and non-pair invariants.
26. **Readiness:** **1 — READY FOR A FRESH SEPARATELY GOVERNED SESSION 14R
    EMPIRICAL RETRY**. This readiness does not authorize that retry itself.
27. **Historical R7:** byte-identical R7 runner SHA-256
    `2bb467f03fc78b44a51ee13fb654813aac58f623c5a14c9f7ebffd42e5f3e00e`;
    manifest SHA-256
    `4cee379c77e9d5dcea11ff5affb4866834ed1abb6e56fa361dac30787860c9cf`.
    Its D/readiness-3 closure and empty access history remain unchanged.
28. **Numerical/lifecycle authority:** unchanged. Historical representation
    summary source SHA-256 remains
    `d0957593d9aa092160b5e890c49987ca6096c1429dfc0a7b9d2daa0388c033c9`.
    No field, integration, owner, launch, lifecycle, exposure or publication
    implementation was edited.
29. **Empirical access:** zero real states and zero real edges opened. The audit
    has no data or acquisition route.
30. **R7 scientific outputs:** none inspected. The audit read only committed R7
    code, protocol/report and compact authority/manifest evidence needed to bind
    the synthetic defect.
31. **Tests:** focused **14 run / 14 passed / 0 skipped**; relevant 14aj/R7/14ai
    **59 / 59 / 0**; full local suite **713 / 710 / 3 retained skips**.
    Compilation passed. The retained skips are historical placeholders, not
    Session 14aj failures.
32. **Python 3.11 CI:** final closure delivery gate; its actual result is
    reported after the closure commit completes ordinary CI.
33. **Python 3.13 CI:** final closure delivery gate; its actual result is
    reported after the closure commit completes ordinary CI.
34. **Distribution CI:** final closure delivery gate. Package version,
    dependency metadata and public exports are unchanged.
35. **Commits and push:** protocol `930a96b`; tested implementation
    `91693a5`; this report, outputs and append-only log form the third closure
    commit. Final delivery records its full hash and synchronization.
36. **Exactly one recommendation:** separately govern a fresh Session 14R
    empirical representation retry using the repaired within-state pair-summary
    aggregation contract.

## Validation and preservation

The governed audit ran once after the tested implementation commit. The output
package contains exactly the ten named evidence files plus `manifest.json`; its
ignored exclusive marker prevents an automatic rerun. Publication checking
recomputed all hashes and rejected unexpected public membership. JSON is finite
and canonical; CSV uses LF endings. Public artifacts contain synthetic fixture
names and aggregate values only.

Compilation, documentation links, history hashes, output membership, schemas,
privacy terms, deterministic serialization and whitespace checks passed locally.
The claim ledger, README, public API, package version, dependencies, field
mathematics, numerical authority, lifecycle machinery and every historical
output remain unchanged. Accessibility remains **PROXY ONLY** and suppression
remains **NOT SUPPORTABLE**.
