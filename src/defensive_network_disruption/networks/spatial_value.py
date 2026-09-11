"""Internal progression bookkeeping; no loading, fitting or causal semantics."""
from dataclasses import dataclass
from typing import Protocol
import math
import sys
from .options import OptionState, OptionNetwork


class SpatialValueSurface(Protocol):
    def value_at(self, x: float, y: float) -> float: ...


@dataclass(frozen=True)
class NormalizedGoalwardProgression:
    pitch_length: float

    def __post_init__(self):
        if isinstance(self.pitch_length, (bool, str)) or not math.isfinite(self.pitch_length) or self.pitch_length <= 0:
            raise ValueError('pitch_length must be finite positive numeric metres')

    def value_at(self, x: float, y: float) -> float:
        if any(isinstance(v, (bool, str)) or not math.isfinite(v) for v in (x, y)):
            raise ValueError('coordinates must be finite numeric metres')
        if not -self.pitch_length / 2 <= x <= self.pitch_length / 2:
            raise ValueError('longitudinal_bound_violation')
        return 0.5 + x / self.pitch_length


def identity_check(left, right, summands):
    tolerance = 64 * sys.float_info.epsilon * max(1., math.fsum(abs(x) for x in summands), abs(left), abs(right))
    if not all(math.isfinite(x) for x in (left, right, tolerance)) or abs(left-right) > tolerance:
        raise ValueError('numerical_identity_failed')
    return abs(left-right)


def sign(value):
    if not math.isfinite(value):
        raise ValueError('nonfinite sign input')
    return 'negative' if value < -1e-12 else 'positive' if value > 1e-12 else 'zero'


@dataclass(frozen=True)
class ValueHorizon:
    receiver_ids: tuple[str, ...]
    receiver_values: tuple[float, ...]
    destination_changes: tuple[float, ...]
    shares: tuple[float, ...]
    horizon: float


@dataclass(frozen=True)
class ValueComparison:
    m0: ValueHorizon
    m1: ValueHorizon
    contributions: tuple[float, ...]
    shift: float
    maximum_identity_residual: float


def horizon(state: OptionState, network: OptionNetwork, surface: SpatialValueSurface) -> ValueHorizon:
    if tuple(e.receiver_id for e in network.edges) != state.candidate_ids or network.carrier_id != state.carrier_id:
        raise ValueError('state/network candidate or carrier alignment mismatch')
    values = tuple(surface.value_at(*xy) for xy in state.candidate_xy)
    carrier = surface.value_at(*state.carrier_xy)
    if not all(math.isfinite(v) and 0 <= v <= 1 for v in (*values, carrier)):
        raise ValueError('surface values must be finite and bounded')
    shares = tuple(e.option_share for e in network.edges)
    if not all(math.isfinite(p) and 0 <= p <= 1 for p in shares):
        raise ValueError('invalid option shares')
    identity_check(math.fsum(shares), 1., shares)
    changes = tuple(v-carrier for v in values)
    terms = tuple(p*d for p,d in zip(shares, changes))
    return ValueHorizon(state.candidate_ids, values, changes, shares, math.fsum(terms))


def compare_horizons(state, m0, m1, surface):
    left, right = horizon(state,m0,surface), horizon(state,m1,surface)
    diff = tuple(b-a for a,b in zip(left.shares,right.shares))
    contributions = tuple(p*d for p,d in zip(diff,left.destination_changes))
    shift = right.horizon-left.horizon
    terms = tuple(p*v for p,v in zip(diff,left.receiver_values))
    residuals = [identity_check(shift,math.fsum(contributions),contributions),
                 identity_check(shift,math.fsum(terms),terms)]
    if isinstance(surface,NormalizedGoalwardProgression):
        terms = tuple(p*xy[0]/surface.pitch_length for p,xy in zip(diff,state.candidate_xy))
        residuals.append(identity_check(shift,math.fsum(terms),terms))
        for h in (left,right):
            terms = tuple(p*(xy[0]-state.carrier_xy[0])/surface.pitch_length for p,xy in zip(h.shares,state.candidate_xy))
            residuals.append(identity_check(h.horizon,math.fsum(terms),terms))
    return ValueComparison(left,right,contributions,shift,max(residuals))
