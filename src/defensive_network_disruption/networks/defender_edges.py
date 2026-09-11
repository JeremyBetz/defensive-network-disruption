"""Neutral, state-local defender-to-option-edge geometry.

The types in this module are internal research primitives.  They describe
distance relationships and do not measure suppression, causality, or value.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from collections.abc import Mapping
import math

import numpy as np

from defensive_network_disruption.geometry.segment import point_to_segment_distance
from defensive_network_disruption.networks.options import OptionNetwork, OptionState
from defensive_network_disruption.validation.ranking_features import choice_features

DISTANCE_TIE_TOLERANCE = 1e-12


@dataclass(frozen=True)
class DefenderEdgeRelation:
    """One anonymous state-local defender's geometry relative to one edge."""

    receiver_id: str
    receiver_index: int
    defender_index: int
    receiver_distance: float
    segment_distance: float
    receiver_rank: float
    segment_rank: float
    receiver_block: int
    segment_block: int
    receiver_block_start: int
    receiver_block_end: int
    segment_block_start: int
    segment_block_end: int

    def membership(self, kind: str, k: int) -> float:
        """Fractional top-k membership when a tie block crosses k."""
        if kind not in {"receiver", "segment"}:
            raise ValueError("kind must be 'receiver' or 'segment'")
        if not isinstance(k, int) or isinstance(k, bool) or k < 1:
            raise ValueError("k must be a positive integer")
        start = getattr(self, f"{kind}_block_start")
        end = getattr(self, f"{kind}_block_end")
        return max(0, min(end, k) - start + 1) / (end - start + 1)


@dataclass(frozen=True)
class DefenderEdgeMap:
    """All defender-edge relations for one carrier-centred option state."""

    carrier_id: str | None
    candidate_ids: tuple[str, ...]
    defender_count: int
    relations: tuple[DefenderEdgeRelation, ...]
    coordinate_convention: str

    def for_receiver(self, receiver_index: int) -> tuple[DefenderEdgeRelation, ...]:
        return tuple(r for r in self.relations if r.receiver_index == receiver_index)


def _rank_blocks(values: list[float]) -> dict[int, tuple[float, int, int, int]]:
    """Return index -> expected rank, block, start, end using block-anchor ties."""
    order = sorted(range(len(values)), key=lambda i: (values[i], i))
    out: dict[int, tuple[float, int, int, int]] = {}
    pos = 0
    block = 0
    while pos < len(order):
        anchor = values[order[pos]]
        end = pos
        while end + 1 < len(order) and abs(values[order[end + 1]] - anchor) <= DISTANCE_TIE_TOLERANCE:
            end += 1
        start_rank, end_rank = pos + 1, end + 1
        expected = (start_rank + end_rank) / 2.0
        for item in order[pos:end + 1]:
            out[item] = (expected, block, start_rank, end_rank)
        pos = end + 1
        block += 1
    return out


def map_defender_edges(state: OptionState) -> DefenderEdgeMap:
    """Construct the complete direct-distance relation map for ``state``."""
    if not isinstance(state, OptionState):
        raise TypeError("state must be an OptionState")
    if not state.defender_xy:
        raise ValueError("state must contain at least one defender")
    relations = []
    for receiver_index, (receiver_id, receiver) in enumerate(zip(state.candidate_ids, state.candidate_xy)):
        receiver_distances = [math.dist(defender, receiver) for defender in state.defender_xy]
        segment_distances = [point_to_segment_distance(defender, state.carrier_xy, receiver)[0]
                             for defender in state.defender_xy]
        rranks = _rank_blocks(receiver_distances)
        sranks = _rank_blocks(segment_distances)
        for defender_index in range(len(state.defender_xy)):
            rr, rb, rs, re = rranks[defender_index]
            sr, sb, ss, se = sranks[defender_index]
            relations.append(DefenderEdgeRelation(
                receiver_id, receiver_index, defender_index,
                receiver_distances[defender_index], segment_distances[defender_index],
                rr, sr, rb, sb, rs, re, ss, se))
    result = DefenderEdgeMap(state.carrier_id, state.candidate_ids, len(state.defender_xy),
                             tuple(relations), state.coordinate_convention)
    features, _ = choice_features(state, "m1")
    for receiver_index in range(len(state.candidate_ids)):
        rows = result.for_receiver(receiver_index)
        if min(r.receiver_distance for r in rows) != float(features[receiver_index, 3]):
            raise RuntimeError("receiver-distance minimum does not reproduce M1")
        if min(r.segment_distance for r in rows) != float(features[receiver_index, 4]):
            raise RuntimeError("segment-distance minimum does not reproduce M1")
    return result


def _nearest_set(rows: tuple[DefenderEdgeRelation, ...], kind: str) -> frozenset[int]:
    return frozenset(r.defender_index for r in rows if getattr(r, f"{kind}_block") == 0)


def summarize_edge_involvement(
    mapping: DefenderEdgeMap, *, network: OptionNetwork | None = None,
) -> Mapping[str, object]:
    """Summarize one relation map; optional weighting requires aligned M1 shares."""
    if not isinstance(mapping, DefenderEdgeMap):
        raise TypeError("mapping must be a DefenderEdgeMap")
    shares = None
    if network is not None:
        if not isinstance(network, OptionNetwork) or network.model_name != "m1":
            raise ValueError("network must be an M1 OptionNetwork")
        if network.carrier_id != mapping.carrier_id or tuple(e.receiver_id for e in network.edges) != mapping.candidate_ids:
            raise ValueError("network candidates and carrier must align with mapping")
        shares = tuple(e.option_share for e in network.edges)
    defenders: dict[int, dict[str, object]] = {}
    for defender in range(mapping.defender_count):
        item: dict[str, object] = {}
        for kind in ("receiver", "segment"):
            selected = [r for r in mapping.relations if r.defender_index == defender]
            distances = [getattr(r, f"{kind}_distance") for r in selected]
            ranks = [getattr(r, f"{kind}_rank") for r in selected]
            item[f"{kind}_nearest_edges"] = sum(getattr(r, f"{kind}_block") == 0 for r in selected)
            item[f"{kind}_mean_rank"] = math.fsum(ranks) / len(ranks)
            item[f"{kind}_median_rank"] = float(np.median(ranks))
            item[f"{kind}_distance_min"] = min(distances)
            item[f"{kind}_distance_median"] = float(np.median(distances))
            item[f"{kind}_distance_max"] = max(distances)
            for k in (1, 2, 3):
                ke = min(k, mapping.defender_count)
                involvement = math.fsum(r.membership(kind, ke) for r in selected)
                item[f"{kind}_top{k}_involvement"] = involvement
                item[f"{kind}_top{k}_edge_share"] = involvement / len(mapping.candidate_ids)
                if kind == "segment" and shares is not None:
                    item[f"segment_top{k}_m1_weighted"] = math.fsum(
                        shares[r.receiver_index] * r.membership("segment", ke) for r in selected)
        defenders[defender] = item
    edge_rows = []
    for receiver_index in range(len(mapping.candidate_ids)):
        rows = mapping.for_receiver(receiver_index)
        rn, sn = _nearest_set(rows, "receiver"), _nearest_set(rows, "segment")
        ordered = sorted(r.segment_distance for r in rows)
        edge_rows.append({
            "receiver_nearest_count": len(rn), "segment_nearest_count": len(sn),
            "nearest_intersects": bool(rn & sn), "nearest_equal": rn == sn,
            "nearest_jaccard": len(rn & sn) / len(rn | sn),
            "same_unique_nearest": len(rn) == len(sn) == 1 and rn == sn,
            "segment_d2_d1": ordered[1] - ordered[0] if len(ordered) >= 2 else None,
            "segment_d3_d1": ordered[2] - ordered[0] if len(ordered) >= 3 else None,
        })
    pair_jaccard: dict[str, list[float]] = {f"top{k}": [] for k in (1, 2, 3)}
    for left in range(len(mapping.candidate_ids)):
        for right in range(left + 1, len(mapping.candidate_ids)):
            for k in (1, 2, 3):
                ke = min(k, mapping.defender_count)
                a = {r.defender_index for r in mapping.for_receiver(left) if r.membership("segment", ke) > 0}
                b = {r.defender_index for r in mapping.for_receiver(right) if r.membership("segment", ke) > 0}
                pair_jaccard[f"top{k}"].append(len(a & b) / len(a | b))
    return MappingProxyType({
        "edges": len(mapping.candidate_ids), "defenders": mapping.defender_count,
        "defender_summaries": MappingProxyType({k: MappingProxyType(v) for k, v in defenders.items()}),
        "edge_summaries": tuple(MappingProxyType(x) for x in edge_rows),
        "segment_pair_jaccard": MappingProxyType({k: tuple(v) for k, v in pair_jaccard.items()}),
        "receiver_unique_nearest_defenders": len(set().union(*(_nearest_set(mapping.for_receiver(i), "receiver") for i in range(len(mapping.candidate_ids))))),
        "segment_unique_nearest_defenders": len(set().union(*(_nearest_set(mapping.for_receiver(i), "segment") for i in range(len(mapping.candidate_ids))))),
    })
