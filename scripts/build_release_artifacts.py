#!/usr/bin/env python3
"""Build reproducible wheel and canonicalized sdist artifacts."""
from __future__ import annotations

import argparse
import gzip
import io
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
EPOCH = 1789091224


def canonicalize_sdist(source: Path, destination: Path) -> None:
    """Rewrite an sdist with sorted members and normalized archive metadata."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name("." + destination.name + ".tmp")
    with tarfile.open(source, "r:gz") as incoming, temporary.open("xb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=EPOCH) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as outgoing:
                for member in sorted(incoming.getmembers(), key=lambda item: item.name):
                    if member.issym() or member.islnk():
                        raise RuntimeError(f"release sdist may not contain links: {member.name}")
                    normalized = tarfile.TarInfo(member.name)
                    normalized.mode = member.mode
                    normalized.mtime = EPOCH
                    normalized.uid = normalized.gid = 0
                    normalized.uname = normalized.gname = ""
                    if member.isdir():
                        normalized.type = tarfile.DIRTYPE
                        outgoing.addfile(normalized)
                    elif member.isfile():
                        payload = incoming.extractfile(member).read()
                        normalized.size = len(payload)
                        outgoing.addfile(normalized, io.BytesIO(payload))
                    else:
                        raise RuntimeError(f"unsupported sdist member type: {member.name}")
    temporary.replace(destination)


def build(out_dir: Path) -> None:
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    if any(out_dir.iterdir()):
        raise RuntimeError("output directory must be empty")
    environment = os.environ.copy()
    environment["SOURCE_DATE_EPOCH"] = str(EPOCH)
    with tempfile.TemporaryDirectory() as raw_dir:
        subprocess.run(
            ["uv", "build", "--wheel", "--sdist", "--out-dir", raw_dir],
            cwd=ROOT, env=environment, check=True,
        )
        raw = Path(raw_dir)
        wheels = list(raw.glob("*.whl"))
        sdists = list(raw.glob("*.tar.gz"))
        if len(wheels) != 1 or len(sdists) != 1:
            raise RuntimeError("build must produce exactly one wheel and one sdist")
        shutil.copyfile(wheels[0], out_dir / wheels[0].name)
        canonicalize_sdist(sdists[0], out_dir / sdists[0].name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    build(parser.parse_args().out_dir)


if __name__ == "__main__":
    main()
