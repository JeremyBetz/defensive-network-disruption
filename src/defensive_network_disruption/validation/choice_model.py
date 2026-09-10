"""Unregularized conditional-softmax fitting for frozen Session 3 models."""

from __future__ import annotations

import numpy as np
from scipy.optimize import linprog, minimize
from scipy.special import logsumexp


def weighted_standardization(features_by_match):
    match_means = []
    for choices in features_by_match.values():
        match_means.append(np.mean([np.mean(x, axis=0) for x in choices], axis=0))
    mean = np.mean(match_means, axis=0)
    match_vars = []
    for choices in features_by_match.values():
        match_vars.append(np.mean([np.mean((x - mean) ** 2, axis=0) for x in choices], axis=0))
    scale = np.sqrt(np.mean(match_vars, axis=0))
    zero = scale == 0
    scale[zero] = 1.0
    return mean, scale, zero


def within_choice_differences(feature_sets, target_indices):
    return np.vstack([
        x[target] - np.delete(x, target, axis=0)
        for x, target in zip(feature_sets, target_indices, strict=True)
    ])


def identifiability(differences):
    if differences.ndim != 2 or differences.shape[0] == 0:
        raise ValueError("within-choice differences must be a nonempty matrix")
    singular = np.linalg.svd(differences, compute_uv=False)
    tolerance = max(differences.shape) * np.finfo(np.float64).eps * singular[0]
    rank = int(np.sum(singular > tolerance))
    complete = linprog(
        np.zeros(differences.shape[1]), A_ub=-differences,
        b_ub=-np.ones(differences.shape[0]), bounds=[(None, None)] * differences.shape[1],
        method="highs",
    ).success
    # Maximize total nonnegative margin under an L1-bounded direction.
    p = differences.shape[1]
    objective = -np.r_[differences.sum(axis=0), -differences.sum(axis=0)]
    constraints = np.c_[-differences, differences]
    quasi_result = linprog(
        objective, A_ub=np.vstack([constraints, np.ones((1, 2 * p))]),
        b_ub=np.r_[np.zeros(differences.shape[0]), 1.0], bounds=[(0, None)] * (2 * p),
        method="highs",
    )
    quasi = quasi_result.success and -quasi_result.fun > 1e-10
    return {"rank": rank, "columns": p, "svd_tolerance": tolerance,
            "complete_separation": complete, "quasi_separation": quasi}


def conditional_objective(beta, features_by_match, targets_by_match):
    """Return the frozen equal-match conditional-softmax loss and gradient."""
    matches = sorted(features_by_match)
    if not matches or set(matches) != set(targets_by_match):
        raise ValueError("matching nonempty feature and target groups are required")
    p = len(beta)
    loss = 0.0
    gradient = np.zeros(p, dtype=np.float64)
    for match in matches:
        if not features_by_match[match]:
            raise ValueError("every training match requires fit-eligible observations")
        match_loss = 0.0
        match_gradient = np.zeros(p, dtype=np.float64)
        for x, target in zip(features_by_match[match], targets_by_match[match], strict=True):
            scores = x @ beta
            normalizer = logsumexp(scores)
            probabilities = np.exp(scores - normalizer)
            match_loss += normalizer - scores[target]
            match_gradient += probabilities @ x - x[target]
        loss += match_loss / len(features_by_match[match])
        gradient += match_gradient / len(features_by_match[match])
    return loss / len(matches), gradient / len(matches)


def fit_conditional_softmax(features_by_match, targets_by_match):
    matches = sorted(features_by_match)
    feature_sets = [x for match in matches for x in features_by_match[match]]
    targets = [x for match in matches for x in targets_by_match[match]]
    differences = within_choice_differences(feature_sets, targets)
    gate = identifiability(differences)
    if gate["rank"] != gate["columns"] or gate["complete_separation"] or gate["quasi_separation"]:
        raise RuntimeError(f"unregularized identifiability gate failed: {gate}")

    p = feature_sets[0].shape[1]
    objective = lambda beta: conditional_objective(beta, features_by_match, targets_by_match)

    result = minimize(
        objective, np.zeros(p), method="L-BFGS-B", jac=True,
        options={"maxiter": 2000, "maxls": 50, "ftol": 1e-12, "gtol": 1e-8},
    )
    _, gradient = objective(result.x)
    max_gradient = float(np.max(np.abs(gradient)))
    if not result.success or not np.isfinite(result.x).all() or not np.isfinite(result.fun) or max_gradient > 1e-6:
        raise RuntimeError(f"optimization gate failed: success={result.success}, gradient={max_gradient}")
    return result.x, {**gate, "iterations": int(result.nit), "objective": float(result.fun),
                      "max_abs_gradient": max_gradient}
