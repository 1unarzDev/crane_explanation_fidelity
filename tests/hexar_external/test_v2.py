import importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis/hexar_external'))
from study_v2 import transform,contract,primitive_bindings,V2
class UniversalClosure(unittest.TestCase):
 def test_missing_not_false_and_no_alias(self):
  events=[{'event_id':'a','topic':'/joy_priority','value':{'data':True}}, {'event_id':'b','topic':'/rosout','value':{'name':'controller_server','msg':'Manual mode prevented motion'}}, {'event_id':'c','topic':'/rosout','value':{'name':'skill_navigate_to_zone','msg':'Skill completed successfully'}}]
  kept,removed,fields=transform(events,'diagnostic_removal');self.assertEqual([e['event_id'] for e in kept],['c']);self.assertEqual(removed,['a','b'])
 def test_every_development_packet_closure_and_core(self):
  packets=json.loads((V2/'development/packets.json').read_text())['packets']
  self.assertEqual(len(packets),54)
  for p in packets:
   c=contract(p['method_packet'],p['job_id'],p['recording_id']);self.assertLessEqual(len(c['answer'].split()),60)
   if p['condition']=='diagnostic_removal':
    refs=primitive_bindings(p['method_packet']);self.assertFalse(any(refs[k] for k in ('manual','charging','uncertainty','planner','progress','physical')))
    self.assertTrue(p['method_packet']['evidence']['navigation_outcomes'])
 def test_removal_preserves_explicit_outcome_only(self):
  t={'task_error_msg':'Joystick caused timeout','skill_sequence':[{'error_msg':'The skill has timed out'},{'error_msg':'obstacle collision'}]}
  e={'event_id':'x','topic':'/task_info','value':{'data':json.dumps(t)}}
  kept,_,fields=transform([e],'diagnostic_removal');got=json.loads(kept[0]['value']['data'])
  self.assertIsNone(got['task_error_msg']);self.assertEqual(got['skill_sequence'][0]['error_msg'],'The skill has timed out');self.assertIsNone(got['skill_sequence'][1]['error_msg'])
if __name__=='__main__':unittest.main()
