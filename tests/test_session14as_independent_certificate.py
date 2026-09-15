from dataclasses import asdict, replace
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest

from defensive_network_disruption.validation import independent_certificate_verifier as v


ROOT = Path(__file__).resolve().parents[1]


class Session14asCertificateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.certificate, cls.observation, cls.authority = v.load_session14ar_certificate(ROOT)

    def test_session14ar_exact_regression(self):
        c, o = self.certificate, self.observation
        self.assertEqual((o.estimate, c.lower_bound, c.upper_bound),
                         (0.21369535129415176, 0.21369535129402328, 0.21369535131181636))
        self.assertEqual(c.upper_bound-c.lower_bound, 1.7793072570881918e-11)
        result = v.certify_warning(o, c)
        self.assertEqual(result.status, v.SUCCESS_STATUS)
        self.assertEqual(result.estimate, o.estimate)
        self.assertEqual(result.adaptive_warning_count, 1)

    def test_width_boundary(self):
        base = 0.0
        for width, accepted in ((math.nextafter(v.AGREEMENT, 0.0), True),
                                (v.AGREEMENT, True),
                                (math.nextafter(v.AGREEMENT, math.inf), False)):
            c = replace(self.certificate, lower_bound=base, upper_bound=width)
            o = replace(self.observation, estimate=width/2)
            if accepted:
                self.assertEqual(v.certify_warning(o, c).status, v.SUCCESS_STATUS)
            else:
                with self.assertRaisesRegex(v.CertificateError, "certificate_too_wide"):
                    v.certify_warning(o, c)

    def test_exact_authority_mismatches(self):
        mappings = {
            "interval_identity":"other", "left_endpoint_binary64":"0"*16,
            "right_endpoint_binary64":"f"*16, "field_family":"expanding",
            "frozen_parameters":(("sigma_metres", 3.0),), "combination":"union",
            "integrand_specification_hash":"0"*64,
            "structural_partition_authority_hash":"0"*64,
            "method_id":"other", "provenance_hash":"0"*64,
            "governing_tolerance":1e-9,
        }
        for name, value in mappings.items():
            with self.subTest(name=name), self.assertRaisesRegex(v.CertificateError, "authority_mismatch"):
                v.certify_warning(self.observation, replace(self.certificate, **{name:value}))

    def test_request_mismatches_block(self):
        for name, value in {
            "interval_identity":"other", "left_endpoint_binary64":"0"*16,
            "field_family":"expanding", "frozen_parameters":(("sigma_metres",3.0),),
            "combination":"union", "integrand_specification_hash":"0"*64,
            "structural_partition_authority_hash":"0"*64, "method_id":"other",
            "provenance_hash":"0"*64, "governing_tolerance":1e-9,
        }.items():
            with self.subTest(name=name):
                request=replace(self.observation.request, **{name:value})
                with self.assertRaises(v.CertificateError):
                    v.certify_warning(replace(self.observation,request=request),self.certificate)

    def test_certificate_failures(self):
        with self.assertRaisesRegex(v.CertificateError,"certificate_unavailable"):
            v.certify_warning(self.observation,None)
        for item in (replace(self.certificate,lower_bound=.3,upper_bound=.2),
                     replace(self.certificate,lower_bound=math.nan),
                     replace(self.certificate,upper_bound=math.inf),
                     replace(self.certificate,method_id="unapproved"),
                     replace(self.certificate,source_manifest_sha256="0"*64),
                     replace(self.certificate,authority_sha256="0"*64),
                     replace(self.certificate,method_authority_hash="0"*64),
                     replace(self.certificate,independence_statement="unapproved")):
            with self.assertRaises(v.CertificateError):v.certify_warning(self.observation,item)
        outside=replace(self.observation,estimate=self.certificate.upper_bound+1e-8)
        with self.assertRaisesRegex(v.CertificateError,"estimate_outside"):
            v.certify_warning(outside,self.certificate)

    def test_warning_restrictions_and_fail_closed_states(self):
        for field,value in (("warning_class","RuntimeWarning"),("warning_message_sha256","0"*64)):
            with self.assertRaisesRegex(v.CertificateError,"ineligible_warning"):
                v.certify_warning(replace(self.observation,**{field:value}),self.certificate)
        for reason in ("exception","discontinuity","root_failure","partition_failure","automatic_certificate_generation"):
            with self.assertRaisesRegex(v.CertificateError,"blocking_piece"):
                v.aggregate_pieces([v.blocking_piece(reason)])

    def test_four_branches_and_outward_aggregation(self):
        ordinary=v.ordinary_piece(.25)
        micro=v.micro_residual_piece(0.0,1e-15,0.0)
        certified=v.certify_warning(self.observation,self.certificate)
        result=v.aggregate_pieces((ordinary,micro,certified))
        self.assertEqual((result["ordinary_piece_count"],result["micro_residual_piece_count"],
                          result["certificate_piece_count"]),(1,1,1))
        self.assertEqual(result["outward_rounding_levels"],1)
        self.assertLess(result["aggregate_lower"],math.fsum((ordinary.lower,micro.lower,certified.lower)))
        self.assertGreater(result["aggregate_upper"],math.fsum((ordinary.upper,micro.upper,certified.upper)))
        self.assertEqual(result["production_estimate"],math.fsum((ordinary.estimate,micro.estimate,certified.estimate)))

    def test_readiness_is_derived_and_typed(self):
        names=[f.name for f in v.fields(v.ProspectiveVerificationReadiness)]
        values={name:(0 if name=="uncertified_blocking_warning_count" else True) for name in names}
        gate=v.ProspectiveVerificationReadiness(**values)
        self.assertTrue(gate.ready)
        with self.assertRaises(TypeError):v.ProspectiveVerificationReadiness(**{**values,"integrity_valid":1})
        self.assertNotIn("ready",asdict(gate))
        for name in names:
            if name=="uncertified_blocking_warning_count":continue
            self.assertFalse(v.ProspectiveVerificationReadiness(**{**values,name:False}).ready)

    def test_deterministic_certificate_serialization(self):
        first=v.canonical(v.certificate_record(self.certificate))
        second=v.canonical(v.certificate_record(self.certificate))
        self.assertEqual(first,second)

    def test_no_empirical_or_certificate_generation_routes(self):
        source=(ROOT/"src/defensive_network_disruption/validation/independent_certificate_verifier.py").read_text()
        for forbidden in ("project_line", "population.jsonl", "quad(", "taylor_enclosure(", "load_model", "target_index"):
            self.assertNotIn(forbidden,source)

    def test_runner_oracles_and_marker(self):
        path=ROOT/"scripts/session_14as_independent_certificate_contract.py"
        spec=importlib.util.spec_from_file_location("session14as_runner_test",path)
        runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
        self.assertTrue(all(row["passed"] for row in runner.positive_oracles(self.certificate,self.observation)))
        negatives=runner.negative_oracles(self.certificate,self.observation)
        self.assertGreaterEqual(len(negatives),25)
        self.assertTrue(all(row["passed"] for row in negatives))
        with tempfile.TemporaryDirectory() as directory:
            marker=Path(directory)/"marker"
            runner.create_once(marker,{"session":"synthetic"})
            with self.assertRaises(FileExistsError):runner.create_once(marker,{"session":"synthetic"})

    def test_public_root_exports_unchanged(self):
        import defensive_network_disruption as package
        self.assertEqual(len(package.__all__),10)
        self.assertNotIn("IndependentIntegralCertificate",package.__all__)


if __name__ == "__main__":
    unittest.main()
