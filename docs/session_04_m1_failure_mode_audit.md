# Session 4 M1 failure-mode audit

Date: 2026-09-10. Starting authority:
`3e7e517108a782ede32e7bf55e2dfb020f3c841f`. Protocol commits: `8fc0630`
and prospective decision-frame amendment `212a223`. Source: SkillCorner Open
Data `02a396ffd09b283c9f092fdedeff11da6d535b66`.

## Decision

**B — SPECIFIC MULTI-DEFENDER FAILURE MODE IDENTIFIED.** M1 uses two useful,
distinct static relationships, but both are minima. It assigns exactly the same
features and utility to the frozen synthetic connection with one defender at
`(15,2)` and the connection with defenders at `(5,2)`, `(10,2)`, and `(15,2)`.
The continuous second- and third-nearest segment-distance gaps are non-degenerate
in all nine development matches, so this collapse removes structure that varies
in the observed population.

This finding justifies one prospective question, not an M2 implementation:

> Does one prospectively specified continuous multi-defender attenuation summary
> add receiver-ranking information beyond the frozen M1 minima?

The proposed family is a sum of continuous defender influences over the finite
connection. Its kernel, scale, normalization, interpretation, and comparison
protocol remain unset and require a separate Session 5 protocol. Reachability is
also a real representational blind spot, but it fails the stricter causal-input
gate in this session.

Accessibility remains **PROXY ONLY**. Suppression remains **NOT SUPPORTABLE**.
The closed Session 3 metrics and interpretation did not change.

## Access and population

The audit used all 7,227 closed choice states from the same nine development
matches. It opened only the existing closed population/QC artifacts, development
metadata, the eight event fields permitted by Amendment 1, and native tracking
frame/identity/coordinate/detection fields. Event fields were used only to recover
the frozen decision-frame keys and reproduce defender membership.

The ten reserved matches, withheld match `1953632`, pose products, vendor Passing
Option scores, and new provider products remained unopened. No real attempt was
ranked, selected, plotted, or inspected as a football passage. No prediction
error or M0/M1 improvement was examined.

The closed coefficient vectors were already available in the public Session 3 QC
artifact and were inspected during planning. This prior closed-result exposure was
recorded before new row-level access. The first aggregate execution stopped at
JSON serialization because a NumPy boolean was not converted to a Python boolean.
Only the coefficient summary, which duplicates closed Session 3 QC values, had
been written locally; no new feature/geometry result or model score was displayed.
The type boundary and atomic serialization were fixed, and the same frozen audit
was rerun without changing a diagnostic. No access-boundary deviation occurred.

## Closed coefficient audit

All coefficients are for standardized inputs. Their magnitudes describe the
closed conditional-choice model and are not causal importance.

| Model feature | Fold signs | Minimum | Median | Maximum |
| --- | --- | ---: | ---: | ---: |
| M0 distance | 9 negative | -1.2174 | -1.1963 | -1.1810 |
| M0 longitudinal displacement | 9 positive | 0.2043 | 0.2398 | 0.2872 |
| M0 lateral displacement | 9 negative | -0.0404 | -0.0305 | -0.0134 |
| M1 distance | 9 negative | -1.6492 | -1.6236 | -1.5943 |
| M1 longitudinal displacement | 9 positive | 1.5062 | 1.5482 | 1.5774 |
| M1 lateral displacement | 9 negative | -0.0341 | -0.0272 | -0.0163 |
| M1 receiver-nearest defender distance | 9 positive | 1.1919 | 1.2150 | 1.2536 |
| M1 finite-segment defender distance | 9 positive | 0.4553 | 0.4924 | 0.5013 |

The two positive defensive signs mean that, holding other fitted inputs fixed,
greater defender distance raises M1 utility in every fold. This is fitted model
behavior, not calibrated accessibility or defensive causation.

## Complementarity and observed geometry

The defensive measures are related without being interchangeable. Their pooled
candidate-level Pearson correlation is 0.3312 and Spearman correlation is 0.3476.
The equal-match, within-choice centered Pearson correlation is 0.3882. Their
two-feature within-choice condition number is 2.27 with full rank; the complete
five-feature M1 condition number is 16.00 with full rank. The two raw defensive
measures disagree on the ordering of 34.78% of comparable candidate pairs when
comparisons are restricted within a choice state.

Equal-match mean match medians are 23.29 m for connection length, 6.31 m for
receiver-nearest defender distance, and 1.51 m for minimum finite-segment distance.
The second-minus-first segment-distance gap has an equal-match median of 1.57 m;
the third-minus-first gap has an equal-match median of 4.06 m. Both continuous gap
distributions pass the numerical non-degeneracy rule in every match. No defender
radius or outcome-driven threshold was introduced.

## Synthetic model behavior

With a fixed 40 m longitudinal connection and segment distance held at 2 m, the
median utility changes relative to a 20 m receiver-nearest distance are -2.499 at
2 m, -2.082 at 5 m, -1.388 at 10 m, 0 at 20 m, and +2.776 at 40 m. With receiver
distance held at 20 m, segment-distance changes relative to 20 m are -4.398 at
0 m, -4.178 at 1 m, -3.958 at 2 m, -3.298 at 5 m, -2.199 at 10 m, and 0 at 20 m.
The valid joint grid is monotone in both defensive distances in every fold.

These values are changes in linear utility under synthetic feature perturbations.
They are not probabilities or calibrated accessibility values. Their fold ranges
and complete joint grid are retained in the compact geometry output.

M1 necessarily gives identical utility to equal static geometry with a defender
moving toward or away from the lane because velocity is absent. A backward
position difference is structurally available for 79,442 of 79,497 decision-state
defender instances (99.93%). Only 53,879 current instances (67.77%) are detected;
the remainder are marked extrapolated. More importantly, authoritative provider
documentation does not establish that the supplied coordinates exclude future-
aware smoothing or extrapolation. Past-only computation is therefore feasible,
but causal velocity input is **BLOCKED** under the selected strict gate.

For the 5 m versus 30 m synthetic connections, the defensive feature contribution
is identical while total median utility changes by -1.128 through the existing
attacking-geometry terms. M1 therefore represents pass length and obstruction
additively but cannot express a travel-time or length-by-obstruction interaction.
Building that interaction would require assumptions about ball speed, trajectory,
defender speed and acceleration, reaction time, and interception logic. None was
selected here.

## Reuse and later research

Floodlight's `VelocityModel` exposes backward differentiation, which is the only
documented library primitive aligned with a future past-only velocity rule; its
central-difference default would violate that rule. DataBallPy's pitch-control
example sums velocity-aware player influence and is a useful aggregation
comparison, but it does not directly define finite-route interception for this
project. Dick, Link and Brefeld remains the closest reachability/availability
precedent. DEFCON is a broader learned defensive-value and attribution framework,
not the primitive needed for this narrowly scoped extension. No library was
installed or executed.

Orientation-conditioned visibility remains a separate future hypothesis and a
proxy for body/viewing direction, not visual attention. No skeletal data was
opened. A future network could summarize validated outgoing edge weights and ask
how a pass changes the receiver's next outgoing structure, but no centrality,
graph feature, or network metric is authorized before the edge measurement is
validated.

## Verification and stop

Production tests cover coefficient-source hashes, finite-segment order statistics,
weighted within-choice correlation, pair ordering, numerical non-degeneracy,
synthetic monotonicity, velocity invariance, pass-length additivity, and the
one-versus-many collapse. The runner blocks prohibited match IDs, unsafe paths,
optimizer imports/calls, repeated completed audits, private identifiers, and
reconstructive public fields.

Session 3 hashes matched before and after the audit. Public outputs contain stable
aliases and aggregates only. Detailed access records remain ignored. Session 4
stops here without M2, M1 refitting, scored-passage analysis, orientation, network
features, reserved evaluation, or Session 5.
