"""Synthetic-only production checks for Session 12b; no provider fixtures."""
import importlib.util
from pathlib import Path
import tempfile
from unittest.mock import patch
import json
import math
import ast
import base64
import unittest
import contextlib
import numpy as np
from defensive_network_disruption.networks.options import OptionState,FrozenOptionModel,evaluate_options,OptionNetwork,OptionEdge
from defensive_network_disruption.networks.spatial_value import NormalizedGoalwardProgression,horizon,compare_horizons,sign,identity_check
from defensive_network_disruption.data.dimension_projection import project_dimensions
from defensive_network_disruption.data.session6c_source import IntegrityError,TreeEntry,verify_blob,git_blob_oid,_transport_category
from defensive_network_disruption.validation.ranking_features import M0_NAMES,M1_NAMES,choice_features

def cases(names, values):
    def decorate(f):
        f._cases = [(v if isinstance(v,tuple) else (v,)) for v in values]
        return f
    return decorate

@contextlib.contextmanager
def raises(error, match=None):
    with unittest.TestCase().assertRaises(error) as caught:
        yield
    if match is not None:
        unittest.TestCase().assertRegex(str(caught.exception),match)

class Approx:
    def __init__(self,value,abs=1e-12): self.value=value;self.tol=abs
    def __eq__(self,other): return math.isclose(self.value,other,rel_tol=1e-12,abs_tol=self.tol)
def approx(value,abs=1e-12):return Approx(value,abs)

spec=importlib.util.spec_from_file_location('session12b',Path(__file__).parents[1]/'scripts/session_12b_progression.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)


def state():return OptionState((-20,0),('A','B','C'),((-10,-15),(0,15),(20,0)),((0,0),))
def network(ps,s=None):
    s=s or state()
    return OptionNetwork(None,'m0',tuple(OptionEdge(k,math.log(p) if p else -1000,p,i,1.) for i,(k,p) in enumerate(zip(s.candidate_ids,ps))),(),{})

@cases('x,expected',[(-50,0),(0,.5),(50,1)])
def test_endpoints_and_lateral(x,expected):
    v=NormalizedGoalwardProgression(100)
    assert v.value_at(x,-900)==v.value_at(x,900)==expected

@cases('length',[True,'100',0,-1,float('nan'),float('inf')])
def test_bad_length(length):
    with raises((ValueError,TypeError)):NormalizedGoalwardProgression(length)

@cases('x',[-50.00000000001,50.00000000001,float('nan'),float('inf'),True,'0'])
def test_coordinate_reject(x):
    with raises(ValueError):NormalizedGoalwardProgression(100).value_at(x,0)


def test_monotonic_and_frozen_formula_family():
    v=NormalizedGoalwardProgression(100)
    assert [v.value_at(x,0) for x in (-50,0,50)]==[0,.5,1]
    for u in (0,.5,1):
        assert u*(1-abs(2*.5-1))==u
        assert u*(1-abs(2*0-1))==0


def test_signed_horizons_and_identities():
    s=state();c=compare_horizons(s,network((.5,.3,.2)),network((.2,.3,.5)),NormalizedGoalwardProgression(100))
    assert c.shift==approx(.09)
    assert math.fsum(c.contributions)==approx(c.shift)
    assert compare_horizons(s,network((.2,.3,.5)),network((.5,.3,.2)),NormalizedGoalwardProgression(100)).shift==approx(-.09)
    s2=OptionState((20,0),s.candidate_ids,s.candidate_xy,s.defender_xy)
    assert horizon(s2,network((.5,.3,.2),s2),NormalizedGoalwardProgression(100)).horizon<0


def test_identical_values_and_shares():
    s=state();v=NormalizedGoalwardProgression(100)
    assert compare_horizons(s,network((.5,.3,.2)),network((.5,.3,.2)),v).shift==0
    equal=OptionState((0,0),s.candidate_ids,((20,1),(20,2),(20,3)),s.defender_xy)
    assert compare_horizons(equal,network((.5,.3,.2),equal),network((.2,.3,.5),equal),v).shift==approx(0,abs=1e-15)


def test_alignment_and_immutability():
    from dataclasses import FrozenInstanceError
    s=state()
    with raises(FrozenInstanceError):s.carrier_xy=(0,0)
    swapped=OptionState(s.carrier_xy,s.candidate_ids[::-1],s.candidate_xy[::-1],s.defender_xy)
    with raises(ValueError):horizon(s,network((.5,.3,.2),swapped),NormalizedGoalwardProgression(100))


def test_frozen_models_features_and_permutation():
    s=state()
    for name,names in [('m0',M0_NAMES),('m1',M1_NAMES)]:
        n=len(names);m=FrozenOptionModel(name,names,(0,)*n,(1,)*n,(-.1,.03,0)+((.01,.02) if n==5 else ()))
        a=evaluate_options(s,model=m);features=choice_features(s,name)[0]
        np.testing.assert_array_equal([e.utility for e in a.edges],features@np.array(m.coefficients))
        rev=OptionState(s.carrier_xy,s.candidate_ids[::-1],s.candidate_xy[::-1],s.defender_xy)
        b=evaluate_options(rev,model=m)
        assert horizon(s,a,NormalizedGoalwardProgression(100)).horizon==approx(horizon(rev,b,NormalizedGoalwardProgression(100)).horizon,abs=1e-15)
    np.testing.assert_array_equal(choice_features(s,'m0')[0],choice_features(s,'m1')[0][:,:3])


def test_selective_projection_sentinel():
    raw=b'{"secret":{"roster":["SENTINEL",{"outcome":true}]},"pitch_length":105,"pitch_width":68}'
    assert project_dimensions(raw)=={'pitch_length':105.,'pitch_width':68.}
    with patch('defensive_network_disruption.data.dimension_projection.json.loads',wraps=json.loads) as spy:
        project_dimensions(raw)
        assert all('SENTINEL' not in call.args[0] for call in spy.call_args_list)

@cases('raw',[b'{"pitch_length":true,"pitch_width":68}',b'{"pitch_length":"105","pitch_width":68}',b'{"pitch_length":0,"pitch_width":68}',b'{"pitch_length":1e999,"pitch_width":68}',b'{"pitch_width":68}',b'{"pitch_length":105,"pitch_width":68,"secret":{"x":1,"x":2}}',b'{"pitch_length":105,"pitch_width":68,"pitch_width":70}',b'[]',b'{"pitch_length":105,"pitch_width":68} secret'])
def test_projection_rejections(raw):
    with raises(ValueError,match='metadata_dimension_schema_invalid'):project_dimensions(raw)


def test_blob_integrity():
    b=b'{"pitch_length":105,"pitch_width":68}';oid=git_blob_oid(b);e=TreeEntry('synthetic','blob',oid,len(b))
    env={'sha':oid,'encoding':'base64','size':len(b),'content':base64.b64encode(b).decode()}
    assert verify_blob(e,env,decoded_limit=1000)==b
    with raises(IntegrityError):verify_blob(e,{**env,'size':len(b)+1},decoded_limit=1000)


def test_firewalls():
    for match,product in [('1953632','metadata'),('1874553','metadata'),('../escape','metadata'),(r.DEV[0],'events'),(r.DEV[0],'tracking')]:
        with raises(PermissionError):r.metadata_path(match,product)
    with tempfile.TemporaryDirectory(dir=r.ROOT) as tmp,patch.object(r,'ROOT',Path(tmp)):
        (Path(tmp)/'sym').symlink_to('/tmp')
        with raises(PermissionError):r.safe(Path('sym/file'))
        with raises(PermissionError):r.safe(Path('../file'))
    with raises(PermissionError):r.MetadataSource('unused')._request('https://media.githubusercontent.com/foo',label='x',maximum=1)


def test_target_independence():
    s=state();raw={'match_id':r.DEV[0],'event_id':'synthetic','carrier_xy':s.carrier_xy,'candidate_xy':s.candidate_xy,'candidate_ids':s.candidate_ids,'defender_xy':s.defender_xy,'target_index':0,'target_outside':False}
    assert r.project_row(raw)==r.project_row({**raw,'target_index':999,'target_outside':True})
    assert 'target' not in repr(r.project_row(raw))


def test_signs_typology_weighting_and_empty():
    assert [sign(x) for x in (-2e-12,-1e-12,0,1e-12,2e-12)]==['negative','zero','zero','zero','positive']
    rows=[{'alias':r.ALIASES[0],'H0':0.,'H1':s,'S':s,'D':d} for s in (-1.,0.,1.) for d in (-1.,0.,1.)]
    out=r.summarize(rows)['groups']['match_macro']
    assert all(v['count']==1 for v in out['typology'].values())
    two=[{'alias':'a','S':0.},{'alias':'b','S':1.},{'alias':'b','S':1.}]
    assert r.stats(two,'S')['mean']==.5
    assert r.stats([],'S')['mean'] is None
    assert r.pearson([1,1],[0,1]) is None


def test_concentration_not_value_and_numerical_guard():
    def neff(p):return math.exp(-math.fsum(x*math.log(x) for x in p if x))
    assert neff((.5,.3,.2))==approx(neff((.2,.3,.5)))
    uniform=network((1/3,)*3);v=NormalizedGoalwardProgression(100)
    assert neff((.8,.1,.1))<3 and neff((.1,.1,.8))<3
    assert compare_horizons(state(),uniform,network((.8,.1,.1)),v).shift<0
    assert compare_horizons(state(),uniform,network((.1,.1,.8)),v).shift>0
    with raises(ValueError):identity_check(0,1,[1])


def test_exclusive_and_failure_closure():
    with tempfile.TemporaryDirectory(dir=r.ROOT) as tmp,patch.object(r,'ROOT',Path(tmp)),patch.object(r,'git',return_value='synthetic'):
        r.exclusive('analyze')
        with raises(FileExistsError):r.exclusive('analyze')
        with patch.object(r,'ledger'),patch.object(r,'close_manifest') as close:
            r.failure('prepare',ValueError('longitudinal_bound_violation'))
            assert r.load(r.OUT/'qc.json')['status']=='blocked'
            close.assert_called_once_with('blocked')


def test_no_cross_command_routes_and_render():
    tree=ast.parse(Path(r.__file__).read_text())
    funcs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
    prepare=ast.unparse(funcs['prepare']);analyze=ast.unparse(funcs['analyze'])
    for term in ('evaluate_options(', 'compare_horizons(', '.value_at('):assert term not in prepare
    for term in ('verify_dimensions(', 'MetadataSource(', '.fit(', 'subprocess.check_output'):assert term not in analyze
    assert r.synthetic_svg()==r.synthetic_svg()
    import xml.etree.ElementTree as ET
    ET.fromstring(r.synthetic_svg())
    assert 'NOT CALIBRATED xT' in r.synthetic_svg()


def test_summary_schema_reject():
    with raises(ValueError):r.validate_summary({'unexpected':1})


def test_synthetic_prepare_to_closure():
    from contextlib import ExitStack
    with tempfile.TemporaryDirectory(dir=r.ROOT) as tmp,ExitStack() as stack:
        stack.enter_context(patch.object(r,'ROOT',Path(tmp)))
        for name,value in [('preflight',lambda:None),('committed',lambda p:None),('ledger',lambda *a,**k:None),('code_hashes',lambda:{}),('environment',lambda:{}),('git',lambda *a:'synthetic'),('COUNTS',(1,)*9)]:stack.enter_context(patch.object(r,name,value))
        for p in (r.PROTOCOL,r.AMEND):
            r.safe(p).parent.mkdir(parents=True,exist_ok=True);r.safe(p).write_text('synthetic protocol')
        models={n:FrozenOptionModel(n,names,(0,)*len(names),(1,)*len(names),(-.1,.03,0)+((.01,.02) if n=='m1' else ())) for n,names in [('m0',M0_NAMES),('m1',M1_NAMES)]}
        r.safe(r.MODEL).parent.mkdir(parents=True,exist_ok=True);r.safe(r.MODEL).write_text(r.encoded({'models':{n:{'feature_names':m.feature_names,'mean':m.mean,'scale':m.scale,'coefficients':m.coefficients} for n,m in models.items()}}))
        st=state();raw=[{'match_id':m,'event_id':'synthetic','candidate_ids':st.candidate_ids,'candidate_xy':st.candidate_xy,'defender_xy':st.defender_xy,'carrier_xy':st.carrier_xy,'target_index':0,'target_outside':False} for m in r.DEV]
        r.safe(r.POP).parent.mkdir(parents=True,exist_ok=True);r.safe(r.POP).write_text(''.join(json.dumps(x)+'\n' for x in raw))
        stack.enter_context(patch.object(r,'POP_SHA',r.digest(r.POP)))
        r.atomic(r.LOCAL/'dimensions.json',{'mapping':{m:{'pitch_length':100.,'pitch_width':60.} for m in r.DEV},'receipts':{},'implementation':{},'environment':{}})
        with patch.object(r,'evaluate_options',side_effect=AssertionError('prepare scored')):r.prepare()
        delta=evaluate_options(st,model=models['m1']).effective_option_count-evaluate_options(st,model=models['m0']).effective_option_count
        old={'groups':{a:{'models':{'change':{'effective_option_count':r.distribution([delta],[1.])}}} for a in (*r.ALIASES,'match_macro')}}
        oldpath=Path('outputs/attacking_option_network/network_summary.json');r.safe(oldpath).parent.mkdir(parents=True,exist_ok=True);r.safe(oldpath).write_text(r.encoded(old))
        with patch.object(r,'MetadataSource',side_effect=AssertionError('analysis acquired')):r.analyze()
        assert r.publication_check()
        r.render_synthetic();assert r.publication_check()
        with raises(ValueError):r.analyze()
        summary=r.load(r.OUT/'horizon_summary.json');summary['groups']['match_macro']['unexpected']=1
        with raises(ValueError):r.validate_summary(summary)


def test_transport_categories_and_retries():
    import socket,urllib.error,http.client
    permitted=[TimeoutError(),ConnectionResetError(),http.client.IncompleteRead(b'partial'),urllib.error.HTTPError('https://example.com',503,'temporary',{},None)]
    for e in permitted:assert _transport_category(e) is not None
    for e in [IntegrityError('hash'),ValueError('schema'),urllib.error.HTTPError('https://example.com',403,'denied',{},None)]:assert _transport_category(e) is None
    class Response:
        headers={'Content-Length':'2'}
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def geturl(self):return 'https://api.github.com/repos/SkillCorner/opendata/git/test'
        def read(self,n):return b'{}'
    from unittest.mock import Mock
    opener=Mock();opener.open.side_effect=[TimeoutError(),ConnectionResetError(),Response()]
    entries=[];wait=[];client=r.MetadataSource('unused',opener=opener,ledger=lambda *x:entries.append(x),sleeper=wait.append)
    assert client._request(Response().geturl(),label='synthetic',maximum=10)==b'{}'
    assert wait==[1.,2.] and len(opener.open.call_args_list)==3
    assert len({call.args[0].full_url for call in opener.open.call_args_list})==1
    assert sum(x[2]=='started' for x in entries)==3


class Session12bTests(unittest.TestCase):
    pass
for _name,_function in list(globals().items()):
    if _name.startswith('test_') and callable(_function):
        for _index,_args in enumerate(getattr(_function,'_cases',[()])):
            def _method(self,function=_function,args=_args):function(*args)
            setattr(Session12bTests,_name+'_'+str(_index),_method)

del _function, _method
