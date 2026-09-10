"""Restricted identity reader used only for the Session 6a compatibility audit."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .receiver_choices import (
    ChoiceSet,
    active_in_period,
    attack_sign,
    attacking_xy,
    clock_microseconds,
    eligible_candidates,
    select_decision_frame,
)
from .skillcorner_session2 import DEVELOPMENT_MATCHES, safe_destination

METADATA_FIELDS = frozenset({"home_team", "away_team", "players", "home_team_side"})
EVENT_FIELDS = (
    "event_id", "event_type", "pass_outcome", "period", "time_end",
    "player_id", "player_in_possession_id", "player_targeted_id",
)
TRACKING_FIELDS = frozenset({"frame", "period", "timestamp", "player_data"})
PLAYER_FIELDS = frozenset({"player_id", "x", "y"})
PRODUCTS = ("metadata", "events", "tracking")


class CompatibilityBlocked(RuntimeError):
    """Raised when observed values require a new, non-frozen decision."""


@dataclass(frozen=True)
class ProjectedMatch:
    metadata: dict[str, Any]
    events: tuple[dict[str, Any], ...]
    frames: tuple[dict[str, Any], ...]


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def git_blob_sha1(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode()
    return hashlib.sha1(header + content).hexdigest()  # noqa: S324 - Git object identity


def id_form(value: Any) -> str:
    """Classify an ID without modifying it."""
    if value is None:
        return "null"
    if not isinstance(value, (str, int)) or isinstance(value, bool):
        return "malformed"
    text = str(value)
    if text == "":
        return "empty"
    if text.isspace():
        return "whitespace_only"
    if text != text.strip():
        return "padded"
    return "ordinary"


def frozen_id(value: Any) -> str:
    """Apply the existing production string coercion without trimming."""
    return str(value) if value is not None else ""


def select_carrier(event: dict[str, Any]) -> tuple[str, bool, bool]:
    """Return carrier, fallback use, and conflict under frozen precedence."""
    primary = event.get("player_id")
    fallback = event.get("player_in_possession_id")
    selected = primary or fallback or ""
    return str(selected), not bool(primary) and bool(fallback), bool(primary) and bool(fallback) and str(primary) != str(fallback)


def project_metadata(raw: dict[str, Any]) -> dict[str, Any]:
    """Project only the fields authorized by Phase 6a."""
    def team(value: Any) -> dict[str, Any]:
        value = value if isinstance(value, dict) else {}
        return {"id": value.get("id")}

    players = []
    for item in raw.get("players") or []:
        periods = []
        playing = item.get("playing_time") if isinstance(item, dict) else None
        for interval in ((playing or {}).get("by_period") or []):
            periods.append({
                "name": interval.get("name"),
                "start_frame": interval.get("start_frame"),
                "end_frame": interval.get("end_frame"),
            })
        players.append({
            "id": item.get("id"), "team_id": item.get("team_id"),
            "playing_time": {"by_period": periods},
        })
    return {
        "home_team": team(raw.get("home_team")),
        "away_team": team(raw.get("away_team")),
        "players": players,
        "home_team_side": list(raw.get("home_team_side") or []),
    }


def project_event(header: tuple[str, ...], row: tuple[str, ...]) -> dict[str, str | None]:
    positions = {name: index for index, name in enumerate(header)}
    missing = [name for name in EVENT_FIELDS if name not in positions]
    if missing:
        raise CompatibilityBlocked(f"authorized event fields missing: {missing}")
    return {name: row[positions[name]] if positions[name] < len(row) else None for name in EVENT_FIELDS}


def project_tracking(raw: dict[str, Any]) -> dict[str, Any]:
    players = []
    for item in raw.get("player_data") or []:
        players.append({name: item.get(name) for name in PLAYER_FIELDS})
    return {
        "frame": raw.get("frame"), "period": raw.get("period"),
        "timestamp": raw.get("timestamp"), "player_data": players,
    }


def safe_product(data_root: Path, match_id: str, product: str) -> Path:
    if match_id not in DEVELOPMENT_MATCHES:
        raise PermissionError("match outside Session 6a development allowlist")
    if product not in PRODUCTS:
        raise PermissionError("product outside Session 6a allowlist")
    path = safe_destination(data_root, match_id, product)
    if path.is_symlink() or not path.is_file():
        raise PermissionError("unsafe or missing authorized product")
    root = data_root.resolve()
    if not path.resolve().is_relative_to(root):
        raise PermissionError("authorized product escapes governed root")
    return path


def verify_products(data_root: Path, match_id: str, authority: dict[str, Any]) -> dict[str, Any]:
    """Verify product bytes before parsing and return non-public identities."""
    verified: dict[str, Any] = {}
    key_for = {"metadata": "match.json", "events": "dynamic_events.csv", "tracking": "tracking_extrapolated.jsonl"}
    for product in PRODUCTS:
        path = safe_product(data_root, match_id, product)
        content = path.read_bytes()
        expected = authority[key_for[product]]
        if product == "tracking":
            if len(content) != expected.get("lfs_declared_payload_size"):
                raise RuntimeError("tracking LFS payload size mismatch")
            if sha256_bytes(content) != expected.get("lfs_payload_sha256"):
                raise RuntimeError("tracking LFS payload hash mismatch")
            verified[product] = {
                "git_pointer_object_sha": expected.get("git_object_sha"),
                "lfs_payload_sha256": expected.get("lfs_payload_sha256"),
                "payload_size": len(content),
            }
        else:
            if len(content) != expected.get("git_object_size") or git_blob_sha1(content) != expected.get("git_object_sha"):
                raise RuntimeError(f"{product} Git object identity mismatch")
            verified[product] = {"git_object_sha": expected.get("git_object_sha"), "size": len(content)}
    return verified


def load_projected_match(data_root: Path, match_id: str) -> ProjectedMatch:
    """Load authorized products and immediately discard non-authorized fields."""
    metadata_path = safe_product(data_root, match_id, "metadata")
    metadata = project_metadata(json.loads(metadata_path.read_text(encoding="utf-8")))

    event_path = safe_product(data_root, match_id, "events")
    events: list[dict[str, Any]] = []
    with event_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        header = tuple(next(reader))
        for row in reader:
            events.append(project_event(header, tuple(row)))

    tracking_path = safe_product(data_root, match_id, "tracking")
    frames: list[dict[str, Any]] = []
    with tracking_path.open(encoding="utf-8") as handle:
        for line in handle:
            frames.append(project_tracking(json.loads(line)))
    return ProjectedMatch(metadata, tuple(events), tuple(frames))


def _identity_counts(values: Iterable[Any]) -> dict[str, int]:
    counts = Counter(id_form(value) for value in values)
    return {name: counts.get(name, 0) for name in ("null", "empty", "whitespace_only", "padded", "malformed")}


def _duplicate_count(values: Iterable[Any], *, nonempty_only: bool = False) -> int:
    converted = [frozen_id(value) for value in values]
    if nonempty_only:
        converted = [value for value in converted if value]
    counts = Counter(converted)
    return sum(count - 1 for count in counts.values() if count > 1)


def _tracked_positions(frame: dict[str, Any]) -> dict[str, tuple[float, float]]:
    positions: dict[str, tuple[float, float]] = {}
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


def restricted_prepare_match(match_id: str, projected: ProjectedMatch) -> tuple[list[ChoiceSet], dict[str, Any], dict[str, Any]]:
    """Replay frozen Session 3 behavior and collect identity-only aggregates."""
    if match_id not in DEVELOPMENT_MATCHES:
        raise PermissionError("match outside Session 6a development allowlist")
    metadata, all_events, all_frames = projected.metadata, projected.events, projected.frames
    roster_items = metadata.get("players") or []
    roster_ids = [str(item["id"]) for item in roster_items]
    if len(roster_ids) != len(set(roster_ids)):
        raise ValueError("duplicate roster identity")
    roster = {str(item["id"]): item for item in roster_items}
    home_raw = metadata["home_team"]["id"]
    away_raw = metadata["away_team"]["id"]
    home_id, away_id = str(home_raw), str(away_raw)
    sides = metadata.get("home_team_side") or []
    if len(sides) != 2:
        raise ValueError("two period directions required")

    event_ids = [row.get("event_id") for row in all_events if row.get("event_id")]
    duplicate_event_ids = len(event_ids) - len(set(event_ids))
    attempts = [row for row in all_events if row.get("event_type") == "player_possession" and row.get("pass_outcome")]

    audit: dict[str, Any] = {
        "identity_forms": {
            "declared_team": _identity_counts((home_raw, away_raw)),
            "roster_player": _identity_counts(item.get("id") for item in roster_items),
            "roster_team": _identity_counts(item.get("team_id") for item in roster_items),
            "event_id": _identity_counts(row.get("event_id") for row in all_events),
            "event_player": _identity_counts(
                row.get(name) for row in all_events
                for name in ("player_id", "player_in_possession_id", "player_targeted_id")
            ),
            "tracking_player": _identity_counts(
                item.get("player_id") for frame in all_frames for item in (frame.get("player_data") or [])
            ),
        },
        "duplicates": {
            "declared_team": _duplicate_count((home_raw, away_raw)),
            "roster": _duplicate_count(item.get("id") for item in roster_items),
            "event_nonempty": duplicate_event_ids,
            "tracking_occurrences": 0,
            "tracking_frames": 0,
        },
        "membership": {"roster_unknown_team": 0, "tracking_player_absent_roster": 0},
        "carrier": {
            "both_missing": 0, "fallback_used": 0, "conflict": 0,
            "selected_absent_roster": 0, "selected_untracked": 0, "selected_inactive": 0,
        },
        "target": {name: 0 for name in (
            "missing", "self", "unresolved", "other_team", "inactive", "untracked",
            "valid_current_state", "not_assessed_invalid_state",
        )},
        "period_contract": {"unknown_direction": 0, "malformed_intervals": 0},
    }
    declared = {home_id, away_id}
    audit["membership"]["roster_unknown_team"] = sum(str(item.get("team_id")) not in declared for item in roster_items)
    if len(declared) != 2:
        raise CompatibilityBlocked("declared home and away team identities are not distinct")
    audit["period_contract"]["unknown_direction"] = sum(side not in {"left_to_right", "right_to_left"} for side in sides)
    for player in roster_items:
        intervals = (player.get("playing_time") or {}).get("by_period") or []
        names = [item.get("name") for item in intervals]
        for period in (1, 2):
            matches = [item for item in intervals if item.get("name") == f"period_{period}"]
            if len(matches) > 1:
                audit["period_contract"]["malformed_intervals"] += 1
            for item in matches:
                try:
                    start, end = int(item.get("start_frame")), int(item.get("end_frame"))
                    if start > end:
                        raise ValueError
                except (TypeError, ValueError):
                    audit["period_contract"]["malformed_intervals"] += 1
        if any(name not in {"period_1", "period_2"} for name in names):
            audit["period_contract"]["malformed_intervals"] += 1

    frames_by_period: dict[int, list[tuple[int, int, dict[str, Any]]]] = {1: [], 2: []}
    roster_set = set(roster)
    for frame in all_frames:
        ids = [str(item.get("player_id", "")) for item in frame.get("player_data") or []]
        duplicates = _duplicate_count(ids)
        audit["duplicates"]["tracking_occurrences"] += duplicates
        audit["duplicates"]["tracking_frames"] += int(duplicates > 0)
        audit["membership"]["tracking_player_absent_roster"] += sum(bool(item) and item not in roster_set for item in ids)
        period, timestamp = frame.get("period"), frame.get("timestamp")
        if period in frames_by_period and timestamp is not None:
            frames_by_period[period].append((clock_microseconds(timestamp), int(frame["frame"]), frame))
    for period_frames in frames_by_period.values():
        if any(a[0] >= b[0] for a, b in zip(period_frames, period_frames[1:])):
            raise ValueError("tracking timestamps must be strictly increasing within period")

    choices: list[ChoiceSet] = []
    exclusions = {name: 0 for name in (
        "missing_or_unusable_target", "invalid_event_or_transition", "invalid_decision_frame",
        "invalid_carrier", "empty_candidate_set", "empty_defender_set_or_geometry",
    )}
    qc: dict[str, Any] = {
        "raw_pass_attempts": len(attempts), "duplicate_event_ids": duplicate_event_ids,
        "target_outside": 0, "target_outside_reasons": {}, "degenerate_segments": 0,
    }
    for event in attempts:
        target = str(event.get("player_targeted_id") or "")
        carrier, fallback_used, conflict = select_carrier(event)
        audit["carrier"]["both_missing"] += int(not carrier)
        audit["carrier"]["fallback_used"] += int(fallback_used)
        audit["carrier"]["conflict"] += int(conflict)
        audit["carrier"]["selected_absent_roster"] += int(bool(carrier) and carrier not in roster)
        if not target:
            audit["target"]["missing"] += 1
        elif target == carrier:
            audit["target"]["self"] += 1
        elif target not in roster:
            audit["target"]["unresolved"] += 1
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
            audit["carrier"]["selected_untracked"] += int(carrier_meta is not None and carrier not in positions)
            audit["carrier"]["selected_inactive"] += int(
                carrier_meta is not None and carrier in positions and not active_in_period(carrier_meta, period, frame_id)
            )
            audit["target"]["not_assessed_invalid_state"] += 1
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
        target_meta = roster[target]
        if str(target_meta.get("team_id")) != carrier_team:
            audit["target"]["other_team"] += 1
        elif not active_in_period(target_meta, period, frame_id):
            audit["target"]["inactive"] += 1
        elif target not in transformed:
            audit["target"]["untracked"] += 1
        else:
            audit["target"]["valid_current_state"] += 1
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
    return choices, qc, audit


def choice_record(choice: ChoiceSet) -> dict[str, Any]:
    return {
        "match_id": choice.match_id, "event_id": choice.event_id,
        "candidate_ids": choice.candidate_ids, "candidate_xy": choice.candidate_xy,
        "defender_xy": choice.defender_xy, "carrier_xy": choice.carrier_xy,
        "target_index": choice.target_index, "target_outside": choice.target_outside,
    }


def canonical_lines(choices: Iterable[ChoiceSet]) -> list[str]:
    return [json.dumps(choice_record(choice), sort_keys=True, separators=(",", ":")) for choice in choices]
