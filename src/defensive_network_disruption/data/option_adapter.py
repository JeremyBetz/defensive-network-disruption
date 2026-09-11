"""Optional Kloppy adapter; eligibility and coordinate context are explicit."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from defensive_network_disruption.networks.options import OptionState, identity


@dataclass(frozen=True)
class MetricCoordinateContext:
    """Caller-verified centred metric coordinates with physical positive-up y.

    No normalization or pitch rescaling is performed. This describes the actual
    supplied frame, not a request to reinterpret normalized coordinates as metres.
    """
    verified: bool
    units: str
    origin: str
    y_axis: str
    attacking_sign: int


def option_state_from_kloppy(
    frame,
    *,
    carrier,
    candidates: Iterable,
    defenders: Iterable,
    coordinate_context: MetricCoordinateContext,
) -> OptionState:
    """Project an explicitly selected Kloppy frame into an ``OptionState``.

    This function validates the supplied selection. It does not decide which
    players are active or eligible and never guesses the coordinate convention.
    """
    from kloppy.domain import Frame
    if not isinstance(frame, Frame):
        raise TypeError("frame must be a kloppy.domain.Frame")
    c = coordinate_context
    if not isinstance(c, MetricCoordinateContext) or c.verified is not True or (
        c.units, c.origin, c.y_axis) != ("metres", "centre", "up") or type(c.attacking_sign) is not int or c.attacking_sign not in (-1, 1):
        raise ValueError(
            "coordinate_context must verify centred metres, positive-up y, "
            "and attacking_sign +1 or -1"
        )
    candidates, defenders = tuple(candidates), tuple(defenders)
    selected = (carrier, *candidates, *defenders)
    ids = [identity(p.player_id) for p in selected]
    if len(ids) != len(set(ids)) or not candidates or not defenders:
        raise ValueError("disjoint nonempty selections required")
    if carrier.team is None or any(p.team is None for p in selected):
        raise ValueError("explicit team identities required")
    if any(p.team != carrier.team for p in candidates) or any(p.team == carrier.team for p in defenders):
        raise ValueError("selection team mismatch")
    if len({p.team.team_id for p in defenders}) != 1:
        raise ValueError("one opposing team required")

    def xy(player):
        if player not in frame.players_data or frame.players_data[player].coordinates is None:
            raise ValueError("selected player not currently tracked")
        p = frame.players_data[player].coordinates
        return c.attacking_sign * p.x, p.y
    return OptionState(xy(carrier), tuple(p.player_id for p in candidates),
                       tuple(xy(p) for p in candidates), tuple(xy(p) for p in defenders),
                       carrier.player_id)
