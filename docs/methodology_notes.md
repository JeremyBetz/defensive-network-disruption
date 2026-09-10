# Methodology notes

Status: candidate design space only. No edge definition, formula, fitted model,
parameter choice, or target has been adopted. The resource review in
[references/library_review.md](../references/library_review.md) informs future
work; software availability does not validate a construct.

## Define the connection before the graph

`w_ij(t)` is a notation placeholder for a directed attacking connection. First
decide whether it describes selection, physical feasibility, receiver access,
completion conditional on an attempted pass, or usefulness after receipt.
These are different targets. Do not call a generic score a probability, and do
not multiply components just because they can all be scaled to [0, 1].

Begin by comparing the observability of current-ball-carrier edges with all
attacker-to-attacker edges. The latter would require specifying how a non-carrier
gets the ball, when the next pass occurs, and which surrounding state is held
fixed. A two-hop path is not automatically executable: positions and possession
change after its first edge. No all-pairs graph is assumed.

| Candidate ingredient | Possible construct | Required scrutiny before adoption |
| --- | --- | --- |
| Distance and ball location | A transparent accessibility baseline. | True units, ball/possession reliability, eligible receivers, and limits of distance alone. |
| Pass travel time | Opportunity for interception along a route. | Pass type, ball height, speed/acceleration assumptions, and sensitivity; no fixed speed selected. |
| Corridor geometry | Defender proximity to a potential ball route. | Segment rather than infinite-line behavior, endpoint cases, moving receiver, and uncertainty; no binary blocking radius selected. |
| Reachability / interception | Whether a defender could arrive in time. | Reaction delay, acceleration, velocities, uncertainty, and motion bounds; no universal reaction parameter selected. |
| Receiver access / spatial control | Space potentially available at receipt. | Distinguish control of a location from traversability of the route. |
| Progression / context | Usefulness of a connection. | Separate physical access from tactical utility; no imported xT/EPV surface or utility weight. |
| Defender orientation / pose | Direction-dependent reach or perception. | Orientation reference, visibility, reliability, temporal alignment, and incremental benefit. |
| Receiver movement / orientation | Ability to receive a particular pass. | Decision-time availability, direction versus facing, and uncertainty; no future-location leakage. |

## Continuous attenuation and comparisons

Attenuation should vary continuously if that matches the chosen mechanism;
neither smoothness nor a visually convincing cover shadow establishes validity.
Line-of-sight occlusion, blocked ground-pass space, and reachable interception
space are distinct concepts. Specify which one is measured and how evidence
could refute it.

A defender-specific comparison needs a defensible reference: removed defender,
displaced position, feasible alternative movement, or another specified state.
Each answers a different question. Removal may violate realistic structure;
displacement changes several routes; multiple defenders may be substitutes or
complements. Do not sum leave-one-out differences as if they necessarily
reconcile with a team score. Any attribution rule must disclose its reference,
interaction handling, and interpretation. No attribution scheme is chosen.

## Validation that can fail

Future protocols must separate:

- geometric correctness on synthetic unit cases from empirical validity;
- pass choice from completion conditional on choice;
- selected passes from the unobserved outcomes of unchosen options;
- present accessibility from downstream progression or attacking success;
- raw behavioral observations from vendor-derived model labels;
- team configurations from individual defender contribution.

Distance-only and simple defender-proximity baselines are candidates to consider,
not finalized comparators. Specify the minimal useful improvement, uncertainty,
calibration if a probability is proposed, temporal alignment tolerances, and
robustness to tracking error before validation. Repeated frames require a
dependence-aware analysis unit. Do not infer a large sample from frame count.

SkillCorner documentation describes model-derived Game Intelligence quantities.
Their construction must be understood before using them as targets. Agreement
with a label that uses the same geometric ingredients could be circular, and
downstream labels could leak outcomes into inputs. Availability is not an
independent validation guarantee. See the
[data dictionary notes](data_dictionary_notes.md).

## Pose and defensive structure

Pose is an optional incremental test: compare a precisely defined XY candidate
with an orientation-aware candidate on appropriately reserved passages, then
assess whether an XY proxy can generalize. Velocity direction is not a default
orientation estimator, especially at low speed. Two games do not establish
population-wide performance. Drop or narrow this branch if its independent
validation is infeasible.

Support, cover, compactness, line integrity, rest defense, and recovery after
being bypassed need separate definitions. Preserving a team's current structure
can preserve a poor structure. No universal “structural cost,” additive utility,
exchange rate, or common scale with attacking disruption is assumed.

Network connectivity, redundancy, and bottlenecks are later summaries. Their
meaning depends on edge semantics, eligibility, time, weighting, and threshold
sensitivity. Start with a simple valid edge and require incremental practitioner
usefulness before introducing graph algorithms.
