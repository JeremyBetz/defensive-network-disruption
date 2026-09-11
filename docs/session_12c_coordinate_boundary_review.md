# Session 12c — Coordinate boundary occurrence review

## Decision

**Primary F — UNRESOLVED.**
**Remedy readiness 2 — READY ONLY AFTER PROVIDER/DOCUMENTATION CLARIFICATION.**
**Execution: valid, bounded review completed once.**

The twelve occurrences reproduce exactly and are present in the verified native
tracking coordinates. Their raw-to-canonical transformations, active-state
checks, decision-frame recovery and pitch-dimension joins passed exactly.
There is no demonstrated project transformation or dimension-mapping defect in
these occurrences. This does not establish the accuracy of the provider's
estimated positions or justify a particular value-domain policy.

The reviewed positions extend **0.12–4.43 metres** beyond their longitudinal
boundary, with median **0.885 metres**. Five are flagged detected and seven
extrapolated. Each belongs to a multi-sample observed boundary run reaching the
edge of the authorized temporal window. Neither legitimate off-pitch behavior,
extrapolation causality nor provider data error is uniquely established. No
boundary remedy or renewed progression execution is authorized by this finding.

## Authority and exact reproduction

Starting local, tracking and live remote main agreed at
`ca17380b7f987d33d8841aa2493897e311f98436`; the tree was clean.
The [Phase 12c protocol](protocols/phase_12c_coordinate_boundary_review.md) was
committed as `2fd8e1b` before new values. Tested implementation `0c27b3f` preceded
occurrence identification. The reproduced authority was committed as `6c5d000`
before deeper provider-value review.

The population hash remained
`cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d`.
The Session 12b dimension-file hash remained
`ded8721ad91f18b98c09488852481aaadfe3098d7b5f2039f0531e6e4f923c69`.
All 7,227 observations and historical match counts matched. The exact selection
predicate `abs(x') > L/2`, with carrier and candidate positions only, reproduced
counts **2,1,3,2,1,1,2,0,0** and exactly twelve occurrences. No population was
regenerated. Local occurrence identities are hash-bound and ignored.

[Occurrence authority](../outputs/coordinate_boundary_review/occurrence_authority.json)
SHA-256: `ece0ba20a2e35fe070b1ec473cf6172bc50f93a35613c967ebd98168a4796a6a`.
Protocol SHA-256:
`3909e8b67db8451688c983bbcd8f64c453b65e786d43886aa20bcbeb8880f1bb`.

## Boundary and detection findings

There is **one carrier occurrence and eleven candidate-receiver occurrences**.
Candidate status does not mean the player was the target; targets were not read.
Seven occurrences lie beyond the negative longitudinal boundary and five beyond
the positive boundary. None also crosses the nominal lateral boundary.

| Stable alias | Occurrences | Carrier | Candidate | Detected | Extrapolated |
| --- | ---: | ---: | ---: | ---: | ---: |
| development_01 | 2 | 0 | 2 | 1 | 1 |
| development_02 | 1 | 0 | 1 | 0 | 1 |
| development_03 | 3 | 1 | 2 | 0 | 3 |
| development_04 | 2 | 0 | 2 | 1 | 1 |
| development_05 | 1 | 0 | 1 | 0 | 1 |
| development_06 | 1 | 0 | 1 | 1 | 0 |
| development_07 | 2 | 0 | 2 | 2 | 0 |
| development_08 | 0 | 0 | 0 | 0 | 0 |
| development_09 | 0 | 0 | 0 | 0 | 0 |

There are no unavailable decision-frame detection statuses. Pitch-length classes
contain three occurrences at 104 metres, seven at 105 metres and two at 106
metres. This is an aggregate class count, not a published match/dimension mapping.

| Status | Count | Minimum excess (m) | Median excess (m) | Maximum excess (m) |
| --- | ---: | ---: | ---: | ---: |
| All | 12 | 0.12 | 0.885 | 4.43 |
| Detected | 5 | 0.20 | 0.94 | 1.33 |
| Extrapolated | 7 | 0.12 | 0.83 | 4.43 |
| Unavailable | 0 | unavailable | unavailable | unavailable |

Displayed distances are rounded summaries of the unedited generated float64
aggregates. No acceptable excess threshold was selected. Detection flags
characterize provenance; they do not show that extrapolation caused the crossing.

## Coordinate provenance and temporal limits

Twenty-one existing local products across the seven affected development matches
passed ordinary Git or LFS payload identity and size verification. Ten bounded
source-object requests succeeded with no failures or retries. No new provider
payload was downloaded. The metadata objects matched Session 12b's identity
receipts and exact dimension mapping, without defaults or cross-match fallback.

Unique canonical event references recovered only the period, transition time
and carrier references needed for the frozen prior-frame lookup. The same-period,
strictly prior, at-most-100-ms rule and integer-microsecond clock parser were
reused. Relevant carrier/player team and period intervals were checked. Every
selected native coordinate reproduced canonical x'=s*x and y'=y exactly under
the frozen float conversion; no tolerance or scaling correction was introduced.
Since abs(s*x)=abs(x), sign reflection alone cannot create or eliminate these
longitudinal boundary violations.

The twelve occurrences are **twelve distinct local player/frame keys**, involving
**ten distinct players within match context**. One player key appears in more
than one occurrence. There are no repeated canonical occurrences of the same
player/frame and no overlapping review-window pairs.

All sixty authorized same-player samples were available. The windows included
at most two adjacent same-period frames each side, with the 200-ms bound. There
were zero detection-status transitions in those windows. There were **twelve
observed local runs**, all censored by an inspection-window edge, and zero
single-observed-sample runs. These counts do not establish twelve complete
physical excursions. Their start/end, longer continuity, match-passage identity
and real football causes remain unassessable within this bounded inspection.
No window was extended and no velocity, interpolation or animation was used.

## Provider semantics and competing explanations

The [pinned provider README](https://github.com/SkillCorner/opendata/blob/02a396ffd09b283c9f092fdedeff11da6d535b66/README.md)
documents pitch-centred metre coordinates, longitudinal x and lateral y, and a
flag distinguishing on-screen detection from extrapolation. It does not establish
whether coordinates are clipped, whether pitch dimensions are a hard support
limit, how physical off-pitch activity is handled, or whether extrapolation may
produce out-of-pitch estimates. Its illustrated pitch is not a substitute for
actual match dimensions.

README Git blob: `d34e5956f7b5b93510764506e6501461a0c5cef8`.
README SHA-256: `c09886c6359e5f7ff3bfd71a653510caf2f674d238ca79219aa1ec9ebe6f4428`.

The earlier [Session 2 brief](session_02_decision_brief.md) already records
coordinates beyond nominal boundaries and cautions against silent clipping.
The [data dictionary](data_dictionary_notes.md) retains centred-metre and
extrapolation limitations. These are preserved historical observations, not an
explicit provider guarantee that the twelve positions represent legitimate
physical locations. No broader documentation search or provider message occurred.

- **Legitimate support:** compatible with the observations, but explicit provider
  semantics and physical context are missing; A is not established.
- **Extrapolation:** present in seven flags, but detected occurrences also exist
  and the bounded windows contain no status transitions; B is not established.
- **Project transformation/join error:** the exact checks pass for all twelve;
  no demonstrated C defect.
- **Isolated anomalies:** rarity and boundary crossing alone are insufficient;
  no single-sample observed runs or independent anomaly evidence establishes D.
- **Mixed mechanisms:** mixed detection statuses are not evidence of distinct
  causes. E is not established.

Therefore F is the defensible primary classification. No intent, goalkeeper role,
substitution, technical area, off-field run or other contextual label was inferred.

## Coordinate support versus value domain

A provider may support coordinates outside field markings while an analytical
value function is defined only on the playable rectangle. Establishing the former
would not uniquely choose an extension of the latter. Session 12b's strict-domain
stop remains valid under its own prospective contract.

Future nearest-boundary projection or endpoint-valued extension could preserve
coordinates while changing value semantics. Clipping values would similarly
change the frozen function. Excluding states would change the analytical
population and needs evidence of invalidity. Abandoning normalized progression
would replace the construct. These are conceptual alternatives only: none was
selected, implemented, evaluated or assigned a numerical threshold here.

Exactly one next action: **obtain provider/documentation clarification about
coordinate support relative to field markings and the interpretation of these
boundary samples**, under separate authorization. Do not send identifiers or
sample records automatically. No remedy or renewed empirical protocol is ready
merely because the transformation checks passed.

## Verification, outputs and preservation

Focused synthetic suite: **18 passed, 0 skipped**. Full active suite before access
and again during closure: **277 passed, 3 retained skips**, 280 total.
Compilation, strict projection sentinels, timing/recovery, transformations,
dimension joins, bounded neighborhoods, runs/censoring, source identity, access
firewalls, failure preservation and command separation passed.

Publication schemas, CSV counts, aggregate consistency, finite-distance checks
and output hashes passed before aggregate closure and again before staged
review. Documentation links, append-only history, staged contents and
`git diff --check` passed. All historical source, outputs, claims, package metadata,
lockfile and release bytes remain unchanged; only research/library logs receive
append-only entries. No implementation repair or review rerun followed access.

The generated summary intentionally leaves documentary interpretation to this
report. Its bytes were not rewritten to insert the F/2 conclusion.
[Summary](../outputs/coordinate_boundary_review/occurrence_summary.json),
[match counts](../outputs/coordinate_boundary_review/match_summary.csv) and
[QC](../outputs/coordinate_boundary_review/qc.json) are hash-bound by the
[manifest](../outputs/coordinate_boundary_review/manifest.json).
Manifest SHA-256:
`f7333c6c39676db87a8ff9f6ca5f102064fb17eeaa85f01dd339b72f32529600`.

## Twenty-four handoff items

1. Starting HEAD: `ca17380b7f987d33d8841aa2493897e311f98436`, clean/live synchronized.
2. Ending HEAD: final delivery handoff, avoiding a recursive commit reference.
3. Protocol: Phase 12c, commit `2fd8e1b`, hash above.
4. Reproduction: exact 12, unchanged 7,227 states and dimension authority.
5. Roles: one carrier, eleven candidate receivers.
6. Per-match counts: 2,1,3,2,1,1,2,0,0 in historical alias order.
7. Length classes: 104 m: 3; 105 m: 7; 106 m: 2.
8. Excess min/median/max: 0.12/0.885/4.43 metres.
9. Boundary sides: five positive, seven negative.
10. Status: five detected, seven extrapolated, zero unavailable.
11. Complete physical excursions: unavailable; twelve censored observed local runs.
12. Transformation: exact verification passed for all twelve.
13. Dimension join: exact verification passed for all twelve.
14. Provider semantics: centred metres and detection flag documented; boundary-support policy unavailable.
15. Temporal grouping: twelve unique player/frame keys, ten player keys, no overlapping windows; findings above.
16. Primary: F — UNRESOLVED.
17. Remedy readiness: 2 — PROVIDER/DOCUMENTATION CLARIFICATION REQUIRED.
18. Policies: conceptual discussion only; none selected or executed.
19. No horizons, shares, ranks, model loading, target or outcome inspection.
20. No reserved-detail, withheld or pose access; no new provider payload acquisition.
21. Tests/checks: 18 focused passes; 277 full passes/3 skips; verification above.
22. Claim ledger unchanged; Session 12b remains blocked and closed.
23. Protocol `2fd8e1b`, implementation `0c27b3f`, occurrence authority `6c5d000`, then reviewed closure commit; push/synchronization in delivery handoff. v0.1.0 remains at `f00690c05d8c1c6db308a65bd311c43f9a8ef2fa`.
24. One next action: separately authorized provider/documentation clarification; not executed.

Accessibility remains **PROXY ONLY**; suppression remains **NOT SUPPORTABLE**.
No progression analysis, external xT, boundary remedy, occlusion work or release
was initiated. Session 12c stops after this coordinate-only review.
