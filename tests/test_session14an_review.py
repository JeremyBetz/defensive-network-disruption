"""Fabricated evidence-only tests; no geometry or numerical algorithms."""
import ast
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('review_runner',ROOT/'scripts/session_14an_retained_evidence_adjudication.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r);v=r.v

class ReviewTests(unittest.TestCase):
    def test_projection_forbidden_values_never_decoded(self):
        p=v.Projection('{"geometry":{"x":12},"root":0.25,"owner":7,"keep":3}',('keep',))
        self.assertEqual(p.run(),{'keep':3});self.assertEqual(p.decoded,[('keep',)])
    def test_array_projection(self):
        p=v.Projection('{"adaptive_returns":[{"a":0.2,"b":0.8,"estimate":0.4,"reported_error":0.0}]}',v.PRIVATE['reproduction'])
        self.assertEqual(p.run(),{'adaptive_returns':[{'estimate':0.4,'reported_error':0.0}]})
        self.assertFalse(any(x[-1] in ('a','b') for x in p.decoded))
    def test_exact_float_and_signed_zero(self):
        p=v.Projection('{"estimate":-0.0}',('estimate',));self.assertEqual(v.canonical(p.run()),b'{"estimate":-0.0}\n')
    def test_missing_fields_not_invented(self):
        self.assertEqual(v.Projection('{"other":2}',('estimate',)).run(),{})
    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):v.Projection('{"x":1,"x":2}',('x',)).run()
    def test_nonfinite_rejected(self):
        for text in ('{"x":NaN}','{"x":1e999}','{"x":Infinity}'):
            with self.assertRaises(ValueError):v.Projection(text,('x',)).run()
    def test_private_labels(self):
        for n in ('000001_selected_geometry.json','../000001_strict.json','000001_structure.json','000001_onset_neighborhood.json','prepared.jsonl'):
            self.assertIsNone(v.select_label(n))
        self.assertEqual(v.select_label('000010_strict.json'),'strict')
    def test_path_guard(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(PermissionError):v.read_selected(Path(d).resolve(),'../x','x')
    def test_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d).resolve();(p/'real').write_text('x');(p/'link').symlink_to(p/'real')
            with self.assertRaises(PermissionError):v.sha(p/'link')
    def test_hash_before_projection(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d).resolve();(p/'000001_strict.json').write_text('{"lower":1}')
            with self.assertRaises(ValueError):v.read_selected(p,'000001_strict.json','0'*64)
    def test_create_once_and_marker(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d).resolve()/'attempt.marker';v.atomic(p,{'once':True})
            with self.assertRaises(FileExistsError):v.atomic(p,{'once':False})
            self.assertEqual(v.load(p),{'once':True})
    def test_classification_missing(self):self.assertEqual(v.classify(dict.fromkeys('ABCDEF')),('H',4))
    def test_multiple_mechanisms(self):
        m=dict.fromkeys('ABCDEF');m.update(A=True,B=True);self.assertEqual(v.classify(m),('G',2))
    def test_classification_types(self):
        with self.assertRaises(ValueError):v.classify(dict.fromkeys('ABCDEF',1))
    def test_missing_evidence_review(self):
        records,n,ready,p=r.adjudicate({},{});self.assertEqual((n,ready,p),('H',4,'P5'))
        self.assertIsNone(records['onset_only_health.json']['checks']['independent_accuracy_established'])
    def test_disagreement_not_cause(self):
        public={'production_path.json':{'data':{'checks':{'unsplit_reference':False}}}}
        records,n,ready,_=r.adjudicate(public,{})
        self.assertEqual((n,ready),('H',4));self.assertTrue(records['onset_only_health.json']['checks']['reference_disagreement'])
    def test_reference_cannot_bootstrap(self):
        p={'production_path.json':{'data':{'checks':{'reference_eligible':True,'piecewise_reference':True}}}}
        result=r.adjudicate(p,{})[0];self.assertIsNone(result['reference_eligibility.json']['checks']['eligible'])
    def test_reference_retained_step(self):
        p={'partition_audit.json':{'data':{'passed':True}}}
        result=r.adjudicate(p,{'piecewise':[{'intervals':16384,'successive_difference':0.0}]})[0]
        self.assertTrue(result['reference_eligibility.json']['checks']['eligible'])
    def package(self,p,valid=True):
        rec,*_=r.adjudicate({},{});return r.close(p,rec,[],[],{},None,valid)
    def test_valid_unresolved_package(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d).resolve();self.package(p);self.assertTrue(v.validate(p))
    def test_invalid_execution_package(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d).resolve();self.package(p,False);self.assertFalse(v.load(p/'qc.json')['execution_valid'])
    def test_changed_hash(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d).resolve();self.package(p);(p/'production_health.json').write_text('{}')
            with self.assertRaises(ValueError):v.validate(p)
    def test_missing_output(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d).resolve();self.package(p);(p/'production_health.json').unlink()
            with self.assertRaises(FileNotFoundError):v.validate(p)
    def test_false_acceptance_rebound_hash(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d).resolve();self.package(p);q=v.load(p/'qc.json');q['combined_repair']=True;(p/'qc.json').write_bytes(v.canonical(q))
            m=v.load(p/'manifest.json');m['outputs']['qc.json']=v.sha(p/'qc.json');(p/'manifest.json').write_bytes(v.canonical(m))
            with self.assertRaises(ValueError):v.validate(p)
    def test_no_numerical_import_route(self):
        for path in (r.MODULE,ROOT/'scripts/session_14an_retained_evidence_adjudication.py'):
            tree=ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node,(ast.Import,ast.ImportFrom)):
                    names=[x.name for x in node.names] if isinstance(node,ast.Import) else [node.module or '']
                    self.assertFalse(any(n.startswith(('numpy','scipy','defensive_network_disruption')) for n in names))
    def test_deterministic_serialization(self):
        self.assertEqual(v.canonical({'b':1,'a':2}),v.canonical({'a':2,'b':1}))
    def test_failure_preserved_independently(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d).resolve()/'failure.json';v.atomic(p,{'exception':'SyntheticFailure','accepted':False})
            with self.assertRaises(FileExistsError):v.atomic(p,{'accepted':True})
            self.assertFalse(v.load(p)['accepted'])
    def test_all_classification_branches(self):
        for k in 'ABCDEF':
            m=dict.fromkeys('ABCDEF');m[k]=True;self.assertEqual(v.classify(m)[0],k)
    def test_csv_lf(self):self.assertNotIn(b'\r',v.csv_bytes([]))

if __name__=='__main__':unittest.main()
