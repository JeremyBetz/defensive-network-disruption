"""Deterministic, non-fitting diagnostics for the closed Session 3 M1 model."""

from __future__ import annotations

import math
import statistics

import numpy as np

from defensive_network_disruption.geometry.segment import point_to_segment_distance


QUANTILES = (0.05, 0.25, 0.5, 0.75, 0.95)
TIE_TOLERANCE = 1e-12


def segment_order_statistics(defenders, start, end):
    distances = sorted(point_to_segment_distance(item, start, end)[0] for item in defenders)
    if not distances:
        raise ValueError("at least one defender is required")
    padded = distances + [math.nan] * max(0, 3 - len(distances))
    return tuple(padded[:3])


def quantile_summary(values):
    array = np.asarray(values, dtype=np.float64)
    array = array[np.isfinite(array)]
    if array.size == 0:
        raise ValueError("finite values are required")
    points = np.quantile(array, QUANTILES)
    return {f"q{int(q * 100):02d}": float(value) for q, value in zip(QUANTILES, points, strict=True)}


def coefficient_summary(qc):
    aliases = sorted(qc["folds"])
    result = {}
    for model in ("m0", "m1"):
        names = qc["folds"][aliases[0]][model]["feature_names"]
        rows = [qc["folds"][alias][model]["parameters"]["coefficients"] for alias in aliases]
        result[model] = {}
        for index, name in enumerate(names):
            values = [float(row[index]) for row in rows]
            result[model][name] = {
                "positive_folds": sum(value > 0 for value in values),
                "negative_folds": sum(value < 0 for value in values),
                "zero_folds": sum(value == 0 for value in values),
                "minimum": min(values),
                "median": statistics.median(values),
                "maximum": max(values),
            }
    return result


def within_choice_centered_correlation(feature_sets, weights=None):
    if not feature_sets:
        raise ValueError("choice sets are required")
    if weights is None:
        weights = [1.0 / len(feature_sets)] * len(feature_sets)
    covariance = np.zeros((feature_sets[0].shape[1],) * 2, dtype=np.float64)
    for matrix, attempt_weight in zip(feature_sets, weights, strict=True):
        centered = matrix - matrix.mean(axis=0)
        covariance += attempt_weight * (centered.T @ centered) / len(matrix)
    scales = np.sqrt(np.diag(covariance))
    if np.any(scales == 0):
        raise ValueError("zero within-choice variance")
    correlation = covariance / np.outer(scales, scales)
    singular = np.linalg.svd(correlation, compute_uv=False)
    tolerance = max(correlation.shape) * np.finfo(np.float64).eps * singular[0]
    rank = int(np.sum(singular > tolerance))
    condition = math.inf if singular[-1] <= tolerance else float(singular[0] / singular[-1])
    return correlation, {"rank": rank, "columns": correlation.shape[1],
                         "svd_tolerance": float(tolerance), "condition_number": condition}


def ordering_disagreement(first, second, *, tolerance=TIE_TOLERANCE):
    first = np.asarray(first, dtype=np.float64)
    second = np.asarray(second, dtype=np.float64)
    if first.shape != second.shape or first.ndim != 1:
        raise ValueError("two equally shaped vectors are required")
    comparable = 0
    discordant = 0
    for left in range(len(first)):
        for right in range(left + 1, len(first)):
            delta_first = first[left] - first[right]
            delta_second = second[left] - second[right]
            if abs(delta_first) <= tolerance or abs(delta_second) <= tolerance:
                continue
            comparable += 1
            discordant += int(delta_first * delta_second < 0)
    return {"comparable_pairs": comparable, "discordant_pairs": discordant,
            "fraction": discordant / comparable if comparable else None}


def numerical_nondegenerate(values):
    array = np.asarray(values, dtype=np.float64)
    array = array[np.isfinite(array)]
    if array.size < 2:
        return False, math.nan
    observed_range = float(np.ptp(array))
    tolerance = array.size * np.finfo(np.float64).eps * max(float(np.max(np.abs(array))), 1.0)
    return bool(observed_range > tolerance), tolerance


def utility(raw_features, coefficients, mean, scale):
    arrays = [np.asarray(item, dtype=np.float64) for item in (raw_features, coefficients, mean, scale)]
    if any(not np.isfinite(item).all() for item in arrays) or np.any(arrays[3] <= 0):
        raise ValueError("finite features/parameters and positive scales are required")
    return float(((arrays[0] - arrays[2]) / arrays[3]) @ arrays[1])


def fold_change_summary(values):
    return {"minimum": min(values), "median": statistics.median(values), "maximum": max(values)}
