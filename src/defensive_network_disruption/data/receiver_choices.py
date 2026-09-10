"""Production construction of Session 3 receiver choice sets."""

from __future__ import annotations

import csv
import json
import math
from bisect import bisect_left
from dataclasses import dataclass
from pathlib import Path

from .skillcorner_session2 import DEVELOPMENT_MATCHES

MAX_AGE_US = 100_000


@dataclass(frozen=True)
class ChoiceSet:
    match_id: str
    event_id: str
    candidate_ids: tuple[str, ...]
    candidate_xy: tuple[tuple[float, float], ...]
    defender_xy: tuple[tuple[float, float], ...]
    carrier_xy: tuple[float, float]
    target_index: int | None
    target_outside: bool


def clock_microseconds(value: str) -> int:
    parts = value.split(":")
    if len(parts) not in (2, 3):
        raise ValueError("unsupported clock format")
    hours = int(parts[0]) if len(parts) == 3 else 0
    minutes = int(parts[-2])
    seconds_text = parts[-1]
    seconds, dot, fraction = seconds_text.partition(".")
    micros = int((fraction + "000000")[:6]) if dot else 0
    return ((hours * 60 + minutes) * 60 + int(seconds)) * 1_000_000 + micros


def active_in_period(player: dict, period: int, frame: int) -> bool:
    intervals = (player.get("playing_time") or {}).get("by_period") or []
    wanted = f"period_{period}"
    matches = [item for item in intervals if item.get("name") == wanted]
    if len(matches) != 1:
        return False
    start, end = matches[0].get("start_frame"), matches[0].get("end_frame")
    return start is not None and end is not None and int(start) <= frame <= int(end)


def attack_sign(home_team_id: str, carrier_team_id: str, home_side: str) -> int:
    if home_side not in {"left_to_right", "right_to_left"}:
        raise ValueError("unknown attacking direction")
    home_sign = 1 if home_side == "left_to_right" else -1
    return home_sign if carrier_team_id == home_team_id else -home_sign


def attacking_xy(x: float, y: float, sign: int) -> tuple[float, float]:
    if sign not in {-1, 1} or not math.isfinite(float(x)) or not math.isfinite(float(y)):
        raise ValueError("finite coordinates and a verified direction are required")
    return sign * float(x), float(y)


def _tracked_positions(frame: dict) -> dict[str, tuple[float, float]]:
    positions = {}
    for item in frame.get("player_data") or []:
        player_id = str(item.get("player_id", ""))
        x, y = item.get("x"), item.get("y")
        if not player_id or x is None or y is None:
            continue
        if not math.isfinite(float(x)) or not math.isfinite(float(y)):
            continue
        if player_id in positions:
            raise ValueError("duplicate tracked identity")
        positions[player_id] = (float(x), float(y))
    return positions


def select_decision_frame(period_frames, event_time_us: int):
    """Select the latest strictly earlier frame within the frozen 100 ms tolerance."""
    times = [item[0] for item in period_frames]
    position = bisect_left(times, event_time_us) - 1
    if position < 0:
        return None
    selected = period_frames[position]
    age = event_time_us - selected[0]
    return selected if 0 < age <= MAX_AGE_US else None


def eligible_candidates(roster, positions, carrier, carrier_team, period, frame_id):
    """Return independent teammate candidates without label or vendor-option input."""
    return tuple(sorted(
        pid for pid, player in roster.items()
        if pid != carrier and str(player.get("team_id")) == carrier_team
        and pid in positions and active_in_period(player, period, frame_id)
    ))


def prepare_match(match_id: str, data_root: Path) -> tuple[list[ChoiceSet], dict]:
    """Build model-independent choices and a mutually exclusive exclusion audit."""
    if match_id not in DEVELOPMENT_MATCHES:
        raise PermissionError("match outside development allowlist")
    directory = data_root / "data/matches" / match_id
    metadata = json.loads((directory / f"{match_id}_match.json").read_text())
    roster_items = metadata.get("players") or []
    roster = {str(item["id"]): item for item in roster_items}
    if len(roster) != len(roster_items):
        raise ValueError("duplicate roster identity")
    home_id = str(metadata["home_team"]["id"])
    sides = metadata.get("home_team_side") or []
    if len(sides) != 2:
        raise ValueError("two period directions required")

    with (directory / f"{match_id}_dynamic_events.csv").open(newline="", encoding="utf-8-sig") as handle:
        all_events = list(csv.DictReader(handle))
    event_ids = [row.get("event_id") for row in all_events if row.get("event_id")]
    duplicate_event_ids = len(event_ids) - len(set(event_ids))
    attempts = [row for row in all_events if row.get("event_type") == "player_possession" and row.get("pass_outcome")]

    frames_by_period: dict[int, list[tuple[int, int, dict]]] = {1: [], 2: []}
    with (directory / f"{match_id}_tracking_extrapolated.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            frame = json.loads(line)
            period, timestamp = frame.get("period"), frame.get("timestamp")
            if period in frames_by_period and timestamp is not None:
                frames_by_period[period].append((clock_microseconds(timestamp), int(frame["frame"]), frame))
    for period_frames in frames_by_period.values():
        if any(a[0] >= b[0] for a, b in zip(period_frames, period_frames[1:])):
            raise ValueError("tracking timestamps must be strictly increasing within period")
    choices = []
    exclusions = {name: 0 for name in (
        "missing_or_unusable_target", "invalid_event_or_transition", "invalid_decision_frame",
        "invalid_carrier", "empty_candidate_set", "empty_defender_set_or_geometry",
    )}
    qc = {"raw_pass_attempts": len(attempts), "duplicate_event_ids": duplicate_event_ids,
          "target_outside": 0, "target_outside_reasons": {}, "degenerate_segments": 0}
    for event in attempts:
        target = str(event.get("player_targeted_id") or "")
        carrier = str(event.get("player_id") or event.get("player_in_possession_id") or "")
        if not target or target not in roster or target == carrier:
            exclusions["missing_or_unusable_target"] += 1
            continue
        try:
            period = int(event["period"])
            event_time = clock_microseconds(event["time_end"])
        except (KeyError, TypeError, ValueError):
            exclusions["invalid_event_or_transition"] += 1
            continue
        if period not in (1, 2) or duplicate_event_ids:
            exclusions["invalid_event_or_transition"] += 1
            continue
        selected_frame = select_decision_frame(frames_by_period[period], event_time)
        if selected_frame is None:
            exclusions["invalid_decision_frame"] += 1
            continue
        _, frame_id, frame = selected_frame
        carrier_meta = roster.get(carrier)
        positions = _tracked_positions(frame)
        if carrier_meta is None or carrier not in positions or not active_in_period(carrier_meta, period, frame_id):
            exclusions["invalid_carrier"] += 1
            continue
        carrier_team = str(carrier_meta.get("team_id"))
        try:
            sign = attack_sign(home_id, carrier_team, sides[period - 1])
        except ValueError:
            exclusions["invalid_carrier"] += 1
            continue
        transformed = {pid: attacking_xy(*xy, sign) for pid, xy in positions.items()}
        candidates = eligible_candidates(roster, transformed, carrier, carrier_team, period, frame_id)
        if not candidates:
            exclusions["empty_candidate_set"] += 1
            continue
        defenders = sorted(
            pid for pid, player in roster.items()
            if str(player.get("team_id")) != carrier_team
            and pid in transformed and active_in_period(player, period, frame_id)
        )
        if not defenders:
            exclusions["empty_defender_set_or_geometry"] += 1
            continue
        target_index = candidates.index(target) if target in candidates else None
        target_outside = target_index is None
        qc["target_outside"] += int(target_outside)
        if target_outside:
            target_meta = roster[target]
            if str(target_meta.get("team_id")) != carrier_team:
                reason = "target_not_same_team"
            elif target == carrier:
                reason = "target_is_carrier"
            elif target not in transformed:
                reason = "target_missing_current_tracking"
            elif not active_in_period(target_meta, period, frame_id):
                reason = "target_outside_verified_active_interval"
            else:
                raise RuntimeError("target absent from candidates without a frozen structural reason")
            qc["target_outside_reasons"][reason] = qc["target_outside_reasons"].get(reason, 0) + 1
        choices.append(ChoiceSet(
            match_id=match_id, event_id=str(event["event_id"]), candidate_ids=tuple(candidates),
            candidate_xy=tuple(transformed[pid] for pid in candidates),
            defender_xy=tuple(transformed[pid] for pid in defenders), carrier_xy=transformed[carrier],
            target_index=target_index, target_outside=target_outside,
        ))
    qc["exclusions"] = exclusions
    qc["evaluation_eligible"] = len(choices)
    qc["fit_eligible"] = sum(choice.target_index is not None for choice in choices)
    return choices, qc
