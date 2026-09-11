#!/usr/bin/env python3
"""Session 9 synthetic public-example orchestration; no empirical data routes."""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "session-09-public-tooling"
import matplotlib.pyplot as plt
from matplotlib.animation import PillowWriter

from defensive_network_disruption.examples import (
    synthetic_option_sequence,
    synthetic_option_state,
)
from defensive_network_disruption.networks.options import FrozenOptionModel, evaluate_options
from defensive_network_disruption.visualization.options import (
    TEXT_COLOR,
    animate_option_network_comparison,
    plot_option_network,
)

START = "645f282402c4fccf6117186381a1212b56f11be9"
PROTOCOL = Path("docs/protocols/phase_09_public_tooling_and_storytelling.md")
CONTRACT = Path("outputs/public_examples/software_contract.json")
MODEL = Path("outputs/reserved_evaluation/final_development_models.json")
MODEL_SHA = "0383561e45bcd9f8d84eccc7e9733b2409536f61c39193fa87d08c36c6f6fd65"
OUT = Path("outputs/public_examples")
STATIC = OUT / "synthetic_option_network.svg"
ANIMATION = OUT / "synthetic_option_network_animation.gif"
AUTHORITY = OUT / "implementation_authority.json"
QC = OUT / "qc.json"
MANIFEST = OUT / "manifest.json"
IMPLEMENTATION = (
    "pyproject.toml", "uv.lock", "src/defensive_network_disruption/__init__.py",
    "src/defensive_network_disruption/networks/__init__.py",
    "src/defensive_network_disruption/networks/options.py",
    "src/defensive_network_disruption/data/option_adapter.py",
    "src/defensive_network_disruption/examples.py",
    "src/defensive_network_disruption/visualization/__init__.py",
    "src/defensive_network_disruption/visualization/options.py",
    "examples/quickstart.py", "scripts/session_09_public_tooling.py",
    "tests/test_session9_public.py",
)
HISTORICAL_APPEND_ONLY = {"docs/research_log.md", "references/library_review.md"}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def safe(path):
    path = ROOT / path
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise PermissionError("symlink paths are not permitted")
    resolved = path.resolve()
    if not resolved.is_relative_to(ROOT.resolve()):
        raise PermissionError("path escapes the repository")
    return resolved


def digest(path):
    h = hashlib.sha256()
    with safe(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path):
    return json.loads(safe(path).read_text(), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def atomic(path, payload):
    path = Path(path)
    if not path.is_relative_to(OUT):
        raise PermissionError("public-example output required")
    destination = safe(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name("." + destination.name + ".tmp")
    with temporary.open("xb") as handle:
        handle.write(payload)
    temporary.replace(destination)


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def committed(path):
    expected = subprocess.check_output(["git", "show", "HEAD:" + str(path)], cwd=ROOT)
    if hashlib.sha256(expected).hexdigest() != digest(path):
        raise ValueError(f"uncommitted authority: {path}")


def historical():
    git("merge-base", "--is-ancestor", START, "HEAD")
    original = set(git("ls-tree", "-r", "--name-only", START).splitlines())
    changed = set(git("diff", "--name-only", START).splitlines())
    for name in original & changed:
        before = subprocess.check_output(["git", "show", f"{START}:{name}"], cwd=ROOT)
        after = safe(name).read_bytes()
        if name in HISTORICAL_APPEND_ONLY:
            if not after.startswith(before):
                raise ValueError(f"append-only history changed: {name}")
        elif name not in IMPLEMENTATION and name != "README.md":
            raise ValueError(f"historical artifact changed: {name}")


def environment():
    from importlib.metadata import version
    return {
        "python": platform.python_version(),
        "numpy": version("numpy"),
        "kloppy": version("kloppy"),
        "pandas": version("pandas"),
        "matplotlib": version("matplotlib"),
        "mplsoccer": version("mplsoccer"),
        "pillow": version("pillow"),
        "uv_lock_sha256": digest("uv.lock"),
    }


def models():
    if digest(MODEL) != MODEL_SHA:
        raise ValueError("frozen public model authority mismatch")
    values = load(MODEL)["models"]
    return tuple(FrozenOptionModel.from_mapping(name, values[name]) for name in ("m0", "m1"))


def verify_authority(require_implementation=False):
    historical()
    committed(PROTOCOL)
    committed(CONTRACT)
    if require_implementation:
        committed(AUTHORITY)
        authority = load(AUTHORITY)
        if authority != {
            "environment": environment(),
            "implementation_sha256": {name: digest(name) for name in IMPLEMENTATION},
            "model_sha256": MODEL_SHA,
            "protocol_sha256": digest(PROTOCOL),
            "schema_version": "1",
            "software_contract_sha256": digest(CONTRACT),
            "starting_commit": START,
        }:
            raise ValueError("implementation authority mismatch")


def preflight():
    verify_authority(require_implementation=safe(AUTHORITY).exists())
    models()
    route_source = "\n".join(inspect.getsource(function) for function in (
        render_static, render_animation, render_pair, render_examples,
    ))
    if any(token in route_source for token in (
        "urlopen(", "requests.", "minimize(", "fit(", "population(",
    )):
        raise ValueError("forbidden acquisition, fitting, or empirical route")
    print("Session 9 preflight passed; no empirical data opened")


def render_static(path, m0_model, m1_model):
    state = synthetic_option_state()
    figure, axes = plt.subplots(1, 2, figsize=(16, 9), constrained_layout=True)
    figure.patch.set_facecolor("#eef2f6")
    for axis, model, title in zip(
        axes, (m0_model, m1_model),
        ("M0 · attacking geometry", "M1 · defense-conditioned geometry"),
    ):
        plot_option_network(
            state, evaluate_options(state, model=model), pitch_length=105,
            pitch_width=68, ax=axis, title=title,
        )
    figure.suptitle("Same options. Different defensive context.", fontsize=23,
                    color=TEXT_COLOR, weight="bold")
    figure.text(
        0.5, 0.018,
        "SYNTHETIC · widths show model-implied receiver-option shares — not accessibility or pass probability",
        ha="center", color=TEXT_COLOR, fontsize=12,
    )
    figure.savefig(path, format="svg", metadata={"Date": None})
    plt.close(figure)


def render_animation(path, m0_model, m1_model):
    states = synthetic_option_sequence()
    animation = animate_option_network_comparison(
        states, m0_model=m0_model, m1_model=m1_model,
        pitch_length=105, pitch_width=68, fps=10,
    )
    animation.save(path, writer=PillowWriter(fps=10, metadata={"artist": "Disrupting the Network"}))
    plt.close(animation._fig)


def render_pair(directory):
    m0_model, m1_model = models()
    static = Path(directory) / STATIC.name
    animation = Path(directory) / ANIMATION.name
    render_static(static, m0_model, m1_model)
    render_animation(animation, m0_model, m1_model)
    return static, animation


def validate_visuals(static, animation):
    import xml.etree.ElementTree as ET
    from PIL import Image
    root = ET.parse(static).getroot()
    if root.attrib.get("width") != "1152pt" or root.attrib.get("height") != "648pt":
        raise ValueError("static dimensions are not 1600 by 900 CSS pixels at Matplotlib's 72 dpi representation")
    text = Path(static).read_text()
    for phrase in ("SYNTHETIC", "M0", "M1", "not accessibility", "effective options"):
        if phrase not in text:
            raise ValueError(f"missing static annotation: {phrase}")
    with Image.open(animation) as image:
        if image.size != (960, 540) or image.n_frames != 80 or image.info.get("loop") != 0:
            raise ValueError("animation dimensions, frames, or looping mismatch")
        durations = []
        for index in range(image.n_frames):
            image.seek(index)
            durations.append(image.info.get("duration"))
        if durations != [100] * 80:
            raise ValueError("animation must contain 80 frames at 10 fps")


def render_examples():
    verify_authority(require_implementation=True)
    if any(safe(path).exists() for path in (STATIC, ANIMATION, QC, MANIFEST)):
        raise ValueError("public outputs already exist")
    with tempfile.TemporaryDirectory() as left, tempfile.TemporaryDirectory() as right:
        left_files = render_pair(left)
        right_files = render_pair(right)
        validate_visuals(*left_files)
        validate_visuals(*right_files)
        for first, second in zip(left_files, right_files):
            if Path(first).read_bytes() != Path(second).read_bytes():
                raise ValueError("public render is not byte deterministic")
        atomic(STATIC, left_files[0].read_bytes())
        atomic(ANIMATION, left_files[1].read_bytes())
    qc = {
        "animation": {"duration_seconds": 8, "fps": 10, "frames": 80,
                      "height": 540, "loop": True, "width": 960},
        "empirical_data_access": False,
        "fitting": False,
        "m2_computation": False,
        "schema_version": "1",
        "static": {"format": "svg", "height": 900, "width": 1600},
        "status": "validated",
    }
    atomic(QC, json_bytes(qc))
    manifest = {
        "implementation_authority_sha256": digest(AUTHORITY),
        "model_sha256": MODEL_SHA,
        "output_sha256": {path.name: digest(path) for path in (STATIC, ANIMATION, QC)},
        "protocol_sha256": digest(PROTOCOL),
        "schema_version": "1",
        "software_contract_sha256": digest(CONTRACT),
        "starting_commit": START,
        "status": "closed",
    }
    atomic(MANIFEST, json_bytes(manifest))
    publication_check()
    print("Session 9 public synthetic examples rendered and closed")


def publication_check():
    verify_authority(require_implementation=True)
    validate_visuals(safe(STATIC), safe(ANIMATION))
    qc = load(QC)
    if qc["status"] != "validated" or qc["empirical_data_access"] or qc["fitting"] or qc["m2_computation"]:
        raise ValueError("QC boundary mismatch")
    manifest = load(MANIFEST)
    expected = {path.name: digest(path) for path in (STATIC, ANIMATION, QC)}
    if manifest != {
        "implementation_authority_sha256": digest(AUTHORITY),
        "model_sha256": MODEL_SHA,
        "output_sha256": expected,
        "protocol_sha256": digest(PROTOCOL),
        "schema_version": "1",
        "software_contract_sha256": digest(CONTRACT),
        "starting_commit": START,
        "status": "closed",
    }:
        raise ValueError("manifest or output hash mismatch")
    print("Session 9 publication checks passed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preflight", "render-examples", "publication-check"))
    command = parser.parse_args().command
    {"preflight": preflight, "render-examples": render_examples,
     "publication-check": publication_check}[command]()
