# References and provenance

The user-supplied ecosystem has been reviewed at the documentation/repository
overview level in [library_review.md](library_review.md). That file records every
provided link, possible integration roles, limitations, and adoption gates.
No listed analytics package or model has been installed or vendored into this
scaffold. The authoritative data source is linked in [data/README.md](../data/README.md).

## Phase 2 literature review queue

This is a planned review, not a completed literature synthesis. Use primary
papers, official documentation, and source code for substantive claims. Library
examples and published results on other datasets are not evidence for this
project's measurement.

| Topic | Questions to extract from primary work |
| --- | --- |
| Passing accessibility and completion | What is conditioned on? Which options are observed? Is selection distinguished from execution? How are unchosen options handled? |
| Interception geometry and time | How are ball travel, defender reach, reaction, orientation, and uncertainty specified and calibrated? |
| Pitch control and accessible space | Does a surface describe arriving first, receiving safely, or traversing a route? Which assumptions transfer to broadcast tracking? |
| Spatial networks | What do edges mean, and does topology add evidence beyond simpler spatial measures? |
| Defensive attribution | Which reference configurations and interactions support attribution, and which conclusions remain model-dependent? |
| Defensive structure | How are support, cover, line integrity, and deformation defined and validated? |
| Pose / perception | What distinguishes facing, vision, physical interception, and intention? Can XY supply an independently validated approximation? |

For each source, record title/authors/year, stable URL/DOI or code revision,
access date, license if code is relevant, construct, inputs, estimand, validation,
failure modes, and project relevance. Mark “not yet read” sources explicitly.
Record rejected as well as promising methods. Use the handbook and supplied
research groups to discover primary sources; follow their citations before
adopting scientific assumptions. Prioritize DEFCON and the U.S. Soccer pose work
for conceptual differentiation alongside passing-accessibility literature.

Store concise notes and citations here. Do not commit third-party data, model
weights, notebooks with match outputs, or copied papers unless redistribution
rights are verified. Never copy prior-project results into the claim ledger.
