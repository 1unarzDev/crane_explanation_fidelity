import copy
from pathlib import Path
import json
import pytest
from roboboat_trace_qualified_validity_v1 import assess

ROOT=Path(__file__).resolve().parents[1]
CAPTURE=ROOT/'artifacts/roboboat-population-development-42005/captures-v8-trace-pilot-001/boat-geom-42005-00001-v1'

def inputs():
    # Retained actual serialized trace validates candidate semantics only; no admission.
    return [json.loads((CAPTURE/name).read_text()) for name in ('navigation-reset-summary.json','worker-0/result.json','fixture-summary.json')]+[[json.loads(x) for x in (CAPTURE/'action-timing.jsonl').read_text().splitlines()],(CAPTURE/'worker-0/player.log').read_text()]

def test_correct_stale_rejection_candidate_never_promotes_retained_failure():
    result=assess(*inputs())
    assert result['candidate_qualified'],[k for k,v in result['checks'].items() if not v]
    assert result['stale_rejections_observed']==1 and not result['worker_valid_original']
    assert not result['scientific_admission_authorized'] and not result['prior_dispositions_changed']

@pytest.mark.parametrize('field',['loggedErrors','loggedExceptions','failedObservations','staleObservations','crossEpisodeActions','depthBufferValidationMismatches','invalidWaterSearches','duplicateActions','unknownSourceActions'])
def test_every_nonstale_benchmark_or_extra_fault_still_rejected(field):
    x=inputs();x[1][field]=1
    assert not assess(*x)['candidate_qualified']

@pytest.mark.parametrize('fault',['wrong_valid','other_rejection','missing_warning','wrong_warning_tick','missing_footer'])
def test_cannot_hide_worker_counter_trace_or_timeout_disagreement(fault):
    x=inputs()
    if fault=='wrong_valid':x[1]['valid']=True
    if fault=='other_rejection':x[1]['rejectedActions']+=1
    if fault=='missing_warning':x[4]=''
    if fault=='wrong_warning_tick':x[4]=x[4].replace('lastApplicationTick=13907','lastApplicationTick=999999')
    if fault=='missing_footer':x[3]=x[3][:-1]
    assert not assess(*x)['candidate_qualified']
