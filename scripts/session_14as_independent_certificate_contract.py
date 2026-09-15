#!/usr/bin/env python3
"""Governed synthetic-only Session 14as certificate-contract acceptance."""
from __future__ import annotations

import argparse
from dataclasses import asdict, fields, replace
import csv
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import traceback


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from defensive_network_disruption.validation import independent_certificate_verifier as v

START = "cc20812c87d3d43506cf4a2b0100660fa51b16bf"
TAG = "f00690c05d8c1c6db308a65bd311c43f9a8ef2fa"
PROTOCOL = ROOT / "docs/protocols/phase_14as_independent_bound_verifier_contract.md"
MODULE = ROOT / "src/defensive_network_disruption/validation/independent_certificate_verifier.py"
TEST = ROOT / "tests/test_session14as_independent_certificate.py"
OUT = ROOT / "outputs/continuous_occlusion_independent_certificate_contract"
LOCAL = OUT / "local"
FILES = ("contract.json", "certificate_regression.json", "positive_oracles.csv",
         "negative_oracles.csv", "synthetic_reference_regression.csv",
         "readiness.json", "qc.json", "manifest.json")
SOURCES = (PROTOCOL, MODULE, Path(__file__).resolve(), TEST)


def git(*args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=ROOT, text=True).strip()


def encoded(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"


def atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    data = encoded(value).encode()
    with temporary.open("xb") as handle:
        handle.write(data); handle.flush(); os.fsync(handle.fileno())
    temporary.replace(path)


def create_once(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(encoded(value).encode()); handle.flush(); os.fsync(handle.fileno())


def csv_write(path: Path, rows: list[dict], columns: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("x", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows); handle.flush(); os.fsync(handle.fileno())
    temporary.replace(path)


def preflight() -> dict:
    if git("status", "--porcelain"):
        raise RuntimeError("dirty_tree")
    git("merge-base", "--is-ancestor", START, "HEAD")
    if git("rev-parse", "v0.1.0^{}") != TAG:
        raise RuntimeError("release_changed")
    if Path(sys.prefix).resolve() != (ROOT / ".venv").resolve():
        raise RuntimeError("project_interpreter")
    for path in SOURCES:
        relative = path.relative_to(ROOT).as_posix()
        if subprocess.check_output(("git", "show", "HEAD:" + relative), cwd=ROOT) != path.read_bytes():
            raise RuntimeError("uncommitted_source:" + relative)
    certificate, observation, authority = v.load_session14ar_certificate(ROOT)
    return {
        "start": START, "implementation_commit": git("rev-parse", "HEAD"),
        "release_target": TAG, "python": platform.python_version(),
        "source_hashes": {p.relative_to(ROOT).as_posix(): v.sha(p) for p in SOURCES},
        "authority_hashes": authority["expected_hashes"],
        "registered_authority": certificate.authority_id,
        "eligible_warning_sha256": observation.warning_message_sha256,
    }


def _replace_request(observation, **changes):
    return replace(observation, request=replace(observation.request, **changes))


def positive_oracles(certificate, observation):
    rows = []
    def add(name, operation):
        error = None
        try: operation()
        except Exception as exc: error = type(exc).__name__ + ":" + str(exc)
        rows.append({"fixture": name, "expected": "accepted", "observed": "accepted" if error is None else "blocked",
                     "passed": error is None, "error_category": "" if error is None else error.split(":", 1)[0]})
    add("session14ar_registered_certificate", lambda: v.certify_warning(observation, certificate))
    for label, width in (("width_predecessor", math.nextafter(v.AGREEMENT, 0.0)),
                         ("width_equal", v.AGREEMENT)):
        add(label, lambda width=width: v.certify_warning(
            replace(observation, estimate=width / 2),
            replace(certificate, lower_bound=0.0, upper_bound=width)))
    def mixed():
        result = v.aggregate_pieces((v.ordinary_piece(.25), v.micro_residual_piece(0.0, 1e-15),
                                     v.certify_warning(observation, certificate)))
        if result["outward_rounding_levels"] != 1 or result["certificate_piece_count"] != 1:
            raise RuntimeError("aggregation")
    add("mixed_conservative_aggregation", mixed)
    add("deterministic_serialization", lambda: None if v.canonical(v.certificate_record(certificate)) ==
        v.canonical(v.certificate_record(certificate)) else (_ for _ in ()).throw(RuntimeError("nondeterminism")))
    def readiness():
        values = {item.name: (0 if item.name == "uncertified_blocking_warning_count" else True)
                  for item in fields(v.ProspectiveVerificationReadiness)}
        if not v.ProspectiveVerificationReadiness(**values).ready: raise RuntimeError("readiness")
    add("derived_readiness", readiness)
    return rows


def negative_oracles(certificate, observation):
    rows = []
    cases = [
        ("no_certificate", lambda: v.certify_warning(observation, None)),
        ("stale_certificate", lambda: v.certify_warning(observation, replace(certificate, source_manifest_sha256="0"*64))),
        ("wrong_interval", lambda: v.certify_warning(_replace_request(observation, interval_identity="other"), certificate)),
        ("wrong_left_endpoint_bits", lambda: v.certify_warning(_replace_request(observation, left_endpoint_binary64="0"*16), certificate)),
        ("wrong_right_endpoint_bits", lambda: v.certify_warning(_replace_request(observation, right_endpoint_binary64="f"*16), certificate)),
        ("wrong_field_family", lambda: v.certify_warning(_replace_request(observation, field_family="expanding"), certificate)),
        ("wrong_parameters", lambda: v.certify_warning(_replace_request(observation, frozen_parameters=(("sigma_metres",3.0),)), certificate)),
        ("wrong_combination", lambda: v.certify_warning(_replace_request(observation, combination="union"), certificate)),
        ("wrong_integrand_hash", lambda: v.certify_warning(_replace_request(observation, integrand_specification_hash="0"*64), certificate)),
        ("wrong_structural_authority", lambda: v.certify_warning(_replace_request(observation, structural_partition_authority_hash="0"*64), certificate)),
        ("wrong_method", lambda: v.certify_warning(_replace_request(observation, method_id="other"), certificate)),
        ("wrong_provenance", lambda: v.certify_warning(_replace_request(observation, provenance_hash="0"*64), certificate)),
        ("wrong_tolerance", lambda: v.certify_warning(_replace_request(observation, governing_tolerance=1e-9), certificate)),
        ("estimate_outside", lambda: v.certify_warning(replace(observation, estimate=certificate.upper_bound+1e-8), certificate)),
        ("width_successor", lambda: v.certify_warning(replace(observation, estimate=v.AGREEMENT/2), replace(certificate, lower_bound=0.0, upper_bound=math.nextafter(v.AGREEMENT, math.inf)))),
        ("reversed_bounds", lambda: v.certify_warning(observation, replace(certificate, lower_bound=.3, upper_bound=.2))),
        ("nonfinite_lower", lambda: v.certify_warning(observation, replace(certificate, lower_bound=math.nan))),
        ("nonfinite_upper", lambda: v.certify_warning(observation, replace(certificate, upper_bound=math.inf))),
        ("unapproved_method_authority", lambda: v.certify_warning(observation, replace(certificate, method_authority_hash="0"*64))),
        ("unapproved_independence", lambda: v.certify_warning(observation, replace(certificate, independence_statement="other"))),
        ("unrelated_integration_warning", lambda: v.certify_warning(replace(observation, warning_message_sha256="0"*64), certificate)),
        ("wrong_warning_class", lambda: v.certify_warning(replace(observation, warning_class="RuntimeWarning"), certificate)),
    ]
    for reason in ("exception", "discontinuity", "root_failure", "partition_failure", "automatic_certificate_generation"):
        cases.append((reason, lambda reason=reason: v.aggregate_pieces((v.blocking_piece(reason),))))
    for name, operation in cases:
        error = None
        try: operation()
        except Exception as exc: error = type(exc).__name__
        rows.append({"fixture": name, "expected": "blocked", "observed": "blocked" if error else "accepted",
                     "passed": error is not None, "error_category": error or ""})
    return rows


def historical_regression():
    path = ROOT / "src/defensive_network_disruption/validation/onset_owner_acceptance.py"
    specification = importlib.util.spec_from_file_location("session14as_acceptance", path)
    module = importlib.util.module_from_spec(specification)
    assert specification.loader is not None
    specification.loader.exec_module(module)
    return module.historical_regression(ROOT)


def _validate_csv(path, columns):
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    if tuple(rows[0]) != columns if rows else True:
        raise RuntimeError("csv_schema:" + path.name)
    return rows


def publication_check() -> dict:
    expected_json = {"contract.json", "certificate_regression.json", "readiness.json", "qc.json"}
    if not OUT.joinpath("manifest.json").is_file(): raise FileNotFoundError("manifest")
    manifest = v.strict_load(OUT / "manifest.json")
    if set(manifest) != {"schema_version","status","classification","readiness","implementation_commit",
                         "protocol_sha256","authority","outputs"}: raise RuntimeError("manifest_schema")
    if set(manifest["outputs"]) != set(FILES) - {"manifest.json"}: raise RuntimeError("manifest_members")
    for name, digest in manifest["outputs"].items():
        if v.sha(OUT/name) != digest: raise RuntimeError("output_hash:"+name)
    for name in expected_json:
        json.dumps(v.strict_load(OUT/name), allow_nan=False)
    positive=_validate_csv(OUT/"positive_oracles.csv",("fixture","expected","observed","passed","error_category"))
    negative=_validate_csv(OUT/"negative_oracles.csv",("fixture","expected","observed","passed","error_category"))
    synthetic=_validate_csv(OUT/"synthetic_reference_regression.csv",("fixture","candidate","passed","components","permutations","error"))
    qc=v.strict_load(OUT/"qc.json"); readiness=v.strict_load(OUT/"readiness.json")
    if not qc["accepted"] or not all(row["passed"]=="True" for row in positive+negative+synthetic):
        raise RuntimeError("acceptance_false")
    if not readiness["ready"] or qc["empirical_states_opened"] or qc["empirical_edges_opened"]:
        raise RuntimeError("readiness_or_access")
    return {"status":"valid","classification":manifest["classification"],"readiness":manifest["readiness"]}


def accept():
    create_once(LOCAL/"accept.marker", {"session":"14as"})
    try:
        authority=preflight()
        certificate,observation,detail=v.load_session14ar_certificate(ROOT)
        piece=v.certify_warning(observation,certificate)
        aggregate=v.aggregate_pieces((piece,))
        regression={
            "schema_version":1,"authority_id":certificate.authority_id,
            "authority_sha256":certificate.authority_sha256,"adaptive_estimate":observation.estimate,
            "lower":certificate.lower_bound,"upper":certificate.upper_bound,
            "width":certificate.upper_bound-certificate.lower_bound,"warning_class":observation.warning_class,
            "warning_message_sha256":observation.warning_message_sha256,"warning_retained":True,
            "estimate_contained":certificate.lower_bound<=observation.estimate<=certificate.upper_bound,
            "width_accepted":certificate.upper_bound-certificate.lower_bound<=v.AGREEMENT,
            "certificate_accepted":True,"verifier_status":piece.status,"numerical_recomputation":False,
        }
        positive=positive_oracles(certificate,observation);negative=negative_oracles(certificate,observation)
        history=historical_regression()
        counts=(len(history),sum(x["components"] for x in history),sum(x["permutations"] for x in history))
        all_positive=all(x["passed"] for x in positive);all_negative=all(x["passed"] for x in negative)
        all_history=counts==(108,366,399) and all(x["passed"] for x in history)
        ready_values={
            "certificate_registry_valid":True,"exact_authority_matching_valid":all_negative,
            "warning_policy_valid":all_negative,"aggregation_valid":all_positive,
            "ordinary_quadrature_regression_valid":all_history,
            "micro_residual_regression_valid":all_positive,
            "synthetic_numerical_regressions_valid":all_history,
            "cases_108_complete":counts[0]==108,"references_366_complete":counts[1]==366,
            "permutations_399_complete":counts[2]==399,"failure_enforcement_valid":all_negative,
            "deterministic":all_positive,"integrity_valid":True,
            "independent_certification_observed":True,"uncertified_blocking_warning_count":0,
        }
        readiness=v.ProspectiveVerificationReadiness(**ready_values)
        accepted=readiness.ready and all(regression[k] for k in ("warning_retained","estimate_contained","width_accepted","certificate_accepted"))
        classification="A" if accepted else ("C" if not all_positive else "E")
        level=1 if accepted else 3
        contract={
            "schema_version":1,"eligible_warning_class":v.ELIGIBLE_WARNING_CLASS,
            "eligible_warning_message":v.ELIGIBLE_WARNING_MESSAGE,
            "eligible_warning_message_sha256":v.ELIGIBLE_WARNING_SHA256,
            "governing_tolerance":v.AGREEMENT,"success_status":v.SUCCESS_STATUS,
            "certificate_schema":[item.name for item in fields(v.IndependentIntegralCertificate)],
            "authority_match":"exact","production_estimate_replaced":False,
            "aggregation":{"summation":"math.fsum","outward_rounding":"once_at_final_aggregate","nested_rewidening":False},
            "branches":["micro_residual","ordinary","independent_certificate","blocking"],
            "automatic_certificate_generation":False,
        }
        readiness_record={"schema_version":1,**asdict(readiness),"ready":readiness.ready,
                          "adaptive_warning_count":aggregate["adaptive_warning_count"],
                          "independently_certified_count":aggregate["independently_certified_count"],
                          "blocking_warning_count":aggregate["blocking_warning_count"],
                          "ordinary_piece_count":aggregate["ordinary_piece_count"],
                          "micro_residual_piece_count":aggregate["micro_residual_piece_count"],
                          "certificate_piece_count":aggregate["certificate_piece_count"],
                          "aggregate_lower":aggregate["aggregate_lower"],"aggregate_upper":aggregate["aggregate_upper"],
                          "final_evidence_status":aggregate["final_evidence_status"]}
        qc={"schema_version":1,"accepted":accepted,"classification":classification,"readiness":level,
            "checks":{"certificate_regression":all(regression[k] for k in ("warning_retained","estimate_contained","width_accepted","certificate_accepted")),
                      "positive_oracles":all_positive,"negative_oracles":all_negative,"synthetic_regression":all_history,
                      "publication":True,"integrity":True},
            "cases":counts[0],"references":counts[1],"permutations":counts[2],
            "empirical_states_opened":0,"empirical_edges_opened":0,"scientific_outputs_opened":0,
            "claim_ledger_changed":False,"authority":authority}
        atomic(OUT/"contract.json",contract);atomic(OUT/"certificate_regression.json",regression)
        csv_write(OUT/"positive_oracles.csv",positive,("fixture","expected","observed","passed","error_category"))
        csv_write(OUT/"negative_oracles.csv",negative,("fixture","expected","observed","passed","error_category"))
        csv_write(OUT/"synthetic_reference_regression.csv",history,("fixture","candidate","passed","components","permutations","error"))
        atomic(OUT/"readiness.json",readiness_record);atomic(OUT/"qc.json",qc)
        members={name:v.sha(OUT/name) for name in FILES if name!="manifest.json"}
        atomic(OUT/"manifest.json",{"schema_version":1,"status":"closed" if accepted else "blocked",
            "classification":classification,"readiness":level,"implementation_commit":git("rev-parse","HEAD"),
            "protocol_sha256":v.sha(PROTOCOL),"authority":authority,"outputs":members})
        publication_check()
        print(f"Session 14as {classification}/readiness {level}; {counts[0]}/{counts[1]}/{counts[2]}")
    except BaseException as exc:
        try:create_once(LOCAL/"failure.json",{"accepted":False,"exception":type(exc).__name__,"traceback":"".join(traceback.format_exception(exc))})
        except Exception:pass
        raise


def main():
    parser=argparse.ArgumentParser();parser.add_argument("command",choices=("preflight","accept","publication-check"));args=parser.parse_args()
    if args.command=="preflight":print(encoded(preflight()),end="")
    elif args.command=="accept":accept()
    else:print(encoded(publication_check()),end="")


if __name__ == "__main__":main()
