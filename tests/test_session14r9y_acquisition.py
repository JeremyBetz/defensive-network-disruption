import copy, json, tempfile, unittest
from fractions import Fraction as F
from pathlib import Path
from defensive_network_disruption.geometry import r9y_acquisition as a
from defensive_network_disruption.geometry.r9x_terminal_authority import load_authority, canonical, digest
from defensive_network_disruption.validation import r9y_evidence as e

ROOT=Path(__file__).resolve().parents[1]

class R9YTests(unittest.TestCase):
    def selected(self):
        return {"alias":"synthetic","carrier":[0.,0.],"receiver":[2.,0.],
                "defenders":[[1.,1.],[1.,-1.],[2.,2.]]}
    def lineage(self):
        depths=list(range(1,80))+[80,80]
        depths.insert(36,depths.pop(-1))
        cells=[{"ordinal":i,"depth":depth,"pair_status":"equal","maximum_status":"maximum"}
               for i,depth in enumerate(depths)]
        cells[36]["maximum_status"]="unresolved"
        return {"cells":cells,"ordered_partition_sha256":"1"*64,"boundary_capture_sha256":"2"*64,"selected_edge_sha256":"3"*64}
    def test_exact_coefficients(self):
        c=a.coefficients([0.,0.],[2.,0.],[1.,1.])
        self.assertEqual((c.q,c.dot,c.cross2),(F(2),F(2),F(4)))
    def test_acquire_round_trip_without_classification(self):
        lineage=self.lineage()
        boundary={"plateau":{"pair":[0,1],"index":0,"end":1,"grid":[0.,1.]}}
        value=a.acquire(lineage=lineage,boundary=boundary,selected=self.selected(),
            private_index_sha256="4"*64,reference_implementation_sha256="5"*64)
        cell,pair,competitors=load_authority(copy.deepcopy(value))
        self.assertEqual((cell["ordinal"],cell["depth"]),(36,80))
        self.assertEqual(len(pair),2); self.assertEqual(len(competitors),1)
        self.assertEqual(canonical(value),canonical(copy.deepcopy(value)))

    def test_lineage_hashes_order_and_unresolved_identity(self):
        with tempfile.TemporaryDirectory(dir=ROOT/"outputs") as tmp:
            folder=Path(tmp); files={"boundary_capture.json":"1"*64,"selected_edge.json":"2"*64}
            for item in self.lineage()["cells"]:
                path=folder/f"reference_reference_cell_{item['ordinal']:03d}.json"
                path.write_bytes(canonical(item)); files[path.name]=digest(path.read_bytes())
            (folder/"private_index.json").write_bytes(canonical({"schema_version":1,"files":files}))
            result=a.load_lineage(folder,expected_index_sha256=digest((folder/"private_index.json").read_bytes()))
            self.assertEqual(len(result["cells"]),81)
            changed=json.loads((folder/"private_index.json").read_text()); changed["files"].pop("reference_reference_cell_080.json")
            (folder/"private_index.json").write_bytes(canonical(changed))
            with self.assertRaises(ValueError): a.load_lineage(folder,expected_index_sha256=digest((folder/"private_index.json").read_bytes()))
    def test_output_contract_and_tamper(self):
        with tempfile.TemporaryDirectory(dir=ROOT/"outputs") as tmp:
            folder=Path(tmp); local=folder/"local"; local.mkdir()
            (local/"terminal_cell_authority.json").write_text('{}\n')
            records={name:{"schema_version":1,"status":"complete","flags":{"ok":True},"counts":{"n":1}}
                     for name in e.NAMES[:-2]}
            qc={"status":"complete","execution_valid":True,"classification":"A","readiness":1,
                "previously_exposed_states_reopened":1,"previously_exposed_edges_reopened":1,
                "new_population_states":0,"new_population_edges":0,"field_evaluations":0,
                "refinement_performed":False,"classification_performed":False}
            self.assertTrue(e.close(folder,records,qc)["valid"])
            value=json.loads((folder/"qc.json").read_text()); value["field_evaluations"]=1
            (folder/"qc.json").write_text(json.dumps(value)+'\n')
            with self.assertRaises(ValueError): e.publication_check(folder)
    def test_runner_contains_no_bound_or_classification_call(self):
        source=(Path(__file__).parents[1]/"scripts/session_14r9y_terminal_cell_authority_acquisition.py").read_text()
        for token in ("classify_terminal(",".bounds(","evaluate_edge(","prepared.jsonl","provider"):
            self.assertNotIn(token,source)

    def test_runner_uses_capture_tool_sidecar_and_preserves_old_receipt(self):
        source=(ROOT/"scripts/session_14r9y_terminal_cell_authority_acquisition.py").read_text()
        self.assertIn('receipt=local/"checkpoint_ci_v2.json"',source)
        self.assertIn('sidecar=local/"checkpoint_ci_v2.json.sha256"',source)
        self.assertNotIn('sidecar=local/"checkpoint_ci.sha256"',source)

if __name__=="__main__": unittest.main()
