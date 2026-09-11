# References and provenance

The user-supplied ecosystem and closest prior mathematical objects have been
reviewed in [library_review.md](library_review.md). That file records provided
links, conceptual neighbors, integration roles, limitations, and adoption gates.
No third-party model, weights, or external match data were adopted as scientific
evidence.

Kloppy 3.19.0 was evaluated on a bounded development sample and classified
**SAFE WITH NATIVE SIDECAR**: coordinates and player/ball presence matched the
native reader, while native detection flags, possession-player identity, and
image projection require sidecar retention. The experimental `v0.1.0` API now
uses Kloppy as an optional explicit-state adapter and mplsoccer as the optional
synthetic pitch renderer. Neither infers eligibility, loads competition data or
changes the numerical core. matplotvideo remains deferred because the public
workflow generates deterministic synthetic animation directly and does not
attach plots to video. Other ecosystem integrations remain conditional. The
authoritative data source and local-use boundary are described in
[data/README.md](../data/README.md).

## Continuing literature and reuse review

The bounded originality and failure-mode reviews are complete for the frozen
receiver-ranking ladder, but the wider literature program remains selective and
ongoing. Use primary papers, official documentation, and source code for
substantive claims. Library examples and published results on other datasets are
not evidence for this project's measurement.

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
