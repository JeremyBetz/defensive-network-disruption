"""Synthetic production-path tests for the one-shot 14am diagnostic."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

import numpy as np
from defensive_network_disruption.geometry import comparator_reproduction as d
from defensive_network_disruption.geometry.diagnostic_serialization import canonical_bytes
from defensive_network_disruption.validation.empirical_switch_diagnosis import project_prepared_edge,project_canonical_edge,selective_bytes
from defensive_network_disruption.validation.r5_persistence import Journal,read_journal

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('session14am_runner',ROOT/'scripts/session_14am_constant_width_comparator_diagnosis.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)


class Session14amTests(unittest.TestCase):
    def test_full_payload_persistent_closure(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp).resolve()
            observed=r.serializer_preflight(folder)
            self.assertTrue(observed['passed'])
            self.assertEqual((folder/'payload.json').read_bytes(),canonical_bytes(r.synthetic_payload()))
            self.assertEqual(r.load(folder/'manifest.json')['payload_sha256'],r.sha(folder/'payload.json'))

    def test_production_observer_actual_success_path(self):
        saved=[]
        success,obs,stages=d.reproduce((0.,0.),(20.,0.),((5.,0.),),lambda k,v:saved.append((k,v)),d.Budget())
        self.assertFalse(success) # A successful verifier cannot reproduce a failed gate.
        self.assertEqual(obs.calls['controlled_vector'],1)
        self.assertEqual(obs.calls['structure'],2)
        self.assertEqual(len(obs.gates),1)
        self.assertTrue(obs.gates[0]['condition'])
        self.assertTrue(d.partition_audit(obs.saved['structure'])['passed'])
        canonical_bytes(saved)
        self.assertEqual(stages[-1]['stage'],'accepted')

    def test_observer_preserves_returned_numerics(self):
        from defensive_network_disruption.geometry.verification_audit import controlled_vector
        captured=[];obs=d.Observer(lambda k,v:captured.append(v))
        def value(n):return {'maximum':.5,'union':.5}
        expected=controlled_vector(value)
        with obs.observing():actual=controlled_vector(value)
        self.assertEqual(expected,actual)
        self.assertEqual(obs.saved['controlled_vector'],actual)

    def test_convergence_and_non_circular_reference(self):
        f=lambda t:np.column_stack((t*t,np.zeros_like(t)))
        records=[]
        uniform,pieces=d.convergence(f,(0.,.25,1.),d.Budget(),lambda k,v:records.append((k,v)))
        self.assertEqual(len(records),14)
        self.assertTrue(d.reference_eligible({'passed':True},pieces))
        self.assertAlmostEqual(pieces[-1]['estimate'],1/3,places=14)
        self.assertFalse(d.reference_eligible({'passed':False},pieces))
        bad=copy.deepcopy(pieces);bad[-1]['estimate']+=1e-8
        self.assertFalse(d.reference_eligible({'passed':True},bad))

    def test_partition_defect(self):
        from defensive_network_disruption.geometry.verification_repair import VerifiedEnvelope
        envelope=VerifiedEnvelope((),(),(0,),(0.,.5,.5,1.),65536)
        result=d.partition_audit(((),envelope,envelope.partitions,(),()))
        self.assertFalse(result['passed'])

    def test_timeout_and_global_budget(self):
        with self.assertRaises(d.DiagnosticTimeout):
            with d.Budget(operation=.01).limit():time.sleep(.03)
        with self.assertRaises(d.DiagnosticTimeout):
            with d.Budget(seconds=-1).limit():pass

    def test_single_edge_and_forbidden_sentinels(self):
        receivers=[{'forbidden':'other'}]*7+[[20,1]]+[{'forbidden':'other'}]
        prepared=json.dumps(dict(alias='development_01',carrier=[0,0],receivers=receivers,defenders=[[5,0]]))
        canonical=json.dumps(dict(match_id='1886347',event_id={'forbidden':'identity'},carrier_xy=[0,0],
            candidate_ids={'forbidden':'ids'},candidate_xy=receivers,defender_xy=[[5,0]],
            target_index={'forbidden':'target'},target_outside={'forbidden':'outcome'}))
        self.assertEqual(selective_bytes(project_prepared_edge(prepared,7)),selective_bytes(project_canonical_edge(canonical,7)))
        for loc in ((5,7,'constant_width'),(4,6,'constant_width'),(4,7,'isotropic'),(True,7,'constant_width')):
            with self.assertRaises(PermissionError):r.check_location(*loc)

    def test_journal_complexity_observed(self):
        for n in (1,2,4):
            records=d.synthetic_journal(n);out=d.profile_replay(records,d.Budget())
            self.assertIsNone(out['rejection'])
            self.assertEqual(out['prefix_visits'],len(records)*(len(records)+1)//2)
            self.assertTrue(out['triangular'])
            self.assertEqual(out['file_reads'],0)

    def test_journal_rejection_preserved(self):
        records=d.synthetic_journal(1);records.append(records[-3])
        self.assertIsNotNone(d.profile_replay(records,d.Budget())['rejection'])

    def test_journal_hash_interruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp).resolve()/'journal'
            journal=Journal(path);journal.append('access_attempt');journal.close()
            self.assertEqual(len(read_journal(path)[0]),1)
            with path.open('ab') as f:f.write(b'{')
            with self.assertRaises(ValueError):read_journal(path)

    def test_marker_is_exclusive(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp).resolve()/'marker';r.claim(path)
            with self.assertRaises(FileExistsError):r.claim(path)

    def package(self,folder,status='closed'):
        local=folder/'local';local.mkdir()
        r.put(local/'private_index.json',{'files':{}})
        q=dict(schema_version=1,status=status,execution_valid=status=='closed',numerical='H' if status=='closed' else 'I',
            readiness=4,publication='P5',outcome='test',reproduced=False,states_opened=0,edges_opened=0,
            exposure_uncertain=False,private_index_sha256=r.sha(local/'private_index.json'))
        r.close(folder,r.unavailable(),q,{},{});return q

    def test_success_and_failure_persisted_publication(self):
        for status in ('closed','invalid'):
            with tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp).resolve();self.package(folder,status)
                self.assertTrue(r.publication_check(folder))

    def test_publication_mutations_rejected(self):
        for mutation in ('missing','hash','false_acceptance','cross_file'):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp).resolve();q=self.package(folder)
                if mutation=='missing':(folder/'production_path.json').unlink()
                elif mutation=='hash':(folder/'partition_audit.json').write_text('{}')
                elif mutation=='false_acceptance':
                    q['numerical']='A';(folder/'qc.json').write_bytes(canonical_bytes(q))
                else:
                    m=r.load(folder/'manifest.json');m['status']='invalid';(folder/'manifest.json').write_bytes(canonical_bytes(m))
                with self.assertRaises((ValueError,FileNotFoundError)):r.publication_check(folder)

    def test_atomic_write_serialization_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp).resolve()/'bad.json'
            try:r.put(path,{'unsupported':object()})
            except TypeError as error:
                r.put(Path(tmp).resolve()/'emergency.json',{'primary':type(error).__name__,'accepted':False})
            self.assertFalse(path.exists())
            self.assertFalse((Path(tmp).resolve()/'manifest.json').exists())
            self.assertFalse(r.load(Path(tmp).resolve()/'emergency.json')['accepted'])

    def test_no_scientific_summary_or_runtime_replacement(self):
        source=(ROOT/'scripts/session_14am_constant_width_comparator_diagnosis.py').read_text()
        for forbidden in ('candidate_summary.json','state_summaries','load_model(', 'mock.patch','setattr('):
            self.assertNotIn(forbidden,source)

if __name__=='__main__':unittest.main()
