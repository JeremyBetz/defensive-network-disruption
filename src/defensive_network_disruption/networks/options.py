"""Experimental carrier-centred option distributions, with no fitting or I/O.

Shares describe a conditional-choice model, not calibrated availability.
Install/use the repository's locked numerical environment for this experimental API.
"""
from __future__ import annotations
from dataclasses import dataclass
from types import MappingProxyType
import math
import numpy as np
from defensive_network_disruption.validation.ranking_features import choice_features, M0_NAMES, M1_NAMES
from defensive_network_disruption.validation.construct_diagnostics import rank_blocks, pair_comparison

SUMMARY_KEYS = ("top_one_share", "top_two_share", "entropy", "normalized_entropy",
                "effective_option_count", "utility_range")


def identity(value):
    if not isinstance(value, str) or not value or value.strip() != value:
        raise ValueError("nonempty unpadded identity required")
    return value


def point(value):
    if len(value) != 2 or any(isinstance(x, (bool, str)) for x in value):
        raise ValueError("two finite numeric coordinates required")
    result = tuple(float(x) for x in value)
    if not all(math.isfinite(x) for x in result):
        raise ValueError("nonfinite coordinate")
    return result


@dataclass(frozen=True)
class OptionState:
    """A selected metric state: x towards attack, native physical y retained."""
    carrier_xy: tuple
    candidate_ids: tuple
    candidate_xy: tuple
    defender_xy: tuple
    carrier_id: str | None = None
    coordinate_convention: str = "metric_attack_x_native_y"

    def __post_init__(self):
        if self.coordinate_convention != "metric_attack_x_native_y":
            raise ValueError("unsupported coordinate convention")
        ids = tuple(identity(x) for x in self.candidate_ids)
        if not ids or len(ids) != len(set(ids)):
            raise ValueError("nonempty unique candidates required")
        if self.carrier_id is not None:
            identity(self.carrier_id)
            if self.carrier_id in ids:
                raise ValueError("carrier cannot be candidate")
        object.__setattr__(self, "candidate_ids", ids)
        for name in ("candidate_xy", "defender_xy"):
            object.__setattr__(self, name, tuple(point(x) for x in getattr(self, name)))
        object.__setattr__(self, "carrier_xy", point(self.carrier_xy))
        if len(ids) != len(self.candidate_xy) or not self.defender_xy:
            raise ValueError("aligned candidates and nonempty defenders required")


@dataclass(frozen=True)
class FrozenOptionModel:
    name: str
    feature_names: tuple
    mean: tuple
    scale: tuple
    coefficients: tuple

    def __post_init__(self):
        expected = {"m0": M0_NAMES, "m1": M1_NAMES}.get(self.name)
        if expected is None or tuple(self.feature_names) != expected:
            raise ValueError("unsupported model or features")
        object.__setattr__(self, "feature_names", tuple(self.feature_names))
        for name in ("mean", "scale", "coefficients"):
            values = tuple(float(v) for v in getattr(self, name))
            if len(values) != len(expected) or not all(math.isfinite(v) for v in values):
                raise ValueError("invalid frozen model")
            object.__setattr__(self, name, values)
        if min(self.scale) <= 0:
            raise ValueError("positive scales required")

    @classmethod
    def from_mapping(cls, name, model):
        return cls(name, tuple(model["feature_names"]), tuple(model["mean"]),
                   tuple(model["scale"]), tuple(model["coefficients"]))


@dataclass(frozen=True)
class OptionEdge:
    receiver_id: str
    utility: float
    option_share: float
    tie_block: int
    expected_rank: float


@dataclass(frozen=True)
class OptionNetwork:
    """An immutable local directed star, with an optionally anonymous root."""
    carrier_id: str | None
    model_name: str
    edges: tuple[OptionEdge, ...]
    top_options: tuple[str, ...]
    summary: object

    @property
    def option_weights(self):
        """Immutable receiver-to-share view."""
        return MappingProxyType({edge.receiver_id: edge.option_share for edge in self.edges})

    @property
    def top_option(self):
        """The unique top receiver, or ``None`` when the top utility is tied."""
        return self.top_options[0] if len(self.top_options) == 1 else None

    @property
    def top_one_share(self):
        return self.summary["top_one_share"]

    @property
    def top_two_share(self):
        return self.summary["top_two_share"]

    @property
    def entropy(self):
        return self.summary["entropy"]

    @property
    def normalized_entropy(self):
        return self.summary["normalized_entropy"]

    @property
    def effective_option_count(self):
        return self.summary["effective_option_count"]

    @property
    def utility_range(self):
        return self.summary["utility_range"]

    def to_records(self):
        """Return fresh records; callers control any subsequent publication."""
        return [dict(receiver_id=e.receiver_id, utility=e.utility,
                     option_share=e.option_share, expected_rank=e.expected_rank,
                     tie_block=e.tie_block, is_top_option=e.receiver_id in self.top_options)
                for e in self.edges]

    def to_pandas(self):
        """Return detached edge rows as a pandas DataFrame.

        Install ``defensive-network-disruption[dataframe]`` when pandas is not
        otherwise available.
        """
        try:
            import pandas as pd
        except ImportError as error:
            raise ImportError(
                "to_pandas() requires the 'dataframe' extra: "
                "pip install 'defensive-network-disruption[dataframe]'"
            ) from error
        rows = []
        for record in self.to_records():
            rows.append({"carrier_id": self.carrier_id, **record})
        return pd.DataFrame(rows, columns=(
            "carrier_id", "receiver_id", "utility", "option_share",
            "expected_rank", "tie_block", "is_top_option"))


def option_distribution(utilities):
    """Stable temperature-one shares and summaries; ties stay utility-based."""
    u = np.asarray(utilities, dtype=np.float64)
    if u.ndim != 1 or not len(u) or not np.isfinite(u).all():
        raise ValueError("finite nonempty one-dimensional utilities required")
    with np.errstate(over="ignore", under="ignore"):
        exp = np.exp(u - np.max(u))
    p = exp / math.fsum(sorted(float(x) for x in exp))
    ordered = sorted((float(x) for x in p), reverse=True)
    entropy = math.fsum(sorted(-float(x) * math.log(float(x)) for x in p if x > 0))
    with np.errstate(over="ignore"):
        spread = float(np.max(u) - np.min(u))
    if not math.isfinite(spread):
        raise ValueError("utility range exceeds float64")
    summary = dict(zip(SUMMARY_KEYS, (
        ordered[0], math.fsum(ordered[:2]), entropy,
        entropy / math.log(len(p)) if len(p) > 1 else 0.0,
        math.exp(entropy), spread)))
    return p, rank_blocks(u), summary


def evaluate_options(state: OptionState, *, model: FrozenOptionModel) -> OptionNetwork:
    matrix, _ = choice_features(state, model.name)
    u = ((matrix - np.asarray(model.mean)) / np.asarray(model.scale)) @ np.asarray(model.coefficients)
    p, ranks, summary = option_distribution(u)
    edges = tuple(OptionEdge(k, float(v), float(s), int(b), float(r)) for k, v, s, b, r in
                  zip(state.candidate_ids, u, p, ranks["blocks"], ranks["ranks"]))
    return OptionNetwork(state.carrier_id, model.name, edges,
                         tuple(sorted(state.candidate_ids[i] for i in ranks["top"])),
                         MappingProxyType(summary))


def compare_options(left: OptionNetwork, right: OptionNetwork):
    """Compare identical candidate populations without label or outcome access."""
    if tuple(e.receiver_id for e in left.edges) != tuple(e.receiver_id for e in right.edges):
        raise ValueError("candidate ordering mismatch")
    pair = pair_comparison([e.tie_block for e in left.edges],
                           [e.tie_block for e in right.edges])
    return {**{k: right.summary[k] - left.summary[k] for k in SUMMARY_KEYS},
            "top_set_changed": float(left.top_options != right.top_options),
            **{k: pair[k] / pair["pairs"] if pair["pairs"] else None
               for k in ("strict_reversal", "tie_created", "tie_removed")},
            "ordering_changed": pair["changed_fraction"]}
