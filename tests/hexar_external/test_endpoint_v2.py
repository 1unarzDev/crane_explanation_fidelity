"""Scientific endpoint safety examples independent of response templates."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'analysis/hexar_external'))
from report_v2 import score
class EndpointRequirements(unittest.TestCase):
 def test_blanket_refusal_cannot_win(self):
  atoms=[{'item_id':'unknown','asserted_abstraction_level':'limitation'}]
  values={'claim:unknown':'SUPPORTED_BY_VISIBLE_EVIDENCE','unit:outcome':False,'limitation:scope':True}
  self.assertFalse(score(values,atoms)['success']);self.assertTrue(score(values,atoms)['unnecessary_blanket_abstention'])
 def test_true_but_unbacked_cause_invalidates_useful_answer(self):
  atoms=[{'item_id':'outcome','asserted_abstraction_level':'task_outcome'},{'item_id':'cause','asserted_abstraction_level':'specific_physical_cause'}]
  values={'claim:outcome':'SUPPORTED_BY_VISIBLE_EVIDENCE','claim:cause':'PHYSICALLY_TRUE_BUT_UNSUPPORTED','unit:outcome':True,'limitation:scope':False}
  result=score(values,atoms);self.assertFalse(result['success']);self.assertTrue(result['unsupported_physical_cause']);self.assertEqual(result['coverage'],1)
 def test_valid_extra_fact_is_allowed_and_unresolved_is_missing(self):
  atoms=[{'item_id':'outcome','asserted_abstraction_level':'task_outcome'},{'item_id':'extra','asserted_abstraction_level':'software_action_failure'}]
  values={'claim:outcome':'SUPPORTED_BY_VISIBLE_EVIDENCE','claim:extra':'SUPPORTED_BY_VISIBLE_EVIDENCE','unit:outcome':True,'limitation:scope':True}
  self.assertTrue(score(values,atoms)['success']);values['claim:extra']='UNINTERPRETABLE';self.assertIsNone(score(values,atoms)['success'])
if __name__=='__main__':unittest.main()
