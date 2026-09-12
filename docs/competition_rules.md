# Competition rules and verification record

Recorded 2026-09-09 for **PySport Analytics Cup 2.0 — USA region — Football**.
The supplied requirements below were checked against the rendered
[official Cup 2.0 page](https://pysport.org/analytics-cup/editions/analytics-cup2/rules)
on 2026-09-09. This is a summary, not a verbatim rulebook or proof of individual
eligibility. The rendered official page was rechecked on 2026-09-12; the README
limit remained 1,000 words and two combined figures/tables. Recheck again before
submission.

| Requirement | Supplied constraint, confirmed on the official page |
| --- | --- |
| Originality | Substantial new work created specifically for Analytics Cup 2.0. |
| Data | Only competition-permitted SkillCorner data. |
| Repository | Public GitHub repository. |
| Open source | Open-source license; submitted work remains open source forever. |
| Reproducibility | Fully reproducible without proprietary software; clean-environment execution. |
| Region | USA. |
| Sport / entry | Football challenge; Defensive Positioning theme. |
| Pitch | YouTube pitch of at most one minute. |
| README length | At most 1,000 words. |
| README visuals | Maximum two figures/tables total, combined. |
| Submission deadline | 18 December 2026. |
| USA regional final | 24 February 2027, Boston. |

The brief identifies sporting relevance, sound methodology, originality, clear
communication, and open-source/reusable potential as judging priorities.
It describes Australia A-League 2024/25 data with season-level aggregated
physical data from 175 games, XY tracking for 20 games, Game Intelligence Dynamic
Events for 10 games, and Body Pose for 2 games, plus documentation/tutorials and
visualization tools. These are expected availability counts, not locally
verified counts or evidence that the products overlap completely.

## Official clarifications and implementation

- Licensed, disclosed pre-existing libraries/frameworks and general-purpose code
  are allowed; completed projects cannot simply be resubmitted or lightly adapted.
- The eligible pool is SkillCorner data provided for this event and/or prior
  Analytics Cups. Additional data, including outside video or extra tracking/
  events, is prohibited. This does not automatically make all SkillCorner open
  data eligible; record the permitted source release.
- The public repository must include all relevant code/resources except data
  and a `LICENSE.md` file. `LICENSE.md` is the canonical project license. An
  initially duplicated bare `LICENSE` file was removed after confirming that no
  repository tool, rule, workflow, or package requirement depended on that name.
- The one-minute pitch must be presented and voiced by the entrant or teammate.
- Choose one region; entry may be individual or a pair. Finalists must attend
  in person. No registration or submission has been performed by this scaffold.
- Originality, relevance, methodology, communication, and open-source potential
  each have a 20% judging weight on the checked page.

The official dataset description specifies 20 XY games **including 10 new games**,
with Dynamic Events for those 10. The upstream repository overview describes 10
tracking games. Inventory the selected release to reconcile coverage and prior
exposure before assigning validation; see [data_dictionary_notes.md](data_dictionary_notes.md).

## Source checks and remaining details

- **Primary working source:** the user-supplied initialization brief, received
  2026-09-09. All numerical submission limits and dates above come from it.
- **Official context:** the indexed
  [SkillCorner Analytics Cup 2027 page](https://skillcorner.com/analytics-cup-2027)
  describes the SkillCorner/PySport partnership and Cup 2.0 as two sports,
  regional competitions, and live finals. It does not verify the detailed
  constraints above in the text retrieved during initialization.
- **Detailed verification completed:** the text browser could not read the
  JavaScript site, but its rendered browser page exposed the current
  [rules](https://pysport.org/analytics-cup/editions/analytics-cup2/rules),
  [datasets](https://pysport.org/analytics-cup/editions/analytics-cup2/datasets),
  and [dates](https://pysport.org/analytics-cup/editions/analytics-cup2/key-dates).
  No revision identifier was displayed. The
  [submissions archive](https://pysport.org/analytics-cup/submissions) is a
  previous-work reference, not an earlier-edition template to adopt.

Before data access/submission, confirm the eligible source release and data
terms, exact acquisition instructions, and deadline cutoff time/timezone (not
specified in the checked page). The official FAQ points to the
[submission portal](https://submissions.analytics-cup.org/); no account or portal
action was taken. Do not infer a timezone. Resolve future changes explicitly
and log them.

## Current delivery status

Original code and documentation use MIT. No data is included or relicensed.
Raw and reconstructive competition records stay local; reviewed aggregate
receiver-ranking results are committed under the repository's publication
rules. The GitHub repository and governed empirical pipeline now exist. The
current README has one synthetic figure, no tables, and remains below the
recorded word limit, leaving one combined figure/table slot unused. Public
repository alignment has been refreshed after the current numerical-validation
work. A final clean-environment empirical reproduction, final submission audit,
one-minute pitch, and submission-portal action remain outstanding.
