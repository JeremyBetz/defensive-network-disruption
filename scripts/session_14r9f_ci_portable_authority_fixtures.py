#!/usr/bin/env python3
"""Derive or validate the hash-only Session 14R9F authority fixture."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from defensive_network_disruption.validation import r9f_portable_authority as authority

STRUCTURE = ROOT / "outputs/session14am_constant_width_comparator_diagnosis/local/000020_structure.json"


def derive() -> dict:
    retained = json.loads(STRUCTURE.read_text())
    current = authority.load_fixture(ROOT)
    observed = authority.semantic_projection_hash(
        retained["partitions"], retained["onsets"], retained["switches"])
    if observed != current["semantic_projection_sha256"]:
        raise ValueError("derived_projection_mismatch")
    return current


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("derive-check", "validate"))
    command = parser.parse_args().command
    value = derive() if command == "derive-check" else authority.load_fixture(ROOT)
    print(json.dumps({"status": "passed", "authority_id": value["authority_id"]}, sort_keys=True))


if __name__ == "__main__":
    main()
