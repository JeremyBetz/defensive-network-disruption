# P01 — Metadata inventory and convention verification

Version: 1.2, 2026-09-10. Status: **STAGE A COMPLETE — CLOSED WITH RECORDED DEVIATION**.
This version authorizes only the two Stage A access steps below after this file
is committed. Public documentation and repository-tree review performed while
planning are recorded separately in the research log.

## Question and construct

Which competition-permitted products and matches are available together, and
what coordinate/time/identity conventions would a valid connection measure
require? The output is a provenance/coverage inventory and a data contract.
There is no scientific outcome, edge metric, or player estimand in Stage A.
This supports feasibility for C01, not evidence that C01 is true.

## Stage A — Metadata only

### Frozen source, operator, and outputs

- **Source:** `https://github.com/SkillCorner/opendata` at commit
  `02a396ffd09b283c9f092fdedeff11da6d535b66` (tree
  `44fd5081d0e6a441dbafadd12c51d6ffca8ab98b`). There are no repository tags or
  releases at the freeze point. The competition terms source is the rendered
  [Cup 2.0 page](https://pysport.org/analytics-cup/editions/analytics-cup2/rules),
  checked 2026-09-09.
- **Operator/start:** Codex for Jeremy Betz, 2026-09-10 America/Chicago.
- **Detailed local manifest:**
  `data/manifests/skillcorner_opendata_02a396f.local.json`.
- **Detailed diagnostics:**
  `outputs/metadata_inventory/skillcorner_opendata_02a396f_inventory.local.json`.
- **Publication-safe summary:**
  `outputs/metadata_inventory/skillcorner_opendata_02a396f_summary.json`.
- **Decision brief:** `docs/session_01_decision_brief.md`.

No other durable output is authorized. The two `.local.json` files and all raw
or mixed-content competition records remain ignored. The compact summary may be
committed only after publication-boundary review.

### Stage A1 — schema and repository inventory

The following access is allowed across all 20 repository match directories:

- Git paths, object types, object hashes, pointer sizes, and Git LFS pointer
  content (`version`, payload OID, and declared payload size only);
- JSON key paths and value types, without retaining or printing values; and
- CSV header names, without reading, retaining, or printing data rows.

Use `gh api` against the frozen tree/blob identifiers. Where content is required,
download it only to a temporary ignored directory. A temporary Python standard-
library parser may enumerate JSON key paths/types and read only the first CSV
record as a header. It must fail if asked to emit values or if a CSV header spans
more than one physical line. Hash every acquired payload before parsing.

Stage A1 does not spend a reserved match. Value-level event/tracking inspection,
receiver-label completeness or joins, football passages, animations, outcome-
bearing metadata, football summaries, performance, and example selection are
prohibited for the reserved group.

### Stage A2 — allowlisted metadata values

After Stage A1 records the schema, amend and commit this protocol with exact JSON
key paths before reading any mixed-content metadata values. Permitted semantic
categories are limited to source/release identity, match identifier,
competition/season, date, team identities, product membership, and documented
pitch dimensions. Scores, outcomes, lineups/player identities, event values,
aggregate-performance values, pose values, and free-text notes are prohibited.

If the schema does not permit exact paths to be frozen without exposing values,
Stage A2 is blocked. Session 1 may finish with Stage A1 findings and the blocker.

Stage A1 found four metadata-schema variants without emitting values. The exact
Stage A2 allowlist is:

- `$.id`, `$.date_time`, `$.pitch_length`, `$.pitch_width`;
- `$.home_team.id`, `$.home_team.name`, `$.home_team.short_name`,
  `$.home_team.acronym`;
- `$.away_team.id`, `$.away_team.name`, `$.away_team.short_name`,
  `$.away_team.acronym`;
- `$.competition_edition.id`, `$.competition_edition.name`;
- `$.competition_edition.competition.id`,
  `$.competition_edition.competition.name`;
- `$.competition_edition.season.id`, `$.competition_edition.season.name`,
  `$.competition_edition.season.start_year`, and
  `$.competition_edition.season.end_year`.

No parent object may be printed or retained wholesale. The parser must address
each path directly, emit `null` for an absent path, and reject unexpected scalar
types. It may retain these values only in the two ignored local JSON artifacts.
The publication-safe summary contains counts and verification statuses, not
match, team, date, or competition identifiers.

1. Verify the frozen release and reconcile the official 20-game description
   with the repository overview and tree without assuming usable record coverage.
2. Select metadata fields before parsing any metadata file. Allow only release
   paths/types/sizes, product availability, match identifiers, competition/season,
   dates, team identities, documented dimensions, and schema descriptions.
   Avoid displaying full match metadata: it may also contain scores or outcomes.
3. Acquire only approved necessary metadata into ignored local storage. Inventory
   match/product overlap. Check duplicate/missing identifiers and unrecognized
   product/release entries without viewing event, tracking, aggregate-performance,
   or pose values. No example match notebooks, clips, or animations are allowed.
4. Audit prior exposure, including matches used by the sister project or prior
   competition work. Public README summaries were visible during the source
   review; do not label overlapping data untouched without an exposure assessment.
5. Record inventory provenance and a non-sensitive coverage report, then define
   a split proposal using metadata and the intended generalization target.

No season-performance summaries, scoring/EPV labels, pass outcomes, player
rankings, or outcome-dependent filters enter Stage A. If a needed metadata file
mixes allowed fields with outcomes, specify a restricted parser and output
allowlist before accessing it; do not inspect the whole file interactively.

### Stage A decisions

- Accept coverage only when source/release and identifiers are unambiguous and
  duplicates/product discrepancies are explained.
- Leave undocumented fields UNKNOWN. A missing required convention blocks use
  of that field, rather than triggering a guessed default.
- Do not force the expected counts: report documented versus available counts.
- If eligible release identity or product overlap remains unresolved, stop
  split assignment and record the blocker.

The selected revision, Stage A1 access, commands, outputs, operator, and start
date are frozen above. Stage A2 remains conditional on a committed exact-path
amendment derived solely from Stage A1 schema output.

## Stage B — Bounded development-only convention checks

Only after Stage A and a frozen split: select development passages by recorded
metadata-based rules. Never sample by visually interesting actions or pass
success. Set the passage count, times, fields, coordinate round-trip tolerance,
timestamp checks, quality criteria, and event alignment tolerances in a committed
amendment before opening records. The present draft does not authorize Stage B.

Check spatial transformations, period/time mapping, identities, missingness,
quality flags, and synchronization only within those development passages.
Log any visible outcomes as development exposure. Keep validation unopened.
Update the data dictionary with verified facts and evidence references; add
actual coordinate/geometry tests once their contracts are specified.

## Artifacts, uncertainty, and stopping

Store the local manifest in `data/manifests/` and inventory diagnostics in
`outputs/`. Log the protocol SHA, code SHA, source identity, commands, scope of
access, deviations, and counts. Report unknown coverage, inconsistent clocks,
and absent products explicitly. Counts are descriptive inventory, not independent
sample size. No inferential test or accuracy claim is appropriate in Stage A.

Stop on ambiguous permissions, unexpected outcome access, unresolved joins,
or unknown conventions required by an intended computation. Record exposure
and revise the protocol as necessary; do not erase the original decision.

Session 1 stops after the metadata/provenance package and decision brief. It does
not authorize candidate construction, receiver-label completeness checks, M0,
model fitting, passage review, or dependency installation.

## Stage A execution closure

Stage A1 ran from committed protocol `23b9359`; Stage A2 ran after the exact
allowlist was frozen in commit `b60d079`. The repository tree was complete and
untruncated: 20 unique match directories each contained entries for match
metadata, tracking, Dynamic Events, and phases of play. Schema-only checks found
four match-metadata schema variants, two Dynamic Events header variants, and one
phases-of-play header variant.

All tracking entries were Git LFS pointers. Pointer identities, payload SHA-256
values, and declared payload sizes were recorded; no tracking payload was
downloaded, so payload integrity and tracking schema remain **UNVERIFIED**.
Allowlisted metadata paths were extracted without retaining parent objects.

The six planned receiver-related columns were present in every Dynamic Events
header. Their values, completeness, joins, and timing were not inspected and are
**BLOCKED BY SESSION 1 SCOPE**. The original reader emitted header information
only, but requested 65,536 bytes from each CSV and retained post-header bytes in
process memory. This was a confirmed deviation from the declared header-only
access boundary. No evidence indicates that post-header values were displayed,
persisted, or used analytically; the reservation verdict is **A — PRESERVED**.
The correction and its evidentiary limits are recorded in L004. Detailed
identifiers remain in ignored local artifacts; the compact summary was reviewed
for publication safety.
