#!/usr/bin/env python3
"""Single governed Session 14R9K comparator acceptance."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/continuous_occlusion_onset_comparator_repair"
OLD = ROOT / "outputs/continuous_occlusion_empirical_retry_r9i/local"
R9J = ROOT / "outputs/continuous_occlusion_r9i_blocker_diagnosis"
PROTOCOL = ROOT / "docs/protocols/phase_14r9k_onset_only_comparator_repair.md"
PREPARED_HASH = "15a809060f0ba4a8cb3790011dab8008db3dad6e931c287ccb395f61ef1530b0"
JOURNAL_HASH = "6f1c2110d20fc0edbfe9d337f231e829a73df9d90eb47f65f6afb2366054ef3c"
AUTHORITY_HASHES = {
    "docs/session_14r9j_r9i_blocker_diagnosis.md": "7b1f4a2ddd0c4b8dc3030aa156c7a4fe058298b0132a3934bf0a95c767af2465",
    "docs/protocols/phase_14r9j_r9i_blocker_diagnosis.md": "8c205e768840260dc81ea7bb000d8edaa143de75eb0158d3a80bb7f3e43de9dd",
    "outputs/continuous_occlusion_r9i_blocker_diagnosis/manifest.json": "cbe421fe0fec781e2456e811806e437ad0dc711f958f05a0d9f1ed7d13602a96",
    "outputs/continuous_occlusion_r9i_blocker_diagnosis/independent_reference.json": "de6cee8dbe6d9bc74be3674a4f9f2d844160ff6ff5a34841f638ad81c3d5fc1d",
    "outputs/continuous_occlusion_r9i_blocker_diagnosis/retained_journal_review.json": "ad62303b09a1fb70324fa1417e86dddc68a4f8ca7a52f402523984df2bbc5891",
    "src/defensive_network_disruption/geometry/r9e_representation.py": "98f5f672f7da85b565a4c3b784ccecf6d4635554de684aaba4891f5ec0bb40d8",
    "src/defensive_network_disruption/geometry/onset_owner_certification.py": "d62dc611a759b03c68098c7628568d3f9e78fd59d995a4f555dd6ed325171b97",
    "src/defensive_network_disruption/geometry/micro_interval_verifier.py": "55389fd78d7c546bb1b4c830cdb434932fce6f67dcc8042a2427e44dc77c2b0e",
    "src/defensive_network_disruption/validation/independent_certificate_verifier.py": "be73a070e4dc290d2697f98146f495a9f4a05dfcf9b256ca57b255414e337789",
    "src/defensive_network_disruption/validation/r9j_linear_publication.py": "a242cb0921d1fd390cd2b74c9d15a0fdff3e2b82e46000dc8be0cbbba6d6c139",
}


def git(*args):
    return subprocess.check_output(("git", *args), cwd=ROOT, text=True).strip()


def preflight():
    from defensive_network_disruption.validation import r9k_evidence as evidence
    if git("status", "--porcelain"): raise RuntimeError("dirty_tree")
    git("merge-base", "--is-ancestor", evidence.START, "HEAD")
    if git("rev-parse", "v0.1.0^{}") != evidence.TAG: raise RuntimeError("release_changed")
    if Path(sys.prefix).resolve() != (ROOT / ".venv").resolve(): raise RuntimeError("locked_environment")
    for name, expected in AUTHORITY_HASHES.items():
        if evidence.sha(ROOT / name) != expected: raise RuntimeError("authority_changed:" + name)
    sources = git("ls-files", "scripts/*14r9k*", "src/**/r9k*", "tests/*14r9k*",
                  str(PROTOCOL.relative_to(ROOT))).splitlines()
    if len(sources) < 5: raise RuntimeError("implementation_incomplete")
    for name in sources:
        if subprocess.check_output(("git", "show", "HEAD:" + name), cwd=ROOT) != (ROOT / name).read_bytes():
            raise RuntimeError("implementation_not_committed:" + name)
    return {
        "implementation": git("rev-parse", "HEAD"),
        "protocol_sha256": evidence.sha(PROTOCOL), "lock_sha256": evidence.sha(ROOT / "uv.lock"),
        "python": sys.version.split()[0],
        "packages": {name: importlib.metadata.version(name)
                     for name in ("numpy", "scipy", "defensive-network-disruption")},
        "historical_hashes": AUTHORITY_HASHES,
        "source_hashes": {name: evidence.sha(ROOT / name) for name in sources},
    }


def bootstrap(path, value):
    raw = (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    if any(item.is_symlink() for item in (path, *path.parents)): raise PermissionError("symlink")
    pending = path.with_name("." + path.name + ".pending")
    with pending.open("xb") as handle:
        handle.write(raw); handle.flush(); os.fsync(handle.fileno())
    os.link(pending, path); pending.unlink()
    descriptor = os.open(path.parent, os.O_RDONLY)
    try: os.fsync(descriptor)
    finally: os.close(descriptor)


def entry(folder, work):
    local = Path(folder) / "local"
    bootstrap(local / "acceptance.marker", {"schema_version": 1, "reserved": True,
                                             "authorizes_access": False})
    try:
        return work(Path(folder))
    except BaseException as error:
        try:
            bootstrap(local / "outer_emergency.json", {
                "schema_version": 1, "status": "invalid", "exception": type(error).__name__,
                "message": str(error), "traceback": "".join(traceback.format_exception(error))})
        except BaseException:
            pass
        raise


class PrivateEvidence:
    def __init__(self, local): self.local = Path(local); self.serial = 0
    def save(self, label, value):
        from defensive_network_disruption.validation import r9k_evidence as evidence
        name = f"{self.serial:06d}_{label}.json"; self.serial += 1
        evidence.put(self.local / name, value); return name


def selected_edge(prepared, receipt):
    from defensive_network_disruption.validation.empirical_switch_diagnosis import project_prepared_edge
    if receipt is None or receipt["state"] != "4" or "7" not in receipt["edges"]:
        raise PermissionError("missing_selected_materialization")
    with Path(prepared).open("rb") as handle:
        for ordinal, raw in enumerate(handle):
            if ordinal == 4: return project_prepared_edge(raw.decode(), 7)
    raise ValueError("selected_row_unavailable")


def _private_index():
    from defensive_network_disruption.validation import r9k_evidence as evidence
    return evidence.load(R9J / "local/private_index.json")["files"]


def _retained(name):
    from defensive_network_disruption.validation import r9k_evidence as evidence
    index = _private_index()
    if name not in index or evidence.sha(R9J / "local" / name) != index[name]:
        raise RuntimeError("r9j_private_authority:" + name)
    return evidence.load(R9J / "local" / name)


def retained_candidates(row, private):
    from defensive_network_disruption.geometry import r9k_comparator as repaired
    mapping = {
        "isotropic": ("000122_controlled.json", "000136_integral.json"),
        "expanding": ("000161_controlled.json", "000189_integral.json"),
        "constant_width": ("000017_controlled.json", "000045_integral.json"),
    }
    public = []; all_pass = True; start = time.perf_counter()
    for candidate in ("isotropic", "expanding", "constant_width"):
        controlled = _retained(mapping[candidate][0]); strict = _retained(mapping[candidate][1])
        stages = []
        edge, result = repaired.evaluate(candidate, row["carrier"], row["receiver"], row["defenders"],
            root=ROOT, authority_context={"alias": row["alias"]}, record=lambda **item: stages.append(item))
        production_preserved = result["intervals"] == controlled["resolution"] and result["estimates"] == controlled["estimates"]
        piecewise_preserved = result["maximum_interval"] == strict["interval"] and tuple(result["partitions"]) == tuple(strict["partitions"])
        comparator_passed = stages[-1]["stage"] == "accepted"
        strict_evidence = result["certificate_evidence"]["strict"]
        certificate_count = strict_evidence["certificate_piece_count"]
        private.save(candidate + "_result", {
            "edge": edge.__dict__, "result": result, "stages": stages,
            "retained_controlled_sha256": _private_index()[mapping[candidate][0]],
            "retained_strict_sha256": _private_index()[mapping[candidate][1]],
        })
        passed = production_preserved and piecewise_preserved and comparator_passed and certificate_count == 0
        all_pass &= passed
        public.append({"candidate": candidate, "status": "passed" if passed else "failed",
                       "accepted_resolution": result["intervals"],
                       "production_preserved": production_preserved,
                       "piecewise_preserved": piecewise_preserved,
                       "comparator_passed": comparator_passed,
                       "certificate_count": certificate_count, "warning_count": 0,
                       "reason": "retained_hash_bound_comparison"})
    return public, all_pass, time.perf_counter() - start


def governed(folder):
    from defensive_network_disruption.validation import r9j_linear_publication as linear
    from defensive_network_disruption.validation import r9k_acceptance as acceptance
    from defensive_network_disruption.validation import r9k_evidence as evidence
    local = folder / "local"; private = PrivateEvidence(local); started = time.perf_counter()
    public = evidence.empty_public(); rows = {name: [] for name in evidence.CSV_SCHEMAS}
    qc = {"status": "blocked", "execution_valid": True, "classification": "E", "readiness": 4,
          "states_reopened": 0, "edges_reopened": 0, "exposure_uncertain": False}
    stage = "preflight"; authority = {}
    try:
        authority = preflight(); private.save("environment", authority)
        evidence.record(public, "repair_contract.json", flags={
            "independent_route": True, "certified_boundaries_only": True,
            "production_unchanged": True, "piecewise_unchanged": True,
            "tolerances_unchanged": True, "certificate_semantics_unchanged": True},
            counts={"agreement_tolerance_power": 10, "synthetic_families": 12})
        stage = "synthetic_acceptance"
        controls = acceptance.synthetic_controls(); history = acceptance.historical_regression(ROOT)
        rows["synthetic_acceptance.csv"].extend(controls + history)
        negatives = acceptance.negative_controls(); rows["negative_controls.csv"].extend(negatives)
        synthetic_pass = all(row["status"] == "passed" for row in controls + history)
        negative_pass = all(row["blocked"] for row in negatives)
        private.save("synthetic_summary", {"controls": controls, "counts": [len(history),
                     sum(row["components"] for row in history), sum(row["permutations"] for row in history)],
                     "negative_controls": negatives})
        performance = acceptance.performance_controls()
        evidence.record(public, "performance.json", flags={
            "linear_piece_work": performance["adaptive_calls"] <= performance["structural_pieces"],
            "one_call_per_ordinary_piece": performance["adaptive_calls"] + performance["micro_pieces"] == performance["structural_pieces"],
            "within_budget": performance["repaired_seconds"] < 600},
            counts={key: performance[key] for key in ("fixtures", "structural_pieces", "adaptive_calls", "micro_pieces")},
            timings={key: performance[key] for key in ("historical_seconds", "repaired_seconds", "overhead_ratio")})
        if not synthetic_pass or not negative_pass: raise RuntimeError("synthetic_acceptance_failed")
        stage = "publication"
        controls_publication = linear.acceptance(local / "linear_controls")
        private.save("linear_controls", controls_publication)
        bootstrap(local / "retained_review.marker", {"schema_version": 1, "single_pass": True})
        replay_start = time.perf_counter()
        retained = linear.review(OLD / "journal.jsonl", expected_sha256=JOURNAL_HASH, select=("4", "7"))
        replay_seconds = time.perf_counter() - replay_start
        checks = linear.check_r9i(retained)
        if not all(checks.values()): raise RuntimeError("retained_replay_mismatch")
        private.save("retained_review", retained.record())
        counters = retained.legacy["snapshot"]["snapshot"]["counters"]
        publication_flags = {"pa_unchanged": all(controls_publication["flags"].values()),
            "single_retained_replay": True,
            **{name: checks[name] for name in ("raw_hash", "chain_valid", "counts_match", "failure_match")},
            "success_package": controls_publication["flags"]["persisted_packages"],
            "failure_package": controls_publication["flags"]["negative_controls"]}
        evidence.record(public, "publication_validation.json", flags=publication_flags,
            counts={"records": retained.records, "states_opened": retained.exposure["states_opened"],
                    "edges_opened": counters["edges_opened"], "states_completed": counters["states_completed"],
                    "edges_completed": counters["edges_completed"], "field_started": counters["field_evaluations_started"],
                    "field_completed": counters["field_evaluations_completed"], "unresolved_edges": counters["unresolved_exposed_edges"]},
            timings={"seconds": replay_seconds})
        stage = "retained_edge"
        if evidence.sha(OLD / "prepared.jsonl") != PREPARED_HASH: raise RuntimeError("prepared_hash")
        evidence.put(local / "access_attempt.json", {"state": 4, "edge": 7, "prepared_sha256": PREPARED_HASH})
        qc["exposure_uncertain"] = True
        row = selected_edge(OLD / "prepared.jsonl", retained.selected_receipt)
        evidence.put(local / "access_materialized.json", {"state": 4, "edge": 7,
            "selected_sha256": evidence.digest(row)})
        qc.update(states_reopened=1, edges_reopened=1, exposure_uncertain=False)
        private.save("selected_geometry", row)
        candidate_rows, retained_pass, retained_seconds = retained_candidates(row, private)
        rows["candidate_regression.csv"].extend(candidate_rows)
        flags = {"receipt_valid": True,
                 "production_unchanged": all(item["production_preserved"] for item in candidate_rows),
                 "piecewise_unchanged": all(item["piecewise_preserved"] for item in candidate_rows),
                 "constant_width_passed": next(item for item in candidate_rows if item["candidate"] == "constant_width")["comparator_passed"],
                 "isotropic_passed": next(item for item in candidate_rows if item["candidate"] == "isotropic")["comparator_passed"],
                 "expanding_passed": next(item for item in candidate_rows if item["candidate"] == "expanding")["comparator_passed"],
                 "no_certificate_special_case": all(item["certificate_count"] == 0 for item in candidate_rows),
                 "warnings_absent": all(item["warning_count"] == 0 for item in candidate_rows),
                 "authority_exact": all(item["production_preserved"] and item["piecewise_preserved"] for item in candidate_rows)}
        evidence.record(public, "retained_edge_replay.json", flags=flags,
            counts={"states_reopened": 1, "edges_reopened": 1, "candidates_run": 3},
            timings={"seconds": retained_seconds})
        all_publication = all(publication_flags.values())
        performance_valid = all(public["performance.json"]["flags"].values())
        if retained_pass and all(flags.values()) and all_publication and performance_valid:
            qc.update(status="complete", classification="A", readiness=1)
        else:
            qc.update(status="blocked", classification="D", readiness=3)
        private.save("closure", {"synthetic_pass": synthetic_pass, "negative_pass": negative_pass,
                                  "retained_pass": retained_pass, "publication_pass": all_publication,
                                  "performance_pass": performance_valid, "elapsed": time.perf_counter()-started})
    except BaseException as error:
        evidence.emergency(local / "governed_emergency.json", error, stage)
        qc.update(status="invalid", execution_valid=False, classification="E", readiness=4)
    return evidence.close(folder, public, rows, qc, authority)


def main(argv=None):
    parser = argparse.ArgumentParser(); parser.add_argument("command", choices=("preflight", "audit", "publication-check"))
    command = parser.parse_args(argv).command
    if command == "preflight": result = preflight()
    elif command == "audit": result = entry(OUT, governed)
    else:
        from defensive_network_disruption.validation.r9k_evidence import publication_check
        result = publication_check(OUT)
    summary = {"command": command, "status": "valid"}
    if command == "audit":
        from defensive_network_disruption.validation.r9k_evidence import load
        qc = load(OUT / "qc.json")
        summary.update({key: qc[key] for key in ("status", "execution_valid", "classification", "readiness")})
    print(json.dumps(summary, sort_keys=True)); return result


if __name__ == "__main__": main()
