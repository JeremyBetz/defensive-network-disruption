# P02 — Development compatibility and benchmark feasibility

Version 1.0, 2026-09-10. Status: **AUTHORIZED FOR SESSION 2 ONLY**.
Protocol checkpoint: Session 1 commit `292506548728069c88a8e2dcc4835cce743cee1b`.
Source: SkillCorner Open Data commit `02a396ffd09b283c9f092fdedeff11da6d535b66`.

## Question and boundaries

Can the nine development matches support a defensible receiver-choice benchmark
using independently constructed candidates and information available immediately
before pass initiation? This phase validates data, labels, alignment, and candidate
feasibility. It does not authorize a model, ranking, performance metric, passage
selection, or value-level access to protected matches.

Session 1's reservation verdict remains **A — PRESERVED**, qualified by L004: its
schema reader mechanically buffered post-header bytes from reserved CSVs, while no
evidence indicates that values were surfaced, persisted, or used analytically.

Development match allowlist: `1886347`, `1899585`, `1925299`, `1996435`,
`2006229`, `2011166`, `2013725`, `2015213`, `2017461`.

Every other match identifier is denied before file open or request construction,
including the ten prospectively reserved matches and withheld match `1953632`.

## Access stages and paths

Stage S2A may acquire and schema-check only these pinned paths for an allowlisted ID:

- `data/matches/{id}/{id}_match.json`
- `data/matches/{id}/{id}_tracking_extrapolated.jsonl`
- `data/matches/{id}/{id}_dynamic_events.csv`

Full development files may be downloaded into ignored `data/session_02/`. Verify
ordinary Git blob identities and tracking LFS SHA-256/declared size against the
Session 1 manifest before parsing. Reject symlinks, path escapes, identity mismatch,
malformed content, and unknown products. Phases, pose, physical aggregates, and
outside data are prohibited.

Stage S2B may inspect projected development values only. Metadata fields are match
and team IDs, pitch dimensions, period/frame bounds, team direction, player IDs,
team IDs, roles, and playing intervals. Event fields are event/type IDs, event
type, frame/time references, possession/carrier/team IDs, target-link and target
player IDs, `targeted`, `received`, and pass outcome ID/category. Tracking fields
are frame/period/time, player and team identity, coordinates, ball, possession,
and native detection/quality fields. Names, birthdays, scores, goals, aggregate
performance, vendor option scores, EPV, and unrelated event values may not enter
diagnostics or logs. An unknown required field blocks the dependent check until a
prospective amendment is committed.

Commands, in order:

```text
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/session_02_compatibility.py preflight
.venv/bin/python scripts/session_02_compatibility.py acquire-schema
.venv/bin/python scripts/session_02_compatibility.py validate
.venv/bin/python scripts/session_02_compatibility.py publication-check
```

Raw data and detailed diagnostics are ignored. The local access ledger is
append-only and records command, code/protocol/source identities, paths, products,
hashes, and access time without row contents. Console and committed outputs contain
aggregate counts, distributions, schema names, hashes, and status labels only—no
coordinates, passage timestamps, player IDs, raw vendor scores, or reconstructive
rows.

## Prespecified validation

Audit tracking integrity, schema, cadence, periods, clocks, coordinates, entities,
ball, possession, and detection/extrapolation provenance for all development
matches. Until its processing provenance is established, extrapolated tracking is
timestamp-restricted offline information rather than proven real-time input.

Identify pass initiation from documented event semantics. Audit target existence,
uniqueness, joins, failure/offsides coverage, identity stability, and whether the
target represents observed intention or a vendor inference. Passing Option scores
and threshold-generated option events are comparison evidence only.

The proposed alignment rule selects the latest same-period tracking frame strictly
before documented pass initiation, with a maximum age of **100 ms**. This is a
prospective draft based on documented 10 Hz cadence, not a truth claim or an
empirically optimized threshold. Coarse/systematically offset timestamps or
uncertain causal ordering produce **alignment blocked**; do not force the threshold.

Build candidates before joining targets: same team, valid identity, active/on
pitch, finite decision-time coordinate, and not the carrier. Include goalkeepers
and backward options, apply no distance limit, defer offside filtering, do not
carry disappeared players forward, and never use vendor options, outcomes, or the
eventual target for admission.

Classify considered fields as decision-time feature, label only, post-outcome /
prohibited feature, or vendor-derived / comparison only. Receipt, outcome, future
trajectory, and vendor availability scores cannot be predictors.

Kloppy compatibility uses a fixed bounded sample: first 300 tracking records in
each of the first two documented periods of every development match. Compare
native semantics, coordinates, time, identities, entities, ball, and omitted
quality fields. No football-content selection is permitted.

## Geometry-only feasibility

M0 and M1 are specifications only. M0 uses carrier-receiver distance and signed
longitudinal/lateral displacement in a verified attacking frame; optional M0+ is
normalized carrier field position only if context is independently required.

M1 feasibility covers nearest-defender distance to the receiver and minimum
distance to the finite carrier-receiver segment. For `v=b-a`, use
`t=clip(dot(d-a,v)/dot(v,v),0,1)` and `norm(d-(a+t*v))`. Segment length at or below
`1e-9` metres uses point distance. This is an implementation tolerance for
floating-point safety and has no football meaning. Reject non-finite coordinates;
an empty defender set yields missing geometry.

M2 receives requirements only: continuous attenuation, promised monotonicity,
synthetic stability, interpretable components, incremental comparison, and no
future-derived inputs.

## PROVISIONAL — NOT AUTHORIZED FOR MODEL EXECUTION

The October 2 draft target is the highest defensible receiver label for one state
immediately before each eligible pass attempt. Candidate, alignment, exclusion,
and unresolved-case rules are those above, subject to this session's evidence.
Future match-macro MRR and Hit@1/3 use identical attempts/candidates, expected
credit for score ties, separately reported missing/ambiguous/empty exclusions,
and zero credit when a unique target lies outside a valid nonempty independent
candidate set. No metric is calculated here. A later explicit protocol freeze is
required before implementing, fitting, or evaluating M0, M1, or M2.

## Outputs and stop rules

Tracked outputs are `docs/session_02_decision_brief.md`, bounded dictionary/log
updates, and four compact JSON summaries under `outputs/development_compatibility/`.
Detailed rows and identifiers remain ignored. Classify the result A intended-label
benchmark, B limited vendor/completed-receiver benchmark, C geometry only, or D
insufficient integration. Separately classify accessibility; suppression remains
unsupported absent stronger evidence.

Stop immediately on prohibited match access, unrecorded field access, integrity
failure affecting scope, raw-value logging, or any protocol deviation. Append the
deviation before further work. Session 2 stops after its report and may not build
or fit models, compute ranking/performance metrics, or select scored passages.
