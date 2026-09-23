"""Strict R9AC retained-content allowlist and source bindings."""
from __future__ import annotations
from contextlib import contextmanager
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import re
import sys

from .checkpoint_ci_authority import canonical_bytes

START = '3563a4460813901f910b0b14d780179046b0f101'
TAG = 'f00690c05d8c1c6db308a65bd311c43f9a8ef2fa'
PROTOCOL = 'docs/protocols/phase_14r9ac_terminal_cell_independent_bound.md'
RUNNER = 'scripts/session_14r9ac_terminal_cell_independent_bound.py'
OUTPUT = 'outputs/continuous_occlusion_terminal_cell_independent_bound'
AB = 'outputs/continuous_occlusion_terminal_cell_authority_v2_acquisition'
V = 'outputs/continuous_occlusion_tie_boundary_publication_diagnosis'
AUTHORITY_HASH = 'b9fab1e5b55d0e105f18d2abdaa2a5a6555547509616e4b9871df3ff57f6e6aa'
AB_INDEX = '25225bb78324b1092c0d91950ecc2e9021b336cb14753fe71c5db67e9d7ff023'
V_INDEX = '2abe5f916265275a94c157bd1a93c55f96d352863cbdce618a40418af3a2ebc6'
PARTITION = '91af2d5a17291223c49e2b361c4091b67047424e70d52cc305c64c49f78c2e26'
REFERENCE = '07697bfa5329193cb5f6cc1f632f1128654a04115fa48c2a8fcfc5656553168f'


def sha(path):
    path=Path(path)
    if path.is_symlink(): raise PermissionError('symlink')
    h=hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda:handle.read(1048576),b''): h.update(chunk)
    return h.hexdigest()


def load(path, expected=None):
    path=Path(path)
    if expected is not None and sha(path)!=expected: raise ValueError('source_hash')
    raw=path.read_bytes(); value=json.loads(raw)
    if canonical_bytes(value)!=raw: raise ValueError('noncanonical_record')
    return value


def inventory(root):
    text=(Path(root)/PROTOCOL).read_text()
    pairs=re.findall(r'^\| `([^`]+)` \| `([0-9a-f]{64})` \|$',text,re.M)
    if len(pairs)!=30 or len(dict(pairs))!=30: raise ValueError('protocol_inventory')
    return dict(pairs)


def verify_bindings(root):
    for name,expected in inventory(root).items():
        if sha(Path(root)/name)!=expected: raise ValueError('inherited_binding:'+name)
    return inventory(root)


def metadata(root):
    root=Path(root)
    ab=load(root/AB/'local/private_index.json',AB_INDEX)
    vi=load(root/V/'local/private_index.json',V_INDEX)
    for index in (ab,vi):
        if set(index)!={'schema_version','files'} or index['schema_version']!=1:
            raise ValueError('index_schema')
    if ab['files'].get('terminal_cell_authority_v2.json')!=AUTHORITY_HASH:
        raise ValueError('authority_index')
    names=[n for n in vi['files'] if re.fullmatch(r'reference_reference_cell_[0-9]+\.json',n)]
    if len(names)!=81: raise ValueError('status_inventory')
    return ab,vi,names


def retained(root):
    """Called only after checkpoint authorization and the create-once attempt."""
    from ..geometry.r9aa_terminal_authority import load_authority
    from ..geometry.r9x_terminal_authority import digest
    root=Path(root); ab,vi,names=metadata(root)
    rows=[]
    for name in names:
        row=load(root/V/'local'/name,vi['files'][name])
        if set(row)!={'ordinal','depth','pair_status','maximum_status'}:
            raise ValueError('status_schema')
        if type(row['ordinal'])is not int or type(row['depth'])is not int or not 0<=row['depth']<=80:
            raise ValueError('status_types')
        if row['pair_status'] not in ('equal','different','unresolved') or row['maximum_status'] not in ('maximum','dominated','unresolved','not_applicable'):
            raise ValueError('status_enum')
        rows.append(row)
    rows.sort(key=lambda row:row['ordinal'])
    if [r['ordinal'] for r in rows]!=list(range(81)) or digest(rows)!=PARTITION:
        raise ValueError('ordered_partition')
    if sum((F(1,2**r['depth']) for r in rows),F(0))!=1: raise ValueError('partition_coverage')
    unresolved=[r for r in rows if r['maximum_status']=='unresolved']
    if len(unresolved)!=1 or unresolved[0]['pair_status']!='equal': raise ValueError('unresolved_identity')
    record=load(root/AB/'local/terminal_cell_authority_v2.json',AUTHORITY_HASH)
    authority=load_authority(record)
    if authority.source_version!=2: raise ValueError('v2_required')
    source={'r9v_private_index_sha256':V_INDEX,'boundary_capture_sha256':vi['files']['boundary_capture.json'],
            'ordered_partition_sha256':PARTITION,'selected_edge_sha256':vi['files']['selected_edge.json'],
            'reference_implementation_sha256':REFERENCE}
    if record['source_authority']!=source: raise ValueError('source_authority')
    if (authority.cell['ordinal'],authority.cell['depth'])!=(unresolved[0]['ordinal'],unresolved[0]['depth']):
        raise ValueError('cell_lineage')
    # Completeness inherited from the exact hash-bound R9AB acquisition, not geometry re-read.
    manifest=load(root/AB/'manifest.json')
    summary=load(root/AB/'authority_capture.json',manifest['outputs']['authority_capture.json'])
    pair_summary=load(root/AB/'pair_authority_validation.json',manifest['outputs']['pair_authority_validation.json'])
    if len(record['coefficients'])!=summary['counts']['coefficient_records'] or len(record['competitors'])!=pair_summary['counts']['unique_competitor_references']:
        raise ValueError('competitor_inventory')
    if record['tie_authority']['boundary_authority_sha256']!=source['boundary_capture_sha256']:
        raise ValueError('tie_boundary_authority')
    if authority.relation_type!='common_inactive_branch' or record['pair_left_ref']==record['pair_right_ref']:
        raise ValueError('acquired_pair_relation')
    return record,rows


@contextmanager
def access_guard(root, own):
    """Audit actual opens: historical geometry paths are never allowed."""
    root,own=Path(root).resolve(),Path(own).resolve()
    enabled=[True]
    allowed={str(root/AB/'local/private_index.json'),str(root/AB/'local/terminal_cell_authority_v2.json'),
             str(root/V/'local/private_index.json')}
    allowed.update(str(root/name) for name in inventory(root))
    # Public authority files are pinned transitively by their committed manifest.
    allowed.update(str(root/AB/name) for name in ('authority_capture.json','pair_authority_validation.json'))
    prefix=str(root/V/'local')+'/'
    def hook(event,args):
        if not enabled[0]:return
        if event in ('socket.connect','socket.getaddrinfo'):raise PermissionError('governed_network_forbidden')
        if event=='open' and isinstance(args[0],(str,bytes)):
            p=Path(args[0]).resolve(); s=str(p)
            if p.is_relative_to(root/'data'):raise PermissionError('data_access_forbidden')
            if p.is_relative_to(root/'outputs') and not p.is_relative_to(own):
                status=s.startswith(prefix) and re.fullmatch(r'reference_reference_cell_[0-9]+\.json',p.name)
                if s not in allowed and not status:raise PermissionError('retained_access_forbidden')
                if isinstance(args[1],str) and any(c in args[1] for c in 'wax+'):raise PermissionError('historical_write_forbidden')
    sys.addaudithook(hook)
    try:yield
    finally:enabled[0]=False
