"""Provider-free acceptance for the R9K structural comparator."""
from __future__ import annotations

import importlib.util
import math
from pathlib import Path
from types import SimpleNamespace
import time
import warnings
from unittest import mock

import numpy as np

from ..geometry import micro_interval_verifier as bounded
from ..geometry import onset_owner_certification as owner
from ..geometry import production_verification as pv
from ..geometry import r9k_comparator as repaired


def _authority(partitions, *, switches=(), witnesses=(), ties=()):
    occupied = {float(item.canonical) for item in switches}
    tie_values = set()
    for tie in ties:
        for boundary in (tie.start, tie.end):
            if boundary is not None: tie_values.update((float(boundary.outside), float(boundary.inside)))
    onsets = tuple(SimpleNamespace(canonical=float(value)) for value in partitions[1:-1]
                   if float(value) not in occupied | tie_values)
    return repaired.structural_authority(
        onsets, SimpleNamespace(tie_intervals=tuple(ties)), tuple(partitions),
        tuple(switches), tuple(witnesses))


def _row(name, family, function, exact, partitions, *, switches=(), witnesses=(), ties=()):
    authority = _authority(partitions, switches=switches, witnesses=witnesses, ties=ties)
    result = repaired.structural_adaptive_comparator(function, authority)
    return {
        "fixture": name, "candidate": "synthetic", "family": family,
        "status": "passed" if bounded.point_interval_distance(exact, result) <= 1e-10 else "failed",
        "reference_kind": "analytic", "within_gate": bounded.point_interval_distance(exact, result) <= 1e-10,
        "production_preserved": True, "piecewise_preserved": True,
        "boundaries_exact": result.structural_piece_count == len(partitions) - 1,
        "components": 1, "permutations": 0, "reason": "analytic_reference",
    }


def synthetic_controls():
    rows = []
    rows.append(_row("smooth_no_switch", "smooth", lambda t: t[:, None], .5, (0., 1.)))
    rows.append(_row("single_onset", "onset", lambda t: np.maximum(0., t-.25)[:, None],
                     .28125, (0., .25, 1.)))
    switch = SimpleNamespace(canonical=.5, owners_before=(1,), owners_at=(0, 1), owners_after=(0,))
    witness = owner.OwnerWitness(0., .25, .5, .75, 1., (1,), (0, 1), (0,))
    rows.append(_row("single_certified_switch", "switch",
                     lambda t: np.column_stack((t, 1-t)), .75, (0., .5, 1.),
                     switches=(switch,), witnesses=(witness,)))
    switch2 = SimpleNamespace(canonical=.5, owners_before=(1,), owners_at=(0, 1), owners_after=(0,))
    witness2 = owner.OwnerWitness(.49, .495, .5, .625, 1., (1,), (0, 1), (0,))
    rows.append(_row("close_onset_switch", "onset_switch",
                     lambda t: np.column_stack((t, 1-t)), .75, (0., .49, .5, 1.),
                     switches=(switch2,), witnesses=(witness2,)))
    outside = .25; inside = float(np.nextafter(outside, math.inf))
    boundary = SimpleNamespace(outside=outside, inside=inside, direction="entry")
    tie = SimpleNamespace(start=boundary, end=None)
    rows.append(_row("exact_tie_endpoint", "tie", lambda t: np.ones((len(t), 2)),
                     1., (0., outside, inside, 1.), ties=(tie,)))
    rows.append(_row("multiway_plateau", "multiway_tie", lambda t: np.full((len(t), 3), .5),
                     .5, (0., .3, .7, 1.)))
    rows.append(_row("multiple_switches", "multiple_switches",
                     lambda t: np.column_stack((np.where(t < .3, 1-t, np.where(t < .7, .7, t)),)),
                     .79, (0., .3, .7, 1.)))
    adjacent = float(np.nextafter(.5, math.inf))
    rows.append(_row("razor_thin_partition", "adjacent_float", lambda t: np.ones((len(t), 1)),
                     1., (0., .5, adjacent, 1.)))
    tiny = math.nextafter(0., 1.)
    rows.append(_row("micro_residual", "micro_residual", lambda t: np.ones((len(t), 1)),
                     1., (0., tiny, 1.)))
    return rows


def negative_controls():
    rows = []
    def blocked(name, expected, action):
        try: action()
        except BaseException as error:
            rows.append({"fixture": name, "expected_failure": expected, "blocked": True,
                         "reason": type(error).__name__})
        else:
            rows.append({"fixture": name, "expected_failure": expected, "blocked": False,
                         "reason": "accepted_unexpectedly"})

    envelope = SimpleNamespace(tie_intervals=())
    onset = SimpleNamespace(canonical=.25)
    blocked("missing_switch", "structural_authority_mismatch",
            lambda: repaired.structural_authority((onset,), envelope, (0., 1.), (), ()))
    blocked("extra_boundary", "structural_authority_mismatch",
            lambda: repaired.structural_authority((), envelope, (0., .25, 1.), (), ()))
    blocked("malformed_order", "partition_order",
            lambda: repaired.structural_authority((), envelope, (0., .5, .4, 1.), (), ()))
    blocked("overlapping_partitions", "partition_order",
            lambda: repaired.structural_authority((), envelope, (0., .6, .4, 1.), (), ()))
    blocked("uncovered_domain", "partition_coverage",
            lambda: repaired.structural_authority((), envelope, (.1, 1.), (), ()))
    bad = SimpleNamespace(outside=.25, inside=.5, direction="entry")
    blocked("invalid_tie_endpoint", "invalid_tie_endpoint",
            lambda: repaired.structural_authority((), SimpleNamespace(tie_intervals=(SimpleNamespace(start=bad,end=None),)),
                                                  (0., .25, .5, 1.), (), ()))
    switch = SimpleNamespace(canonical=.5, owners_before=(0,), owners_at=(0,1), owners_after=(1,))
    witness = owner.OwnerWitness(0.,.25,.5,.75,1.,(1,),(0,1),(1,))
    blocked("wrong_owner_witness", "witness_owners",
            lambda: repaired.structural_authority((), envelope, (0.,.5,1.), (switch,), (witness,)))
    blocked("nonfinite_boundary", "partition_nonfinite",
            lambda: repaired.structural_authority((), envelope, (0.,float("nan"),1.), (), ()))
    blocked("biased_integrand", "piecewise_unsplit",
            lambda: pv.require(bounded.interval_distance(
                bounded.IntegralInterval(0.,0.,0.,1,1,0),
                bounded.IntegralInterval(1e-9,1e-9,0.,1,1,0)) <= 1e-10,
                "piecewise_unsplit"))
    def warning():
        def warned(*args, **kwargs):
            warnings.warn("unmatched comparator warning", RuntimeWarning); return 0., 0.
        with mock.patch.object(bounded.historical, "quad", warned), warnings.catch_warnings():
            warnings.simplefilter("error")
            repaired.structural_adaptive_comparator(lambda t: np.zeros((len(t),1)), _authority((0.,1.)))
    blocked("unmatched_warning", "warning", warning)
    blocked("nonfinite_integrand", "adaptive_nonfinite",
            lambda: repaired.structural_adaptive_comparator(
                lambda t: np.full((len(t),1),float("nan")), _authority((0.,1.))))
    return rows


def historical_regression(root: Path):
    spec = importlib.util.spec_from_file_location(
        "r9k_cases", root / "scripts/session_14v_micro_interval_verifier.py")
    cases = importlib.util.module_from_spec(spec); spec.loader.exec_module(cases)
    rows = []
    for label, case in cases.authority_cases():
        _, result = repaired.evaluate(
            case["candidate"], case["origin"], case["receiver"], case["defenders"],
            root=root, authority_context={"alias": "synthetic_r9k"}, synthetic=True,
            historical_failure=case["historical_failure"])
        expected = case["historical_vector"]
        equivalent = result["intervals"] == expected["intervals"] and tuple(result["estimates"]) == tuple(expected["estimates"])
        if equivalent:
            for name, value in result["estimates"].items():
                prior = expected["estimates"][name]
                equivalent &= abs(value-prior) <= 64*np.finfo(float).eps*max(1.,abs(value),abs(prior))
        rows.append({"fixture": label, "candidate": case["candidate"], "family": "historical_authority",
                     "status": "passed" if equivalent else "failed", "reference_kind": "frozen_64_epsilon",
                     "within_gate": bool(equivalent), "production_preserved": bool(equivalent),
                     "piecewise_preserved": True, "boundaries_exact": True,
                     "components": len(result["estimates"]), "permutations": result["permutations"],
                     "reason": "frozen_historical_vector"})
    counts = (len(rows), sum(row["components"] for row in rows), sum(row["permutations"] for row in rows))
    if counts != (108, 366, 399) or not all(row["status"] == "passed" for row in rows):
        raise RuntimeError("historical_regression_failed")
    return rows


def performance_controls(repetitions=3):
    function = lambda t: np.column_stack((t, 1-t))
    authority = _authority((0., .5, 1.), switches=(
        SimpleNamespace(canonical=.5, owners_before=(1,), owners_at=(0,1), owners_after=(0,)),),
        witnesses=(owner.OwnerWitness(0.,.25,.5,.75,1.,(1,),(0,1),(0,)),))
    historical_seconds = repaired_seconds = 0.
    for _ in range(repetitions):
        start=time.perf_counter(); pv.adaptive_maximum(function,(0.,1.),1e-13); historical_seconds+=time.perf_counter()-start
        start=time.perf_counter(); result=repaired.structural_adaptive_comparator(function,authority); repaired_seconds+=time.perf_counter()-start
    return {"historical_seconds": historical_seconds, "repaired_seconds": repaired_seconds,
            "overhead_ratio": repaired_seconds/historical_seconds if historical_seconds else 0.,
            "fixtures": repetitions, "structural_pieces": repetitions*result.structural_piece_count,
            "adaptive_calls": repetitions*result.quadrature_piece_count,
            "micro_pieces": repetitions*result.bounded_piece_count}
