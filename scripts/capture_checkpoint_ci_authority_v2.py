#!/usr/bin/env python3
"""Capture one explicit CI attempt, using source bindings from its Git commit."""
from pathlib import Path
import argparse
import subprocess
from defensive_network_disruption.validation.checkpoint_ci_authority_v2 import Expectation,capture,sha

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser()
    for name in ('run-id','attempt','checkpoint','protocol','runner','output'):
        parser.add_argument('--'+name,required=True,type=int if name in ('run-id','attempt') else str)
    args=parser.parse_args()
    def git_hash(path):
        return sha(subprocess.check_output(('git','show',f'{args.checkpoint}:{path}'),cwd=ROOT))
    expected=Expectation(args.checkpoint,git_hash(args.protocol),git_hash(args.runner),
        git_hash('uv.lock'),git_hash('.github/workflows/ci.yml'),args.run_id,args.attempt)
    verified=capture(Path(args.output),expected)
    print(verified.receipt_sha256)


if __name__=='__main__':main()
