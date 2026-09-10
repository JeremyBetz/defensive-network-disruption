"""Structural validation helpers with no scoring or ranking behavior."""

from __future__ import annotations

import math


def resolve_unique_target_link(event_rows: list[dict], link: str) -> dict | None:
    """Resolve one target link, rejecting duplicate event identifiers."""
    matches = [row for row in event_rows if row.get("event_id") == link]
    if not matches:
        return None
    if len(matches) != 1:
        raise ValueError("target link is ambiguous")
    return matches[0]


def independent_candidate_ids(
    roster: dict[str, dict],
    tracked: dict[str, dict],
    *,
    carrier_id: str,
    carrier_team_id: str,
    active_ids: set[str],
) -> tuple[str, ...]:
    """Construct data-valid teammates without target or vendor-option inputs."""
    candidates = []
    for player_id, metadata in roster.items():
        coordinate = tracked.get(player_id)
        if player_id == carrier_id or str(metadata.get("team_id")) != carrier_team_id:
            continue
        if player_id not in active_ids or coordinate is None:
            continue
        x, y = coordinate.get("x"), coordinate.get("y")
        if x is None or y is None or not math.isfinite(float(x)) or not math.isfinite(float(y)):
            continue
        candidates.append(player_id)
    return tuple(sorted(candidates))
