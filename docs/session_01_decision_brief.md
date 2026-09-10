# Session 1 decision brief

Date: 2026-09-10. Status: **COMPLETE — STOP BEFORE MODEL DEVELOPMENT**.

## Decision

The first empirical question is a behavioral benchmark:

> Given the ball carrier and eligible teammates immediately before a pass
> attempt, does transparent defensive geometry improve receiver ranking beyond
> a credible defender-free comparator?

Accessibility remains a separate construct requiring synthetic and structured
football validation. Suppression is unsupported without stronger evidence.
The likely contribution is a transparent benchmark and geometric reformulation
with an analyst-facing diagnostic; a novel mathematical construct is not
established.

## Source and coverage

The selected source is [SkillCorner Open Data](https://github.com/SkillCorner/opendata)
at commit `02a396ffd09b283c9f092fdedeff11da6d535b66`, tree
`44fd5081d0e6a441dbafadd12c51d6ffca8ab98b`. No GitHub tag or release existed at
the freeze point.

- **VERIFIED:** the untruncated tree has 20 unique match directories and 20 file
  entries each for metadata, tracking, Dynamic Events, and phases of play.
- **DOCUMENTED:** the official Cup page describes 20 tracking games, including
  10 new games, and Dynamic Events for those 10 new games.
- **UNVERIFIED:** usable record coverage. Repository file presence does not
  establish payload completeness, schema compatibility, or valid joins.
- **UNVERIFIED:** tracking payload integrity and schema. Only Git LFS pointer
  identities, payload hashes, and declared sizes were accessed.

Schema inspection found four metadata variants, two Dynamic Events header
variants (294 and 322 columns), and one 44-column phases header. The compact
machine-readable result is `skillcorner_opendata_02a396f_summary.json` under
`outputs/metadata_inventory/`.

## Exposure and provisional partition

The sister project pinned an earlier source revision and analyzed nine matches.
The ten additions are prospectively reserved from 2026-09-10; their earlier
exposure remains unverified. One older match remains withheld because the sister
project recorded a metadata-status inconsistency.

Candidate A is the provisional split: nine previously analyzed matches for
development, ten additions reserved, and one match withheld pending metadata
review. Exact identifiers and exposure classes live only in the ignored local
manifest. Candidate B remains dormant and requires a prospective amendment
before any reserved value-level access.

The reservation permits path, object, schema, and header inspection. It prohibits
reserved event/tracking values, receiver-label values or completeness, football
passages, animations, outcomes, performance, and example selection. No such
access occurred in Session 1.

## Receiver-label feasibility

- **VERIFIED:** every Dynamic Events header contains
  `targeted_passing_option_event_id`, `player_targeted_id`, `targeted`,
  `received`, `pass_outcome`, and `pass_outcome_id`.
- **DOCUMENTED:** the vendor specification distinguishes targeting, receipt, and
  pass outcome, and describes Passing Option events as receiver-model outputs.
- **BLOCKED:** field completeness, join integrity, timing, and intended-receiver
  validity were deliberately not inspected.

Vendor Passing Option events must not define candidate membership or serve as
independent availability ground truth. Their outputs may later provide disclosed
model-comparison evidence.

## Closest prior objects

The closest mathematical predecessor is Dick, Link, and Brefeld's receiver
Availability: pass reception without opponent interception, combining ball
dynamics, player reachability, and technical execution. Spearman et al. provide
the earlier time-to-intercept/time-to-control pass-probability foundation.
SoccerMap and un-xPass distinguish selection, success, and value; the more recent
TGN reception model combines target selection and receipt against defensive
structures. GAPP and DEFCON extend receiver/action models toward defender
influence, responsibility, and credit.

The remaining opportunity is a disciplined, open comparison of defender-free,
simple defensive, and graded geometric representations, with candidate-set and
claim boundaries made explicit. Whether the eventual geometric score deserves
the name accessibility remains an empirical question.

## Artifacts and next gate

The detailed local manifest and schema diagnostics are ignored and hash-bound in
the research log. Raw data, event rows, tracking payloads, model outputs, and
football passages were not acquired.

The next phase requires a separately frozen development-only protocol for
payload acquisition, integrity verification, compatibility checks, label joins,
timing, and candidate eligibility. Session 1 supplies no authority to begin it.
