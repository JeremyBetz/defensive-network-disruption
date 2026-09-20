"""R9R runner, zero-access gates, immutable publication and failure evidence."""
from pathlib import Path
import importlib.util
import json
import tempfile
import unittest
from unittest.mock import patch

from defensive_network_disruption.validation import r9r_acceptance as a
from defensive_network_disruption.validation import r9r_evidence as e

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('r9r_runner',ROOT/'scripts/session_14r9r_switch_localization_repair.py')
r=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(r)


def blocked_history(root,sink,**kwargs):
    rows=[]
    label,case=a.historical_cases(root)[0]
    expected=a.primitive(case['historical_vector'])
    # Source-shaped synthetic data, not empirical identifiers or geometry.
    detail=dict(old={'estimates':{'individual':{'float':0.,'hex':'0x0.0p+0'}},'intervals':512},new=None,
                expected=expected,
                localizations=[],fixture='synthetic_regression',reason='localization_G',stage='owner_certification',seconds=0.)
    h=sink('historical_0',detail)
    rows.append(dict(fixture=label,candidate=case['candidate'],status='blocked',components=len(expected['estimates']),permutations=0,
                     structure_exact=False,production_preserved=False,verification_preserved=False,reason='localization_G',evidence_sha256=h))
    return rows


def run_blocked(folder):
    with patch.object(r,'preflight',return_value={'synthetic':True}),patch.object(a,'historical_regression',side_effect=blocked_history),patch.object(r,'selected',side_effect=AssertionError('forbidden_geometry')) as access:
        result=r.audit(folder);access.assert_not_called()
    return result


class RunnerTests(unittest.TestCase):
    def test_complete_synthetic_blocked_runner_and_no_access(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp).resolve();result=run_blocked(folder)
            self.assertEqual((result['classification'],result['readiness']),("C",3))
            self.assertEqual((result['states_reopened'],result['edges_reopened']),(0,0))
            self.assertFalse((folder/'local/numerical.marker').exists())
            self.assertEqual(set(p.name for p in folder.iterdir() if p.is_file()),set(e.NAMES))
            with patch.object(r,'preflight',return_value={'synthetic':True}):
                with self.assertRaises(FileExistsError):r.audit(folder)

    def test_linear_terminal_controls(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows,result=r.publication_controls(Path(tmp).resolve())
            self.assertEqual(len(rows),5);self.assertTrue(all(result['flags'].values()),result)

    def test_changed_hash_missing_evidence_and_false_acceptance(self):
        for name in ('qc.json','local/outcome.json','local/topology_controls.csv.json'):
            with self.subTest(name=name),tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp).resolve();run_blocked(folder)
                (folder/name).write_text('{}')
                with self.assertRaises(ValueError):e.publication_check(folder)
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp).resolve();run_blocked(folder)
            q=e.load(folder/'qc.json');q.update(classification='A',readiness=1)
            (folder/'qc.json').write_bytes(e.canonical(q))
            m=e.load(folder/'manifest.json');m['outputs']['qc.json']=e.sha(folder/'qc.json')
            (folder/'manifest.json').write_bytes(e.canonical(m))
            with self.assertRaisesRegex(ValueError,'false_decision'):e.publication_check(folder)

    def test_publication_check_does_not_replay_or_reconstruct(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp).resolve();run_blocked(folder)
            from defensive_network_disruption.validation import r9j_linear_publication as linear
            with patch.object(linear,'review',side_effect=AssertionError('review forbidden')),patch.object(r,'selected',side_effect=AssertionError('selection forbidden')),patch.object(a,'historical_regression',side_effect=AssertionError('evaluation forbidden')):
                self.assertTrue(e.publication_check(folder)['valid'])

    def test_synthetic_timeout_failure_stops_without_access(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp).resolve()
            with patch.object(r,'preflight',return_value={'synthetic':True}),patch.object(a,'historical_regression',side_effect=TimeoutError('synthetic_timeout')),patch.object(r,'selected',side_effect=AssertionError('forbidden')) as access:
                result=r.audit(folder);access.assert_not_called()
            self.assertEqual(result['classification'],'E')
            self.assertTrue((folder/'local/failure/original_failure.json').exists())
            self.assertTrue((folder/'local/failure/numerical_traceback.txt').exists())

    def test_serialization_nonfinite_symlink_and_interrupted_write(self):
        with self.assertRaises(ValueError):r.canonical({'x':float('nan')})
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp).resolve();(folder/'.record.json.pending').write_text('incomplete')
            with self.assertRaises(FileExistsError):r.put(folder/'record.json',{})
            r.put(folder/'other.json',{'x':1})
            with self.assertRaises(FileExistsError):r.put(folder/'other.json',{'x':2})
            (folder/'link.json').symlink_to(folder/'other.json')
            with self.assertRaises(PermissionError):r.put(folder/'link.json',{})

    def test_preflight_rejects_dirty_tree_and_no_access(self):
        with patch.object(r,'git',return_value='dirty'),patch.object(r,'selected',side_effect=AssertionError('forbidden')) as access:
            with self.assertRaisesRegex(RuntimeError,'dirty_tree'):r.preflight()
            access.assert_not_called()

    def test_direct_entry_and_incomplete_unlock_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(PermissionError):r.selected(Path(tmp),None)
            with self.assertRaises(PermissionError):r.AccessPermit(object(),'synthetic')
            with self.assertRaises(PermissionError):r.unlock({}, {n:[] for n in e.COLUMNS}, {'flags':{}})

    def test_missing_retained_index_never_loads_geometry(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp).resolve()
            with patch.object(r,'RETAINED',folder/'missing'):
                with self.assertRaises(FileNotFoundError):r.selected(folder/'local',r.AccessPermit(r._ACCESS_SEAL,'synthetic_checkpoint'))
            self.assertFalse((folder/'local/access_attempt.json').exists())

    def test_retained_selection_uses_only_single_edge_and_receipts(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp).resolve();old=folder/'retained';new=folder/'local';old.mkdir()
            r.put(old/'selected_geometry.json',dict(alias='synthetic_r9r',carrier=[0.,0.],receiver=[20.,0.],defenders=[[8.,2.]]))
            r.put(old/'retained_review.json',dict(synthetic=True));r.put(old/'access_attempt.json',dict(synthetic=True))
            r.put(old/'access_materialized.json',dict(schema_version=1,selected_sha256=r.sha(old/'selected_geometry.json'),attempt_sha256=r.sha(old/'access_attempt.json')))
            r.put(old/'private_index.json',dict(schema_version=1,files={p.name:r.sha(p) for p in old.iterdir()}))
            with patch.object(r,'RETAINED',old),patch.object(r,'INDEX',r.sha(old/'private_index.json')),patch.object(r,'REVIEW',r.sha(old/'retained_review.json')):
                row=r.selected(new,r.AccessPermit(r._ACCESS_SEAL,'synthetic_checkpoint'))
            self.assertEqual(row['alias'],'synthetic_r9r');self.assertTrue((new/'access_materialized.json').exists())
            self.assertEqual(r.sha(new/'selected_geometry.json'),r.sha(old/'selected_geometry.json'))

    def test_import_failure_original_traceback_survives(self):
        import builtins
        original=builtins.__import__
        def importing(name,*args,**kwargs):
            if name.startswith('defensive_network_disruption'):raise ImportError('synthetic_import')
            return original(name,*args,**kwargs)
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp).resolve()
            with patch.object(r,'OUT',folder),patch.object(r,'audit',side_effect=ImportError('synthetic_import')),patch('sys.argv',['runner','audit']),patch.object(builtins,'__import__',side_effect=importing):
                with self.assertRaises(ImportError):r.main()
            value=json.loads((folder/'local/outer_failure.json').read_bytes())
            self.assertEqual(value['exception'],'ImportError')
            self.assertEqual(value['traceback_sha256'],r.sha(folder/'local/outer_traceback.txt'))

    def test_actual_single_candidate_success_and_failure_closure(self):
        from defensive_network_disruption.geometry import r9r_adapter
        from defensive_network_disruption.validation import r9j_linear_publication as linear
        import time
        for failed in (False,True):
            with self.subTest(failed=failed),tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp).resolve();old=folder/'retained';local=folder/'local';old.mkdir();local.mkdir()
                cell={'left':{'numerator_hex':'1','denominator_hex':'a'},'right':{'numerator_hex':'1','denominator_hex':'5'}}
                r.put(old/'000001_reference_cell.json',cell)
                r.put(old/'private_index.json',{'files':{'000001_reference_cell.json':r.sha(old/'000001_reference_cell.json')}})
                row=dict(alias='synthetic_r9r',carrier=[0.,0.],receiver=[20.,0.],defenders=[[8.,2.]])
                serial=[0]
                def sink(label,value):
                    serial[0]+=1;path=local/(str(serial[0])+'_'+label+'.json');r.put(path,value);return r.sha(path)
                with patch.object(r,'RETAINED',old),patch.object(linear,'review',wraps=linear.review) as review:
                    if failed:
                        def broken(*args,**kwargs):
                            kwargs['record'](stage='geometry');raise ValueError('synthetic_numerical_failure')
                        with patch.object(r9r_adapter,'evaluate',side_effect=broken):
                            with self.assertRaisesRegex(ValueError,'synthetic_numerical_failure'):
                                r.retained_run(local,row,sink,time.monotonic()+10)
                        self.assertTrue((local/'numerical_failure/original_failure.json').exists())
                        self.assertTrue((local/'failed_diagnostic_publication/qc.json').exists())
                    else:
                        self.assertTrue(r.retained_run(local,row,sink,time.monotonic()+10))
                        self.assertTrue((local/'retained_success.json').exists())
                    self.assertEqual(review.call_count,1)

    def test_historical_bindings_preserved(self):
        for name,h in r.bindings().items():self.assertEqual(r.sha(ROOT/name),h,name)

    def test_public_privacy_and_type_rejection(self):
        value=e.record(dict(authority_bound=True,separate_math_binary64=True,historical_sources_preserved=True,no_tolerance_change=True),dict(topology_families=14,negative_families=9),{})
        value['evidence_sha256']='0'*64;e.validate_record('repair_contract.json',value)
        value['coordinates']=[1,2]
        with self.assertRaises(ValueError):e.validate_record('repair_contract.json',value)
        del value['coordinates'];value['counts']['topology_families']=True
        with self.assertRaises(ValueError):e.validate_record('repair_contract.json',value)


if __name__=='__main__':unittest.main()
