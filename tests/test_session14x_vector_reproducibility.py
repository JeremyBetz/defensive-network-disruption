from __future__ import annotations
import base64, hashlib, math, struct, unittest
from defensive_network_disruption.geometry.vector_reproducibility import component_record, extract_log_envelope, float_bits, signed_zero, ulp_distance

class Session14xVectorTests(unittest.TestCase):
    def test_bits_ulp_and_signed_zero(self):
        self.assertEqual(float_bits(1.0),"3ff0000000000000")
        self.assertEqual(ulp_distance(1.0,math.nextafter(1.0,math.inf)),1)
        self.assertEqual(ulp_distance(-0.0,0.0),0)
        self.assertEqual(signed_zero(-0.0),"negative")
        self.assertEqual(signed_zero(0.0),"positive")
        self.assertIsNone(ulp_distance(math.inf,1.0))
    def test_component_record(self):
        row=component_record("union",1.0,math.nextafter(1.0,math.inf))
        self.assertEqual(tuple(row)[:3],("component","expected","actual"))
        self.assertEqual(row["ulp_distance"],1); self.assertFalse(row["bitwise_equal"])
    def test_exact_log_envelope(self):
        raw=b'{"safe":true}\n'; sha=hashlib.sha256(raw).hexdigest(); payload=base64.b64encode(raw).decode()
        text=f"prefix\nSESSION14X_DIAGNOSTIC_BEGIN {sha} {payload}\nSESSION14X_DIAGNOSTIC_END\n"
        self.assertEqual(extract_log_envelope(text),raw)
        with self.assertRaises(ValueError): extract_log_envelope(text+text)
    def test_no_private_schema_terms(self):
        source=__import__('pathlib').Path(__file__).parents[1].joinpath('scripts/session_14x_cross_platform_vector_reproducibility.py').read_text()
        for term in ('population.jsonl','prepared.jsonl','target_rank','option_share','acquire-reserved'):
            self.assertNotIn(term,source)

if __name__=='__main__': unittest.main()
