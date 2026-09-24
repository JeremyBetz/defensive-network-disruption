"""Prospective pair equality / global maximality separation.

No I/O, identifiers, integrations or tolerance overrides. A certified dominance
boundary is never passed off as a historical pair-equality boundary.
"""
from dataclasses import dataclass
from fractions import Fraction as F
import time

from .r9r_localization import FieldAuthority, Bounds, VerificationError


@dataclass(frozen=True)
class Proposal:
    left: F
    right: F
    pair: tuple[int, int]
    competitors: tuple[int, ...]
    identities: tuple[tuple, ...]
    owner_tolerance: float = 1e-12

    def validate(self, fields):
        n = len(fields)
        if (type(self.left) is not F or type(self.right) is not F
                or not 0 <= self.left < self.right <= 1
                or type(self.pair) is not tuple or len(self.pair) != 2
                or any(type(i) is not int or not 0 <= i < n for i in self.pair)
                or self.pair[0] == self.pair[1]):
            raise VerificationError('tie_proposal_schema')
        if self.competitors != tuple(i for i in range(n) if i not in self.pair):
            raise VerificationError('tie_competitor_coverage')
        if self.identities != tuple(f.identity for f in fields):
            raise VerificationError('tie_lineage')
        if type(self.owner_tolerance) is not float or self.owner_tolerance.hex() != (1e-12).hex():
            raise VerificationError('tie_owner_tolerance')


@dataclass(frozen=True)
class Cell:
    left: F
    right: F
    depth: int
    relation: str
    maximality: str
    positive: bool
    values: tuple[Bounds, ...]
    differences: tuple[Bounds, ...]


@dataclass(frozen=True)
class Coverage:
    proposal: Proposal
    cells: tuple[Cell, ...]
    subdivisions: int
    bound_calls: int
    exhausted: bool
    positive_witness: tuple[Bounds, Bounds]


def proposal(fields, pair, left, right):
    result = Proposal(F(left), F(right), tuple(pair),
                      tuple(i for i in range(len(fields)) if i not in pair),
                      tuple(f.identity for f in fields))
    result.validate(fields)
    return result


def inactive(field, a, b):
    # Exact branch proof, separate from the production owner rule.
    return (type(field) is FieldAuthority and field.candidate != 'isotropic'
            and max(field.dot*a, field.dot*b) <= field.q)


def cell(fields, item, a, b, depth):
    values = tuple(Bounds.point(0) if inactive(f, a, b) else f.bounds(a, b)[0]
                   for f in fields)
    x, y = item.pair
    identity = fields[x].identity == fields[y].identity
    zero = values[x] == values[y] == Bounds.point(0)
    relation = 'identity' if identity else 'inactive' if zero else 'unresolved'
    pair_lo = max(values[x].lo, values[y].lo)
    pair_hi = max(values[x].hi, values[y].hi)
    differences = tuple(Bounds(pair_lo-values[k].hi, pair_hi-values[k].lo)
                        for k in item.competitors)
    maximal = all(fields[k].identity in (fields[x].identity, fields[y].identity)
                  or d.lo >= 0 for k, d in zip(item.competitors, differences))
    dominated = any(d.hi < 0 for d in differences)
    state = 'maximal' if maximal else 'dominated' if dominated else 'unresolved'
    return Cell(a, b, depth, relation, state, pair_lo > 0, values, differences)


def review(fields, item, *, deadline, max_depth=80, max_leaves=65536,
           sink=lambda value: None):
    """Complete deterministic coverage. Limits preserve unresolved regions."""
    fields = tuple(fields); item.validate(fields)
    if (type(max_depth) is not int or not 0 <= max_depth <= 80
            or type(max_leaves) is not int or not 1 <= max_leaves <= 65536):
        raise VerificationError('tie_limits')
    if time.monotonic() >= deadline:raise TimeoutError('tie_maximality_deadline')
    midpoint=(item.left+item.right)/2
    witness=tuple(Bounds.point(0) if inactive(fields[k],midpoint,midpoint)
                  else fields[k].bounds(midpoint,midpoint)[0] for k in item.pair)
    pending = [(item.left, item.right, 0)]; leaves = []; splits = 0; calls = 2
    exhausted = False
    while pending:
        if time.monotonic() >= deadline:
            raise TimeoutError('tie_maximality_deadline')
        a, b, depth = pending.pop()
        proof = cell(fields, item, a, b, depth); calls += len(fields)
        unresolved = proof.relation == 'unresolved' or proof.maximality == 'unresolved'
        if unresolved and depth < max_depth and len(leaves)+len(pending)+2 <= max_leaves:
            mid = (a+b)/2; splits += 1
            pending.extend(((mid, b, depth+1), (a, mid, depth+1)))
        else:
            exhausted |= unresolved
            leaves.append(proof); sink(proof)
    result = Coverage(item, tuple(leaves), splits, calls, exhausted, witness)
    validate_coverage(result)
    return result


def validate_coverage(result):
    """Structural persisted-proof validation; never reevaluates fields."""
    p = result.proposal; cells = result.cells
    if (len(p.pair) != 2 or len(set(p.pair)) != 2
            or any(type(i) is not int or not 0 <= i < len(p.identities) for i in p.pair)
            or p.competitors != tuple(i for i in range(len(p.identities)) if i not in p.pair)
            or type(p.owner_tolerance) is not float or p.owner_tolerance.hex() != (1e-12).hex()):
        raise VerificationError('tie_proof_authority')
    if (not cells or cells[0].left != p.left or cells[-1].right != p.right
            or any(a.right != b.left for a, b in zip(cells, cells[1:]))):
        raise VerificationError('tie_coverage')
    if (result.subdivisions!=len(cells)-1
            or result.bound_calls!=(2*result.subdivisions+1)*len(p.identities)+2):
        raise VerificationError('tie_work_counts')
    if type(result.positive_witness) is not tuple or len(result.positive_witness)!=2:
        raise VerificationError('tie_positive_witness')
    midpoint=(p.left+p.right)/2
    covering=[c for c in cells if c.left<=midpoint<=c.right]
    for k,w in zip(p.pair,result.positive_witness):
        if type(w) is not Bounds or not w.lo<=w.hi or any(
                w.hi<c.values[k].lo or w.lo>c.values[k].hi for c in covering):
            raise VerificationError('tie_positive_witness')
    for c in cells:
        if (type(c.left) is not F or type(c.right) is not F
                or type(c.depth) is not int or not c.left < c.right or not 0 <= c.depth <= 80
                or c.right-c.left!=(p.right-p.left)/2**c.depth
                or len(c.values) != len(p.identities)
                or len(c.differences) != len(p.competitors)
                or c.relation not in ('identity', 'inactive', 'unresolved')
                or c.maximality not in ('maximal', 'dominated', 'unresolved')):
            raise VerificationError('tie_cell_schema')
        x, y = p.pair
        low, high = max(c.values[x].lo, c.values[y].lo), max(c.values[x].hi, c.values[y].hi)
        expected = tuple(Bounds(low-c.values[k].hi, high-c.values[k].lo) for k in p.competitors)
        identity = p.identities[x] == p.identities[y]
        relation = 'identity' if identity else 'inactive' if c.values[x] == c.values[y] == Bounds.point(0) else 'unresolved'
        maximal = all(p.identities[k] in (p.identities[x], p.identities[y]) or d.lo >= 0
                      for k, d in zip(p.competitors, expected))
        state = 'maximal' if maximal else 'dominated' if any(d.hi < 0 for d in expected) else 'unresolved'
        if c.differences != expected or c.relation != relation or c.maximality != state or c.positive != (low > 0):
            raise VerificationError('tie_forged_proof')
    exhausted=any(c.relation=='unresolved' or c.maximality=='unresolved' for c in cells)
    if result.exhausted!=exhausted:raise VerificationError('tie_limit_claim')
    return result


def disposition(result):
    """Only full-region retention/exclusion is representable without new types.

    Mixed coverage must not fabricate historical equality-boundary metadata.
    A future clipping interface needs separate prospective authority.
    """
    validate_coverage(result)
    if result.exhausted or any(c.relation == 'unresolved' or c.maximality == 'unresolved'
                               for c in result.cells):
        raise VerificationError('tie_maximality_unresolved')
    if all(c.maximality == 'dominated' for c in result.cells):
        return 'exclude'
    # Common inactive portions are not positive owner witnesses. A retained
    # domain-spanning tie must also have positive evidence, and still passes
    # the unchanged historical boundary/owner checks in the caller.
    if all(c.maximality == 'maximal' for c in result.cells) and (
            any(c.positive for c in result.cells) or max(w.lo for w in result.positive_witness)>0):
        return 'retain'
    if all(all(v == Bounds.point(0) for v in c.values) for c in result.cells):
        return 'exclude_inactive'
    raise VerificationError('tie_clipping_unrepresentable')
