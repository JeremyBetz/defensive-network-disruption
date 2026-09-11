# Session 7 — Formal construct-diagnostic and model-behavior report

## Decision

**Primary: B — USEFUL RECEIVER-SELECTION GEOMETRY, BUT ACCESSIBILITY
INTERPRETATION REMAINS WEAK.** The frozen M1 representation behaves coherently
as receiver-selection geometry. Its two defensive terms encode distinct spatial
relationships, their fitted signs agree with the stated distance semantics, and
their behavior remains structured across all nine development matches and the
prospectively frozen geometric strata. The diagnostics cannot distinguish
accessibility from correlated tactical and receiver-selection structure.

The permitted interpretation is:

> The frozen defensive-geometry representation exhibits behavior consistent
> with interpretable spatial constraints relevant to receiver selection in the
> development data.

This is weaker than accessibility validation. Accessibility remains **PROXY
ONLY** and suppression remains **NOT SUPPORTABLE**.

**M2: 3 — DISTRIBUTED-DEFENDER TERM IS PRIMARILY A SMALL PREDICTIVE
REFINEMENT.** Its fitted direction is geometrically coherent, but it changes few
candidate-pair orderings and few top-ranked sets. The frozen non-nearest-defender
strata do not show a steadily larger target-rank effect in more crowded states.
The development diagnostics therefore do not establish a clear practical
construct meaning beyond M2's already supported, smaller ranking increment.

**Software readiness: YES, BUT NARROWLY.** Expose reusable provider-independent
primitives with explicit neutral names: carrier–receiver geometry,
receiver-nearest-defender distance, finite-segment defender distance, and fixed
summed segment proximity. Do not call the API accessibility, suppression,
defender credit, or defensive value.

**Network readiness: YES, WITH RESTRICTIONS.** The edge representation has earned
a separately governed exploratory attacking-option network phase using neutral
edge semantics. Network aggregation would be a diagnostic extension, not proof
that the edges represent true availability or that graph summaries have tactical
or practical value. **THE GRAPH IS NOT THE STARTING POINT** remains the rule.

## Authority and scope

The starting local, tracking, and live-remote checkpoint was
`2e43368eecb4ccea38d14afb2fc7f3b615ab38f8`. Phase 07b was committed before
classification at `6c5c8b0`; the final result commit is the commit introducing
this report and can be resolved with `git log --diff-filter=A -1 --format=%H --
docs/session_07_construct_validity_diagnostic_report.md`.

The governing sequence is the original
[Phase 07 protocol](protocols/phase_07_construct_validity_diagnostics.md), the
later [Phase 07a human-review withdrawal](protocols/phase_07a_human_review_withdrawal.md),
and the [Phase 07b formal closure](protocols/phase_07b_formal_diagnostic_closure.md).
Phase 07a supersedes only the review path; Phase 07b authorizes classification
from already closed public aggregate diagnostics.

The exact final M0/M1/M2 model artifact evaluated in Session 6e has SHA-256
`0383561e45bcd9f8d84eccc7e9733b2409536f61c39193fa87d08c36c6f6fd65`.
The canonical development population has SHA-256
`cd706f9f4621efcf659fbe890d9a6a0ebfff97c3407095a6db5ea05044c1264d`:
7,227 observations from nine spent development matches. All target comparisons
below are **IN-SAMPLE DIAGNOSTICS**, because these final models were fitted on
those matches. They are not another predictive replication.

No model was refitted, no preprocessing was estimated, and no diagnostic was
recomputed for this closure. The committed aggregate package was interpreted
byte-for-byte. No reserved row or passage, withheld match, pose data, raw
provider product, ignored diagnostic row, case mapping, diagram, or response
file was opened. Human review was withdrawn before responses; Stage B was never
revealed, and no human, project-author, self, or assistant judgment is evidence.

## M1 feature disagreement

Across 312,602 eligible within-choice candidate pairs, the receiver-nearest and
finite-segment defender distances disagreed on ordering for 108,543 pairs. The
equal-match disagreement rate was `0.347759757`. It was present in every match,
ranging from `0.318451276` to `0.369893858`. Only five of 7,227 states had no
eligible comparison pair; 7,218 states contained at least one discordant pair.

M1 strictly reversed the M0 ordering for an equal-match fraction of
`0.126764370` of the compared disagreement states/pairs under the frozen
summary, with per-match values from `0.117343451` to `0.141387479`. No tie was
created or removed. These results show that the two defensive variables are not
interchangeable summaries of a single distance and that they alter ordering in
a repeatable subset of choice states. They do not tell us which ordering is
tactically correct.

## Fitted utility decomposition

The final M1 coefficients have the expected directional structure for their
declared inputs: greater carrier–receiver distance lowers fitted utility;
forward displacement raises it; greater defender distance from the receiver and
from the finite segment raises it. This is model behavior, not a causal defender
effect.

All components vary within choice sets. The median within-choice utility range
is `6.098748290` for M1 attacking geometry, `3.775307104` for receiver-nearest
defender geometry, and `0.705140805` for segment-nearest geometry. The segment
term is smaller in typical range but nonzero and structurally distinct. The
maximum utility-reconstruction residual is `3.552713679e-15`, supporting the
additive bookkeeping at the frozen floating-point tolerance.

Model differences cannot be assigned only to newly added columns. When moving
from M0 to M1, the shared attacking coefficients also change; when moving from
M1 to M2, the five shared coefficients change again. The centered M2−M1 shared
component spans a 5th–95th percentile interval of approximately `-0.277221932`
to `0.253686721`, while the new attenuation component spans approximately
`-0.360652634` to `0.297254732`. The report therefore treats each as fitted
utility bookkeeping and does not label the attenuation column as the entire M2
effect.

## M2 behavioral role

M2 changes `0.025080769` of within-choice candidate-pair orderings and changes
the top-ranked set in `0.051981412` of states. Target rank is unchanged in 6,216
of 7,227 states (`86.01%`), improves in 552 (`7.64%`), and worsens in 459
(`6.35%`). Mean absolute target-rank movement is `0.158820457`; the median and
75th percentile are zero, and the 95th percentile is one position. Its signed
mean target-rank change is `-0.013451653`, where negative denotes improvement.

The attenuation coefficient is negative, so greater summed proximity to the
finite segment lowers fitted utility, consistent with the primitive's stated
geometry. Yet the label-independent non-nearest-defender state strata do not
show a monotonic increase in M2 target-rank movement: equal-match means across
the four frozen bins are `-0.015672975`, `-0.021492551`, `-0.020062250`, and
`0.002518873`. The most crowded bin is essentially neutral and slightly favors
worsening on this signed summary. M2 is therefore mainly a small perturbation;
these diagnostics do not establish a stronger distributed-defense construct.

## Frozen geometric strata

M1 target-rank behavior is structured rather than uniform. Across increasing
connection-length quartile bins, equal-match mean rank changes are `0.033162508`,
`-0.989018204`, `-1.498578984`, and `-1.169362605`. Improvements are concentrated
away from the shortest connections. Across increasing receiver-nearest-defender
distance bins, the corresponding values are `0.351835030`, `-0.125410410`,
`-0.547218614`, and `-1.581024138`; across increasing finite-segment-distance
bins they are `0.134549827`, `-0.124913377`, `-0.452568285`, and
`-1.033004871`. This matches the fitted model's preference for candidates with
more defensive separation while retaining failures in tightly defended strata.

M1 improves average target rank in forward (`-0.674234755`), approximately
lateral (`-0.764427956`), and backward (`-0.235639457`) categories. No
degenerate segment occurred. M2 remains small and mixed by direction: forward
`0.039767625`, approximately lateral `-0.016448076`, and backward
`-0.097027185`. Across target-connection attenuation bins, M2 improves average
rank in the first three but worsens in the highest bin. These are conditional
descriptions of provider-target connections, not estimates of option
availability or population-level tactical effects.

## Formal failures and limits

M1's average target-rank change is `-0.536542494`, but its frozen distribution
includes a maximum worsening of eight positions and a 95th percentile worsening
of two. M2 includes a maximum worsening of four and a 95th percentile worsening
of one. The algorithmic selection procedure filled all three formal failure
slots, as well as three feature-disagreement, three M2-ordering-change, and three
agreement slots, without quota relaxation. Those cases and diagrams remain
historical review-ready artifacts; none was inspected for this closure.

The failures prevent an unqualified accessibility claim, but they do not expose
a fundamental numerical or geometric contradiction. The defensive variables
retain their expected fitted direction, their distinctness is stable across
matches, the additive decomposition reconstructs utility, and the diagnostic QC
records no fitting, raw-provider, reserved-detail, or withheld access. The
result therefore supports B rather than A, C, or D: useful bounded geometry,
with weak accessibility interpretation.

## Claims and unresolved alternatives

C09 remains **SUPPORTED WITHIN SCOPE** for M1 receiver ranking and C10 remains
**SUPPORTED WITHIN SCOPE** for the smaller M2 increment. C01 and C02 remain **IN
PROGRESS** because general attacking-edge meaning and defensive attenuation of
connectivity remain under investigation. C03–C08 remain **UNTESTED**.

Formal coherence does not resolve defenders reacting to latent attacking
structure; player and team tactical tendencies; receiver quality or role;
omitted carrier orientation; progression preference; provider target-generation
semantics; latent game state; or the joint determination of attacking and
defensive geometry. It does not validate accessibility, suppression, causal
defender effects, best-pass judgment, player attribution or value, practitioner
usefulness, or network disruption. Tier B target limitations and the offline,
extrapolated-tracking qualification remain.

## Verification and closure

The preserved diagnostic manifest SHA-256 is
`8a4ad2f684fdf83101cdf439aaaf5aec66bcde6e431efcb73b76cdda1c4485fc`.
The formal closure manifest SHA-256 is
`3384c707fb9612dedd9b7ac1dad0f8773952ab7e8ef2d3ccac472604a773f879`.
To avoid recursion, the manifest binds this report by the SHA-256 obtained after
replacing that displayed manifest hash with 64 zeroes.

Required focused and full test counts, compilation, publication checks,
authority preservation, staged review, push, and final synchronization are
recorded after execution in the append-only research log and final handoff.

## One next direction, not executed

Run one **separately governed exploratory attacking-option network phase** using
only the frozen neutral edge primitives and provider-independent interfaces.
Test whether simple aggregation adds interpretable information beyond edge-level
summaries. Do not call the edges accessibility, suppression, or value, and do
not add a model, alternate kernel, pose, velocity, reachability, pitch control,
attribution, or player ranking under that authority.

Session 7 stops here. The recommendation is not executed.
