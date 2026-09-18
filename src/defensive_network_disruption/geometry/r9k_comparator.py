"""Prospective R9K structural adaptive comparator.

Historical R9E orchestration remains unchanged.  This adapter composes its
production and certificate-aware piece primitives while evaluating the
whole-integral comparator through the separate bounded-adaptive implementation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import itertools
import json
import math
from pathlib import Path
import warnings

import numpy as np

from . import onset_owner_certification as owner
from . import production_verification as pv
from . import r9e_representation as historical
from .integration_review import values_for_components
from .micro_interval_verifier import (
    IntegralInterval,
    bounded_adaptive_maximum,
    interval_distance,
    point_interval_distance,
)
from .occlusion_fields import CarrierOriginField, combine, points, simpson_average, validate_geometry
from .representation_study import VerifiedEdge
from .verification_audit import controlled_vector
from .verification_repair import mapped_signature


def _canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


@dataclass(frozen=True)
class StructuralComparatorAuthority:
    """Exact pre-result structural boundaries accepted by the comparator."""

    partitions: tuple[float, ...]
    onset_coordinates: tuple[float, ...]
    switch_coordinates: tuple[float, ...]
    tie_endpoints: tuple[float, ...]
    witness_sha256: str
    authority_sha256: str


def structural_authority(onsets, envelope, partitions, switches, witnesses) -> StructuralComparatorAuthority:
    """Validate that the comparator consumes the complete certified structure."""
    onset_coordinates = tuple(float(item.canonical) for item in onsets)
    switch_coordinates = tuple(float(item.canonical) for item in switches)
    tie_endpoints = []
    for tie in envelope.tie_intervals:
        for boundary in (tie.start, tie.end):
            if boundary is None:
                continue
            outside, inside = float(boundary.outside), float(boundary.inside)
            pv.require(float(np.nextafter(outside, inside)) == inside, "invalid_tie_endpoint")
            pv.require((outside < inside) == (boundary.direction == "entry"),
                       "invalid_tie_direction")
            tie_endpoints.extend((outside, inside))

    parts = tuple(float(value) for value in partitions)
    pv.require(len(parts) >= 2 and parts[0] == 0.0 and parts[-1] == 1.0,
               "partition_coverage")
    pv.require(all(math.isfinite(value) and 0.0 <= value <= 1.0 for value in parts),
               "partition_nonfinite")
    pv.require(all(right > left for left, right in zip(parts[:-1], parts[1:], strict=True)),
               "partition_order")
    expected = tuple(sorted({0.0, 1.0, *onset_coordinates,
                             *switch_coordinates, *tie_endpoints}))
    pv.require(parts == expected, "structural_authority_mismatch")
    pv.require(len(switches) == len(witnesses), "witness_count")

    witness_rows = []
    for switch, witness in zip(switches, witnesses, strict=True):
        pv.require(float(switch.canonical) == float(witness.canonical),
                   "witness_coordinate")
        pv.require((tuple(switch.owners_before), tuple(switch.owners_at),
                    tuple(switch.owners_after)) ==
                   (tuple(witness.owners_before), tuple(witness.owners_at),
                    tuple(witness.owners_after)), "witness_owners")
        pv.require(witness.left_limit < witness.before < witness.canonical <
                   witness.after < witness.right_limit, "witness_order")
        witness_rows.append({
            "left": float(witness.left_limit), "before": float(witness.before),
            "canonical": float(witness.canonical), "after": float(witness.after),
            "right": float(witness.right_limit),
            "owners_before": list(witness.owners_before),
            "owners_at": list(witness.owners_at),
            "owners_after": list(witness.owners_after),
        })
    witness_sha256 = hashlib.sha256(_canonical(witness_rows)).hexdigest()
    payload = {
        "partitions": list(parts), "onsets": list(onset_coordinates),
        "switches": list(switch_coordinates), "tie_endpoints": tie_endpoints,
        "witness_sha256": witness_sha256,
    }
    return StructuralComparatorAuthority(
        parts, onset_coordinates, switch_coordinates, tuple(tie_endpoints),
        witness_sha256, hashlib.sha256(_canonical(payload)).hexdigest())


def structural_adaptive_comparator(function, authority: StructuralComparatorAuthority,
                                   *, record=lambda **kw: None) -> IntegralInterval:
    """Independently integrate over certified cuts without certificate lookup."""
    before = getattr(function, "_r9k_comparator_calls", None)
    result = bounded_adaptive_maximum(function, authority.partitions, 1e-13)
    record(
        structural_pieces=result.structural_piece_count,
        adaptive_calls=result.quadrature_piece_count,
        micro_pieces=result.bounded_piece_count,
        authority_sha256=authority.authority_sha256,
    )
    # The optional marker is test-only and may not be mutated by the comparator.
    pv.require(getattr(function, "_r9k_comparator_calls", None) == before,
               "comparator_mutated_integrand")
    return result


def independent_maximum(function, partitions, onsets, envelope, switches, witnesses,
                        *, root: Path, candidate: str, context: dict,
                        historical_failure=False, record=lambda **kw: None):
    """Preserve historical verification except for the structural comparator."""
    structural = tuple(partitions)
    authority = structural_authority(onsets, envelope, structural, switches, witnesses)
    widths = [right - left for left, right in zip(structural[:-1], structural[1:], strict=True)]
    bounded = sum(width <= 1e-12 / len(widths) for width in widths)
    record(stage="routing", pieces=len(widths), bounded=bounded,
           quadrature=len(widths) - bounded)
    record(stage="strict_piecewise")
    strict, strict_evidence = historical._integrate(
        function, structural, 1e-13, root=root, candidate=candidate,
        context=context, structural_partitions=structural, onsets=onsets,
        switches=switches)
    record(stage="repeat_piecewise")
    repeat, repeat_evidence = historical._integrate(
        function, structural, 1e-11, root=root, candidate=candidate,
        context=context, structural_partitions=structural, onsets=onsets,
        switches=switches)
    pv.require(interval_distance(strict, repeat) <= 1e-10, "piecewise_repeat")
    record(stage="onset_adaptive")
    comparator_rows = []
    comparator = structural_adaptive_comparator(
        function, authority, record=lambda **row: comparator_rows.append(row))
    pv.require(interval_distance(comparator, strict) <= 1e-10, "piecewise_unsplit")
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
    return strict, {
        "strict": strict_evidence, "repeat": repeat_evidence,
        "comparator": asdict(comparator), "comparator_work": comparator_rows[0],
        "structural_authority": asdict(authority),
    }


def evaluate(candidate, origin, receiver, defenders, *, root: Path,
             authority_context: dict, synthetic=False, historical_failure=False,
             record=lambda **kw: None):
    """Evaluate one edge using unchanged production and repaired comparison."""
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
            estimates = {**{f"individual_{i+1}": float(value)
                            for i, value in enumerate(endpoint)},
                         "union": union, "maximum": maximum}
            record(stage="accepted")
            return VerifiedEdge(tuple(endpoint), tuple(endpoint), union, maximum,
                                union, maximum, 0, 0.0, 0.0), {
                "estimates": estimates, "degenerate": True,
                "certificate_evidence": None,
            }
        record(stage="joint_simpson")
        count, estimates, change = controlled_vector(
            lambda intervals: values_for_components(field, base, end, defence, intervals))
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
            function, partitions, onsets, envelope, switches, witnesses,
            root=root, candidate=candidate, context=runtime_context,
            historical_failure=historical_failure, record=record)
        error = point_interval_distance(estimates["maximum"], interval)
        pv.require(error <= 1e-6, "joint_maximum_reference_error")
        record(stage="accepted")
        edge = VerifiedEdge(
            tuple(map(float, endpoint)),
            tuple(estimates[f"individual_{index + 1}"] for index in range(len(defence))),
            union, maximum, estimates["union"], estimates["maximum"], count, change, error)
        return edge, {
            "estimates": estimates, "intervals": count, "change": change,
            "permutations": permutations, "partitions": partitions,
            "maximum_interval": asdict(interval), "degenerate": False,
            "continuity": continuity, "deterministic": True,
            "canonical_onsets": [
                (item.defender_index, item.branch, item.last_pre_branch, item.canonical)
                for item in onsets],
            "canonical_switches": [
                (item.last_pre_switch, item.exact_zero_start, item.exact_zero_end,
                 item.canonical, item.owners_before, item.owners_at,
                 item.owners_after, item.crossing_pairs) for item in switches],
            "certificate_evidence": certificate_evidence,
        }


def evaluate_edge(candidate, origin, receiver, defenders, *, root: Path,
                  authority_context: dict, record=lambda **kw: None):
    return evaluate(candidate, origin, receiver, defenders, root=root,
                    authority_context=authority_context, record=record)[0]


__all__ = ["StructuralComparatorAuthority", "evaluate", "evaluate_edge",
           "independent_maximum", "structural_adaptive_comparator",
           "structural_authority"]
