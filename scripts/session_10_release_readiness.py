#!/usr/bin/env python3
"""Synthetic-only Session 10 API and distribution release audit."""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.metadata
import inspect
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tarfile
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import defensive_network_disruption as dnd
from defensive_network_disruption.examples import demonstration_models, synthetic_option_state

START = "506891ace7c7cff5b3e9e5e0e54667252bd91a15"
PROTOCOL = Path("docs/protocols/phase_10_package_hardening_and_release_readiness.md")
CONTRACT = Path("outputs/package_release_readiness/release_contract.json")
OUTPUT = Path("outputs/package_release_readiness")
EXPECTED_EXPORTS = (
    "FrozenOptionModel", "MetricCoordinateContext", "OptionEdge", "OptionNetwork",
    "OptionState", "animate_option_network_comparison", "compare_options",
    "evaluate_options", "option_state_from_kloppy", "plot_option_network",
)
EXPECTED_SDIST = {
    "LICENSE.md", "README.md", "CHANGELOG.md", "CONTRIBUTING.md",
    "docs/public_api.md", "docs/release_checklist.md", "examples/quickstart.py",
    "pyproject.toml", "scripts/build_release_artifacts.py",
    "scripts/session_10_release_readiness.py",
}
PROHIBITED_PARTS = {
    ".git", ".venv", "__pycache__", "outputs", "build", "dist",
}


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load(path: Path) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def committed(path: Path) -> None:
    current = (ROOT / path).read_bytes()
    authority = subprocess.check_output(["git", "show", f"HEAD:{path}"], cwd=ROOT)
    if current != authority:
        raise RuntimeError(f"authority file is not committed unchanged: {path}")


def preflight() -> None:
    git("merge-base", "--is-ancestor", START, "HEAD")
    committed(PROTOCOL)
    committed(CONTRACT)
    contract = load(CONTRACT)
    if contract["version"] != "0.1.0" or tuple(sorted(contract["public_exports"])) != EXPECTED_EXPORTS:
        raise RuntimeError("release contract does not match the frozen public surface")
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    called = {
        node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
        for node in ast.walk(tree) if isinstance(node, ast.Call)
        and isinstance(node.func, (ast.Attribute, ast.Name))
    }
    if {"urlopen", "minimize", "fit", "acquire", "download"} & called:
        raise RuntimeError("release audit contains a prohibited acquisition or fitting route")
    print("Session 10 preflight passed; synthetic and committed public inputs only")


def audit_api() -> dict:
    preflight()
    if tuple(sorted(dnd.__all__)) != EXPECTED_EXPORTS:
        raise RuntimeError("root public exports differ from the release contract")
    state = synthetic_option_state()
    m0, m1 = demonstration_models()
    left = dnd.evaluate_options(state, model=m0)
    right = dnd.evaluate_options(state, model=m1)
    comparison = dnd.compare_options(left, right)
    started = time.perf_counter()
    for _ in range(1000):
        dnd.evaluate_options(state, model=m1)
    elapsed = time.perf_counter() - started
    if elapsed >= 10.0:
        raise RuntimeError("1,000-state engineering sanity check exceeded ten seconds")
    result = {
        "comparison_keys": sorted(comparison),
        "elapsed_seconds": elapsed,
        "evaluations": 1000,
        "performance_claim": False,
        "public_exports": list(EXPECTED_EXPORTS),
        "status": "passed",
    }
    print(json.dumps(result, sort_keys=True))
    return result


def _safe_member(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or any(part in PROHIBITED_PARTS for part in path.parts):
        raise RuntimeError(f"prohibited distribution member: {name}")
    if path.parts and (path.parts[0] == "data" or
                       (len(path.parts) > 1 and path.parts[1] == "data" and
                        path.parts[0] != "defensive_network_disruption")):
        raise RuntimeError(f"prohibited repository data member: {name}")
    return path


def audit_distributions(directory: Path) -> dict:
    directory = directory.resolve()
    wheels = sorted(directory.glob("*.whl"))
    sdists = sorted(directory.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise RuntimeError("dist-dir must contain exactly one wheel and one source archive")
    wheel, sdist = wheels[0], sdists[0]
    if "0.1.0" not in wheel.name or "0.1.0" not in sdist.name:
        raise RuntimeError("distribution filenames must contain version 0.1.0")
    with zipfile.ZipFile(wheel) as archive:
        wheel_names = [_safe_member(name) for name in archive.namelist()]
        if not any(path.name == "LICENSE.md" for path in wheel_names):
            raise RuntimeError("wheel is missing LICENSE.md")
        if not any(str(path) == "defensive_network_disruption/__init__.py" for path in wheel_names):
            raise RuntimeError("wheel is missing the import package")
        metadata_name = next((str(path) for path in wheel_names if path.name == "METADATA"), None)
        metadata = archive.read(metadata_name).decode("utf-8") if metadata_name else ""
        for value in ("Version: 0.1.0", "License-Expression: MIT", "Provides-Extra: public"):
            if value not in metadata:
                raise RuntimeError(f"wheel metadata missing {value}")
    with tarfile.open(sdist, "r:gz") as archive:
        sdist_names = [_safe_member(member.name) for member in archive.getmembers()]
        root_names = {"/".join(path.parts[1:]) for path in sdist_names if len(path.parts) > 1}
        missing = sorted(EXPECTED_SDIST - root_names)
        if missing:
            raise RuntimeError(f"source archive is missing: {', '.join(missing)}")
    result = {
        "sdist": {"bytes": sdist.stat().st_size, "file_count": len(sdist_names),
                  "name": sdist.name, "sha256": sha256(sdist)},
        "status": "passed",
        "wheel": {"bytes": wheel.stat().st_size, "file_count": len(wheel_names),
                  "name": wheel.name, "sha256": sha256(wheel)},
    }
    print(json.dumps(result, sort_keys=True))
    return result


def publication_check() -> None:
    preflight()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    words = len(readme.split())
    visuals = len(re.findall(r"!\[[^]]*\]\([^)]+\)", readme))
    tables = sum(line.strip().startswith("|") and line.strip().endswith("|")
                 for line in readme.splitlines())
    if words >= 1000 or visuals != 1 or tables:
        raise RuntimeError("README competition limits failed")
    for name in ("environment_authority.json", "distribution_inventory.json", "qc.json", "manifest.json"):
        path = OUTPUT / name
        value = load(path)
        if value.get("schema_version") != "1":
            raise RuntimeError(f"invalid publication schema: {name}")
    manifest = load(OUTPUT / "manifest.json")
    for name, expected in manifest["output_sha256"].items():
        if sha256(ROOT / OUTPUT / name) != expected:
            raise RuntimeError(f"output hash mismatch: {name}")
    public_paths = [ROOT / "README.md", ROOT / "docs/public_api.md",
                    ROOT / "docs/session_10_package_hardening_report.md",
                    *(ROOT / OUTPUT / name for name in manifest["output_sha256"])]
    forbidden = ("/Users/", "/private/", "github-cloud.githubusercontent.com", "Authorization:")
    for path in public_paths:
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in forbidden):
            raise RuntimeError(f"publication-sensitive text in {path.name}")
    print("Session 10 publication checks passed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=(
        "preflight", "audit-api", "audit-distributions", "publication-check",
    ))
    parser.add_argument("--dist-dir", type=Path)
    args = parser.parse_args()
    if args.command == "preflight":
        preflight()
    elif args.command == "audit-api":
        audit_api()
    elif args.command == "audit-distributions":
        if args.dist_dir is None:
            parser.error("audit-distributions requires --dist-dir")
        audit_distributions(args.dist_dir)
    else:
        publication_check()


if __name__ == "__main__":
    main()
