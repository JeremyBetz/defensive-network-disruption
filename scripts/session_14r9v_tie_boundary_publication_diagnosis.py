#!/usr/bin/env python3
"""One governed R9V diagnosis; imports remain inside the failure boundary."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
START = "d1fec793d63370f6e9ed687cbcba83519459b798"
TAG = "f00690c05d8c1c6db308a65bd311c43f9a8ef2fa"
PROTOCOL = ROOT / "docs/protocols/phase_14r9v_tie_boundary_and_publication_diagnosis.md"
OUT = ROOT / "outputs/continuous_occlusion_tie_boundary_publication_diagnosis"
OLD = ROOT / "outputs/continuous_occlusion_empirical_retry_r9u/local"
EXPECTED = {
    "docs/protocols/phase_14r9u_empirical_representation_retry.md": "46542fa8be7e2c8f609f07aa329f3ca1edab113afa200ee98e898fcc52a6a16b",
    "docs/session_14r9u_empirical_representation_retry.md": "7adc513a9953441ed1d0b9db29f5a126c7a261d7dd01a0444df0c0cd2dd56ff5",
    "src/defensive_network_disruption/validation/r9u_study.py": "9b7806e5bb90534cbb5923648330d2592059f009aa253031d3483574a9f6cee7",
}
RETAINED = {
    "prepared.jsonl": "15a809060f0ba4a8cb3790011dab8008db3dad6e931c287ccb395f61ef1530b0",
    "journal.jsonl": "ef3906cc5de9b1c15166720045fe4c5775a271866d0dfc8233786cd91e38ac26",
    "linear_authority.json": "60f6cb33a6fb92b2c48f849fd933e2e9eed60855bd99c800a4a90dd50cc4ede2",
    "original_failure.json": "987abb1af84b473e80108ac9699749cac70b16214f542389f5a28eaa24565bdb",
    "numerical_traceback.txt": "421b9e65bd918992f01a442a5818b36d375b3a8d31bb91384eaf2d0f4cf2729e",
    "publication_failure.json": "006471a1c32c02290bdee6e748d816c38427917049eac5e01b322a3ac5348d93",
    "publication_traceback.txt": "d59619f1fb3aad1a81deb69d5226fa2e7f7d66502ad93f150193d8c0f2858833",
}


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def put(path, value):
    path = Path(path)
    if any(item.is_symlink() for item in (path, *path.parents)):
        raise PermissionError("symlink")
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_name("." + path.name + ".pending")
    with pending.open("xb") as handle:
        handle.write(canonical(value)); handle.flush(); os.fsync(handle.fileno())
    os.link(pending, path); pending.unlink()
    descriptor = os.open(path.parent, os.O_RDONLY)
    try: os.fsync(descriptor)
    finally: os.close(descriptor)


def git(*args):
    return subprocess.check_output(("git", *args), cwd=ROOT, text=True).strip()


def expectation():
    from defensive_network_disruption.validation.checkpoint_ci_authority import CIExpectation
    return CIExpectation(git("rev-parse", "HEAD"), sha(PROTOCOL), sha(Path(__file__)),
                         sha(ROOT / "uv.lock"), sha(ROOT / ".github/workflows/ci.yml"))


def preflight(folder=OUT):
    if git("status", "--porcelain"):
        raise RuntimeError("dirty_tree")
    if git("rev-parse", "HEAD") != git("rev-parse", "origin/main"):
        raise RuntimeError("tracking_mismatch")
    git("merge-base", "--is-ancestor", START, "HEAD")
    if git("rev-parse", "v0.1.0^{}") != TAG:
        raise RuntimeError("release_target")
    if Path(sys.prefix).resolve() != (ROOT / ".venv").resolve():
        raise RuntimeError("project_environment")
    for name, expected in EXPECTED.items():
        if sha(ROOT / name) != expected:
            raise RuntimeError("inherited_authority_hash")
    for name, expected in RETAINED.items():
        if sha(OLD / name) != expected:
            raise RuntimeError("retained_authority_hash")
    sources = git("ls-files", "*r9v*", str(PROTOCOL.relative_to(ROOT))).splitlines()
    for name in sources:
        if subprocess.check_output(("git", "show", "HEAD:" + name), cwd=ROOT) != (ROOT / name).read_bytes():
            raise RuntimeError("implementation_freshness")
    local = Path(folder) / "local"
    for name in ("review.marker", "numerical.marker", "publication.marker", "outer_failure.json"):
        if (local / name).exists():
            raise FileExistsError("governed_attempt_exists")
    from defensive_network_disruption.validation.checkpoint_ci_authority import validate_receipt
    receipt = local / "checkpoint_ci.json"
    sidecar = local / "checkpoint_ci.sha256"
    ci = validate_receipt(receipt, expectation(), expected_sha256=sidecar.read_text().strip())
    return {"head": git("rev-parse", "HEAD"), "protocol_sha256": sha(PROTOCOL),
            "runner_sha256": sha(Path(__file__)), "ci_receipt_sha256": ci.receipt_sha256,
            "release": TAG}


def lexical_selected(path, state=10, edge=2):
    from defensive_network_disruption.validation.empirical_switch_diagnosis import project_prepared_edge
    with Path(path).open("rb") as handle:
        for ordinal, line in enumerate(handle):
            if ordinal == state:
                return project_prepared_edge(line.decode(), edge)
    raise ValueError("retained_row_missing")


def review_retained():
    from defensive_network_disruption.validation import r9j_linear_publication as linear
    authority = linear.review(OLD / "journal.jsonl", expected_sha256=RETAINED["journal.jsonl"],
                              select=("10", "2"))
    record = authority.record()
    expected_failure = {"state": "10", "edge": "2", "candidate": "constant_width",
                        "stage": "owner_certification", "exception": "VerificationError",
                        "traceback_sha256": RETAINED["numerical_traceback.txt"]}
    if record["records"] != 33223 or record["failure"] != expected_failure:
        raise ValueError("retained_terminal_authority")
    receipt = record["selected_receipt"]
    if receipt is None or receipt["state"] != "10" or "2" not in receipt["edges"]:
        raise ValueError("retained_materialization_receipt")
    if sha(OLD / "numerical_traceback.txt") != expected_failure["traceback_sha256"]:
        raise ValueError("retained_traceback")
    return authority


def private_capture(value):
    if value is None or type(value) in (str, bool, int): return value
    if isinstance(value, float):
        if not math.isfinite(value): raise ValueError("nonfinite_capture")
        return value
    if isinstance(value, (list, tuple)): return [private_capture(item) for item in value]
    if isinstance(value, dict): return {str(key): private_capture(item) for key, item in value.items()}
    if hasattr(value, "tolist"): return private_capture(value.tolist())
    raise TypeError("unsupported_private_capture:" + type(value).__name__)


def collision_semantics(trace, *, first_write_valid, original_failure_preserved):
    valid = all(token in trace for token in ("r9o_terminal.py", "retain_authority",
                                              "linear_authority.json", "immutable_record_exists"))
    return {"reproduced": valid, "first_write_valid": first_write_valid,
            "second_write_blocked": "immutable_record_exists" in trace,
            "original_failure_preserved": original_failure_preserved,
            "authority_writers": 2}


def collision_observation():
    return collision_semantics((OLD / "publication_traceback.txt").read_text(),
        first_write_valid=sha(OLD / "linear_authority.json") == RETAINED["linear_authority.json"],
        original_failure_preserved=sha(OLD / "original_failure.json") == RETAINED["original_failure.json"])


def diagnose(folder=OUT):
    folder = Path(folder); local = folder / "local"; started = time.monotonic()
    environment = preflight(folder)
    from defensive_network_disruption.validation import r9v_evidence as e
    from defensive_network_disruption.validation.checkpoint_ci_authority import FailureController
    records = e.empty(); tie_rows = []; publication_rows = []
    numerical = "NF"; publication = "PD"; execution_valid = False
    controller = FailureController(local / "failure")
    exposure = False
    try:
        put(local / "review.marker", {"reserved": True, "authorizes_access": False})
        authority = review_retained()
        put(local / "retained_review.json", authority.record())
        e.fill(records, "authority.json", reason="retained_authority_valid",
               flags={"bindings_valid": True, "journal_valid": True, "terminal_match": True,
                      "traceback_match": True, "receipt_match": True},
               counts={"journal_records": authority.records})

        put(local / "publication.marker", {"reserved": True, "authorizes_access": False})
        collision = collision_observation(); put(local / "collision.json", collision)
        e.fill(records, "publication_collision.json", reason="historical_collision_confirmed",
               flags={key: collision[key] for key in ("reproduced", "first_write_valid",
                       "second_write_blocked", "original_failure_preserved")},
               counts={"authority_writers": collision["authority_writers"]})
        from defensive_network_disruption.validation.r9v_publication_ownership import controls
        before = time.monotonic(); control_rows = controls(local / "publication_controls")
        publication_seconds = time.monotonic() - before
        publication_rows = [{"fixture": row["fixture"], "reviews": row["reviews"],
                             "passed": row["passed"]} for row in control_rows]
        all_publication = all(row["passed"] for row in control_rows)
        repair_flags = {"single_writer": all_publication, "descriptor_bound": all_publication,
                        "validators_read_only": all_publication,
                        "one_linear_review": all(row["reviews"] in (0, 1) for row in control_rows),
                        "legacy_replay_unreachable": all_publication,
                        "original_failures_preserved": all_publication,
                        "negative_controls": all_publication}
        e.fill(records, "publication_repair.json", reason="prospective_single_writer",
               flags=repair_flags, counts={"controls": len(control_rows),
               "controls_passed": sum(row["passed"] for row in control_rows)},
               timings={"seconds": publication_seconds})
        publication = "PA" if collision["reproduced"] and all(repair_flags.values()) else "PB"

        from defensive_network_disruption.geometry.r9v_tie_diagnosis import synthetic_controls
        tie_rows = [{"fixture": row["fixture"], "expected": row["topology"],
                     "observed": row["observed"], "passed": row["passed"]}
                    for row in synthetic_controls()]
        if not all(row["passed"] for row in tie_rows):
            raise RuntimeError("synthetic_tie_control")

        put(local / "numerical.marker", {"reserved": True, "authorizes_access": False})
        if sha(OLD / "prepared.jsonl") != RETAINED["prepared.jsonl"]:
            raise ValueError("prepared_hash")
        put(local / "access_attempt.json", {"schema_version": 1,
            "retained_review_sha256": sha(local / "retained_review.json")})
        selected = lexical_selected(OLD / "prepared.jsonl")
        put(local / "selected_edge.json", selected)
        put(local / "access_materialized.json", {"schema_version": 1,
            "attempt_sha256": sha(local / "access_attempt.json"),
            "selected_sha256": sha(local / "selected_edge.json")})
        exposure = True

        from defensive_network_disruption.geometry import r9t_adapter
        from defensive_network_disruption.geometry.r9v_tie_diagnosis import (
            BoundaryObserver, classify_observation, reference)
        from defensive_network_disruption.geometry.verification_repair import VerificationError
        observer = BoundaryObserver(); stages = []
        reproduction_start = time.monotonic(); deadline = reproduction_start + 3600
        try:
            with observer.enabled():
                r9t_adapter.evaluate_edge("constant_width", selected["carrier"], selected["receiver"],
                    selected["defenders"], root=ROOT,
                    authority_context={"alias": selected["alias"], "state": "10", "edge": "2"},
                    record=lambda **detail: stages.append(detail["stage"]), deadline=deadline)
        except VerificationError as error:
            reproduced = str(error) == "tie_boundary_not_maximal" and stages[-1:] == ["owner_certification"]
            controller.capture(error, "numerical_diagnosis", context=("10", "2", "constant_width"))
        else:
            reproduced = False
        reproduction_seconds = time.monotonic() - reproduction_start
        capture = observer.result() if reproduced else None
        if capture is not None:
            put(local / "boundary_capture.json", private_capture(capture))
        e.fill(records, "numerical_reproduction.json", status="complete" if reproduced else "partial",
               reason="exact_failure_reproduced" if reproduced else "different_result",
               flags={"reproduced": reproduced, "unchanged_route": True,
                      "frame_captured": capture is not None,
                      "original_preserved": (local / "failure/original_failure.json").exists()},
               counts={"boundary_frames": len(observer.frames)},
               timings={"seconds": reproduction_seconds})
        if reproduced:
            pair = capture["pair"]; owners = capture["owners"]
            pair_in = set(pair).issubset(owners)
            e.fill(records, "tie_invariant.json", reason="source_invariant_observed",
                   flags={"exact_pair_tie": capture["pair_inside_difference"] == 0.,
                          "pair_in_global_owner_block": pair_in,
                          "positive_global_maximum": capture["global_maximum"] > 0.,
                          "tolerance_distinct": True},
                   counts={"pair_members": 2, "global_owners": len(owners)})
            plateau = capture.get("plateau")
            if plateau is None:
                raise ValueError("missing_plateau_frame")
            grid = plateau["grid"]; left = float(grid[plateau["index"]]); right = float(grid[plateau["end"]])
            reference_start = time.monotonic()
            result = reference(selected["carrier"], selected["receiver"], selected["defenders"],
                pair, left, right, deadline=min(deadline, reference_start + 600),
                sink=lambda label, value: put(local / f"reference_{label}_{time.monotonic_ns()}.json", value))
            reference_seconds = time.monotonic() - reference_start
            put(local / "reference_result.json", result)
            numerical, specification = classify_observation(capture, result)
            put(local / "prospective_specification.json", {"classification": numerical,
                                                             "specification": specification})
            e.fill(records, "tie_maximality.json", status="complete" if result["complete"] else "partial",
                   reason="independent_reference",
                   flags={"pair_equal": result["pair_counts"]["equal"] > 0,
                          "globally_maximal": result["maximum_counts"]["maximum"] > 0,
                          "third_defender_dominance": result["maximum_counts"]["dominated"] > 0,
                          "extension_available": False, "complete": result["complete"]},
                   counts={"cells": result["cells"],
                           "dominated_cells": result["maximum_counts"]["dominated"],
                           "unresolved_cells": result["maximum_counts"]["unresolved"]})
            e.fill(records, "independent_reference.json", status="complete" if result["complete"] else "partial",
                   reason="exact_constant_width_bounds",
                   flags={"exact_inputs": True, "outward_bounds": True,
                          "symbolic_identity": result["pair_counts"]["equal"] > 0,
                          "complete": result["complete"]},
                   counts={"cells": result["cells"], "subdivisions": result["subdivisions"],
                           "max_depth": result["max_depth"]}, timings={"seconds": reference_seconds})
        execution_valid = reproduced
    except BaseException as error:
        if not (local / "failure/original_failure.json").exists():
            controller.capture(error, "governed_diagnosis")
        else:
            controller.publication_failure(error)
    qc = {"status": "complete" if execution_valid else "partial",
          "execution_valid": execution_valid, "numerical": numerical,
          "publication": publication, "readiness": 3 if execution_valid and publication == "PA" else 4,
          "states_reopened": int(exposure), "edges_reopened": int(exposure),
          "exposure_uncertain": (local / "access_attempt.json").exists() and not exposure}
    return e.close(folder, environment, records, tie_rows, publication_rows, qc)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "diagnose", "publication-check"))
    args = parser.parse_args()
    try:
        if args.command == "preflight": result = preflight()
        elif args.command == "diagnose": result = diagnose()
        else:
            from defensive_network_disruption.validation.r9v_evidence import publication_check
            result = publication_check(OUT)
        print(json.dumps(result, sort_keys=True, allow_nan=False))
    except BaseException as error:
        if args.command == "diagnose" and not isinstance(error, FileExistsError):
            try:
                put(OUT / "local/outer_failure.json", {"schema_version": 1,
                    "exception": type(error).__name__, "message": str(error),
                    "traceback": "".join(traceback.format_exception(error))})
            except BaseException: pass
        raise


if __name__ == "__main__":
    main()
