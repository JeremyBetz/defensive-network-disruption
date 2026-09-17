#!/usr/bin/env python3
"""Fresh one-shot Session 14R9I empirical execution wrapper."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback


ROOT = Path(__file__).resolve().parents[1]
START = "7246f3d8638b1d15b4d55c2432695fcce38f754c"
TAG = "f00690c05d8c1c6db308a65bd311c43f9a8ef2fa"
PROTOCOL = Path("docs/protocols/phase_14r9i_empirical_execution.md")
OUT = Path("outputs/continuous_occlusion_empirical_retry_r9i")
LOCAL = OUT / "local"
FIXTURE = Path("tests/authority_fixtures/session14r9e_certificate_authority.json")
TEST_COMMAND = ("-m", "unittest", "discover", "-s", "tests",
                "-p", "test_session14r9i.py")

INHERITED_AUTHORITY = {
    "outputs/continuous_occlusion_empirical_retry_r9/manifest.json":
        "4673ac2a12847f4b52944e5913ed3b7c8df9fb29f83a19696b40c259b0819d87",
    "outputs/continuous_occlusion_empirical_retry_r9/synthetic_acceptance.json":
        "05ca51d437f71615d2856c59ffd97be0ba57b83a9eb5ddfba47cf66c4a0b2255",
    "outputs/continuous_occlusion_empirical_retry_r9/synthetic_stress_summary.json":
        "1d6c1c86c4bde130508030c1d371fc3f69e3860209ca416c81bf41557a8cd550",
    "outputs/continuous_occlusion_empirical_retry_r9/visual_qa.json":
        "3a14eeaa10bdcb68b8eec555408645d3357c8ee23ce3f082f3fa9b50367cdc55",
    "outputs/continuous_occlusion_empirical_retry_r9/synthetic_field_comparison.svg":
        "8ddd9b97223927bfa3f5ebf36c7123d8b85e154fb67f683cd2f598b675c9128f",
    "outputs/continuous_occlusion_empirical_retry_r9a/manifest.json":
        "39ba0732240483c54593cdb99aa010b3d55e953b9ba0cfe6e6e82219255df8e4",
    "outputs/continuous_occlusion_empirical_retry_r9a/revalidation.json":
        "30e4fe81bcc9806f0cf6417e719f9a7d17c45d7a706e94b08d8cb0b82c9fe2f4",
    "outputs/continuous_occlusion_ci_portability/manifest.json":
        "502be83251b2222f386ac4c49483782e6549589eb3efbfcf94c0b91aef75d859",
    FIXTURE.as_posix():
        "84357ed8cee08b6452fe146bcd97eb5a2d3166910aba86e46f2768f358be85f9",
    "outputs/continuous_occlusion_runner_authority_context/manifest.json":
        "9a93eab00654015332c7e19d374f825fa9286b2183e89a379efc4011f78443f4",
    "outputs/continuous_occlusion_independent_certificate_contract/manifest.json":
        "e1902366a0761b097aa49af2052892b58b14dd7914f8b53aa26f875c9603c0f2",
    "outputs/continuous_occlusion_terminal_interval_reference/manifest.json":
        "bb3d352e9b43b579f897e36f4f000f3fb770701fe11877f23af76a36668d97b4",
    "docs/session_14r9h_runner_authority_context.md":
        "b7a9c0443f6df96eff1fab00956a6a665d44510834fd6bb137a0d9fdd246ea6d",
    "docs/session_14r9f_ci_portable_authority_fixtures.md":
        "d307e1bf53af4ce25774f7ae044219c91c6fc39bea8d328599f94c1b861eadd9",
    "docs/session_14r9a_publication_contract_reconciliation.md":
        "46dd153c642a0ef092ea252c3092ec9a22c3e9de341321fbd02c9449f380cd48",
    "docs/session_14as_independent_bound_verifier_contract.md":
        "feb2a8ded114d326f95e8152f1f9e14bf1b9ee34f322a72e0f1fd493a10ed2f2",
    "docs/session_14ar_terminal_interval_reference.md":
        "f651d86aae81770eb936fcbf6be975766e6ae46b241fd019d884b8222580e184",
}

FROZEN_IMPLEMENTATION = {
    "scripts/session_14r9e_empirical_execution.py":
        "16e009e9a11d86c6ad6da10d8316c629abbcb9f69361f8ff62a85b5cfc66ea99",
    "scripts/session_14r9_occlusion_study.py":
        "21d7cb219fcef9884700e119d15e2c9e131fb08485d1d1ed8d271b434cbb7912",
    "src/defensive_network_disruption/geometry/r9e_representation.py":
        "98f5f672f7da85b565a4c3b784ccecf6d4635554de684aaba4891f5ec0bb40d8",
    "src/defensive_network_disruption/geometry/production_verification.py":
        "6d4eeddf0c7537ecbea027e1c308e4f573b2cf0f4bb71a0b3b839e2382f75a6c",
    "src/defensive_network_disruption/geometry/micro_interval_verifier.py":
        "55389fd78d7c546bb1b4c830cdb434932fce6f67dcc8042a2427e44dc77c2b0e",
    "src/defensive_network_disruption/geometry/occlusion_fields.py":
        "d7fd23bc131d0db2686ef27475a128fdca78aea88616c4494609962c165533aa",
    "src/defensive_network_disruption/validation/r9e_publication.py":
        "77ec96e2fcd547df1dbd7d093f4a59fef4919cf67fbca8f597555a05257590c3",
    "src/defensive_network_disruption/validation/r9f_portable_authority.py":
        "b85f7ba84b5843d676fa2deb316ec16088f1b418247c26ede6fe585075448497",
    "src/defensive_network_disruption/validation/r9_certificate_orchestration.py":
        "64268899b3e6f146e033dfe78f424d589dedc1101253e27d2b442f36e0f5a66a",
    "src/defensive_network_disruption/validation/independent_certificate_verifier.py":
        "be73a070e4dc290d2697f98146f495a9f4a05dfcf9b256ca57b255414e337789",
}

CODE = (
    "scripts/session_14r9i_empirical_execution.py",
    "scripts/session_14r9e_empirical_execution.py",
    "src/defensive_network_disruption/geometry/r9e_representation.py",
    "src/defensive_network_disruption/validation/r9e_publication.py",
    "src/defensive_network_disruption/validation/r9f_portable_authority.py",
    "tests/test_session14r9i.py",
)


def _safe(path: Path) -> Path:
    target = ROOT / path
    if (any(item.is_symlink() for item in (target, *target.parents)) or
            not target.resolve().is_relative_to(ROOT.resolve())):
        raise PermissionError("unsafe_path")
    return target


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with _safe(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1_048_576), b""):
            digest.update(block)
    return digest.hexdigest()


def _atomic(path: Path, value: object) -> None:
    target = _safe(path)
    if target.exists():
        raise FileExistsError("immutable_record_exists:" + target.name)
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False) + "\n").encode()
    pending = target.with_name("." + target.name + ".pending")
    with pending.open("xb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    os.link(pending, target)
    pending.unlink()


def _load_base():
    sys.path.insert(0, str(ROOT / "src"))
    spec = importlib.util.spec_from_file_location(
        "session14r9i_frozen_r9e", ROOT / "scripts/session_14r9e_empirical_execution.py")
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise ImportError("r9e_loader_unavailable")
    spec.loader.exec_module(module)
    module.START = START
    module.TAG = TAG
    module.PROTOCOL = PROTOCOL
    module.OUT = OUT
    module.LOCAL = LOCAL
    module.TEST_COMMAND = TEST_COMMAND
    module.CODE = CODE
    module.HISTORICAL = {
        **module.HISTORICAL,
        **INHERITED_AUTHORITY,
        **FROZEN_IMPLEMENTATION,
    }
    return module


def verify_frozen_authority() -> dict:
    for name, expected in {**INHERITED_AUTHORITY, **FROZEN_IMPLEMENTATION}.items():
        if _sha(Path(name)) != expected:
            raise RuntimeError("r9i_authority_changed:" + name)
    fixture = json.loads(_safe(FIXTURE).read_text())
    if (fixture.get("authority_id") != "session14ar_terminal_interval_8" or
            fixture.get("semantic_projection_sha256") !=
            "b6e853d6cf3c97da328f4292a334b60e12ec98dfe624ad9602f04363008f0a2a"):
        raise RuntimeError("portable_fixture_authority")
    acceptance = json.loads(_safe(Path(
        "outputs/continuous_occlusion_empirical_retry_r9/synthetic_acceptance.json")).read_text())
    if (acceptance.get("cases"), acceptance.get("references"),
            acceptance.get("permutations"), acceptance.get("passed")) != (108, 366, 399, True):
        raise RuntimeError("inherited_acceptance_status")
    visual = json.loads(_safe(Path(
        "outputs/continuous_occlusion_empirical_retry_r9/visual_qa.json")).read_text())
    if visual.get("status") != "approved" or not visual.get("byte_identical"):
        raise RuntimeError("inherited_visual_status")
    return {
        "authority_count": len(INHERITED_AUTHORITY),
        "implementation_count": len(FROZEN_IMPLEMENTATION),
        "fixture_sha256": INHERITED_AUTHORITY[FIXTURE.as_posix()],
        "r9h_manifest_sha256": INHERITED_AUTHORITY[
            "outputs/continuous_occlusion_runner_authority_context/manifest.json"],
        "acceptance": {"cases": 108, "references": 366, "permutations": 399},
        "visual_inherited": True,
    }


def preflight(base=None) -> dict:
    base = _load_base() if base is None else base
    authority = verify_frozen_authority()
    result = base.preflight()
    marker = _safe(LOCAL / "preaccess.marker")
    if marker.exists():
        raise FileExistsError("fresh_marker_exists:preaccess.marker")
    return {**result, "schema_version": 2, "session": "14R9I",
            "frozen_authority": authority, "empirical_access_authorized": False}


def run(base=None) -> None:
    base = _load_base() if base is None else base
    stage = "r9i_startup"
    try:
        authority = preflight(base)
        _atomic(LOCAL / "preaccess.marker", {
            "schema_version": 1,
            "status": "reserved",
            "head": subprocess.check_output(
                ("git", "rev-parse", "HEAD"), cwd=ROOT, text=True).strip(),
            "authority_sha256": hashlib.sha256(json.dumps(
                authority, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        })
        stage = "r9i_empirical_execution"
        base.run()
        stage = "r9i_final_package_verification"
        receipt = base.publication_check()
        _atomic(LOCAL / "final_validator_receipt.json", receipt)
        print("R9I empirical execution closed and publication validated")
    except BaseException as error:
        emergency = LOCAL / "r9i_emergency_failure.json"
        if not _safe(emergency).exists():
            _atomic(emergency, {
                "schema_version": 1,
                "status": "failure",
                "stage": stage,
                "exception": type(error).__name__,
                "traceback": "".join(traceback.format_exception(error)),
            })
        raise


def publication_check(base=None) -> dict:
    base = _load_base() if base is None else base
    receipt = base.publication_check()
    saved = json.loads(_safe(LOCAL / "final_validator_receipt.json").read_text())
    if receipt != saved:
        raise RuntimeError("final_validator_receipt_mismatch")
    if receipt.get("artifact_count") != 19 or receipt.get("status") != "valid":
        raise RuntimeError("final_validator_receipt_invalid")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("preflight", "run", "publication-check"))
    command = parser.parse_args().command
    try:
        base = _load_base()
        if command == "preflight":
            print(json.dumps(preflight(base), sort_keys=True, allow_nan=False))
        elif command == "run":
            run(base)
        else:
            print(json.dumps(publication_check(base), sort_keys=True, allow_nan=False))
    except BaseException as error:
        if command == "run":
            emergency = LOCAL / "r9i_import_failure.json"
            if not _safe(emergency).exists():
                _atomic(emergency, {
                    "schema_version": 1,
                    "status": "failure",
                    "stage": "startup_or_import",
                    "exception": type(error).__name__,
                    "traceback": "".join(traceback.format_exception(error)),
                })
        raise


if __name__ == "__main__":
    main()
