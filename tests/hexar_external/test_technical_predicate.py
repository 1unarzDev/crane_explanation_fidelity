import copy
import json
from pathlib import Path
import pytest
from analysis.hexar_external.acquisition.technical_predicate import evaluate

BASE=Path(__file__).resolve().parents[2]/'manifests/hexar_external/acquisition'


def fixture():
    plan=json.loads((BASE/'development_episode_plan_v15.json').read_text())
    run=json.loads((BASE/'development_episode_plan_v15_qualification_run.json').read_text())
    review=json.loads((BASE/'controller_boundary_qualification_v15.json').read_text())
    return [(receipt,json.loads((BASE/record['episode_id']/'episode.json').read_text()),record,row)
        for receipt,record,row in zip(run['episodes'],plan['records'],review['episodes'])]


def test_all_actual_v15_episodes_pass_without_success_based_selection():
    for receipt,episode,planned,review in fixture():
        assert evaluate(receipt,episode,planned,review)['valid']
        for status in (None,2,4,5,6):
            other=copy.deepcopy(episode);other.update(terminal_action_status=status,timeout=True)
            assert evaluate(receipt,other,planned,review)['valid']


@pytest.mark.parametrize('change',['wrong_seed','exposed','required_raw_missing','no_goal','wrong_distance','wrong_domain','late_setup','missing_fields'])
def test_real_missingness_and_invalid_setup_fail_closed(change):
    receipt,episode,planned,review=copy.deepcopy(fixture()[1])
    if change=='wrong_seed':episode['seed_hidden']+=1
    elif change=='exposed':receipt['method_outputs_generated']=True
    elif change=='required_raw_missing':review['bag_integrity']['bag_integrity_passed']=False
    elif change=='no_goal':episode['accepted']=False
    elif change=='wrong_distance':episode['sampling_hidden']['distance_m']=1.
    elif change=='wrong_domain':receipt['observed_ros_domain_id']='80'
    elif change=='late_setup':episode['intervention_observations_hidden'][0]['observed_sim_stamp_ns']=review['observed_action_window']['end_stamp_ns']
    else:episode={}
    assert not evaluate(receipt,episode,planned,review)['valid']
