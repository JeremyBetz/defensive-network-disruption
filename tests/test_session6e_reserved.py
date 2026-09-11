import ast
import base64
import copy
import hashlib
import http.client
import inspect
import json
import socket
import ssl
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

import numpy as np
from defensive_network_disruption.data import session6e_transport as t
from defensive_network_disruption.data.session6c_source import public_entry, git_blob_oid, safe_destination, parse_lfs_pointer, verify_blob
from test_session6c_reserved import Response, Opener, pointer
from test_session6_reserved import fixture
import scripts.session_06e_reserved as r

TEST_TEMP_ROOT = Path(__file__).resolve().parent


def dns(*args,**kwargs):
    return [(socket.AF_INET,socket.SOCK_STREAM,6,'',('185.199.108.133',443))]


def envelope(p, url=None, **action):
    return {'transfer':'basic','objects':[{'oid':p.payload_sha256,'size':p.payload_size,'actions':{'download':{'href':url or 'https://github-cloud.githubusercontent.com/synthetic?signature=SECRET',**action}}}]}


def setup_client(body=b'complete', outcomes=None):
    p=t.LfsPointer(hashlib.sha256(body).hexdigest(),len(body))
    env=envelope(p)
    opener=Opener([Response(t.BATCH,json.dumps(env).encode()),*(outcomes if outcomes is not None else [Response(env['objects'][0]['actions']['download']['href'],body)])])
    ledger=[];waits=[]
    client=t.OfficialLfsClient('REPOSITORY_SECRET',opener=opener,ledger=lambda *a:ledger.append(a),sleeper=waits.append,resolver=dns)
    return client,opener,p,ledger,waits


def entry():
    return t.TreeEntry(t.source_path('1874553','tracking',t.RESERVED),'blob','a'*40,133)


class OfficialTransportTests(unittest.TestCase):
    def test_exact_batch_and_no_repository_auth(self):
        client,opener,p,_,_=setup_client()
        requests=[]
        original=opener.open
        def capture(req,timeout):
            requests.append(req);return original(req,timeout)
        opener.open=capture
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as d:
            result=client.acquire(entry(),Path(d)/'payload',pointer=p,label='reserved_01')
        self.assertEqual(result,{'bytes':8,'lfs_payload_sha256':p.payload_sha256})
        self.assertEqual(json.loads(requests[0].data),{'operation':'download','transfers':['basic'],'objects':[{'oid':p.payload_sha256,'size':8}]})
        self.assertNotIn('Authorization',requests[0].headers)
        self.assertNotIn('REPOSITORY_SECRET',str(requests[1].headers))

    def test_duplicate_json_and_nonfinite_reject(self):
        for raw in (b'{"objects":[],"objects":[]}',b'{"size":NaN}',b'{'):
            with self.assertRaises(t.IntegrityError):t.unique_json(raw)

    def test_object_cardinality_identity_size_transfer_errors(self):
        p=t.LfsPointer('a'*64,3);good=envelope(p)
        cases=[]
        for objects in ([],good['objects']*2,None):cases.append(dict(good,objects=objects))
        for change in ({'oid':'b'*64},{'size':4},{'size':True},{'error':{}},{'actions':{}},{'size':None}):
            case=copy.deepcopy(good);case['objects'][0].update(change);cases.append(case)
        cases.extend([dict(good,transfer='other'),dict(good,hash_algo='sha1')])
        for case in cases:
            with self.subTest(case=case),self.assertRaises(t.IntegrityError):t.validate_action(case,p,resolver=dns)

    def test_action_https_origin_userinfo_port_and_fragment(self):
        p=t.LfsPointer('a'*64,0)
        for url in ('http://github-cloud.githubusercontent.com/a','https://evil.example/a','https://u@github-cloud.githubusercontent.com/a','https://github-cloud.githubusercontent.com:444/a','https://github-cloud.githubusercontent.com/a#x','file:///a','https://127.0.0.1/a'):
            with self.subTest(url=url),self.assertRaises(t.IntegrityError):t.validate_action(envelope(p,url),p,resolver=dns)

    def test_private_or_empty_dns(self):
        p=t.LfsPointer('a'*64,0)
        for addresses in ([],[(2,1,6,'',('127.0.0.1',443))],[(2,1,6,'',('10.0.0.1',443))]):
            with self.assertRaises(t.IntegrityError):t.validate_action(envelope(p),p,resolver=lambda *a,**k:addresses)

    def test_action_header_allowlist(self):
        p=t.LfsPointer('a'*64,0)
        self.assertEqual(t.validate_action(envelope(p,header={'Authorization':'action-secret'}),p,resolver=dns).headers,{'Authorization':'action-secret'})
        for header in ({'Cookie':'x'},{'Host':'x'},{'Proxy-Authorization':'x'},{'Range':'x'},{'Connection':'x'},{'Accept':'x\r\ny'},{'Accept-Encoding':'gzip'},{'Accept':'x','accept':'y'},{'Accept':'x'*8193}):
            with self.assertRaises(t.IntegrityError):t.validate_action(envelope(p,header=header),p,resolver=dns)

    def test_expiry_and_action_repr_redacted(self):
        p=t.LfsPointer('a'*64,0)
        a=t.validate_action(envelope(p,expires_in=30),p,now=5,resolver=dns)
        self.assertEqual(a.expires,35);self.assertNotIn('SECRET',repr(a))
        for expiry in (0,-1,True,'30'):
            with self.assertRaises(t.IntegrityError):t.validate_action(envelope(p,expires_in=expiry),p,resolver=dns)
        with self.assertRaises(t.IntegrityError):t.validate_action(envelope(p,expires_at='yesterday'),p,resolver=dns)

    def test_permitted_transport_retries(self):
        url=envelope(t.LfsPointer('a'*64,8))['objects'][0]['actions']['download']['href']
        errors=[TimeoutError(),ConnectionResetError(),ConnectionAbortedError(),BrokenPipeError(),http.client.IncompleteRead(b'x',2)]
        errors += [urllib.error.HTTPError(url,n,'busy',{},None) for n in (500,502,503,504)]
        for error in errors:
            client,opener,p,ledger,waits=setup_client(outcomes=[error,Response(url,b'complete')])
            with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as d:
                dest=Path(d)/'p';client.acquire(entry(),dest,pointer=p,label='reserved_01')
                self.assertEqual(dest.read_bytes(),b'complete');self.assertEqual(list(Path(d).glob('.*.tmp')),[])
            self.assertEqual(waits,[1]);self.assertEqual(opener.urls[1],opener.urls[2])
            self.assertEqual([x[1] for x in ledger if x[0]=='reserved_01' and x[2]=='started'],[1,2])

    def test_exhaustion(self):
        client,opener,p,ledger,waits=setup_client(outcomes=[TimeoutError()]*3)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as d,self.assertRaises(t.TransportError):client.acquire(entry(),Path(d)/'p',pointer=p,label='reserved_01')
        self.assertEqual(waits,[1,2]);self.assertEqual(len(opener.urls),4)

    def test_forbidden_retry_tls_http_integrity(self):
        url=envelope(t.LfsPointer('a'*64,8))['objects'][0]['actions']['download']['href']
        errors=[ssl.SSLCertVerificationError('SECRET'),t.IntegrityError('identity'),urllib.error.HTTPError(url,403,'expired',{},None),urllib.error.HTTPError(url,404,'missing',{},None)]
        for error in errors:
            client,opener,p,ledger,waits=setup_client(outcomes=[error,Response(url,b'complete')])
            with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as d,self.assertRaises(t.IntegrityError) as cm:client.acquire(entry(),Path(d)/'p',pointer=p,label='reserved_01')
            self.assertNotIn('SECRET',str(cm.exception));self.assertEqual(waits,[]);self.assertEqual(len(opener.urls),2)
            self.assertNotIn('SECRET',str(ledger))

    def test_wrong_sha_size_truncation_redirect_no_retry(self):
        url=envelope(t.LfsPointer('a'*64,8))['objects'][0]['actions']['download']['href']
        for response in (Response(url,b'wrongxxx'),Response(url,b'short'),Response(url,b'complete',declared=9),Response('https://elsewhere.invalid',b'complete')):
            client,opener,p,_,waits=setup_client(outcomes=[response,Response(url,b'complete')])
            with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as d,self.assertRaises(t.IntegrityError):client.acquire(entry(),Path(d)/'p',pointer=p,label='reserved_01')
            self.assertEqual(waits,[]);self.assertEqual(len(opener.urls),2)

    def test_interrupted_bytes_not_combined_and_fresh_files(self):
        url=envelope(t.LfsPointer('a'*64,8))['objects'][0]['actions']['download']['href']
        class Broken(Response):
            def read(self,size=-1):
                if self.offset:raise http.client.IncompleteRead(b'xx',2)
                self.offset=1;return b'bad'
        client,_,p,_,_=setup_client(outcomes=[Broken(url),Response(url,b'complete')])
        names=[];original=t.tempfile.mkstemp
        def capture(*a,**k):
            value=original(*a,**k);names.append(value[1]);return value
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as d,patch.object(t.tempfile,'mkstemp',side_effect=capture):
            dest=Path(d)/'p';client.acquire(entry(),dest,pointer=p,label='reserved_01')
            self.assertEqual(dest.read_bytes(),b'complete');self.assertEqual(len(set(names)),2)
            self.assertTrue(all(not Path(n).exists() for n in names))

    def test_expired_refresh_keeps_object_and_budget(self):
        p=t.LfsPointer(hashlib.sha256(b'complete').hexdigest(),8)
        env=envelope(p,expires_in=1);url=env['objects'][0]['actions']['download']['href']
        opener=Opener([Response(t.BATCH,json.dumps(env).encode()),TimeoutError(),Response(t.BATCH,json.dumps(env).encode()),Response(url,b'complete')])
        ticks=iter([0,2,2]);requests=[];original=opener.open
        def capture(req,timeout):requests.append(req);return original(req,timeout)
        opener.open=capture
        c=t.OfficialLfsClient(opener=opener,sleeper=lambda _:None,resolver=dns,clock=lambda:next(ticks))
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as d:c.acquire(entry(),Path(d)/'p',pointer=p,label='reserved_01')
        self.assertEqual(requests[0].data,requests[2].data)

    def test_batch_bounds_redirect_tls_and_retry(self):
        p=t.LfsPointer('a'*64,0)
        for response in (Response(t.BATCH,b'x'*65537),Response('https://elsewhere.invalid',b'{}'),ssl.SSLCertVerificationError()):
            opener=Opener([response]);c=t.OfficialLfsClient(opener=opener,resolver=dns)
            with self.assertRaises(t.IntegrityError):c.batch(p,'reserved_01:batch')
        opener=Opener([TimeoutError(),Response(t.BATCH,json.dumps(envelope(p)).encode())]);waits=[]
        c=t.OfficialLfsClient(opener=opener,sleeper=waits.append,resolver=dns)
        c.batch(p,'reserved_01:batch');self.assertEqual(waits,[1])

    def test_no_redownload_and_unsafe_paths(self):
        client,_,p,_,_=setup_client()
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as d:
            dest=Path(d)/'p';dest.write_bytes(b'old')
            with self.assertRaises(t.IntegrityError):client.acquire(entry(),dest,pointer=p,label='reserved_01')
            dest.unlink();dest.symlink_to(Path(d)/'other')
            with self.assertRaises(t.IntegrityError):client.acquire(entry(),dest,pointer=p,label='reserved_01')
        for match in ('1953632','1886347','../1874553'):
            with self.assertRaises((PermissionError,t.IntegrityError)):t.check_entry(t.TreeEntry(f'data/matches/{match}/x','blob','a'*40,1))
        with self.assertRaises((PermissionError,t.IntegrityError)):t.check_entry(t.TreeEntry('data/matches/1874553/pose.json','blob','a'*40,1))

    def test_ordinary_blob_no_auth_and_integrity(self):
        body=b'{}';e=t.TreeEntry(t.source_path('1874553','metadata',t.RESERVED),'blob',git_blob_oid(body),len(body))
        url=f'https://raw.githubusercontent.com/{t.OWNER_REPO}/{t.SOURCE_COMMIT}/{e.path}'
        op=Opener([Response(url,body)]);c=t.OfficialLfsClient('secret',opener=op)
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as d:
            self.assertEqual(c.acquire(e,Path(d)/'p',pointer=None,label='reserved_01'),{'git_oid':e.git_oid,'bytes':2})

    def test_real_default_tls_context_and_no_science_imports(self):
        c=t.OfficialLfsClient()
        https=next(h for h in c._opener.handlers if isinstance(h,t.urllib.request.HTTPSHandler))
        self.assertEqual(https._context.verify_mode,ssl.CERT_REQUIRED);self.assertTrue(https._context.check_hostname)
        text=Path(t.__file__).read_text()
        self.assertNotIn('media.githubusercontent.com',text)
        imports=[n.module for n in ast.walk(ast.parse(text)) if isinstance(n,ast.ImportFrom)]
        self.assertFalse(any('model' in (n or '') or 'validation' in (n or '') for n in imports))

    def test_pointer_historical_regression(self):
        raw=pointer(size=90729279);self.assertEqual(len(raw),133)
        e=t.TreeEntry(entry().path,'blob',git_blob_oid(raw),133)
        env={'sha':e.git_oid,'size':133,'encoding':'base64','content':base64.b64encode(raw).decode()}
        self.assertEqual(parse_lfs_pointer(verify_blob(e,env,decoded_limit=1024)).payload_size,90729279)


class CommandLifecycleTests(unittest.TestCase):
    def sandbox(self,directory):
        """Synthetic I/O only; production reader/features/metrics remain unpatched."""
        from contextlib import ExitStack
        stack=ExitStack();root=Path(directory)
        out=root/'outputs';local=out/'local';data=root/'data'
        paths={'ROOT':root,'OUTPUT':out,'LOCAL':local,'DATA':data,'SOURCE_AUTHORITY':local/'source_authority.json','SOURCE_RECEIPTS':local/'source_receipts.json','ACCESS_LEDGER':local/'access.jsonl','POPULATION':local/'population.jsonl','ALIAS_MAP':local/'aliases.json','EXECUTION':local/'execution.json','TRANSPORT_AUTHORITY':out/'transport_authority.json','POPULATION_SUMMARY':out/'population_summary.json','PROTOCOL':root/'protocol.md','FINAL_MODELS':root/'models.json'}
        for key,value in paths.items():stack.enter_context(patch.object(r,key,value))
        root.joinpath('protocol.md').write_text('synthetic')
        models={'environment':{'synthetic':True},'models':{m:{'mean':[0.]*n,'scale':[1.]*n,'coefficients':[.01]*n,'feature_names':[str(i) for i in range(n)]} for m,n in (('m0',3),('m1',5),('m2',6))}}
        root.joinpath('models.json').write_text(json.dumps(models))
        stack.enter_context(patch.object(r,'verify_history',return_value=models));stack.enter_context(patch.object(r,'ensure_implementation_committed',return_value='synthetic'))
        stack.enter_context(patch.object(r,'require_clean'));stack.enter_context(patch.object(r,'require_committed',return_value='synthetic'));stack.enter_context(patch.object(r,'git',return_value='synthetic'));stack.enter_context(patch.object(r,'implementation_hashes',return_value={'synthetic':'0'*64}))
        local.mkdir(parents=True)
        raw={};records={}
        fx=fixture()
        import csv,io
        buf=io.StringIO();writer=csv.DictWriter(buf,fieldnames=list(fx.events[0]));writer.writeheader();writer.writerows(fx.events)
        bodies={'metadata':json.dumps(dict(fx.metadata,sentinel='DO_NOT_RETAIN')).encode(),'events':buf.getvalue().encode(),'tracking':(json.dumps(dict(fx.frames[0],sentinel='DO_NOT_RETAIN'))+'\n').encode()}
        for match,alias in r.RESERVED_ALIASES.items():
            records[alias]={}
            for product,body in bodies.items():
                path=t.source_path(match,product,t.RESERVED);raw[path]=body
                ptr=t.LfsPointer(hashlib.sha256(body).hexdigest(),len(body)) if product=='tracking' else None
                obj=pointer(ptr.payload_sha256,ptr.payload_size) if ptr else body
                e=t.TreeEntry(path,'blob',git_blob_oid(obj),len(obj))
                records[alias][product]={'path':path,**public_entry(e,ptr)}
        authority={'source_commit':t.SOURCE_COMMIT,'source_tree':'a'*40,'records':records}
        r.atomic_text(r.SOURCE_AUTHORITY,r.json_text(authority));r.atomic_text(r.TRANSPORT_AUTHORITY,r.json_text({'reserved_match_count':10,'withheld_access':False}))
        stack.enter_context(patch.object(r,'load_source_authority',return_value=({},authority)))
        class SyntheticClient:
            def __init__(self,**kwargs):pass
            def acquire(self,e,destination,*,pointer,label):
                r.append_access(label,1,'started',None)
                destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(raw[e.path])
                r.append_access(label,1,'verified',None)
                return {'lfs_payload_sha256':pointer.payload_sha256,'bytes':len(raw[e.path])} if pointer else {'git_oid':e.git_oid,'bytes':len(raw[e.path])}
        stack.enter_context(patch.object(r,'OfficialLfsClient',SyntheticClient))
        return stack,models,authority

    def test_end_to_end_production_prepare_score_and_closure(self):
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as d:
            stack,models,authority=self.sandbox(d)
            with stack:
                r.preflight();r.acquire_reserved();r.verify_acquired(authority);r.prepare_reserved()
                self.assertNotIn('DO_NOT_RETAIN',r.POPULATION.read_text())
                summary=json.loads(r.POPULATION_SUMMARY.read_text());self.assertEqual(summary['evaluation_eligible'],10)
                self.assertFalse((r.OUTPUT/'aggregate_metrics.json').exists())
                with patch.object(r,'OfficialLfsClient',side_effect=AssertionError('scoring cannot acquire')):
                    r.score()
                r.publication_check();r.validate_outputs()
                self.assertEqual(json.loads((r.OUTPUT/'manifest.json').read_text())['status'],'closed')
                with self.assertRaises(RuntimeError):r.score()
                with self.assertRaises(FileExistsError):r.create_execution_marker()

    def test_acquisition_failure_closes_without_population(self):
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as d:
            stack,_,_=self.sandbox(d)
            with stack,patch.object(r,'OfficialLfsClient',side_effect=t.IntegrityError('synthetic')):
                r.append_access('rehearsal',1,'started',None)
                with self.assertRaises(SystemExit):r.dispatch('acquire-reserved')
                r.publication_check()
                m=json.loads((r.OUTPUT/'manifest.json').read_text());self.assertEqual(m['verified_products'],0);self.assertFalse(m['scoring_started'])

    def test_preparation_failure_is_not_repaired_or_scored(self):
        from defensive_network_disruption.data.session6_population import Session6ContractError
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as d:
            stack,_,_=self.sandbox(d)
            with stack:
                r.acquire_reserved()
                with patch.object(r,'prepare_match_session6',side_effect=Session6ContractError('synthetic unsupported state')):
                    with self.assertRaises(SystemExit):r.dispatch('prepare-reserved')
                r.publication_check();m=json.loads((r.OUTPUT/'manifest.json').read_text())
                self.assertEqual(m['verified_products'],30);self.assertTrue(m['structural_access_started']);self.assertFalse(m['scoring_started'])

    def test_scoring_validation_failure_remains_unclosed(self):
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as d:
            stack,_,_=self.sandbox(d)
            with stack:
                r.acquire_reserved();r.prepare_reserved()
                with patch.object(r,'validate_outputs',side_effect=RuntimeError('synthetic validation defect')):
                    with self.assertRaises(SystemExit):r.dispatch('score')
                r.publication_check();m=json.loads((r.OUTPUT/'manifest.json').read_text())
                self.assertTrue(m['scoring_started']);self.assertEqual(m['status'],'invalid')
                self.assertEqual(json.loads(r.EXECUTION.read_text())['status'],'started')
                with self.assertRaises(RuntimeError):r.dispatch('score')

    def test_tampered_output_rejected(self):
        with tempfile.TemporaryDirectory(dir=TEST_TEMP_ROOT) as d:
            stack,_,_=self.sandbox(d)
            with stack:
                r.acquire_reserved();r.prepare_reserved();r.score()
                p=r.OUTPUT/'m2_m1_paired.csv';p.write_text(p.read_text().replace('reserved_01','reserved_11'))
                with self.assertRaises(RuntimeError):r.validate_outputs()

    def test_preparation_scoring_call_firewall(self):
        def names(fn):
            return {n.func.id for n in ast.walk(ast.parse(inspect.getsource(fn))) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)}
        self.assertTrue(names(r.prepare_reserved).isdisjoint({'expected_credits','score','fit_final_models'}))
        self.assertTrue(names(r.score).isdisjoint({'acquire_reserved','load_projected_match_session6','prepare_match_session6','fit_final_models'}))
        self.assertEqual(r.OUTPUT.name,'reserved_evaluation_v3')
        self.assertEqual(r.FINAL_MODELS_SHA,'0383561e45bcd9f8d84eccc7e9733b2409536f61c39193fa87d08c36c6f6fd65')

if __name__=='__main__':unittest.main()
