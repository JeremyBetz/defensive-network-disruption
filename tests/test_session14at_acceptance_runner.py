import importlib.util
from pathlib import Path
import tempfile
import unittest

from defensive_network_disruption.validation import acceptance_runner as runner

ROOT=Path(__file__).resolve().parents[1]

class Session14atRunnerTests(unittest.TestCase):
    def test_package_context_import(self):
        self.assertEqual(runner.onset_owner_acceptance.__package__,"defensive_network_disruption.validation")
        self.assertTrue(callable(runner.onset_owner_acceptance.historical_regression))

    def test_historical_direct_file_failure(self):
        path=ROOT/"src/defensive_network_disruption/validation/onset_owner_acceptance.py"
        spec=importlib.util.spec_from_file_location("standalone_session14at_oracle",path)
        module=importlib.util.module_from_spec(spec)
        with self.assertRaisesRegex(ImportError,runner.HISTORICAL_IMPORT_ERROR): spec.loader.exec_module(module)

    def test_certificate_semantics_and_controls(self):
        regression,positive,negative,aggregate=runner.certificate_controls(ROOT)
        self.assertTrue(all(regression[key] for key in ("warning_retained","estimate_contained","width_accepted","certificate_accepted")))
        self.assertTrue(all(x["passed"] for x in positive));self.assertTrue(all(x["passed"] for x in negative))
        self.assertEqual(aggregate["outward_rounding_levels"],1)

    def test_failure_publication_all_stages(self):
        for stage,exc in (("package_import",ImportError(runner.HISTORICAL_IMPORT_ERROR)),("certificate_authority",RuntimeError("authority")),("synthetic_regression",RuntimeError("regression")),("publication",OSError("publication"))):
            with self.subTest(stage=stage),tempfile.TemporaryDirectory() as directory:
                out=Path(directory);marker=out/"marker";runner.create_once(marker,{"test":True})
                runner.publish_failure(out,stage,exc,["preflight"],marker)
                self.assertEqual(runner.publication_check(out,success=False)["status"],"valid_failure")

    def test_failure_schema_rejects_forgery(self):
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory);marker=out/"marker";runner.create_once(marker,{"test":True})
            runner.publish_failure(out,"package_import",ImportError("x"),[],marker)
            data=runner.verifier.strict_load(out/"failure.json");data["readiness"]=True
            (out/"failure.json").write_bytes(runner._encoded(data))
            with self.assertRaises(RuntimeError):runner.publication_check(out,success=False)

    def test_marker_collision(self):
        with tempfile.TemporaryDirectory() as directory:
            marker=Path(directory)/"marker";runner.create_once(marker,{"x":1})
            with self.assertRaises(FileExistsError):runner.create_once(marker,{"x":1})

    def test_no_empirical_routes(self):
        source=(ROOT/"src/defensive_network_disruption/validation/acceptance_runner.py").read_text()
        for forbidden in ("project_line","population.jsonl","target_index","load_model"):
            self.assertNotIn(forbidden,source)

    def test_public_api_unchanged(self):
        import defensive_network_disruption as package
        self.assertEqual(len(package.__all__),10)

if __name__=="__main__":unittest.main()
