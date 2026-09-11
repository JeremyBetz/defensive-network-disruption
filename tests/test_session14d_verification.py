"""Synthetic software checks for the isolated 14d audit instruments."""
import ast
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from defensive_network_disruption.geometry.verification_audit import (
    controlled_vector, scalar_oracle, complete_signature, historical_decision_function)
from defensive_network_disruption.geometry.maximum_envelope import (
    EnvelopeSwitch, SwitchResult, TieInterval)

PATH=Path(__file__).resolve().parents[1]/'scripts/session_14d_verification_audit.py'
spec=importlib.util.spec_from_file_location('runner14d_tests',PATH)
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)


class AuditTests(unittest.TestCase):
    def test_joint_rule_waits_for_all_components(self):
        calls=[]
        def estimates(n):
            calls.append(n)
            return {'individual': 1.0 if n==256 else 0.5, 'maximum':0.25}
        n, values, diff=controlled_vector(estimates)
        self.assertEqual(n,1024);self.assertEqual(calls,[256,512,1024])
        self.assertEqual(diff,0.);self.assertEqual(values['individual'],.5)

    def test_joint_cap_and_bad_vectors(self):
        n,_,_=controlled_vector(lambda n:{'a':1./n})
        self.assertIsNone(n)
        for bad in (float('nan'),float('inf')):
            with self.assertRaises(ValueError):controlled_vector(lambda n:{'a':bad})
        with self.assertRaises(ValueError):
            controlled_vector(lambda n:{'a' if n==256 else 'b':1.})

    def test_independent_axial_oracles(self):
        for candidate in ('expanding','constant_width'):
            self.assertEqual(scalar_oracle(candidate,(0,0),(5,0),(5,0)),0.)
            self.assertEqual(scalar_oracle(candidate,(0,0),(5,0),(5.5,0)),.5)
            self.assertEqual(scalar_oracle(candidate,(0,0),(5,0),(6,0)),1.)
        self.assertEqual(scalar_oracle('isotropic',(0,0),(5,0),(5,0)),1.)

    def test_full_signature_includes_ties_and_pairs(self):
        s=EnvelopeSwitch(.5,(0,),(0,1),(1,),((0,1),),False,False,.7)
        original=SwitchResult((s,),(TieInterval(.6,.7,(0,1)),),(0,1),65536)
        reverse=SwitchResult((EnvelopeSwitch(.5,(1,),(1,0),(0,),((1,0),),False,False,.7),),
                              (TieInterval(.6,.7,(1,0)),),(1,0),65536)
        self.assertEqual(complete_signature(original,(0,1)),complete_signature(reverse,(1,0)))
        changed=SwitchResult((s,),(TieInterval(.6,.71,(0,1)),),(0,1),65536)
        self.assertNotEqual(complete_signature(original,(0,1)),complete_signature(changed,(0,1)))

    def test_ast_harness_extracts_actual_statements_without_runner(self):
        source='''
def review():
    raise RuntimeError('must never run')
    unresolved = case_rows
    classification = 'A' if deterministic else 'F'
    maximum_decision = '1'
    readiness = '1' if permutation_stable else '3'
    grouped = []
'''
        function=historical_decision_function(source)
        self.assertEqual(function([],[],False,False),('F','1','3'))

    def test_safe_symlink_and_path_rejection(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(r,'ROOT',Path(tmp).resolve()):
            (Path(tmp)/'link').symlink_to('/tmp')
            for path in ('../outside','/tmp/outside','link/outside'):
                with self.assertRaises(ValueError):r.safe(path)
            with self.assertRaises(ValueError):r.load('unapproved.json')

    def test_marker_and_existing_artifact_prevent_rerun(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(r,'ROOT',Path(tmp).resolve()), \
             patch.object(r,'git',return_value=''),patch.object(r,'ledger'):
            r.begin()
            with self.assertRaises(FileExistsError):r.begin()
            self.assertTrue(r.safe(r.OUT/'local/execution.marker').exists())

    def test_dirty_state_blocked(self):
        with patch.object(r,'git',return_value=' M something'):
            with self.assertRaisesRegex(ValueError,'clean_tree'):r.begin()

    def test_output_immutability_and_json_boundary(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(r,'ROOT',Path(tmp).resolve()):
            r.atomic(r.OUT/'test.json','{}')
            with self.assertRaises(FileExistsError):r.atomic(r.OUT/'test.json','{changed}')
            with self.assertRaises(ValueError):r.atomic('outside.json','{}')
            with self.assertRaises(ValueError):r.put_json('qc.json',{'unexpected':1})
            r.atomic(r.OUT/'duplicate.json','{"a":1,"a":2}')
            with self.assertRaises(ValueError):r.load(r.OUT/'duplicate.json')
            r.atomic(r.OUT/'nonfinite.json','{"a":NaN}')
            with self.assertRaises(ValueError):r.load(r.OUT/'nonfinite.json')

    def test_failure_preserves_marker_record_and_blocks_second_attempt(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(r,'ROOT',Path(tmp).resolve()), \
             patch.object(r,'preflight'),patch.object(r,'ledger'),patch.object(r,'git',return_value=''), \
             patch.object(r,'digest',return_value='hash'),patch.object(r,'environment',return_value={}), \
             patch.object(r,'perform',side_effect=RuntimeError('injected')):
            with self.assertRaisesRegex(RuntimeError,'audit_invalid_preserved'):r.audit()
            self.assertEqual(r.load(r.OUT/'manifest.json')['status'],'closed_invalid')
            self.assertEqual(r.load(r.OUT/'qc.json')['result'],'INVALID — Audit execution failure')
            with self.assertRaises(FileExistsError):r.audit()

    def test_closed_success_and_publication_tamper(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(r,'ROOT',Path(tmp).resolve()), \
             patch.object(r,'preflight'),patch.object(r,'history'),patch.object(r,'ledger'), \
             patch.object(r,'git',return_value=''),patch.object(r,'digest',return_value='hash'), \
             patch.object(r,'environment',return_value={}),patch.object(r,'validate'):
            def fake_perform():
                r.put_json('qc.json',{'schema_version':1,'status':'complete','result':'PASS',
                                     'cases':108,'components':366,'empirical_access':False,'models_loaded':0,'error':None})
            with patch.object(r,'perform',side_effect=fake_perform):r.audit()
            self.assertEqual(r.load(r.OUT/'manifest.json')['status'],'closed')
            r.publication_check()
            m=r.load(r.OUT/'manifest.json');m['outputs']['qc.json']='tampered'
            r.safe(r.OUT/'manifest.json').write_text(json.dumps(m))
            with self.assertRaisesRegex(ValueError,'output_hash'):r.publication_check()

    def test_no_empirical_routes(self):
        r.routes()
        tree=ast.parse(PATH.read_text())
        self.assertFalse({n.id for n in ast.walk(tree) if isinstance(n,ast.Name)} &
                         {'evaluate_options','FrozenOptionModel','urlopen','minimize'})
        self.assertNotIn('population'+'.jsonl',PATH.read_text())


if __name__=='__main__':unittest.main()
