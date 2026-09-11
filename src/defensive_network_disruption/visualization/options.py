"""Optional mplsoccer presentation for local option networks."""
from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from defensive_network_disruption.networks.options import (
    FrozenOptionModel,
    OptionNetwork,
    OptionState,
    evaluate_options,
)

PITCH_COLOR = "#f4f7f2"
LINE_COLOR = "#bcc8c1"
TEXT_COLOR = "#13293d"
EDGE_COLOR = "#157f9b"
DEFENDER_COLOR = "#c65a3a"
RECEIVER_COLOR = "#157f9b"


def _libraries():
    try:
        import matplotlib.pyplot as plt
        from mplsoccer import Pitch
    except ImportError as error:
        raise ImportError(
            "plotting requires the 'visualization' extra: "
            "pip install 'defensive-network-disruption[visualization]'"
        ) from error
    return plt, Pitch


def _dimensions(pitch_length: float, pitch_width: float) -> tuple[float, float]:
    values = float(pitch_length), float(pitch_width)
    if not all(math.isfinite(v) and v > 0 for v in values):
        raise ValueError("pitch_length and pitch_width must be finite and positive")
    return values


def _validate_alignment(state: OptionState, network: OptionNetwork) -> None:
    if not isinstance(state, OptionState) or not isinstance(network, OptionNetwork):
        raise TypeError("state must be an OptionState and network must be an OptionNetwork")
    if tuple(edge.receiver_id for edge in network.edges) != state.candidate_ids:
        raise ValueError("network edges must exactly match state candidate order")


def _pitch_xy(
    point: tuple[float, float], length: float, width: float,
) -> tuple[float, float]:
    x, y = point
    result = x + length / 2.0, y + width / 2.0
    if not (0.0 <= result[0] <= length and 0.0 <= result[1] <= width):
        raise ValueError("state coordinate lies outside the supplied pitch")
    return result


def plot_option_network(
    state: OptionState,
    network: OptionNetwork,
    *,
    pitch_length: float,
    pitch_width: float,
    ax: Any = None,
    title: str | None = None,
) -> tuple[Any, Any]:
    """Plot one aligned network on an explicit metric pitch.

    Install the ``visualization`` extra before calling. The returned pair is the
    Matplotlib figure and axes used for the drawing.
    """
    _validate_alignment(state, network)
    length, width = _dimensions(pitch_length, pitch_width)
    plt, Pitch = _libraries()
    pitch = Pitch(
        pitch_type="custom", pitch_length=length, pitch_width=width,
        pitch_color=PITCH_COLOR, line_color=LINE_COLOR, linewidth=1.0,
        goal_type="line", corner_arcs=True,
    )
    if ax is None:
        figure, ax = pitch.draw(figsize=(8, 5), tight_layout=False)
    else:
        figure = ax.figure
        pitch.draw(ax=ax)
    carrier = _pitch_xy(state.carrier_xy, length, width)
    receivers = tuple(_pitch_xy(point, length, width) for point in state.candidate_xy)
    defenders = tuple(_pitch_xy(point, length, width) for point in state.defender_xy)
    for edge, receiver in zip(network.edges, receivers):
        width_value = 0.8 + 8.0 * edge.option_share
        alpha = 0.28 + 0.68 * edge.option_share
        ax.plot((carrier[0], receiver[0]), (carrier[1], receiver[1]),
                color=EDGE_COLOR, linewidth=width_value, alpha=alpha,
                solid_capstyle="round", zorder=2)
        ax.scatter(*receiver, s=85, color=RECEIVER_COLOR, edgecolor="white",
                   linewidth=0.8, zorder=4)
        label = f"{edge.receiver_id}  {edge.option_share:.0%}"
        ax.annotate(label, receiver, xytext=(6, 6), textcoords="offset points",
                    fontsize=9, color=TEXT_COLOR, weight="semibold", zorder=5)
    if defenders:
        ax.scatter([p[0] for p in defenders], [p[1] for p in defenders], s=80,
                   marker="s", color=DEFENDER_COLOR, edgecolor="white",
                   linewidth=0.8, zorder=4)
    ax.scatter(*carrier, s=105, color=TEXT_COLOR, edgecolor="white",
               linewidth=0.8, zorder=5)
    ax.annotate("Carrier", carrier, xytext=(-8, -17), textcoords="offset points",
                ha="center", fontsize=9, color=TEXT_COLOR, weight="semibold")
    top = ", ".join(network.top_options)
    ax.text(0.02, 0.04,
            f"Top: {top} · top-two {network.top_two_share:.0%} · "
            f"effective options {network.effective_option_count:.2f}",
            transform=ax.transAxes, fontsize=9, color=TEXT_COLOR,
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.82,
                  "boxstyle": "round,pad=0.35"}, zorder=6)
    if title:
        ax.set_title(title, fontsize=13, color=TEXT_COLOR, weight="bold", pad=8)
    return figure, ax


def animate_option_network_comparison(
    states: Sequence[OptionState],
    *,
    m0_model: FrozenOptionModel,
    m1_model: FrozenOptionModel,
    pitch_length: float,
    pitch_width: float,
    fps: int = 10,
) -> Any:
    """Return a Matplotlib animation comparing explicit M0/M1 models.

    Install the ``visualization`` extra. This function neither saves the
    animation nor loads or fits a model.
    """
    states = tuple(states)
    if not states or any(not isinstance(state, OptionState) for state in states):
        raise ValueError("states must be a nonempty sequence of OptionState objects")
    if type(fps) is not int or fps <= 0:
        raise ValueError("fps must be a positive integer")
    length, width = _dimensions(pitch_length, pitch_width)
    plt, _ = _libraries()
    from matplotlib.animation import FuncAnimation

    figure, axes = plt.subplots(1, 2, figsize=(9.6, 5.4), constrained_layout=True)
    figure.patch.set_facecolor("#eef2f6")

    def draw(index):
        state = states[index]
        for axis in axes:
            axis.clear()
        m0 = evaluate_options(state, model=m0_model)
        m1 = evaluate_options(state, model=m1_model)
        plot_option_network(state, m0, pitch_length=length, pitch_width=width,
                            ax=axes[0], title="M0 · attacking geometry")
        plot_option_network(state, m1, pitch_length=length, pitch_width=width,
                            ax=axes[1], title="M1 · defense-conditioned geometry")
        figure.suptitle(
            "SYNTHETIC local attacking-option network",
            fontsize=15, color=TEXT_COLOR, weight="bold",
        )
        figure.text(
            0.5, 0.012,
            "Widths show model-implied receiver-option shares — not accessibility or pass probability",
            ha="center", fontsize=9, color=TEXT_COLOR,
        )
        return tuple(artist for axis in axes for artist in axis.get_children())

    animation = FuncAnimation(
        figure, draw, frames=len(states), interval=1000 / fps,
        blit=False, repeat=True,
    )
    animation._option_network_states = states
    animation._option_network_fps = fps
    return animation
