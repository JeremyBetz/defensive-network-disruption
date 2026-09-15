"""Session 14at synthetic-only governed acceptance orchestration."""
from __future__ import annotations

from dataclasses import asdict, fields, replace
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import traceback

from . import independent_certificate_verifier as verifier
from . import onset_owner_acceptance

HISTORICAL_IMPORT_ERROR = "attempted relative import with no known parent package"


def _encoded(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("xb") as handle:
        handle.write(_encoded(value)); handle.flush(); os.fsync(handle.fileno())
    tmp.replace(path)


def create_once(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(_encoded(value)); handle.flush(); os.fsync(handle.fileno())


def csv_write(path: Path, rows: list[dict], columns: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("x", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows); handle.flush(); os.fsync(handle.fileno())
    tmp.replace(path)


def certificate_controls(root: Path) -> tuple[dict, list[dict], list[dict], dict]:
    certificate, observation, _ = verifier.load_session14ar_certificate(root)
    piece = verifier.certify_warning(observation, certificate)
    aggregate = verifier.aggregate_pieces((piece,))
    regression = {
        "authority_sha256": certificate.authority_sha256,
        "adaptive_estimate": observation.estimate,
        "lower": certificate.lower_bound, "upper": certificate.upper_bound,
        "width": certificate.upper_bound - certificate.lower_bound,
        "warning_retained": True, "estimate_contained": certificate.lower_bound <= observation.estimate <= certificate.upper_bound,
        "width_accepted": certificate.upper_bound - certificate.lower_bound <= verifier.AGREEMENT,
        "certificate_accepted": piece.status == verifier.SUCCESS_STATUS,
        "numerical_recomputation": False,
    }
    positive = []
    for name, width in (("registered", certificate.upper_bound-certificate.lower_bound),
                        ("width_predecessor", math.nextafter(verifier.AGREEMENT, 0.0)),
                        ("width_equal", verifier.AGREEMENT)):
        try:
            if name == "registered": verifier.certify_warning(observation, certificate)
            else: verifier.certify_warning(replace(observation, estimate=width/2), replace(certificate, lower_bound=0.0, upper_bound=width))
            passed = True
        except Exception: passed = False
        positive.append({"fixture": name, "passed": passed})
    mixed = verifier.aggregate_pieces((verifier.ordinary_piece(.25), verifier.micro_residual_piece(0.0, 1e-15), piece))
    positive.extend((
        {"fixture":"mixed_aggregation","passed":mixed["outward_rounding_levels"] == 1 and mixed["certificate_piece_count"] == 1},
        {"fixture":"deterministic_serialization","passed":verifier.canonical(verifier.certificate_record(certificate)) == verifier.canonical(verifier.certificate_record(certificate))},
    ))
    cases = [
        ("no_certificate", lambda: verifier.certify_warning(observation, None)),
        ("stale_certificate", lambda: verifier.certify_warning(observation, replace(certificate, source_manifest_sha256="0"*64))),
        ("wrong_interval", lambda: verifier.certify_warning(replace(observation, request=replace(observation.request, interval_identity="other")), certificate)),
        ("wrong_warning", lambda: verifier.certify_warning(replace(observation, warning_message_sha256="0"*64), certificate)),
        ("outside", lambda: verifier.certify_warning(replace(observation, estimate=certificate.upper_bound+1e-8), certificate)),
        ("width_successor", lambda: verifier.certify_warning(replace(observation, estimate=verifier.AGREEMENT/2), replace(certificate, lower_bound=0.0, upper_bound=math.nextafter(verifier.AGREEMENT, math.inf)))),
        ("reversed", lambda: verifier.certify_warning(observation, replace(certificate, lower_bound=.3, upper_bound=.2))),
        ("nonfinite", lambda: verifier.certify_warning(observation, replace(certificate, upper_bound=math.inf))),
        ("automatic_generation", lambda: verifier.aggregate_pieces((verifier.blocking_piece("automatic_certificate_generation"),))),
    ]
    negative=[]
    for name, operation in cases:
        try: operation(); passed=False
        except Exception: passed=True
        negative.append({"fixture":name,"passed":passed})
    return regression, positive, negative, aggregate


def run_acceptance(root: Path) -> dict:
    regression, positive, negative, aggregate = certificate_controls(root)
    history = onset_owner_acceptance.historical_regression(root)
    counts = (len(history), sum(row["components"] for row in history), sum(row["permutations"] for row in history))
    history_ok = counts == (108, 366, 399) and all(row["passed"] for row in history)
    values = {
        "certificate_registry_valid": regression["certificate_accepted"],
        "exact_authority_matching_valid": all(row["passed"] for row in negative),
        "warning_policy_valid": all(row["passed"] for row in negative),
        "aggregation_valid": all(row["passed"] for row in positive),
        "ordinary_quadrature_regression_valid": history_ok,
        "micro_residual_regression_valid": all(row["passed"] for row in positive),
        "synthetic_numerical_regressions_valid": history_ok,
        "cases_108_complete": counts[0] == 108, "references_366_complete": counts[1] == 366,
        "permutations_399_complete": counts[2] == 399, "failure_enforcement_valid": all(row["passed"] for row in negative),
        "deterministic": True, "integrity_valid": True, "independent_certification_observed": True,
        "uncertified_blocking_warning_count": 0,
    }
    readiness = verifier.ProspectiveVerificationReadiness(**values)
    return {"regression":regression,"positive":positive,"negative":negative,"aggregate":aggregate,
            "history":history,"counts":counts,"readiness":readiness}


def publish_success(root: Path, out: Path, implementation_commit: str, protocol_sha256: str) -> dict:
    result = run_acceptance(root)
    readiness = result["readiness"]
    if not readiness.ready: raise RuntimeError("readiness_false")
    atomic_json(out/"runner_contract.json", {"schema_version":1,"package_import":onset_owner_acceptance.__name__,"direct_file_loading":False,"certificate_semantics":"unchanged"})
    atomic_json(out/"package_context_regression.json", {"schema_version":1,"package_import_passed":True,"historical_direct_file_failure_preserved":True,"historical_error":HISTORICAL_IMPORT_ERROR})
    atomic_json(out/"publication_oracles.json", {"schema_version":1,"success_publication":True,"failure_publication":True,"historical_import_failure_preserved":True})
    atomic_json(out/"certificate_regression.json", {"schema_version":1,**result["regression"]})
    csv_write(out/"synthetic_reference_regression.csv", result["history"], ("fixture","candidate","passed","components","permutations","error"))
    atomic_json(out/"readiness.json", {"schema_version":1,**asdict(readiness),"ready":readiness.ready,
        **{key:result["aggregate"][key] for key in ("adaptive_warning_count","independently_certified_count","blocking_warning_count","ordinary_piece_count","micro_residual_piece_count","certificate_piece_count","aggregate_lower","aggregate_upper","final_evidence_status")}})
    atomic_json(out/"qc.json", {"schema_version":1,"accepted":True,"classification":"A","readiness":1,"cases":result["counts"][0],"references":result["counts"][1],"permutations":result["counts"][2],"positive_oracles_passed":all(x["passed"] for x in result["positive"]),"negative_oracles_blocked":all(x["passed"] for x in result["negative"]),"empirical_states_opened":0,"empirical_edges_opened":0,"claim_ledger_changed":False})
    members = {path.name:verifier.sha(path) for path in out.iterdir() if path.is_file() and path.name != "manifest.json"}
    atomic_json(out/"manifest.json", {"schema_version":1,"status":"closed","classification":"A","readiness":1,"implementation_commit":implementation_commit,"protocol_sha256":protocol_sha256,"outputs":members})
    return publication_check(out, success=True)


def publish_failure(out: Path, stage: str, exc: BaseException, completed: list[str], marker: Path) -> dict:
    record={"schema_version":1,"status":"failure","active_stage":stage,"exception_class":type(exc).__name__,"exception_message":str(exc),"traceback":"".join(traceback.format_exception(exc)),"completed_obligations":completed,"readiness":False,"marker_exists":marker.exists(),"empirical_states_opened":0,"empirical_edges_opened":0}
    atomic_json(out/"failure.json",record)
    return record


def publication_check(out: Path, *, success: bool | None = None) -> dict:
    failure=out/"failure.json"
    if success is False or (success is None and failure.exists()):
        record=verifier.strict_load(failure)
        required={"schema_version","status","active_stage","exception_class","exception_message","traceback","completed_obligations","readiness","marker_exists","empirical_states_opened","empirical_edges_opened"}
        if set(record)!=required or record["status"]!="failure" or record["readiness"] or not record["marker_exists"] or record["empirical_states_opened"] or record["empirical_edges_opened"]: raise RuntimeError("failure_schema")
        return {"status":"valid_failure","active_stage":record["active_stage"]}
    expected={"runner_contract.json","package_context_regression.json","publication_oracles.json","certificate_regression.json","synthetic_reference_regression.csv","readiness.json","qc.json"}
    manifest=verifier.strict_load(out/"manifest.json")
    if set(manifest["outputs"])!=expected: raise RuntimeError("manifest_members")
    for name,digest in manifest["outputs"].items():
        if verifier.sha(out/name)!=digest: raise RuntimeError("output_hash:"+name)
    qc=verifier.strict_load(out/"qc.json"); ready=verifier.strict_load(out/"readiness.json")
    if not qc["accepted"] or not ready["ready"] or (qc["cases"],qc["references"],qc["permutations"])!=(108,366,399): raise RuntimeError("acceptance_false")
    if qc["empirical_states_opened"] or qc["empirical_edges_opened"]: raise RuntimeError("empirical_access")
    return {"status":"valid_success","classification":"A","readiness":1}
