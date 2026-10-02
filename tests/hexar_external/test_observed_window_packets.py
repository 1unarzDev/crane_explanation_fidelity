import json
from pathlib import Path

from analysis.hexar_external.acquisition.navigation_contract import contract
from analysis.hexar_external.acquisition.navigation_references import build

ROOT=Path(__file__).resolve().parents[2]


def records():
    return json.loads((ROOT/'manifests/hexar_external/acquisition/navigation_packet_qualification_v2.json').read_text())['packets']


def test_native_observed_window_survives_masks_without_restoring_motion():
    rows=records()
    assert len(rows)==54 and len({r['development_id'] for r in rows})==6
    for episode in {r['development_id'] for r in rows}:
        trio={r['condition']:r['method_packet'] for r in rows if r['development_id']==episode and r['question_id']=='q1'}
        assert trio['intact']==trio['irrelevant_removal']
        full,masked=trio['intact'],trio['diagnostic_removal']
        assert full['evidence']['observed_action_window']==masked['evidence']['observed_action_window']
        assert full['evidence']['navigation_outcomes']==masked['evidence']['navigation_outcomes']
        assert masked['evidence']['odometry_observation']==[]
        assert masked['availability']['odometry_observation']=='unavailable'
        odom=full['evidence']['odometry_observation'][0];window=full['evidence']['observed_action_window'][0]
        assert window['start_stamp_ns']<=odom['measurement_stamp_ns_first']<=odom['measurement_stamp_ns_last']<=window['end_stamp_ns']
        assert odom['maximum_measurement_gap_ns']<=40000000
        assert not odom['physical_goal_attainment_inferred']


def test_v11_reference_and_contract_use_real_cancellations_and_observed_motion():
    for record in records():
        packet=record['method_packet'];reference=build(packet)
        output=contract(packet,'v11-assembly-regression',record['development_id'])
        assert len(output['answer'].split())<=60
        present=bool(packet['evidence']['odometry_observation'])
        assert ('claim-motion' in output['plan']['required_claim_ids'])==present
        assert ('recorded_odometry_observation' in {u['unit_id'] for u in reference['required_units']})==present
        if present:
            assert output['plan']['approved_numeric_values'][0]['value']==packet['evidence']['odometry_observation'][0]['sampled_xy_path_distance_m']
        if packet['evidence']['observed_action_window'][0]['terminal_result_status']==5:
            assert 'reported a timeout' in output['answer']
            assert reference['required_units'][0]['required_explicit_dispositions']==['timeout']
