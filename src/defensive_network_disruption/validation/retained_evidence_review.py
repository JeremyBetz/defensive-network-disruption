"""Standard-library retained-evidence review. No package or numerical imports."""
from __future__ import annotations
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re

PUBLIC = ('serializer_preflight.json','retained_failure_authority.json','topology_summary.json',
 'partition_audit.json','unsplit_convergence.csv','piecewise_convergence.csv','production_path.json',
 'onset_neighborhood.csv','piece_contributions.csv','agreement_gate_replay.json','stopping_logic.json',
 'runtime_breakdown.json','synthetic_reproduction.json','journal_replay_profile.json',
 'publication_options.json','emergency_record_check.json','qc.json')
OUTPUTS = ('evidence_inventory.csv','production_health.json','piecewise_health.json',
 'reference_eligibility.json','onset_only_health.json','gate_adjudication.json',
 'numerical_classification.json','journal_evidence_inventory.csv','replay_complexity.json',
 'publication_classification.json','repair_scope.json','qc.json')
HEALTH = ('production_health.json','piecewise_health.json','reference_eligibility.json',
 'onset_only_health.json','gate_adjudication.json')
CSV_FIELDS = ('domain','artifact','visibility','status','finding','sha256')
PRIVATE = {
 'controlled_vector': ('intervals','estimates.maximum','change'),
 'strict': ('lower','upper','residual_bound','pieces','quadrature_pieces','bounded_pieces'),
 'repeat': ('lower','upper','residual_bound','pieces','quadrature_pieces','bounded_pieces'),
 'onset_adaptive': ('estimate',), 'actual_gate_inputs': ('condition','reason'),
 'piecewise': ('intervals','estimate','successive_difference','seconds','evaluations'),
 'uniform': ('intervals','estimate','successive_difference','seconds','evaluations'),
 'independent_comparisons': ('health','production_difference','unsplit_difference'),
 'reproduction': ('reproduced','stage','calls','durations','inclusive_wall','inclusive_cpu',
                 'adaptive_returns.*.epsabs','adaptive_returns.*.epsrel','adaptive_returns.*.limit',
                 'adaptive_returns.*.estimate','adaptive_returns.*.reported_error'),
 'journal_metadata': ('records','bytes'),
 'timeout': ('exception','partial_operation.records','partial_operation.seconds',
             'partial_operation.cpu_seconds','partial_operation.calls','partial_operation.prefix_visits',
             'partial_operation.last_prefix','partial_operation.completed'),
 'retained_failure': ('original.exception','emergency.publication_exception'),
}

def canonical(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()

def digest(value): return hashlib.sha256(canonical(value)).hexdigest()

def safe(path):
    path=Path(path)
    if any(p.is_symlink() for p in (path,*path.parents)): raise PermissionError('symlink')
    return path

def sha(path):
    h=hashlib.sha256()
    with safe(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''): h.update(chunk)
    return h.hexdigest()

def atomic(path, value, raw=False):
    path=safe(path);path.parent.mkdir(parents=True,exist_ok=True)
    data=value if raw else canonical(value)
    temp=path.with_name('.'+path.name+'.pending')
    with temp.open('xb') as f: f.write(data);f.flush();os.fsync(f.fileno())
    try: os.link(temp,path)
    finally: temp.unlink()
    fd=os.open(path.parent,os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)

class Projection:
    """Lexically traverse JSON; decode scalar values only on allowlisted paths."""
    def __init__(self,text,paths):
        self.text=text;self.i=0;self.paths=[tuple(p.split('.')) for p in paths];self.decoded=[]
    def ws(self):
        while self.i<len(self.text) and self.text[self.i].isspace(): self.i+=1
    def string(self,decode):
        start=self.i;self.i+=1
        while self.i<len(self.text):
            c=self.text[self.i];self.i+=1
            if c=='\\': self.i+=1
            elif c=='"': return json.loads(self.text[start:self.i]) if decode else None
        raise ValueError('unterminated_string')
    def permitted(self,path):
        return any(len(path)>=len(p) and all(a==b or a=='*' for a,b in zip(p,path)) for p in self.paths)
    def wanted(self,path):
        return self.permitted(path) or any(len(p)>len(path) and all(a==b or a=='*' for a,b in zip(p,path)) for p in self.paths)
    def value(self,path=()):
        self.ws()
        if self.i>=len(self.text): raise ValueError('missing_value')
        keep=self.wanted(path);c=self.text[self.i]
        if c=='{':
            self.i+=1;result={};seen=set();self.ws()
            if self.text[self.i]=='}': self.i+=1;return result if keep else None
            while True:
                self.ws()
                if self.text[self.i]!='"': raise ValueError('key')
                key=self.string(True)
                if key in seen: raise ValueError('duplicate_key')
                seen.add(key);self.ws()
                if self.text[self.i]!=':': raise ValueError('colon')
                self.i+=1;v=self.value((*path,key))
                if self.wanted((*path,key)): result[key]=v
                self.ws();c=self.text[self.i];self.i+=1
                if c=='}': break
                if c!=',': raise ValueError('separator')
            return result if keep else None
        if c=='[':
            self.i+=1;result=[];n=0;self.ws()
            if self.text[self.i]==']':self.i+=1;return result if keep else None
            while True:
                v=self.value((*path,str(n)));n+=1
                if keep: result.append(v)
                self.ws();c=self.text[self.i];self.i+=1
                if c==']':break
                if c!=',':raise ValueError('separator')
            return result if keep else None
        permitted=self.permitted(path)
        if c=='"': v=self.string(permitted)
        else:
            start=self.i
            while self.i<len(self.text) and self.text[self.i] not in ',]} \r\n\t':self.i+=1
            token=self.text[start:self.i]
            if not re.fullmatch(r'(?:true|false|null|-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)',token): raise ValueError('scalar_syntax')
            v=json.loads(token) if permitted else None
        if permitted:
            self.decoded.append(path)
            if isinstance(v,float) and not math.isfinite(v):raise ValueError('nonfinite')
        return v
    def run(self):
        v=self.value();self.ws()
        if self.i!=len(self.text):raise ValueError('trailing_json')
        return v

def load(path): return strict_json(safe(path).read_bytes())

def strict_json(data):
    def pairs(items):
        out={}
        for k,v in items:
            if k in out:raise ValueError('duplicate_key')
            out[k]=v
        return out
    result=json.loads(data,object_pairs_hook=pairs,parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite')))
    canonical(result)
    return result

def select_label(name):
    m=re.fullmatch(r'[0-9]{6}_([a-z_]+)\.json',name)
    return m.group(1) if m and m.group(1) in PRIVATE else None

def read_selected(folder,name,expected):
    label=select_label(name)
    if label is None or Path(name).name!=name:raise PermissionError('private_not_allowed')
    path=folder/name
    if sha(path)!=expected:raise ValueError('retained_hash')
    return Projection(path.read_text(),PRIVATE[label]).run()

def finite(value):return type(value) in (float,int) and math.isfinite(value)

def classify(mechanisms):
    if set(mechanisms)!=set('ABCDEF') or any(v is not None and type(v) is not bool for v in mechanisms.values()):raise ValueError('mechanism_schema')
    supported=[k for k,v in mechanisms.items() if v is True]
    if len(supported)>1:return 'G',3 if any(k in 'DEF' for k in supported) else 2
    if not supported:return 'H',4
    k=supported[0];return k,1 if k in 'AB' else 2 if k=='C' else 3

def health(checks,limitations,refs):
    return dict(schema_version=1,status='reviewed',checks=checks,limitations=limitations,evidence=refs)

def csv_bytes(rows):
    f=io.StringIO(newline='');w=csv.DictWriter(f,fieldnames=CSV_FIELDS,lineterminator='\n');w.writeheader();w.writerows(rows);return f.getvalue().encode()

def validate(folder):
    m=load(folder/'manifest.json');q=load(folder/'qc.json')
    if set(m)!={'schema_version','status','outputs','authority','private_projection_sha256'} or m['schema_version']!=1:raise ValueError('manifest_schema')
    if set(m['outputs'])!=set(OUTPUTS):raise ValueError('output_set')
    if set(q)!={'schema_version','status','execution_valid','numerical','readiness','publication','geometry_accesses','new_numerical_evidence','combined_repair','private_projection_sha256'}:raise ValueError('qc_schema')
    if q['status'] not in ('closed','invalid') or m['status']!=q['status'] or q['execution_valid']!=(q['status']=='closed'):raise ValueError('execution')
    if any(type(q[k]) is not bool for k in ('execution_valid','combined_repair')):raise ValueError('boolean')
    if q['geometry_accesses']!=0 or q['new_numerical_evidence']!=0:raise ValueError('access')
    if m['private_projection_sha256']!=q['private_projection_sha256']:raise ValueError('private_cross_file')
    if q['private_projection_sha256'] is not None and sha(folder/'local/projected_evidence.json')!=q['private_projection_sha256']:raise ValueError('private_hash')
    for n,h in m['outputs'].items():
        if sha(folder/n)!=h:raise ValueError('output_hash')
        if n.endswith('.csv'):
            with (folder/n).open(newline='') as f:
                r=csv.DictReader(f);rows=list(r)
            if r.fieldnames!=list(CSV_FIELDS) or any(set(row)!=set(CSV_FIELDS) for row in rows):raise ValueError('csv_schema')
        elif n in HEALTH:
            r=load(folder/n)
            if set(r)!={'schema_version','status','checks','limitations','evidence'} or r['schema_version']!=1:raise ValueError('health_schema')
            if any(v is not None and type(v) is not bool for v in r['checks'].values()):raise ValueError('check_type')
        elif n!='qc.json':
            r=load(folder/n)
            if set(r)!={'schema_version','status','data'} or r['schema_version']!=1:raise ValueError('record_schema')
        text=(folder/n).read_text()
        if any(token in text for token in ('/Users/','/private/','"traceback"','"carrier"','"defenders"')):raise ValueError('privacy')
    if q['status']=='closed':
        n=load(folder/'numerical_classification.json')['data'];p=load(folder/'publication_classification.json')['data'];r=load(folder/'repair_scope.json')['data']
        if classify(n['mechanisms'])!=(q['numerical'],q['readiness']) or n['classification']!=q['numerical'] or n['readiness']!=q['readiness']:raise ValueError('classification_cross_file')
        if p['classification']!=q['publication'] or r['combined_authority']!=q['combined_repair']:raise ValueError('repair_cross_file')
        allowed=q['numerical'] in 'ABCG' and q['readiness'] in (1,2) and q['publication'] in ('P1','P2')
        if q['combined_repair']!=allowed:raise ValueError('false_acceptance')
        gate=load(folder/'gate_adjudication.json')['checks']
        onset=load(folder/'onset_only_health.json')['checks']
        if n['mechanisms']['A'] is True and onset.get('insufficient_convergence_established') is not True:raise ValueError('unsupported_A')
        if n['mechanisms']['B'] is True and gate.get('unjustified_equivalence_established') is not True:raise ValueError('unsupported_B')
    return True
