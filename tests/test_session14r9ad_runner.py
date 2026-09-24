"""Actual one-shot closure, access isolation and persisted-record controls."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from defensive_network_disruption.validation import r9ad_run as run
from defensive_network_disruption.validation import r9ad_evidence as evidence
from defensive_network_disruption.validation import r9ad_authority as authority
from defensive_network_disruption.validation import r9j_linear_publication as linear
from defensive_network_disruption.validation import r7_execution as execution
from defensive_network_disruption.validation import numerical_failure_publication as legacy
from defensive_network_disruption.validation.r9j_evidence import load,sha,put,canonical
from defensive_network_disruption.validation.r9t_acceptance import primitive
import hashlib
from defensive_network_disruption.validation.r9v_publication_ownership import controls

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('r9ad_cli',ROOT/authority.RUNNER)
cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)


class RunnerTests(unittest.TestCase):
    def place(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        return Path(temporary.name).resolve()/'package'

    def binding(self):return {'schema_version':1,'kind':'synthetic','ci_receipt_sha256':'1'*64}

    def failure(self,folder):
        binding=self.binding()
        def fault(stage):
            if stage=='synthetic_controls':raise RuntimeError('synthetic_original')
        return run.execute(ROOT,folder,gate=lambda:binding,load_inputs=lambda:self.fail('retained_access'),binding=binding,fault=fault)

    def test_direct_entry_requires_checkpoint_gate(self):
        folder=self.place()
        with self.assertRaises(PermissionError):
            run.execute(ROOT,folder,gate=lambda:None,load_inputs=lambda:self.fail(),binding=self.binding())
        self.assertFalse((folder/'local/acceptance.marker').exists())

    def test_failure_capture_linear_closure_and_zero_access(self):
        folder=self.place()
        with patch.object(linear,'review',wraps=linear.review) as spy, \
             patch.object(execution.Progress,'failure',side_effect=AssertionError('legacy')), \
             patch.object(execution._CoreView,'snapshot',side_effect=AssertionError('legacy')), \
             patch.object(legacy,'replay',side_effect=AssertionError('legacy')):
            result=self.failure(folder)
        self.assertEqual(spy.call_count,1)
        self.assertEqual(result,{'status':'valid','classification':'E','readiness':4})
        self.assertEqual(load(folder/'qc.json')['reopened_edges'],0)
        original=load(folder/'local/failure/original_failure.json')
        self.assertEqual(original['traceback_sha256'],sha(folder/'local/failure/numerical_traceback.txt'))

    def test_rerun_rejected(self):
        folder=self.place();self.failure(folder)
        with self.assertRaises(FileExistsError):self.failure(folder)

    def test_persisted_validation_does_not_replay(self):
        folder=self.place();self.failure(folder)
        with patch.object(linear,'review',side_effect=AssertionError('second_review')):
            self.assertEqual(evidence.publication_check(folder)['status'],'valid')

    def test_cross_file_tampering_rejected(self):
        folder=self.place();self.failure(folder)
        (folder/'qc.json').write_text('{}\n')
        with self.assertRaises(ValueError):evidence.publication_check(folder)

    def test_private_trace_tampering_rejected(self):
        folder=self.place();self.failure(folder)
        (folder/'local/failure/numerical_traceback.txt').write_text('changed')
        with self.assertRaises(ValueError):evidence.publication_check(folder)

    def test_publisher_failure_preserves_original_independently(self):
        folder=self.place()
        with patch.object(evidence,'close',side_effect=RuntimeError('publisher_failure')):
            with self.assertRaisesRegex(RuntimeError,'publisher_failure'):self.failure(folder)
        self.assertEqual(load(folder/'local/failure/original_failure.json')['exception_message'],'synthetic_original')
        self.assertTrue((folder/'local/failure/publication_failure.json').exists())

    def test_actual_entry_preflight_failure_is_durable(self):
        folder=self.place()
        with patch.object(cli,'OUT',folder),patch.object(cli,'preflight',side_effect=ImportError('synthetic_import')):
            with self.assertRaises(ImportError):cli.main(['audit'])
        record=load(folder/'local/startup_failure/original_failure.json')
        self.assertEqual(record['exception_type'],'ImportError')
        self.assertEqual(record['traceback_sha256'],sha(folder/'local/startup_failure/traceback.txt'))

    def test_only_three_commands(self):
        with self.assertRaises(SystemExit):cli.main(['run'])

    def test_no_geometry_read_before_permission(self):
        folder=ROOT/authority.OUTPUT
        with authority.guard(ROOT,folder,[False]):
            for path in (ROOT/'data/forbidden.json',ROOT/authority.V/'local/selected_edge.json',
                         ROOT/'outputs/continuous_occlusion_retry/local/prepared.jsonl'):
                with self.assertRaises(PermissionError):path.read_bytes()

    def test_metadata_bindings(self):
        # Portable: protocol inventory only; ignored empirical indexes are not read.
        bindings,private=authority.inventories(ROOT)
        self.assertTrue(bindings)
        self.assertEqual(set(private),{'continuous_occlusion_terminal_cell_independent_bound',
                                     'continuous_occlusion_tie_boundary_publication_diagnosis'})

    def test_preflight_uses_offline_attempt_bound_receipt(self):
        from test_checkpoint_ci_authority_v2 import capture,expectation
        from defensive_network_disruption.validation.checkpoint_ci_authority import CIExpectation
        folder=self.place();receipt=folder/'local/checkpoint_ci.json'
        verified,_=capture(receipt);expected=expectation()
        paths=['synthetic_'+str(i) for i in range(9)]
        # Replace only repository/environment reads; receipt parsing and every
        # offline content/attempt/provenance check remain real.
        def git(*args):
            if args[0]=='status':return ''
            if args[0]=='ls-files':return '\n'.join(paths)
            if args[0]=='merge-base':return ''
            if args[-1]=='v0.1.0^{}':return authority.TAG
            return expected.checkpoint_commit
        bindings=CIExpectation(expected.checkpoint_commit,expected.protocol_sha256,
            expected.runner_implementation_sha256,expected.lockfile_sha256,expected.workflow_sha256)
        with patch.object(cli,'OUT',folder),patch.object(cli,'git',side_effect=git), \
             patch.object(cli,'expectation',return_value=bindings), \
             patch.object(cli,'sha',return_value='1'*64), \
             patch.object(authority,'verify',return_value={'selected_edge.json':'2'*64}), \
             patch.object(cli.subprocess,'check_output',return_value=b'synthetic'), \
             patch.object(Path,'is_relative_to',return_value=True):
            original=Path.read_bytes
            def read(path):return b'synthetic' if path.name in paths else original(path)
            with patch.object(Path,'read_bytes',read),patch('socket.socket',side_effect=AssertionError('network')):
                self.assertEqual(cli.preflight()['ci_receipt_sha256'],verified.receipt_sha256)
                receipt.write_bytes(b'{}\n')
                with self.assertRaises(ValueError):cli.preflight()

    def test_all_single_writer_success_failure_controls(self):
        rows=controls(self.place())
        self.assertEqual(len(rows),9)
        self.assertTrue(all(row['passed'] for row in rows))

    def synthetic_history(self,root,sink,**kwargs):
        # Test-only entrypoint fixture, never governed numerical acceptance.
        rows=[]
        for i in range(108):
            estimates={str(k):1. for k in range(4 if i<42 else 3)}
            detail={'intervals':512,'estimates':estimates,'permutations':4 if i<75 else 3,
                    'partitions':[0.,1.],'canonical_onsets':[],'canonical_switches':[],
                    'maximum_interval':{},'certificate_evidence':None}
            record={'new':primitive(detail),'old':primitive(detail),'expected':primitive(detail),
                    'previous_structures':[],'localizations':[],
                    'component_order':dict.fromkeys(('new','old','expected'),list(estimates))}
            h=sink('historical_'+str(i),record)
            rows.append({'fixture':'synthetic_'+str(i),'candidate':'constant_width','status':'passed',
                         'components':len(estimates),'permutations':detail['permutations'],
                         'structure_exact':True,'production_preserved':True,'verification_preserved':True,
                         'reason':'accepted','evidence_sha256':h})
        return rows

    def complete(self,folder,*,interrupt=False):
        row={'alias':'synthetic_r9ad','carrier':[0.,0.],'receiver':[10.,0.],'defenders':[[5.,2.]]}
        binding={**self.binding(),'selected_sha256':hashlib.sha256(canonical(row)).hexdigest()}
        def materialize():
            local=folder/'local'
            put(local/'selected_edge.json',row)
            put(local/'access_materialized.json',{'schema_version':1,'attempt_sha256':sha(local/'access_attempt.json'),
                'selected_sha256':sha(local/'selected_edge.json'),'reopened_states':1,'reopened_edges':1})
            return row
        def fault(stage):
            if interrupt and stage=='materialization_receipt':raise InterruptedError('receipt_interruption')
        with patch.object(run,'historical_regression',side_effect=self.synthetic_history):
            return run.execute(ROOT,folder,gate=lambda:binding,load_inputs=materialize,binding=binding,fault=fault)

    def test_complete_synthetic_candidate_does_not_complete_empirical_state(self):
        folder=self.place()
        with patch.object(linear,'review',wraps=linear.review) as spy:
            result=self.complete(folder)
        self.assertEqual(result['classification'],'A')
        qc=load(folder/'qc.json')
        self.assertEqual(qc['evidence_kind'],'synthetic')
        self.assertEqual(qc['completed_empirical_states'],0)
        self.assertEqual(qc['completed_empirical_edges'],0)
        # Nine control closures plus this one diagnostic closure.
        self.assertEqual(spy.call_count,10)

    def test_receipt_interruption_keeps_known_exposure_and_uncertainty(self):
        folder=self.place();result=self.complete(folder,interrupt=True)
        self.assertEqual(result['classification'],'E')
        qc=load(folder/'qc.json')
        self.assertEqual(qc['reopened_edges'],1)
        self.assertTrue(qc['exposure_uncertain'])
        self.assertEqual(load(folder/'retained_edge_replay.json')['candidate_invocations'],0)

if __name__=='__main__':unittest.main()
