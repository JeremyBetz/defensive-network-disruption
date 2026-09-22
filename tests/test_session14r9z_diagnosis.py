import copy, json, tempfile, unittest
from pathlib import Path
from defensive_network_disruption.validation import r9z_diagnosis as d

ROOT=Path(__file__).resolve().parents[1]
class R9ZTests(unittest.TestCase):
    def _metadata_fixture(self, folder):
        values={
            "original_failure.json":{"stage":"authority_construction","exception_type":"ValueError","message":"pair_authority","traceback_status":"unavailable_due_runner_capture_defect"},
            "lineage_receipt.json":{"cells":81,"ordered_partition_sha256":"a"*64,"private_index_sha256":"b"*64},
            "materialization_receipt.json":{"attempt_sha256":"c"*64,"selected_edge_sha256":"d"*64},
        }
        hashes={}
        for name,value in values.items():
            path=folder/name; path.write_bytes(d.canonical(value)); hashes[name]=d.sha(path)
        (folder/"private_index.json").write_bytes(d.canonical({"schema_version":1,"files":hashes}))
    def test_pair_semantics(self):
        rows=d.synthetic_controls(); self.assertEqual(len(rows),5); self.assertTrue(all(x["passed"] for x in rows))
        self.assertEqual(rows[1]["observed"],"common_inactive_branch")
        self.assertEqual(rows[3]["observed"],"unresolved_tolerance_only")
    def test_distinct_ordered_references_are_deterministic(self):
        a=d.coefficient(1,2,3); b=d.coefficient(1,4,5)
        x=d.pair_record(a,b,"unresolved_distinct")
        self.assertEqual(d.canonical(x),d.canonical(copy.deepcopy(x))); self.assertEqual(len(set(x["pair"])),2)
        self.assertNotEqual(d.digest(d.pair_record(a,b,"unresolved_distinct")),d.digest(d.pair_record(b,a,"unresolved_distinct")))
    def test_synthetic_failure_capture(self):
        value=d.synthetic_failure("authority_construction")
        self.assertTrue(value["captured_before_closure"]); self.assertEqual(len(value["traceback_sha256"]),64)
    def test_source_and_retained_metadata_diagnosis(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp); self._metadata_fixture(folder)
            value=d.inspect(ROOT,folder)
            self.assertTrue(value["pair_established"]); self.assertTrue(value["failure_established"])
            self.assertFalse(value["traceback_available"])
            self.assertTrue(value["blocked_qc_constructed_before_reraise"])
            index=json.loads((folder/"private_index.json").read_text()); index["files"]["original_failure.json"]="0"*64
            (folder/"private_index.json").write_bytes(d.canonical(index))
            with self.assertRaises(ValueError): d.inspect(ROOT,folder)
    def test_publication_and_tamper(self):
        with tempfile.TemporaryDirectory(dir=ROOT/"outputs") as tmp:
            folder=Path(tmp); local=folder/"local"; local.mkdir(); (local/"x.json").write_text("{}\n")
            records={name:{"schema_version":1,"status":"complete","flags":{"ok":True},"counts":{"n":1}}
                     for name in d.NAMES[:3]+d.NAMES[4:5]}
            rows=[{"control":"x","expected":"x","observed":"x","ordered":True,"retains_both":True,"passed":True}]
            neg=[{"control":"x","expected":"blocked","observed":"blocked","passed":True}]
            qc={"status":"complete","execution_valid":True,"classification":"A","readiness":1,"pair_defect_established":True,"traceback_defect_established":True,"states_reopened":0,"edges_reopened":0,"empirical_computations":0}
            self.assertTrue(d.close(folder,records,rows,neg,qc)["valid"])
            value=json.loads((folder/"qc.json").read_text()); value["states_reopened"]=1; (folder/"qc.json").write_text(json.dumps(value)+"\n")
            with self.assertRaises(ValueError): d.publication_check(folder)
    def test_runner_tripwires(self):
        source=(ROOT/"scripts/session_14r9z_pair_authority_failure_evidence_diagnosis.py").read_text()
        for token in ("selected_edge.json","boundary_capture.json","prepared.jsonl","classify_terminal(",".bounds(","evaluate_edge("):
            self.assertNotIn(token,source)
if __name__=="__main__": unittest.main()
