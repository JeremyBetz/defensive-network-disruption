"""Canonical geometry-only projection; skipped labels are never decoded."""
from .boundary_review import View, identifier, finite_point
from ..geometry.occlusion_fields import validate_geometry

# Existing development membership, reproduced from the closed Session 13 authority.
DEVELOPMENT = ('1886347','1899585','1925299','1996435','2006229','2011166','2013725','2015213','2017461')
ALIASES = tuple(f'development_{i:02d}' for i in range(1,10))
COUNTS = (885,801,952,877,861,629,764,734,724)
CANONICAL_KEYS = {'match_id','event_id','carrier_xy','candidate_ids','candidate_xy','defender_xy','target_index','target_outside'}


def project_line(text):
    view = View(text); fields = view.fields()
    if set(fields) != CANONICAL_KEYS:
        raise ValueError('canonical_schema')
    match = identifier(view.get(fields, 'match_id'))
    if match not in DEVELOPMENT:
        raise PermissionError('development_only')
    event = identifier(view.get(fields, 'event_id'))
    ids = tuple(identifier(x) for x in view.get(fields, 'candidate_ids'))
    carrier = finite_point(view.get(fields, 'carrier_xy'))
    receivers = tuple(finite_point(x) for x in view.get(fields, 'candidate_xy'))
    defenders = tuple(finite_point(x) for x in view.get(fields, 'defender_xy'))
    if not ids or len(ids) != len(receivers) or len(set(ids)) != len(ids):
        raise ValueError('candidate_identity')
    validate_geometry(carrier, defenders)
    alias = ALIASES[DEVELOPMENT.index(match)]
    return (alias, event), dict(alias=alias, carrier=carrier, receivers=receivers, defenders=defenders)
