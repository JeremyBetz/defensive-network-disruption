# Data dictionary notes

Status: Stage A schema and metadata inventory complete; **not yet a verified
tracking/event data contract**. Distinguish BRIEF EXPECTATION, DOCUMENTED,
VERIFIED IN SELECTED RELEASE, UNVERIFIED, and BLOCKED.

## Availability and release identity

The [official Cup 2.0 dataset page](https://pysport.org/analytics-cup/editions/analytics-cup2/datasets)
lists 175-game season physical aggregates, 20 XY games including 10 new games,
Dynamic Events for those 10 games, and 2 Body Pose games. The user-supplied
[SkillCorner repository](https://github.com/SkillCorner/opendata) overview still
describes 10 tracking games. Reconcile the release, product coverage, and previous
edition overlap through metadata; do not resolve this by assuming all 20 have
events or that the root README is a complete inventory.

Selected release: commit `02a396ffd09b283c9f092fdedeff11da6d535b66`,
tree `44fd5081d0e6a441dbafadd12c51d6ffca8ab98b`.

| Stage A finding | Status |
| --- | --- |
| 20 unique match directories; metadata, tracking, Dynamic Events, and phases entries for every directory | VERIFIED FILE PRESENCE |
| Four metadata schema variants; two Dynamic Events header variants; one phases header variant | VERIFIED OUTPUT; ACQUISITION DEVIATION RECORDED |
| Tracking entries are LFS pointers with recorded payload SHA-256 and declared size | VERIFIED POINTER IDENTITY |
| Tracking payload hashes, payload schema, usable event rows, product joins, and record coverage | UNVERIFIED |
| Official 20 tracking games including 10 new; Dynamic Events for those 10 | DOCUMENTED, NOT A LOCAL COVERAGE CLAIM |

## Documented clues requiring release-specific checks

Source: [SkillCorner Open Data README](https://github.com/SkillCorner/opendata),
reviewed 2026-09-09. These facts guide verification; no loader defaults follow.

| Concept | Documented clue | Required local verification |
| --- | --- | --- |
| Tracking files | `{id}_tracking_extrapolated.jsonl`; match metadata in `{id}_match.json`. | Exact release paths, schema version, record shape. |
| Space | Metres; pitch-centred origin; x along length, y along width. | Axis signs, actual dimensions, direction per period, any normalization. |
| Time | Tracking described at 10 fps with frame, timestamp, and period. | Clock origin, resets, stoppages, irregular intervals, frame/event joins. |
| Identity / ball | `player_data`, `ball_data`, and possession player/group fields. | Stability, missingness, substitutions, keeper and team mapping. |
| Observation quality | `is_detected` distinguishes detections and extrapolations. | Meaning and availability per product; exclusions and uncertainty. |
| Events | Event IDs are match-scoped; event coordinates need scaling attention. | Composite keys, exact units, timestamps, pass/receipt semantics. |
| Pose | 25 fps, 29 joints, detected players only; XY/pose misalignment is possible. | Orientation derivation, uncertainty, interpolation and synchronization. |
| Vendor model labels | EPV, pressure, and passing-option fields are described. | Provenance, decision-time availability, leakage, and validation independence. |

## Receiver-related event schema

Every Dynamic Events header in the selected release contains
`targeted_passing_option_event_id`, `player_targeted_id`, `targeted`, `received`,
`pass_outcome`, and `pass_outcome_id` (**VERIFIED PRESENCE ONLY**). The vendor
documentation describes distinct targeting, receipt, and outcome semantics.

Passing Option events are partly generated using a vendor receiver model and a
score/duration rule; targeted receivers receive an event independently of that
threshold. Therefore they are not independent availability labels and cannot
define this project's candidate set. Values, completeness, joins, and timing are
**BLOCKED BY SESSION 1 SCOPE**.

The original schema reader requested 65,536 bytes per CSV rather than stopping
its application read at the header terminator. The column-presence finding is
supported by the retained header-only output, but strict header-only acquisition
is not verified and is superseded by the L004 deviation record.

## Contract still to specify

For every field used later, record product, exact source name/type, units,
null semantics, identity scope, clock, coordinate frame, derivation, quality
flags, source/version, and allowed role (input, outcome, stratifier, or audit
only). Preserve provider fields before transforming them. Record every join's
cardinality and reject unexplained duplicates or absent keys.

Unresolved decisions include possession and in-play eligibility, attack direction,
boundary handling, missing ball/player treatment, smoothing/velocity estimation,
event synchronization tolerances, airborne-pass scope, receiver eligibility,
offside handling, and pose confidence. No standard pitch size, inferred keeper
rule, universal sampling frequency, or imputation behavior is hard-coded.

The future local manifest should include source commit/release, acquisition date,
terms reference, relative product paths, file sizes/checksums, match/product
membership, and prior exposure status. Keep manifests with identifiers in
`data/manifests/` until public release eligibility is reviewed. Define the split
only after metadata coverage and sister-project overlap are understood.

## Session 2 verified development contract

The following facts apply to the nine development matches at source commit
`02a396ffd09b283c9f092fdedeff11da6d535b66`; they are not reserved-set findings.

| Field or object | Source | Decision-time status | Future/vendor derived | Allowed role | Notes |
| --- | --- | --- | --- | --- | --- |
| frame, period, timestamp | tracking V3 | Yes, under strict prior-frame rule | No | Feature key | 10 Hz; same period required |
| player x/y and identity | tracking V3 | Yes | Extrapolation provenance unresolved | Feature with native quality sidecar | Pitch-centred metres; do not clip |
| player `is_detected` | tracking V3 | Yes | Provider quality flag | Quality/filter input | Lost by Kloppy |
| ball x/y/z, `is_detected` | tracking V3 | Yes | Extrapolation provenance unresolved | Context/quality candidate | Lost detection flag in Kloppy |
| possession player/group | tracking V3 | Yes | Provider-derived semantics | Audit/context candidate | Preserve native sidecar |
| image projection | tracking V3 | Yes | Calibration product | Audit only | Lost by Kloppy |
| pass event end frame/time | Dynamic Events | Observation key | Event derivation | Alignment/selection only | Operational pass transition |
| `player_targeted_id` | Dynamic Events | No | Vendor target provenance limited | Label only | Present on 99.25% of passes |
| `targeted_passing_option_event_id` | Dynamic Events | No | Vendor event linkage | Label audit only | Resolves on 92.66% of passes |
| `targeted` | Dynamic Events | No | Vendor-derived | Label audit only | Never candidate membership |
| `received`, `pass_outcome` | Dynamic Events | No | Outcome | Label/stratifier only | Prohibited predictor |
| option ease/probability/score | Dynamic Events | No | Vendor model-derived | Comparison only | Never ground truth or predictor |
| post-pass/future trajectory | tracking/events | No | Future-derived | Prohibited | Includes centred/future smoothing |

Kloppy 3.19.0 is **SAFE WITH NATIVE SIDECAR**. It preserved player sets and
player/ball coordinates in SkillCorner coordinates over the prespecified 5,400
frames, but did not preserve detection flags, possession-player identity, or
image-projection fields in frame `other_data`.

Candidate validity requires same-team metadata, active playing interval, current
finite tracking coordinate, and exclusion of the carrier. Goalkeeper and backward
options remain included, no distance limit is applied, and offside filtering is
deferred. These are development-feasibility rules, not model-selected choices.

## Session 3 frozen benchmark fields

The following contract was executed only on the nine development matches.

| Derived field | Inputs | Role | Verified handling |
| --- | --- | --- | --- |
| decision frame | period and integer-microsecond event/tracking clocks | offline feature-state key | latest strictly earlier same-period frame, age ≤100 ms; no interpolation or offset tuning |
| attacking x/y | native x/y plus verified team-period direction | feature coordinate | `x'=s*x`, `y'=y`; unknown direction blocks state |
| candidate membership | roster team, carrier ID, exact period interval, current finite coordinate | choice-set construction | label/vendor-option independent; keeper/backward included; no distance/offside filter |
| defender membership | opponent team, exact period interval, current finite coordinate | M1 geometry | empty set blocks common comparison population |
| M0 distance/dx/dy | carrier and candidate attacking coordinates | predictor | exact three-column defender-free baseline |
| nearest receiver-defender distance | candidate and active opponents | M1 predictor | decision-state geometry only |
| finite-segment defender distance | carrier, candidate, active opponents | M1 predictor | analytic clipped projection; `1e-9` m is an implementation tolerance only |
| target player ID | Dynamic Events | label only | self-target is unusable; candidate admission never uses target |

The finalized development population contains 7,227 fit/evaluation states from
7,292 pass attempts. Fifty-six attempts have an unusable target label and nine
have an invalid carrier state under the frozen waterfall. No target-outside state
remains. These counts supersede Session 2's preliminary ten mismatch descriptions
for the frozen benchmark population; they do not change the Tier B provenance of
the vendor target.

## Session 4 diagnostic fields

Session 4 added no model inputs. It computed feature-only audit quantities from
the frozen development population:

| Diagnostic | Definition | Status / limitation |
| --- | --- | --- |
| second/third segment distance | second/third order statistic of defender distance to the same finite carrier-receiver segment | DESCRIPTIVE ONLY; absent from M1 |
| distance gaps | second or third order statistic minus the M1 minimum | DESCRIPTIVE ONLY; no football cutoff |
| prior-frame availability | same identity, immediately prior same-period frame, finite coordinates, positive elapsed time | STRUCTURALLY AVAILABLE for 99.93% of audited defender instances |
| current/prior detection | provider `is_detected` combinations | QUALITY/PROVENANCE ONLY |
| backward velocity | difference between current and immediately prior coordinate divided by elapsed time | FUTURE CANDIDATE; not calculated; provider-causal processing unverified |

The numerical multiplicity test uses only floating-point non-degeneracy. It is not
a minimum football-relevant separation. Provider documentation recommends speed
or acceleration smoothing but does not establish that supplied extrapolated
coordinates are free from future-aware processing. Any future velocity remains
offline and blocked from a causal-input claim until that provenance is resolved.

## Session 6a verified identity contract

The restricted development reader verified the following without changing the
Session 3 population:

| Identity rule | Verified handling |
| --- | --- |
| Raw identity form | Preserve exactly; do not trim, case-fold, repair, or map blank, whitespace, padded, or malformed values |
| Carrier precedence | Populated event `player_id` wins; use `player_in_possession_id` only when the primary field is empty; report conflicts separately |
| Declared teams | Require two distinct match teams; roster team IDs are audited against both |
| Roster identity | String-coerce under frozen production behavior; duplicate identity is a hard failure |
| Tracking identity | Current-frame identity must resolve to roster; duplicate within a frame is a hard failure; no carry-forward |
| Event identity | Duplicate nonempty event IDs invalidate all otherwise labelled pass attempts in that match under frozen behavior |
| Target identity | Label only; missing, self, unresolved, other-team, inactive, and untracked states are audited without changing candidates |
| Eligibility | Evaluation and fit eligibility are represented independently even though both equal 7,227 in the frozen development population |

Across the nine development matches, all declared-team, roster, event-key, and
tracking identity keys were ordinary and unique. Optional Dynamic Event player
references may be empty. For frozen pass attempts, 55 targets were missing, one
was self-targeted, and nine carrier identities were absent from the selected
decision frame. Those cases map uniquely to the existing Session 3 waterfall.
The restricted replay is byte-identical to the authoritative population at
SHA-256 `cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d`.
These are development-only facts and do not describe protected-match identity
quality.
