#!/usr/bin/env python3
"""Standard-library startup boundary for the one-shot Session 14R9U runner."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import traceback


ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / "outputs/continuous_occlusion_empirical_retry_r9u/local"


def _fallback_import_failure(error: BaseException) -> None:
    """Preserve failure even if the R9M controller itself cannot import."""
    LOCAL.mkdir(parents=True, exist_ok=True)
    trace = "".join(traceback.format_exception(error)).encode()
    trace_path = LOCAL / "startup_import_traceback.txt"
    record_path = LOCAL / "startup_import_failure.json"
    if trace_path.exists() or record_path.exists():
        raise FileExistsError("startup_failure_already_recorded")
    with trace_path.open("xb") as handle:
        handle.write(trace); handle.flush(); os.fsync(handle.fileno())
    import hashlib
    record = {"exception_message": str(error), "exception_type": type(error).__name__,
              "schema_version": 1, "stage": "startup_import",
              "traceback_sha256": hashlib.sha256(trace).hexdigest()}
    raw = (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode()
    with record_path.open("xb") as handle:
        handle.write(raw); handle.flush(); os.fsync(handle.fileno())


def main() -> None:
    sys.path.insert(0, str(ROOT / "src"))
    try:
        from defensive_network_disruption.validation.checkpoint_ci_authority import FailureController
    except BaseException as error:
        _fallback_import_failure(error)
        raise
    controller = FailureController(LOCAL)
    try:
        from defensive_network_disruption.validation.r9u_study import main as implementation_main
    except BaseException as error:
        controller.capture(error, "startup_import")
        raise
    implementation_main()


if __name__ == "__main__":
    main()
