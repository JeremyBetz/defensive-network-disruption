"""Prospective R9E empirical adapter with exact certificate orchestration."""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import itertools
import math
from pathlib import Path
import warnings

import numpy as np
from scipy.integrate import quad

from . import onset_owner_certification as owner
from . import production_verification as pv
from .integration_review import values_for_components
from .micro_interval_verifier import IntegralInterval, interval_distance, point_interval_distance
from .occlusion_fields import CarrierOriginField, combine, points, simpson_average, validate_geometry
from .representation_study import VerifiedEdge
from .verification_audit import controlled_vector
from .verification_repair import mapped_signature
from ..validation import independent_certificate_verifier as certificates
from ..validation import r9f_portable_authority as portable


def _canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _warning_identity(item: warnings.WarningMessage) -> tuple[str, str]:
    cls = item.category
    return f"{cls.__module__}.{cls.__name__}", _sha(str(item.message).encode())


def _certify_observation(root: Path, estimate: float, warning_class: str,
                         warning_hash: str, request: certificates.IntegralRequest):
    registered, _, _ = certificates.load_session14ar_certificate(root)
    return certificates.certify_warning(
        certificates.AdaptiveObservation(float(estimate), warning_class, warning_hash, request),
        registered)


def _runtime_request(root: Path, *, candidate: str, context: dict, lower: float,
                     upper: float, partitions: tuple[float, ...], onsets,
                     switches) -> certificates.IntegralRequest:
    """Derive an exact registered request from current execution facts.

    The retained request is returned only after exact geometry, endpoint, and
    canonical-structure equivalence. No proximity or ordinal-only match exists.
    """
    registered, _, authority = certificates.load_session14ar_certificate(root)
    fixture = portable.load_fixture(root)
    selected_hash = portable.selected_geometry_hash(context)
    expected_selected = authority["integrand_specification"]["selected_geometry_authority_hash"]
    if selected_hash != expected_selected:
        raise certificates.CertificateError("authority_mismatch:selected_geometry")
    if candidate != registered.field_family:
        raise certificates.CertificateError("authority_mismatch:field_family")
    if certificates.float_bits(float(lower)) != registered.left_endpoint_binary64:
        raise certificates.CertificateError("authority_mismatch:left_endpoint")
    if certificates.float_bits(float(upper)) != registered.right_endpoint_binary64:
        raise certificates.CertificateError("authority_mismatch:right_endpoint")

    if portable.semantic_projection_hash(partitions, onsets, switches) != fixture["semantic_projection_sha256"]:
        raise certificates.CertificateError("authority_mismatch:structure_semantics")

    spec = {
        "interval_identity": "sanitized_terminal_interval_8",
        "left_endpoint_binary64": certificates.float_bits(float(lower)),
        "right_endpoint_binary64": certificates.float_bits(float(upper)),
        "field_family": candidate,
        "frozen_parameters": [["onset_metres", 1.0], ["sigma_metres", 2.0]],
        "combination": "maximum",
        "selected_geometry_authority_hash": selected_hash,
        "retained_interval_authority_hash": authority["integrand_specification"]["retained_interval_authority_hash"],
        "onset_authority_hash": authority["integrand_specification"]["onset_authority_hash"],
        "structural_partition_authority_hash": authority["integrand_specification"]["structural_partition_authority_hash"],
    }
    if _sha(certificates.canonical(spec)) != registered.integrand_specification_hash:
        raise certificates.CertificateError("authority_mismatch:integrand")
    return certificates.IntegralRequest(
        spec["interval_identity"], spec["left_endpoint_binary64"],
        spec["right_endpoint_binary64"], candidate,
        tuple((name, value) for name, value in spec["frozen_parameters"]),
        "maximum", registered.integrand_specification_hash,
        spec["structural_partition_authority_hash"], registered.method_id,
        registered.provenance_hash, registered.governing_tolerance,
    )


def _piece(function, lower: float, upper: float, tolerance: float, *, root: Path,
           candidate: str, context: dict, partitions: tuple[float, ...], onsets,
           switches) -> certificates.PieceEvidence:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        value, error = quad(
            lambda t: float(np.max(function(np.array([t], dtype=np.float64))[0])),
            lower, upper, epsabs=tolerance, epsrel=tolerance, limit=1000,
        )
    pv.require(math.isfinite(value) and math.isfinite(error), "adaptive_nonfinite")
    if not caught:
        return certificates.ordinary_piece(float(value))
    if len(caught) != 1:
        raise certificates.CertificateError("multiple_warnings")
    warning_class, warning_hash = _warning_identity(caught[0])
    request = _runtime_request(root, candidate=candidate, context=context,
                               lower=lower, upper=upper, partitions=partitions,
                               onsets=onsets, switches=switches)
    return _certify_observation(root, float(value), warning_class, warning_hash, request)


def _integrate(function, partitions, tolerance, *, root: Path, candidate: str,
               context: dict, structural_partitions: tuple[float, ...], onsets,
               switches) -> tuple[IntegralInterval, dict]:
    pairs = tuple(zip(partitions[:-1], partitions[1:], strict=True))
    pv.require(pairs and all(b > a for a, b in pairs), "partition_order")
    allocation = 1e-12 / len(pairs)
    evidence = []
    residual = 0.0
    for lower, upper in pairs:
        width = float(upper - lower)
        if width <= allocation:
            evidence.append(certificates.micro_residual_piece(0.0, width, 0.0))
            residual = math.fsum((residual, width))
        else:
            evidence.append(_piece(function, float(lower), float(upper), tolerance,
                                   root=root, candidate=candidate, context=context,
                                   partitions=structural_partitions, onsets=onsets,
                                   switches=switches))
    aggregate = certificates.aggregate_pieces(evidence)
    interval = IntegralInterval(aggregate["aggregate_lower"], aggregate["aggregate_upper"],
                                residual, len(pairs),
                                aggregate["ordinary_piece_count"] + aggregate["certificate_piece_count"],
                                aggregate["micro_residual_piece_count"])
    return interval, aggregate


def independent_maximum(function, partitions, onsets, switches, *, root: Path,
                        candidate: str, context: dict, historical_failure=False,
                        record=lambda **kw: None):
    structural = tuple(partitions)
    widths = [b - a for a, b in zip(structural[:-1], structural[1:], strict=True)]
    bounded = sum(width <= 1e-12 / len(widths) for width in widths)
    record(stage="routing", pieces=len(widths), bounded=bounded,
           quadrature=len(widths) - bounded)
    record(stage="strict_piecewise")
    strict, strict_evidence = _integrate(function, structural, 1e-13, root=root,
        candidate=candidate, context=context, structural_partitions=structural,
        onsets=onsets, switches=switches)
    record(stage="repeat_piecewise")
    repeat, repeat_evidence = _integrate(function, structural, 1e-11, root=root,
        candidate=candidate, context=context, structural_partitions=structural,
        onsets=onsets, switches=switches)
    pv.require(interval_distance(strict, repeat) <= 1e-10, "piecewise_repeat")
    record(stage="onset_adaptive")
    onset_partitions = tuple(sorted({0.0, 1.0, *(x.canonical for x in onsets)}))
    onset_interval, onset_evidence = _integrate(function, onset_partitions, 1e-13,
        root=root, candidate=candidate, context=context,
        structural_partitions=structural, onsets=onsets, switches=switches)
    pv.require(interval_distance(onset_interval, strict) <= 1e-10, "piecewise_unsplit")
    record(stage="direct_simpson")
    direct = float(simpson_average(
        np.max(function(np.linspace(0.0, 1.0, 65537, dtype=np.float64)), axis=1)[:, None]
    )[0])
    pv.require(point_interval_distance(direct, strict) <= 1e-9, "piecewise_direct")
    if historical_failure:
        first, _ = pv.split_simpson(function, structural, 32768)
        second, _ = pv.split_simpson(function, structural, 65536)
        pv.require(abs(first - second) <= 1e-10 and
                   point_interval_distance(first, strict) <= 1e-10 and
                   point_interval_distance(second, strict) <= 1e-10,
                   "split_simpson_agreement")
    return strict, {"strict": strict_evidence, "repeat": repeat_evidence,
                    "onset": onset_evidence}


def evaluate(candidate, origin, receiver, defenders, *, root: Path,
             authority_context: dict, synthetic=False, historical_failure=False,
             record=lambda **kw: None):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        record(stage="geometry")
        base, defence, _ = validate_geometry(origin, defenders)
        end = points(receiver, one=True)
        field = CarrierOriginField(candidate)
        endpoint = field.individual_values(base, defence, end[None, :])[0]
        union = float(combine(endpoint[None, :], "union")[0])
        maximum = float(np.max(endpoint))
        if math.dist(base, end) <= 1e-9:
            estimates = {**{f"individual_{i+1}": float(x) for i, x in enumerate(endpoint)},
                         "union": union, "maximum": maximum}
            record(stage="accepted")
            return VerifiedEdge(tuple(endpoint), tuple(endpoint), union, maximum,
                                union, maximum, 0, 0.0, 0.0), {
                "estimates": estimates, "degenerate": True,
                "certificate_evidence": None,
            }
        record(stage="joint_simpson")
        count, estimates, change = controlled_vector(
            lambda n: values_for_components(field, base, end, defence, n))
        pv.require(count is not None, "controlled_nonconvergence")

        def function(t):
            return field.individual_values(
                base, defence, base[None, :] + t[:, None] * (end - base)[None, :])

        record(stage="envelope")
        record(stage="owner_certification")
        structure = owner.canonical_geometry(candidate, base, end, defence, function)
        onsets, envelope, partitions, switches, witnesses = structure
        pv.require(structure == owner.canonical_geometry(candidate, base, end, defence, function),
                   "nondeterminism")
        permutations = 0
        continuity = False
        if synthetic:
            continuity = pv.check_continuity(candidate, base, defence)
            pv.require(continuity, "continuity")
            identity = tuple(range(len(defence)))
            signature = mapped_signature(envelope, identity)
            for permutation in itertools.permutations(identity):
                other = owner.canonical_geometry(
                    candidate, base, end, defence[list(permutation)],
                    lambda t, p=permutation: function(t)[:, p])
                pv.check_permutation(signature, mapped_signature(other[1], permutation))
                pv.require(partitions == other[2], "canonical_permutation")
                permutations += 1
        record(stage="partition_construction")
        runtime_context = {**authority_context, "origin": tuple(map(float, base)),
                           "receiver": tuple(map(float, end)),
                           "defenders": tuple(tuple(map(float, row)) for row in defence)}
        interval, certificate_evidence = independent_maximum(
            function, partitions, onsets, switches, root=root, candidate=candidate,
            context=runtime_context, historical_failure=historical_failure, record=record)
        error = point_interval_distance(estimates["maximum"], interval)
        pv.require(error <= 1e-6, "joint_maximum_reference_error")
        record(stage="accepted")
        edge = VerifiedEdge(
            tuple(map(float, endpoint)),
            tuple(estimates[f"individual_{i+1}"] for i in range(len(defence))),
            union, maximum, estimates["union"], estimates["maximum"], count, change, error)
        return edge, {
            "estimates": estimates, "intervals": count, "change": change,
            "permutations": permutations, "partitions": partitions,
            "maximum_interval": asdict(interval), "degenerate": False,
            "continuity": continuity, "deterministic": True,
            "canonical_onsets": [(x.defender_index, x.branch, x.last_pre_branch, x.canonical)
                                  for x in onsets],
            "canonical_switches": [(x.last_pre_switch, x.exact_zero_start,
                                      x.exact_zero_end, x.canonical,
                                      x.owners_before, x.owners_at, x.owners_after,
                                      x.crossing_pairs) for x in switches],
            "certificate_evidence": certificate_evidence,
        }


def evaluate_edge(candidate, origin, receiver, defenders, *, root: Path,
                  authority_context: dict, record=lambda **kw: None):
    return evaluate(candidate, origin, receiver, defenders, root=root,
                    authority_context=authority_context, record=record)[0]


__all__ = ["evaluate", "evaluate_edge", "independent_maximum"]
