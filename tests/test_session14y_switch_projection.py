from __future__ import annotations
import json, unittest
from defensive_network_disruption.geometry.verification_repair import VerifiedSwitch
from defensive_network_disruption.geometry.switch_diagnostic_projection import project_verified_switch

class Session14ySwitchProjectionTests(unittest.TestCase):
    def switch(self, **changes):
        values=dict(location=.5,owners_before=(0,),owners_at=(0,1),owners_after=(1,),
                    crossing_pairs=((0,1),),endpoint=False,multiway=False,envelope_value=.75)
        values.update(changes); return VerifiedSwitch(**values)
    def test_real_schema_and_old_failure(self):
        switch=self.switch()
        self.assertFalse(hasattr(switch,'left_owners')); self.assertFalse(hasattr(switch,'right_owners'))
        self.assertEqual(tuple(project_verified_switch(switch))[1:4],('owners_before','owners_at','owners_after'))
    def test_owner_states_multiway_ownerless_and_identical(self):
        cases=(self.switch(),self.switch(owners_at=(2,0,1),multiway=True),
               self.switch(owners_before=(),owners_at=(0,),owners_after=(0,)),
               self.switch(owners_before=(1,),owners_at=(1,),owners_after=(1,)))
        for switch in cases:
            with self.subTest(switch=switch):
                record=project_verified_switch(switch)
                self.assertEqual(record['owners_at'],sorted(record['owners_at']))
                self.assertEqual(json.dumps(record,sort_keys=True),json.dumps(project_verified_switch(switch),sort_keys=True))
    def test_permutation_mapping(self):
        record=project_verified_switch(self.switch(),(1,0))
        self.assertEqual(record['owners_before'],[1]); self.assertEqual(record['owners_after'],[0])
        self.assertEqual(record['crossing_pairs'],[[0,1]])

if __name__=='__main__': unittest.main()
