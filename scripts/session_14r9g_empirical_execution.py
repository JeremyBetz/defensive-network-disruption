#!/usr/bin/env python3
"""Fresh Session 14R9G execution over the frozen R9E implementation."""
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
OUT = Path("outputs/continuous_occlusion_empirical_retry_r9g")
LOCAL = OUT / "local"
PROTOCOL = Path("docs/protocols/phase_14r9g_empirical_execution.md")
START = "c54d20121ea6107728f82759d82a2444be67ce6a"
TAG = "f00690c05d8c1c6db308a65bd311c43f9a8ef2fa"
FIXTURE = Path("tests/authority_fixtures/session14r9e_certificate_authority.json")
FIXTURE_SHA256 = "84357ed8cee08b6452fe146bcd97eb5a2d3166910aba86e46f2768f358be85f9"
R9F_AUTHORITY = {
    "outputs/continuous_occlusion_ci_portability/manifest.json":
        "502be83251b2222f386ac4c49483782e6549589eb3efbfcf94c0b91aef75d859",
    "docs/session_14r9f_ci_portable_authority_fixtures.md":
        "d307e1bf53af4ce25774f7ae044219c91c6fc39bea8d328599f94c1b861eadd9",
    "src/defensive_network_disruption/validation/r9f_portable_authority.py":
        "b85f7ba84b5843d676fa2deb316ec16088f1b418247c26ede6fe585075448497",
    FIXTURE.as_posix(): FIXTURE_SHA256,
}
CODE = (
    "scripts/session_14r9g_empirical_execution.py",
    "scripts/session_14r9e_empirical_execution.py",
    "src/defensive_network_disruption/geometry/r9e_representation.py",
    "src/defensive_network_disruption/validation/r9e_publication.py",
    "src/defensive_network_disruption/validation/r9f_portable_authority.py",
    FIXTURE.as_posix(),
    "tests/test_session14r9g.py",
)
TEST_COMMAND = ("-m", "unittest", "discover", "-s", "tests",
                "-p", "test_session14r9g.py")


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
        "session14r9g_frozen_r9e", ROOT / "scripts/session_14r9e_empirical_execution.py")
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
    module.HISTORICAL = {**module.HISTORICAL, **R9F_AUTHORITY}
    return module


def _verify_fixture(base) -> dict:
    if _sha(FIXTURE) != FIXTURE_SHA256:
        raise RuntimeError("portable_fixture_bytes_changed")
    from defensive_network_disruption.validation import r9f_portable_authority
    fixture = r9f_portable_authority.load_fixture(ROOT)
    if fixture["semantic_projection_sha256"] != (
            "b6e853d6cf3c97da328f4292a334b60e12ec98dfe624ad9602f04363008f0a2a"):
        raise RuntimeError("portable_fixture_semantics_changed")
    return {"path": FIXTURE.as_posix(), "sha256": FIXTURE_SHA256,
            "authority_id": fixture["authority_id"],
            "non_reconstructive": True, "private_fallback": False}


def preflight(base=None) -> dict:
    base = _load_base() if base is None else base
    result = base.preflight()
    result["portable_fixture"] = _verify_fixture(base)
    if _safe(LOCAL / "preaccess.marker").exists():
        raise FileExistsError("fresh_marker_exists:preaccess.marker")
    result["schema_version"] = 2
    result["session"] = "14R9G"
    return result


def run(base=None) -> None:
    base = _load_base() if base is None else base
    stage = "r9g_startup"
    try:
        authority = preflight(base)
        _atomic(LOCAL / "preaccess.marker", {
            "schema_version": 1, "status": "reserved",
            "head": subprocess.check_output(("git", "rev-parse", "HEAD"),
                                            cwd=ROOT, text=True).strip(),
            "authority_sha256": hashlib.sha256(
                json.dumps(authority, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
        })
        stage = "r9e_frozen_execution"
        base.run()
        stage = "final_package_verification"
        receipt = base.publication_check()
        _atomic(LOCAL / "final_validator_receipt.json", receipt)
        print("R9G empirical execution closed and publication validated")
    except BaseException as error:
        emergency = LOCAL / "r9g_emergency_failure.json"
        if not _safe(emergency).exists():
            _atomic(emergency, {
                "schema_version": 1, "status": "failure", "stage": stage,
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
            emergency = LOCAL / "r9g_import_failure.json"
            if not _safe(emergency).exists():
                _atomic(emergency, {"schema_version": 1, "status": "failure",
                    "stage": "startup_or_import", "exception": type(error).__name__,
                    "traceback": "".join(traceback.format_exception(error))})
        raise


if __name__ == "__main__":
    main()
