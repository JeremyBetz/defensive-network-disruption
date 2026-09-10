# P01 — Metadata inventory and convention verification

Version: draft 0.1, 2026-09-09. Status: **DRAFT — NOT EXECUTED**.
This protocol defines the next step; its unresolved gates must be completed
and the relevant version committed before empirical access. Public documentation
review during initialization is recorded separately in the research log.

## Question and construct

Which competition-permitted products and matches are available together, and
what coordinate/time/identity conventions would a valid connection measure
require? The output is a provenance/coverage inventory and a data contract.
There is no scientific outcome, edge metric, or player estimand in Stage A.
This supports feasibility for C01, not evidence that C01 is true.

## Stage A — Metadata only

1. Confirm current competition terms and choose the permitted release/commit.
   Source: `https://github.com/SkillCorner/opendata`. Reconcile the official
   20-game description with the repository overview's 10-game description.
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

Before execution fill: selected release SHA; eligible metadata paths and exact
field allowlist; terms source; inventory script/command and version; local
manifest/output names; operator and start time. None is currently selected.

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
