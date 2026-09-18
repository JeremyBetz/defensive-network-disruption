"""R9J diagnostic-only constant-width enclosure; standard library, no field calls.

All inputs are exact binary64 rationals. No detector owner or quadrature result
is used as mathematical authority. This module cannot register a certificate.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F
from functools import lru_cache
import heapq
import math
import time

SCALE = 1 << 256
TARGET = F.from_float(1e-12)


def rational(x):
    if type(x) is not float or not math.isfinite(x):
        raise ValueError("finite_binary64_required")
    return F.from_float(x)


def down(x):
    return F((x.numerator * SCALE) // x.denominator, SCALE)


def up(x):
    return -down(-x)


@dataclass(frozen=True)
class Bounds:
    lo: F
    hi: F

    def __post_init__(self):
        if self.lo > self.hi:
            raise ValueError("reversed_bounds")

    @classmethod
    def point(cls, x):
        x = F(x)
        return cls(down(x), up(x))

    def __add__(self, other):
        other = other if isinstance(other, Bounds) else Bounds.point(other)
        return Bounds(down(self.lo + other.lo), up(self.hi + other.hi))

    __radd__ = __add__

    def __neg__(self):
        return Bounds(-self.hi, -self.lo)

    def __sub__(self, other):
        return self + -(other if isinstance(other, Bounds) else Bounds.point(other))

    def __mul__(self, other):
        other = other if isinstance(other, Bounds) else Bounds.point(other)
        products = (self.lo * other.lo, self.lo * other.hi,
                    self.hi * other.lo, self.hi * other.hi)
        return Bounds(down(min(products)), up(max(products)))

    __rmul__ = __mul__

    def __truediv__(self, other):
        other = other if isinstance(other, Bounds) else Bounds.point(other)
        if other.lo <= 0 <= other.hi:
            raise ValueError("division_contains_zero")
        return self * Bounds(down(1 / other.hi), up(1 / other.lo))

    def floats(self):
        a, b = float(self.lo), float(self.hi)
        if not math.isfinite(a) or not math.isfinite(b):
            raise ValueError("nonfinite_bound")
        if F.from_float(a) > self.lo:
            a = math.nextafter(a, -math.inf)
        if F.from_float(b) < self.hi:
            b = math.nextafter(b, math.inf)
        return a, b


def sqrt_bounds(q):
    q = F(q)
    if q < 0:
        raise ValueError("negative_square_root")
    n = math.isqrt((q.numerator * SCALE * SCALE) // q.denominator)
    lo = F(n, SCALE)
    hi = lo if lo * lo == q else F(n + 1, SCALE)
    return Bounds(lo, hi)


@lru_cache(maxsize=4096)
def exp_negative(x):
    """Enclose exp(-x), x>=0, by alternating series and interval squaring."""
    x = F(x)
    if x < 0:
        raise ValueError("negative_exponential_argument")
    shifts = 0
    y = x
    while y > F(1, 2):
        y /= 2
        shifts += 1
    term = total = F(1)
    for n in range(1, 33):
        term *= -y / n
        total += term
    next_term = abs(term * y / 33)
    result = Bounds(max(F(0), down(total - next_term)), min(F(1), up(total)))
    for _ in range(shifts):
        result = result * result
    return result


def smooth(x):
    x = min(F(1), max(F(0), x))
    return x * x * (3 - 2 * x)


def poly_mul(a, b):
    result = [Bounds.point(0) for _ in range(len(a) + len(b) - 1)]
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            result[i+j] = result[i+j] + x * y
    return result


@dataclass(frozen=True)
class Integrand:
    q: F
    dot: F
    lam: F
    rho: Bounds
    alpha: Bounds

    @classmethod
    def coefficients(cls, q, dot, lam):
        q, dot, lam = F(q), F(dot), F(lam)
        if q <= 0 or lam < 0:
            raise ValueError("invalid_integrand")
        rho = sqrt_bounds(q)
        return cls(q, dot, lam, rho, Bounds.point(dot) / rho)

    def range(self, a, b):
        ell = self.alpha * Bounds(a, b) - self.rho
        gate = Bounds(down(smooth(ell.lo)), up(smooth(ell.hi)))
        gaussian = Bounds(exp_negative(self.lam*b*b).lo,
                          exp_negative(self.lam*a*a).hi)
        return gate * gaussian, ell

    def integral(self, a, b, ell):
        if ell.hi <= 0:
            return Bounds.point(0)
        if not (ell.lo >= 1 or (ell.lo >= 0 and ell.hi <= 1)):
            return None
        c, h = (a+b)/2, (b-a)/2
        radius = self.lam * max(abs(a*a-c*c), abs(b*b-c*c))
        if radius > F(1, 2):
            return None
        if ell.lo >= 1:
            gate = [Bounds.point(1)]
        else:
            affine = [self.alpha*c-self.rho, self.alpha]
            square = poly_mul(affine, affine)
            cube = poly_mul(square, affine)
            gate = [3*(square[i] if i < len(square) else Bounds.point(0)) - 2*cube[i]
                    for i in range(4)]
        shift = [Bounds.point(0), Bounds.point(-2*self.lam*c), Bounds.point(-self.lam)]
        power = [Bounds.point(1)]
        exponential = [Bounds.point(1)]
        for n in range(1, 17):
            power = [x/n for x in poly_mul(power, shift)]
            exponential += [Bounds.point(0)] * (len(power)-len(exponential))
            exponential = [x+y for x, y in zip(exponential, power)]
        polynomial = poly_mul(gate, exponential)
        result = Bounds.point(0)
        for k in range(0, len(polynomial), 2):
            result += polynomial[k] * (2*h**(k+1)/F(k+1))
        result *= exp_negative(self.lam*c*c)
        remainder = 2*radius**17/F(math.factorial(17)) * (b-a)
        return Bounds(max(F(0), down(result.lo-remainder)),
                      min(b-a, up(result.hi+remainder)))


def from_geometry(origin, receiver, defenders):
    def point(p):
        if len(p) != 2:
            raise ValueError("xy_required")
        return tuple(rational(x) for x in p)
    b, r = point(origin), point(receiver)
    v = tuple(y-x for x, y in zip(b, r))
    fields = []
    for raw in defenders:
        d = point(raw)
        u = tuple(y-x for x, y in zip(b, d))
        q = sum(x*x for x in u)
        if q <= F.from_float(1e-9)**2:
            raise ValueError("origin_exclusion")
        dot = sum(x*y for x, y in zip(v, u))
        cross = v[0]*u[1]-v[1]*u[0]
        fields.append(Integrand.coefficients(q, dot, cross*cross/(8*q)))
    if not fields:
        raise ValueError("empty_defenders")
    # Only provably identical mathematical functions, never tolerance owners.
    return tuple({(f.q, f.dot, f.lam): f for f in fields}.values())


def cell_bound(fields, a, b):
    ranges = [f.range(a, b) for f in fields]
    fallback = Bounds(max(x[0].lo for x in ranges)*(b-a),
                      max(x[0].hi for x in ranges)*(b-a))
    for i, (value, ell) in enumerate(ranges):
        if all(i == j or value.lo >= other[0].hi for j, other in enumerate(ranges)):
            integral = fields[i].integral(a, b, ell)
            if integral is not None:
                return Bounds(max(fallback.lo, integral.lo), min(fallback.hi, integral.hi)), True
    return fallback, False


def enclose(fields, cuts, *, deadline=None, max_leaves=65536, max_depth=80):
    cuts = tuple(sorted(set(F(x) for x in cuts)))
    if len(cuts) < 2 or cuts[0] < 0 or cuts[-1] > 1:
        raise ValueError("reference_cuts")
    started = time.monotonic()
    heap, leaves = [], {}
    lower = upper = F(0)
    serial = 0
    def add(a, b, depth, group):
        nonlocal lower, upper, serial
        bound, smooth_owner = cell_bound(fields, a, b)
        entry = (a, b, depth, group, bound, smooth_owner)
        leaves[serial] = entry
        heapq.heappush(heap, (-(bound.hi-bound.lo), a, b, serial))
        lower += bound.lo; upper += bound.hi; serial += 1
    for group, (a, b) in enumerate(zip(cuts, cuts[1:])):
        if b <= a:
            raise ValueError("positive_reference_cell")
        add(a, b, 0, group)
    reason = "precision"
    while True:
        lo, hi = Bounds(lower, upper).floats()
        if hi-lo <= float(TARGET):
            break
        if deadline is not None and time.monotonic() >= deadline:
            reason = "deadline"; break
        if len(leaves) >= max_leaves:
            reason = "leaf_limit"; break
        _, _, _, key = heapq.heappop(heap)
        a, b, depth, group, bound, _ = leaves[key]
        if depth >= max_depth:
            reason = "depth_limit"; break
        del leaves[key]; lower -= bound.lo; upper -= bound.hi
        middle = (a+b)/2
        add(a, middle, depth+1, group); add(middle, b, depth+1, group)
    groups = []
    for group in range(len(cuts)-1):
        subset = [v for v in leaves.values() if v[3] == group]
        groups.append(Bounds(sum((x[4].lo for x in subset), F(0)),
                             sum((x[4].hi for x in subset), F(0))))
    return {"bound": Bounds(lower, upper), "groups": groups, "reason": reason,
            "eligible": reason == "precision", "leaves": len(leaves),
            "smooth_leaves": sum(x[5] for x in leaves.values()),
            "seconds": time.monotonic()-started}


def compare(point_or_interval, reference, tolerance):
    a, b = point_or_interval
    if not all(math.isfinite(x) for x in (a, b, tolerance)) or a > b:
        raise ValueError("comparison_input")
    a, b, tolerance = map(F.from_float, (a, b, tolerance))
    minimum = max(F(0), reference.lo-b, a-reference.hi)
    maximum = max(abs(a-reference.hi), abs(b-reference.lo))
    return {"accurate": maximum <= tolerance, "inaccurate": minimum > tolerance,
            "minimum": minimum, "maximum": maximum}
