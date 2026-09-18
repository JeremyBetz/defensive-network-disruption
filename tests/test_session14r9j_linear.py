import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from defensive_network_disruption.validation import r9j_linear_publication as new
from defensive_network_disruption.validation import numerical_failure_publication as old
from defensive_network_disruption.validation import r9e_publication as historical
from defensive_network_disruption.validation import r9j_evidence as e

ROOT=Path(__file__).resolve().parents[1]


class LinearTests(unittest.TestCase):
    def test_all_controls_and_prefixes(self):
        with tempfile.TemporaryDirectory() as tmp:
            result=new.acceptance(Path(tmp).resolve())
            self.assertTrue(all(result['flags'].values()))
            self.assertEqual(result['counts']['controls'],10)
            self.assertGreater(result['counts']['prefixes'],100)
            self.assertGreaterEqual(result['counts']['rejections'],20)

    def test_real_historical_14ai_fixtures(self):
        spec=importlib.util.spec_from_file_location('fixture_ai',ROOT/'tests/test_session14ai_contracts.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        for diagnostic in (False,True):
            for success in (False,True):
                events=module.events(diagnostic=diagnostic,success=success)
                # Historical fixture rows are action/payload tuples.
                rows=new.chain(events)
                self.assertEqual(new.outcomes(old.replay,rows),new.outcomes(new.replay,rows))

    def test_real_historical_r7_progress(self):
        for session in ('r7','r8','r9'):
            spec=importlib.util.spec_from_file_location('fixture_'+session,ROOT/f'tests/test_session14{session}_enforcement.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            with self.subTest(session=session),tempfile.TemporaryDirectory(dir=ROOT) as tmp:
                folder=Path(tmp);j,p=module.control(folder)
                module.finish(p);j.close()
                authority=new.review(j.path)
                self.assertEqual(authority.legacy,old.authority(j.path,j.previous))

    def test_exposure_retained_on_partial_field_failure(self):
        value=new.replay(new.fixture('failure'))['snapshot']
        self.assertEqual(value['counters']['edges_opened'],2)
        self.assertEqual(value['counters']['edges_completed'],1)
        self.assertEqual(value['counters']['field_evaluations_completed'],5)
        self.assertEqual(value['active'],{'state':'0','edge':'1','candidate':'constant_width'})

    def test_uncertainty_is_not_zero_exposure(self):
        value=new.replay(new.fixture('uncertain'))['snapshot']
        self.assertEqual(value['counters']['edges_opened'],0)
        self.assertEqual(value['counters']['unresolved_projection_attempts'],1)
        self.assertFalse(value['confirmed_zero_exposure'])

    def test_full_chain_precedes_semantic_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp).resolve()/'journal'
            rows=new.fixture('success');rows[0]['action']='unknown'
            # Also breaks next-record chain, as old read_journal must detect first.
            new.write_records(p,rows)
            with self.assertRaisesRegex(new.LifecycleError,'journal_chain'):new.review(p)

    def test_partial_write_and_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp).resolve()/'journal';new.write_records(p,new.fixture('failure'))
            with self.assertRaisesRegex(new.LifecycleError,'retained_raw_hash'):new.review(p,expected_sha256='0'*64)
            with self.assertRaisesRegex(new.LifecycleError,'journal_truncation_or_reset'):new.review(p,expected_head='0'*64)
            p.write_bytes(p.read_bytes()[:-1])
            with self.assertRaisesRegex(new.LifecycleError,'interrupted_journal_write'):new.review(p)

    def test_immutable_authority_and_snapshot_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp).resolve()/'journal';new.write_records(p,new.fixture('failure'));authority=new.review(p)
            value=authority.record();value['legacy']['snapshot']['terminal']=False
            self.assertTrue(authority.legacy['snapshot']['terminal'])
            self.assertEqual(authority.legacy['snapshot_sha256'],new.digest(authority.legacy['snapshot']))
            self.assertNotEqual(authority.legacy['snapshot_sha256'],authority.record()['lifecycle_snapshot_sha256'])
            with self.assertRaises(TypeError):new.Authority(b'{}',object())

    def test_empty_preaccess_compatibility(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp).resolve()/'journal';p.write_bytes(b'')
            value=new.review(p)
            self.assertEqual(value.progress('pre_access'),historical.derive_progress(p,expected_head=None,mode='pre_access'))
            with self.assertRaises(ValueError):value.progress('empirical_failure')

    def test_numerical_success_and_failed_acceptance_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp).resolve();p=folder/'journal';new.write_records(p,new.fixture('success'));authority=new.review(p)
            package=old.package(authority.legacy,accepted=True,checks={'synthetic':True})
            for name in ('qc','manifest','evidence'):e.put(folder/(name+'.json'),package)
            self.assertEqual(new.validate_numerical_package(folder,authority),old.validate_persisted(folder,p,authority.legacy['journal_sha256']))
            for name in ('qc','manifest','evidence'):
                item=copy.deepcopy(package);item['checks']['synthetic']=False;(folder/(name+'.json')).write_bytes(e.canonical(item))
            with self.assertRaisesRegex(new.LifecycleError,'acceptance_gate'):new.validate_numerical_package(folder,authority)

    def test_source_mutation_invalidates_reuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp).resolve();p=folder/'journal';new.write_records(p,new.fixture('success'));authority=new.review(p)
            for name in ('qc','manifest','evidence'):e.put(folder/(name+'.json'),old.package(authority.legacy,accepted=True,checks={'synthetic':True}))
            p.write_bytes(p.read_bytes()+b'\n')
            with self.assertRaisesRegex(new.LifecycleError,'authority_source_changed'):new.validate_numerical_package(folder,authority)

    def test_package_mismatches_and_missing_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp).resolve();p=folder/'journal';new.write_records(p,new.fixture('failure'));authority=new.review(p)
            private,public,trace,mode=new.persist_control(folder/'package',authority)
            self.assertEqual(new.validate_public(public,private,authority,mode,traceback_path=trace)['status'],'valid')
            data=e.load(private/'progress_authority.json');data['exposure']['edges_opened']=0
            (private/'progress_authority.json').write_bytes(e.canonical(data))
            with self.assertRaisesRegex(ValueError,'private_progress_mismatch'):new.validate_public(public,private,authority,mode,traceback_path=trace)

    def test_operation_counts_observed(self):
        result=new.complexity_probe()
        self.assertTrue(all(result['flags'].values()))
        self.assertEqual(result['counts']['measured_attempt_scans'],result['counts']['predicted_attempt_scans'])

    def test_benchmark_timeout_is_censored(self):
        result=new.benchmark(1000,seconds=.001)
        self.assertEqual(result['old_status'],'timeout')
        self.assertEqual(result['equal'],'')
        skipped=new.benchmark(1000,old_enabled=False)
        self.assertEqual(skipped['old_seconds'],'')

    def test_small_benchmark_equivalence(self):
        result=new.benchmark(16,seconds=1)
        self.assertEqual(result['old_status'],'completed');self.assertTrue(result['equal'])

    def test_all_single_event_deletions_and_duplications(self):
        rows=new.fixture('success')
        for index in range(len(rows)):
            for changed in (rows[:index]+rows[index+1:],rows[:index]+[rows[index]]+rows[index:]):
                self.assertEqual(new.outcomes(old.replay,changed),new.outcomes(new.replay,changed))


if __name__=='__main__':unittest.main()
