# Disrupting the Network

**How does defensive positioning reshape attacking options before a tackle or
interception ever happens?**

Most defensive statistics begin when a defender touches the ball. This project
starts earlier. It uses football tracking data to study how defenders change the
receiver choices available to the player in possession, then exposes the tested
geometry through an experimental provider-independent Python package.

The research is an entry in the **PySport Analytics Cup 2.0, USA Football /
Defensive Positioning challenge**, using permitted SkillCorner Australia
A-League 2024/25 data.

![Synthetic M0 and M1 local attacking-option networks](https://raw.githubusercontent.com/JeremyBetz/defensive-network-disruption/main/outputs/public_examples/synthetic_option_network.svg)

The figure is fully synthetic. Edge width shows model-implied receiver-option
share, not true accessibility or pass probability. View the
[eight-second animation](https://github.com/JeremyBetz/defensive-network-disruption/blob/main/outputs/public_examples/synthetic_option_network_animation.gif).

## What has been established

The empirical foundation is a receiver-selection ranking benchmark. Immediately
before a provider-recorded pass transition, each eligible teammate is a candidate
receiver:

- **M0** uses connection length and longitudinal and lateral displacement.
- **M1** adds the nearest defender to the receiver and to the finite passing
  segment.
- **M2** adds one fixed summary of distributed defender proximity to the segment.

Mean reciprocal rank (MRR) rewards placing the provider-targeted receiver near
the top. On ten protected matches, M0 achieved `0.487333389` MRR and M1 achieved
`0.579003393`, a gain of `0.091670004`. M1 improved MRR, Hit@1 and Hit@3 in every
match. This is the major replicated result: transparent defensive geometry adds
receiver-selection ranking information beyond attacking geometry.

M2 reached `0.585853527`, adding `0.006850134` over M1. Its MRR gain was positive
in all ten matches, but Hit@1 improved in nine and Hit@3 split five positive and
five negative. M2 is a smaller, metric-dependent refinement. See the
[Session 6e evidence](https://github.com/JeremyBetz/defensive-network-disruption/blob/main/docs/session_06e_corrected_reserved_evaluation_decision_brief.md)
and [claim ledger](https://github.com/JeremyBetz/defensive-network-disruption/blob/main/docs/claim_status.md).

## Scientific limits

The benchmark predicts a useful SkillCorner vendor target with **Tier B label
limitations**. It does not observe every option the player considered or prove
which passes were available. Accessibility remains **PROXY ONLY** and suppression
remains **NOT SUPPORTABLE**.

The extrapolated tracking supports an offline benchmark, not a proven real-time
system. Results do not identify causal defender effects, best passes, pass
success, tactical intent, player quality or defensive value. Generalization is
limited to the evaluated competition matches. The development-only
[construct diagnostic](https://github.com/JeremyBetz/defensive-network-disruption/blob/main/docs/session_07_construct_validity_diagnostic_report.md)
found coherent receiver-selection geometry while leaving accessibility weak; no
human-review evidence was collected.

## Why a local network

Receiver ranking validates a possible edge representation. The broader theory is
that attackers form a changing set of possible connections and defenders reshape
that set without winning the ball. Session 8 represented one state as a complete
carrier-centred star and summarized its option-share distribution. In development
data, effective modeled option count changed from `7.165293607` for M0 to
`5.980391018` for M1. This is descriptive and in-sample; summaries add no
information beyond the complete edge vector.

**THE GRAPH IS NOT THE STARTING POINT.** Topology, centrality, attribution and
value require separate questions and evidence.

## Experimental Python package

Version `0.1.0` defines the first coherent public API and remains pre-1.0 and
experimental. Importing the package never loads competition data or model
coefficients. Callers provide explicit states, models, selections and coordinate
context. The numerical core requires NumPy; optional extras provide Kloppy
interoperability, pandas export and mplsoccer/Matplotlib visualization.

The package has not been published. Install the current public workflow from the
repository:

```sh
git clone https://github.com/JeremyBetz/defensive-network-disruption.git
cd defensive-network-disruption
uv sync --locked --all-extras
uv run --locked python examples/quickstart.py --output quickstart.svg
```

The quickstart constructs a synthetic Kloppy frame, evaluates explicit M0 and M1
demonstration models, compares their local stars, exports rows and renders a
side-by-side SVG. Software tests use synthetic fixtures and download no data.

See the [public API guide](https://github.com/JeremyBetz/defensive-network-disruption/blob/main/docs/public_api.md),
[changelog](https://github.com/JeremyBetz/defensive-network-disruption/blob/main/CHANGELOG.md),
and [contributing guide](https://github.com/JeremyBetz/defensive-network-disruption/blob/main/CONTRIBUTING.md).
Run the suite with:

```sh
uv run --locked python -m unittest discover -s tests
```

Competition data is never committed or automatically loaded. Reproduction of
empirical results requires separately obtained permitted files and the applicable
frozen protocol. Review the [data guidance](https://github.com/JeremyBetz/defensive-network-disruption/blob/main/data/README.md),
[research log](https://github.com/JeremyBetz/defensive-network-disruption/blob/main/docs/research_log.md),
[governance](https://github.com/JeremyBetz/defensive-network-disruption/blob/main/docs/research_governance.md),
and [competition rules](https://github.com/JeremyBetz/defensive-network-disruption/blob/main/docs/competition_rules.md).
Code and original documentation use the [MIT License](https://github.com/JeremyBetz/defensive-network-disruption/blob/main/LICENSE.md);
SkillCorner data is neither included nor relicensed.
