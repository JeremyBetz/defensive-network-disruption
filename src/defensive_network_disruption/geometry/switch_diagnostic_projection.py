"""Deterministic JSON-safe projection of immutable verified switches."""
from __future__ import annotations

from .verification_repair import VerifiedSwitch


def project_verified_switch(switch: VerifiedSwitch, permutation: tuple[int, ...] | None = None) -> dict:
    """Project every real owner-state field without changing production semantics."""
    if not isinstance(switch, VerifiedSwitch):
        raise TypeError("switch_must_be_VerifiedSwitch")
    if permutation is None:
        pair_owners = tuple(index for pair in switch.crossing_pairs for index in pair)
        permutation = tuple(range(max((*switch.owners_before, *switch.owners_at,
                                       *switch.owners_after, *pair_owners), default=-1) + 1))
    def owners(values):
        return sorted(permutation[index] for index in values)
    pairs = sorted(sorted((permutation[left], permutation[right]))
                   for left, right in switch.crossing_pairs)
    return {
        "location": switch.location,
        "owners_before": owners(switch.owners_before),
        "owners_at": owners(switch.owners_at),
        "owners_after": owners(switch.owners_after),
        "crossing_pairs": pairs,
        "endpoint": switch.endpoint,
        "multiway": switch.multiway,
        "envelope_value": switch.envelope_value,
    }
