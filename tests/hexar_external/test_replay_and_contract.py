"""Focused evidence-boundary regression tests, not comparative endpoint labels."""
import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'analysis/hexar_external'))
from replay import objects,dispatch,replay
from build_development import transform,packet,PATTERN
from contract_adapter import contract_answer

class BoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.events=json.loads((ROOT/'data/hexar_external/extracted/bagfile_6_1.json').read_text())['events']
    def test_removal_closure_and_no_cached_state(self):
        intact,s0,_=packet(self.events,'What happened?','intact')
        masked,s1,_=packet(self.events,'What happened?','decisive_removal')
        self.assertIs(s0['is_joystick_manual'],True)
        self.assertIsNone(s1['is_joystick_manual'])
        self.assertEqual(masked['evidence']['manual_state'],[])
        self.assertEqual(intact['task_window'],masked['task_window'])
        self.assertEqual(intact['evidence']['navigation_outcomes'],masked['evidence']['navigation_outcomes'])
        retained,_=transform(self.events,'decisive_removal')
        self.assertFalse(any(e['topic']=='/joy_priority' for e in retained))
        self.assertFalse(any(PATTERN.search(json.dumps(e['value'])) for e in retained if e['topic']=='/rosout'))
    def test_irrelevant_removal_is_identical(self):
        a,sa,_=packet(self.events,'What happened?','intact')
        b,sb,_=packet(self.events,'What happened?','irrelevant_removal')
        self.assertEqual(a,b);self.assertEqual(sa['llm_request'],sb['llm_request'])
    def test_mask_physical_events_only_removed_never_fabricated(self):
        original={e['event_id']:e for e in self.events}
        for mode in ('intact','irrelevant_removal','decisive_removal'):
            retained,_=transform(self.events,mode)
            self.assertTrue(all(e==original[e['event_id']] for e in retained))
    def test_missing_not_false_and_final_state_outside_window(self):
        nav,skill=objects()
        self.assertIsNone(nav.is_joystick_manual)
        dispatch(nav,skill,{'recorded_ns':1,'topic':'/joy_priority','value':{'data':True}})
        self.assertIs(nav.is_joystick_manual,True)
        # Upstream injects latest override even when the logs' requested window excludes it.
        nav.generate_explanation('Why?',100,200)
        self.assertIn('joystick is in manual mode',nav.llm_client.requests[-1]['messages'][1]['content'])
    def test_covariance_counter_is_not_reset_by_low_samples(self):
        nav,skill=objects()
        low=[0.]*36;high=[0.]*36;high[0]=high[7]=.3
        for _ in range(10):dispatch(nav,skill,{'recorded_ns':1,'topic':'/amcl_pose','value':{'covariance':low}})
        for _ in range(6):dispatch(nav,skill,{'recorded_ns':2,'topic':'/amcl_pose','value':{'covariance':high}})
        self.assertEqual(nav.high_localization_variance_count,-4)
        self.assertEqual(nav.logs,[])
    def test_log_skip_dedupe_and_unpadded_clock(self):
        nav,skill=objects()
        def log(msg):dispatch(nav,skill,{'recorded_ns':2_000_000_005,'topic':'/rosout','value':{'name':'controller_server','msg':msg,'level':20}})
        log('Failed to make progress');log('Failed to make progress');log('Optimizer reset')
        self.assertEqual(len(nav.logs),1)
        self.assertEqual(nav.logs[0]['timestamp'],'2.5')
        self.assertEqual(nav.get_relevant_logs(2.0,2.1),[])
    def test_pinned_core_support_and_useful_partial_preservation(self):
        for mode in ('intact','decisive_removal'):
            p,_,_=packet(self.events,'What happened?',mode)
            c=contract_answer(p,'test-'+mode)
            self.assertIn('claim-timeout',c['diagnosis']['approved_claim_ids'])
            self.assertNotIn('claim-physical',c['diagnosis']['approved_claim_ids'])
            self.assertEqual('claim-manual' in c['diagnosis']['approved_claim_ids'],mode=='intact')
            self.assertLessEqual(len(c['answer'].split()),60)
            self.assertIn('timed out',c['answer'])
            self.assertEqual(c['realization']['audit']['missing_required_claim_ids'],())
if __name__=='__main__':unittest.main()
