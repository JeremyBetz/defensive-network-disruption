"""Explicit R9R orchestration: only canonical localization is prospective.

The evaluator body preserves R9K sequencing and calls its unchanged numerical
and certificate primitives. Historical sources are never mutated or replaced.
"""
from dataclasses import asdict
import itertools
import math
from pathlib import Path
import warnings
import numpy as np
from . import r9r_localization as owner
from . import r9k_comparator as comparator
from .r9k_comparator import (pv, historical, values_for_components, IntegralInterval,
    point_interval_distance, CarrierOriginField, combine, points, simpson_average,
    validate_geometry, VerifiedEdge, controlled_vector, mapped_signature)

independent_maximum = comparator.independent_maximum

def evaluate(candidate, origin, receiver, defenders, *, root: Path,
             authority_context: dict, synthetic=False, historical_failure=False,
             record=lambda **kw: None, localization_sink=lambda **kw: None, deadline=None):
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
        structure = owner.canonical_geometry(candidate, base, end, defence, function, deadline=deadline, sink=localization_sink)
        onsets, envelope, partitions, switches, witnesses = structure
        pv.require(structure == owner.canonical_geometry(candidate, base, end, defence, function, deadline=deadline, sink=localization_sink),
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
                    lambda t, p=permutation: function(t)[:, p], deadline=deadline, sink=localization_sink)
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
                  authority_context: dict, record=lambda **kw: None, localization_sink=lambda **kw: None, deadline=None):
    return evaluate(candidate, origin, receiver, defenders, root=root,
                    authority_context=authority_context, record=record, localization_sink=localization_sink, deadline=deadline)[0]
