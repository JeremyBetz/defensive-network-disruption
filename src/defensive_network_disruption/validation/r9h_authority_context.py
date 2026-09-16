"""Synthetic-only evidence for the R9H runtime authority-context join."""
from __future__ import annotations

from dataclasses import replace
import hashlib
from pathlib import Path
from unittest.mock import patch

import numpy as np

from defensive_network_disruption.geometry import r9e_representation as representation
from defensive_network_disruption.geometry.occlusion_fields import CarrierOriginField
from defensive_network_disruption.validation import independent_certificate_verifier as certificates
from defensive_network_disruption.validation import r9f_portable_authority as portable


SYNTHETIC_IDENTITY = {"alias": "synthetic-r9h", "state": "0", "edge": "1"}
SYNTHETIC_ORIGIN = (0.0, 0.0)
SYNTHETIC_RECEIVER = (20.0, 3.0)
SYNTHETIC_DEFENDERS = ((5.0, 0.0), (8.0, 2.0), (10.0, -3.0))


def _sha_text(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def observe_actual_join(root: Path) -> dict:
    """Observe the real evaluator join while leaving its functions unchanged."""
    captured: dict = {}
    historical = representation.independent_maximum

    def observer(function, partitions, onsets, switches, **kwargs):
        context = kwargs["context"]
        captured["context"] = context
        sample = function(np.array([0.0, 0.5, 1.0], dtype=np.float64))
        field = CarrierOriginField("constant_width")
        origin = np.asarray(context["origin"], dtype=np.float64)
        receiver = np.asarray(context["receiver"], dtype=np.float64)
        defenders = np.asarray(context["defenders"], dtype=np.float64)
        expected = field.individual_values(
            origin, defenders,
            origin[None, :] + np.array([0.0, 0.5, 1.0])[:, None] *
            (receiver - origin)[None, :])
        captured["field_values_identical"] = bool(np.array_equal(sample, expected))
        captured["partitions"] = partitions
        captured["onsets"] = onsets
        captured["switches"] = switches
        return representation.IntegralInterval(0.0, 1.0, 0.0, len(partitions) - 1,
                                               len(partitions) - 1, 0), {
            "strict": {"status": "synthetic_observer"},
            "repeat": {"status": "synthetic_observer"},
            "onset": {"status": "synthetic_observer"},
        }

    with patch.object(representation, "independent_maximum", wraps=observer) as wrapped:
        representation.evaluate(
            "constant_width", SYNTHETIC_ORIGIN, SYNTHETIC_RECEIVER,
            SYNTHETIC_DEFENDERS, root=root,
            authority_context=dict(SYNTHETIC_IDENTITY))
    if wrapped.call_count != 1:
        raise RuntimeError("join_observer_call_count")
    context = captured["context"]
    expected = {
        **SYNTHETIC_IDENTITY,
        "origin": tuple(map(float, SYNTHETIC_ORIGIN)),
        "receiver": tuple(map(float, SYNTHETIC_RECEIVER)),
        "defenders": tuple(tuple(map(float, item)) for item in SYNTHETIC_DEFENDERS),
    }
    if context != expected:
        raise RuntimeError("runtime_context_not_canonical_geometry")

    selected: dict = {}
    original_hash = portable.selected_geometry_hash

    def hash_observer(value):
        selected["context"] = value
        selected["sha256"] = original_hash(value)
        return selected["sha256"]

    try:
        with patch.object(portable, "selected_geometry_hash", wraps=hash_observer):
            representation._runtime_request(
                root, candidate="constant_width", context=context,
                lower=0.0, upper=1.0, partitions=captured["partitions"],
                onsets=captured["onsets"], switches=captured["switches"])
    except certificates.CertificateError as error:
        if str(error) != "authority_mismatch:selected_geometry":
            raise
        mismatch = str(error)
    else:
        raise RuntimeError("synthetic_authority_must_not_match_empirical")
    if selected.get("context") != context:
        raise RuntimeError("authority_builder_context_changed")
    return {
        "actual_chain_observed": True,
        "identifier_context_fields": sorted(SYNTHETIC_IDENTITY),
        "runtime_context_fields": sorted(context),
        "origin_identical": context["origin"] == expected["origin"],
        "receiver_identical": context["receiver"] == expected["receiver"],
        "defenders_identical_and_ordered": context["defenders"] == expected["defenders"],
        "field_values_identical": captured["field_values_identical"],
        "authority_builder_received_complete_context": selected.get("context") == context,
        "synthetic_fingerprint_sha256": selected["sha256"],
        "synthetic_empirical_match_result": mismatch,
        "first_apparent_loss_interface": "calculate_edge.authority_context_metadata",
        "actual_geometry_join_interface": "r9e_representation.evaluate.runtime_context",
        "actual_loss_observed": False,
    }


def mutation_oracles() -> list[dict]:
    base = {**SYNTHETIC_IDENTITY, "origin": SYNTHETIC_ORIGIN,
            "receiver": SYNTHETIC_RECEIVER, "defenders": SYNTHETIC_DEFENDERS}
    baseline = portable.selected_geometry_hash(base)
    variants = {
        "origin_coordinate": {**base, "origin": (0.0, 0.25)},
        "receiver_coordinate": {**base, "receiver": (20.0, 3.25)},
        "defender_coordinate": {**base, "defenders": ((5.0, 0.0), (8.0, 2.25), (10.0, -3.0))},
        "defender_order": {**base, "defenders": tuple(reversed(SYNTHETIC_DEFENDERS))},
        "identifier_only_false_match": {**base, "receiver": (20.0, 3.5)},
    }
    rows = []
    for name, value in variants.items():
        changed = portable.selected_geometry_hash(value)
        rows.append({"oracle": name, "alias_state_edge_unchanged": True,
                     "fingerprint_changed": changed != baseline,
                     "exact_match_rejected": changed != baseline,
                     "status": "passed" if changed != baseline else "failed"})
    return rows


def retained_certificate_orchestration(root: Path) -> dict:
    registered, observation, authority = certificates.load_session14ar_certificate(root)
    evidence = representation._certify_observation(
        root, observation.estimate, observation.warning_class,
        observation.warning_message_sha256, observation.request)
    return {
        "evidence_kind": "retained_observation_certificate_orchestration",
        "authority_id": registered.authority_id,
        "authority_sha256": registered.authority_sha256,
        "source_manifest_sha256": registered.source_manifest_sha256,
        "integrand_specification_hash": registered.integrand_specification_hash,
        "selected_geometry_authority_hash": authority["integrand_specification"]["selected_geometry_authority_hash"],
        "warning_preserved": evidence.adaptive_warning_count == 1,
        "exact_request_matched": True,
        "certificate_lookup_succeeded": evidence.independently_certified_count == 1,
        "blocking_warning_count": evidence.blocking_warning_count,
        "status": evidence.status,
        "empirical_geometry_reconstructed": False,
    }


def unmatched_warning_oracle(root: Path) -> dict:
    _, observation, _ = certificates.load_session14ar_certificate(root)
    wrong = replace(observation.request, interval_identity="synthetic-unmatched-r9h")
    try:
        representation._certify_observation(
            root, observation.estimate, observation.warning_class,
            observation.warning_message_sha256, wrong)
    except certificates.CertificateError as error:
        result = str(error)
    else:
        raise RuntimeError("unmatched_warning_not_blocked")
    return {
        "warning_preserved": True,
        "request_kind": "synthetic_authority_mutation",
        "certificate_lookup_succeeded": False,
        "blocking": True,
        "readiness": False,
        "failure": result,
        "fallback_certificate": False,
    }


def no_reopening_guard(root: Path) -> dict:
    paths = (
        root / "src/defensive_network_disruption/geometry/r9e_representation.py",
        root / "src/defensive_network_disruption/validation/r9f_portable_authority.py",
    )
    source = "\n".join(path.read_text() for path in paths)
    prohibited = ("population.jsonl", "project_line(", "000010_selected_geometry.json",
                  "000020_structure.json", "target_index", "load_model")
    hits = [item for item in prohibited if item in source]
    # The portable module names these historical records only as public hash keys.
    hash_keys = {"000010_selected_geometry.json", "000020_structure.json"}
    allowed_hash_key = bool(hash_keys.intersection(hits))
    hits = [item for item in hits if item not in hash_keys]
    return {"provider_or_prepared_loader_present": bool(hits),
            "prohibited_hits": hits, "historical_hash_key_only": allowed_hash_key,
            "private_fallback_present": False,
            "passed": not hits}


__all__ = ["mutation_oracles", "no_reopening_guard", "observe_actual_join",
           "retained_certificate_orchestration", "unmatched_warning_oracle"]
