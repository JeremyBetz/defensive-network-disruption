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
    _, model = demonstration_models()
    network = evaluate_options(state, model=model)
    dataframe = network.to_pandas()
    figure, _ = plot_option_network(
        state, network, pitch_length=105, pitch_width=68,
        title="Synthetic M1 option network",
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.output, format="svg", metadata={"Date": None})
    print(dataframe.to_string(index=False))
    print(f"effective_option_count={network.effective_option_count:.3f}")
    print(f"saved={args.output}")


if __name__ == "__main__":
    main()
