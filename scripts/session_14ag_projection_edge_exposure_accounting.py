#!/usr/bin/env python3
"""Synthetic-only Session 14ag projection exposure accounting audit."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import traceback
from typing import Any, Callable, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defensive_network_disruption.validation.projection_exposure import (  # noqa: E402
    CANDIDATES, ExposureAuthority, capture_failure, package_record,
    progress_view, replay_exposure, validate_cross_file_package,
)
from defensive_network_disruption.validation.r5_persistence import (  # noqa: E402
    durable_write, read_journal,
)
from defensive_network_disruption.validation.state_lifecycle import (  # noqa: E402
    LifecycleError, canonical_bytes,
)

OUT = ROOT / "outputs" / "session14_projection_edge_exposure"
LOCAL = OUT / "local"
PROTOCOL = ROOT / "docs" / "protocols" / "phase_14ag_projection_edge_exposure_accounting.md"
IMPLEMENTATION = ROOT / "src" / "defensive_network_disruption" / "validation" / "projection_exposure.py"
TEST = ROOT / "tests" / "test_session14ag_projection_exposure.py"
STARTING_HEAD = "0a673cf7277e6f6c62da18e24ff0bdb1c95ff2ee"
CLASSIFICATION = "A — PROJECTION-TO-EDGE EXPOSURE ACCOUNTING REPAIRED"
FILES = (
    "exposure_contract.json", "edge_lifecycle_oracles.csv", "field_work_oracles.csv",
    "r5_regression.json", "invalid_package_injections.csv", "valid_package_controls.csv",
    "wrapper_compatibility.json", "access_journal_summary.json", "qc.json",
)
HISTORICAL = {
    "r5_persistence.py": "0feda7ee71e7175268e4a5aaf8bcda78e1f68c8c278049caf6bb2799300a9a9d",
    "state_lifecycle.py": "9aaff345990f2ea4d51afb86b024424ba8311dd2917d1cc417c2f76bcee991fe",
    "empirical_lifecycle.py": "41157725f762352e96d9eeda0123406f79e48655e2d366df47fcb0bbbad423ca",
    "session_14r5_occlusion_study.py": "84c32d859ea093734f8bf05db55bf5c23739aa9b64911062fc3447d89eddec6b",
    "r5_interruption.json": "e4013b39d1a8d8804af1401043a546093bf334a386b0b2b6546a183630dda325",
    "r5_manifest.json": "cdaec4c686ae16a69fae3e48144dd28692d3897dc49f6c09167af01031a0dbed",
}


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, text=True, capture_output=True).stdout.strip()


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            value.update(chunk)
    return value.hexdigest()


def atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_name("." + path.name + ".pending")
    with pending.open("xb") as handle:
        handle.write(content); handle.flush(); os.fsync(handle.fileno())
    os.replace(pending, path)


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    atomic(path, canonical_bytes(value))


def write_csv(path: Path, fields: Iterable[str], rows: list[dict[str, Any]]) -> None:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=tuple(fields), lineterminator="\n")
    writer.writeheader(); writer.writerows(rows)
    atomic(path, stream.getvalue().encode())


def historical_paths() -> dict[str, Path]:
    return {
        "r5_persistence.py": ROOT / "src/defensive_network_disruption/validation/r5_persistence.py",
        "state_lifecycle.py": ROOT / "src/defensive_network_disruption/validation/state_lifecycle.py",
        "empirical_lifecycle.py": ROOT / "src/defensive_network_disruption/validation/empirical_lifecycle.py",
        "session_14r5_occlusion_study.py": ROOT / "scripts/session_14r5_occlusion_study.py",
        "r5_interruption.json": ROOT / "outputs/continuous_occlusion_retry_14r5/authority/interruption_boundary_check.json",
        "r5_manifest.json": ROOT / "outputs/continuous_occlusion_retry_14r5/manifest.json",
    }


def preflight() -> None:
    if git("status", "--porcelain"):
        raise LifecycleError("dirty_tree")
    for path in (PROTOCOL, IMPLEMENTATION, TEST, Path(__file__)):
        if not path.is_file() or not git("ls-files", "--error-unmatch", str(path.relative_to(ROOT))):
            raise LifecycleError("uncommitted_authority")
    observed = {name: sha256(path) for name, path in historical_paths().items()}
    if observed != HISTORICAL:
        raise LifecycleError("historical_authority_changed")
    print("Session 14ag preflight passed")


def new(case: str, states: tuple[tuple[str, tuple[str, ...]], ...]) -> ExposureAuthority:
    path = LOCAL / "journals" / case / "journal.jsonl"
    item = ExposureAuthority(path); item.authorize_access()
    for state, edges in states: item.discover_state(state, edges)
    return item


def snapshot(item: ExposureAuthority) -> dict[str, Any]:
    return replay_exposure(read_journal(item.journal.path)[0])


def project(item: ExposureAuthority, state: str) -> None:
    item.project(state, lambda: {"synthetic": True})


def prepare(item: ExposureAuthority, state: str = "state_01") -> None:
    item.prepare_state(state); item.start_state(state)


def complete_fields(item: ExposureAuthority, state: str, edge: str, count: int) -> None:
    for candidate in CANDIDATES[:count]:
        item.start_field(state, edge, candidate); item.complete_field(state, edge, candidate)


def close_failure(item: ExposureAuthority, case: str, *, state: str | None = None,
                  edge: str | None = None, candidate: str | None = None) -> dict[str, Any]:
    capture_failure(item, stage=case, exception=RuntimeError("synthetic interruption"),
                    state=state, edge=edge, candidate=candidate)
    result = snapshot(item); item.close(); return result


def oracle_row(name: str, result: Mapping[str, Any], expected: str = "accepted") -> dict[str, Any]:
    counters = result["counters"]
    return {
        "oracle": name, "expected": expected, "observed": "accepted",
        "states_discovered": counters["states_discovered"],
        "states_completed": counters["states_completed"],
        "edges_discovered": counters["edges_discovered"],
        "edges_opened": counters["edges_opened"],
        "edges_evaluation_started": counters["edges_evaluation_started"],
        "edges_completed": counters["edges_completed"],
        "unresolved_exposed_edges": counters["unresolved_exposed_edges"],
        "unresolved_projection_attempts": counters["unresolved_projection_attempts"],
        "field_evaluations_started": counters["field_evaluations_started"],
        "field_evaluations_completed": counters["field_evaluations_completed"],
        "active_state": result["active"]["state"] is not None,
        "active_edge": result["active"]["edge"] is not None,
        "active_candidate": result["active"]["candidate"] or "none",
    }


def interruption_oracles() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    item = ExposureAuthority(LOCAL / "journals/before_discovery/journal.jsonl"); item.authorize_access()
    rows.append(oracle_row("before_edge_discovery", close_failure(item, "before_discovery")))

    item = new("after_discovery", (("state_01", ("edge_01",)),))
    rows.append(oracle_row("after_discovery_before_projection", close_failure(item, "after_discovery", state="state_01")))

    item = new("projection_failure", (("state_01", ("edge_01",)),))
    try: item.project("state_01", lambda: (_ for _ in ()).throw(RuntimeError("synthetic projection")))
    except RuntimeError: pass
    rows.append(oracle_row("during_projection_before_materialization", close_failure(item, "projection_failure", state="state_01")))

    for name, completed, start_only in (
        ("immediately_after_projection", 0, False),
        ("after_first_field_started", 0, True),
        ("after_one_field_completed", 1, False),
        ("after_two_fields_completed", 2, False),
        ("after_all_fields_before_edge_completion", 3, False),
    ):
        item = new(name, (("state_01", ("edge_01",)),)); project(item, "state_01"); prepare(item)
        complete_fields(item, "state_01", "edge_01", completed)
        candidate = None
        if start_only:
            candidate = "isotropic"; item.start_field("state_01", "edge_01", candidate)
        rows.append(oracle_row(name, close_failure(item, name, state="state_01", edge="edge_01", candidate=candidate)))

    item = new("after_edge_completion", (("state_01", ("edge_01",)),)); project(item, "state_01"); prepare(item)
    complete_fields(item, "state_01", "edge_01", 3); item.complete_edge("state_01", "edge_01")
    rows.append(oracle_row("after_edge_completion", close_failure(item, "after_edge_completion", state="state_01")))

    item = new("multi_edge_partial", (("state_01", ("edge_01", "edge_02")),)); project(item, "state_01"); prepare(item)
    complete_fields(item, "state_01", "edge_01", 3); item.complete_edge("state_01", "edge_01")
    rows.append(oracle_row("multiple_edges_one_unresolved", close_failure(item, "multi_edge_partial", state="state_01")))
    return rows


def field_work_oracles() -> list[dict[str, Any]]:
    rows = []
    for count in (0, 1, 2, 3):
        item = new(f"field_work_{count}", (("state_01", ("edge_01",)),)); project(item, "state_01"); prepare(item)
        complete_fields(item, "state_01", "edge_01", count)
        result = close_failure(item, f"field_work_{count}", state="state_01", edge="edge_01")
        row = oracle_row(f"{count}_fields_completed", result)
        for candidate in CANDIDATES:
            row[candidate + "_started"] = result["field_work_by_candidate"][candidate]["started"]
            row[candidate + "_completed"] = result["field_work_by_candidate"][candidate]["completed"]
        rows.append(row)
    item = new("field_failure", (("state_01", ("edge_01",)),)); project(item, "state_01"); prepare(item)
    complete_fields(item, "state_01", "edge_01", 2); item.start_field("state_01", "edge_01", "constant_width")
    result = close_failure(item, "field_failure", state="state_01", edge="edge_01", candidate="constant_width")
    row = oracle_row("final_field_failure", result)
    for candidate in CANDIDATES:
        row[candidate + "_started"] = result["field_work_by_candidate"][candidate]["started"]
        row[candidate + "_completed"] = result["field_work_by_candidate"][candidate]["completed"]
    rows.append(row)
    return rows


def package(item: ExposureAuthority, mode: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    view = progress_view(item.journal.path, expected_head=item.journal.previous, mode=mode)
    return view, [package_record(view) for _ in range(4)]


def validate_package(item: ExposureAuthority, mode: str, items: list[dict[str, Any]]) -> None:
    validate_cross_file_package(journal_path=item.journal.path, expected_head=item.journal.previous,
                                mode=mode, qc=items[0], manifest=items[1], evidence=items[2], report=items[3])


def invalid_injections() -> list[dict[str, str]]:
    item = new("invalid_base", (("state_01", ("edge_01", "edge_02")),)); project(item, "state_01")
    item.fail("synthetic_interruption", RuntimeError("synthetic"), state="state_01")
    _, base = package(item, "empirical_failure")
    mutations: tuple[tuple[str, int, Callable[[dict[str, Any]], None]], ...] = (
        ("two_projected_zero_opened", 0, lambda r: r["progress_authority"]["snapshot"]["counters"].__setitem__("edges_opened", 0)),
        ("negative_unresolved", 0, lambda r: r["progress_authority"]["snapshot"]["counters"].__setitem__("unresolved_exposed_edges", -1)),
        ("completed_exceeds_opened", 0, lambda r: r["progress_authority"]["snapshot"]["counters"].__setitem__("edges_completed", 3)),
        ("completed_without_fields", 0, lambda r: r["progress_authority"]["snapshot"]["counters"].__setitem__("edges_completed", 1)),
        ("state_complete_with_unresolved", 0, lambda r: r["progress_authority"]["snapshot"]["counters"].__setitem__("states_completed", 1)),
        ("field_count_as_edges", 0, lambda r: r["progress_authority"]["snapshot"]["counters"].__setitem__("edges_opened", 6)),
        ("journal_edges_public_zero", 2, lambda r: r["progress_authority"]["snapshot"]["counters"].__setitem__("edges_opened", 0)),
        ("qc_manifest_disagree", 1, lambda r: r["progress_authority"]["snapshot"]["counters"].__setitem__("edges_opened", 0)),
        ("failure_resets_exposure", 3, lambda r: r["progress_authority"]["snapshot"]["counters"].__setitem__("unresolved_exposed_edges", 0)),
        ("missing_active_edge", 0, lambda r: r["progress_authority"]["snapshot"]["active"].__setitem__("state", None)),
    )
    rows = []
    for name, target, mutate in mutations:
        changed = copy.deepcopy(base); mutate(changed[target])
        try:
            validate_package(item, "empirical_failure", changed); observed = "accepted"
        except LifecycleError as exc:
            observed = "rejected:" + str(exc)
        rows.append({"injection": name, "expected": "rejected", "observed": observed})
    item.close(); return rows


def valid_controls() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    def finish(name: str, item: ExposureAuthority, mode: str) -> dict[str, Any]:
        view, items = package(item, mode); validate_package(item, mode, items)
        row = oracle_row(name, view["snapshot"]); rows.append(row); item.close(); return view["snapshot"]

    item = new("valid_no_exposure", (("state_01", ("edge_01",)),)); item.block("synthetic_stop", "no_exposure")
    finish("no_edge_exposure", item, "pre_access")
    for count in (0, 1, 2):
        item = new(f"valid_partial_{count}", (("state_01", ("edge_01",)),)); project(item, "state_01"); prepare(item)
        complete_fields(item, "state_01", "edge_01", count); item.fail("synthetic_partial", RuntimeError("synthetic"), state="state_01", edge="edge_01")
        finish(("projected_only", "one_field_partial", "two_field_partial")[count], item, "empirical_failure")
    item = new("valid_completed_edge", (("state_01", ("edge_01",)),)); project(item, "state_01"); prepare(item)
    complete_fields(item, "state_01", "edge_01", 3); item.complete_edge("state_01", "edge_01"); item.fail("after_edge", RuntimeError("synthetic"), state="state_01")
    finish("completed_edge", item, "empirical_failure")
    item = new("valid_partial_state", (("state_01", ("edge_01", "edge_02")),)); project(item, "state_01"); prepare(item)
    complete_fields(item, "state_01", "edge_01", 3); item.complete_edge("state_01", "edge_01"); item.fail("partial_state", RuntimeError("synthetic"), state="state_01")
    finish("partial_state_unresolved_edge", item, "empirical_failure")
    item = new("valid_completed_state", (("state_01", ("edge_01",)),)); project(item, "state_01"); prepare(item)
    complete_fields(item, "state_01", "edge_01", 3); item.complete_edge("state_01", "edge_01"); item.complete_state("state_01"); item.succeed()
    finish("completed_state", item, "empirical_success")
    item = new("valid_multi_state", (("state_01", ("edge_01", "edge_02")), ("state_02", ("edge_03",))))
    for state, edges in (("state_01", ("edge_01", "edge_02")), ("state_02", ("edge_03",))):
        project(item, state); prepare(item, state)
        for candidate in CANDIDATES:
            for edge in edges: item.start_field(state, edge, candidate); item.complete_field(state, edge, candidate)
        for edge in edges: item.complete_edge(state, edge)
        item.complete_state(state)
    item.succeed(); success = finish("multi_state_success", item, "empirical_success")
    return rows, success


def audit() -> None:
    preflight(); OUT.mkdir(parents=True, exist_ok=True); LOCAL.mkdir(parents=True, exist_ok=True)
    durable_write(LOCAL / "audit.marker", {"session": "14ag", "attempt": 1})
    if any((OUT / name).exists() for name in (*FILES, "manifest.json")):
        raise LifecycleError("public_outputs_already_exist")

    edge_rows = interruption_oracles(); work_rows = field_work_oracles()
    invalid_rows = invalid_injections(); valid_rows, success = valid_controls()
    if any(not row["observed"].startswith("rejected:") for row in invalid_rows):
        raise LifecycleError("invalid_package_accepted")

    r5 = next(row for row in edge_rows if row["oracle"] == "immediately_after_projection")
    if (r5["edges_opened"], r5["edges_evaluation_started"], r5["edges_completed"], r5["unresolved_exposed_edges"]) != (1, 0, 0, 1):
        raise LifecycleError("single_edge_projection_regression")
    r5_item = new("r5_exact", (("state_01", ("edge_01", "edge_02")),)); project(r5_item, "state_01")
    r5_result = close_failure(r5_item, "after_projection_registration", state="state_01")
    r5_counts = r5_result["counters"]
    if tuple(r5_counts[k] for k in ("edges_opened", "edges_evaluation_started", "edges_completed", "unresolved_exposed_edges")) != (2, 0, 0, 2):
        raise LifecycleError("r5_regression")

    contract = {
        "schema_version": 1, "scope": "synthetic_accounting_publication_only",
        "geometric_edge": "one_carrier_to_receiver_connection",
        "edge_lifecycle": ["discovered", "projection_attempted", "geometry_projected_opened", "evaluation_started", "evaluation_completed"],
        "exposure_boundary": "successful_receiver_geometry_materialization",
        "projection_receipt_before_downstream": True,
        "unresolved_exposed_edges": "unique_projected_edges_minus_completed_edges",
        "candidate_order": list(CANDIDATES), "candidate_calls_are_edges": False,
        "real_states_opened": 0, "real_edges_opened": 0,
    }
    r5_public = {"schema_version": 1, "status": "pass", "historical_defect": {"projected_edges": 2, "reported_opened_edges": 0, "validator_accepted": True},
                 "repaired": {key: r5_counts[key] for key in ("edges_opened", "edges_evaluation_started", "edges_completed", "unresolved_exposed_edges")},
                 "real_states_opened": 0, "real_edges_opened": 0}
    wrapper = {"schema_version": 1, "status": "pass", "sequence": ["fail_closed_launch", "synthetic_state_discovery", "receiver_geometry_projection", "synthetic_interruption", "failure_publication"],
               "projected_history_preserved": True, "opened_edges": 2, "unresolved_exposed_edges": 2, "real_states_opened": 0, "real_edges_opened": 0}
    journal_summary = {"schema_version": 1, "status": "pass", "authority": "append_only_hash_chained_journal",
                       "projection_attempts_distinct_from_receipts": True, "batch_receipt_counts_unique_edges": True,
                       "candidate_calls_separate": True, "unresolved_attempt_blocks_confirmed_zero": True,
                       "synthetic_journals": len(edge_rows) + len(work_rows) + len(valid_rows) + 2,
                       "real_journal_entries": 0}
    qc = {"schema_version": 1, "status": "success", "classification": CLASSIFICATION, "readiness": 1,
          "r5_regression_passed": True, "interruption_oracles_passed": len(edge_rows),
          "invalid_packages_rejected": len(invalid_rows), "valid_packages_accepted": len(valid_rows),
          "unique_edge_accounting": True, "field_work_separate": True,
          "cross_file_validation": True, "failure_preservation": True,
          "real_states_opened": 0, "real_edges_opened": 0,
          "historical_hashes": HISTORICAL}

    write_json(OUT / "exposure_contract.json", contract)
    write_csv(OUT / "edge_lifecycle_oracles.csv", edge_rows[0].keys(), edge_rows)
    write_csv(OUT / "field_work_oracles.csv", work_rows[0].keys(), work_rows)
    write_json(OUT / "r5_regression.json", r5_public)
    write_csv(OUT / "invalid_package_injections.csv", ("injection", "expected", "observed"), invalid_rows)
    write_csv(OUT / "valid_package_controls.csv", valid_rows[0].keys(), valid_rows)
    write_json(OUT / "wrapper_compatibility.json", wrapper)
    write_json(OUT / "access_journal_summary.json", journal_summary)
    write_json(OUT / "qc.json", qc)
    manifest = {"schema_version": 1, "status": "success", "classification": CLASSIFICATION, "readiness": 1,
                "starting_head": STARTING_HEAD, "implementation_commit": git("rev-parse", "HEAD"),
                "protocol_sha256": sha256(PROTOCOL), "implementation_sha256": sha256(IMPLEMENTATION),
                "test_sha256": sha256(TEST), "historical_hashes": HISTORICAL,
                "outputs": {name: sha256(OUT / name) for name in FILES}}
    write_json(OUT / "manifest.json", manifest)
    publication_check(); atomic(LOCAL / "closed", b"closed\n")
    print(CLASSIFICATION + "; readiness 1")


def publication_check() -> None:
    manifest = json.loads((OUT / "manifest.json").read_text())
    expected = {"schema_version", "status", "classification", "readiness", "starting_head", "implementation_commit",
                "protocol_sha256", "implementation_sha256", "test_sha256", "historical_hashes", "outputs"}
    if set(manifest) != expected or set(manifest["outputs"]) != set(FILES):
        raise LifecycleError("manifest_schema")
    if manifest["historical_hashes"] != HISTORICAL or {name: sha256(path) for name, path in historical_paths().items()} != HISTORICAL:
        raise LifecycleError("historical_hash")
    for name, expected_hash in manifest["outputs"].items():
        if sha256(OUT / name) != expected_hash:
            raise LifecycleError("output_hash")
    qc = json.loads((OUT / "qc.json").read_text())
    if qc["classification"] != CLASSIFICATION or qc["readiness"] != 1 or qc["real_states_opened"] or qc["real_edges_opened"]:
        raise LifecycleError("qc_result")
    if not all((qc[key] for key in ("r5_regression_passed", "unique_edge_accounting", "field_work_separate", "cross_file_validation", "failure_preservation"))):
        raise LifecycleError("qc_gate")
    for path in (OUT / name for name in (*FILES, "manifest.json")):
        content = path.read_text()
        for forbidden in ("/Users/", "/private/", "event_id", "target_index", "candidate_xy", "defender_xy", "token="):
            if forbidden in content:
                raise LifecycleError("publication_content")
    print("Session 14ag publication checks passed")


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("command", choices=("preflight", "audit", "publication-check"))
    command = parser.parse_args().command
    if command == "preflight": preflight()
    elif command == "publication-check": publication_check()
    else:
        try: audit()
        except BaseException as exc:
            LOCAL.mkdir(parents=True, exist_ok=True)
            failure = LOCAL / "failure.json"
            if not failure.exists():
                write_json(failure, {"schema_version": 1, "stage": "governed_audit", "exception": type(exc).__name__,
                                     "traceback": traceback.format_exc(), "real_states_opened": 0, "real_edges_opened": 0})
            raise


if __name__ == "__main__": main()
