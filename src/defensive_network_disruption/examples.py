"""Small deterministic synthetic fixtures for public examples and tests."""
from __future__ import annotations

import math

from defensive_network_disruption.networks.options import FrozenOptionModel, OptionState
from defensive_network_disruption.validation.ranking_features import M0_NAMES, M1_NAMES


def synthetic_option_state() -> OptionState:
    """Return the frozen, clearly synthetic Session 9 state."""
    return OptionState(
        (0.0, 0.0),
        ("A", "B", "C", "D"),
        ((12.0, 8.0), (22.0, 0.0), (10.0, -12.0), (30.0, 15.0)),
        ((8.0, 3.0), (16.0, -2.0), (24.0, 10.0)),
        carrier_id="carrier",
    )


def synthetic_option_sequence(frames: int = 80) -> tuple[OptionState, ...]:
    """Return the frozen smooth synthetic sequence; it is not a simulator."""
    if type(frames) is not int or frames < 2:
        raise ValueError("frames must be an integer of at least two")
    states = []
    for index in range(frames):
        t = index / (frames - 1)
        candidates = (
            (12.0 + 2.0 * t, 8.0),
            (22.0, 2.0 * math.sin(2.0 * math.pi * t)),
            (10.0 + 3.0 * t, -12.0 + 2.0 * t),
            (30.0 - 2.0 * t, 15.0 - 3.0 * t),
        )
        defenders = (
            (8.0 + 4.0 * t, 3.0 - 4.0 * t),
            (16.0 - 2.0 * t, -2.0 - 4.0 * math.sin(math.pi * t)),
            (24.0 - 5.0 * t, 10.0 - 3.0 * t),
        )
        states.append(OptionState(
            (0.0, 0.0), ("A", "B", "C", "D"), candidates, defenders,
            carrier_id="carrier",
        ))
    return tuple(states)


def demonstration_models() -> tuple[FrozenOptionModel, FrozenOptionModel]:
    """Explicit illustrative models for quickstarts, never empirical authority."""
    m0 = FrozenOptionModel("m0", M0_NAMES, (0.0,) * 3, (20.0, 20.0, 20.0),
                           (-1.0, 0.35, 0.0))
    m1 = FrozenOptionModel("m1", M1_NAMES, (0.0,) * 5,
                           (20.0, 20.0, 20.0, 10.0, 10.0),
                           (-1.0, 0.35, 0.0, 0.6, 1.2))
    return m0, m1
