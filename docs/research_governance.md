# Research governance

Effective 2026-09-09. Applies to exploratory and confirmatory work, including
negative results. Current status aligned 2026-09-12: governed development and
protected receiver-ranking work has been completed through Session 6e; Session
7 closed as a development-only formal diagnostic after its human-review branch
was withdrawn; and Session 13 established recurring development-only multi-edge
geometry. Continuous-field work remains pre-empirical after Session 14ag repaired
the prospective exposure-accounting contract that blocked Session 14R5.
Exposure, partitions, protocols, results, failures, and current non-claims are
recorded in the research log and linked authorities.

## Prospective protocols

Before each empirical phase, commit a protocol under `docs/protocols/` and
reference its commit from the run record. A draft is not authorization to run
an analysis with undefined decisions. Resolve all fields relevant to that run:

1. Protocol ID, version, author, date/time, status, question, and linked claim IDs.
2. Observable construct and candidate estimand, units/scale, observation unit,
   population, eligible pairs/states, horizon, and intended level of inference.
3. Permitted release/version, required fields, joins, preprocessing, quality
   exclusions, synchronization rules, and missing-data treatment.
4. Assumptions, candidate mechanisms, alternative explanations, and explicit
   non-claims; distinguish measured inputs from inferred quantities.
5. Development and validation membership references, grouping and selection
   procedures, seed if random, previous exposure, and intended generalization.
6. Primary candidate/target/metric, simple baseline, restricted alternatives,
   ablations, robustness checks, and how multiple comparisons will be handled.
7. Validation logic, uncertainty accounting for repeated observations, feasibility
   requirements, numerical decision rules, stop conditions, and failure handling.
8. Exact execution command, configuration, code and environment versions, expected
   artifacts, logging location, and what outcomes will become visible to whom.
9. Permitted conclusions for success, mixed evidence, failure, or invalidity.
10. Amendments and deviations, with timing relative to outcome access.

Before inspecting the relevant outcome, freeze selection rules, target, metric,
and decision criteria. Candidate discovery on development data is allowed and
must be labeled exploratory. Do not describe retrospective choices as
prospective. If an amendment follows an outcome view, label it accordingly and
identify the fresh evidence needed for confirmation.

## Development and validation discipline

Inventory metadata first. Record which products overlap at match level before
choosing partitions; exact proportions, match assignments, and seeds are unset.
Consider the event subset and the two-game pose subset explicitly. An apparently
large frame count is not a large independent match sample.

Keep related observations together at the justified independent grouping level.
Adjacent frames, overlapping windows, and the same possession cannot cross
partitions. Prefer match-level separation when feasible; document recurring
teams/players and any remaining dependence. If the target is unseen teams or
players, match separation alone does not establish that generalization.

Fit thresholds, normalization, imputation, smoothing choices, and candidate
selection on development data only. Freeze preprocessing before evaluating
validation. Only information available at the decision time may enter a
prospective connection estimate: later receiver positions, future events, and
centered smoothing can leak the answer. Any retrospective diagnostic using
future information must be labeled and excluded from prospective claims.

Maintain an access ledger in [research_log.md](research_log.md). For each view,
record timestamp, operator, protocol version, local partition/match reference,
fields or outcomes accessed, purpose, and whether it spends validation data.
Protected identifiers can remain in ignored local manifests, with public
protocol references and hashes only where release terms permit them. Viewing
validation plots, aggregates, labels, or outcome-dependent quality summaries
counts as access, not just running a model. No hidden outcome peeking.

If validation is accidentally opened, log the exposure promptly. Reclassify the
affected material as exposed; revise the evaluation design before continuing.
Do not silently reset the ledger or keep calling those observations untouched.
If no fresh validation remains, state that limitation rather than imply
independent confirmation.

## Results and claim escalation

Keep all planned comparisons and attempted candidate versions, including
negative, mixed, invalid, and stopped runs. Never select a new metric after
seeing validation simply because it improves the story. Later candidates need
a new protocol and, for confirmation, fresh validation.

Retain local run artifacts under `outputs/`, including code SHA, protocol SHA,
configuration, release/manifests, environment, seeds, counts/exclusions, metrics,
uncertainty, failures, and deviations. Record a non-sensitive summary in the
research log even when a run produces no publishable figure. Preserve old
entries; append corrections and superseding decisions. Safe summaries can be
published after terms and provenance checks; raw and derived competition
records remain untracked.

The claim ladder is **measurement -> association -> interpretation -> attribution
-> value**. This is an evidence ladder, not an automatic promotion sequence:

| Level | Evidence needed to consider it | Insufficient evidence |
| --- | --- | --- |
| Measurement | Defined semantics, verified inputs, meaningful validation, uncertainty, and scope. | A plausible plot or mathematical construction alone. |
| Association | Prespecified target and comparison, dependence-aware uncertainty, leakage checks, and validation beyond development. | Correlation among neighboring frames or a selected example. |
| Interpretation | A football mechanism compatible with evidence and alternatives; clearly labeled inference. | Naming a score “cover shadow” or inferring intent from XY. |
| Attribution | Explicit reference/comparison, interaction handling, robustness, and identification assumptions. A causal claim needs a justified causal design. | Removing a defender from a model and calling the difference their real-world effect. |
| Value | A validated beneficial sporting outcome, context, costs/tradeoffs, reliability, and the necessary attribution evidence. | Larger disruption or smaller compactness automatically meaning better defense. |

Update [claim_status.md](claim_status.md) only with linked protocol/run evidence,
scope, uncertainty, limitations, and a dated rationale. Team-level evidence
cannot promote an individual-player claim. Model sensitivity is not identified
player contribution; association is not causation.

## New work, permitted data, and open-source release

Use only the competition-permitted SkillCorner data. Public literature can
inform methods, but external match data, labels, pretrained empirical models,
or parameters learned on ineligible data cannot be silently introduced as
competition inputs. Check eligibility before such use. Purely synthetic unit
test geometry must be labeled, contain no match records, and never serve as
football-validation evidence.

No `moving-the-defense` code, results, figures, tuned settings, or datasets are
imported by this scaffold. Its public README was viewed, including visible
published summaries. Treat possible shared-data exposure explicitly in the
future split audit rather than claiming absence of prior knowledge. Before actual reuse of any
general utility, record its origin/version, license, exact reused material,
reason for reuse, adaptations, competition eligibility, and how this entry
still contains substantial new work with a different question and estimand.
If eligibility is unclear, do not bring that material into the submission until
resolved. General lessons and coding patterns do not establish a new result.

Release original code and documentation under MIT and keep the submitted work
open source forever, as required by the supplied brief. The software license
does not grant rights to SkillCorner data. Do not commit raw data, derived
records, credentials, private paths, or notebook outputs containing them.
`.gitignore` is a guard, not a guarantee: inspect staged files and notebook cells
before committing; never force-add competition data. Record sources and retain
third-party attribution and license notices where appropriate.

Public release hardening, the video, and final submission are separate future
steps. Before submission, audit claim wording, data provenance, README limits,
and license scope. Reproduce the exact documented workflow in a new environment
using only open-source tools and permitted inputs. Software checks demonstrate
implementation behavior; scientific evidence comes only from the governed
empirical protocols and results within their stated scope.
