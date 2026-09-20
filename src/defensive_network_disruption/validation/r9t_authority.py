"""Allowlisted R9S retained authority; no population or reference-evaluation route."""
from dataclasses import fields
from fractions import Fraction as F
import json
import math
from pathlib import Path
from .r9j_evidence import sha,load

SOURCE='outputs/continuous_occlusion_binary64_transition_trace/local'
INDEX='0664c743e1319f2882a42d08a30a2d92eafb5657e5b20e53f99668325df28f98'
PROTOCOL='docs/protocols/phase_14r9t_binary64_transition_contract_repair.md'


def allowlist(root):
    return json.loads((root/PROTOCOL).read_text().split('```json\n')[2].split('\n```',1)[0])


def verify_sources(root):
    folder=root/SOURCE
    if sha(folder/'private_index.json')!=INDEX:raise ValueError('r9s_index_hash')
    index=load(folder/'private_index.json')['files'];allowed=allowlist(root)
    for name,h in allowed.items():
        if index.get(name)!=h or sha(folder/name)!=h:raise ValueError('r9s_source_hash')
    return allowed


def decode(value):
    if type(value)is list:return [decode(v) for v in value]
    if type(value)is dict:
        if set(value)=={'float','hex'}:
            v=value['float']
            if type(v)is not float or not math.isfinite(v) or v.hex()!=value['hex']:raise ValueError('float_evidence')
            return v
        if set(value)=={'numerator_hex','denominator_hex'}:
            a,b=int(value['numerator_hex'],16),int(value['denominator_hex'],16)
            if b<=0:raise ValueError('rational_evidence')
            return F(a,b)
        return {k:decode(v) for k,v in value.items()}
    return value


def strict(cls,value,**overrides):
    if set(value)!={f.name for f in fields(cls)}:raise ValueError('dataclass_schema')
    return cls(**{**value,**overrides})


def topology(value):
    from ..geometry.r9r_localization import Bounds,Cell,Topology
    cells=[]
    for cell in value['cells']:
        cells.append(strict(Cell,cell,difference=strict(Bounds,cell['difference']),
            derivative=None if cell['derivative'] is None else strict(Bounds,cell['derivative'])))
    return strict(Topology,value,cells=tuple(cells),root_intervals=tuple(tuple(x) for x in value['root_intervals']),boundary_roots=tuple(value['boundary_roots']))


def crossing(value):
    from ..geometry.r9t_transition import CrossingAuthority
    return strict(CrossingAuthority,value,topology=topology(value['topology']),
        enclosure=tuple(value['enclosure']),structural_region=tuple(value['structural_region']))


def evidence(value):
    from ..geometry import r9t_transition as t
    from ..geometry.r9r_localization import Transition
    v=decode(value)
    return strict(t.TransitionEvidence,v,authority=crossing(v['authority']),
        windows=tuple(tuple(x) for x in v['windows']),probes=tuple(strict(t.Probe,p) for p in v['probes']),
        cache=tuple(tuple(x) for x in v['cache']),transition=strict(Transition,v['transition']))


def input_tuple(value):
    from ..geometry import r9t_transition as t
    a,w,p,c=decode(value)
    return crossing(a),tuple(tuple(x) for x in w),tuple(strict(t.Probe,x) for x in p),tuple(tuple(x) for x in c)


def resolve_saved(trace,records):
    """Pure saved-observation rule. No field or mathematical-bound recomputation."""
    from ..geometry import r9s_trace as s
    from ..geometry import r9t_transition as t
    from . import r9s_authority as inherited
    summary=s.summarize(trace,retained=True)
    if (summary['diagnosis'],summary['pattern'],summary['count'],summary['complete'])!=('BC','F',65,True):raise ValueError('r9s_identity')
    args,reference,structures=inherited.context(records)
    if trace['arguments']!=args or trace['reference']!=reference or trace['structures']!=structures:raise ValueError('r9s_trace_authority')
    region=decode(records['region']['value']);top=topology(decode(records['topology']['value']))
    a,b=map(s.fraction,args['enclosure']);lo,hi=map(s.number,args['outer'])
    authority=t.CrossingAuthority(top,(a,b),lo,hi,args['before'],args['after'],tuple(region['structural_neighbors']))
    probes=tuple(t.Probe(p['ordinal'],p['window'],p['key'],s.number(p['difference'])) for p in trace['probes'])
    windows=tuple(tuple(w['bounds']) for w in trace['windows'])
    cache=tuple(tuple(v) for v in trace['final']['cache'])
    return t.canonicalize(authority,windows,probes,cache)
