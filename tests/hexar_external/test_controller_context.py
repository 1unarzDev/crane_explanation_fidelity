import copy
import json
from pathlib import Path
import pytest
from analysis.hexar_external.acquisition.controller_context import validate

ROOT=Path(__file__).resolve().parents[2]

def observed():
    return json.loads((ROOT/'manifests/hexar_external/acquisition/controller_probe_qualification_v2/observed_controller.json').read_text())['snapshot']


def test_observed_public_parameters_and_real_base_receiver():
    assert validate(observed())==observed()


@pytest.mark.parametrize('mutation', ['marker_only','timeout','bool_priority','missing_input','zero_clock'])
def test_incomplete_or_misleading_controller_capture_fails(mutation):
    snapshot=copy.deepcopy(observed())
    if mutation=='marker_only':snapshot['output_receivers']=[r for r in snapshot['output_receivers'] if r['node_name']=='twist_marker']
    if mutation=='timeout':snapshot['parameters']['topics.navigation.timeout']=0.
    if mutation=='bool_priority':snapshot['parameters']['topics.navigation.priority']=True
    if mutation=='missing_input':del snapshot['subscribers']['/docking_vel']
    if mutation=='zero_clock':snapshot['stamp']={'sec':0,'nanosec':0}
    with pytest.raises(ValueError):validate(snapshot)


def test_boundary_evidence_equal_projection_and_universal_diagnostic_mask():
    from analysis.hexar_external.acquisition.controller_context import extend
    from analysis.hexar_external.confirmatory_v1.rich_blind_projection import project
    from analysis.hexar_external.acquisition.navigation_references import build
    packets=json.loads((ROOT/'manifests/hexar_external/acquisition/navigation_packet_qualification_v2.json').read_text())['packets']
    packet=packets[0]['method_packet'];before=copy.deepcopy(packet)
    snapshots=[observed(),observed()];snapshots[1]['stamp']['sec']+=40
    result=extend(packet,snapshots,'intact')
    assert packet==before
    assert result['source_context']['controller_runtime_observations']==snapshots
    payload=project(result,build(result),'Navigation software reported failure.')
    assert payload['visible_evidence']['source_context']['controller_runtime_observations']==snapshots
    masked=extend(packet,snapshots,'diagnostic_removal')
    assert masked['source_context']['controller_runtime_observations']==[]
    wrong=copy.deepcopy(snapshots);wrong[0]['technical_review']={'candidate_integrity':True}
    with pytest.raises(ValueError,match='closed public'):extend(packet,wrong,'intact')
    with pytest.raises(ValueError,match='ordered'):extend(packet,[snapshots[0],snapshots[0]],'intact')
