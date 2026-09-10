# Phase 07 — Development construct diagnostics and independent human review

Status: prospectively frozen before development-value diagnostics. Starting live/local checkpoint: `68617d1f94f54707c9cd8d4547f09f894818cbc3`. The authorized accidental “pos sitive” edit was restored to its committed bytes before this protocol. Historical authorities/results and the Session 6e review-order qualification remain unchanged; only bounded append-only research-log entries are permitted.

## Question, authority and non-claims

Does the frozen M1/M2 ladder show geometry compatible with receiving-option accessibility, rather than only geometry associated with the eventual vendor target? This is falsification/diagnosis, not performance optimization, causality, suppression, value, player attribution or network-disruption evidence. Target labels retain Tier B limitations. Accessibility remains PROXY ONLY; suppression NOT SUPPORTABLE. Even a supportive result permits only: “The defensive-geometry relationships show behavior consistent with specific spatial constraints relevant to receiver accessibility in development data.”

Use only the existing canonical Session 3 population at outputs/receiver_ranking_m0_m1/local/population.jsonl, SHA-256 `cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d`, with 7,227 evaluation/fit observations. Development allowlist: `1886347,1899585,1925299,1996435,2006229,2011166,2013725,2015213,2017461`; development_01..09 follow ascending provider ID. Exact canonical fields: match_id,event_id,candidate_ids,candidate_xy,defender_xy,carrier_xy,target_index,target_outside. Verify bytes before parsing, then field set, membership, identities, finite XY and label bounds. No population regeneration or new exclusions.

Use the final model artifact outputs/reserved_evaluation/final_development_models.json, SHA-256 `0383561e45bcd9f8d84eccc7e9733b2409536f61c39193fa87d08c36c6f6fd65`, including original preprocessing, coefficients, features and environment. Development target comparisons are IN-SAMPLE DIAGNOSTICS, not replication. No fit, preprocessing estimation, feature/kernel/scale change, alternative model or new population rule.

No raw provider products, network requests, reserved detail, withheld match, pose, velocity, animation or temporal-context access. Public historical aggregates may be read as authority/context only. The canonical XY snapshots contain no measured ball/pitch dimensions/player roles; do not invent them.

## Chronology, commands and storage

Separate commits: protocol; tested implementation; feature-only authority; aggregate diagnostics plus selected-case authority before rendering; review-ready checkpoint; final report after independent review. No amendments/squashing of historical research commits. The runner scripts/session_07_construct_validity.py exposes preflight, prepare-diagnostics, summarize, select-passages, render-passages, record-review, reveal-passages, close-review, publication-check. Each requires its prerequisite commits and hashes; no automatic boundary crossing. Outcome-bearing diagnostics use an exclusive persistent marker, with no automatic rerun. Preserve exposed artifacts and stop on a defect.

Public namespace outputs/construct_validity_diagnostics/: diagnostic_authority.json, diagnostic_summary.json, feature_disagreement.csv, contribution_summary.json, m2_role_summary.json, stratified_diagnostics.csv, selected_passage_manifest.json, review_summary.json, qc.json, manifest.json. All detailed rows, source/case mappings, scores, coordinates, diagrams, response forms and execution/access logs remain in ignored local/ beneath that namespace. Public outputs contain aggregates, stable aliases, neutral case IDs and provenance only; no reconstructive records or case-to-category mappings. New CSVs use LF.

## Pure calculations and diagnostic authority

Reuse pure choice_features, point_to_segment_distance, summed_segment_attenuation and expected_credits. Do not import Session 5's fitting wrapper or historical orchestration modules. Assemble M2 by appending the unchanged attenuation primitive to M1; synthetic feature oracles establish equivalence. No optimizer imports/calls in the Session 7 production dependency graph.

Canonical utility is float64 standardized-matrix @ frozen coefficients. Per-feature components are standardized values times coefficients; attacking component sums the first three. Record raw and within-choice-centered component distributions. Validate reconstruction with 8*p*float64_epsilon*max(1,sum(abs(components)),abs(utility)); record maximum absolute residual. Rankings always use canonical utility, not reconstructed sums. M1−M0 and M2−M1 bookkeeping separately records changed shared-feature coefficients and new defensive terms, raw and centered; these are fitted-score components, never causal contributions or importance estimates.

Ranks use descending block-high absolute 1e-12 ties and expected positions; compare top sets without identity tie-breaking. Report strict reversals separately from tie creation/removal and other ordering changes. Pairwise order is determined from these blocks. Target rank difference is new minus old (negative improves). No whole-development headline performance benchmark is recomputed; report the authorized diagnostic rank changes and frequencies.

Candidate distributions weight match → attempt → candidate equally; pair distributions weight match → attempt → eligible pair equally. Report empty eligible-pair states separately, not as zero disagreement. Scalar state summaries weight match then attempt. Summary quantiles are inverse weighted empirical CDF at 5%,25%,50%,75%,95%; rank changes additionally report mean, median, minimum, maximum and sign counts. This is descriptive, no significance test or confidence interval.

prepare-diagnostics passes only geometry to feature/cutpoint functions. Freeze 25/50/75% weighted inverse-CDF cuts for distance, signed longitudinal displacement, absolute lateral displacement, nearest receiver-defender distance, minimum finite-segment distance and attenuation. Boundaries belong to the lower interval; duplicate cuts collapse. Direction: forward dx/length > sin(10 degrees), backward < -sin(10 degrees), otherwise approximately lateral. Length <=1e-9 m is a separate degenerate implementation case. The angular band is descriptive, not football truth.

Non-nearest proximity mass is math.fsum(exp(-d/5)) over numerically sorted defender-segment distances after removing one nearest distance. Its candidate mean forms a label-independent state descriptor with equal-match/attempt quartiles. It is diagnostic bookkeeping, not a predictor. Commit feature-only cutpoints and authority before outcome-bearing summaries.

## Families and strata

A: within-choice candidate-pair receiver-distance versus segment-distance disagreement, omitting differences <=1e-12 in either feature. Report eligible/disagreeing pair counts, equal-weight fractions, and M0/M1 order agreement/reversal/tie behavior on discordant pairs.

B: distributions of the fitted utility components and within-choice contrasts. Report between-model shared-coefficient changes separately from added terms. Utilities are not calibrated physical accessibility units.

C: M2 top-set changes, target expected-rank improvements/worsenings/ties and magnitudes; unchanged order despite utility changes; tie and strict-reversal frequencies. Describe concentration across non-nearest-mass strata without tuning cutoffs.

D: target-connection strata use the six frozen feature cuts plus direction; explicitly condition on the vendor's selected target. State non-nearest-mass strata are label-independent. Report per-match counts/mean rank changes and equal-match means across represented matches, with represented-match counts. Empty strata are explicit count zero/null summary, never zero effect. No new exclusions for sparse bins.

E: selected regressions/disagreement cases as below. No manual interesting-example selection or omitted embarrassing cases.

## Deterministic twelve-case selection

Priority: failure, feature disagreement, M2 ordering change, agreement. At most three each and twelve total; at most two cases per match globally; never duplicate a canonical row. Tie key is SHA-256(population_hash + ':' + zero-based canonical row ordinal). Candidate identifiers never break model rank ties.

Failure: two M1−M0 cases, then one M2−M1 case with expected target rank worsening >=2; greatest worsening first then hash. Feature disagreement: positive raw-feature disagreement and different M0/M1 top sets; greatest disagreement fraction then hash. M2 ordering change: different M1/M2 top sets; greatest changed-pair fraction, greatest absolute target-rank change, then hash. Agreement: common unique top candidate in all three models equal to target; hash order. Greedily enforce existing quotas, global match cap and deduplication; no replacement rules or relaxation. Report shortfalls. These are purposive cases, not prevalence estimates.

Selection output is committed before rendering. Assign neutral case_01.. IDs in hash order; hide selection categories in both review stages. Public manifest contains aggregate category counts, neutral IDs and hashes, never category-to-case mappings. The ignored selection file retains ordinals/category/hash and binds the packet.

## Independent human review

Stage A: dependency-free static SVG coordinate maps, equal aspect ratio, scale in metres, attack +x arrow, carrier, anonymous candidates and defenders. No pitch boundary/ball/team-role invention. No target, scores, ranks, components or category. Render only selected states. A local README and editable JSON form comprise the packet. Neutral IDs and candidate labels remain stable between stages. Validate graphical geometry and masking synthetically before access; preview only Stage A after selection commit.

Stage A response schema: reviewer {experience,prior_familiarity}; each case {case_id,candidate_accessibility:{C01..: high|intermediate|low|not_assessable},receiver_pressure,corridor_constraints,missing_context,confidence: low|medium|high,practitioner_meaningful: yes|no|uncertain,notes}. Human fields initially null/empty, never generated as judgments. Require every selected case/candidate and reviewer metadata, with unknown judgments allowed. Preserve returned bytes separately; normalize only JSON formatting for a locked representation. No answer repair/inference. record-review --stage A --input reads only the fixed local/stage_a_responses.json; locks/hash-commits before reveal. No packet is sent to others automatically.

Stage B: reveal target, expected ranks and bounded raw/centered fitted-component tables, retaining the Stage A maps. Fixed questions: (1) M1 geometric relationship; (2) receiver/corridor agreement; (3) model-preferred candidate's spatial accessibility; (4) provider target's spatial constraint/accessibility; (5) M2 additional defender structure; (6) omitted football factors; (7) practitioner relevance; (8) accessibility-consistent / receiver-selection-only / ambiguous / model-failure interpretation. Candidate nearest defenders are geometric references, not credited blockers. Preserve uncertainty and unfavorable responses. record-review --stage B similarly locks the fixed response file. Case masking is not full study blinding; prior familiarity is recorded.

First execution stops with AWAITING INDEPENDENT REVIEW and a Stage A packet. It must not reveal Stage B or issue a construct classification. Missing human input is pending, not invalid. Later commands require returned human forms; assistant may summarize, never fabricate review. Final primary A/B/C/D and secondary 1/2/3/4 are reasoned after review, not automatically calculated from arbitrary cutoffs. close-review requires a human-reviewed interpretation record naming these classifications, rationale and exactly one future question; no model revision.

## Tests, publication, closure

Before outcome-bearing diagnostics test feature oracles/nesting, decomposition and signs, ties/ranks/population identity, disagreement/weighting/cuts/target independence, quotas/caps/shortfalls/determinism, masking, immutable reviews/reveal gates, exact read-path/firewalls, no prohibited imports, schemas/redaction, atomic closure/failure and synthetic full lifecycle. Test LF output and inspect each command exit before commit/push, preserving Session 6e's qualification.

Hash-check authority before every phase; logs contain phase/operator/status/hashes and aliases only. Hash and validate generated aggregates before display; do not manually alter them. Full active suite and focused tests report pass/skip counts separately; compile, publication, changed/staged-artifact, link and git diff checks before reviewed commit/push. Pending manifest explicitly records review pending; final report docs/session_07_construct_validity_diagnostic_report.md only after human review. Do not update unrelated status surfaces.

The final report must consider defenders reacting to attacking structure, provider target-generation dependence, tactical preferences, receiver role/quality, missing carrier orientation, progression preference, latent game state, omitted dynamics and attacking/defensive dependence. Preserve negative/mixed conclusions. Primary A remains proxy support only; M2 cannot decide primary interpretation. Recommend exactly one evidence-linked future question; network/pose/velocity/model revision remain unauthorized. Stop after the appropriate human-review checkpoint or final closure; no Session 8.
