"""Frozen Session 6 population adapter and strict input contract."""

from __future__ import annotations

import csv
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from .identity_compatibility import (
    ProjectedMatch,
    _tracked_positions,
    canonical_lines,
    frozen_id,
    id_form,
    project_event,
    project_metadata,
    project_tracking,
    select_carrier,
)
from .receiver_choices import (
    ChoiceSet,
    active_in_period,
    attack_sign,
    attacking_xy,
    clock_microseconds,
    eligible_candidates,
    select_decision_frame,
)
from .session6_source import safe_destination


class Session6ContractError(RuntimeError):
    """An unsupported match-level input contract condition."""


IDENTITY_FIELDS = ("event_id", "player_id", "player_in_possession_id", "player_targeted_id")
ALLOWED_DIRECTIONS = {"left_to_right", "right_to_left"}
ALLOWED_PERIOD_NAMES = {"period_1", "period_2"}


def load_projected_match_session6(
    data_root: Path,
    match_id: str,
    *,
    allowlist: frozenset[str],
) -> ProjectedMatch:
    """Project the exact frozen fields from a preverified local product set."""
    metadata_path = safe_destination(data_root, match_id, "metadata", allowlist)
    events_path = safe_destination(data_root, match_id, "events", allowlist)
    tracking_path = safe_destination(data_root, match_id, "tracking", allowlist)
    for path in (metadata_path, events_path, tracking_path):
        if path.is_symlink() or not path.is_file():
            raise PermissionError("authorized local product is missing or unsafe")
    metadata = project_metadata(json.loads(metadata_path.read_text(encoding="utf-8")))
    events = []
    with events_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        try:
            header = tuple(next(reader))
        except StopIteration as exc:
            raise Session6ContractError("event product is empty") from exc
        for row in reader:
            events.append(project_event(header, tuple(row)))
    frames = []
    with tracking_path.open(encoding="utf-8") as handle:
        for line in handle:
            frames.append(project_tracking(json.loads(line)))
    return ProjectedMatch(metadata, tuple(events), tuple(frames))


def _required_id(value: Any, label: str) -> str:
    if id_form(value) != "ordinary":
        raise Session6ContractError(f"invalid required {label} identity form")
    return frozen_id(value)


def _optional_id(value: Any, label: str) -> str:
    form = id_form(value)
    if form in {"null", "empty"}:
        return ""
    if form != "ordinary":
        raise Session6ContractError(f"invalid optional {label} identity form")
    return frozen_id(value)


def validate_input_contract(projected: ProjectedMatch) -> dict[str, Any]:
    """Validate every strict Session 6 input invariant before population work."""
    metadata = projected.metadata
    try:
        home_id = _required_id(metadata["home_team"]["id"], "home team")
        away_id = _required_id(metadata["away_team"]["id"], "away team")
    except (KeyError, TypeError) as exc:
        raise Session6ContractError("declared match teams are missing") from exc
    if home_id == away_id:
        raise Session6ContractError("declared team identities are duplicated")
    declared = {home_id, away_id}

    sides = metadata.get("home_team_side")
    if not isinstance(sides, list) or len(sides) != 2 or any(side not in ALLOWED_DIRECTIONS for side in sides):
        raise Session6ContractError("two verified period directions are required")

    roster_items = metadata.get("players")
    if not isinstance(roster_items, list):
        raise Session6ContractError("roster must be a list")
    roster_ids: list[str] = []
    for player in roster_items:
        if not isinstance(player, dict):
            raise Session6ContractError("roster entries must be objects")
        player_id = _required_id(player.get("id"), "roster player")
        team_id = _required_id(player.get("team_id"), "roster team")
        if team_id not in declared:
            raise Session6ContractError("roster team does not resolve to a declared team")
        roster_ids.append(player_id)
        playing = player.get("playing_time")
        if not isinstance(playing, dict) or not isinstance(playing.get("by_period"), list):
            raise Session6ContractError("playing interval structure is malformed")
        names: list[str] = []
        for interval in playing["by_period"]:
            if not isinstance(interval, dict):
                raise Session6ContractError("playing interval must be an object")
            name = interval.get("name")
            if name not in ALLOWED_PERIOD_NAMES or name in names:
                raise Session6ContractError("playing interval period is unknown or duplicated")
            names.append(name)
            start, end = interval.get("start_frame"), interval.get("end_frame")
            if isinstance(start, bool) or isinstance(end, bool):
                raise Session6ContractError("playing interval frames must be integers")
            try:
                start_int, end_int = int(start), int(end)
            except (TypeError, ValueError) as exc:
                raise Session6ContractError("playing interval frames are malformed") from exc
            if str(start_int) != str(start) or str(end_int) != str(end) or start_int > end_int:
                raise Session6ContractError("playing interval frames are malformed")
    if len(roster_ids) != len(set(roster_ids)):
        raise Session6ContractError("duplicate roster identity")
    roster_set = set(roster_ids)

    duplicate_event_ids = 0
    event_ids: list[str] = []
    event_identity_forms = Counter()
    optional_reference_blanks = 0
    carrier_fallback = 0
    carrier_conflicts = 0
    pass_attempts = 0
    for event in projected.events:
        event_id = _required_id(event.get("event_id"), "event")
        event_ids.append(event_id)
        for field in IDENTITY_FIELDS:
            event_identity_forms[id_form(event.get(field))] += 1
        for field in ("player_id", "player_in_possession_id", "player_targeted_id"):
            optional_reference_blanks += int(_optional_id(event.get(field), field) == "")
        if event.get("event_type") == "player_possession" and event.get("pass_outcome"):
            pass_attempts += 1
            _, fallback, conflict = select_carrier(event)
            carrier_fallback += int(fallback)
            carrier_conflicts += int(conflict)
    duplicate_event_ids = len(event_ids) - len(set(event_ids))
    if carrier_conflicts:
        raise Session6ContractError("conflicting populated carrier references on pass attempts")

    tracking_records = 0
    ignored_non_playing_period_records = 0
    tracking_player_records = 0
    tracking_coordinate_missing = 0
    tracking_duplicate_occurrences = 0
    tracking_identity_forms = Counter()
    last_timestamp: dict[int, int] = {}
    for frame in projected.frames:
        tracking_records += 1
        period = frame.get("period")
        if period is None:
            ignored_non_playing_period_records += 1
            continue
        frame_id = frame.get("frame")
        timestamp = frame.get("timestamp")
        if period not in (1, 2) or isinstance(frame_id, bool):
            raise Session6ContractError("tracking period or frame representation is unsupported")
        try:
            int_frame = int(frame_id)
        except (TypeError, ValueError) as exc:
            raise Session6ContractError("tracking frame is malformed") from exc
        if str(int_frame) != str(frame_id):
            raise Session6ContractError("tracking frame representation is unsupported")
        try:
            timestamp_us = clock_microseconds(timestamp)
        except (AttributeError, TypeError, ValueError) as exc:
            raise Session6ContractError("tracking clock representation is unsupported") from exc
        if period in last_timestamp and timestamp_us <= last_timestamp[period]:
            raise Session6ContractError("tracking clocks are not strictly increasing within period")
        last_timestamp[period] = timestamp_us
        seen: set[str] = set()
        player_data = frame.get("player_data")
        if not isinstance(player_data, list):
            raise Session6ContractError("tracking player data must be a list")
        for player in player_data:
            tracking_player_records += 1
            if not isinstance(player, dict):
                raise Session6ContractError("tracking player entry must be an object")
            tracking_identity_forms[id_form(player.get("player_id"))] += 1
            player_id = _required_id(player.get("player_id"), "tracking player")
            if player_id in seen:
                tracking_duplicate_occurrences += 1
            seen.add(player_id)
            if player_id not in roster_set:
                raise Session6ContractError("tracking identity does not resolve to roster")
            x, y = player.get("x"), player.get("y")
            if x is None or y is None:
                tracking_coordinate_missing += 1
                continue
            try:
                float(x), float(y)
            except (TypeError, ValueError) as exc:
                raise Session6ContractError("tracking coordinate representation is unsupported") from exc
        if tracking_duplicate_occurrences:
            raise Session6ContractError("duplicate tracking identity within frame")

    return {
        "declared_team_count": 2,
        "roster_player_count": len(roster_ids),
        "pass_attempt_count": pass_attempts,
        "duplicate_nonempty_event_ids": duplicate_event_ids,
        "optional_event_reference_blanks": optional_reference_blanks,
        "carrier_fallback_count": carrier_fallback,
        "carrier_conflict_count": carrier_conflicts,
        "tracking_records": tracking_records,
        "ignored_non_playing_period_records": ignored_non_playing_period_records,
        "tracking_player_records": tracking_player_records,
        "tracking_coordinate_missing": tracking_coordinate_missing,
        "event_identity_form_counts": dict(sorted(event_identity_forms.items())),
        "tracking_identity_form_counts": dict(sorted(tracking_identity_forms.items())),
    }


def prepare_match_session6(
    match_id: str,
    projected: ProjectedMatch,
    *,
    allowlist: Iterable[str],
) -> tuple[list[ChoiceSet], dict[str, Any], dict[str, Any]]:
    """Apply the frozen population loop after strict contract validation."""
    allowed = frozenset(str(item) for item in allowlist)
    if str(match_id) not in allowed:
        raise PermissionError("match outside the explicit Session 6 partition allowlist")
    contract = validate_input_contract(projected)
    metadata, all_events, all_frames = projected.metadata, projected.events, projected.frames
    roster_items = metadata["players"]
    roster = {str(item["id"]): item for item in roster_items}
    home_id = str(metadata["home_team"]["id"])
    sides = metadata["home_team_side"]
    event_ids = [row.get("event_id") for row in all_events if row.get("event_id")]
    duplicate_event_ids = len(event_ids) - len(set(event_ids))
    attempts = [row for row in all_events if row.get("event_type") == "player_possession" and row.get("pass_outcome")]

    frames_by_period: dict[int, list[tuple[int, int, dict[str, Any]]]] = {1: [], 2: []}
    for frame in all_frames:
        if frame["period"] not in frames_by_period or frame["timestamp"] is None:
            continue
        frames_by_period[frame["period"]].append(
            (clock_microseconds(frame["timestamp"]), int(frame["frame"]), frame)
        )

    choices: list[ChoiceSet] = []
    exclusions = {name: 0 for name in (
        "missing_or_unusable_target", "invalid_event_or_transition",
        "invalid_decision_frame", "invalid_carrier", "empty_candidate_set",
        "empty_defender_set_or_geometry",
    )}
    target_qc = {name: 0 for name in (
        "missing", "self", "unresolved", "other_team", "inactive", "untracked",
        "valid_current_state", "not_assessed_invalid_state",
    )}
    carrier_qc = {name: 0 for name in (
        "both_missing", "fallback_used", "selected_absent_roster",
        "selected_untracked", "selected_inactive", "nonfinite_coordinate",
    )}
    qc: dict[str, Any] = {
        "raw_pass_attempts": len(attempts),
        "duplicate_event_ids": duplicate_event_ids,
        "target_outside": 0,
        "target_outside_reasons": {},
        "target_qc": target_qc,
        "carrier_qc": carrier_qc,
        "candidate_counts": [],
        "defender_counts": [],
    }
    for event in attempts:
        target = str(event.get("player_targeted_id") or "")
        carrier, fallback_used, _ = select_carrier(event)
        carrier_qc["both_missing"] += int(not carrier)
        carrier_qc["fallback_used"] += int(fallback_used)
        carrier_qc["selected_absent_roster"] += int(bool(carrier) and carrier not in roster)
        if not target:
            target_qc["missing"] += 1
        elif target == carrier:
            target_qc["self"] += 1
        elif target not in roster:
            target_qc["unresolved"] += 1
        if not target or target not in roster or target == carrier:
            exclusions["missing_or_unusable_target"] += 1
            continue
        try:
            period = int(event["period"])
            event_time = clock_microseconds(event["time_end"])
        except (KeyError, AttributeError, TypeError, ValueError):
            exclusions["invalid_event_or_transition"] += 1
            continue
        if period not in (1, 2) or duplicate_event_ids:
            exclusions["invalid_event_or_transition"] += 1
            continue
        selected = select_decision_frame(frames_by_period[period], event_time)
        if selected is None:
            exclusions["invalid_decision_frame"] += 1
            continue
        _, frame_id, frame = selected
        carrier_meta = roster.get(carrier)
        positions = _tracked_positions(frame)
        if carrier_meta is None or carrier not in positions or not active_in_period(carrier_meta, period, frame_id):
            carrier_qc["selected_untracked"] += int(carrier_meta is not None and carrier not in positions)
            carrier_qc["selected_inactive"] += int(
                carrier_meta is not None and carrier in positions
                and not active_in_period(carrier_meta, period, frame_id)
            )
            target_qc["not_assessed_invalid_state"] += 1
            exclusions["invalid_carrier"] += 1
            continue
        carrier_team = str(carrier_meta.get("team_id"))
        try:
            sign = attack_sign(home_id, carrier_team, sides[period - 1])
            transformed = {pid: attacking_xy(*xy, sign) for pid, xy in positions.items()}
        except (TypeError, ValueError):
            carrier_qc["nonfinite_coordinate"] += 1
            target_qc["not_assessed_invalid_state"] += 1
            exclusions["invalid_carrier"] += 1
            continue
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
        target_meta = roster[target]
        if str(target_meta.get("team_id")) != carrier_team:
            target_qc["other_team"] += 1
        elif not active_in_period(target_meta, period, frame_id):
            target_qc["inactive"] += 1
        elif target not in transformed:
            target_qc["untracked"] += 1
        else:
            target_qc["valid_current_state"] += 1
        target_index = candidates.index(target) if target in candidates else None
        target_outside = target_index is None
        qc["target_outside"] += int(target_outside)
        if target_outside:
            if str(target_meta.get("team_id")) != carrier_team:
                reason = "target_not_same_team"
            elif target not in transformed:
                reason = "target_missing_current_tracking"
            elif not active_in_period(target_meta, period, frame_id):
                reason = "target_outside_verified_active_interval"
            else:
                raise RuntimeError("target absent from candidates without frozen reason")
            qc["target_outside_reasons"][reason] = qc["target_outside_reasons"].get(reason, 0) + 1
        qc["candidate_counts"].append(len(candidates))
        qc["defender_counts"].append(len(defenders))
        choices.append(ChoiceSet(
            match_id=str(match_id), event_id=str(event["event_id"]),
            candidate_ids=tuple(candidates),
            candidate_xy=tuple(transformed[pid] for pid in candidates),
            defender_xy=tuple(transformed[pid] for pid in defenders),
            carrier_xy=transformed[carrier], target_index=target_index,
            target_outside=target_outside,
        ))
    qc["exclusions"] = exclusions
    qc["evaluation_eligible"] = len(choices)
    qc["fit_eligible"] = sum(choice.target_index is not None for choice in choices)
    return choices, qc, contract


def rendered_population(choices: Iterable[ChoiceSet]) -> bytes:
    lines = canonical_lines(choices)
    return (("\n".join(lines) + "\n") if lines else "").encode()
