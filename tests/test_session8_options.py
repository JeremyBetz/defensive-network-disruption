"""Synthetic checks for production Session 8 paths; no competition fixtures."""
import importlib.util
from datetime import timedelta
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from defensive_network_disruption.networks.options import (
    OptionState, FrozenOptionModel, evaluate_options, option_distribution, compare_options)
from defensive_network_disruption.data.option_adapter import MetricCoordinateContext, option_state_from_kloppy
from defensive_network_disruption.validation.ranking_features import M0_NAMES, M1_NAMES, choice_features
from defensive_network_disruption.visualization.option_svg import synthetic_options_svg

spec=importlib.util.spec_from_file_location("session8_runner",Path(__file__).parents[1]/"scripts/session_08_option_network.py")
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)


def models():
    return {"m0":FrozenOptionModel("m0",M0_NAMES,(0,)*3,(1,)*3,(-.1,.05,0)),
            "m1":FrozenOptionModel("m1",M1_NAMES,(0,)*5,(1,)*5,(-.1,.05,0,.1,.1))}


def state():
    return OptionState((0,0),("a","b","c"),((10,0),(15,4),(-4,10)),((5,1),(13,2)))


class CoreTests(unittest.TestCase):
    def test_exact_features_and_frozen_utility(self):
        s=state()
        for name,m in models().items():
            x,_=choice_features(s,name)
            n=evaluate_options(s,model=m)
            np.testing.assert_array_equal([e.utility for e in n.edges],((x-m.mean)/m.scale)@m.coefficients)
        np.testing.assert_array_equal(choice_features(s,"m0")[0],choice_features(s,"m1")[0][:,:3])

    def test_determinism_and_permutation(self):
        s=state();m=models()["m1"];a=evaluate_options(s,model=m)
        p=OptionState(s.carrier_xy,s.candidate_ids[::-1],s.candidate_xy[::-1],s.defender_xy[::-1])
        b=evaluate_options(p,model=m)
        self.assertEqual(a.to_records(),evaluate_options(s,model=m).to_records())
        self.assertEqual(a.top_options,b.top_options)
        for x,y in zip(a.edges,b.edges[::-1]):
            self.assertEqual(x,y)
        self.assertAlmostEqual(a.summary["entropy"],b.summary["entropy"])

    def test_normalization_shift_extreme_and_ties(self):
        for u in ([1,2,3],[1000,0,-1000],[0,0],[2],[-1000,-1001,0]):
            p,b,s=option_distribution(u)
            self.assertAlmostEqual(sum(p),1)
            q,c,t=option_distribution(np.asarray(u)+7)
            np.testing.assert_allclose(p,q)
            self.assertEqual(b,c)
        p,b,_=option_distribution([0,-1000,-1001])
        self.assertEqual(p[1],p[2])
        self.assertNotEqual(b["blocks"][1],b["blocks"][2])
        _,b,_=option_distribution([1,1-0.75e-12,1-1.5e-12])
        self.assertEqual(b["blocks"],[0,0,1])

    def test_uniform_singleton_concentrated(self):
        _,_,u=option_distribution([0]*4)
        self.assertAlmostEqual(u["entropy"],np.log(4))
        self.assertAlmostEqual(u["normalized_entropy"],1)
        self.assertAlmostEqual(u["effective_option_count"],4)
        _,_,s=option_distribution([5])
        self.assertEqual(s["normalized_entropy"],0)
        self.assertEqual(s["effective_option_count"],1)
        self.assertEqual(s["top_two_share"],1)
        _,_,c=option_distribution(np.log([.97,.01,.01,.01]))
        self.assertLess(c["effective_option_count"],u["effective_option_count"])

    def test_equal_leading_shares_distinct_tail(self):
        a,b=(option_distribution(np.log(p)) for p in
             ([.4,.3,.15,.1,.05],[.4,.3,.2,.075,.025]))
        self.assertEqual(a[1],b[1])
        for k in ("top_one_share","top_two_share"):
            self.assertAlmostEqual(a[2][k],b[2][k])
        self.assertNotAlmostEqual(a[2]["entropy"],b[2]["entropy"])

    def test_invalid_state_models_and_utility(self):
        for u in ([],[float("nan")],[float("inf")],[[1]]):
            with self.assertRaises(ValueError):option_distribution(u)
        for ids,points,defs in (((),(),((0,0),)),(("a","a"),((1,1),(2,2)),((0,0),)),
                               (("a",),((1,float("nan")),),((0,0),)),(("a",),((1,1),),())):
            with self.assertRaises(ValueError):OptionState((0,0),ids,points,defs)
        with self.assertRaises(ValueError):FrozenOptionModel("m2",M1_NAMES,(0,)*5,(1,)*5,(1,)*5)
        with self.assertRaises(ValueError):FrozenOptionModel("m0",M0_NAMES,(0,)*3,(0,)*3,(1,)*3)
        with self.assertRaises(ValueError):OptionState((0,0),("a",),((1,1),),((2,2),),carrier_id="a")

    def test_records_immutable_and_alignment(self):
        n=evaluate_options(state(),model=models()["m0"])
        with self.assertRaises(TypeError):n.summary["entropy"]=0
        r=n.to_records();r[0]["utility"]=9
        self.assertNotEqual(r,n.to_records())
        s=state()
        other=OptionState(s.carrier_xy,("x","b","c"),s.candidate_xy,s.defender_xy)
        with self.assertRaises(ValueError):compare_options(n,evaluate_options(other,model=models()["m1"]))


class AdapterTests(unittest.TestCase):
    def setup_frame(self):
        from kloppy.domain import Frame, Player, Team, Ground, PlayerData, Point
        home=Team("h","Home",Ground.HOME);away=Team("v","Away",Ground.AWAY)
        c,a,d=Player("c",home,1),Player("a",home,2),Player("d",away,3)
        f=Frame(None,timedelta(),[],home,None,1,
                {c:PlayerData(Point(0,0)),a:PlayerData(Point(10,4)),d:PlayerData(Point(5,2))},
                {},None)
        return f,c,a,d

    def test_real_kloppy_frame_metric_conversion(self):
        f,c,a,d=self.setup_frame()
        ctx=MetricCoordinateContext(True,"metres","centre","up",-1)
        s=option_state_from_kloppy(f,carrier=c,candidates=[a],defenders=[d],coordinate_context=ctx)
        self.assertEqual(s.candidate_xy,((-10,4),))
        self.assertEqual(s.carrier_id,"c")
        self.assertEqual(evaluate_options(s,model=models()["m1"]).summary["effective_option_count"],1)

    def test_context_selection_tracking_and_team_rejection(self):
        f,c,a,d=self.setup_frame()
        good=MetricCoordinateContext(True,"metres","centre","up",1)
        for ctx in (None,MetricCoordinateContext(False,"metres","centre","up",1),
                    MetricCoordinateContext(True,"normalized","centre","up",1)):
            with self.assertRaises(ValueError):option_state_from_kloppy(f,carrier=c,candidates=[a],defenders=[d],coordinate_context=ctx)
        for candidates,defenders in (([c],[d]),([a,a],[d]),([d],[a])):
            with self.assertRaises(ValueError):option_state_from_kloppy(f,carrier=c,candidates=candidates,defenders=defenders,coordinate_context=good)
        del f.players_data[a]
        with self.assertRaises(ValueError):option_state_from_kloppy(f,carrier=c,candidates=[a],defenders=[d],coordinate_context=good)


class RunnerTests(unittest.TestCase):
    def raw(self):
        s=state()
        return dict(match_id=runner.DEV[0],event_id="synthetic-event",
                    candidate_ids=list(s.candidate_ids),candidate_xy=s.candidate_xy,
                    carrier_xy=s.carrier_xy,defender_xy=s.defender_xy,
                    target_index="SENTINEL",target_outside={"outcome":"SENTINEL"})

    def test_projection_independence_and_firewall(self):
        r=self.raw();a=runner.projected_row(r)
        r["target_index"]=None;r["target_outside"]=False
        self.assertEqual(a,runner.projected_row(r))
        self.assertIsNone(a[2].carrier_id)
        self.assertNotIn("SENTINEL",repr(a))
        for bad in ("1874553","1953632","unknown"):
            r["match_id"]=bad
            with self.assertRaises(PermissionError):runner.projected_row(r)
        r=self.raw();r["vendor_score"]=1
        with self.assertRaises(PermissionError):runner.projected_row(r)

    def test_path_marker_and_atomic_firewall(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(runner,"ROOT",Path(tmp).resolve()),patch.object(runner,"git",return_value="synthetic"):
            with self.assertRaises(PermissionError):runner.safe("../outside")
            (Path(tmp)/"link").symlink_to("/tmp")
            with self.assertRaises(PermissionError):runner.safe("link/file")
            runner.marker()
            with self.assertRaises(FileExistsError):runner.marker()
            with self.assertRaises(PermissionError):runner.atomic(Path("other/file"),"bad")

    def test_weighting_schema_csv_and_constant_correlations(self):
        rows=[("a",state()),("b",state()),("b",state())]
        s=runner.summarize_rows(rows,models())
        runner.validate_summary(s,{"a":1,"b":2})
        self.assertEqual(s["groups"]["match_macro"]["states"],3)
        self.assertNotIn("\r",runner.csv_text(s))
        self.assertIsNone(runner.pearson([1,1],[2,3]))
        self.assertAlmostEqual(runner.pearson([1,2,3],[2,4,6]),1)
        s["unknown"]=1
        with self.assertRaises(ValueError):runner.validate_summary(s,{"a":1,"b":2})

    def test_synthetic_svg_is_deterministic(self):
        s=synthetic_options_svg(models())
        self.assertEqual(s,synthetic_options_svg(models()))
        import xml.etree.ElementTree as ET
        ET.fromstring(s)
        self.assertIn("SYNTHETIC",s)
        self.assertIn("not availability",s)
        self.assertNotIn("event",s)

    def test_no_fitting_acquisition_or_empirical_render_route(self):
        import inspect
        for fn in (runner.analyze,runner.summarize_rows,evaluate_options):
            source=inspect.getsource(fn)
            for token in ("fit(", "urlopen", "requests.", "optimizer", "read_csv"):
                self.assertNotIn(token,source)
        src=inspect.getsource(runner.render_synthetic)
        self.assertNotIn("population()",src)

    def test_analysis_lifecycle_and_failure_preservation(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(runner,"ROOT",Path(tmp).resolve()),patch.object(runner,"git",return_value="synthetic"),patch.object(runner,"ledger"):
            with patch.object(runner,"authorities",return_value=models()),patch.object(runner,"population",side_effect=ValueError("private details")):
                with self.assertRaisesRegex(RuntimeError,"stopped"):runner.analyze()
            failure=runner.load(runner.OUT/"local/failure.json")
            self.assertEqual(failure,{"stage":"analyze","category":"ValueError"})
            self.assertNotIn("private details",str(failure))
            with self.assertRaises(FileExistsError):runner.marker()

    def test_complete_synthetic_command_sequence(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(runner,"ROOT",Path(tmp).resolve()),patch.object(runner,"git",return_value="synthetic"),patch.object(runner,"ledger"),patch.object(runner,"authorities",return_value=models()):
            with patch.object(runner,"population",return_value=[(a,state()) for a in runner.ALIASES]),patch.object(runner,"COUNTS",(1,)*9),patch.object(runner,"digest",return_value="a"*64):
                runner.analyze()
                self.assertTrue(runner.safe(runner.OUT/"local/aggregate_closure.json").exists())
                runner.publication_check()
                runner.render_synthetic()
                runner.publication_check()
                self.assertTrue(runner.safe(runner.OUT/"synthetic_options.svg").exists())
                with self.assertRaises(ValueError):runner.analyze()
                with self.assertRaises(ValueError):runner.render_synthetic()

    def test_hash_gate_precedes_parsing(self):
        with patch.object(runner,"ledger"),patch.object(runner,"digest",return_value="wrong"),patch.object(runner,"projected_row") as parse:
            with self.assertRaises(ValueError):runner.population()
            parse.assert_not_called()

    def test_unequal_match_weights(self):
        a=state()
        b=OptionState((0,0),("x","y"),((2,0),(4,0)),((1,2),))
        result=runner.summarize_rows([("a",a),("b",b),("b",b),("b",b)],models())
        for model in ("m0","m1"):
            mean=(result["groups"]["a"]["models"][model]["entropy"]["mean"]+result["groups"]["b"]["models"][model]["entropy"]["mean"])/2
            self.assertAlmostEqual(result["groups"]["match_macro"]["models"][model]["entropy"]["mean"],mean)

    def test_nested_schema_and_csv_tamper(self):
        s=runner.summarize_rows([("a",state())],models())
        s["groups"]["a"]["models"]["m0"]["entropy"]["player_id"]="forbidden"
        with self.assertRaises(ValueError):runner.validate_summary(s,{"a":1})


if __name__=="__main__":
    unittest.main()
