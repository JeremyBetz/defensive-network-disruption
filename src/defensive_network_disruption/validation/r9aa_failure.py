"""Prospective acquisition failure boundary with capture-first ordering."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .checkpoint_ci_authority import FailureController

_SEAL = object()


@dataclass(frozen=True)
class CapturedFailure:
    directory: Path
    stage: str
    exception_type: str
    exception_message: str
    traceback_sha256: str
    _seal: object

    def __post_init__(self):
        if self._seal is not _SEAL:
            raise TypeError("captured_failure_required")


class AcquisitionFailureBoundary:
    def __init__(self, directory: Path):
        self.directory = Path(directory)
        self.controller = FailureController(self.directory)

    def capture(self, error: BaseException, stage: str, *, context=None,
                timestamp: str | None = None) -> CapturedFailure:
        record = self.controller.capture(error, stage, context=context, timestamp=timestamp)
        validated = self.controller.validate()
        if validated["stage"] != stage or validated["exception_type"] != type(error).__name__:
            raise ValueError("failure_capture_validation")
        return CapturedFailure(self.directory, stage, record["exception_type"],
                               record["exception_message"], record["traceback_sha256"], _SEAL)

    def validate_capture(self, captured: CapturedFailure) -> dict:
        if captured._seal is not _SEAL or captured.directory != self.directory:
            raise TypeError("captured_failure_required")
        validated = self.controller.validate()
        if (validated["stage"] != captured.stage or
                validated["exception_type"] != captured.exception_type or
                validated["traceback_sha256"] != captured.traceback_sha256):
            raise ValueError("captured_failure_binding")
        return validated

    def close(self, error: BaseException, stage: str, *,
              write_blocked_qc: Callable[[CapturedFailure], object],
              publish: Callable[[CapturedFailure], object], context=None,
              timestamp: str | None = None, reraise: bool = False):
        original_traceback = error.__traceback__
        captured = self.capture(error, stage, context=context, timestamp=timestamp)
        events = ["traceback_captured", "capture_validated"]
        publication_error = None
        qc_result = publication_result = None
        try:
            self.validate_capture(captured)
            qc_result = write_blocked_qc(captured)
            events.append("blocked_qc")
            self.validate_capture(captured)
            publication_result = publish(captured)
            events.append("publication")
        except BaseException as secondary:
            publication_error = secondary
            self.controller.publication_failure(secondary, timestamp=timestamp)
            events.append("publication_failure_preserved")
        self.validate_capture(captured)
        if reraise:
            raise error.with_traceback(original_traceback)
        return {
            "captured": captured,
            "events": tuple(events),
            "qc_result": qc_result,
            "publication_result": publication_result,
            "publication_error": None if publication_error is None else type(publication_error).__name__,
        }


__all__ = ["AcquisitionFailureBoundary", "CapturedFailure"]
