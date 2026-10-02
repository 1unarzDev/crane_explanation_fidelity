import copy
import json
from pathlib import Path
import pytest
from analysis.hexar_external.confirmatory_v1.unique_request_plan import build

ROOT=Path(__file__).resolve().parents[2]


def entries():
    packets=json.loads((ROOT/'manifests/hexar_external/acquisition/controller_boundary_qualification_v12_v2.json').read_text())['packets']
    return [dict(episode_id=r['development_id'],method=method,job_id=f'{r["question_id"]}-{r["condition"]}',
                 packet=r['method_packet'],implementation_binding=dict(prompt='candidate frozen strong prompt',model='unbound development alias',renderer='candidate'))
            for r in packets for method in ('HX-PROMPT','HX-CONTRACT')]


def test_identical_evidence_aliases_share_one_attempt_without_cross_episode_merging():
    result=build(entries())
    assert result['battery_cells']==108 and result['unique_requests']==72
    assert not result['dispatch_authorized'] and result['semantic_calls']==0
    for episode in {r['episode_id'] for r in result['aliases']}:
        for method in ('HX-PROMPT','HX-CONTRACT'):
            rows={r['job_id']:r['unique_request_id'] for r in result['aliases'] if r['episode_id']==episode and r['method']==method}
            for query in ('q1','q2','q3'):
                assert rows[f'{query}-intact']==rows[f'{query}-irrelevant_removal']
                assert rows[f'{query}-intact']!=rows[f'{query}-diagnostic_removal']
    a=entries()[0];b=copy.deepcopy(a);b['episode_id']='distinct-independent-episode'
    assert build([a,b])['unique_requests']==2


def test_changed_query_evidence_or_implementation_never_reuses_semantics():
    a=entries()[0]
    for mutation in ('query','evidence','runtime'):
        b=copy.deepcopy(a);b['job_id']='distinct-cell'
        if mutation=='query':b['packet']['question']+=' Different required question.'
        if mutation=='evidence':b['packet']['evidence']['navigation_logs'].append(dict(message='new observation',logger='public',evidence_id='new',callback_time='1'))
        if mutation=='runtime':b['implementation_binding']['model']='different model'
        assert build([a,b])['unique_requests']==2
    assert build(entries())==build(list(reversed(entries())))


def test_identity_duplicates_and_hidden_metadata_fail_before_any_dispatch():
    a=entries()[0]
    with pytest.raises(ValueError,match='duplicate'):build([a,a])
    bad=copy.deepcopy(a);bad['packet']['source_context']['ground_truth']='hidden'
    with pytest.raises(ValueError,match='forbidden'):build([bad])
