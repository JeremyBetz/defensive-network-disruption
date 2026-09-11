import math
import unittest
from dataclasses import FrozenInstanceError

from defensive_network_disruption.networks.options import OptionState, FrozenOptionModel, evaluate_options
from defensive_network_disruption.networks.defender_edges import map_defender_edges, summarize_edge_involvement
from defensive_network_disruption.visualization.defender_edges import synthetic_defender_edge_svg
from defensive_network_disruption.validation.ranking_features import M1_NAMES


class DefenderEdgeTests(unittest.TestCase):
    def state(self, defenders=((5, 0), (18, -9), (18, 9), (-7, 4))):
        return OptionState((0, 0), ("A", "B", "C", "D"),
                           ((20, -10), (25, 0), (20, 10), (-10, 5)), defenders)

    def model(self):
        return FrozenOptionModel("m1", M1_NAMES, (0,)*5, (1,)*5, (-.1,.1,0,.1,.1))

    def test_distances_and_m1_minima(self):
        state=self.state(); mapping=map_defender_edges(state)
        rows=mapping.for_receiver(0)
        self.assertAlmostEqual(rows[1].receiver_distance, math.sqrt(5))
        self.assertEqual(rows[0].segment_distance, 5/math.sqrt(5))

    def test_ties_fractional_membership_and_conservation(self):
        state=OptionState((0,0),("A",),((10,0),),((5,1),(5,-1),(20,20)))
        mapping=map_defender_edges(state); rows=mapping.for_receiver(0)
        self.assertEqual(rows[0].segment_rank,1.5)
        self.assertEqual(rows[0].membership("segment",1),.5)
        for k in (1, 2, 3):
            self.assertEqual(sum(r.membership("segment",k) for r in rows),min(k,3))
        summary=summarize_edge_involvement(mapping,network=evaluate_options(state,model=self.model()))
        self.assertAlmostEqual(sum(x["segment_top2_m1_weighted"] for x in summary["defender_summaries"].values()),2)

    def test_near_tie_uses_absolute_anchor(self):
        state=OptionState((0,0),("A",),((10,0),),((5,1),(5,1+5e-13),(5,1+1.4e-12)))
        rows=map_defender_edges(state).for_receiver(0)
        self.assertEqual((rows[0].segment_rank,rows[1].segment_rank),(1.5,1.5))
        self.assertEqual(rows[2].segment_rank,3)

    def test_same_defender_can_be_nearest_to_multiple_edges(self):
        mapping=map_defender_edges(OptionState((0,0),("A","B"),((10,-2),(10,2)),((5,0),(20,20))))
        summary=summarize_edge_involvement(mapping)
        self.assertEqual(summary["defender_summaries"][0]["segment_nearest_edges"],2)

    def test_permutations_preserve_geometry(self):
        a=map_defender_edges(self.state())
        b=map_defender_edges(self.state(tuple(reversed(self.state().defender_xy))))
        da=sorted((r.receiver_id,r.receiver_distance,r.segment_distance) for r in a.relations)
        db=sorted((r.receiver_id,r.receiver_distance,r.segment_distance) for r in b.relations)
        self.assertEqual(da,db)

    def test_coincident_defenders_preserved(self):
        m=map_defender_edges(self.state(((5,0),(5,0))))
        self.assertEqual(m.defender_count,2)
        self.assertEqual(len(m.relations),8)

    def test_immutable_and_alignment(self):
        mapping=map_defender_edges(self.state())
        with self.assertRaises(FrozenInstanceError): mapping.defender_count=9
        bad=evaluate_options(OptionState((0,0),("Z",),((1,0),),((0,1),)),model=self.model())
        with self.assertRaises(ValueError): summarize_edge_involvement(mapping,network=bad)

    def test_invalid_inputs(self):
        with self.assertRaises(TypeError): map_defender_edges(object())
        with self.assertRaises(ValueError): OptionState((0,0),("A",),((1,0),),())

    def test_synthetic_render_is_deterministic(self):
        a=synthetic_defender_edge_svg()
        self.assertEqual(a,synthetic_defender_edge_svg())
        self.assertIn("NOT SUPPRESSION",a)
        self.assertIn('<svg',a)


if __name__ == "__main__": unittest.main()
