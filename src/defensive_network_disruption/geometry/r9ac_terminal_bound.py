"""R9AC coefficient-only independent bound; no geometry or production route."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F
import heapq
import math
import time

from .r9aa_terminal_authority import load_authority
from .r9x_terminal_authority import canonical, digest, fraction_record as fr, parse_fraction as pf
from .r9j_reference import Bounds


@dataclass(frozen=True)
class Limits:
    depth: int = 80
    leaves: int = 65536
    seconds: float = 900.0

    def __post_init__(self):
        if type(self.depth) is not int or not 0 <= self.depth <= 80:
            raise ValueError('depth_limit')
        if type(self.leaves) is not int or not 1 <= self.leaves <= 65536:
            raise ValueError('leaf_limit')
        if not 0 < self.seconds <= 900:
            raise ValueError('time_limit')


def interval(value):
    return [fr(value.lo), fr(value.hi)]


def read_interval(value):
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError('interval_schema')
    return Bounds(pf(value[0]), pf(value[1]))


def _maximum(values):
    return Bounds(max(x.lo for x in values), max(x.hi for x in values))


def _field(item, a, b):
    # Both pair members are bounded, even when symbolically identical.
    value, derivative = item.bounds(a, b)
    inactive = max(item.dot*a, item.dot*b) <= item.q
    positive = min(item.dot*a, item.dot*b) > item.q
    if inactive:
        value = Bounds.point(0)
        derivative = Bounds.point(0)
    return {'ref': item.authority_sha256, 'range': interval(value),
            'derivative': None if derivative is None else interval(derivative),
            'inactive': inactive, 'positive': positive}


def facts(fields):
    """Derive conclusions from persisted enclosures and explicit exact proofs."""
    pair, competitors = fields[:2], fields[2:]
    if len(pair) != 2 or not competitors:
        raise ValueError('field_inventory')
    p = [read_interval(x['range']) for x in pair]
    c = [read_interval(x['range']) for x in competitors]
    pm, cm = _maximum(p), _maximum(c)
    def ge(member, other, mb, ob):
        return (member['ref'] == other['ref'] or other['inactive'] or mb.lo >= ob.hi)
    maximal = all(any(ge(x, y, xb, yb) for x, xb in zip(pair, p))
                  for y, yb in zip(competitors, c))
    dominated = any(all(yb.lo > xb.hi or (x['inactive'] and y['positive'])
                        for x, xb in zip(pair, p)) for y, yb in zip(competitors, c))
    if maximal and dominated:
        raise ValueError('contradictory_proof')
    strict_pair = all(any(xb.lo > yb.hi or (y['inactive'] and x['positive'])
                          for x, xb in zip(pair, p)) for y, yb in zip(competitors, c))
    pair_equal = pair[0]['ref'] == pair[1]['ref'] or all(x['inactive'] for x in pair)
    equality = any(
        (all(x['inactive'] for x in pair) and y['inactive']) or
        any(x['ref'] == y['ref'] and ge(x, pair[1-i], p[i], p[1-i])
            for i, x in enumerate(pair)) for y in competitors)
    return {'status': 'TA' if maximal else 'TB' if dominated else 'unresolved',
            'strict_pair': strict_pair, 'pair_equal': pair_equal,
            'interior_equality': equality, 'pair_maximum': interval(pm),
            'competitor_maximum': interval(cm), 'difference': interval(pm-cm),
            'comparisons': [[interval(x-y) for y in c] for x in p]}


def cell(loaded, a, b, *, node_id, parent, depth):
    fields = [_field(item, a, b) for item in (*loaded.pair, *loaded.competitors)]
    return {'schema_version': 1, 'id': node_id, 'parent': parent, 'depth': depth,
            'left': fr(a), 'right': fr(b), 'fields': fields, **facts(fields)}


def classification(nodes):
    statuses = [x['status'] for x in nodes]
    if all(x == 'TA' for x in statuses):
        return 'TA'
    if all(x == 'TB' for x in statuses):
        return 'TB'
    if 'TA' in statuses and 'TB' in statuses:
        return 'TC'
    if any(x['interior_equality'] for x in nodes):
        return 'TD'
    return 'TE'


def bound(record, *, limits=Limits(), sink=lambda record: None,
          clock=time.monotonic, session_deadline=None):
    loaded = load_authority(record)
    if loaded.source_version != 2:
        raise ValueError('v2_required')
    start = clock()
    deadline = min(start+limits.seconds, session_deadline or float('inf'))
    left, right = loaded.cell['left'], loaded.cell['right']
    nodes, frontier, queue = [], {}, []
    reason = 'proved'
    def add(a, b, parent, depth):
        if clock() >= deadline:
            raise TimeoutError('refinement_deadline')
        item = cell(loaded, a, b, node_id=len(nodes), parent=parent, depth=depth)
        sink(item)  # Durable record precedes any next computation.
        nodes.append(item); frontier[item['id']] = item
        if item['status'] == 'unresolved':
            heapq.heappush(queue, (a, item['id']))
        return item
    try:
        add(left, right, None, 0)
        while queue:
            if classification(list(frontier.values())) in ('TA', 'TB', 'TC'):
                break
            if clock() >= deadline:
                reason = 'deadline'; break
            _, identifier = heapq.heappop(queue)
            item = frontier[identifier]
            if item['depth'] >= limits.depth:
                reason = 'depth_limit'; continue
            if len(frontier) >= limits.leaves:
                reason = 'leaf_limit'; break
            a, b = pf(item['left']), pf(item['right']); middle = (a+b)/2
            # Parent remains represented until BOTH child records exist.
            first = add(a, middle, identifier, item['depth']+1)
            try:
                second = add(middle, b, identifier, item['depth']+1)
            except TimeoutError:
                frontier.pop(first['id'])
                reason = 'deadline'; break
            frontier.pop(identifier)
    except TimeoutError:
        reason = 'deadline'
    ordered = sorted(frontier.values(), key=lambda item: pf(item['left']))
    result = {'schema_version': 1, 'input_sha256': digest(record),
              'frontier': [x['id'] for x in ordered], 'node_count': len(nodes),
              'classification': classification(ordered) if ordered else 'TE',
              'reason': reason, 'historical_depth': loaded.cell['depth'],
              'limits': {'depth': limits.depth, 'leaves': limits.leaves, 'seconds': limits.seconds},
              'elapsed_seconds': max(0.0, clock()-start)}
    if ordered:
        result['maximum_difference_width'] = fr(max(
            read_interval(x['difference']).hi-read_interval(x['difference']).lo for x in ordered))
    else:
        result['maximum_difference_width'] = None
    validate_result(record, nodes, result)
    return result, nodes


def validate_result(record, nodes, result):
    """No field evaluation: check coverage, stored proof algebra and decisions."""
    loaded = load_authority(record)
    required = {'schema_version','input_sha256','frontier','node_count','classification',
                'reason','historical_depth','limits','elapsed_seconds','maximum_difference_width'}
    if set(result) != required or result['schema_version'] != 1 or result['input_sha256'] != digest(record):
        raise ValueError('result_binding')
    if result['node_count'] != len(nodes) or result['historical_depth'] != loaded.cell['depth']:
        raise ValueError('result_counts')
    limits = Limits(**result['limits'])
    if type(result['elapsed_seconds']) not in (int,float) or not math.isfinite(result['elapsed_seconds']) or result['elapsed_seconds']<0:
        raise ValueError('result_time')
    if result['reason'] not in ('proved','deadline','depth_limit','leaf_limit'):
        raise ValueError('stop_reason')
    expected = [x.authority_sha256 for x in (*loaded.pair,*loaded.competitors)]
    node_keys = {'schema_version','id','parent','depth','left','right','fields',*facts([
        {'ref':'a','range':interval(Bounds.point(0)),'inactive':True,'positive':False},
        {'ref':'a','range':interval(Bounds.point(0)),'inactive':True,'positive':False},
        {'ref':'b','range':interval(Bounds.point(0)),'inactive':True,'positive':False}]).keys()}
    for index, node in enumerate(nodes):
        if set(node) != node_keys or node['schema_version'] != 1 or node['id'] != index:
            raise ValueError('node_schema')
        a,b=pf(node['left']),pf(node['right'])
        if not loaded.cell['left'] <= a < b <= loaded.cell['right']:
            raise ValueError('node_bounds')
        if index == 0:
            if node['parent'] is not None or node['depth'] != 0 or (a,b)!=(loaded.cell['left'],loaded.cell['right']):
                raise ValueError('root_cell')
        else:
            parent=node['parent']
            if type(parent) is not int or not 0 <= parent < index:
                raise ValueError('node_parent')
            ancestor=nodes[parent]; al,ar=pf(ancestor['left']),pf(ancestor['right']); mid=(al+ar)/2
            if (a,b) not in ((al,mid),(mid,ar)) or node['depth']!=ancestor['depth']+1:
                raise ValueError('bisection')
        if node['depth'] > limits.depth or [x['ref'] for x in node['fields']] != expected:
            raise ValueError('node_inventory')
        for field, coefficient in zip(node['fields'],(*loaded.pair,*loaded.competitors)):
            if set(field) != {'ref','range','derivative','inactive','positive'}:
                raise ValueError('field_schema')
            value=read_interval(field['range'])
            if not 0 <= value.lo <= value.hi <= 1:
                raise ValueError('field_range')
            inactive=max(coefficient.dot*a,coefficient.dot*b)<=coefficient.q
            positive=min(coefficient.dot*a,coefficient.dot*b)>coefficient.q
            if field['inactive'] is not inactive or field['positive'] is not positive:
                raise ValueError('branch_proof')
            if inactive and value != Bounds.point(0):
                raise ValueError('inactive_range')
            if field['derivative'] is not None: read_interval(field['derivative'])
        derived=facts(node['fields'])
        if any(node[key]!=value for key,value in derived.items()):
            raise ValueError('node_false_claim')
    ids=result['frontier']
    if len(set(ids))!=len(ids) or any(type(i)is not int or not 0<=i<len(nodes) for i in ids):
        raise ValueError('frontier_ids')
    leaves=[nodes[i] for i in ids]
    if len(leaves)>limits.leaves:
        raise ValueError('frontier_limit')
    if leaves:
        cursor=loaded.cell['left']
        for item in leaves:
            if pf(item['left'])!=cursor: raise ValueError('coverage')
            cursor=pf(item['right'])
        if cursor!=loaded.cell['right']: raise ValueError('coverage')
        width=fr(max(read_interval(x['difference']).hi-read_interval(x['difference']).lo for x in leaves))
    else:
        if result['reason']!='deadline': raise ValueError('missing_frontier')
        width=None
    actual=classification(leaves) if leaves else 'TE'
    if result['classification']!=actual or result['maximum_difference_width']!=width:
        raise ValueError('false_classification')
    return {'classification':actual,'leaves':len(leaves),'nodes':len(nodes),
            'additional_depth':max((x['depth'] for x in leaves),default=0),
            'coverage_complete':bool(leaves),'unresolved_leaves':sum(x['status']=='unresolved' for x in leaves),
            'pair_equality_proved':bool(leaves) and all(x['pair_equal'] for x in leaves),
            'strict_winner_reversal':any(x['strict_pair'] for x in leaves) and any(x['status']=='TB' for x in leaves),
            'interior_equality_proved':any(x['interior_equality'] for x in leaves),
            'resource_limited':result['reason']!='proved'}
