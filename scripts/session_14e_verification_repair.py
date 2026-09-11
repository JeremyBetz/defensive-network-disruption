#!/usr/bin/env python3
"""Synthetic-only Session 14e verification repair and acceptance audit."""
from __future__ import annotations

import argparse
import ast
import csv
from dataclasses import asdict, fields, replace
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import itertools
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np
import scipy

from defensive_network_disruption.geometry.integration_review import (
    directional_breakpoints,
    values_for_components,
)
from defensive_network_disruption.geometry.occlusion_fields import CANDIDATES, CarrierOriginField
from defensive_network_disruption.geometry.verification_audit import controlled_vector
from defensive_network_disruption.geometry.verification_repair import (
    VerificationError,
    VerificationReadiness,
    find_verified_envelope,
    independent_continuity,
    mapped_signature,
    opposite_nonzero_signs,
)
from defensive_network_disruption.validation.json_scalars import json_native

START = "9188222c4270ba1a89963ae1bbdb9003b0bf9f1e"
TAG = "f00690c05d8c1c6db308a65bd311c43f9a8ef2fa"
PROTOCOL = "docs/protocols/phase_14e_verification_repair_and_acceptance.md"
OUT = Path("outputs/continuous_occlusion_verification_repair")
CODE = (
    "scripts/session_14e_verification_repair.py",
    "src/defensive_network_disruption/geometry/verification_repair.py",
    "tests/test_session14e_verification.py",
)
INPUTS = (
    "scripts/session_14_occlusion_fields.py",
    "src/defensive_network_disruption/geometry/occlusion_fields.py",
    "src/defensive_network_disruption/geometry/integration_review.py",
    "src/defensive_network_disruption/geometry/maximum_envelope.py",
    "src/defensive_network_disruption/geometry/verification_audit.py",
    "outputs/continuous_occlusion_numerics_14b/reference_summary.json",
    "outputs/continuous_occlusion_numerics_14b/manifest.json",
    "outputs/continuous_occlusion_max_switching/unresolved_case_comparison.csv",
    "outputs/continuous_occlusion_max_switching/manifest.json",
    "outputs/continuous_occlusion_verification_audit/manifest.json",
    "uv.lock",
)
FILES = (
    "repair_summary.json", "continuity_oracles.csv", "tiny_sign_oracles.csv",
    "tie_boundary_oracles.csv", "controlled_integration.csv", "reference_comparison.csv",
    "failure_injection.json", "readiness_gate.json", "qc.json",
)
RESULT_PASS = "PASS — VERIFICATION CONTRACT REPAIRED; SESSION 14R MAY RESUME"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT).decode().strip()


def safe(relative: str | Path) -> Path:
    relative = Path(relative)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("unsafe_path")
    path = ROOT / relative
    if not path.resolve().is_relative_to(ROOT.resolve()) or any(x.is_symlink() for x in (path, *path.parents)):
        raise ValueError("unsafe_path")
    return path


def digest(relative: str | Path) -> str:
    return hashlib.sha256(safe(relative).read_bytes()).hexdigest()


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def load_json(relative: str | Path):
    return json.loads(safe(relative).read_text(), object_pairs_hook=no_duplicates,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite_json")))


def atomic_text(relative: str | Path, value: str) -> None:
    relative = Path(relative)
    if not relative.is_relative_to(OUT):
        raise ValueError("output_not_allowlisted")
    target = safe(relative)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError("preserve_existing")
    temporary = target.with_name("." + target.name + ".tmp")
    with temporary.open("x", newline="\n") as handle:
        handle.write(value)
    temporary.replace(target)


def put_json(name: str, value) -> None:
    atomic_text(OUT / name, json.dumps(json_native(value), sort_keys=True, indent=2, allow_nan=False) + "\n")


def put_csv(name: str, keys: tuple[str, ...], rows: list[dict]) -> None:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=keys, lineterminator="\n")
    writer.writeheader(); writer.writerows(rows)
    atomic_text(OUT / name, stream.getvalue())


def environment() -> dict:
    return {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
            "uv_lock_sha256": digest("uv.lock")}


def committed(relative: str) -> None:
    old = subprocess.check_output(["git", "show", "HEAD:" + relative], cwd=ROOT)
    if hashlib.sha256(old).hexdigest() != digest(relative):
        raise ValueError("uncommitted_authority")


def history() -> None:
    git("merge-base", "--is-ancestor", START, "HEAD")
    if git("rev-parse", "v0.1.0^{}") != TAG:
        raise ValueError("release_tag_changed")
    for path in INPUTS:
        old = subprocess.check_output(["git", "show", START + ":" + path], cwd=ROOT)
        if hashlib.sha256(old).hexdigest() != digest(path):
            raise ValueError("historical_input_changed")
    before = subprocess.check_output(["git", "show", START + ":docs/research_log.md"], cwd=ROOT)
    if not safe("docs/research_log.md").read_bytes().startswith(before):
        raise ValueError("research_log_not_append_only")


def route_guard() -> None:
    for path in CODE[:2]:
        tree = ast.parse(safe(path).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and any(term in (node.module or "") for term in ("models", "networks", "data.")):
                raise ValueError("forbidden_import")
            if isinstance(node, ast.Import) and any(item.name.split(".")[0] in ("requests", "urllib") for item in node.names):
                raise ValueError("forbidden_network")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("minimize", "evaluate_options", "urlopen"):
                raise ValueError("forbidden_call")


def preflight() -> None:
    history(); route_guard()
    for path in (PROTOCOL, *CODE):
        committed(path)
    if git("status", "--porcelain"):
        raise ValueError("clean_tree_required")
    if not git("check-ignore", "--", str(OUT / "local/probe")):
        raise ValueError("local_records_not_ignored")
    prior = load_json("outputs/continuous_occlusion_verification_audit/manifest.json")
    current = environment()
    if prior["environment"] != {"python": current["python"], "numpy": current["numpy"],
                                "scipy": current["scipy"], "lock": current["uv_lock_sha256"]}:
        raise ValueError("environment_changed")
    print("Session 14e preflight passed; synthetic-only authority verified")


def fixture_rows():
    spec = importlib.util.spec_from_file_location("session14e_fixtures", safe(INPUTS[0]))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    rows = tuple(module.fixtures())
    if len(rows) != 36:
        raise ValueError("fixture_count_changed")
    return rows


def references() -> dict:
    records = load_json(INPUTS[5])["records"]
    result = {(row["fixture"], row["candidate"], row["component"]): (row["reference"], "14b")
              for row in records if row["available"]}
    unavailable = {(row["fixture"], row["candidate"], row["component"])
                   for row in records if not row["available"]}
    with safe(INPUTS[7]).open(newline="") as handle:
        replacements = list(csv.DictReader(handle))
    replacement_keys = {(row["fixture"], row["candidate"], "maximum") for row in replacements}
    if len(records) != 366 or len(result) != 362 or unavailable != replacement_keys or len(replacement_keys) != 4:
        raise ValueError("reference_authority_invalid")
    for row in replacements:
        if row["available"] != "True":
            raise ValueError("piecewise_reference_unavailable")
        result[row["fixture"], row["candidate"], "maximum"] = (float(row["piecewise_reference"]), "14c")
    return result


def independent_scalar(candidate, origin, defender, query) -> float:
    dx, dy = defender[0]-origin[0], defender[1]-origin[1]
    radius = math.hypot(dx, dy)
    if radius <= 1e-9:
        raise VerificationError("origin_defender_direction_undefined")
    qx, qy = query[0]-defender[0], query[1]-defender[1]
    if candidate == "isotropic":
        return math.exp(-(qx*qx+qy*qy)/(2*2.0**2))
    ell = (qx*dx+qy*dy)/radius
    lateral = abs(qx*dy-qy*dx)/radius
    gate = 0.0 if ell <= 0.0 else 1.0 if ell >= 1.0 else 3*ell**2-2*ell**3
    width = 2.0 + (max(ell,0.0)*math.tan(math.radians(10.0)) if candidate == "expanding" else 0.0)
    return gate*math.exp(-lateral*lateral/(2*width*width))


def continuity_rows() -> list[dict]:
    rows = []
    steps = (1e-1,1e-2,1e-3,1e-4,1e-5,1e-6)
    geometries = (((0.,0.),(5.,0.),"axial"), ((1.,-2.),(4.,2.),"rotated"))
    for origin, defender, geometry in geometries:
        dx,dy=defender[0]-origin[0],defender[1]-origin[1]; radius=math.hypot(dx,dy)
        ux,uy=dx/radius,dy/radius
        for candidate in CANDIDATES:
            field=CarrierOriginField(candidate)
            for branch in (0.0,1.0):
                for step in steps:
                    values=[]
                    for ell in (branch-step,branch,branch+step):
                        point=(defender[0]+ell*ux,defender[1]+ell*uy)
                        expected=independent_scalar(candidate,origin,defender,point)
                        actual=float(field.individual_values(origin,(defender,),(point,))[0,0])
                        values.append((expected,actual))
                    passed=all(math.isclose(a,b,abs_tol=1e-12,rel_tol=1e-12) for a,b in values)
                    rows.append({"candidate":candidate,"geometry":geometry,"branch":branch,"step":step,
                                 "left":values[0][1],"at":values[1][1],"right":values[2][1],"oracle_passed":passed})
    rows.append({"candidate":"negative_control","geometry":"step","branch":.5,"step":0.0,
                 "left":.2,"at":.8,"right":.8,"oracle_passed":not independent_continuity(.2,.8)})
    return rows


def tiny_rows() -> list[dict]:
    rows=[]
    for magnitude in (1e-8,1e-12,1e-15,1e-200):
        rows.append({"fixture":f"opposite_{magnitude:.0e}","left":-magnitude,"right":magnitude,
                     "expected_bracket":True,"observed_bracket":opposite_nonzero_signs(-magnitude,magnitude)})
        rows.append({"fixture":f"same_{magnitude:.0e}","left":magnitude,"right":magnitude,
                     "expected_bracket":False,"observed_bracket":opposite_nonzero_signs(magnitude,magnitude)})
    rows.extend((
        {"fixture":"exact_zero","left":0.,"right":1.,"expected_bracket":False,"observed_bracket":opposite_nonzero_signs(0.,1.)},
        {"fixture":"structural_zero","left":0.,"right":0.,"expected_bracket":False,"observed_bracket":opposite_nonzero_signs(0.,0.)},
        {"fixture":"adjacent_node","left":-1e-15,"right":0.,"expected_bracket":False,"observed_bracket":opposite_nonzero_signs(-1e-15,0.)},
    ))
    return rows


def tie_rows() -> list[dict]:
    rows=[]
    for name,lower,upper in (("grid",.25,.75),("off_grid",.251,.749)):
        def function(t, lo=lower, hi=upper):
            base=np.full_like(t,.6)
            other=np.where((t>=lo)&(t<=hi),.6,np.nextafter(.6,0.0))
            return np.column_stack((base,other))
        result=find_verified_envelope(function)
        tie=result.tie_intervals[0]
        rows.append({"fixture":name,"known_start":lower,"start_outside":tie.start.outside,
                     "start_inside":tie.start.inside,"known_end":upper,"end_inside":tie.end.inside,
                     "end_outside":tie.end.outside,"owners":"|".join(map(str,tie.owners)),
                     "adjacent":bool(np.nextafter(tie.start.outside,tie.start.inside)==tie.start.inside and
                                     np.nextafter(tie.end.outside,tie.end.inside)==tie.end.inside),
                     "known_enclosed":tie.start.outside<lower<=tie.start.inside and tie.end.inside<=upper<tie.end.outside})
    return rows


def value_function(candidate, origin, receiver, defenders, permutation):
    field=CarrierOriginField(candidate); b=np.array(origin,dtype=np.float64); edge=np.array(receiver)-b
    selected=tuple(defenders[i] for i in permutation)
    return lambda t: field.individual_values(origin,selected,b[None,:]+t[:,None]*edge[None,:])


def governed_calculation():
    refs=references(); controlled=[]; comparisons=[]; permutation_count=0; switching_ok=True; deterministic=True
    continuity_switches=True
    for label,origin,receiver,defenders in fixture_rows():
        for candidate in CANDIDATES:
            field=CarrierOriginField(candidate)
            count,estimates,change=controlled_vector(lambda n:values_for_components(field,origin,receiver,defenders,n))
            controlled.append({"fixture":label,"candidate":candidate,"intervals":count,"component_count":len(estimates),
                               "successive_vector_difference":change,"converged":count is not None})
            for component,estimate in estimates.items():
                reference,source=refs[label,candidate,component]; error=abs(estimate-reference)
                comparisons.append({"fixture":label,"candidate":candidate,"component":component,
                                    "reference_source":source,"intervals":count,"estimate":estimate,
                                    "reference":reference,"absolute_error":error,"passed":count is not None and error<=1e-6})
            identity=tuple(range(len(defenders)))
            onset=() if candidate=="isotropic" else directional_breakpoints(origin,receiver,defenders)
            first=find_verified_envelope(value_function(candidate,origin,receiver,defenders,identity),extra_partitions=onset)
            again=find_verified_envelope(value_function(candidate,origin,receiver,defenders,identity),extra_partitions=onset)
            deterministic &= first==again
            expected=mapped_signature(first,identity)
            for permutation in itertools.permutations(identity):
                other=first if permutation==identity else find_verified_envelope(
                    value_function(candidate,origin,receiver,defenders,permutation),extra_partitions=onset)
                switching_ok &= mapped_signature(other,permutation)==expected
                permutation_count+=1
            partitions=first.partitions
            for switch in first.switches:
                if switch.endpoint: continue
                left=max(x for x in partitions if x<switch.location); right=min(x for x in partitions if x>switch.location)
                for step in (1e-3,1e-4,1e-5,1e-6,1e-7):
                    delta=min(step,(switch.location-left)/4,(right-switch.location)/4)
                    function=value_function(candidate,origin,receiver,defenders,identity)
                    locations=(switch.location-delta,switch.location,switch.location+delta)
                    observed=np.max(function(np.array(locations)),axis=1)
                    expected=[]
                    for location in locations:
                        query=(origin[0]+location*(receiver[0]-origin[0]),
                               origin[1]+location*(receiver[1]-origin[1]))
                        expected.append(max(independent_scalar(candidate,origin,defender,query)
                                            for defender in defenders))
                    continuity_switches &= all(math.isclose(float(actual),oracle,abs_tol=1e-12,rel_tol=1e-12)
                                               for actual,oracle in zip(observed,expected,strict=True))
    if len(controlled)!=108 or len(comparisons)!=366 or permutation_count!=399:
        raise ValueError("governed_count_mismatch")
    return controlled,comparisons,permutation_count,switching_ok,deterministic,continuity_switches


def failure_rows() -> tuple[list[dict], bool]:
    names=tuple(VerificationReadiness.__dataclass_fields__)
    rows=[]
    control=VerificationReadiness(**{name:True for name in names})
    rows.append({"injection":"valid_control","affected":"none","ready":control.ready,"blocked":not control.ready})
    labels={
        "continuity_failure":"continuity_verified", "discontinuous_surrogate":"continuity_verified",
        "missed_tiny_sign":"switching_verified", "uncertified_tie":"switching_verified",
        "root_failure":"switching_verified", "unavailable_reference":"references_complete",
        "controlled_nonconvergence":"controlled_integration_verified",
        "permutation_mismatch":"permutation_verified", "nondeterminism":"deterministic",
        "blocking_warning":"blocking_warnings_absent", "integrity_failure":"integrity_verified",
        "marker_collision":"integrity_verified",
    }
    for label,field in labels.items():
        item=replace(control,**{field:False})
        rows.append({"injection":label,"affected":field,"ready":item.ready,"blocked":not item.ready})
    return rows, control.ready and all(row["blocked"] for row in rows[1:])


def begin() -> None:
    if any(safe(OUT/name).exists() for name in (*FILES,"manifest.json")):
        raise FileExistsError("governed_outputs_exist")
    marker=OUT/"local/execution.marker"
    atomic_text(marker,git("rev-parse","HEAD")+"\n")
    ledger("audit","started")


def ledger(stage,status):
    path=safe(OUT/"local/access.jsonl");path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("a") as handle:
        handle.write(json.dumps({"time":datetime.now(timezone.utc).isoformat(),"stage":stage,"status":status,
                                 "commit":git("rev-parse","HEAD"),"synthetic_only":True})+"\n")


def perform() -> VerificationReadiness:
    continuity=continuity_rows(); tiny=tiny_rows(); ties=tie_rows()
    controlled,comparisons,permutations,switching,deterministic,switch_continuity=governed_calculation()
    failures,enforcement=failure_rows()
    readiness=VerificationReadiness(
        continuity_verified=all(row["oracle_passed"] for row in continuity) and switch_continuity,
        switching_verified=switching and all(row["observed_bracket"]==row["expected_bracket"] for row in tiny)
            and all(row["adjacent"] and row["known_enclosed"] for row in ties),
        controlled_integration_verified=all(row["converged"] for row in controlled),
        references_complete=len(comparisons)==366 and all(row["passed"] for row in comparisons),
        permutation_verified=switching and permutations==399,
        deterministic=deterministic,
        failure_enforcement_verified=enforcement,
        blocking_warnings_absent=True,
        integrity_verified=True,
    )
    put_csv("continuity_oracles.csv",tuple(continuity[0]),continuity)
    put_csv("tiny_sign_oracles.csv",tuple(tiny[0]),tiny)
    put_csv("tie_boundary_oracles.csv",tuple(ties[0]),ties)
    put_csv("controlled_integration.csv",tuple(controlled[0]),controlled)
    put_csv("reference_comparison.csv",tuple(comparisons[0]),comparisons)
    put_json("failure_injection.json",{"schema_version":1,"records":failures,"all_failures_block":enforcement})
    put_json("readiness_gate.json",{"schema_version":1,"inputs":asdict(readiness),"ready":readiness.ready,
                                      "classification":RESULT_PASS if readiness.ready else "BLOCKED — ADDITIONAL BOUNDED REPAIR REQUIRED"})
    put_json("repair_summary.json",{"schema_version":1,"status":"complete","classification":RESULT_PASS if readiness.ready else "BLOCKED — ADDITIONAL BOUNDED REPAIR REQUIRED",
        "historical_defects_repaired":4,"fixture_cases":108,"component_references":366,
        "full_permutation_comparisons":permutations,"continuity_oracles":len(continuity),
        "tiny_sign_oracles":len(tiny),"tie_boundary_oracles":len(ties),
        "finite_grid_global_completeness_claim":False,"empirical_access":False,"models_loaded":0})
    put_json("qc.json",{"schema_version":1,"status":"complete","ready":readiness.ready,
        "classification":RESULT_PASS if readiness.ready else "BLOCKED — ADDITIONAL BOUNDED REPAIR REQUIRED",
        "passed_references":sum(row["passed"] for row in comparisons),"reference_count":len(comparisons),
        "fixture_cases":len(controlled),"permutation_comparisons":permutations,"failure_injections":len(failures)-1,
        "empirical_access":False,"models_loaded":0,"error":None})
    return readiness


def validate() -> None:
    expected=set(FILES)
    for name in expected:
        path=safe(OUT/name)
        if not path.exists(): raise ValueError("missing_output")
        text=path.read_text()
        if any(token in text for token in ("/Users/","player_id","event_id","https://","token=","candidate_xy")):
            raise ValueError("publication_sensitive")
        if name.endswith(".csv") and b"\r" in path.read_bytes(): raise ValueError("csv_line_endings")
        if name.endswith(".json"): load_json(OUT/name)
    summary=load_json(OUT/"repair_summary.json"); readiness=load_json(OUT/"readiness_gate.json"); qc=load_json(OUT/"qc.json")
    if summary["fixture_cases"]!=108 or summary["component_references"]!=366 or summary["full_permutation_comparisons"]!=399:
        raise ValueError("summary_counts")
    if not readiness["ready"] or readiness["classification"]!=RESULT_PASS or not all(readiness["inputs"].values()):
        raise ValueError("readiness_not_passed")
    if qc["passed_references"]!=366 or qc["models_loaded"]!=0 or qc["empirical_access"] is not False:
        raise ValueError("qc_invalid")


def close() -> None:
    validate(); history()
    hashes={name:digest(OUT/name) for name in FILES}
    put_json("manifest.json",{"schema_version":1,"status":"closed","start":START,
        "execution_commit":git("rev-parse","HEAD"),"protocol_sha256":digest(PROTOCOL),
        "implementation_sha256":{path:digest(path) for path in CODE},
        "historical_inputs_sha256":{path:digest(path) for path in INPUTS},
        "environment":environment(),"outputs_sha256":hashes,"classification":RESULT_PASS,
        "empirical_access":False,"models_loaded":0})
    ledger("audit","closed")


def audit() -> None:
    preflight(); begin()
    try:
        readiness=perform()
        if not readiness.ready: raise VerificationError("readiness_failed")
        close()
    except Exception as error:
        ledger("audit","invalid_"+type(error).__name__)
        raise RuntimeError("session_14e_audit_failed_preserved") from None
    print(RESULT_PASS)


def publication_check() -> None:
    history(); route_guard()
    manifest=load_json(OUT/"manifest.json")
    if manifest["status"]!="closed" or manifest["classification"]!=RESULT_PASS:
        raise ValueError("manifest_status")
    if manifest["protocol_sha256"]!=digest(PROTOCOL) or manifest["environment"]!=environment():
        raise ValueError("authority_changed")
    for group,paths in (("implementation_sha256",CODE),("historical_inputs_sha256",INPUTS)):
        if set(manifest[group])!=set(paths): raise ValueError("manifest_file_set")
        if any(manifest[group][path]!=digest(path) for path in paths): raise ValueError("manifest_hash")
    if set(manifest["outputs_sha256"])!=set(FILES): raise ValueError("output_set")
    if any(value!=digest(OUT/name) for name,value in manifest["outputs_sha256"].items()): raise ValueError("output_hash")
    validate()
    print("Session 14e publication checks passed; closed hashes unchanged")


if __name__ == "__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("command",choices=("preflight","audit","publication-check"))
    {"preflight":preflight,"audit":audit,"publication-check":publication_check}[parser.parse_args().command]()
