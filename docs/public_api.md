# Experimental public API

The public API evaluates one local directed star from a ball carrier to an
explicit set of candidate receivers. Its edges contain linear model utilities,
temperature-one softmax shares, expected ranks and tie blocks. The shares are
**model-implied receiver-option shares**. They are not calibrated accessibility,
pass-success probability, causal suppression or defender value.

## Install

The numerical core needs NumPy:

```sh
pip install defensive-network-disruption
```

Repository users can install every public example dependency with:

```sh
uv sync --locked --all-extras
```

Separate extras are available for `interop`, `dataframe`, and `visualization`.
The package is version `0.0.0`; its API is deliberately experimental.

## Evaluate an explicit state

```python
from defensive_network_disruption import OptionState, evaluate_options
from defensive_network_disruption.examples import demonstration_models

state = OptionState(
    carrier_xy=(0, 0),
    candidate_ids=("A", "B"),
    candidate_xy=((12, 8), (22, 0)),
    defender_xy=((8, 3), (16, -2)),
    carrier_id="carrier",
)
_, m1 = demonstration_models()
network = evaluate_options(state, model=m1)

print(network.top_options)
print(network.effective_option_count)
print(network.to_records())
```

Coordinates must be finite metres with positive `x` pointing toward the
attacking goal and the native physical `y` sign retained. Candidates are unique,
aligned with their coordinates and distinct from the carrier. At least one
candidate and one defender are required. The library does not infer eligibility,
active intervals, teams, direction or missing coordinates.

Every call receives a `FrozenOptionModel`. The helper in this example returns
illustrative coefficients; it is not an empirical authority. Application code
may construct a model from its own governed parameters. No model is discovered
or loaded automatically.

`OptionNetwork.edges` preserves candidate order. `top_options` preserves a tied
top set, while `top_option` returns a receiver only when that set is unique.
Summary properties expose top-one share, top-two cumulative share, entropy,
normalized entropy, effective option count and utility range. Entropy and
effective count are two transformations of the same distribution rather than
independent evidence.

## Kloppy frames

```python
from defensive_network_disruption import (
    MetricCoordinateContext,
    option_state_from_kloppy,
)

state = option_state_from_kloppy(
    frame,
    carrier=carrier,
    candidates=candidates,
    defenders=defenders,
    coordinate_context=MetricCoordinateContext(
        verified=True,
        units="metres",
        origin="centre",
        y_axis="up",
        attacking_sign=1,
    ),
)
```

The adapter accepts a real `kloppy.domain.Frame` and explicit Player selections.
It validates that all selected players are tracked, candidates share the
carrier's team, defenders belong to one opposing team, and the coordinate
context is supported. It does not replace Kloppy's dataset, frame, player or
coordinate abstractions. The complete synthetic workflow is in
[`examples/quickstart.py`](../examples/quickstart.py).

## Dataframe export

`network.to_pandas()` returns a fresh dataframe with:

```text
carrier_id, receiver_id, utility, option_share, expected_rank,
tie_block, is_top_option
```

Pandas is imported only when the method is called. Without the `dataframe`
extra, the method raises an installation message; the core remains usable.

## Plot and animate

```python
from defensive_network_disruption import (
    animate_option_network_comparison,
    plot_option_network,
)

figure, axis = plot_option_network(
    state,
    network,
    pitch_length=105,
    pitch_width=68,
    title="Synthetic option network",
)

animation = animate_option_network_comparison(
    states,
    m0_model=m0,
    m1_model=m1,
    pitch_length=105,
    pitch_width=68,
    fps=10,
)
```

The caller must supply actual pitch dimensions. mplsoccer draws the custom pitch;
project code owns the option-network encoding. Plotting translates centred
metric coordinates into that canvas and rejects points outside it. The animation
returns a Matplotlib `FuncAnimation`; callers choose how and where to save it.

The committed [static hero](../outputs/public_examples/synthetic_option_network.svg)
and [animation](../outputs/public_examples/synthetic_option_network_animation.gif)
use the same four anonymous candidates and three defenders in both M0 and M1
panels. They contain no provider data. Moving synthetic players illustrate API
behavior only; the paths are not a physical or tactical simulation.

## Scientific boundary

The protected receiver-ranking result supports a narrow association between the
frozen defensive geometry and a Tier B vendor target. Accessibility remains
**PROXY ONLY** and suppression **NOT SUPPORTABLE**. The tracking benchmark is
offline and extrapolated. Neither a strong edge nor a concentrated star proves
that a pass was impossible, a defender caused an effect, or a team gained value.
Read the [claim ledger](claim_status.md) before reusing the terms or results.
