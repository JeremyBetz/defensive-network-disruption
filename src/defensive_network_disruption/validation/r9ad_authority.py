"""Frozen R9AD metadata and tightly scoped retained-copy access."""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sys

START='5c26b2021f7224a22dbcebbf2564c82b8018f3b9'
TAG='f00690c05d8c1c6db308a65bd311c43f9a8ef2fa'
PROTOCOL='docs/protocols/phase_14r9ad_tie_boundary_mechanism_repair.md'
RUNNER='scripts/session_14r9ad_tie_boundary_mechanism_repair.py'
OUTPUT='outputs/continuous_occlusion_tie_boundary_mechanism_repair'
V='outputs/continuous_occlusion_tie_boundary_publication_diagnosis'

def sha(path):
    path=Path(path)
    if any(p.is_symlink() for p in (path,*path.parents)):raise PermissionError('symlink')
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()

def inventories(root):
    blocks=(Path(root)/PROTOCOL).read_text().split('```json\n')[1:]
    return tuple(json.loads(x.split('\n```',1)[0]) for x in blocks)

def verify(root):
    root=Path(root); bindings,private=inventories(root)
    for path,expected in bindings.items():
        if sha(root/path)!=expected:raise ValueError('inherited_binding')
    for namespace,authority in private.items():
        path=root/'outputs'/namespace/'local/private_index.json'
        if sha(path)!=authority['private_index_sha256']:raise ValueError('private_index_binding')
        if json.loads(path.read_bytes())!=authority['indexed_hashes']:raise ValueError('private_inventory')
    return private['continuous_occlusion_tie_boundary_publication_diagnosis']['indexed_hashes']['files']

def selected(root,local,permit):
    from .r9j_evidence import put,load
    if not permit:raise PermissionError('retained_gate')
    root=Path(root);local=Path(local);files=verify(root)
    if load(local/'access_attempt.json')!={'schema_version':1,'selected_sha256':files['selected_edge.json']}:
        raise ValueError('access_attempt_binding')
    # Only historical metadata and this one retained copy; no source fallback.
    for name in ('access_attempt.json','access_materialized.json','selected_edge.json'):
        if sha(root/V/'local'/name)!=files[name]:raise ValueError('selected_lineage_hash')
    receipt=load(root/V/'local/access_materialized.json')
    if receipt['selected_sha256']!=files['selected_edge.json'] or receipt['attempt_sha256']!=files['access_attempt.json']:
        raise ValueError('selected_materialization_lineage')
    row=load(root/V/'local/selected_edge.json')
    put(local/'selected_edge.json',row)
    put(local/'access_materialized.json',{'schema_version':1,'attempt_sha256':sha(local/'access_attempt.json'),
        'selected_sha256':sha(local/'selected_edge.json'),'reopened_states':1,'reopened_edges':1})
    return row

@contextmanager
def guard(root,own,permission):
    root=Path(root).resolve();own=Path(own).resolve();enabled=[True]
    bindings,private=inventories(root)
    allowed={root/path for path in bindings}
    allowed.update(root/'outputs'/n/'local/private_index.json' for n in private)
    allowed.update(root/path for path in (
        'outputs/continuous_occlusion_numerics_14b/reference_summary.json',
        'outputs/continuous_occlusion_max_switching/unresolved_case_comparison.csv',
        'outputs/continuous_occlusion_production_acceptance/reference_comparison.csv'))
    retained={root/V/'local'/name for name in ('selected_edge.json','access_attempt.json','access_materialized.json')}
    def hook(event,args):
        if not enabled[0]:return
        if event in ('socket.connect','socket.getaddrinfo'):raise PermissionError('governed_network')
        if event=='open' and isinstance(args[0],(str,bytes)):
            p=Path(args[0]).resolve()
            if p.is_relative_to(root/'data'):raise PermissionError('provider_access')
            if p.is_relative_to(root/'outputs') and not p.is_relative_to(own):
                certificate=(p.parent==root/'outputs/continuous_occlusion_terminal_interval_reference' and p.suffix=='.json')
                if p not in allowed and not certificate and not (permission[0] and p in retained):
                    raise PermissionError('retained_access_forbidden')
                if isinstance(args[1],str) and any(c in args[1] for c in 'wax+'):
                    raise PermissionError('historical_write')
    sys.addaudithook(hook)
    try:yield
    finally:enabled[0]=False
