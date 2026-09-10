# Data dictionary notes

Status: documentation-level notes, **not a verified local data contract**.
No competition files have been downloaded or opened. Distinguish BRIEF EXPECTATION,
DOCUMENTED, and VERIFIED IN SELECTED RELEASE; nothing is in the last category.

## Availability and release identity

The [official Cup 2.0 dataset page](https://pysport.org/analytics-cup/editions/analytics-cup2/datasets)
lists 175-game season physical aggregates, 20 XY games including 10 new games,
Dynamic Events for those 10 games, and 2 Body Pose games. The user-supplied
[SkillCorner repository](https://github.com/SkillCorner/opendata) overview still
describes 10 tracking games. Reconcile the release, product coverage, and previous
edition overlap through metadata; do not resolve this by assuming all 20 have
events or that the root README is a complete inventory.

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
