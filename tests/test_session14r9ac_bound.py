from __future__ import annotations
import copy
from fractions import Fraction as F
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from defensive_network_disruption.geometry import r9ac_terminal_bound as core
from defensive_network_disruption.geometry.r9x_terminal_authority import Coefficients, canonical, digest
from defensive_network_disruption.validation import r9ac_controls as controls
from defensive_network_disruption.validation import r9ac_evidence as evidence
from defensive_network_disruption.validation import r9ac_authority as authority
from defensive_network_disruption.validation.r9ac_run import execute
from defensive_network_disruption.validation.checkpoint_ci_authority import FailureController
from defensive_network_disruption.validation import r9j_linear_publication as linear

ROOT=Path(__file__).resolve().parents[1]
RUNNER=ROOT/'scripts/session_14r9ac_terminal_cell_independent_bound.py'

def inputs():
    record=controls.authority(controls.coefficient(),[controls.coefficient(cross2=8)])
    rows=[{'ordinal':0,'depth':0,'pair_status':'equal','maximum_status':'unresolved'}]
    return record,rows

def binding():
    record,rows=inputs()
    return {'schema_version':1,'kind':'synthetic','source_authority_sha256':digest(record),
            'historical_status_sha256':digest(rows),'protocol_sha256':digest(b'synthetic protocol'),
            'runner_sha256':digest(b'synthetic runner'),'checkpoint_commit':'0'*40,'ci_receipt_sha256':'1'*64}


def runner():
    spec=importlib.util.spec_from_file_location('r9ac_test_runner',RUNNER)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


class BoundTests(unittest.TestCase):
    def test_all_ten_frozen_controls_measured(self):
        rows,details=controls.controls()
        self.assertEqual(len(rows),10);self.assertTrue(all(x['passed'] for x in rows))
        self.assertEqual([x['observed'] for x in rows],['TA','TB','TC','TD','TE','TA','TA','TA','rejected','rejected'])
        self.assertEqual(len(details),10)

    def test_each_pair_member_and_every_competitor_is_bounded(self):
        record=controls.authority((controls.coefficient(),controls.coefficient(cross2=8)),
            [controls.coefficient(cross2=16),controls.coefficient(cross2=24)])
        original=Coefficients.bounds;seen=[]
        def spy(instance,a,b):seen.append(instance.authority_sha256);return original(instance,a,b)
        with patch.object(Coefficients,'bounds',spy):result,nodes=core.bound(record)
        self.assertEqual(len(seen),4)
        self.assertEqual(seen[:2],[record['pair_left_ref'],record['pair_right_ref']])
        self.assertEqual(set(seen[2:]),set(record['competitors']))

    def test_shared_endpoint_and_complete_rational_partition(self):
        _,record,limits,_=controls.fixtures()[2]
        result,nodes=core.bound(record,limits=limits)
        summary=core.validate_result(record,nodes,result)
        self.assertTrue(summary['coverage_complete']);self.assertEqual(summary['classification'],'TC')
        self.assertFalse(summary['strict_winner_reversal'])
        self.assertGreater(summary['additional_depth'],0)

    def test_inactive_proof_is_independent_of_label(self):
        first=controls.coefficient(dot=0);second=controls.coefficient(q=4,dot=0)
        record=controls.authority((first,second),[controls.coefficient(q=9,dot=0)])
        result,nodes=core.bound(record)
        self.assertEqual(result['classification'],'TA')
        self.assertTrue(all(x['inactive'] for x in nodes[0]['fields']))
        self.assertTrue(core.validate_result(record,nodes,result)['pair_equality_proved'])

    def test_false_common_branch_label_does_not_prove_equality(self):
        record=controls.authority((controls.coefficient(cross2=8),controls.coefficient(cross2=9)),[controls.coefficient(cross2=16)])
        result,nodes=core.bound(record,limits=core.Limits(depth=0))
        self.assertFalse(core.validate_result(record,nodes,result)['pair_equality_proved'])

    def test_rounding_bounds_contain_known_exact_field(self):
        x=controls.coefficient();value,derivative=x.bounds(F(1,2),F(1))
        self.assertLessEqual(value.lo,1);self.assertGreaterEqual(value.hi,1)
        self.assertIsNotNone(derivative)

    def test_publication_validation_never_reevaluates_fields(self):
        record,_=inputs();result,nodes=core.bound(record)
        with patch.object(Coefficients,'bounds',side_effect=AssertionError('forbidden evaluation')):
            self.assertEqual(core.validate_result(record,nodes,result)['classification'],'TA')

    def test_forged_classification_and_node_claims_block(self):
        record,_=inputs();result,nodes=core.bound(record)
        for mutation in ('classification','coverage','branch','comparison','inventory','width'):
            r,n=copy.deepcopy(result),copy.deepcopy(nodes)
            if mutation=='classification':r['classification']='TB'
            elif mutation=='coverage':n[0]['right']={'numerator':'3','denominator':'4'}
            elif mutation=='branch':n[0]['fields'][0]['inactive']=True
            elif mutation=='comparison':n[0]['status']='TB'
            elif mutation=='inventory':n[0]['fields'].pop()
            else:r['maximum_difference_width']={'numerator':'0','denominator':'1'}
            with self.subTest(mutation=mutation),self.assertRaises((ValueError,KeyError)):
                core.validate_result(record,n,r)

    def test_local_depth_is_additional(self):
        _,record,_,_=controls.fixtures()[2]
        record['cell']['depth']=80
        record['provenance_sha256']=digest({k:v for k,v in record.items() if k!='provenance_sha256'})
        result,nodes=core.bound(record)
        self.assertEqual(result['historical_depth'],80)
        self.assertGreater(core.validate_result(record,nodes,result)['additional_depth'],0)

    def test_depth_leaf_and_deadline_limits_preserve_evidence(self):
        _,record,_,_=controls.fixtures()[4]
        for limit in (core.Limits(depth=0),core.Limits(leaves=1)):
            result,nodes=core.bound(record,limits=limit)
            self.assertEqual(result['classification'],'TE');self.assertEqual(len(nodes),1)
        calls=[0]
        def clock():calls[0]+=1;return calls[0]*1000.
        result,nodes=core.bound(record,clock=clock)
        self.assertEqual(result['classification'],'TE');self.assertEqual(result['reason'],'deadline')
        self.assertEqual(nodes,[])

    def test_interrupted_sink_stops_without_second_operation(self):
        record,_=inputs();calls=[]
        def sink(node):calls.append(node);raise OSError('interrupted sync')
        with self.assertRaises(OSError):core.bound(record,sink=sink)
        self.assertEqual(len(calls),1)

    def test_limits_and_nonfinite_inputs_reject(self):
        for args in ({'depth':81},{'leaves':65537},{'seconds':901},{'depth':-1}):
            with self.assertRaises(ValueError):core.Limits(**args)
        record,_=inputs();record['coefficients'][0]['q']['numerator']='NaN'
        with self.assertRaises(ValueError):core.bound(record)

    def test_deterministic_proof_content_separate_from_time(self):
        record,_=inputs();a,n=core.bound(record);b,m=core.bound(record)
        a.pop('elapsed_seconds');b.pop('elapsed_seconds')
        self.assertEqual(canonical(a),canonical(b));self.assertEqual(canonical(n),canonical(m))

    def test_mechanism_does_not_infer_boundary_error_from_dominance(self):
        result={'classification':'TB','coverage_complete':True,'pair_equality_proved':True}
        rows=[{'ordinal':0,'depth':1,'pair_status':'equal','maximum_status':'dominated'},
              {'ordinal':1,'depth':1,'pair_status':'equal','maximum_status':'unresolved'}]
        decision=evidence.decisions(result,rows)
        self.assertEqual(decision['mechanism'],'ND')
        result['classification']='TE'
        self.assertEqual(evidence.decisions(result,rows)['mechanism'],'NF')


class PublicationTests(unittest.TestCase):
    def place(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);return Path(tmp.name).resolve()
    def run_package(self,folder,**kwargs):
        return execute(folder,gate=lambda:None,load_inputs=inputs,binding=binding(),**kwargs)

    def test_success_one_linear_review_and_read_only_check(self):
        folder=self.place();original=linear.review;calls=[]
        def review(*a,**kw):calls.append(1);return original(*a,**kw)
        with patch.object(linear,'review',review):result=self.run_package(folder)
        self.assertTrue(result['publication_valid']);self.assertEqual(calls,[1])
        before={p.relative_to(folder):p.read_bytes() for p in folder.rglob('*') if p.is_file()}
        with (patch.object(linear,'review',side_effect=AssertionError('replay')),
              patch.object(Coefficients,'bounds',side_effect=AssertionError('recompute'))):
            evidence.publication_check(folder)
        after={p.relative_to(folder):p.read_bytes() for p in folder.rglob('*') if p.is_file()}
        self.assertEqual(before,after)
        self.assertEqual(sorted(p.name for p in folder.iterdir() if p.is_file()),sorted(evidence.FILES))

    def test_first_failure_closes_and_preserves_traceback(self):
        for stage in ('prerequisites','synthetic_controls','authority_load','independent_bound','publication_initialization','publication'):
            with self.subTest(stage=stage):
                folder=self.place();calls=[];original=linear.review
                def fail(current):
                    if current==stage:raise RuntimeError('synthetic:'+stage)
                def review(*a,**kw):calls.append(1);return original(*a,**kw)
                with patch.object(linear,'review',review),self.assertRaisesRegex(RuntimeError,'synthetic:'):
                    self.run_package(folder,fault=fail)
                self.assertEqual(calls,[1])
                result=evidence.publication_check(folder)
                self.assertFalse(result['execution_valid']);self.assertEqual(result['readiness'],4)
                captured=FailureController(folder/'local/failure').validate()
                self.assertEqual(captured['stage'],stage)
                self.assertEqual(result['new_edges'],0)

    def test_qc_and_publisher_failures_preserve_original_independently(self):
        for secondary in ('blocked_qc','failure_publication'):
            folder=self.place()
            def fail(stage):
                if stage=='authority_load':raise ValueError('original')
                if stage==secondary:raise OSError('secondary')
            with self.assertRaisesRegex(ValueError,'original'):self.run_package(folder,fault=fail)
            controller=FailureController(folder/'local/failure');self.assertEqual(controller.validate()['exception_type'],'ValueError')
            self.assertTrue((folder/'local/failure/publication_failure.json').exists())

    def test_marker_collision_is_read_only_and_no_loader_call(self):
        folder=self.place();self.run_package(folder)
        before=(folder/'manifest.json').read_bytes()
        with self.assertRaises(FileExistsError):self.run_package(folder)
        self.assertEqual((folder/'manifest.json').read_bytes(),before)

    def test_persisted_tampering_and_missing_files_block(self):
        for name in ('qc.json','local/result.json','local/nodes/000000.json','local/linear_authority.json'):
            folder=self.place();self.run_package(folder);(folder/name).write_bytes(b'{}\n')
            with self.assertRaises(ValueError):evidence.publication_check(folder)
        folder=self.place();self.run_package(folder);(folder/'local/result.json').unlink()
        with self.assertRaises(ValueError):evidence.publication_check(folder)

    def test_false_public_claim_with_updated_manifest_still_blocks(self):
        folder=self.place();self.run_package(folder)
        qc=json.loads((folder/'qc.json').read_bytes());qc['mechanism']='NA'
        (folder/'qc.json').write_bytes(canonical(qc))
        manifest=json.loads((folder/'manifest.json').read_bytes())
        manifest['outputs']['qc.json']=authority.sha(folder/'qc.json')
        (folder/'manifest.json').write_bytes(canonical(manifest))
        with self.assertRaisesRegex(ValueError,'public_semantics'):evidence.publication_check(folder)

    def test_legacy_replay_tripwires(self):
        from defensive_network_disruption.validation import numerical_failure_publication as legacy
        from defensive_network_disruption.validation.r7_execution import Progress
        with (patch.object(legacy,'replay',side_effect=AssertionError('prefix replay')),
              patch.object(Progress,'failure',side_effect=AssertionError('legacy failure'))):
            self.run_package(self.place())

    def test_public_privacy_has_no_coefficients_or_exact_values(self):
        folder=self.place();self.run_package(folder)
        for name in evidence.FILES:
            text=(folder/name).read_text()
            for token in ('numerator','denominator','pair_left_ref','cross2','/Users/','selected_edge','carrier','receiver'):
                self.assertNotIn(token,text)


class AccessAndEntryTests(unittest.TestCase):
    def test_committed_bindings_and_metadata_only_inventory(self):
        self.assertEqual(len(authority.verify_bindings(ROOT)),30)
        # No private metadata is needed for this portable test.
        self.assertEqual(authority.AUTHORITY_HASH,'b9fab1e5b55d0e105f18d2abdaa2a5a6555547509616e4b9871df3ff57f6e6aa')

    def test_selected_boundary_prepared_provider_and_network_tripwires(self):
        own=ROOT/authority.OUTPUT
        with authority.access_guard(ROOT,own):
            for path in (ROOT/authority.V/'local/selected_edge.json',ROOT/authority.V/'local/boundary_capture.json',
                         ROOT/'outputs/not_authorized/prepared.json',ROOT/'data/provider.json'):
                with self.assertRaises(PermissionError):path.open('rb')
            import socket
            with self.assertRaises(PermissionError):socket.getaddrinfo('example.com',443)

    def test_runner_has_only_three_commands(self):
        result=subprocess.run([sys.executable,str(RUNNER),'--help'],capture_output=True,text=True)
        self.assertEqual(result.returncode,0);self.assertIn('preflight,bound,publication-check',result.stdout)

    def test_actual_main_failure_preserves_stdlib_traceback(self):
        module=runner()
        with tempfile.TemporaryDirectory() as tmp:
            module.OUT=Path(tmp).resolve()
            with patch.object(module,'governed',side_effect=ImportError('controlled import')):
                with self.assertRaisesRegex(ImportError,'controlled import'):module.main(['bound'])
            original=json.loads((module.OUT/'local/startup_failure/original_failure.json').read_bytes())
            self.assertEqual(original['exception_type'],'ImportError')
            self.assertEqual(original['traceback_sha256'],authority.sha(module.OUT/'local/startup_failure/traceback.txt'))

    def test_actual_main_synthetic_success_uses_same_engine(self):
        module=runner()
        with tempfile.TemporaryDirectory() as tmp:
            module.OUT=Path(tmp).resolve()
            with patch.object(module,'governed',lambda:execute(module.OUT,gate=lambda:None,load_inputs=inputs,binding=binding())):
                module.main(['bound'])
            self.assertTrue(evidence.publication_check(module.OUT)['publication_valid'])

    def test_direct_entry_and_missing_receipt_cannot_load_retained(self):
        module=runner()
        with patch.object(module,'git',return_value='dirty'):
            with self.assertRaisesRegex(RuntimeError,'dirty_tree'):module.preflight()

    def test_source_contains_no_geometry_numerical_or_acquisition_route(self):
        files=[ROOT/'src/defensive_network_disruption/geometry/r9ac_terminal_bound.py',
               ROOT/'src/defensive_network_disruption/validation/r9ac_run.py']
        for file in files:
            text=file.read_text()
            for token in ('from_geometry','evaluate_edge','classify_terminal(','load_prepared','detect_switch','load_lineage'):
                self.assertNotIn(token,text)


class AdditionalAuthorityTests(unittest.TestCase):
    def test_all_schema_mutations_reject_before_bounds(self):
        base,_=inputs()
        changes=(lambda v:v.update(schema_version=1),
                 lambda v:v['tie_authority'].update(scope='point'),
                 lambda v:v['tie_authority'].pop('structural_tie_lineage_sha256'),
                 lambda v:v['cell'].update(left={'numerator':'2','denominator':'4'}),
                 lambda v:v.update(pair_left_ref='f'*64),
                 lambda v:v.update(competitors=[]),
                 lambda v:v.update(provenance_sha256='0'*64),
                 lambda v:v['coefficients'].reverse())
        for change in changes:
            value=copy.deepcopy(base);change(value)
            with self.assertRaises(ValueError):core.bound(value)

    def test_missing_or_changed_source_never_falls_back(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'record.json';path.write_bytes(b'{}\n')
            with self.assertRaisesRegex(ValueError,'source_hash'):authority.load(path,'0'*64)
            path.unlink()
            with self.assertRaises(FileNotFoundError):authority.load(path,'0'*64)

    def test_offline_preflight_requires_exact_receipt_and_freshness(self):
        module=runner()
        def git(*args):
            if args==('status','--porcelain'):return ''
            if args==('rev-parse','v0.1.0^{}'):return authority.TAG
            if args[0]=='ls-files':return args[-1]
            return authority.START
        with tempfile.TemporaryDirectory() as temp:
            module.OUT=Path(temp).resolve()
            with (patch.object(module,'git',git),patch.object(authority,'metadata',return_value=({}, {}, [])),
                  patch.object(sys,'executable',str(ROOT/'.venv/bin/python'))):
                with self.assertRaises(FileNotFoundError):module.preflight()
                (module.OUT/'local').mkdir()
                (module.OUT/'local/checkpoint_ci.json').write_bytes(b'{}\n')
                (module.OUT/'local/checkpoint_ci.json.sha256').write_text('0'*64)
                with self.assertRaisesRegex(ValueError,'ci_receipt_hash'):module.preflight()

    def test_actual_governed_route_calls_only_allowed_loader_after_gate(self):
        module=runner();record,rows=inputs()
        with tempfile.TemporaryDirectory() as temp:
            module.OUT=Path(temp).resolve();order=[]
            def preflight():order.append('gate');return {'head':'0'*40,'receipt_sha256':'1'*64}
            def source(root):order.append('source');return record,rows
            with (patch.object(module,'preflight',preflight),patch.object(authority,'retained',source),
                  patch.object(authority,'AUTHORITY_HASH',digest(record)),patch.object(authority,'PARTITION',digest(rows)),
                  patch('defensive_network_disruption.validation.checkpoint_ci_authority.validate_receipt',return_value=None)):
                result=module.governed()
            self.assertEqual(order,['gate','source']);self.assertTrue(result['publication_valid'])

    def test_false_traceback_hash_or_missing_original_blocks(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp).resolve()
            def fail(stage):
                if stage=='authority_load':raise ValueError('original')
            with self.assertRaises(ValueError):execute(folder,gate=lambda:None,load_inputs=inputs,binding=binding(),fault=fail)
            original=folder/'local/failure/original_failure.json'
            before=original.read_bytes();value=json.loads(before);value['traceback_sha256']='0'*64
            original.write_bytes(canonical(value))
            with self.assertRaises(ValueError):evidence.publication_check(folder)

    def test_incomplete_success_and_empty_exposure_tampering_reject(self):
        for relative in ('local/stages/03.json','local/empirical_journal.jsonl'):
            with tempfile.TemporaryDirectory() as temp:
                folder=Path(temp).resolve();execute(folder,gate=lambda:None,load_inputs=inputs,binding=binding())
                (folder/relative).write_bytes(b'{}\n')
                with self.assertRaises(ValueError):evidence.publication_check(folder)


class PersistedCheckpointTests(unittest.TestCase):
    def test_retained_namespace_cannot_claim_synthetic_authority(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp).resolve()/Path(authority.OUTPUT).name
            with self.assertRaisesRegex(ValueError,'retained_namespace'):
                execute(folder,gate=lambda:None,load_inputs=inputs,binding=binding())
            self.assertTrue((folder/'local/failure/original_failure.json').exists())

    def test_retained_binding_requires_checkpoint_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp).resolve();b=binding();b.update(kind='retained',source_authority_sha256=authority.AUTHORITY_HASH,
                historical_status_sha256=authority.PARTITION)
            with self.assertRaises(FileNotFoundError):execute(folder,gate=lambda:None,load_inputs=inputs,binding=b)
            self.assertTrue((folder/'local/failure/original_failure.json').exists())


class OperationDeadlineTests(unittest.TestCase):
    def test_deadline_interrupts_one_slow_arithmetic_call_and_preserves_frontier(self):
        import time
        from defensive_network_disruption.validation.r9ac_run import operation_deadline
        record,_=inputs()
        def slow(*args):time.sleep(1)
        with patch.object(Coefficients,'bounds',slow),operation_deadline(.02):
            result,nodes=core.bound(record)
        self.assertEqual(result['classification'],'TE')
        self.assertEqual(result['reason'],'deadline')
        self.assertEqual(nodes,[])


if __name__=='__main__':unittest.main()
