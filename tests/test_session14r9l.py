"""Pre-access contract tests for Session 14R9L."""
import importlib.util, pathlib, tempfile, unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('r9l',ROOT/'scripts/session_14r9l_empirical_representation_retry.py')
R=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(R)
class R9LTests(unittest.TestCase):
 def test_surface_and_fresh_namespace(self):
  self.assertEqual(R.OUT,pathlib.Path('outputs/continuous_occlusion_empirical_retry_r9l'))
  self.assertEqual(R.main.__name__,'main')
 def test_explicit_repaired_evaluator(self):
  self.assertEqual(R.evaluate_edge.__module__,'defensive_network_disruption.geometry.r9k_comparator')
 def test_linear_publisher_only(self):
  self.assertEqual(R.linear_review.__module__,'defensive_network_disruption.validation.r9j_linear_publication')
  self.assertNotIn('derive_progress',R.__dict__)
 def test_direct_entry_guard(self):
  old=R.PROGRESS;R.PROGRESS=None
  try:
   with self.assertRaises(PermissionError):R.calculate_edge('isotropic',(0,0),(1,0),((0,1),),'x',0,0)
  finally:R.PROGRESS=old
 def test_failure_before_progress_is_preserved(self):
  with tempfile.TemporaryDirectory(dir=ROOT) as d:
   rel=pathlib.Path(d).relative_to(ROOT);old_out,old_local=R.OUT,R.LOCAL
   R.OUT,R.LOCAL=rel,rel/'local'
   try:
    R.close_failure('startup',RuntimeError('synthetic'))
    self.assertTrue((ROOT/R.LOCAL/'emergency_failure.json').is_file())
   finally:R.OUT,R.LOCAL=old_out,old_local
if __name__=='__main__':unittest.main()
