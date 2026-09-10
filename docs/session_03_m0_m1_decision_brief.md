# Session 3 M0/M1 development decision brief

Date: 2026-09-10. Starting authority: `5fcef6b`. Protocol commit:
`1dddb6f`. Score-free population and execution commit: `54dc4f8`. Source:
SkillCorner Open Data `02a396ffd09b283c9f092fdedeff11da6d535b66`.

## Decision

The frozen development comparison found consistent incremental receiver-ranking
information in the two transparent defensive-geometry features. Match-macro MRR
was 0.48177 for M0 and 0.56779 for M1, an absolute difference of 0.08602. All
nine held-out matches had positive paired MRR differences; their median difference
was 0.08373. Match-macro Hit@1 increased from 0.25245 to 0.35464 and Hit@3 from
0.62510 to 0.72731. The secondary metrics agree with the MRR direction.

This is one development-only result using a useful vendor target label with
limitations. No practical-effect threshold or inferential test was specified, so
the result is described as consistent rather than declared practically meaningful
or externally validated. Accessibility remains **PROXY ONLY**. Suppression remains
**NOT SUPPORTABLE**. M2 is deferred until a separate, prospective proposal names a
specific limitation worth testing; aggregate improvement does not authorize it.

## Frozen population and reconciliation

The runner re-derived 7,292 pass attempts from the nine development matches.
The mutually exclusive waterfall removed 56 missing, ambiguous, or unusable
targets and nine invalid carrier states. The 56 target exclusions comprise the
55 missing labels already reported in Session 2 and the single remaining
target/candidate mismatch, which was structurally a provider self-target. A
self-target cannot be a receiver under the frozen non-carrier candidate rule and
was therefore classified as an unusable label before fitting.

The final common population has 7,227 evaluation-eligible and 7,227 fit-eligible
attempts. There are no retained target-outside observations, empty candidate sets,
empty defender sets, stale/ambiguous frames, or transition failures. Evaluation
and fit counts remain distinct fields in every public match/fold record even
though they coincide here. The population SHA-256 is
`cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d`.

| Alias | Raw attempts | Evaluation | Fit | Excluded labels | Invalid carriers |
| --- | ---: | ---: | ---: | ---: | ---: |
| development_01 | 902 | 885 | 885 | 15 | 2 |
| development_02 | 820 | 801 | 801 | 18 | 1 |
| development_03 | 963 | 952 | 952 | 11 | 0 |
| development_04 | 878 | 877 | 877 | 0 | 1 |
| development_05 | 861 | 861 | 861 | 0 | 0 |
| development_06 | 630 | 629 | 629 | 0 | 1 |
| development_07 | 766 | 764 | 764 | 0 | 2 |
| development_08 | 736 | 734 | 734 | 0 | 2 |
| development_09 | 736 | 724 | 724 | 12 | 0 |

## Implementation and scientific controls

Candidates were constructed before labels from same-team, non-carrier players
with a unique identity, a verified active interval, and finite current coordinates.
Goalkeepers and backward options were included; no distance or offside filter was
applied. Defenders used the corresponding active/current rules. Coordinates were
oriented only from verified team-period direction metadata.

Every state used the latest same-period frame strictly before the provider pass
transition, no more than 100 ms old, with integer-microsecond clock parsing. No
interpolation, period bridge, or offset adjustment was used. The 100 ms value
remains a prospective cadence-based tolerance rather than a timing truth claim,
and the benchmark remains offline because extrapolated tracking has not been
shown to exclude future frames.

M0 used carrier-receiver distance and signed longitudinal/lateral displacement.
M1 used the exact standardized M0 columns plus nearest-defender distance to the
receiver and minimum defender distance to the finite carrier-receiver segment.
No degenerate segment occurred; the `1e-9` metre branch remains a floating-point
implementation tolerance without football meaning. M0+ was omitted.

Both models used unregularized conditional softmax with equal match weighting,
analytic gradients, training-fold-only standardization, and nine leave-one-match-
out folds. All 18 fits had full within-choice rank, no complete or quasi separation,
successful L-BFGS-B termination, finite values, and maximum absolute gradients
below `1e-6`. M0's standardized columns were exactly equal inside M1. There was
no randomness, penalty, fallback, feature search, or hyperparameter search.

## Development results

| Alias | M0 MRR | M1 MRR | M1 − M0 |
| --- | ---: | ---: | ---: |
| development_01 | 0.49111 | 0.57485 | 0.08373 |
| development_02 | 0.49587 | 0.57265 | 0.07678 |
| development_03 | 0.47538 | 0.57996 | 0.10458 |
| development_04 | 0.50230 | 0.58736 | 0.08506 |
| development_05 | 0.50580 | 0.57751 | 0.07171 |
| development_06 | 0.47055 | 0.54336 | 0.07281 |
| development_07 | 0.44673 | 0.54201 | 0.09528 |
| development_08 | 0.44590 | 0.55516 | 0.10927 |
| development_09 | 0.50226 | 0.57720 | 0.07494 |

The mean paired MRR difference is 0.08602 and the median is 0.08373, with nine
positive, zero negative, and zero tied matches. Match-macro Hit@1 and Hit@3
differences are 0.10219 and 0.10221. Pooled descriptive MRR is 0.48272 for M0
and 0.56914 for M1; pooled values are secondary because the protocol's target is
equal match weighting. No target tie blocks occurred.

The comparison supports the narrow statement that these two defensive geometry
relationships add receiver-selection ranking information beyond the frozen
attacking-geometry baseline in these development matches. It does not show that
the score is calibrated accessibility, that defenders caused a choice, or that
an option was suppressed.

## Integrity, access, and closure

Only the same nine development matches and the three Session 2 local products
were opened. The ten prospectively reserved matches and withheld match `1953632`
were not requested or opened. Session 1's **A — PRESERVED** reservation verdict
and its mechanical over-read qualification remain unchanged. No football passage,
per-attempt score, ranking, coordinates, timestamp, or identity-linked result was
inspected for interpretation or published.

The initial output formatter omitted the required pooled descriptive summary and
public preprocessing/model parameter record. The initially scored files were
preserved with hashes in ignored local storage. Those two records were derived
from the already frozen match outputs and fitted parameters without any refit or
rescore. This did not change the population, match metrics, paired differences,
or interpretation. Corrective reruns are now explicitly blocked when scored
outputs exist.

The committed package contains only stable aliases, aggregate counts, match-level
metrics, fit diagnostics, parameters, hashes, and this report. Candidate rows,
identities, coordinates, timestamps, utilities, rankings, and detailed access
material remain ignored. Session 3 stops here without M2, orientation, network
features, reserved evaluation, scored-passage review, or Session 4.
