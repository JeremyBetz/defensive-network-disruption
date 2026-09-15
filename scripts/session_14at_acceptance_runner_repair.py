#!/usr/bin/env python3
"""Governed Session 14at synthetic contract acceptance."""
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys
from pathlib import Path

from defensive_network_disruption.validation import acceptance_runner as runner
from defensive_network_disruption.validation import independent_certificate_verifier as verifier

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"outputs/continuous_occlusion_acceptance_runner_repair"
LOCAL=OUT/"local"
PROTOCOL=ROOT/"docs/protocols/phase_14at_acceptance_runner_repair.md"
TAG="f00690c05d8c1c6db308a65bd311c43f9a8ef2fa"

def git(*args): return subprocess.check_output(("git",*args),cwd=ROOT,text=True).strip()

def preflight():
    if git("status","--porcelain"): raise RuntimeError("dirty_tree")
    if git("rev-parse","v0.1.0^{}") != TAG: raise RuntimeError("release_changed")
    verifier.load_session14ar_certificate(ROOT)
    return {"status":"ready","package_authority":runner.onset_owner_acceptance.__name__,"protocol_sha256":verifier.sha(PROTOCOL),"empirical_routes":False}

def accept():
    marker=LOCAL/"accept.marker"; runner.create_once(marker,{"session":"14at"})
    completed=[]; stage="preflight"
    try:
        preflight(); completed.append(stage); stage="contract_acceptance"
        result=runner.publish_success(ROOT,OUT,git("rev-parse","HEAD"),verifier.sha(PROTOCOL)); completed.append(stage)
        print(json.dumps(result,sort_keys=True))
    except BaseException as exc:
        runner.publish_failure(OUT,stage,exc,completed,marker)
        raise

def main():
    p=argparse.ArgumentParser();p.add_argument("command",choices=("preflight","accept","publication-check"));a=p.parse_args()
    if a.command=="preflight": print(json.dumps(preflight(),sort_keys=True))
    elif a.command=="accept": accept()
    else: print(json.dumps(runner.publication_check(OUT),sort_keys=True))
if __name__=="__main__":main()
