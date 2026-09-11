# Agent operating guide

## Repository authority

**THE CURRENT COMMITTED REPOSITORY IS AUTHORITATIVE.** This guide helps a fresh
agent recover context; it is not a research result and does not replace a frozen
protocol, the append-only research log, a decision brief, an output manifest, or
the claim ledger. Do not infer the scientific frontier from chat memory alone.

Before recommending or executing scientific work, reconstruct the current state
from Git and committed evidence. Establish the current `HEAD`, latest completed
session, latest frozen protocol or amendment, unfinished work, authorized next
step, data-exposure state, and supported and unsupported claims. If documents
disagree, preserve the disagreement and identify the later authority that
supersedes the earlier state. Never rewrite history or silently combine
contradictory records into a cleaner story.

Later committed scientific authority takes precedence over this file. Update
this guide when durable policy or the research frontier materially changes; do
not turn it into a session-by-session log.

## After a context reset

1. Run `git status` and identify `HEAD`.
2. If live synchronization is expected, verify `HEAD == origin/main`, including
   the live remote rather than relying only on a local tracking reference.
3. Inspect the latest commits and read this guide.
4. Read [research governance](docs/research_governance.md), the latest entries in
   the [research log](docs/research_log.md), the
   [claim ledger](docs/claim_status.md), and the
   [competition record](docs/competition_rules.md).
5. Read the latest relevant protocol, amendment, decision brief, and output
   manifest. For the current frontier, begin with
   [Phase 07](docs/protocols/phase_07_construct_validity_diagnostics.md), its
   later [Phase 07a amendment](docs/protocols/phase_07a_human_review_withdrawal.md),
   the [Phase 07b closure](docs/protocols/phase_07b_formal_diagnostic_closure.md),
   and the [Session 7 report](docs/session_07_construct_validity_diagnostic_report.md).
6. Inspect authority manifests when the proposed work depends on an existing
   population, model, or result. Relevant current manifests include the
   [Session 6e result manifest](outputs/reserved_evaluation_v3/manifest.json) and
   the [Session 7 formal closure manifest](outputs/construct_validity_diagnostics/formal_closure_manifest.json).
7. State the reconstructed frontier before proposing a new scientific direction:
   latest completed session, current unfinished session, authorized next step,
   spent and protected evidence, and unsupported claims.

Never infer “the previous session succeeded, therefore continue automatically.”
A new governed research session needs a new explicit handoff and whatever
prospective authority that work requires.

## Project identity and research question

The working project is **Disrupting the Network**, an entry in the PySport
Analytics Cup 2.0 USA Football / Defensive Positioning challenge using permitted
SkillCorner Australia A-League 2024/25 data. The motivating question is whether
defender positioning changes the attacking option set before observable
defensive events such as tackles or interceptions.

The completed empirical work is narrower. It tests whether transparent static
defensive geometry adds information when ranking the provider-targeted receiver
among independently constructed teammate candidates. That receiver-ranking
relationship must not be relabeled automatically as accessibility truth,
suppression, cover-shadow truth, causal defender effect, or defensive value.

## Current scientific state

Session 6e is the latest completed protected empirical evaluation. On the ten
then-reserved matches, the frozen models produced these match-macro results:

- M0 MRR: `0.487333389`.
- M1 MRR: `0.579003393`; M1−M0 gain: `0.091670004`. The MRR gain was positive in
  all ten matches, and Hit@1 and Hit@3 agreed in direction in all ten.
- M2 MRR: `0.585853527`; M2−M1 gain: `0.006850134`. The MRR gain was positive in
  all ten matches; Hit@1 was positive in nine and negative in one, while Hit@3
  split five positive and five negative.

The durable interpretation is receiver-selection evidence: the two transparent
M1 defensive-geometry features added replicated ranking information beyond the
defender-free M0 attacking geometry, and the fixed M2 multi-defender attenuation
added a smaller, metric-dependent increment. No significance test or practical
effect threshold was introduced.

The target remains a vendor target with **Tier B limitations**. Accessibility is
**PROXY ONLY**. Suppression is **NOT SUPPORTABLE**. The benchmark uses offline,
extrapolated tracking; selecting a prior timestamp does not prove that provider
processing was causal or available in real time. The evidence does not establish
pass success, the best pass, tactical value, defender intent, attribution, or
generalization to unseen teams, leagues, or providers.

Historical Session 6 and Session 6c executions remain preserved as invalid
outcomes. Their verifier and transport failures were not erased by the corrected
Session 6e execution. Read the Session 6e brief and research log for the exact
chronology and qualifications, including the documented CSV review-order lapse.

## Current frontier after Session 7

Session 7 is closed as a **development-only formal construct-diagnostic and
model-behavior audit** of the frozen M0/M1/M2 geometry. Its development target
comparisons are in-sample diagnostics because the final models were trained on
those matches; they are not another replication study.

Phase 07 originally authorized an independent two-stage human review. A
review-ready packet was produced, but the review branch was withdrawn before any
Stage A response was collected or locked, and Stage B was never revealed. Phase
07a is the later authority. No external reviewer, project-author reviewer, or
assistant reviewer may be introduced as evidence for this execution. The blank
packet and public `AWAITING INDEPENDENT REVIEW` output remain preserved as the
historical stopped checkpoint.

Do not invoke Phase 07's `record-review`, `reveal-passages`, or human-dependent
`close-review` routes. Phase 07b subsequently closed the audit from the already
closed aggregates. Its primary classification is **B — useful
receiver-selection geometry, but accessibility interpretation remains weak**;
M2 is primarily a small predictive refinement. Software readiness is **YES, BUT
NARROWLY**, and network readiness is **YES, WITH RESTRICTIONS** for a separately
governed exploratory network with neutral edge semantics. Session 7 does not
establish independent practitioner validation, ground-truth accessibility,
suppression, causality, attribution, or value. Read the
[Session 7 report](docs/session_07_construct_validity_diagnostic_report.md).

## Data and evidence boundaries

- **Development:** nine matches, already spent for model development and
  diagnostics. They may support explicitly development-only exploratory or
  diagnostic work only under appropriate prospective authority.
- **Formerly reserved:** ten matches, spent by the frozen Session 6e M0/M1/M2
  evaluation. They are not untouched validation for future variants, model
  choices, or exploratory analysis.
- **Withheld:** one match remains protected and unopened. Do not access it unless
  a future committed protocol explicitly authorizes that access.
- **Pose:** remains protected and unopened. Do not assume it is available for a
  new branch without checking later repository authority.

Verify these facts from the current repository before acting. Never infer that a
holdout remains untouched because an older planning document calls it reserved.
Do not publish provider IDs or the protected alias mapping in a continuity
document, report, log, or public diagnostic.

## Claim ladder

The governing evidence ladder is:

`measurement -> association -> football interpretation -> attribution -> value`

Success at one level does not authorize promotion to the next. Predictive
receiver ranking does not prove accessibility. Geometric proximity does not
prove suppression. Removing a defender from a model does not identify causal
contribution. Lower modeled attacking connectivity does not automatically mean
defensive value. Each stronger claim needs its own question, assumptions,
observable, validation, alternatives, and prospective authority.

## Prospective research governance

Before outcome-bearing work:

1. State the football and scientific question.
2. Define the observable or estimand.
3. Identify assumptions, alternative explanations, and non-claims.
4. Specify permitted data, population, partitions, and prior exposure.
5. Specify comparisons, metrics, aggregation, and uncertainty treatment.
6. Define failure, invalidity, deviation, and stop behavior.
7. Freeze and commit the protocol before outcome access.
8. Freeze and test the implementation when appropriate.
9. Execute once according to that authority.
10. Preserve negative, mixed, stopped, and invalid outcomes.
11. Close and report the work before moving to a new scientific question.

Never call a retrospective choice prospective. Never tune a measure silently
until it produces a desirable football story. Protected outcomes are a finite
resource. Development exploration must be labeled as such, and new protected
evidence is needed when a changed model or decision requires confirmation.

Negative, mixed, stopped, and **INVALID** executions are legitimate research
outcomes. Do not amend or squash them away, rewrite old briefs, delete
inconvenient evidence, silently rerun a protected evaluation after a defect, or
redefine failure after seeing results. Use append-only corrections and explicitly
superseding records.

## No automatic escalation

Do not begin any of the following without a specific scientific justification,
explicit user handoff, and new prospective authority:

- M3 or another model variant;
- alternate M2 kernels, scales, interactions, or post-result refitting;
- pose, orientation, velocity, reachability, pitch control, or interception
  modeling;
- network topology, PageRank, community detection, or GNN work;
- defender attribution, player ranking, or defensive-value estimation;
- withheld-match evaluation or renewed scoring on the spent protected set.

Do not add complexity to rescue a weak interpretation.

## Software and open-source direction

The public package is prepared at experimental version `0.1.0`. Session 10
classified it **A — READY FOR EXPERIMENTAL 0.1.0 RELEASE** and the portfolio
artifact **1 — STRONG PORTFOLIO ARTIFACT NOW** after reproducible distribution
and clean-install checks. Its supported surface is the root-package API in
`docs/public_api.md`; deeper research modules remain internal. Read
`docs/session_10_package_hardening_report.md` before release work. The version
has not been tagged, published to PyPI, or issued as a GitHub release.

If the science supports it, the project should produce a meaningful open-source
software contribution. Prefer a reusable, provider-independent Python library or
API before a web/HTTP service. Build in layers: scientifically warranted geometry
or measurement primitives, football-data ecosystem adapters, a visualization or
practitioner interface, and only later an optional service API.

Use neutral names while semantics remain uncertain. An explicit finite-segment
distance or attenuation primitive is safer than publishing a function called
`accessibility_probability()` before calibrated accessibility has been
validated. Do not package an unsupported scientific claim.

**BUILD THE SCIENTIFICALLY NOVEL PRIMITIVE. REUSE THE PLUMBING.** Do not rebuild
commodity football analytics infrastructure when an established package offers
the required semantics. Candidates include Kloppy for provider-independent data
representation, mplsoccer for pitch presentation, matplotvideo for justified
linked animation/video workflows, and NumPy, SciPy, Pandas, or Polars for general
numerical and tabular work. Consider an upstream contribution when a generic
capability is missing from an established PySport package.

Before adopting a package, inspect its current behavior, defaults, license, and
semantic fit. Record the version and reused material, test a narrow adapter, and
preserve competition eligibility and reproducibility. Do not force mismatched
semantics or add dependencies for sophistication alone. The detailed current
reuse record is in [the library review](references/library_review.md).

## Publication and privacy

Only competition-permitted SkillCorner data may support the submission. Original
code and documentation use MIT under the canonical [LICENSE.md](LICENSE.md); that
license does not relicense provider data.

Do not publish raw tracking or event data, credentials, signed URLs, private or
local paths, restricted coordinates or timestamps, identity mappings, detailed
access ledgers, candidate rows, or reconstructive per-attempt outputs. Public
artifacts must be aggregate, sanitized, reproducible, and compatible with the
competition and data licenses. `.gitignore` is a guard, not proof of safety:
inspect every staged artifact and retain required third-party attribution.

## Codex handoffs and session boundaries

Every future Codex handoff for this repository should include exactly:

```text
Planning: ON/OFF
Turbo: ON/OFF
Model: <allowed model>
```

Allowed models: Terra Light, Sol Light, Sol Medium, Astra Light, Astra Medium,
and Astra Extra High.

Use these defaults:

| Task | Planning | Turbo | Model |
| --- | --- | --- | --- |
| Scientific protocol or governance design | ON | OFF | Sol Medium |
| Difficult methodological fork or major architecture decision | ON | OFF | Astra Extra High |
| Repository archaeology or ambiguous debugging | ON | OFF | Astra Medium |
| Light planning or research | ON | OFF | Astra Light |
| Frozen straightforward implementation | OFF | ON | Sol Light |
| Moderate implementation requiring judgment | OFF | ON | Sol Medium |
| Simple mechanical work | OFF | ON | Terra Light |

These settings are workflow defaults, not scientific authority. Choose them for
the actual task; they do not expand its permitted scope.

At the end of each governed research session: close outputs, run and inspect all
required checks, commit, push, verify a clean synchronized repository, stop, and
return the results and one authorized recommendation. Start a new session only
from a new explicit handoff.

## Documentation alignment

The public [README](README.md), [claim ledger](docs/claim_status.md),
[project charter](docs/project_charter.md), and
[research roadmap](docs/research_roadmap.md) were aligned after Session 6e and
Phase 07a. They summarize the current frontier but remain secondary to frozen
protocols, decision briefs, manifests, and later research-log entries.

Public summaries can drift again as research advances. If a summary conflicts
with later committed scientific authority, preserve the historical record and
handle alignment as a separate explicit documentation task. Never alter a
protocol, result, or prior log entry merely to make the public narrative cleaner.
