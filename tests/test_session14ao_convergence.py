"""Frozen provider-free instrumentation and fabricated publication controls."""
import ast
import copy
import importlib.util
import math
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
import numpy as np
from defensive_network_disruption.geometry import onset_convergence as d
from defensive_network_disruption.validation import retained_evidence_review as v
from defensive_network_disruption.validation.r5_persistence import Journal,read_journal

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('session14ao',ROOT/'scripts/session_14ao_onset_only_adaptive_convergence.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)

class ConvergenceTests(unittest.TestCase):
    def test_observational_controls(self):self.assertTrue(all(x['passed'] for x in d.synthetic_controls()))
    def test_candidate_guard(self):
        for args in ((4,8,'constant_width'),(3,7,'constant_width'),(4,7,'expanding'),(True,7,'constant_width')):
            with self.assertRaises(PermissionError):d.guard(*args)
        d.guard(4,7,'constant_width')
    def test_sequence(self):self.assertEqual(d.TOLERANCES,(1e-13,5e-14,2e-14,1e-14,5e-15,2e-15))
    def test_quad_counters(self):
        p=d.diagnostic_piece(lambda t:t[:,None]**3,0.,1.,1e-13)
        self.assertEqual(p['neval'],len(p['trace']));self.assertEqual(len(p['alist']),p['last']);self.assertTrue(p['normal'])
    def test_initialized_arrays_only(self):
        fake=dict(neval=0,last=1,alist=np.array([0.,np.nan]),blist=np.array([1.,np.nan]),rlist=np.array([.5,np.nan]),elist=np.array([0.,np.nan]))
        with patch.object(d,'quad',return_value=(.5,0.,fake)):
            p=d.diagnostic_piece(lambda t:t[:,None],0.,1.,1e-13)
        self.assertEqual(p['alist'],[0.])
    def test_warning_message_blocks(self):
        p=d.diagnostic_piece(lambda t:abs(t-.371)[:,None],0.,1.,1e-13,limit=1)
        self.assertFalse(p['normal']);self.assertTrue(p['warnings']);self.assertTrue(p['exhausted'])
    def test_partial_warning_level(self):
        p=d.diagnostic_piece(lambda t:abs(t-.371)[:,None],0.,1.,1e-13,limit=1)
        with patch.object(d,'diagnostic_piece',return_value=p):
            x=d.run_level(lambda t:t[:,None],(0.,.5,1.),1e-13,d.Budget(),lambda *_:None)
        self.assertFalse(x['complete']);self.assertEqual(x['pieces_attempted'],1)
    def test_timeout(self):
        with self.assertRaises(d.DiagnosticTimeout):
            with d.Budget(total=.02,level=.01).operation():time.sleep(.03)
    def test_timeout_preserves_trace(self):
        def f(t):raise d.DiagnosticTimeout('fabricated')
        with self.assertRaises(d.DiagnosticTimeout) as caught:d.diagnostic_piece(f,0.,1.,1e-13)
        self.assertEqual(caught.exception.diagnostic_piece['exception'],'DiagnosticTimeout')
    def test_partial_level_preserved(self):
        p=d.diagnostic_piece(lambda t:t[:,None],0.,.5,1e-13)
        with patch.object(d,'diagnostic_piece',side_effect=[p,d.DiagnosticTimeout('fabricated')]):
            with self.assertRaises(d.DiagnosticTimeout) as caught:d.run_level(lambda t:t[:,None],(0.,.5,1.),1e-13,d.Budget(),lambda *_:None)
        self.assertEqual(caught.exception.level_partial['pieces_attempted'],1)
    def test_nonfinite_stops(self):
        with self.assertRaises(ValueError):d.diagnostic_piece(lambda t:np.full((1,1),np.nan),0.,1.,1e-13)
    def test_deterministic_trace(self):
        a=d.diagnostic_piece(lambda t:t[:,None],0.,1.,1e-13);b=d.diagnostic_piece(lambda t:t[:,None],0.,1.,1e-13)
        self.assertEqual(a['trace_sha256'],b['trace_sha256'])
    def levels(self,values,work=True):
        return [dict(tolerance=t,complete=True,normal=True,warnings=False,exhausted=False,estimate=x,neval=21+i if work else 21,subdivisions=i if work else 0,trace_sha256=str(i) if work else 'same') for i,(t,x) in enumerate(zip(d.TOLERANCES,values))]
    def test_A_recovered(self):self.assertEqual(d.classify(self.levels([1e-8,1e-9,1e-10,1e-11,0.,0.]),0.)[:2],('A',1))
    def test_A_late_drift(self):self.assertEqual(d.classify(self.levels([1e-6,8e-7,6e-7,4e-7,2e-7,1e-7]),0.)[0],'A')
    def test_B_qualified(self):self.assertEqual(d.classify(self.levels([1e-8]*6),0.)[:2],('B',4))
    def test_same_trace_not_B(self):self.assertEqual(d.classify(self.levels([1e-8]*6,False),0.)[:2],('H',4))
    def test_warning_not_A(self):
        x=self.levels([1e-8,1e-9,1e-10,1e-11,0.,0.]);x[-1]['warnings']=True;self.assertEqual(d.classify(x,0.)[0],'H')
    def test_missing_level_H(self):self.assertEqual(d.classify(self.levels([1e-8]*6)[:-1],0.)[0],'H')
    def test_authority_invalid_D(self):self.assertEqual(d.classify([],0.,authority_invalid=True)[:2],('D',3))
    def test_comparisons_separate(self):
        a=self.levels([2e-10]*6)[0];x=d.compare(a,None,0.,(1.9e-10,2.1e-10),2e-10)
        self.assertFalse(x['reference_within_gate']);self.assertTrue(x['piecewise_within_gate'])
    def test_relative_zero_unavailable(self):self.assertIsNone(d.compare(self.levels([0.]*6)[0],None,0.,(0.,0.),0.)['relative_error'])
    def test_onset_localization(self):
        x=d.run_level(lambda t:np.ones((len(t),1)),(0.,.25,1.),1e-13,d.Budget(),lambda *_:None)
        self.assertEqual(x['onset_adjacent_panels'],2);self.assertEqual(x['subdivisions'],0)
    def test_forbidden_receiver_sentinel(self):
        from defensive_network_disruption.data.representation_projection import ALIASES
        text='{"alias":'+__import__('json').dumps(ALIASES[0])+',"carrier":[0,0],"receivers":["FORBIDDEN",[20,0]],"defenders":[[5,2]]}'
        x=r.project_prepared_edge(text,1);self.assertEqual(x['receiver'],(20.,0.))
    def test_onset_projection_skips_owners(self):
        p=v.Projection('{"onsets":[{"type":"certified_onset","first_post_branch":0.2,"defender_index":7}],"switches":[{"owner":42}]}',('onsets.*.type','onsets.*.first_post_branch'))
        x=p.run();self.assertNotIn('switches',x);self.assertFalse(any('defender_index' in key for key in p.decoded))
    def test_receipt_before_attempt_rejected(self):
        records=[dict(action='authorized',payload=dict(state=4,edge=7,candidate='constant_width')),dict(action='access_materialized',payload=dict(product='prepared',state=4,edge=7,candidate='constant_width'))]
        with self.assertRaises(ValueError):r.access_summary(records)
    def test_diagnostic_before_access_rejected(self):
        with self.assertRaises(ValueError):r.access_summary([dict(action='level_started',payload=dict(level=0,tolerance=1e-13))])
    def test_immutable_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp).resolve()/'attempt.marker';r.put(p,{'one':True})
            with self.assertRaises(FileExistsError):r.put(p,{'one':False})
    def test_interrupted_journal(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp).resolve()/'j';j=Journal(p);j.append('authorized',state=4,edge=7,candidate='constant_width');j.close()
            with p.open('ab') as f:f.write(b'{')
            with self.assertRaises(ValueError):read_journal(p)
    def test_uncertain_materialization(self):
        x=r.access_summary([dict(action='authorized',payload=dict(state=4,edge=7,candidate='constant_width')),dict(action='access_attempt',payload=dict(product='prepared',state=4,edge=7,candidate='constant_width'))]);self.assertTrue(x['uncertain']);self.assertEqual(x['edges_opened'],0)
    def test_unique_edge_two_receipts(self):
        rows=[dict(action='authorized',payload=dict(state=4,edge=7,candidate='constant_width'))]
        for product in ('canonical','prepared'):
            for action in ('access_attempt','access_materialized'):rows.append(dict(action=action,payload=dict(product=product,state=4,edge=7,candidate='constant_width')))
        self.assertEqual(r.access_summary(rows),dict(states_opened=1,edges_opened=1,uncertain=False))
    def package(self,p,complete=False):
        e=r.Evidence(p/'local');j=Journal(p/'local/journal.jsonl');j.append('authorized',state=4,edge=7,candidate='constant_width')
        if complete:
            for product in ('canonical','prepared'):
                j.append('access_attempt',product=product,state=4,edge=7,candidate='constant_width')
                j.append('access_materialized',product=product,state=4,edge=7,candidate='constant_width')
            for i,tol in enumerate(d.TOLERANCES):
                j.append('level_started',level=i,tolerance=tol)
                j.append('level_finished',level=i,complete=True,warning=False,exhausted=False)
        j.close();_,head=read_journal(p/'local/journal.jsonl');e.files['journal.jsonl']=v.sha(p/'local/journal.jsonl')
        levels=[];hashes=[];comps=[]
        if complete:
            e.save('reference',dict(reference=0.,anchor=1e-8,bounds=(0.,0.)))
            for i,x in enumerate(self.levels([1e-8]*6)):
                x.update(terminal_panels=i+1,onset_adjacent_panels=0,onset_error_fraction=None,reported_error=0.,reported_bounds_met=True,seconds=.01,pieces_attempted=1,pieces_required=1)
                levels.append(x);hashes.append(e.save('level',x));comps.append(d.compare(x,levels[-2] if len(levels)>1 else None,0.,(0.,0.),1e-8))
        retained=dict(reference_eligible=True,selected_serialization_verified=complete,onset_count=0,input_hashes={},retained_hashes={})
        return r.close(p,e,levels,hashes,comps,{},retained,0.,True,None,False,True,head,dict(states_opened=int(complete),edges_opened=int(complete),uncertain=False))
    def test_partial_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp).resolve();self.package(p);self.assertTrue(r.publication_check(p))
    def test_complete_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp).resolve();q=self.package(p,True);self.assertEqual(q['classification'],'B');self.assertTrue(r.publication_check(p))
    def test_missing_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp).resolve();self.package(p);(p/'reference_comparison.csv').unlink()
            with self.assertRaises(FileNotFoundError):r.publication_check(p)
    def test_changed_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp).resolve();self.package(p);(p/'classification.json').write_text('{}')
            with self.assertRaises(ValueError):r.publication_check(p)
    def test_false_A(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp).resolve();self.package(p,True)
            for name in ('classification.json','qc.json'):
                x=v.load(p/name);x.update(classification='A',readiness=1);(p/name).write_bytes(v.canonical(x))
            m=v.load(p/'manifest.json');m['outputs'].update({n:v.sha(p/n) for n in ('classification.json','qc.json')});(p/'manifest.json').write_bytes(v.canonical(m))
            with self.assertRaises(ValueError):r.publication_check(p)
    def test_serialization_rejects_object(self):
        with self.assertRaises(TypeError):r.project_evidence({'unsupported':object()})
    def test_no_forbidden_execution_calls(self):
        tree=ast.parse((ROOT/'scripts/session_14ao_onset_only_adaptive_convergence.py').read_text())
        forbidden={'evaluate_edge','controlled_vector','canonical_geometry','independent_maximum','replay','scalar_oracle','maximum_simpson'}
        calls={n.func.attr for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)}
        self.assertFalse(calls&forbidden)

if __name__=='__main__':unittest.main()
