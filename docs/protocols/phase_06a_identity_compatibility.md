# Phase 06a protocol: development identity-contract compatibility audit

**Status:** FROZEN FOR ONE DEVELOPMENT-ONLY COMPATIBILITY AUDIT

**Starting authority:** `3cd72c1509bf2ca08d6b41a236b80e065156668d`

**SkillCorner source:** `02a396ffd09b283c9f092fdedeff11da6d535b66`

## Question and scope

Can a restricted, fully specified identity reader reproduce the authoritative
Session 3 development population without requiring a new scientific decision?

Use only development matches `1886347`, `1899585`, `1925299`, `1996435`,
`2006229`, `2011166`, `2013725`, `2015213`, and `2017461`. Reject every other
match identifier before opening, hashing, or parsing a provider file. Reserved
matches `1874553`, `1927964`, `1959846`, `1986691`, `1996436`, `2006363`,
`2007448`, `2007721`, `2010085`, `2016236`, and withheld match `1953632` are
prohibited.

This audit may inspect development values only after this protocol is committed.
It may not fit a model, calculate rankings or performance, inspect passages, or
change any closed Session 3, 4, or 5 population, code, or result artifact.

## Authorized fields and file access

Before parsing, verify pinned Git and LFS identities and declared sizes. Resolve
paths beneath the governed development root; reject path traversal, symlinks,
unknown products, and non-development identifiers before file open.

Project only these fields while parsing and never retain complete mixed-content
rows:

- Metadata: declared home and away team IDs; roster player and team IDs; period
  directions; period-specific playing intervals.
- Dynamic Events: `event_id`, `event_type`, `pass_outcome`, `period`, `time_end`,
  `player_id`, `player_in_possession_id`, and `player_targeted_id`.
- Tracking: `frame`, `period`, `timestamp`, and player identity, `x`, and `y`.

Raw and detailed diagnostics, replay bytes, identity mappings, and the access
ledger remain under ignored locations. Public artifacts may contain aggregate
counts and stable aliases only. Publication checks reject player or event IDs,
coordinates, timestamps, private paths, and reconstructive rows.

## Frozen identity contract

Identity strings are interpreted exactly as supplied. Do not trim, case-fold,
repair, map, or otherwise normalize null, empty, whitespace-only, padded, or
malformed values. Audit those forms separately at aggregate match level.

A populated `player_id` is the carrier. Use `player_in_possession_id` only when
`player_id` is empty under the existing production truthiness rule. When both
are populated and disagree, retain `player_id` precedence and record a conflict
flag. This protocol freezes existing behavior; it does not claim the precedence
is provider truth.

Preserve existing production behavior, including match-wide invalidation of
otherwise labelled pass attempts when duplicate nonempty event IDs occur.
Duplicate roster and tracking identities remain hard failures. Audit duplicate
declared-team identities, roster teams outside the two declared match teams,
tracking players absent from the roster, unresolved carrier identities, and
malformed period direction or playing intervals.

Target admission remains independent of eventual target, vendor Passing Option,
receipt, and outcome values. Audit missing, self-targeting, unresolved,
other-team, inactive, and untracked targets. Do not admit or repair a candidate
because it was targeted. Reuse the frozen strict prior-frame timing, active
interval, attacking-coordinate, candidate, defender, exclusion-order, and
target-outside rules.

If observed development data require trimming, repair, a new mapping, changed
precedence, a new exclusion, or any scientific choice not uniquely determined by
the existing contract, stop with **BLOCKED — New decision required**.

## Audit and replay

The Session 6a runner exposes `preflight`, `audit`, `replay`, and
`publication-check`.

`audit` reports aggregate per-match counts for null, empty, whitespace-only, and
padded event/player/team identifiers; duplicate event, roster, tracking, and
declared-team identities; roster and tracking membership failures; carrier
reference states; target join states; directions; and playing intervals.

`replay` writes a new ignored population using original event, candidate, and
defender ordering, coordinates, and canonical Session 3 JSON serialization. It
must never overwrite or regenerate the authoritative Session 3 population.

Require independently:

- authoritative evaluation-eligible total, currently expected as 7,227;
- authoritative fit-eligible total, currently expected as 7,227;
- exact per-match evaluation and fit counts;
- exact per-match exclusions, target-outside counts/reasons, and population
  hashes;
- byte-for-byte equality with the ignored authoritative population; and
- combined SHA-256
  `cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d`.

The equality of the two totals is an observed Session 3 result, not a general
rule. Evaluation and fit eligibility remain distinct. A valid target outside an
independent candidate set may be evaluation-eligible with zero retrieval credit
and fit-ineligible.

Any replay difference produces **FAIL — Replay mismatch**. Diagnose it only with
development structural evidence and do not change rules to recover the expected
hash.

## Tests, outputs, and stop conditions

Test the production reader on synthetic fixtures for null, blank, whitespace,
padded, malformed, duplicate, unknown, and conflicting identities; both carrier
fields populated and disagreeing; every frozen target state; independent
candidates; strict timing; period intervals and direction; separate evaluation
and fit eligibility; reserved/withheld firewalls; path traversal; symlinks;
field projection; deterministic serialization; and exact replay.

Create only these durable artifacts:

- `docs/session_06a_identity_compatibility_audit.md`;
- compact aggregate files under `outputs/identity_compatibility/`;
- bounded append-only entries in `docs/research_log.md` and
  `docs/data_dictionary_notes.md`.

Detailed diagnostics, replay bytes, alias mapping, and the access ledger remain
ignored. Record source, protocol, implementation, environment, authority, and
output hashes. Verify focused and full tests, compilation, authority/source and
output hashes, schemas, publication safety, staged contents, and
`git diff --check`.

Return exactly one decision: **PASS — Identity contract compatible**;
**BLOCKED — New decision required**; **FAIL — Replay mismatch**; or
**INVALID — Execution or integrity failure**. Only PASS permits later planning
and freezing of protected Session 6. Stop after this audit without reserved
access, protected training/scoring, or Session 6 execution.
