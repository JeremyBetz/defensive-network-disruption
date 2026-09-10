#!/usr/bin/env python3
"""Governed Session 2 acquisition and validation entry point."""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import json
import statistics
import subprocess
import sys
import tempfile
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defensive_network_disruption.data.skillcorner_session2 import (  # noqa: E402
    DEVELOPMENT_MATCHES,
    SOURCE_COMMIT,
    safe_destination,
    source_path,
)

CHECKPOINT = "292506548728069c88a8e2dcc4835cce743cee1b"
PROTOCOL = ROOT / "docs/protocols/phase_02_development_compatibility.md"
MANIFEST = ROOT / "data/manifests/skillcorner_opendata_02a396f.local.json"
DATA_ROOT = ROOT / "data/session_02"
LOCAL_ROOT = ROOT / "outputs/development_compatibility/local"
LEDGER = LOCAL_ROOT / "access_ledger.jsonl"
OWNER_REPO = "SkillCorner/opendata"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def preflight() -> dict:
    if git("rev-parse", "HEAD") != CHECKPOINT:
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", CHECKPOINT, "HEAD"], cwd=ROOT
        )
        if ancestor.returncode != 0:
            raise RuntimeError("Session 1 checkpoint is not an ancestor of HEAD")
    if not PROTOCOL.is_file() or not MANIFEST.is_file():
        raise RuntimeError("protocol or ignored Session 1 manifest is missing")
    if subprocess.run(["git", "check-ignore", "-q", str(MANIFEST)], cwd=ROOT).returncode != 0:
        raise RuntimeError("detailed manifest is not ignored")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest["source"]["commit"] != SOURCE_COMMIT:
        raise RuntimeError("source revision mismatch")
    if set(manifest["matches"]) != DEVELOPMENT_MATCHES | {
        "1874553", "1927964", "1959846", "1986691", "1996436",
        "2006363", "2007448", "2007721", "2010085", "2016236", "1953632",
    }:
        raise RuntimeError("manifest inventory changed")
    return manifest


def token() -> str:
    return subprocess.run(["gh", "auth", "token"], check=True, capture_output=True, text=True).stdout.strip()


def append_ledger(entry: dict) -> None:
    LOCAL_ROOT.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def download_blob(path: str, destination: Path, expected_sha: str, auth: str) -> dict:
    url = f"https://api.github.com/repos/{OWNER_REPO}/git/blobs/{expected_sha}"
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {auth}", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=60) as response:
        envelope = json.load(response)
    payload = base64.b64decode(envelope["content"])
    actual = hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()
    if actual != expected_sha or envelope["sha"] != expected_sha:
        raise RuntimeError(f"Git blob integrity failure: {path}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)
    return {"git_sha": actual, "bytes": len(payload)}


def download_tracking(path: str, destination: Path, expected_sha256: str, expected_size: int, auth: str) -> dict:
    url = f"https://media.githubusercontent.com/media/{OWNER_REPO}/{SOURCE_COMMIT}/{path}"
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {auth}", "User-Agent": "session-2-development-only"})
    digest = hashlib.sha256()
    size = 0
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(request, timeout=120) as response, destination.open("wb") as handle:
        while block := response.read(1024 * 1024):
            digest.update(block)
            size += len(block)
            handle.write(block)
    if digest.hexdigest() != expected_sha256 or size != expected_size:
        destination.unlink(missing_ok=True)
        raise RuntimeError(f"tracking integrity failure: {path}")
    return {"sha256": digest.hexdigest(), "bytes": size}


def acquire_schema() -> None:
    manifest = preflight()
    auth = token()
    acquired = []
    for match_id in sorted(DEVELOPMENT_MATCHES, key=int):
        for product in ("metadata", "events", "tracking"):
            path = source_path(match_id, product)
            destination = safe_destination(DATA_ROOT, match_id, product)
            record = manifest["matches"][match_id][{
                "metadata": "match.json", "events": "dynamic_events.csv",
                "tracking": "tracking_extrapolated.jsonl",
            }[product]]
            if destination.exists():
                if product == "tracking":
                    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
                    if digest != record["lfs_payload_sha256"] or destination.stat().st_size != record["lfs_declared_payload_size"]:
                        raise RuntimeError(f"existing tracking file failed integrity: {path}")
                    result = {"sha256": digest, "bytes": destination.stat().st_size}
                else:
                    payload = destination.read_bytes()
                    actual = hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()
                    if actual != record["git_object_sha"]:
                        raise RuntimeError(f"existing Git blob failed integrity: {path}")
                    result = {"git_sha": actual, "bytes": len(payload)}
            elif product == "tracking":
                result = download_tracking(path, destination, record["lfs_payload_sha256"], record["lfs_declared_payload_size"], auth)
            else:
                result = download_blob(path, destination, record["git_object_sha"], auth)
            acquired.append({"match_id": match_id, "product": product, "path": path, **result})
    append_ledger({
        "timestamp": datetime.now(timezone.utc).isoformat(), "command": "acquire-schema",
        "source": SOURCE_COMMIT, "protocol_sha256": hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "python": sys.version.split()[0],
        "files": acquired,
    })
    print(json.dumps({"status": "ok", "development_matches": 9, "products": 27}))


def clock_seconds(value: str) -> float:
    parts = [float(part) for part in value.split(":")]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    raise ValueError("unsupported clock format")


def distribution(values) -> dict:
    ordered = sorted(values)
    if not ordered:
        return {"count": 0}
    return {
        "count": len(ordered), "minimum": ordered[0],
        "median": statistics.median(ordered), "maximum": ordered[-1],
    }


def active_at(player: dict, period: int, frame: int) -> bool:
    playing = player.get("playing_time") or {}
    for interval in playing.get("by_period") or []:
        name = str(interval.get("name", ""))
        if name in {str(period), f"{period}H", f"Period {period}"}:
            start, end = interval.get("start_frame"), interval.get("end_frame")
            return start is not None and end is not None and start <= frame <= end
    total = playing.get("total") or {}
    start, end = total.get("start_frame"), total.get("end_frame")
    return start is not None and end is not None and start <= frame <= end


def validate() -> None:
    preflight()
    tracking_frames_total = 0
    period_frames = Counter()
    frame_steps = Counter()
    cadence_deltas = Counter()
    timestamp_types = Counter()
    player_count_values = []
    detected_players = missing_players = detected_balls = missing_balls = 0
    coordinate_extrema = [float("inf"), float("-inf"), float("inf"), float("-inf")]
    pitch_dimensions = set()
    event_schema_widths = Counter()
    outcome_counts = Counter()
    pass_attempts = target_id_present = target_link_present = target_link_resolved = 0
    target_link_ambiguous = duplicate_event_ids = unresolved_target_ids = 0
    target_by_outcome = Counter()
    aligned = unmatched = over_tolerance = noncausal = 0
    timing_ages = []
    same_frame_offsets = []
    candidate_counts = []
    zero_candidates = target_in = target_out = missing_carrier = 0
    target_out_reasons = Counter()
    goalkeeper_targets = backward_targets = 0
    kloppy_frames = kloppy_native_player_mismatches = 0
    kloppy_coordinate_max_error = 0.0
    kloppy_ball_coordinate_max_error = 0.0
    kloppy_ball_presence_mismatches = 0
    kloppy_quality_preserved = False
    per_match = []

    for match_id in sorted(DEVELOPMENT_MATCHES, key=int):
        directory = DATA_ROOT / "data/matches" / match_id
        metadata = json.loads((directory / f"{match_id}_match.json").read_text(encoding="utf-8"))
        players = {str(player["id"]): player for player in metadata["players"]}
        pitch_dimensions.add((metadata["pitch_length"], metadata["pitch_width"]))
        home_id = str(metadata["home_team"]["id"])
        side_by_period = {index + 1: side for index, side in enumerate(metadata.get("home_team_side", []))}

        events_path = directory / f"{match_id}_dynamic_events.csv"
        with events_path.open(newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
        event_schema_widths[len(rows[0]) if rows else 0] += 1
        ids = Counter(row["event_id"] for row in rows if row.get("event_id"))
        duplicate_event_ids += sum(count - 1 for count in ids.values() if count > 1)
        event_by_id = {row["event_id"]: row for row in rows if row.get("event_id")}
        passes = [row for row in rows if row.get("pass_outcome")]
        needed_frames = {int(float(row["frame_end"])) for row in passes}
        needed_frames |= {frame - 1 for frame in needed_frames}

        frames = {}
        last_frame = {}
        last_time = {}
        track_path = directory / f"{match_id}_tracking_extrapolated.jsonl"
        with track_path.open(encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                tracking_frames_total += 1
                period = row.get("period")
                timestamp_types[type(row.get("timestamp")).__name__] += 1
                if period is not None:
                    period_frames[str(period)] += 1
                    if period in last_frame:
                        frame_steps[row["frame"] - last_frame[period]] += 1
                    last_frame[period] = row["frame"]
                    if row.get("timestamp") is not None:
                        current_time = clock_seconds(row["timestamp"])
                        if period in last_time:
                            cadence_deltas[round(current_time - last_time[period], 6)] += 1
                        last_time[period] = current_time
                pdata = row.get("player_data") or []
                player_count_values.append(len(pdata))
                for player in pdata:
                    if player.get("is_detected") is True:
                        detected_players += 1
                    else:
                        missing_players += 1
                    x, y = player.get("x"), player.get("y")
                    if x is not None and y is not None:
                        coordinate_extrema[0] = min(coordinate_extrema[0], x)
                        coordinate_extrema[1] = max(coordinate_extrema[1], x)
                        coordinate_extrema[2] = min(coordinate_extrema[2], y)
                        coordinate_extrema[3] = max(coordinate_extrema[3], y)
                ball = row.get("ball_data") or {}
                if ball.get("is_detected") is True:
                    detected_balls += 1
                else:
                    missing_balls += 1
                if row["frame"] in needed_frames:
                    frames[row["frame"]] = row

        match_passes = match_aligned = match_target_in = 0
        for event in passes:
            pass_attempts += 1
            match_passes += 1
            outcome = event["pass_outcome"]
            outcome_counts[outcome] += 1
            target = event.get("player_targeted_id") or ""
            link = event.get("targeted_passing_option_event_id") or ""
            if target:
                target_id_present += 1
                target_by_outcome[outcome] += 1
                if target not in players:
                    unresolved_target_ids += 1
            if link:
                target_link_present += 1
                if link in event_by_id and event_by_id[link].get("event_type") == "passing_option":
                    target_link_resolved += 1
            period = int(float(event["period"]))
            event_frame = int(float(event["frame_end"]))
            event_seconds = clock_seconds(event["time_end"])
            prior = frames.get(event_frame - 1)
            same = frames.get(event_frame)
            if same is not None and same.get("period") == period and same.get("timestamp") is not None:
                same_frame_offsets.append(round(event_seconds - clock_seconds(same["timestamp"]), 6))
            if prior is None or prior.get("period") != period or prior.get("timestamp") is None:
                unmatched += 1
                continue
            age = event_seconds - clock_seconds(prior["timestamp"])
            if age <= 0:
                noncausal += 1
                continue
            if age > 0.1000001:
                over_tolerance += 1
                continue
            aligned += 1
            match_aligned += 1
            timing_ages.append(round(age, 6))
            carrier = event.get("player_id") or event.get("player_in_possession_id") or ""
            carrier_meta = players.get(carrier)
            if carrier_meta is None:
                missing_carrier += 1
                continue
            team_id = str(carrier_meta.get("team_id"))
            tracked = {
                str(item["player_id"]): item for item in prior.get("player_data") or []
                if item.get("x") is not None and item.get("y") is not None
            }
            candidates = [
                pid for pid, meta in players.items()
                if pid != carrier and str(meta.get("team_id")) == team_id
                and pid in tracked and active_at(meta, period, prior["frame"])
            ]
            candidate_counts.append(len(candidates))
            if not candidates:
                zero_candidates += 1
            if target and target in candidates:
                target_in += 1
                match_target_in += 1
                role = (players[target].get("player_role") or {}).get("name")
                if role == "Goalkeeper":
                    goalkeeper_targets += 1
                carrier_x = tracked.get(carrier, {}).get("x")
                target_x = tracked[target]["x"]
                home_attacks_ltr = side_by_period.get(period) == "left_to_right"
                attacks_ltr = home_attacks_ltr if team_id == home_id else not home_attacks_ltr
                if carrier_x is not None and ((attacks_ltr and target_x < carrier_x) or (not attacks_ltr and target_x > carrier_x)):
                    backward_targets += 1
            elif target:
                target_out += 1
                if target not in players:
                    target_out_reasons["target_identity_unresolved"] += 1
                elif target not in tracked:
                    target_out_reasons["target_coordinate_missing"] += 1
                elif not active_at(players[target], period, prior["frame"]):
                    target_out_reasons["target_not_active_by_metadata"] += 1
                else:
                    target_out_reasons["team_or_other_validity_mismatch"] += 1

        # Fixed, content-independent Kloppy subset: first 300 rows per period.
        native = []
        counts = {1: 0, 2: 0}
        with track_path.open(encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                period = row.get("period")
                if period in counts and counts[period] < 300:
                    native.append((line, row)); counts[period] += 1
                if min(counts.values()) == 300:
                    break
        from kloppy import skillcorner
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl") as subset:
            subset.writelines(line for line, _ in native); subset.flush()
            dataset = skillcorner.load(directory / f"{match_id}_match.json", subset.name, coordinates="skillcorner", include_empty_frames=True)
        kloppy_frames += len(dataset.frames)
        for (_, raw), frame in zip(native, dataset.frames, strict=True):
            raw_players = {str(item["player_id"]): item for item in raw.get("player_data") or []}
            parsed_players = {str(player.player_id): data for player, data in frame.players_data.items()}
            if set(raw_players) != set(parsed_players):
                kloppy_native_player_mismatches += 1
            for player_id in set(raw_players) & set(parsed_players):
                raw_player, parsed = raw_players[player_id], parsed_players[player_id]
                if raw_player.get("x") is not None and parsed.coordinates is not None:
                    kloppy_coordinate_max_error = max(
                        kloppy_coordinate_max_error,
                        abs(raw_player["x"] - parsed.coordinates.x),
                        abs(raw_player["y"] - parsed.coordinates.y),
                    )
            raw_ball = raw.get("ball_data") or {}
            parsed_ball = frame.ball_coordinates
            raw_ball_present = raw_ball.get("x") is not None and raw_ball.get("y") is not None
            if raw_ball_present != (parsed_ball is not None):
                kloppy_ball_presence_mismatches += 1
            if raw_ball_present and parsed_ball is not None:
                kloppy_ball_coordinate_max_error = max(
                    kloppy_ball_coordinate_max_error,
                    abs(raw_ball["x"] - parsed_ball.x), abs(raw_ball["y"] - parsed_ball.y),
                    abs((raw_ball.get("z") or 0.0) - (parsed_ball.z or 0.0)),
                )
        per_match.append({"pass_attempts": match_passes, "aligned": match_aligned, "target_in_candidates": match_target_in})

    detailed = {
        "source": SOURCE_COMMIT, "protocol_commit": "d76068e", "development_matches": sorted(DEVELOPMENT_MATCHES),
        "tracking": {"frames": tracking_frames_total, "period_frames": period_frames, "frame_steps": frame_steps,
                     "cadence_deltas_seconds": cadence_deltas, "timestamp_types": timestamp_types,
                     "pitch_dimensions_metres": sorted(pitch_dimensions), "player_counts": distribution(player_count_values),
                     "detected_players": detected_players, "extrapolated_or_missing_players": missing_players,
                     "detected_balls": detected_balls, "extrapolated_or_missing_balls": missing_balls,
                     "coordinate_extrema": coordinate_extrema},
        "events": {"schema_widths": event_schema_widths, "pass_attempts": pass_attempts, "outcomes": outcome_counts,
                   "target_id_present": target_id_present, "target_link_present": target_link_present,
                   "target_link_resolved": target_link_resolved, "duplicate_event_ids": duplicate_event_ids,
                   "unresolved_target_ids": unresolved_target_ids, "target_by_outcome": target_by_outcome},
        "alignment": {"aligned": aligned, "unmatched": unmatched, "over_tolerance": over_tolerance,
                      "noncausal": noncausal, "age_seconds": distribution(timing_ages),
                      "same_frame_offset_seconds": distribution(same_frame_offsets)},
        "candidates": {"counts": distribution(candidate_counts), "zero": zero_candidates, "target_in": target_in,
                       "target_out": target_out, "target_out_reasons": target_out_reasons,
                       "goalkeeper_targets": goalkeeper_targets, "backward_targets": backward_targets},
        "kloppy": {"version": __import__("kloppy").__version__, "frames": kloppy_frames,
                   "player_set_mismatch_frames": kloppy_native_player_mismatches,
                   "coordinate_max_abs_error_metres": kloppy_coordinate_max_error,
                   "ball_coordinate_max_abs_error_metres": kloppy_ball_coordinate_max_error,
                   "ball_presence_mismatch_frames": kloppy_ball_presence_mismatches,
                   "native_quality_fields_preserved": kloppy_quality_preserved},
        "per_match": per_match,
    }
    LOCAL_ROOT.mkdir(parents=True, exist_ok=True)
    (LOCAL_ROOT / "validation_details.json").write_text(json.dumps(detailed, indent=2, default=dict) + "\n")

    public_root = ROOT / "outputs/development_compatibility"
    public_root.mkdir(parents=True, exist_ok=True)
    summaries = {
        "tracking_schema_summary.json": {
            "schema_version": "1.0.0", "source_commit": SOURCE_COMMIT, "development_match_count": 9,
            "skillcorner_format": "V3_JSONL",
            "payload_integrity": "verified_all_9", "tracking_frames": tracking_frames_total,
            "periods": [1, 2], "frame_step_one_count": frame_steps[1], "cadence_hz": 10,
            "cadence_delta_0_1_seconds_count": cadence_deltas[0.1],
            "pitch_dimensions_metres": [list(value) for value in sorted(pitch_dimensions)],
            "coordinate_unit": "metres", "coordinate_origin": "pitch_center",
            "coordinate_extrema_metres": {"x_min": coordinate_extrema[0], "x_max": coordinate_extrema[1], "y_min": coordinate_extrema[2], "y_max": coordinate_extrema[3]},
            "native_fields": ["frame", "timestamp", "period", "player_data", "ball_data", "possession", "image_corners_projection"],
            "player_fields": ["player_id", "x", "y", "is_detected"], "ball_fields": ["x", "y", "z", "is_detected"],
            "kloppy_version": __import__("kloppy").__version__, "kloppy_verdict": "safe_with_native_sidecar",
            "kloppy_bounded_frames_compared": kloppy_frames,
            "kloppy_player_coordinate_max_abs_error_metres": kloppy_coordinate_max_error,
            "kloppy_ball_coordinate_max_abs_error_metres": kloppy_ball_coordinate_max_error,
            "kloppy_player_set_mismatch_frames": kloppy_native_player_mismatches,
            "kloppy_ball_presence_mismatch_frames": kloppy_ball_presence_mismatches,
            "native_sidecar_required": ["player.is_detected", "ball.is_detected", "possession.player_id", "image_corners_projection"],
            "player_detected_rate": detected_players / (detected_players + missing_players),
            "ball_detected_rate": detected_balls / (detected_balls + missing_balls),
            "extrapolation_provenance": "future_use_not_ruled_out_offline_only",
        },
        "event_label_summary.json": {
            "schema_version": "1.0.0", "source_commit": SOURCE_COMMIT, "development_match_count": 9,
            "event_schema_column_counts": sorted(event_schema_widths), "pass_attempts": pass_attempts,
            "pass_outcomes": dict(outcome_counts), "target_player_id_present": target_id_present,
            "target_option_link_present": target_link_present, "target_option_link_resolved": target_link_resolved,
            "duplicate_event_ids": duplicate_event_ids, "unresolved_target_player_ids": unresolved_target_ids,
            "target_present_by_outcome": dict(target_by_outcome), "label_classification": "useful_vendor_target_label_with_limitations",
        },
        "alignment_summary.json": {
            "schema_version": "1.0.0", "source_commit": SOURCE_COMMIT, "development_match_count": 9,
            "rule": "latest_same_period_frame_strictly_before_pass_initiation", "draft_tolerance_ms": 100,
            "tolerance_status": "prospective_draft_from_documented_10_hz_not_truth_claim",
            "aligned": aligned, "unmatched": unmatched, "over_tolerance": over_tolerance, "noncausal": noncausal,
            "age_ms": {key: round(value * 1000, 6) if key != "count" else value for key, value in distribution(timing_ages).items()},
            "event_to_same_frame_offset_ms": {key: round(value * 1000, 6) if key != "count" else value for key, value in distribution(same_frame_offsets).items()},
        },
        "candidate_set_summary.json": {
            "schema_version": "1.0.0", "source_commit": SOURCE_COMMIT, "development_match_count": 9,
            "rules": ["same_team", "not_carrier", "active_by_metadata", "finite_coordinate", "goalkeepers_included", "backward_included", "no_distance_limit", "offside_deferred"],
            "candidate_count": distribution(candidate_counts), "zero_candidate_cases": zero_candidates,
            "candidate_count_frequency": dict(sorted(Counter(candidate_counts).items())),
            "target_in_candidate": target_in, "target_outside_candidate": target_out,
            "target_outside_reasons": dict(target_out_reasons), "goalkeeper_targets": goalkeeper_targets,
            "backward_targets": backward_targets,
        },
    }
    for name, payload in summaries.items():
        (public_root / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    append_ledger({"timestamp": datetime.now(timezone.utc).isoformat(), "command": "validate", "source": SOURCE_COMMIT,
                   "protocol_sha256": hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
                   "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   "python": sys.version.split()[0], "kloppy": __import__("kloppy").__version__,
                   "aggregate_status": "complete"})
    print(json.dumps({"status": "ok", "pass_attempts": pass_attempts, "aligned": aligned, "target_in_candidates": target_in}))


def publication_check() -> None:
    preflight()
    public_root = ROOT / "outputs/development_compatibility"
    required = {"tracking_schema_summary.json", "event_label_summary.json", "alignment_summary.json", "candidate_set_summary.json"}
    if {path.name for path in public_root.glob("*.json")} != required:
        raise RuntimeError("unexpected compact output set")
    prohibited_keys = {"player_id", "event_id", "timestamp", "coordinates", "rows", "passages"}
    prohibited_match_ids = {
        "1874553", "1927964", "1959846", "1986691", "1996436",
        "2006363", "2007448", "2007721", "2010085", "2016236", "1953632",
    }

    def keys(value):
        if isinstance(value, dict):
            for key, child in value.items():
                yield key
                yield from keys(child)
        elif isinstance(value, list):
            for child in value:
                yield from keys(child)

    for path in public_root.glob("*.json"):
        payload = json.loads(path.read_text())
        if prohibited_keys & set(keys(payload)):
            raise RuntimeError(f"prohibited reconstructive top-level field in {path.name}")
        text = path.read_text()
        if str(ROOT) in text or any(match_id in text for match_id in prohibited_match_ids):
            raise RuntimeError(f"private path in {path.name}")
    print(json.dumps({"status": "ok", "compact_outputs": 4}))


def main() -> None:
    command = argparse.ArgumentParser()
    command.add_argument("command", choices=("preflight", "acquire-schema", "validate", "publication-check"))
    args = command.parse_args()
    if args.command == "preflight":
        preflight()
        print(json.dumps({"status": "ok", "checkpoint": CHECKPOINT, "development_matches": 9}))
    elif args.command == "acquire-schema":
        acquire_schema()
    elif args.command == "validate":
        validate()
    elif args.command == "publication-check":
        publication_check()
    else:
        raise AssertionError(args.command)


if __name__ == "__main__":
    main()
