import json
from pathlib import Path
import pytest
from audit_roboboat_launcher_terminal_v1 import assess
ROOT=Path(__file__).resolve().parents[1]
CAPTURE=ROOT/'artifacts/roboboat-tracing-overhead-v1-001/captures/boat-reliability-trace-v1-001-04'

def inputs():
    return [json.loads((CAPTURE/n).read_text()) for n in ('navigation-reset-summary.json','worker-0/result.json','fixture-summary.json')]+[(CAPTURE/'controller.log').read_text(),(CAPTURE/'endpoint.log').read_text(),1]

def test_complete_source_rejected_summary_is_not_an_arbitrary_launcher_failure():
    result=assess(*inputs());assert result['terminal_classification_pass']
    assert set(result['strict_summary_failed_predicates'])=={'worker_valid','rejected_actions_zero','stale_actions_zero'}
    assert not result['scientific_admission_authorized']

@pytest.mark.parametrize('fault',['wrong_exit','wrong_summary','wrong_observer','endpoint_error','transport_count','runtime_error'])
def test_no_general_exit_waiver_or_other_error_masking(fault):
    x=inputs()
    if fault=='wrong_exit':x[-1]=124
    if fault=='wrong_summary':x[0]['valid']=True
    if fault=='wrong_observer':x[0]['expectedOutcomeObserved']=False
    if fault=='endpoint_error':x[4]+='\n[ERROR] retained endpoint failure\n'
    if fault=='transport_count':x[0]['transport']['connections']+=1
    if fault=='runtime_error':x[1]['loggedErrors']=1
    assert not assess(*x)['terminal_classification_pass']
