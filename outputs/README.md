# Outputs

This directory now contains reviewed, publication-safe aggregate authorities and
results from governed sessions. The protected Session 6e receiver-ranking result
and unfinished Session 7 construct diagnostics are the current public evidence;
read their manifests and decision authorities before interpretation.

Detailed populations, coordinates, timestamps, identities, candidate rows,
per-attempt scores, access ledgers, execution state, and review materials remain
ignored in session-local directories. Do not force-add them. A committed output
is not automatically safe to reinterpret outside the scope of its protocol.

Every empirical run must preserve protocol/code/environment identities,
configuration, source authority, counts and exclusions, results, uncertainty,
failures, and deviations. Do not overwrite unfavorable or invalid runs. Record
a bounded public summary in the append-only
[research log](../docs/research_log.md).

Current entry points:

- [Session 6e protected evaluation](reserved_evaluation_v3/manifest.json)
- [Session 7 diagnostic checkpoint](construct_validity_diagnostics/manifest.json)
- [Session 6e decision brief](../docs/session_06e_corrected_reserved_evaluation_decision_brief.md)
- [Phase 07a human-review withdrawal](../docs/protocols/phase_07a_human_review_withdrawal.md)

Synthetic software checks are not real-match evidence. Review every proposed
aggregate, figure, and table against provider terms and repository publication
rules before committing it.
