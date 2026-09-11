from __future__ import annotations
import hashlib, importlib.util, json, tempfile, unittest
from pathlib import Path
from defensive_network_disruption.geometry.diagnostic_artifact_transport import ARTIFACT_FILENAME, ARTIFACT_NAME, diagnostic_bytes, read_verified_diagnostic, write_diagnostic

ROOT=Path(__file__).parents[1]
SPEC=importlib.util.spec_from_file_location("session14z",ROOT/"scripts/session_14z_ci_artifact_transport_and_reproducibility.py")
RUNNER=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(RUNNER)

class Session14zArtifactTransportTests(unittest.TestCase):
    def test_deterministic_roundtrip_and_hash_rejection(self):
        record={"schema_version":1,"z":[-0.0,1.25],"a":{"b":True}}
        self.assertEqual(diagnostic_bytes(record),diagnostic_bytes(record))
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/ARTIFACT_FILENAME
            size,sha=write_diagnostic(path,record)
            loaded,raw=read_verified_diagnostic(path,sha)
            self.assertEqual(loaded,record); self.assertEqual(size,len(raw)); self.assertEqual(sha,hashlib.sha256(raw).hexdigest())
            path.write_bytes(raw+b" ")
            with self.assertRaisesRegex(ValueError,"hash"): read_verified_diagnostic(path,sha)
    def test_path_and_existing_guards(self):
        with tempfile.TemporaryDirectory() as directory:
            bad=Path(directory)/"wrong.json"
            with self.assertRaisesRegex(ValueError,"path"): write_diagnostic(bad,{})
            good=Path(directory)/ARTIFACT_FILENAME; good.write_text("x")
            with self.assertRaisesRegex(ValueError,"existing"): write_diagnostic(good,{})
    def test_workflow_contract(self):
        text=(ROOT/".github/workflows/session14z-diagnostic.yml").read_text()
        self.assertIn('python-version: "3.13"',text); self.assertEqual(text.count(" ci-diagnostic "),1)
        self.assertIn("actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",text)
        self.assertIn(f"name: {ARTIFACT_NAME}",text); self.assertIn(f"path: {ARTIFACT_FILENAME}",text)
        self.assertNotIn("base64",text)
    def test_session14y_schema_validation_and_privacy(self):
        record=json.loads((ROOT/"outputs/cross_platform_vector_reproducibility_14y/local_diagnostic.json").read_text())
        RUNNER.validate_record(record)
        raw=diagnostic_bytes(record)
        self.assertLess(len(raw),2_000_000)
        for forbidden in (b"/Users/",b"/home/runner/",b"event_id",b"target_id",b"X-Amz-Signature"):
            self.assertNotIn(forbidden,raw)

if __name__=="__main__": unittest.main()
