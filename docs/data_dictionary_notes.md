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
| Four metadata schema variants; two Dynamic Events header variants; one phases header variant | VERIFIED SCHEMA/HEADER |
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
