"""Synthetic Session 12c tests; no competition-value fixtures."""
import ast
from contextlib import ExitStack
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from defensive_network_disruption.data import boundary_review as b
from defensive_network_disruption.data.session6c_source import TreeEntry,verify_blob,git_blob_oid,IntegrityError
import base64
spec=importlib.util.spec_from_file_location('boundary_runner',Path(__file__).parents[1]/'scripts/session_12c_boundary.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)


def canonical():return dict(match_id=r.DEV[0],event_id='synthetic',carrier_xy=[51,1],candidate_ids=['p'],candidate_xy=[[-52,2]],defender_xy='SECRET',target_index='SECRET',target_outside='SECRET')
def metadata():return {'home_team':{'id':'home','secret':'SECRET'},'away_team':{'id':'away'},'home_team_side':['left_to_right','right_to_left'],'pitch_length':100,'pitch_width':60,'players':[{'id':pid,'team_id':'home','playing_time':{'by_period':[{'name':'period_1','start_frame':0,'end_frame':100}]},'secret':'SECRET'} for pid in ('carrier','p','other')]}
def tracking(frame,x=51):return {'frame':frame,'period':1,'timestamp':f'00:00:{frame/10:04.1f}','player_data':[{'player_id':'p','x':x,'y':1,'is_detected':True,'secret':'SECRET'},{'player_id':'other','x':'SECRET','y':'SECRET'}],'ball_data':'SECRET'}


class ProjectionTests(unittest.TestCase):
    def test_canonical_no_target_decoding(self):
        with patch.object(b.json,'loads',wraps=json.loads) as spy:
            row=b.canonical_projection(json.dumps(canonical()))
            self.assertFalse(any('SECRET' in c.args[0] for c in spy.call_args_list))
        points=b.occurrence_points(row,100)
        self.assertEqual([p['role'] for p in points],['carrier','candidate'])
        self.assertEqual(len(b.occurrence_points(row,110)),0)
    def test_syntax_and_duplicates(self):
        for text in ('{','{"x":NaN}','[] trailing','{"x":1,}'):
            with self.subTest(text=text),self.assertRaises(ValueError):b.View(text)
        with self.assertRaises(ValueError):b.View('{"x":1,"x":2}').fields()
    def test_count_gate(self):
        bcount=dict(zip(r.ALIASES,r.COUNTS));vcount=dict(zip(r.ALIASES,r.VIOLATIONS))
        r.validate_occurrence_counts(bcount,vcount)
        with self.assertRaises(ValueError):r.validate_occurrence_counts(bcount,{})
    def test_csv_projection_multiline_and_quoted(self):
        text='event_id,period,time_end,player_id,player_in_possession_id,player_targeted_id,pass_outcome\nother,1,0,p,p,SECRET,SECRET\ne,1,"00:00:01.0",p,p,"SECRET\nSECRET",SECRET\n'
        with patch.object(b,'decode_csv',wraps=b.decode_csv) as spy:
            out=b.exact_events(io.StringIO(text),{'e'})
            self.assertEqual(out['e']['player_id'],'p')
            self.assertFalse(any('SECRET' in c.args[0] for c in spy.call_args_list))
        with self.assertRaises(ValueError):b.exact_events(io.StringIO(text),{'missing'})
    def test_duplicate_event(self):
        text='event_id,period,time_end,player_id,player_in_possession_id\ne,1,0,p,p\ne,1,0,p,p\n'
        with self.assertRaises(ValueError):b.exact_events(io.StringIO(text),{'e'})
    def test_carrier_rules(self):
        self.assertEqual(b.carrier_reference({'player_id':'p','player_in_possession_id':'p'}),'p')
        self.assertEqual(b.carrier_reference({'player_id':'','player_in_possession_id':'p'}),'p')
        for event in ({},{'player_id':' p'},{'player_id':'a','player_in_possession_id':'b'}):
            with self.assertRaises(ValueError):b.carrier_reference(event)
    def test_metadata_selection(self):
        with patch.object(b.json,'loads',wraps=json.loads) as spy:
            out=b.metadata_projection(json.dumps(metadata()),{'carrier','p'})
            self.assertEqual(set(out['players']),{'carrier','p'})
            self.assertFalse(any('SECRET' in c.args[0] for c in spy.call_args_list))
        bad=metadata();bad['pitch_length']='100'
        with self.assertRaises(ValueError):b.metadata_projection(json.dumps(bad),{'p'})
    def test_tracking_projection_and_status(self):
        raw=tracking(10)
        with patch.object(b.json,'loads',wraps=json.loads) as spy:
            out=b.player_samples(json.dumps(raw),{'p'})
            self.assertEqual(out['p']['status'],'detected')
            self.assertFalse(any('SECRET' in c.args[0] for c in spy.call_args_list))
        for flag,status in [(False,'extrapolated'),(None,'unavailable')]:
            raw['player_data'][0]['is_detected']=flag
            self.assertEqual(b.player_samples(json.dumps(raw),{'p'})['p']['status'],status)
        for flag in (0,1,'false','True'):
            raw['player_data'][0]['is_detected']=flag
            with self.assertRaises(ValueError):b.player_samples(json.dumps(raw),{'p'})
    def test_missing_sample(self):
        self.assertEqual(b.player_samples(json.dumps(tracking(10)),{'absent'}),{})
        raw=tracking(10);raw['player_data'][0]['x']=None
        self.assertIsNone(b.player_samples(json.dumps(raw),{'p'})['p'])


class CoordinateTests(unittest.TestCase):
    def test_excess_and_sign(self):
        self.assertEqual(b.verify_point((-51,1),(51,1),-1,100),1)
        self.assertEqual(abs(-51),abs(51))
        with self.assertRaisesRegex(ValueError,'transformation_defect'):b.verify_point((51,1),(51,1),-1,100)
        with self.assertRaisesRegex(ValueError,'dimension_join_defect'):b.verify_point((51,1),(51,1),1,110)
    def test_time_and_neighbor_bounds(self):
        idx=[(i*100000,i,i) for i in range(7)]
        self.assertEqual(b.select_decision_frame(idx,300000),idx[2])
        self.assertIsNone(b.select_decision_frame(idx,800001))
        self.assertEqual(b.neighbors(idx,3),(1,2,3,4,5))
        self.assertEqual(b.neighbors(idx,0),(0,1,2))
        gap=[(0,0,0),(100000,1,1),(400000,2,2)]
        self.assertEqual(b.neighbors(gap,1),(0,1))
    def test_runs_missing_and_censoring(self):
        key=lambda i:('match',1,'player',i)
        samples={key(0):{'side':1},key(1):{'side':1},key(2):None,key(3):{'side':-1}}
        self.assertEqual(b.local_runs(samples,{key(0)}),{'observed_local_runs':2,'censored_runs':1,'single_observed_sample_runs':1})
    def test_index_only(self):
        raw='\n'.join(json.dumps(tracking(i)) for i in range(5))
        with patch.object(b.json,'loads',wraps=json.loads) as spy:
            idx=r.build_index(io.StringIO(raw))
            self.assertEqual(len(idx[1]),5)
            self.assertFalse(any('SECRET' in c.args[0] for c in spy.call_args_list))
        with self.assertRaises(ValueError):r.build_index(io.StringIO(json.dumps(tracking(1))+'\n'+json.dumps(tracking(1))))


class ExecutionTests(unittest.TestCase):
    def test_source_and_path_firewalls(self):
        for match in ('1953632','1874553','../escape',r.DEV[-1]):
            with self.assertRaises(PermissionError):r.product_path(match,'tracking')
        with self.assertRaises(PermissionError):r.product_path(r.DEV[0],'pose')
        with self.assertRaises(PermissionError):r.ObjectSource('unused').acquire(None)
        with self.assertRaises(PermissionError):r.ObjectSource('unused')._request('https://raw.githubusercontent.com/anything',label='x',maximum=1)
        with tempfile.TemporaryDirectory(dir=r.ROOT) as tmp,patch.object(r,'ROOT',Path(tmp)):
            (Path(tmp)/'link').symlink_to('/tmp')
            with self.assertRaises(PermissionError):r.safe(Path('link/value'))
            with self.assertRaises(PermissionError):r.safe(Path('../value'))
    def test_blob_hash(self):
        raw=b'synthetic';oid=git_blob_oid(raw);entry=TreeEntry('test','blob',oid,len(raw));env={'sha':oid,'size':len(raw),'encoding':'base64','content':base64.b64encode(raw).decode()}
        self.assertEqual(verify_blob(entry,env,decoded_limit=100),raw)
        with self.assertRaises(IntegrityError):verify_blob(entry,{**env,'size':2},decoded_limit=100)
    def test_exclusive_failure(self):
        with tempfile.TemporaryDirectory(dir=r.ROOT) as tmp,patch.object(r,'ROOT',Path(tmp)),patch.object(r,'git',return_value='test'):
            r.exclusive('review')
            with self.assertRaises(FileExistsError):r.exclusive('review')
            with patch.object(r,'ledger'),patch.object(r,'close') as close:
                r.failure('review',ValueError('transformation_defect'))
                self.assertEqual(r.load(r.OUT/'qc.json')['primary'],'C');close.assert_called_once_with('stopped')
    def test_no_model_routes(self):
        for path in (Path(r.__file__),Path(b.__file__)):
            tree=ast.parse(path.read_text())
            imports=[n.module or '' for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
            self.assertFalse(any(any(x in module for x in ('networks','choice_model','session5','ranking_features')) for module in imports))
        with self.assertRaises(ValueError):r.validate_occurrence_counts({}, {})
    def test_synthetic_recovery(self):
        with tempfile.TemporaryDirectory(dir=r.ROOT) as tmp,patch.object(r,'ROOT',Path(tmp)),patch.object(r,'ledger'):
            def write(product,value):
                p=r.safe(Path('data/session_02')/r.product_path(r.DEV[0],product));p.parent.mkdir(parents=True,exist_ok=True);p.write_text(value)
            write('metadata',json.dumps(metadata()))
            write('events','event_id,period,time_end,player_id,player_in_possession_id,pass_outcome,player_targeted_id\ne,1,00:00:01.1,carrier,carrier,SECRET,SECRET\n')
            write('tracking','\n'.join(json.dumps(tracking(i,51)) for i in range(8,14)))
            occ={'match':r.DEV[0],'event':'e','player':'p','xy':(51,1),'review_id':'synthetic','role':'candidate'}
            result,samples,edges,windows=r.recover_match(r.DEV[0],[occ],{'pitch_length':100,'pitch_width':60})
            self.assertEqual(result[0]['frame'],10);self.assertEqual(result[0]['excess'],1)
            self.assertEqual(len(result[0]['samples']),5)
            agg=r.aggregate(result,samples,edges,windows)
            self.assertEqual(agg['observed_local_runs'],1);self.assertEqual(agg['censored_runs'],1)
            with self.assertRaisesRegex(ValueError,'dimension_join_defect'):r.recover_match(r.DEV[0],[occ],{'pitch_length':101,'pitch_width':60})
