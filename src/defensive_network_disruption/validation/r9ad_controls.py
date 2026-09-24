"""Provider-free independently bounded R9AD fixtures, frozen before access."""
from dataclasses import replace
from fractions import Fraction as F
import time

from ..geometry import r9ad_tie_regions as r
from .r9t_acceptance import primitive, fixture
from ..geometry.r9t_transition import canonicalize
from .r9j_evidence import digest


class Polynomial:
    """Exact rational engineering function; independent Horner bounds."""
    def __init__(self, *coefficients):
        self.coefficients = tuple(F(x) for x in coefficients)
        self.identity = ('engineering_polynomial', *self.coefficients)

    def bounds(self, a, b):
        t = r.Bounds(F(a), F(b)); result = r.Bounds.point(0)
        for coefficient in reversed(self.coefficients):
            result = result*t + coefficient
        return result, None


class Ambiguous:
    identity = ('engineering_unresolved',)
    def bounds(self, a, b):
        return r.Bounds(F(0), F(2)), None


NAMES = ('maximal', 'dominated', 'maximal_left', 'maximal_right',
         'equality_to_dominance', 'three_way', 'tolerance_only', 'point_only',
         'tiny_dominance', 'unresolved', 'onset_adjacent', 'switch_adjacent',
         'oscillatory', 'duplicate_dominated')
EXPECTED = ('retain', 'exclude', 'blocked', 'blocked', 'blocked', 'retain',
            'blocked', 'blocked', 'blocked', 'blocked', 'blocked', 'blocked',
            '6', 'exclude')
NEGATIVES = ('incomplete_competitors', 'missing_proof', 'malformed_partition',
             'overlapping_regions', 'uncovered_domain', 'invalid_witness',
             'unresolved_region', 'wrong_lineage', 'owner_tolerance', 'fabricated_boundary')


def fields_for(name):
    pair = (Polynomial(1), Polynomial(1)); competitor = Polynomial(F(1, 2))
    if name in ('dominated',): competitor = Polynomial(2)
    if name in ('maximal_left', 'onset_adjacent', 'switch_adjacent'): competitor = Polynomial(F(1,2),1)
    if name == 'maximal_right': competitor = Polynomial(F(3,2),-1)
    if name == 'equality_to_dominance': competitor = Polynomial(1,1)
    if name == 'three_way': competitor = Polynomial(1)
    if name == 'tolerance_only': pair = (Polynomial(1), Polynomial(1+F(1,10**13)))
    if name == 'point_only': pair = (Polynomial(1), Polynomial(F(5,4),-1,1))
    if name == 'tiny_dominance': competitor = Polynomial(F(3,4)+F(1,2**100),1,-1)
    if name == 'unresolved': competitor = Ambiguous()
    if name == 'duplicate_dominated':
        pair = tuple(r.FieldAuthority.from_geometry('constant_width',(0.,0.),(20.,0.),d)
                     for d in ((5.,1.),(5.,-1.)))
        competitor = Polynomial(2)
    return (*pair, competitor)


def controls(sink=lambda label,value: digest(value)):
    rows = []
    for name, expected in zip(NAMES, EXPECTED):
        detail = {'fixture': name, 'expected': expected}
        try:
            if name == 'oscillatory':
                result = canonicalize(*fixture('NNPPZNPPP'))
                detail['proof'] = primitive(result); observed = str(result.canonical_index)
            else:
                fields = fields_for(name); item = r.proposal(fields,(0,1),F(0),F(1))
                result = r.review(fields,item,deadline=time.monotonic()+10,max_depth=8,max_leaves=512)
                detail['proof'] = primitive(result)
                observed = r.disposition(result)
        except r.VerificationError as error:
            observed = 'blocked'; detail['reason'] = str(error)
        detail['observed'] = observed
        rows.append(dict(fixture=name,expected=expected,observed=observed,
                         passed=observed==expected,evidence_sha256=sink('topology_'+name,detail)))
    return rows


def negatives(sink=lambda label,value: digest(value)):
    fields = fields_for('maximal'); item = r.proposal(fields,(0,1),F(0),F(1))
    proof = r.review(fields,item,deadline=time.monotonic()+10)
    c = proof.cells[0]
    actions = (
        lambda: replace(item,competitors=()).validate(fields),
        lambda: r.validate_coverage(replace(proof,cells=(replace(c,differences=()),))),
        lambda: r.validate_coverage(replace(proof,cells=(replace(c,left=F(1),right=F(0)),))),
        lambda: r.validate_coverage(replace(proof,cells=(c,c))),
        lambda: r.validate_coverage(replace(proof,cells=(replace(c,left=F(1,2)),))),
        lambda: r.validate_coverage(replace(proof,cells=(replace(c,maximality='dominated'),))),
        lambda: r.disposition(r.review(fields_for('unresolved'),r.proposal(fields_for('unresolved'),(0,1),F(0),F(1)),deadline=time.monotonic()+10,max_depth=0)),
        lambda: replace(item,identities=tuple(reversed(item.identities))).validate(fields),
        lambda: replace(item,owner_tolerance=1e-11).validate(fields),
        lambda: r.validate_coverage(replace(proof,cells=(replace(c,right=F(1,2)),))),
    )
    rows = []
    for name, action in zip(NEGATIVES, actions):
        try: action()
        except (ValueError, TypeError) as error: blocked=True; reason=type(error).__name__
        else: blocked=False; reason='unexpected_acceptance'
        detail=dict(blocked=blocked,reason=reason)
        rows.append(dict(fixture=name,**detail,evidence_sha256=sink('negative_'+name,detail)))
    return rows
