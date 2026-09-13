# Phase 14aj — Within-state pair-summary aggregation repair

**Frozen:** 2026-09-13  
**Starting authority:** `be8de6996c7a2dd79ec0ae2714bf445617e64741`  
**Scope:** synthetic aggregation and statistics only

## Question and boundary

Session 14aj asks whether the summary layer can enforce the Session 14R7
weighting hierarchy for every pair-derived family while leaving pair
eligibility, ordering semantics, non-pair summaries, numerical fields,
execution controls and historical evidence unchanged. Session 14R7 remains
**D — BLOCKED / readiness 3** and is not resumed.

No development geometry, provider product, target, outcome, model, option
share, protected/formerly-reserved/withheld record, pose, xT, progression or
Session 14R7 scientific partial output is authorized. This phase produces no
scientific result and changes no claim.

## Frozen defect

The inherited collector retained one list of eligible pair values per state.
Its mean happened to receive equal state weight, because each pair in a state
was assigned `1 / pairs_in_state` of that state's weight. Its extrema and
inverse-ECDF percentiles nevertheless operated on the individual values. They
therefore described a weighted raw-pair support rather than the required
distribution of state summaries. In the frozen R7 oracle, states `[0, 1]` and
`[1, 1]` correctly have state means `[0.5, 1]`; the historical median was `1`
instead of the required `0.5`, and its minimum was `0` instead of `0.5`.

## Observational units and family inventory

The repair will encode these units explicitly:

| R7 family | Raw construction | Frozen published unit | Classification |
| --- | --- | --- | --- |
| Candidate-family field difference, paired on receiver edge | one signed difference per aligned edge | one arithmetic mean per eligible state | **B — STATE-EQUAL SUMMARY** (`state_pair_mean`) |
| Candidate-pair Spearman across aligned edges | one correlation per state | state correlation | **B — STATE-EQUAL SUMMARY** (`state`); never reduce its rank terms |
| Candidate-family ordering: agreement, reversal, tie creation/removal, both tied | eligible unordered edge pairs | one proportion per category per state | **C — CATEGORICAL STATE SUMMARY** (`state_pair_proportion`) |
| Opposing receiver/corridor raw-distance order | eligible unordered edge pairs after frozen tie exclusion | one disagreement proportion per state | **C — CATEGORICAL STATE SUMMARY** |
| Field order on opposing receiver/corridor pairs: endpoint-following, corridor-following, tied | frozen opposing pairs | one proportion per category per state | **C — CATEGORICAL STATE SUMMARY** |
| Endpoint-versus-segment field ordering categories | eligible unordered edge pairs | one proportion per category per state | **C — CATEGORICAL STATE SUMMARY** |
| Endpoint-versus-segment Spearman | one correlation per state | state correlation | **B — STATE-EQUAL SUMMARY** (`state`) |
| Session 13 top-k support-set Jaccard between edge pairs | unordered edge pairs | arithmetic mean within state, already stored in the state descriptor | **B — STATE-EQUAL SUMMARY** (`state_pair_mean`) |
| Across-state overlap/redundancy Spearman | correlation over state descriptors inside each match | one match correlation | **B — STATE-EQUAL SUMMARY** (`match`); its state inputs remain state summaries |
| Empty or constant/insufficient versions of the above | no assessable state value | unavailable | **D — UNAVAILABLE / NOT USED** |

No retained R7 output is intentionally published as a raw-pair distribution.
Raw values remain internal only long enough to form their state summary. Edge
endpoint fields, segment-average fields, union-minus-maximum values, direct
edge geometry, field-owner availability and other explicitly edge-level
families are not pair-derived and remain governed by their existing equal
match → state → edge weights.

## Frozen aggregation contract

The hierarchy is:

`equal match weight → equal state weight within match → eligible pairs averaged within state`.

For a scalar pair family with eligible values \(x_{msp}\), the retained state
value is

\[
\bar x_{ms}=\frac{1}{n_{ms}}\sum_{p=1}^{n_{ms}}x_{msp}.
\]

For categorical pair families, each category indicator is reduced by the same
formula, producing within-state category proportions that sum to one when the
state is assessable. A state with one eligible pair retains that pair's scalar
or one-hot category value. A state with no eligible pair is unavailable; it is
not assigned zero and does not enter the represented-state denominator.

Within a match, means and inverse-ECDF 5/25/50/75/95 percentiles operate on the
one retained value per assessable state. The inverse empirical CDF returns the
first ordered value whose cumulative normalized weight is at least the
requested probability. Match means give states equal weight.

The macro mean is the arithmetic mean of represented match means. A macro
percentile, when a frozen output row requires one, applies the same inverse-ECDF
rule to state summaries with weights `1 / represented_matches /
assessable_states_in_match`; it never pools raw pairs and never lets a larger
match dominate. No new percentile family is introduced.

Counts retain separate meanings: `source_observations` records the number of
raw eligible pairs; `observations` records published state summaries for pair
families; `states_assessable` is the number of retained state values. Unit
metadata must distinguish `edge`, `state`, `state_pair_mean`,
`state_pair_proportion`, `match`, and `macro_match` wherever applicable.

## Repair design and invariants

One internal, unreleased aggregation module will provide explicit pair-to-state,
state-to-match and equal-match operations. The future R path may call it; no
historical runner or output is rewritten. Every pair-derived serialization path
must pass through the state reduction or declare an already-reduced `state` or
`match` unit. The helper rejects nonfinite values, duplicate state keys,
unsupported units, invalid weights and mixed category denominators.

Pair eligibility, candidate order, exact ties, the absolute `1e-12`
block-anchor ordering rule and the five ordering categories remain unchanged.
Spearman stays within-state with average ranks for exact ties. No Pearson,
significance test, bin, threshold or post-result statistic is introduced.

Non-pair endpoint, segment-average, union-minus-maximum, multi-edge, direct
Session 13 and candidate metrics must reproduce their historical synthetic
summaries exactly. Field formulas, integration, canonical partitions,
certification, launch, lifecycle, exposure and publication machinery are out of
scope and must remain byte-identical.

## Prospective synthetic oracles

The governed implementation must pass:

1. one pair at `0` versus one hundred pairs at `1`: equal-state mean `0.5`, not
   pooled mean `100/101`;
2. the exact R7 `[0,1]`, `[1,1]` regression: state distribution `[0.5,1]`,
   median `0.5`, minimum `0.5`;
3. unequal match sizes: states equal within match and represented matches equal
   in the macro mean and weighted macro percentiles;
4. categorical imbalance: proportions are formed per state before aggregation;
5. unavailable, one-pair and multiple-pair states with exact denominators and
   no zero imputation;
6. unchanged pair counts and category assignments before and after reduction;
7. exact tie/order behavior and deterministic serialization;
8. exact non-pair summary invariance; and
9. a complete inventory trace from raw calculation through serialized unit.

Fixtures are synthetic engineering records. The one governed audit executes
the inventory and these oracles once after the tested implementation is
committed. Unexpected failure after exposure is retained and closes the phase
without repair or rerun.

## Outputs, classification and stop rules

The audit creates only the eleven specified files under
`outputs/session14_pair_aggregation/`, plus the report and one append-only
research-log entry. Public artifacts contain synthetic values, unit metadata,
counts and hashes only. Schemas require finite JSON, deterministic LF CSV,
explicit denominators, atomic writes and a manifest binding protocol,
implementation, environment and output hashes.

Classification is exactly one of:

- **A — WITHIN-STATE PAIR AGGREGATION REPAIRED**: every family is inventoried,
  state-first and equal-match rules pass, unavailable and percentile behavior
  pass, non-pair summaries remain exact and the R7 regression passes.
- **B — PAIR-FAMILY UNIT SEMANTICS REMAIN AMBIGUOUS**.
- **C — MATCH/MACRO WEIGHTING REMAINS DEFECTIVE**.
- **D — PERCENTILE CONTRACT REMAINS DEFECTIVE**.
- **E — MULTIPLE ISSUES**.
- **F — UNRESOLVED**.
- **G — INVALID / EXECUTION FAILURE**.

Readiness is independently 1 (fresh separately governed empirical retry), 2
(one small repair remains), 3 (summary design needs revision), or 4 (more
evidence required). Only A can earn readiness 1.

Validation comprises focused 14aj, relevant 14R7/14-series and full tests;
compilation; schemas/hashes; privacy/publication checks; documentation links;
historical-byte and append-only checks; staged inspection; `git diff --check`;
and ordinary Python 3.11, Python 3.13 and distribution CI. The phase then stops.

