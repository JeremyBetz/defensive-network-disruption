import copy
from pathlib import Path
import tempfile
import unittest

from defensive_network_disruption.validation.projection_exposure import (
    CANDIDATES,
    ExposureAuthority,
    capture_failure,
    package_record,
    progress_view,
    replay_exposure,
    validate_cross_file_package,
)
from defensive_network_disruption.validation.r5_persistence import read_journal
from defensive_network_disruption.validation.state_lifecycle import LifecycleError


def authority(root: Path, states=(('state_01', ('edge_01',)),)) -> ExposureAuthority:
    item = ExposureAuthority(root.resolve() / 'journal.jsonl')
    item.authorize_access()
    for state, edges in states:
        item.discover_state(state, edges)
    return item


def snapshot(item: ExposureAuthority):
    return replay_exposure(read_journal(item.journal.path)[0])


def project(item: ExposureAuthority, state: str):
    return item.project(state, lambda: {'synthetic_geometry': True})


def start(item: ExposureAuthority, state='state_01'):
    item.prepare_state(state); item.start_state(state)


def fields(item: ExposureAuthority, edge='edge_01', count=3, state='state_01'):
    for candidate in CANDIDATES[:count]:
        item.start_field(state, edge, candidate)
        item.complete_field(state, edge, candidate)


def records(item: ExposureAuthority, mode: str):
    view = progress_view(item.journal.path, expected_head=item.journal.previous, mode=mode)
    return view, [package_record(view) for _ in range(4)]


class Session14agProjectionExposureTests(unittest.TestCase):
    def test_exact_r5_regression_reports_two_open_unresolved_edges(self):
        with tempfile.TemporaryDirectory() as directory:
            item = authority(Path(directory), (('state_01', ('edge_01', 'edge_02')),))
            project(item, 'state_01')
            evidence = capture_failure(item, stage='after_registration', exception=RuntimeError('synthetic'), state='state_01')
            counters = evidence.terminal['counters']
            self.assertEqual(counters['edges_opened'], 2)
            self.assertEqual(counters['edges_evaluation_started'], 0)
            self.assertEqual(counters['edges_completed'], 0)
            self.assertEqual(counters['unresolved_exposed_edges'], 2)
            item.close()

    def test_projection_failure_before_materialization_does_not_open_edge(self):
        with tempfile.TemporaryDirectory() as directory:
            item = authority(Path(directory))
            with self.assertRaisesRegex(RuntimeError, 'projection'):
                item.project('state_01', lambda: (_ for _ in ()).throw(RuntimeError('projection')))
            item.fail('projection', RuntimeError('projection'), state='state_01')
            result = snapshot(item)
            self.assertEqual(result['counters']['edges_opened'], 0)
            self.assertEqual(result['counters']['unresolved_projection_attempts'], 0)
            self.assertTrue(result['confirmed_zero_exposure'])
            item.close()

    def test_unresolved_projection_attempt_blocks_confirmed_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            item = authority(Path(directory)); item.begin_projection('state_01')
            item.fail('projection_receipt', RuntimeError('interrupted'), state='state_01')
            result = snapshot(item)
            self.assertEqual(result['counters']['edges_opened'], 0)
            self.assertEqual(result['counters']['unresolved_projection_attempts'], 1)
            self.assertFalse(result['confirmed_zero_exposure'])
            item.close()

    def test_field_progress_and_unique_edge_accounting(self):
        for completed in range(4):
            with self.subTest(completed=completed), tempfile.TemporaryDirectory() as directory:
                item = authority(Path(directory)); project(item, 'state_01'); start(item)
                fields(item, count=completed)
                result = snapshot(item); counters = result['counters']
                self.assertEqual(counters['edges_opened'], 1)
                self.assertEqual(counters['field_evaluations_started'], completed)
                self.assertEqual(counters['field_evaluations_completed'], completed)
                self.assertEqual(counters['edges_evaluation_started'], int(completed > 0))
                self.assertEqual(counters['edges_completed'], 0)
                self.assertEqual(counters['unresolved_exposed_edges'], 1)
                item.close()

    def test_three_fields_then_edge_and_state_completion(self):
        with tempfile.TemporaryDirectory() as directory:
            item = authority(Path(directory)); project(item, 'state_01'); start(item); fields(item)
            item.complete_edge('state_01', 'edge_01'); item.complete_state('state_01'); item.succeed()
            result = snapshot(item); counters = result['counters']
            self.assertEqual((counters['edges_opened'], counters['edges_completed']), (1, 1))
            self.assertEqual((counters['field_evaluations_started'], counters['field_evaluations_completed']), (3, 3))
            self.assertEqual(counters['unresolved_exposed_edges'], 0)
            item.close()

    def test_final_field_failure_preserves_partial_work(self):
        with tempfile.TemporaryDirectory() as directory:
            item = authority(Path(directory)); project(item, 'state_01'); start(item); fields(item, count=2)
            item.start_field('state_01', 'edge_01', 'constant_width')
            capture = capture_failure(item, stage='field_evaluation', exception=RuntimeError('synthetic'),
                                      state='state_01', edge='edge_01', candidate='constant_width')
            counters = capture.terminal['counters']
            self.assertEqual((counters['edges_opened'], counters['edges_completed'], counters['unresolved_exposed_edges']), (1, 0, 1))
            self.assertEqual((counters['field_evaluations_started'], counters['field_evaluations_completed']), (3, 2))
            self.assertEqual(capture.terminal['active']['candidate'], 'constant_width')
            item.close()

    def test_state_completion_rejects_unresolved_required_edge(self):
        with tempfile.TemporaryDirectory() as directory:
            item = authority(Path(directory), (('state_01', ('edge_01', 'edge_02')),))
            project(item, 'state_01'); start(item); fields(item, 'edge_01'); item.complete_edge('state_01', 'edge_01')
            with self.assertRaisesRegex(LifecycleError, 'invalid_state_completion'):
                item.complete_state('state_01')
            item.close()

    def test_multi_state_success_counts_edges_once_and_calls_three_times(self):
        with tempfile.TemporaryDirectory() as directory:
            states = (('state_01', ('edge_01', 'edge_02')), ('state_02', ('edge_03',)))
            item = authority(Path(directory), states)
            for state, edge_keys in states:
                project(item, state); start(item, state)
                for candidate in CANDIDATES:
                    for edge in edge_keys:
                        item.start_field(state, edge, candidate); item.complete_field(state, edge, candidate)
                for edge in edge_keys: item.complete_edge(state, edge)
                item.complete_state(state)
            item.succeed(); result = snapshot(item); counters = result['counters']
            self.assertEqual((counters['states_completed'], counters['edges_opened'], counters['edges_completed']), (2, 3, 3))
            self.assertEqual(counters['field_evaluations_completed'], 9)
            item.close()

    def test_field_order_duplicate_projection_and_premature_completion_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            item = authority(Path(directory)); project(item, 'state_01'); start(item)
            with self.assertRaisesRegex(LifecycleError, 'field_order'):
                item.start_field('state_01', 'edge_01', 'expanding')
            with self.assertRaisesRegex(LifecycleError, 'duplicate_edge_materialization'):
                project(item, 'state_01')
            with self.assertRaisesRegex(LifecycleError, 'invalid_edge_completion'):
                item.complete_edge('state_01', 'edge_01')
            item.close()

    def test_cross_file_validator_recomputes_journal_authority(self):
        with tempfile.TemporaryDirectory() as directory:
            item = authority(Path(directory), (('state_01', ('edge_01', 'edge_02')),)); project(item, 'state_01')
            item.fail('synthetic_interruption', RuntimeError('synthetic'), state='state_01')
            view, package = records(item, 'empirical_failure')
            validate_cross_file_package(journal_path=item.journal.path, expected_head=item.journal.previous,
                                        mode='empirical_failure', qc=package[0], manifest=package[1],
                                        evidence=package[2], report=package[3])
            mutations = {'edges_opened': 0, 'unresolved_exposed_edges': 0, 'field_evaluations_completed': 1}
            for field, replacement in mutations.items():
                altered = copy.deepcopy(package)
                altered[0]['progress_authority']['snapshot']['counters'][field] = replacement
                with self.subTest(field=field), self.assertRaises(LifecycleError):
                    validate_cross_file_package(journal_path=item.journal.path, expected_head=item.journal.previous,
                                                mode='empirical_failure', qc=altered[0], manifest=altered[1],
                                                evidence=altered[2], report=altered[3])
            self.assertEqual(view['snapshot']['counters']['edges_opened'], 2)
            item.close()

    def test_pre_access_requires_confirmed_zero_and_no_attempt_uncertainty(self):
        with tempfile.TemporaryDirectory() as directory:
            item = authority(Path(directory)); item.block('synthetic_stop', 'no_access')
            progress_view(item.journal.path, expected_head=item.journal.previous, mode='pre_access')
            item.close()
        with tempfile.TemporaryDirectory() as directory:
            item = authority(Path(directory)); item.begin_projection('state_01'); item.fail('interrupted', RuntimeError())
            with self.assertRaisesRegex(LifecycleError, 'pre_access_not_confirmed_zero'):
                progress_view(item.journal.path, expected_head=item.journal.previous, mode='pre_access')
            item.close()

    def test_no_empirical_or_numerical_routes(self):
        import defensive_network_disruption.validation.projection_exposure as module
        public = set(vars(module))
        for forbidden in ('evaluate_edge', 'project_line', 'load_model', 'fit', 'acquire', 'target'):
            self.assertNotIn(forbidden, public)


if __name__ == '__main__':
    unittest.main()
