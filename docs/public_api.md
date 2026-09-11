# Experimental public API

Version `0.1.0` evaluates one local directed star from a ball carrier to an
explicit set of candidate receivers. Its edges contain linear utilities,
temperature-one softmax shares, expected ranks and tie blocks. Shares are
**model-implied receiver-option shares**. They are not calibrated accessibility,
pass-success probability, causal suppression or defender value.

## Install

The package is not published on PyPI. From a repository checkout:

```sh
uv sync --locked
```

The core requires only NumPy. Optional environments are:

```sh
uv sync --locked --extra interop        # Kloppy adapter
uv sync --locked --extra dataframe      # pandas export
uv sync --locked --extra visualization  # plots and GIF support
uv sync --locked --extra public         # complete public workflow
```

The experimental wheel and source archive are distributed through the
[`v0.1.0` GitHub prerelease](https://github.com/JeremyBetz/defensive-network-disruption/releases/tag/v0.1.0).
If a future PyPI publication is separately authorized, the corresponding syntax
will be `pip install "defensive-network-disruption[public]"`.

The API is experimental and pre-1.0. Minor releases may change interfaces; each
change must be recorded in [the changelog](../CHANGELOG.md). The ten names
exported by `defensive_network_disruption` are the supported surface. Deep
research and session modules are internal even though their source ships with the
research package.

## Core concepts

`OptionState` is immutable selected geometry. Coordinates are finite metres in
the `metric_attack_x_native_y` convention: positive x points toward attack and y
retains its physical sign. Callers decide eligibility, active state, teams and
attacking direction. At least one candidate and one defender are required.

`FrozenOptionModel` contains an explicit M0 or M1 feature order, training means,
scales and coefficients. It never discovers, fits or loads a model.

`OptionNetwork` contains immutable `OptionEdge` rows, the tied top set and the
six frozen summaries. `top_option` is a receiver only for a unique top utility;
otherwise it is `None`.

## Evaluate and compare

```python
from defensive_network_disruption import FrozenOptionModel, OptionState, evaluate_options

state = OptionState(
    carrier_xy=(0, 0),
    candidate_ids=("A", "B"),
    candidate_xy=((12, 8), (22, 0)),
    defender_xy=((8, 3), (16, -2)),
    carrier_id="carrier",
)
m0 = FrozenOptionModel(
    "m0",
    ("distance", "longitudinal_displacement", "lateral_displacement"),
    (0, 0, 0), (20, 20, 20), (-1, 0.35, 0),
)
network = evaluate_options(state, model=m0)
print(network.top_options, network.effective_option_count)
```

Evaluate a second explicit model on the identical state, then call
`compare_options(first, second)`. Comparison requires receiver IDs in exactly the
same order. Its changes include changed shared-feature coefficients as well as
additional defensive features; they are descriptive model changes, not causal
defender attribution.

## Kloppy interoperability

```python
from defensive_network_disruption import MetricCoordinateContext, option_state_from_kloppy

state = option_state_from_kloppy(
    frame, carrier=carrier, candidates=candidates, defenders=defenders,
    coordinate_context=MetricCoordinateContext(
        verified=True, units="metres", origin="centre", y_axis="up",
        attacking_sign=1,
    ),
)
```

The `interop` extra supplies Kloppy. The adapter requires a real Kloppy `Frame`,
explicit disjoint player selections, one opposing team, currently tracked
coordinates and verified metric context. It does not infer eligibility or repair
ambiguous coordinates.

## Dataframe export

`network.to_pandas()` lazily imports pandas and returns a new dataframe with:

```text
carrier_id, receiver_id, utility, option_share, expected_rank,
tie_block, is_top_option
```

Install the `dataframe` extra if pandas is unavailable. Mutating the returned
dataframe cannot alter the immutable network.

## Plot and animate

```python
from defensive_network_disruption import animate_option_network_comparison, plot_option_network

figure, axis = plot_option_network(
    state, network, pitch_length=105, pitch_width=68,
)
animation = animate_option_network_comparison(
    states, m0_model=m0, m1_model=m1,
    pitch_length=105, pitch_width=68, fps=10,
)
```

The `visualization` extra supplies mplsoccer, Matplotlib and Pillow. Pitch
dimensions are mandatory and every coordinate must lie inside the supplied
pitch. Plotting validates exact state/network candidate alignment. Animation
returns a Matplotlib `FuncAnimation`; callers choose whether and where to save it.

The complete [quickstart](../examples/quickstart.py) constructs a synthetic
Kloppy frame, evaluates M0/M1, prints bounded summaries and writes a side-by-side
SVG. The committed [hero](../outputs/public_examples/synthetic_option_network.svg)
and [GIF](../outputs/public_examples/synthetic_option_network_animation.gif)
contain no provider data.

## Errors and limitations

Validation errors name the malformed identity, coordinate, selection, model or
plot argument. Missing optional packages name the extra to install. The library
does not silently trim identities, infer teams, rescale coordinates, load
coefficients or discard candidates.

The protected receiver-ranking result supports a narrow association with a Tier
B vendor target. Accessibility remains **PROXY ONLY** and suppression remains
**NOT SUPPORTABLE**. The benchmark is offline and extrapolated. A strong edge or
concentrated star does not establish availability, the best pass, causality,
defender credit or value. Review the [claim ledger](claim_status.md) before using
the empirical findings.
