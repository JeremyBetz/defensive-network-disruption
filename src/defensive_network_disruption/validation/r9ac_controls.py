"""Frozen provider-free R9AC coefficient controls, with measured outcomes."""
from __future__ import annotations
from fractions import Fraction as F
from ..geometry.r9x_terminal_authority import Coefficients, SOURCE_KEYS, digest
from ..geometry.r9aa_terminal_authority import create_authority_v2
from ..geometry.r9ac_terminal_bound import bound, Limits

SOURCE={key:digest(('synthetic:'+key).encode()) for key in SOURCE_KEYS}

def coefficient(q=1,dot=4,cross2=0):return Coefficients(F(q),F(dot),F(cross2))

def authority(pair,competitors,*,left=F(1,2),right=F(1)):
    if not isinstance(pair,tuple):pair=(pair,pair)
    relation='symbolic_identity' if pair[0]==pair[1] else 'tolerance_certified'
    if all(max(x.dot*left,x.dot*right)<=x.q for x in pair) and pair[0]!=pair[1]:relation='common_inactive_branch'
    return create_authority_v2(ordinal=0,depth=0,left=left,right=right,pair=pair,
        competitors=tuple(competitors),source=SOURCE,relation_type=relation,
        tolerance_authority_sha256=digest(b'synthetic_tolerance'),
        structural_tie_lineage_sha256=digest(b'synthetic_tie'),
        boundary_authority_sha256=digest(b'synthetic_boundary'),
        interval_authority_sha256=digest(b'synthetic_interval'))


def fixtures():
    p=coefficient(cross2=8); zero=coefficient(); close=coefficient(cross2=F(8)+F(1,10**30))
    inactive=(coefficient(dot=0),coefficient(q=4,dot=0))
    return [
        ('pair_maximal',authority(zero,[p]),Limits(),'TA'),
        ('competitor_dominant',authority(p,[zero]),Limits(),'TB'),
        ('dominance_switch',authority(inactive,[coefficient(dot=2)],left=F(1,4),right=F(3,4)),Limits(),'TC'),
        ('interior_equality',authority(p,[p,close]),Limits(depth=0),'TD'),
        ('unresolved_overlap',authority(p,[close]),Limits(depth=0),'TE'),
        ('distinct_pair',authority((zero,p),[coefficient(cross2=16)]),Limits(),'TA'),
        ('symbolic_identity',authority(zero,[zero]),Limits(),'TA'),
        ('common_inactive',authority(inactive,[coefficient(q=9,dot=0)]),Limits(),'TA')]


def controls():
    rows=[];details=[]
    for name,record,limits,expected in fixtures():
        result,nodes=bound(record,limits=limits)
        rows.append({'control':name,'expected':expected,'observed':result['classification'],
                     'passed':result['classification']==expected})
        details.append({'control':name,'authority':record,'result':result,'nodes':nodes})
    for name in ('tampered_authority','missing_competitor'):
        record=authority(coefficient(),[coefficient(cross2=8)])
        if name=='tampered_authority':record['coefficients'][0]['q']['numerator']='2'
        else:record.pop('competitors')
        try:bound(record)
        except ValueError:observed='rejected'
        else:observed='accepted'
        rows.append({'control':name,'expected':'rejected','observed':observed,'passed':observed=='rejected'})
        details.append({'control':name,'authority':record,'observed':observed})
    if not all(row['passed'] for row in rows):raise ValueError('synthetic_control_failure')
    return rows,details
