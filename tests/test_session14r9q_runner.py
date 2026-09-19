"""R9Q orchestration and persisted publication with synthetic temporary evidence."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from defensive_network_disruption.validation import r9q_evidence as e

ROOT=Path(__file__).parents[1]
SPEC=importlib.util.spec_from_file_location('r9q_runner',ROOT/'scripts/session_14r9q_expanding_switch_equality_diagnosis.py')
r=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(r)


def package(folder,*,attempt=False,materialized=False):
    local=folder/'local';local.mkdir(parents=True)
    e.put(local/'control_rows.json',[])
    e.put(local/'publication_observations.json',dict.fromkeys(e.SCHEMAS['publication_route.json'][0],False))
    e.put(local/'reference_summary.json',dict(topology='H',complete=False,root_count=None))
    e.put(local/'outcome.json',dict(schema_version=1,records=e.empty(),reason='governed_failure',execution_valid=False,timings={'wall':0.}))
    if attempt:e.put(local/'access_attempt.json',dict(synthetic=True))
    if materialized:
        e.put(local/'selected_geometry.json',{'synthetic':True})
        e.put(local/'access_materialized.json',dict(schema_version=1,selected_sha256=e.sha(local/'selected_geometry.json'),attempt_sha256=e.sha(local/'access_attempt.json')))
    return e.close(folder,{'synthetic':True})


class RunnerTests(unittest.TestCase):
    def test_create_once_and_interrupted_pending(self):
        with tempfile.TemporaryDirectory() as name:
            path=Path(name).resolve()/'entry.json';r.put(path,{'a':1})
            with self.assertRaises(FileExistsError):r.put(path,{'a':2})
            self.assertEqual(json.loads(path.read_text()),{'a':1})
            pending=Path(name).resolve()/'.broken.json.pending';pending.write_text('interrupted')
            with self.assertRaises(FileExistsError):r.put(Path(name).resolve()/'broken.json',{})

    def test_selective_lexical_sentinels(self):
        from defensive_network_disruption.data.representation_projection import ALIASES
        with tempfile.TemporaryDirectory() as name:
            path=Path(name).resolve()/'prepared'
            row={'alias':ALIASES[0],'carrier':[0.,0.],'defenders':[[3.,1.]],'receivers':['FORBIDDEN']*8+[[8.,0.],'FORBIDDEN']}
            path.write_text('UNDECODABLE\n'*5+json.dumps(row)+'\nUNDECODABLE\n')
            selected=r.lexical_selected(path,5,8)
            self.assertEqual(selected['receiver'],(8.,0.));self.assertNotIn('receivers',selected)
            with self.assertRaises(PermissionError):r.selected(Path('must_not_open'),None)

    def test_five_linear_paths_and_once_review(self):
        with tempfile.TemporaryDirectory() as name:
            rows,flags=r.publication_controls(Path(name).resolve())
            self.assertEqual(len(rows),5);self.assertTrue(all(flags.values()))

    def test_persisted_invalid_and_uncertain_packages(self):
        for attempt,materialized in ((False,False),(True,False),(True,True)):
            with self.subTest(attempt=attempt,materialized=materialized),tempfile.TemporaryDirectory() as name:
                folder=Path(name).resolve();result=package(folder,attempt=attempt,materialized=materialized)
                self.assertTrue(result['valid']);self.assertEqual(result['numerical'],'NF')
                q=e.load(folder/'qc.json');self.assertEqual(q['edges_reopened'],int(materialized))
                self.assertEqual(q['exposure_uncertain'],attempt and not materialized)
                self.assertEqual(set(p.name for p in folder.iterdir() if p.is_file()),set(e.NAMES))

    def test_publication_check_rejects_false_decision_even_rehashed(self):
        with tempfile.TemporaryDirectory() as name:
            folder=Path(name).resolve();package(folder)
            q=e.load(folder/'qc.json');q.update(numerical='NA',readiness=1,publication='PA')
            (folder/'qc.json').write_bytes(e.canonical(q))
            m=e.load(folder/'manifest.json');m['outputs']['qc.json']=e.sha(folder/'qc.json')
            (folder/'manifest.json').write_bytes(e.canonical(m))
            with self.assertRaisesRegex(ValueError,'false_decision'):e.publication_check(folder)

    def test_missing_changed_private_and_cross_file(self):
        for target in ('authority.json','local/outcome.json','local/reference_summary.json'):
            with self.subTest(target=target),tempfile.TemporaryDirectory() as name:
                folder=Path(name).resolve();package(folder);(folder/target).write_text('{}')
                with self.assertRaises(ValueError):e.publication_check(folder)

    def test_no_historical_reads_during_publication_check(self):
        with tempfile.TemporaryDirectory() as name:
            folder=Path(name).resolve();package(folder)
            from defensive_network_disruption.validation import r9p_retained_authority as retained
            with patch.object(retained,'review_registered',side_effect=AssertionError('forbidden_review')),patch.object(r,'selected',side_effect=AssertionError('forbidden_geometry')):
                self.assertTrue(e.publication_check(folder)['valid'])

    def test_runner_integrity_failure_and_rerun(self):
        with tempfile.TemporaryDirectory() as name:
            folder=Path(name).resolve();output=folder/'out'
            with patch.object(r,'preflight',return_value={'synthetic':True}),patch.object(r,'OLD',folder/'missing'),patch.object(r,'selected',side_effect=AssertionError('forbidden_geometry')) as access:
                result=r.diagnose(output);self.assertTrue(result['valid']);self.assertEqual(result['numerical'],'NF');access.assert_not_called()
                with self.assertRaises(FileExistsError):r.diagnose(output)
            self.assertTrue((output/'local/failure/numerical_traceback.txt').exists())
            self.assertEqual(e.load(output/'qc.json')['edges_reopened'],0)

    def test_main_import_failure_survives_without_package(self):
        import builtins
        original=builtins.__import__
        def importing(name,*args,**kwargs):
            if name.startswith('defensive_network_disruption'):raise ImportError('synthetic_import_failure')
            return original(name,*args,**kwargs)
        with tempfile.TemporaryDirectory() as name:
            output=Path(name).resolve()/'out'
            with patch.object(r,'OUT',output),patch.object(r,'diagnose',side_effect=ImportError('synthetic_import_failure')),patch('sys.argv',['runner','diagnose']),patch.object(builtins,'__import__',side_effect=importing):
                with self.assertRaises(ImportError):r.main()
            self.assertEqual(e.load(output/'local/outer_failure.json')['exception'],'ImportError')
            self.assertEqual(e.sha(output/'local/outer_traceback.txt'),e.load(output/'local/outer_failure.json')['traceback_sha256'])

    def test_schema_rejects_private_field_and_nonfinite(self):
        record=e.empty()['authority.json'];record['evidence_sha256']='0'*64
        e.validate_record('authority.json',record)
        record['coordinates']=[1,2]
        with self.assertRaises(ValueError):e.validate_record('authority.json',record)
        del record['coordinates'];record['counts']['records']=True
        with self.assertRaises(ValueError):e.validate_record('authority.json',record)
        with self.assertRaises(ValueError):e.canonical({'bad':float('nan')})

    def test_preflight_blocks_dirty_tree_before_dependency_or_access(self):
        with patch.object(r,'git',return_value='dirty'),patch.object(r,'selected',side_effect=AssertionError('forbidden')) as spy:
            with self.assertRaisesRegex(RuntimeError,'dirty_tree'):r.preflight()
            spy.assert_not_called()

    def test_complete_synthetic_runner_stops_after_first_numerical_failure(self):
        from types import SimpleNamespace
        from defensive_network_disruption.validation import r9p_retained_authority as retained
        from defensive_network_disruption.geometry import r9q_diagnosis as diagnosis
        from defensive_network_disruption.data.representation_projection import ALIASES
        with tempfile.TemporaryDirectory() as name:
            folder=Path(name).resolve();old=folder/'retained';old.mkdir()
            row={'alias':ALIASES[0],'carrier':[0.,0.],'defenders':[[3.,1.]],'receivers':['FORBIDDEN']*8+[[8.,0.],'FORBIDDEN']}
            prepared=old/'prepared.jsonl';prepared.write_text('SKIPPED\n'*5+json.dumps(row)+'\n')
            authority=SimpleNamespace(sha256='synthetic',derived_record_count=1,record=lambda:{'synthetic':True})
            with patch.object(r,'preflight',return_value={'synthetic':True}),patch.object(r,'OLD',old),patch.object(r,'RETAINED',{}),patch.object(r,'RECEIPT','synthetic'),patch.object(r,'PREPARED',r.sha(prepared)),patch.object(retained,'review_registered',return_value=authority),patch.object(r,'selected',side_effect=lambda p,a:r.lexical_selected(p,5,8)),patch.object(diagnosis,'reproduce',side_effect=RuntimeError('synthetic_new_failure')) as once:
                result=r.diagnose(folder/'out')
                self.assertTrue(result['valid']);self.assertEqual(result['numerical'],'NF');self.assertEqual(result['publication'],'PA');self.assertEqual(once.call_count,1)
            q=e.load(folder/'out/qc.json');self.assertEqual(q['edges_reopened'],1);self.assertFalse(q['exposure_uncertain']);self.assertFalse(q['execution_valid'])
            self.assertTrue((folder/'out/local/failure/emergency_failure.json').exists())

    def test_historical_sources_are_bound_and_not_modified(self):
        for path,expected in r.bindings().items():self.assertEqual(r.sha(ROOT/path),expected,path)
        self.assertNotIn('project_canonical_edge',(ROOT/'scripts/session_14r9q_expanding_switch_equality_diagnosis.py').read_text())
