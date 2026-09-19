from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from defensive_network_disruption.validation import r9o_terminal as t
from defensive_network_disruption.validation.r7_execution import Progress,Journal

class TerminalTests(unittest.TestCase):
    def test_five_actual_routes(self):
        with tempfile.TemporaryDirectory() as d:
            rows=t.controls(Path(d).resolve())
            self.assertEqual(len(rows),5);self.assertTrue(all(x['passed'] for x in rows))

    def test_rerun_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).resolve();j=Journal(root/'journal');p=Progress(j);c=t.TerminalClosure(p,root)
            try:
                try:raise RuntimeError('original')
                except RuntimeError as error:c.fail(error,'startup',lambda a,tr:t.failure_package(root/'package',a,tr))
                with self.assertRaises(FileExistsError):c.fail(RuntimeError('second'),'startup',lambda a,tr:None)
            finally:j.close()

    def test_trace_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).resolve();j=Journal(root/'journal');p=Progress(j);c=t.TerminalClosure(p,root)
            try:
                def publisher(a,tr):
                    tr.write_text('tampered')
                    return t.failure_package(root/'package',a,tr)
                with self.assertRaisesRegex(ValueError,'traceback_missing'):c.fail(RuntimeError('original'),'startup',publisher)
                self.assertTrue((root/'publication_failure.json').exists())
            finally:j.close()

    def test_one_linear_review(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).resolve();j=Journal(root/'journal');p=Progress(j);c=t.TerminalClosure(p,root)
            try:
                with patch.object(t.linear,'review',wraps=t.linear.review) as spy:
                    c.fail(RuntimeError('original'),'startup',lambda a,tr:t.failure_package(root/'package',a,tr))
                    self.assertEqual(spy.call_count,1)
            finally:j.close()

    def test_incomplete_success_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).resolve();j=Journal(root/'journal');p=Progress(j)
            try:
                with self.assertRaisesRegex(ValueError,'incomplete_success'):t.TerminalClosure(p,root).succeed(lambda a,tr:None)
            finally:j.close()
