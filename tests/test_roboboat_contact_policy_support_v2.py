import copy
import json
from pathlib import Path
import pytest
from run_roboboat_contact_policy_support_v2 import partial_answerability

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'artifacts/roboboat-contact-policy-comparison-v2/batches/opaque-contact-policy-v2-567294030d66c3b8/method_packets'


def packet(level='L2'):return json.loads((P/f'{level}.json').read_text())


def test_independent_answerability_selects_only_observed_compliant_interval():
    assert [partial_answerability(packet(l)) for l in ('L0','L1','L2')]==[False,False,True]


@pytest.mark.parametrize('mode',['gap','short','velocity','violation'])
def test_positive_unit_not_required_without_complete_supported_partial_compliance(mode):
    p=packet()
    if mode=='gap':del p['post_result'][10:40]
    elif mode=='short':p['post_result']=p['post_result'][:100]
    elif mode=='velocity':p['post_result'][20].pop('velocity')
    else:p['post_result'][20]['x']+=2
    assert not partial_answerability(p)


def test_evaluator_isolation_never_injects_contact_truth_into_method_packet():
    p=packet();before=copy.deepcopy(p)
    assert partial_answerability(p)
    assert p==before and 'contacts' not in p


def test_late_position_violation_does_not_remove_fixed_dwell_answerability():
    p=packet();p['post_result'][350]['x']+=2
    assert partial_answerability(p)
