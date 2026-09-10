# Session 6a identity-contract compatibility audit

**Decision: PASS — Identity contract compatible.**

The restricted reader reproduced the authoritative Session 3 development
population without a new scientific decision. This result authorizes planning
and freezing a protected Session 6 protocol; it does not authorize protected
data access by itself.

## Authority and access

- Starting authority: `3cd72c1509bf2ca08d6b41a236b80e065156668d`.
- Protocol-first commit: `6f08ffa119c2641f436dea9ab0b221cfe90d47ea`.
- SkillCorner source: `02a396ffd09b283c9f092fdedeff11da6d535b66`.
- Scope: the nine frozen development matches, represented publicly as
  `development_01` through `development_09`.
- Products: metadata, Dynamic Events, and extrapolated tracking from the
  governed Session 2 local copy.
- Source integrity: all nine metadata and event Git objects and all nine LFS
  tracking payload hashes and declared sizes verified before parsing. Git
  pointer identities remained distinct from LFS payload identities.
- Projection: only the Phase 6a metadata, event, and tracking fields were
  retained in memory. No complete mixed-content row was retained.
- Protection: no reserved or withheld provider product, pose product, passage,
  feature, score, ranking, or performance result was opened or computed.

## Identity findings

Across declared-team, roster-player, roster-team, event-ID, and tracking-player
identities, the audit found zero null, empty, whitespace-only, padded, or
malformed values. Optional player-reference columns across all Dynamic Event
types contained 35,653 empty cells; these are ordinary absent optional
references and were neither normalized nor joined.

There were no duplicate declared-team, nonempty event, roster, or within-frame
tracking identities. Every roster team belonged to one of the two declared
match teams, and every nonempty tracking player identity resolved to the roster.
All nine matches had two distinct declared teams, known period directions, and
no malformed period-specific playing interval.

Among the 7,292 frozen structural pass attempts, the selected carrier reference
was always present and roster-resolved. No attempt used the fallback carrier
field and no attempt had conflicting populated carrier fields. Nine attempts had
the selected carrier absent from the strict decision frame; the existing
`invalid_carrier` rule uniquely excludes them. This is the same frozen Session 3
behavior and requires no repair or new exclusion.

Target auditing found 55 missing target references, one self-target, zero
unresolved or other-team targets, and zero active-state or current-tracking
failures among otherwise valid states. Target state was not assessed for the
nine attempts whose carrier state failed first, preserving the exclusion
waterfall. The remaining 7,227 target joins were valid at the decision frame.

The carrier rule is now explicit and tested: a populated `player_id` has
precedence; `player_in_possession_id` is only a fallback when `player_id` is
empty. A direct conflicting-fields fixture confirms that frozen precedence and
records the conflict independently.

## Exact replay

The restricted reader used the frozen production helpers for strict prior-frame
selection, active intervals, attacking coordinates, candidates, defenders,
exclusion order, and target-outside handling. Candidate construction remained
independent of target, vendor-option, receipt, and outcome values.

| Check | Result |
| --- | ---: |
| Raw pass attempts | 7,292 |
| Evaluation-eligible | 7,227 |
| Fit-eligible | 7,227 |
| Target outside independent candidate set | 0 |
| Per-match counts, exclusions, and hashes | Exact, 9/9 |
| Byte equality with Session 3 population | Exact |
| Authority and replay SHA-256 | `cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d` |

Evaluation and fit eligibility remain separate fields. Their equal totals are
an observed property of this development population, not a reader assumption.
The synthetic suite verifies that a valid target outside the independent choice
set remains evaluation-eligible, receives zero retrieval credit downstream, and
is not fit-eligible.

## Verification and limits

Nineteen focused identity-contract tests passed, including malformed and
duplicate identities, unknown teams, unresolved tracking, missing/fallback/
conflicting carrier references, target states, candidate independence, timing,
period contracts, firewalls, projection, deterministic serialization, and
separate eligibility. The full active suite, compilation, output schemas and
hashes, publication guards, staged review, and whitespace checks also passed.

The compact public summary contains stable aliases and aggregate counts only.
Row diagnostics, replay bytes, source identities, alias mapping, and access
ledger remain ignored. Public manifest SHA-256:
`b2b1627bd3b333c62766a9c4ffdcc908618726093c164e33c97743ac7ec82bde`.

Session 6a stops here. No protected evaluation protocol was written, and no
protected training or scoring began. Accessibility remains **PROXY ONLY** and
suppression remains **NOT SUPPORTABLE**.
