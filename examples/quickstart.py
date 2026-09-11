#!/usr/bin/env python3
"""Public synthetic quickstart; no provider files or fitted artifacts required."""
from __future__ import annotations

import argparse
from datetime import timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from kloppy.domain import Frame, Ground, Player, PlayerData, Point, Team

from defensive_network_disruption import (
    MetricCoordinateContext,
    compare_options,
    evaluate_options,
    option_state_from_kloppy,
    plot_option_network,
)
from defensive_network_disruption.examples import demonstration_models


def synthetic_frame():
    """Build a tiny Kloppy frame whose coordinates are explicitly synthetic."""
    attack = Team("attack", "Synthetic Attack", Ground.HOME)
    defend = Team("defend", "Synthetic Defence", Ground.AWAY)
    carrier = Player("carrier", attack, 1)
    candidates = tuple(Player(name, attack, number) for name, number in
                       zip(("A", "B", "C", "D"), range(2, 6)))
    defenders = tuple(Player(f"X{number}", defend, number) for number in range(1, 4))
    positions = {
        carrier: (0.0, 0.0),
        **dict(zip(candidates, ((12.0, 8.0), (22.0, 0.0),
                                (10.0, -12.0), (30.0, 15.0)))),
        **dict(zip(defenders, ((8.0, 3.0), (16.0, -2.0), (24.0, 10.0)))),
    }
    frame = Frame(
        None, timedelta(), [], attack, None, 1,
        {player: PlayerData(Point(*xy)) for player, xy in positions.items()},
        {}, None,
    )
    return frame, carrier, candidates, defenders


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("quickstart.svg"))
    args = parser.parse_args()
    frame, carrier, candidates, defenders = synthetic_frame()
    state = option_state_from_kloppy(
        frame,
        carrier=carrier,
        candidates=candidates,
        defenders=defenders,
        coordinate_context=MetricCoordinateContext(
            verified=True, units="metres", origin="centre", y_axis="up",
            attacking_sign=1,
        ),
    )
    m0_model, m1_model = demonstration_models()
    m0_network = evaluate_options(state, model=m0_model)
    m1_network = evaluate_options(state, model=m1_model)
    comparison = compare_options(m0_network, m1_network)
    dataframe = m1_network.to_pandas()
    import matplotlib.pyplot as plt
    figure, axes = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)
    plot_option_network(state, m0_network, pitch_length=105, pitch_width=68,
                        ax=axes[0], title="Synthetic M0")
    plot_option_network(state, m1_network, pitch_length=105, pitch_width=68,
                        ax=axes[1], title="Synthetic M1")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.output, format="svg", metadata={"Date": None})
    print(dataframe.to_string(index=False))
    print(f"m0_effective_options={m0_network.effective_option_count:.3f}")
    print(f"m1_effective_options={m1_network.effective_option_count:.3f}")
    print(f"top_set_changed={bool(comparison['top_set_changed'])}")
    print(f"saved={args.output}")


if __name__ == "__main__":
    main()
