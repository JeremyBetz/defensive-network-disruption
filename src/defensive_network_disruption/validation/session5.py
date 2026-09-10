"""Frozen feature and fail-closed feasibility helpers for Session 5."""

from __future__ import annotations

import numpy as np
from scipy.optimize import linprog

from defensive_network_disruption.geometry.attenuation import summed_segment_attenuation
from defensive_network_disruption.validation.choice_model import (
    fit_conditional_softmax,
    within_choice_differences,
)
from defensive_network_disruption.validation.ranking_features import M1_NAMES, choice_features


M2_NAMES = M1_NAMES + ("summed_segment_attenuation",)
QUASI_MARGIN_TOLERANCE = 1e-10


def choice_features_m1_m2(choice):
    """Return exactly nested M1 and M2 feature matrices."""
    m1, degenerate = choice_features(choice, "m1")
    attenuation = np.asarray([
        summed_segment_attenuation(choice.defender_xy, choice.carrier_xy, receiver)
        for receiver in choice.candidate_xy
    ], dtype=np.float64)
    m2 = np.column_stack((m1, attenuation))
    if not np.array_equal(m1, m2[:, : len(M1_NAMES)]):
        raise RuntimeError("M1 raw columns are not exactly nested in M2")
    if not np.isfinite(m2).all():
        raise ValueError("M2 features must be finite")
    return m1, m2, degenerate


def fail_closed_identifiability(differences, *, linprog_fn=linprog):
    """Run the Session 3 gates while requiring conclusive LP solver states."""
    matrix = np.asarray(differences, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[0] == 0 or not np.isfinite(matrix).all():
        raise ValueError("finite nonempty within-choice differences are required")
    singular = np.linalg.svd(matrix, compute_uv=False)
    tolerance = max(matrix.shape) * np.finfo(np.float64).eps * singular[0]
    rank = int(np.sum(singular > tolerance))
    p = matrix.shape[1]

    complete_result = linprog_fn(
        np.zeros(p), A_ub=-matrix, b_ub=-np.ones(matrix.shape[0]),
        bounds=[(None, None)] * p, method="highs",
    )
    if complete_result.status not in {0, 2}:
        raise RuntimeError(f"complete-separation feasibility inconclusive: status={complete_result.status}")
    complete = complete_result.status == 0 and bool(complete_result.success)
    if complete_result.status == 2 and bool(complete_result.success):
        raise RuntimeError("inconsistent complete-separation solver result")

    objective = -np.r_[matrix.sum(axis=0), -matrix.sum(axis=0)]
    constraints = np.c_[-matrix, matrix]
    quasi_result = linprog_fn(
        objective,
        A_ub=np.vstack([constraints, np.ones((1, 2 * p))]),
        b_ub=np.r_[np.zeros(matrix.shape[0]), 1.0],
        bounds=[(0, None)] * (2 * p), method="highs",
    )
    if quasi_result.status != 0 or not bool(quasi_result.success) or not np.isfinite(quasi_result.fun):
        raise RuntimeError(f"quasi-separation optimization inconclusive: status={quasi_result.status}")
    quasi = bool(-quasi_result.fun > QUASI_MARGIN_TOLERANCE)
    return {
        "rank": rank, "columns": p, "svd_tolerance": float(tolerance),
        "complete_separation": complete, "complete_solver_status": int(complete_result.status),
        "quasi_separation": quasi, "quasi_solver_status": int(quasi_result.status),
    }


def fit_with_fail_closed_gate(features_by_match, targets_by_match):
    feature_sets = [matrix for match in sorted(features_by_match) for matrix in features_by_match[match]]
    targets = [target for match in sorted(targets_by_match) for target in targets_by_match[match]]
    differences = within_choice_differences(feature_sets, targets)
    gate = fail_closed_identifiability(differences)
    if gate["rank"] != gate["columns"] or gate["complete_separation"] or gate["quasi_separation"]:
        raise RuntimeError(f"fail-closed identifiability gate failed: {gate}")
    if differences.shape[1] == len(M2_NAMES):
        attenuation = differences[:, -1]
        scale = max(float(np.max(np.abs(attenuation))), 1.0)
        tolerance = len(attenuation) * np.finfo(np.float64).eps * scale
        if float(np.ptp(attenuation)) <= tolerance or not np.any(np.abs(attenuation) > tolerance):
            raise RuntimeError("attenuation has no numerical within-choice information")
    beta, fit_qc = fit_conditional_softmax(features_by_match, targets_by_match)
    return beta, {**fit_qc, **gate}
