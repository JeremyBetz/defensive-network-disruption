"""Synthetic runner boundaries, retained receipts and persisted-only publication."""
from dataclasses import asdict, replace
from fractions import Fraction as F
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
import numpy as np
from defensive_network_disruption.validation import r9t_acceptance as a,r9t_evidence as e,r9t_authority as authority
from defensive_network_disruption.validation import r9s_authority as old_authority,r9s_acceptance as capture
from defensive_network_disruption.geometry import r9t_transition as t,r9t_adapter as adapter,r9s_trace
from defensive_network_disruption.validation.r9j_evidence import load,sha
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('r9t_runner',ROOT/'scripts/session_14r9t_binary64_transition_contract_repair.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)


def blocked_history(root,sink,**kw):
    label,case=a.historical_cases(root)[0];old={'synthetic':'blocked'}
    detail=dict(old=old,baseline=old,new=None,expected=a.primitive(case['historical_vector']),localizations=[])
    h=sink('historical_0',detail)
    return [dict(fixture=label,candidate=case['candidate'],status='blocked',components=len(case['historical_vector']['estimates']),permutations=0,structure_exact=False,production_preserved=False,verification_preserved=False,reason='VerificationError',evidence_sha256=h)]


def blocked(folder):
    with patch.object(r,'preflight',return_value={'synthetic':True}),patch.object(a,'historical_regression',side_effect=blocked_history),patch.object(r,'trace_review',side_effect=AssertionError('retained_forbidden')):
        return r.audit(folder)


def synthetic_records():
    mid=t.old._bits(.5);lo,hi=.4,.6;root=(F.from_float(t.old._float(mid-16)),F.from_float(t.old._float(mid+16)))
    top=t.classify(a.Linear(F(1,2)),F.from_float(lo),F.from_float(hi),deadline=time.monotonic()+5)
    proposal=dict(location=.5,crossing_pairs=[[0,1]])
    values=dict(raw=dict(onsets=[],envelope=dict(switches=[proposal],tie_intervals=[])),
        region=dict(raw_proposal=proposal,constrained_region=[lo,hi],structural_neighbors=[0.,1.]),
        pair={},topology=top,root=root,work=dict(floats_inspected=65))
    records={k:dict(kind=old_authority.KINDS[k],value=a.primitive(v)) for k,v in values.items()}
    bound=lambda x,y:dict(lower=a.primitive(F(x)),upper=a.primitive(F(y)))
    records['excluded']=dict(left=a.primitive(F(1,10)),right=a.primitive(F(1,5)),difference=bound(1,2),status='signed')
    records['receipt']=dict(selected_sha256='synthetic_selected',attempt_sha256='synthetic_attempt')
    records['lineage']=dict(review_sha256='synthetic_review')
    sources=dict(old_authority.SOURCES)
    for k in ('selected','attempt','review'):sources[k]=('synthetic','synthetic','synthetic_'+k)
    with patch.object(old_authority,'SOURCES',sources):args,ref,structures=old_authority.context(records)
    def function(ts):
        values=[]
        for x in ts:
            k=t.old._bits(float(x))-mid
            values.append(-1. if k<0 else 1. if k==0 else 0. if k==1 else -1. if k==2 else 1.)
        return np.column_stack((values,np.zeros_like(ts)))
    trace,error,_=capture.collect(function,(0,1),*root,lo,hi,-1,1,ref,structures,lambda *_:None,engineering=True)
    return trace,records,sources


class AuthorityTests(unittest.TestCase):
    def test_saved_65_trace_pure_resolution_and_overlap(self):
        trace,records,sources=synthetic_records()
        with patch.object(old_authority,'SOURCES',sources),patch.object(t.old,'_pair',side_effect=AssertionError('new_probe')),patch.object(t.PairAuthority,'bounds',side_effect=AssertionError('new_math')):
            result=authority.resolve_saved(trace,records)
        self.assertEqual(len(result.probes),65);self.assertGreaterEqual(result.suffix_length,2)
        self.assertEqual(result.transition.first_post,t.old._float(t.old._bits(.5)+3))

    def test_changed_saved_trace_and_missing_proof_block(self):
        trace,records,sources=synthetic_records()
        for kind in ('count','cache','proof'):
            bad=copy.deepcopy(trace);rec=copy.deepcopy(records)
            if kind=='count':bad['probes'].pop()
            elif kind=='cache':bad['final']['cache'][0][1]=1
            else:rec['topology']['value']['complete']=False
            with patch.object(old_authority,'SOURCES',sources),self.assertRaises(ValueError):authority.resolve_saved(bad,rec)

    def test_direct_entry_rejects(self):
        with tempfile.TemporaryDirectory() as d:
            for fn in (r.selected,r.trace_review):
                with self.assertRaises(PermissionError):fn(Path(d),None)
            with self.assertRaises(PermissionError):r.Permit(object())
            with self.assertRaises(PermissionError):r.unlock({}, {n:[] for n in e.COLUMNS},{'flags':{}})

    def test_selected_receipt_and_interruption(self):
        for interrupt in (False,True):
            with tempfile.TemporaryDirectory() as d:
                root=Path(d).resolve();local=root/'new';source=root/'synthetic';r.put(source/'retained/selected.json',dict(alias='synthetic',carrier=[0.,0.],receiver=[10.,0.],defenders=[[2.,1.]]))
                r.put(local/'retained_bindings.json',{'retained/selected.json':sha(source/'retained/selected.json')})
                put=r.put
                def write(path,v):
                    if interrupt and path.name=='access_materialized.json':raise OSError('receipt_interrupted')
                    put(path,v)
                with patch.object(r,'ROOT',root),patch.object(authority,'SOURCE','synthetic'),patch.object(r,'put',side_effect=write):
                    if interrupt:
                        with self.assertRaises(OSError):r.selected(local,r.Permit(r._SEAL))
                    else:self.assertEqual(r.selected(local,r.Permit(r._SEAL))['alias'],'synthetic')
                self.assertTrue((local/'access_attempt.json').exists());self.assertEqual((local/'access_materialized.json').exists(),not interrupt)


class RunnerTests(unittest.TestCase):
    def test_complete_blocked_package_rerun_and_zero_access(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d).resolve();result=blocked(folder)
            self.assertEqual((result['classification'],result['readiness']),("C",3));self.assertEqual(result['edges_reopened'],0)
            self.assertEqual(set(p.name for p in folder.iterdir() if p.is_file()),set(e.NAMES))
            with patch.object(r,'preflight',return_value={'synthetic':True}),self.assertRaises(FileExistsError):r.audit(folder)

    def test_tampered_hash_and_forged_decision(self):
        for name in ('qc.json','local/outcome.json','local/synthetic_trace_controls.csv.json'):
            with tempfile.TemporaryDirectory() as d:
                folder=Path(d).resolve();blocked(folder);(folder/name).write_text('{}')
                with self.assertRaises(ValueError):e.publication_check(folder)
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d).resolve();blocked(folder);q=load(folder/'qc.json');q['data']['classification']='A';q['data']['readiness']=1
            (folder/'qc.json').write_bytes(e.canonical(q));m=load(folder/'manifest.json');m['outputs']['qc.json']=sha(folder/'qc.json');(folder/'manifest.json').write_bytes(e.canonical(m))
            with self.assertRaisesRegex(ValueError,'false_decision'):e.publication_check(folder)

    def test_checking_has_no_numerical_or_replay_route(self):
        from defensive_network_disruption.validation import r9j_linear_publication as linear
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d).resolve();blocked(folder)
            with patch.object(linear,'review',side_effect=AssertionError('replay')),patch.object(adapter,'evaluate',side_effect=AssertionError('field')),patch.object(r,'selected',side_effect=AssertionError('geometry')):
                self.assertTrue(e.publication_check(folder)['valid'])

    def test_timeout_before_access_preserves_original(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d).resolve()
            with patch.object(r,'preflight',return_value={'synthetic':True}),patch.object(a,'historical_regression',side_effect=TimeoutError('synthetic_timeout')),patch.object(r,'trace_review',side_effect=AssertionError('forbidden')):
                result=r.audit(folder)
            self.assertEqual(result['classification'],'E');self.assertTrue((folder/'local/outer_failure/numerical_traceback.txt').exists())

    def test_publication_controls(self):
        with tempfile.TemporaryDirectory() as d:
            rows,summary=r.publication_controls(Path(d).resolve())
            self.assertEqual(len(rows),5);self.assertTrue(all(summary['flags'].values()))

    def test_actual_candidate_entry_success_failure_and_uncertainty(self):
        from defensive_network_disruption.validation import r9j_linear_publication as linear,numerical_failure_publication as legacy
        resolution=t.canonicalize(*a.fixture())
        row=dict(alias='synthetic_only',carrier=[0.,0.],receiver=[20.,0.],defenders=[[8.,2.]])
        real=adapter.evaluate
        for mode in ('success','numerical_failure','receipt_failure'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as d:
                local=Path(d).resolve()
                def selected(*_):
                    r.put(local/'access_attempt.json',{'synthetic':True})
                    if mode=='receipt_failure':raise OSError('receipt_interrupted')
                    r.put(local/'selected_geometry.json',row);r.put(local/'access_materialized.json',{'synthetic':True});return row
                def evaluate(*args,**kw):
                    if mode=='numerical_failure':kw['record'](stage='geometry');raise t.VerificationError('synthetic_numerical')
                    # Isolated boundary-control observation, explicitly engineering.
                    kw['localization_sink'](kind='transition_evidence',value=asdict(resolution))
                    return real(*args,**kw)
                with patch.object(r,'selected',side_effect=selected),patch.object(old_authority,'geometry_match'),patch.object(adapter,'evaluate',side_effect=evaluate),patch.object(legacy,'replay',side_effect=AssertionError('legacy')),patch.object(linear,'review',wraps=linear.review) as review:
                    if mode=='success':r.retained_candidate(local,r.Permit(r._SEAL),resolution,{},lambda *_:None,time.monotonic()+30)
                    else:
                        with self.assertRaises((ValueError,OSError)):r.retained_candidate(local,r.Permit(r._SEAL),resolution,{},lambda *_:None,time.monotonic()+30)
                self.assertEqual(review.call_count,1)
                closure=e.check_closure(local);self.assertEqual(closure['legacy']['snapshot']['diagnostic_success'],mode=='success')
                if mode=='receipt_failure':self.assertEqual(closure['exposure']['unresolved_projection_attempts'],1)
                self.assertEqual(closure['exposure']['field_evaluations_completed'],0)

    def test_trace_only_block_has_zero_geometry_and_one_review(self):
        from defensive_network_disruption.validation import r9j_linear_publication as linear
        with tempfile.TemporaryDirectory() as d:
            local=Path(d).resolve()
            with patch.object(linear,'review',wraps=linear.review) as review:
                try:raise t.VerificationError('transition_suffix_too_short')
                except t.VerificationError as error:r.close_trace_block(local,error)
            self.assertEqual(review.call_count,1);receipt=e.check_closure(local)
            self.assertEqual(receipt['exposure']['states_opened'],0)
            self.assertEqual(receipt['exposure']['edges_opened'],0)
            self.assertFalse((local/'access_attempt.json').exists())

    def test_marker_nonfinite_and_interrupted_write(self):
        with self.assertRaises(ValueError):r.canonical({'value':float('nan')})
        with tempfile.TemporaryDirectory() as d:
            p=Path(d).resolve();r.put(p/'acceptance.marker',{})
            with self.assertRaises(FileExistsError):r.put(p/'acceptance.marker',{})
            (p/'.broken.pending').write_text('partial')
            with self.assertRaises(FileExistsError):r.write(p/'broken',b'data')

    def test_preflight_stops_dirty_before_receipt_or_access(self):
        with patch.object(r,'git',return_value='dirty'),patch.object(authority,'verify_sources',side_effect=AssertionError('retained')):
            with self.assertRaisesRegex(RuntimeError,'dirty_tree'):r.preflight()

    def test_startup_import_failure_bound_without_package(self):
        import builtins
        original=builtins.__import__
        def importing(name,*args,**kw):
            if name.startswith('defensive_network_disruption'):raise ImportError('synthetic_dependency')
            return original(name,*args,**kw)
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d).resolve()
            with patch.object(r,'OUT',folder),patch.object(r,'audit',side_effect=ImportError('synthetic_dependency')),patch('sys.argv',['runner','audit']),patch.object(builtins,'__import__',side_effect=importing):
                with self.assertRaises(ImportError):r.main()
            f=load(folder/'local/outer_failure.json');self.assertEqual(f['traceback_sha256'],sha(folder/'local/outer_traceback.txt'))

    def test_bound_history_unchanged(self):
        for name,h in r.bindings().items():self.assertEqual(sha(ROOT/name),h,name)

if __name__=='__main__':unittest.main()
