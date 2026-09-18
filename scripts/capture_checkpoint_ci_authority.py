#!/usr/bin/env python3
"""Capture one authenticated checkpoint-CI receipt before governed execution."""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defensive_network_disruption.validation.checkpoint_ci_authority import (
    CIExpectation, capture_github_receipt, durable_bytes, sha256_file)


def git(*args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=ROOT, text=True).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True, type=int)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--runner", required=True, type=Path)
    args = parser.parse_args()
    expected = CIExpectation(
        checkpoint_commit=git("rev-parse", "HEAD"),
        protocol_sha256=sha256_file(ROOT / args.protocol),
        runner_implementation_sha256=sha256_file(ROOT / args.runner),
        lockfile_sha256=sha256_file(ROOT / "uv.lock"),
        workflow_sha256=sha256_file(ROOT / ".github/workflows/ci.yml"),
    )
    capture_github_receipt(ROOT / args.output, args.run_id, expected)
    digest = sha256_file(ROOT / args.output)
    durable_bytes((ROOT / args.output).with_suffix((ROOT / args.output).suffix + ".sha256"),
                  (digest + "\n").encode())
    print(digest)


if __name__ == "__main__":
    main()
