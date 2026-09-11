from __future__ import annotations

from dataclasses import FrozenInstanceError
import itertools
import math

import numpy as np
import pytest
from unittest.mock import patch

from defensive_network_disruption.geometry.verification_repair import (
    VerificationError,
    VerificationReadiness,
    find_verified_envelope,
    independent_continuity,
    mapped_signature,
    opposite_nonzero_signs,
)
import defensive_network_disruption.geometry.verification_repair as repair


def test_raw_sign_predicate_preserves_tiny_signs_and_zeros():
    for magnitude in (1e-8, 1e-12, 1e-15, 1e-200):
        assert opposite_nonzero_signs(-magnitude, magnitude)
        assert not opposite_nonzero_signs(magnitude, magnitude)
    assert not opposite_nonzero_signs(0.0, 1.0)
    assert not opposite_nonzero_signs(0.0, 0.0)
    with pytest.raises(VerificationError):
        opposite_nonzero_signs(math.nan, 1.0)


def test_tiny_crossing_is_detected_without_product_underflow():
    def values(t):
        return np.column_stack((np.full_like(t, 5e-200) + 1e-200*(t-.500001),
                                np.full_like(t, 5e-200)))
    result = find_verified_envelope(values)
    # The raw root is retained as a partition.  The pre-existing 1e-12 owner
    # block deliberately prevents these 1e-200 differences from becoming an
    # envelope-owner switch.
    assert any(point == pytest.approx(.500001, abs=1e-12) for point in result.partitions)
    assert result.switches == ()


def test_exact_node_root_and_structural_zero_are_distinct():
    crossing = find_verified_envelope(lambda t: np.column_stack((t, 1-t)))
    assert len(crossing.switches) == 1
    zero = find_verified_envelope(lambda t: np.column_stack((np.zeros_like(t), np.zeros_like(t))))
    assert zero.switches == ()
    assert zero.maximizing_defenders == ()


@pytest.mark.parametrize("lower,upper", [(.25,.75), (.251,.749)])
def test_certified_tie_plateau_encloses_exact_boundaries(lower, upper):
    def plateau(t):
        base = np.full_like(t, .6)
        other = np.where((t >= lower) & (t <= upper), .6, np.nextafter(.6, 0.0))
        return np.column_stack((base, other))
    result = find_verified_envelope(plateau)
    assert len(result.tie_intervals) == 1
    tie = result.tie_intervals[0]
    assert tie.start.outside < lower <= tie.start.inside
    assert tie.end.inside <= upper < tie.end.outside
    assert np.nextafter(tie.start.outside, tie.start.inside) == tie.start.inside
    assert np.nextafter(tie.end.outside, tie.end.inside) == tie.end.inside
    assert {tie.start.outside,tie.start.inside,tie.end.outside,tie.end.inside}.issubset(result.partitions)


def test_endpoint_and_three_way_plateaus_preserve_owner_sets():
    endpoint = find_verified_envelope(lambda t: np.column_stack((np.full_like(t,.6), .6-.1*np.maximum(t-.75,0))))
    assert endpoint.tie_intervals[0].start is None
    three = find_verified_envelope(lambda t: np.column_stack((np.full_like(t,.6),np.full_like(t,.6),np.full_like(t,.6))))
    assert three.tie_intervals[0].owners == (0,1,2)


def test_non_envelope_equality_does_not_create_plateau():
    result = find_verified_envelope(lambda t: np.column_stack((np.full_like(t,.2),np.full_like(t,.2),np.full_like(t,.8))))
    assert result.tie_intervals == ()


def test_permutation_maps_complete_records():
    function = lambda t: np.column_stack((t,1-t,np.full_like(t,.5)))
    baseline = find_verified_envelope(function)
    identity = (0,1,2)
    expected = mapped_signature(baseline, identity)
    for permutation in itertools.permutations(identity):
        result = find_verified_envelope(lambda t,p=permutation: function(t)[:,p])
        assert mapped_signature(result, permutation) == expected


def test_independent_continuity_rejects_step():
    assert independent_continuity(.2,.2)
    assert not independent_continuity(.2,.8)


def test_readiness_is_immutable_derived_and_fail_closed():
    names = tuple(VerificationReadiness.__dataclass_fields__)
    control = VerificationReadiness(**{name:True for name in names})
    assert control.ready
    with pytest.raises(FrozenInstanceError):
        control.integrity_verified = False
    with pytest.raises(TypeError):
        VerificationReadiness(**{name:(1 if name=='integrity_verified' else True) for name in names})
    for failed in names:
        values = {name:True for name in names}; values[failed] = False
        assert not VerificationReadiness(**values).ready


def test_ready_cannot_be_supplied():
    values = {name:True for name in VerificationReadiness.__dataclass_fields__}
    with pytest.raises(TypeError):
        VerificationReadiness(**values, ready=True)


def test_bracketed_root_failure_fails_closed():
    with patch.object(repair, "brentq", side_effect=RuntimeError("injected")):
        with pytest.raises(VerificationError, match="bracketed_root_failed"):
            find_verified_envelope(lambda t: np.column_stack((.400001+.2*t, .6-.2*t)))


def test_hidden_within_cell_crossings_remain_explicit_fixture_limitation():
    center = 32768.5/65536
    values = lambda t: np.column_stack((np.full_like(t,.4),
        .3+.2*np.maximum(0,1-np.abs(t-center)/(.4/65536))))
    assert find_verified_envelope(values).switches == ()
