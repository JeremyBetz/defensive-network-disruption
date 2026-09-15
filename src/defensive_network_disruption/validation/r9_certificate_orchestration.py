"""R9 retained-observation certificate orchestration; no geometry route."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

from . import independent_certificate_verifier as certificate


@dataclass(frozen=True)
class CertificateGateReadiness:
    authority_loaded: bool
    warning_preserved: bool
    lookup_attempted: bool
    exact_authority_match: bool
    estimate_contained: bool
    width_accepted: bool
    piece_certified: bool
    aggregation_valid: bool
    publication_validated: bool
    scope_valid: bool

    @property
    def ready(self) -> bool:
        return all(asdict(self).values())


def retained_observation_gate(root: Path, *, publish: Callable[[dict], bool]) -> dict:
    """Exercise registered evidence at the result boundary without field evaluation."""
    registered, observation, authority = certificate.load_session14ar_certificate(root)
    lookup_attempted = True
    piece = certificate.certify_warning(observation, registered)
    aggregate = certificate.aggregate_pieces((piece,))
    record = {
        "schema_version": 1,
        "evidence_type": "retained_observation_certificate_orchestration",
        "field_evaluation_performed": False,
        "empirical_geometry_accessed": False,
        "certificate_scope": "terminal_interval_8_only",
        "whole_integral_certified": False,
        "unrelated_comparator_disagreement_resolved": False,
        "warning_class": observation.warning_class,
        "warning_message_sha256": observation.warning_message_sha256,
        "warning_preserved": piece.adaptive_warning_count == 1,
        "certificate_lookup_attempted": lookup_attempted,
        "authority_id": registered.authority_id,
        "authority_sha256": registered.authority_sha256,
        "exact_authority_match": True,
        "lower_bound": registered.lower_bound,
        "upper_bound": registered.upper_bound,
        "adaptive_estimate": observation.estimate,
        "estimate_contained": registered.lower_bound <= observation.estimate <= registered.upper_bound,
        "width": registered.upper_bound - registered.lower_bound,
        "width_accepted": registered.upper_bound - registered.lower_bound <= certificate.AGREEMENT,
        "piece_status": piece.status,
        "aggregate": aggregate,
        "source_manifest_sha256": registered.source_manifest_sha256,
        "integrand_specification_hash": registered.integrand_specification_hash,
        "structural_partition_authority_hash": registered.structural_partition_authority_hash,
        "provenance_hash": registered.provenance_hash,
        "authority_files_verified": bool(authority["expected_hashes"]),
    }
    publication_validated = bool(publish(record))
    gate = CertificateGateReadiness(
        authority_loaded=True,
        warning_preserved=record["warning_preserved"],
        lookup_attempted=lookup_attempted,
        exact_authority_match=record["exact_authority_match"],
        estimate_contained=record["estimate_contained"],
        width_accepted=record["width_accepted"],
        piece_certified=piece.status == certificate.SUCCESS_STATUS,
        aggregation_valid=(aggregate["independently_certified_count"] == 1 and
                           aggregate["blocking_warning_count"] == 0),
        publication_validated=publication_validated,
        scope_valid=(not record["whole_integral_certified"] and
                     not record["unrelated_comparator_disagreement_resolved"]),
    )
    return {**record, "readiness_inputs": asdict(gate), "ready": gate.ready,
            "publication_validator_result": publication_validated}


def runtime_certificate_lookup(observation: certificate.AdaptiveObservation,
                               root: Path) -> certificate.PieceEvidence:
    """Exact registry lookup for a runtime-derived request; unmatched requests block."""
    registered, _, _ = certificate.load_session14ar_certificate(root)
    return certificate.certify_warning(observation, registered)


__all__ = ["CertificateGateReadiness", "retained_observation_gate",
           "runtime_certificate_lookup"]
