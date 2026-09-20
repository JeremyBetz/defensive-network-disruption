"""Allowlisted retained context, with no population or reference calculation route."""
from fractions import Fraction as F
from ..geometry.r9s_trace import binary, fraction, rational, sign
from .r9r_evidence import unprimitive
from .r9j_evidence import load, sha

R='outputs/continuous_occlusion_switch_localization_repair/local'
Q='outputs/continuous_occlusion_expanding_switch_equality_diagnosis/local'
R_INDEX='eb232a322574fea8b069c9fcb94c3a757ed1ee8a138bc17c6d7a3ddedd51d779'
Q_INDEX='5652d6e4d57a92c0bf084d20d6cc1ee33708713f15bc5ff4c325b7a715f9c14a'
SOURCES={
 'raw':(R,'000135_localization.json','caf0d67527fbb9185e5e63beb410b1ff9b6d2836d665d0d23052d9251c0a7f21'),
 'region':(R,'000136_localization.json','7323d80f082fe4e70b8a86a5ecfc412be3a45096b755a090b361606b80963126'),
 'pair':(R,'000137_localization.json','88ac5aea5cadb5739e8ab27302cbfafdfb98b018614d572853d72b7f07e1643e'),
 'topology':(R,'000138_localization.json','35c7da2876a06132fc76c697198a3fbc628bb8eaf827e996ad5bf8a1be186651'),
 'root':(R,'000139_localization.json','3044ac7ca2b2373dc02c6f1096dff0146aa955ffcb05277d4b06f56ea45c702f'),
 'work':(R,'000140_localization.json','fd6fdc84a6101bebfce5fdddf4c5754efa4c81c83c7a0d335fbf9a559cc6d92b'),
 'excluded':(Q,'000022_reference_cell.json','1097a05ac7eceb528d50fd07932ae85057262514e67e2bcda98bd110b840a428'),
 'selected':(R,'selected_geometry.json','d83657fca645d14531a74f28227ad0a0049717e6743de1b84d6ff408332a8954'),
 'receipt':(R,'access_materialized.json','e0d22f63e9def24b28ea6aa574200babce768a91d3cbe90f48c7c0670f8c0c8b'),
 'attempt':(R,'access_attempt.json','8cb4931d293d81478af9dbc5dbb6a174d9d9726b0e6d6eb9d844ba1a8978645b'),
 'lineage':(R,'retained_lineage.json','d74d80519ec8252cd45e8c9c902efe32a3e08290281ba318f59fd7eea91a0d2e'),
 'review':(Q,'retained_review.json','06061aeb8c6437da39e05503c8383e8c453713028c3bd75af8449d1218db82f1'),
}
KINDS=dict(raw='raw_structures',region='candidate_region',pair='pair_authority',topology='topology',root='isolated_root',work='inspection_work')


def verify_sources(root):
    indexes={}
    for directory,h in ((R,R_INDEX),(Q,Q_INDEX)):
        path=root/directory/'private_index.json'
        if sha(path)!=h:raise ValueError('retained_index_hash')
        indexes[directory]=load(path)['files']
    for label,(directory,name,h) in SOURCES.items():
        if indexes[directory].get(name)!=h or sha(root/directory/name)!=h:raise ValueError('retained_source_hash')


def context(records):
    """Interpret only already hash-verified records. No evaluation of any field."""
    values={}
    for label,kind in KINDS.items():
        item=records[label]
        if set(item)!= {'kind','value'} or item['kind']!=kind:raise ValueError('record_kind')
        values[label]=unprimitive(item['value'])
    raw,region,authority,top,root,work=(values[k] for k in KINDS)
    if work!={'floats_inspected':65}:raise ValueError('retained_inspection_count')
    lower,upper=region['constrained_region'];left,right=region['structural_neighbors']
    proposal=region['raw_proposal'];pairs=proposal['crossing_pairs']
    if len(pairs)!=1:raise ValueError('ambiguous_retained_pair')
    pair=pairs[0]
    if not 0<=left<=lower<proposal['location']<upper<=right<=1:raise ValueError('retained_region_order')
    if proposal not in raw['envelope']['switches']:raise ValueError('proposal_not_retained')
    if top['classification']!='B' or top['complete'] is not True or len(top['root_intervals'])!=1:raise ValueError('crossing_authority')
    cells=top['cells'];cross=[c for c in cells if c['kind']=='crossing']
    if len(cross)!=1 or fraction(cells[0]['left'])!=F.from_float(lower) or fraction(cells[-1]['right'])!=F.from_float(upper):raise ValueError('crossing_coverage')
    if any(fraction(a['right'])!=fraction(b['left']) for a,b in zip(cells,cells[1:])):raise ValueError('cell_gap')
    derivative=cross[0]['derivative']
    if derivative is None:raise ValueError('missing_derivative')
    dl,dh=map(fraction,(derivative['lo'],derivative['hi']))
    direction=1 if dl>0 else -1 if dh<0 else 0
    a,b=map(fraction,root)
    if not direction or not fraction(cross[0]['left'])<=a<=b<=fraction(cross[0]['right']):raise ValueError('root_derivative_authority')
    excluded=records['excluded'];ql,qr=map(fraction,(excluded['left'],excluded['right']))
    # R9Q cells store independent difference bounds. Never recalculate them.
    bounds=excluded['difference']
    def signed(v):
        if set(v)!={'lower','upper'}:raise ValueError('r9q_bound_schema')
        return 1 if fraction(v['lower'])>0 else -1 if fraction(v['upper'])<0 else 0
    excluded_proved=bool(signed(bounds)) or (excluded['derivative'] is not None and bool(signed(excluded['derivative'])) and signed(excluded['endpoints'][0])!=0 and signed(excluded['endpoints'][0])==signed(excluded['endpoints'][1]))
    if excluded['status']!='signed' or not excluded_proved:raise ValueError('excluded_region_not_signed')
    if not (b<ql or a>qr):raise ValueError('root_exclusion_conflict')
    receipt=records['receipt']
    if receipt['selected_sha256']!=SOURCES['selected'][2] or receipt['attempt_sha256']!=SOURCES['attempt'][2]:raise ValueError('materialization_lineage')
    if records['lineage']['review_sha256']!=SOURCES['review'][2]:raise ValueError('review_lineage')
    # No geometry is re-opened by publication checking. Coefficients were matched
    # during materialization; their immutable source hashes remain authoritative.
    reference=dict(enclosure=root,outer=[binary(lower),binary(upper)],one_crossing=True,
                   strict_derivative=True,authority_valid=True,boundary_refuted=False,
                   excluded=[rational(ql),rational(qr)])
    ties=[]
    for tie in raw['envelope']['tie_intervals']:
        ties.append([binary(0. if tie['start'] is None else tie['start']['inside']),
                     binary(1. if tie['end'] is None else tie['end']['inside'])])
    structures=dict(onsets=[binary(x['first_post_branch']) for x in raw['onsets']],ties=ties,status='uncertified')
    return dict(pair=pair,enclosure=root,outer=[binary(lower),binary(upper)],before=-direction,after=direction),reference,structures


def geometry_match(records,row):
    if set(row)!= {'alias','carrier','receiver','defenders'}:raise ValueError('selected_schema')
    pair=unprimitive(records['region']['value'])['raw_proposal']['crossing_pairs'][0]
    coefficients=records['pair']['value']
    origin=list(map(F.from_float,row['carrier']));end=list(map(F.from_float,row['receiver']))
    v=[x-y for x,y in zip(end,origin)]
    for label,index in zip(('first','second'),pair):
        d=[F.from_float(x)-y for x,y in zip(row['defenders'][index],origin)]
        expected=dict(q=sum(x*x for x in d),dot=sum(x*y for x,y in zip(v,d)),
                      cross2=(v[0]*d[1]-v[1]*d[0])**2,vv=sum(x*x for x in v))
        field=coefficients[label]
        if field['candidate']!='expanding' or any(fraction(field[k])!=val for k,val in expected.items()):raise ValueError('selected_pair_coefficients')
    return True
