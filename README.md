# Disrupting the Network

**A provider-independent study of how defensive positioning reshapes local
carrier-to-receiver option networks.**

Football is a system of interacting spatial options. Before a tackle,
interception, or completed pass appears in an event log, the player in possession
faces a changing set of possible receiver connections. Defenders can relate to
several of those connections at once: by pressuring a receiver, occupying a
passing corridor, or changing the shape of the option set without touching the
ball.

Disrupting the Network asks how those relationships can be measured without
jumping directly to an opaque whole-team graph. The current supported object is
a **local directed star** from one anonymous carrier to every eligible teammate.
Its edges are transparent geometric descriptions evaluated through a governed
receiver-ranking benchmark and an experimental public Python package.

The project is an entry in the **PySport Analytics Cup 2.0, USA Football /
Defensive Positioning challenge**, using permitted SkillCorner Australia
A-League 2024/25 data.

![Synthetic M0 and M1 local attacking-option networks](https://raw.githubusercontent.com/JeremyBetz/defensive-network-disruption/main/outputs/public_examples/synthetic_option_network.svg)

The figure is fully synthetic. Edge width shows model-implied receiver-option
share, not true accessibility or pass probability. View the
[eight-second animation](https://github.com/JeremyBetz/defensive-network-disruption/blob/main/outputs/public_examples/synthetic_option_network_animation.gif).

## What has been established

The empirical foundation ranks the provider-targeted receiver among independently
constructed teammate candidates immediately before a recorded pass transition:

- **M0** uses connection length and signed longitudinal and lateral displacement.
- **M1** adds distance from the nearest defender to the receiver and to the finite
  carrier-receiver segment.
- **M2** adds one fixed summary of distributed defender proximity to that segment.

Mean reciprocal rank (MRR) rewards placing the targeted receiver near the top.
On ten protected matches, M0 achieved `0.487333389` and M1 achieved
`0.579003393`, a gain of `0.091670004`. M1 improved MRR, Hit@1, and Hit@3 in
every match. This is the major replicated result: transparent defensive geometry
adds receiver-selection ranking information beyond attacking geometry.

M2 reached `0.585853527`, adding `0.006850134` over M1. Its MRR gain was positive
in all ten matches, but Hit@1 improved in nine and Hit@3 split five positive and
five negative. It is a smaller, metric-dependent refinement. Read the
[protected-evaluation brief](https://github.com/JeremyBetz/defensive-network-disruption/blob/main/docs/session_06e_corrected_reserved_evaluation_decision_brief.md)
and [claim ledger](https://github.com/JeremyBetz/defensive-network-disruption/blob/main/docs/claim_status.md).

The local-star view exposes structure that a leading-option list misses. In all
7,227 development states, at least one anonymous defender was segment-nearest
for multiple carrier-receiver edges. The most involved defender was nearest to a
mean 5.83 edges. Receiver-nearest and corridor-nearest defender sets overlapped
on only about 29.3% of edges, showing that endpoint pressure and passing-corridor
geometry are often different relationships. These are aggregate geometric
patterns, not defender attribution or suppression. See the
[Session 13 report](https://github.com/JeremyBetz/defensive-network-disruption/blob/main/docs/session_13_defender_edge_influence_report.md).

## Current research direction

The current scientific question is whether continuous carrier-origin directional
fields can compactly describe that multi-edge geometry beyond isotropic
proximity. These fields remain geometric hypotheses; cover shadows have not been
validated. The project has completed substantial synthetic numerical,
cross-platform reproducibility, canonical partition, failure-handling, lifecycle,
and exposure-accounting validation. A full development-set structural comparison
has not yet completed, so there is no empirical field result to interpret. The
complete stopped and negative history remains in the
[research log](https://github.com/JeremyBetz/defensive-network-disruption/blob/main/docs/research_log.md).

Conditional future work includes behavioral validation, defensive-configuration
evaluation, threat or value weighting, pose and orientation, and possible links
to defensive reallocation research. None is authorized by the current evidence.

**THE GRAPH IS NOT THE STARTING POINT.** A complete star contains its edge
vector; summary statistics do not create new information. Whole-team topology,
centrality, attribution, and value require separate questions and evidence.

## Use the experimental package

The public [`v0.1.0` prerelease](https://github.com/JeremyBetz/defensive-network-disruption/releases/tag/v0.1.0)
provides immutable option states and networks, explicit M0/M1 evaluation,
Kloppy interoperability, pandas export, and mplsoccer/Matplotlib visualization.
It is provider-independent and pre-1.0: importing it never loads competition data
or coefficients. Callers supply states, models, player selections, and coordinate
context explicitly.

The package is not on PyPI. Run the complete synthetic workflow from source:

```sh
git clone https://github.com/JeremyBetz/defensive-network-disruption.git
cd defensive-network-disruption
uv sync --locked --all-extras
uv run --locked python examples/quickstart.py --output quickstart.svg
```

The quickstart constructs a synthetic Kloppy frame, evaluates explicit M0 and M1
demonstration models, compares their stars, exports rows, and renders an SVG. See
the [public API guide](https://github.com/JeremyBetz/defensive-network-disruption/blob/main/docs/public_api.md)
for the core, optional extras, plotting, animation, ties, and error behavior.
The repository combines spatiotemporal data contracts, geometric feature
engineering, protected evaluation, deterministic numerical oracles,
cross-platform CI, fail-closed research execution, packaging, and release
engineering in one reproducible workflow.

## Repository guide

- [`src/defensive_network_disruption`](https://github.com/JeremyBetz/defensive-network-disruption/tree/main/src/defensive_network_disruption): released API and internal research primitives.
- [`examples/quickstart.py`](https://github.com/JeremyBetz/defensive-network-disruption/blob/main/examples/quickstart.py): proprietary-free runnable example.
- [`tests`](https://github.com/JeremyBetz/defensive-network-disruption/tree/main/tests): synthetic software, numerical, integrity, and publication tests.
- [`docs`](https://github.com/JeremyBetz/defensive-network-disruption/blob/main/docs/README.md): current authority, governance, protocols, reports, and evidence limits.
- [`outputs`](https://github.com/JeremyBetz/defensive-network-disruption/tree/main/outputs): reviewed aggregate evidence and synthetic public artifacts.

Run the active suite with `uv run --locked python -m unittest discover -s tests`.
Bug reports, questions and general feedback are welcome through
[GitHub issues](https://github.com/JeremyBetz/defensive-network-disruption/issues).
The [participation policy](https://github.com/JeremyBetz/defensive-network-disruption/blob/main/CONTRIBUTING.md)
explains how independent competition authorship is preserved while the released
software remains available under its open-source license.

## Limits and reproducibility

The benchmark uses a useful SkillCorner vendor target with **Tier B label
limitations**. Model-implied shares are conditional receiver-choice quantities,
not calibrated accessibility probabilities. Accessibility remains **PROXY ONLY**
and suppression remains **NOT SUPPORTABLE**. The offline, extrapolated tracking
does not establish real-time availability. Results do not identify a causal
defender effect, best pass, pass success, tactical intent, player quality, or
defensive value, and the current network is not a validated whole-team graph.

Competition data is never committed or automatically loaded. Empirical
reproduction requires separately obtained permitted files and the applicable
frozen protocol. Review the [data guidance](https://github.com/JeremyBetz/defensive-network-disruption/blob/main/data/README.md),
[governance](https://github.com/JeremyBetz/defensive-network-disruption/blob/main/docs/research_governance.md),
and [competition rules](https://github.com/JeremyBetz/defensive-network-disruption/blob/main/docs/competition_rules.md).
Original code and documentation use the [MIT License](https://github.com/JeremyBetz/defensive-network-disruption/blob/main/LICENSE.md);
SkillCorner data is neither included nor relicensed.
