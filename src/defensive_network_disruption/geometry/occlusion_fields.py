"""Internal fixed carrier-origin field hypotheses, without models or data I/O.

Field strengths are dimensionless geometric descriptors, never probabilities.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np

CANDIDATES = ("isotropic", "expanding", "constant_width")
SIGMA = 2.0
ONSET = 1.0
ANGLE = math.radians(10.0)
ORIGIN_TOLERANCE = 1e-9
QUADRATURE_TOLERANCE = 1e-6


class FieldError(ValueError):
    """Sanitized field-contract error."""


class QuadratureError(FieldError):
    """The frozen coarse/fine comparison failed; no finer fallback is allowed."""

    def __init__(self, diagnostics):
        super().__init__("quadrature_agreement_failed")
        self.diagnostics = diagnostics


def points(values, *, one=False):
    """Require explicit finite numeric XY; do not coerce strings or booleans."""
    raw = np.asarray(values)
    if raw.dtype.kind not in "iuf" or raw.dtype.kind == "b":
        raise FieldError("finite_numeric_coordinates_required")
    result = np.asarray(values, dtype=np.float64)
    if one:
        if result.shape != (2,):
            raise FieldError("one_xy_point_required")
    elif result.ndim != 2 or result.shape[1] != 2 or not len(result):
        raise FieldError("nonempty_xy_matrix_required")
    if not np.isfinite(result).all():
        raise FieldError("finite_numeric_coordinates_required")
    return result


def validate_geometry(origin, defenders):
    b, ds = points(origin, one=True), points(defenders)
    with np.errstate(over="ignore", invalid="ignore"):
        radius = np.hypot(*(ds-b).T)
    if not np.isfinite(radius).all():
        raise FieldError("coordinate_arithmetic_overflow")
    if np.any(radius <= ORIGIN_TOLERANCE):
        raise FieldError("origin_defender_direction_undefined")
    return b, ds, radius


@dataclass(frozen=True)
class EdgeFieldSummary:
    receiver_individual: tuple[float, ...]
    segment_individual: tuple[float, ...]
    receiver_union: float
    receiver_maximum: float
    segment_union: float
    segment_maximum: float
    coarse_intervals: int
    fine_intervals: int
    maximum_agreement_error: float


@dataclass(frozen=True)
class CarrierOriginField:
    """One frozen candidate; arbitrary scale overrides are not accepted."""

    candidate: str

    def __post_init__(self):
        if self.candidate not in CANDIDATES:
            raise FieldError("unknown_candidate")

    def individual_values(self, origin, defenders, queries):
        """Return query-by-defender values in [0,1]."""
        b, ds, radii = validate_geometry(origin, defenders)
        qs = points(queries)
        with np.errstate(over="ignore", invalid="ignore", under="ignore"):
            diff = qs[:, None, :] - ds[None, :, :]
            if self.candidate == "isotropic":
                distance = np.hypot(diff[..., 0], diff[..., 1])
                values = np.exp(-0.5 * (distance / SIGMA)**2)
            else:
                unit = (ds-b) / radii[:, None]
                ell = diff[..., 0]*unit[None, :, 0] + diff[..., 1]*unit[None, :, 1]
                h = np.abs(diff[..., 0]*unit[None, :, 1] - diff[..., 1]*unit[None, :, 0])
                t = np.clip(ell/ONSET, 0.0, 1.0)
                gate = t*t*(3.0-2.0*t)
                width = SIGMA + (np.maximum(ell, 0.0)*math.tan(ANGLE)
                                 if self.candidate == "expanding" else 0.0)
                values = gate * np.exp(-0.5*(h/width)**2)
        if not np.isfinite(values).all() or np.any(values<0) or np.any(values>1):
            raise FieldError("field_bounds_or_arithmetic")
        return values

    def combined_values(self, origin, defenders, queries, *, combination="union"):
        return combine(self.individual_values(origin, defenders, queries), combination)

    def summarize_edge(self, origin, receiver, defenders):
        """Endpoint and segment-average field with the frozen accuracy check."""
        b = points(origin, one=True)
        end = points(receiver, one=True)
        endpoint = self.individual_values(b, defenders, end[None, :])[0]
        length = math.hypot(*(end-b))
        if not math.isfinite(length):
            raise FieldError("coordinate_arithmetic_overflow")
        if length <= ORIGIN_TOLERANCE:
            a = tuple(float(x) for x in endpoint)
            return EdgeFieldSummary(a, a, float(combine(endpoint[None,:], "union")[0]),
                float(max(endpoint)), float(combine(endpoint[None,:], "union")[0]),
                float(max(endpoint)), 0, 0, 0.0)
        ns = tuple(max(2, 2*math.ceil(length/(2*spacing))) for spacing in (0.25, 0.125))
        integrals = []
        for n in ns:
            t = np.linspace(0.0, 1.0, n+1, dtype=np.float64)
            vals = self.individual_values(b, defenders, b[None,:]+t[:,None]*(end-b)[None,:])
            all_values = np.column_stack((vals, combine(vals, "union"), combine(vals, "maximum")))
            integrals.append(simpson_average(all_values))
        error = np.abs(integrals[1]-integrals[0])
        if np.any(error > QUADRATURE_TOLERANCE):
            names = ["individual"]*len(endpoint)+["union", "maximum"]
            index = int(np.argmax(error))
            raise QuadratureError({"candidate":self.candidate,"coarse_intervals":ns[0],
                "fine_intervals":ns[1],"component":names[index],
                "coarse_value":float(integrals[0][index]),"fine_value":float(integrals[1][index]),
                "absolute_difference":float(error[index]),"allowed_difference":QUADRATURE_TOLERANCE})
        fine = integrals[1]
        return EdgeFieldSummary(tuple(float(x) for x in endpoint),
            tuple(float(x) for x in fine[:-2]), float(combine(endpoint[None,:], "union")[0]),
            float(max(endpoint)), float(fine[-2]), float(fine[-1]), ns[0], ns[1], float(max(error)))


def combine(values, rule):
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 2 or not array.shape[1] or not np.isfinite(array).all() or np.any(array<0) or np.any(array>1):
        raise FieldError("combination_values_invalid")
    if rule == "maximum":
        return np.max(array, axis=1)
    if rule != "union":
        raise FieldError("unknown_combination")
    result = np.empty(len(array), dtype=np.float64)
    for i,row in enumerate(array):
        if np.any(row == 1.0):
            result[i] = 1.0
        else:
            result[i] = -math.expm1(math.fsum(math.log1p(-float(v)) for v in sorted(row)))
    return result


def simpson_average(values):
    """Composite Simpson on uniform t in [0,1], independently per column."""
    values = np.asarray(values, dtype=np.float64)
    if values.ndim != 2 or len(values)<3 or (len(values)-1)%2 or not np.isfinite(values).all():
        raise FieldError("simpson_shape_or_values")
    n = len(values)-1
    return np.array([math.fsum([float(column[0]),float(column[-1]),
        4*math.fsum(float(x) for x in column[1:-1:2]),
        2*math.fsum(float(x) for x in column[2:-1:2])])/(3*n) for column in values.T])
