import hashlib
import pytest
import yaml
from pathlib import Path
from run_roboboat_terminal_capture import configuration_path,ROOT


def test_only_internal_stopping_thresholds_change_and_physical_contract_stays_fixed():
    base=ROOT/'packages/crane_ml/Tools/Performance/roboboat_terminal_v1.yaml'
    successor=base.with_name('roboboat_terminal_settling_v1.yaml')
    a=yaml.safe_load(base.read_text());b=yaml.safe_load(successor.read_text())
    checker=b['controller_server']['ros__parameters']['goal_checker']
    assert checker['trans_stopped_velocity']==checker['rot_stopped_velocity']==.02
    checker['trans_stopped_velocity']=checker['rot_stopped_velocity']=.05
    assert a==b
    assert configuration_path({})==base
    binding={'path':str(successor.relative_to(ROOT)),
             'sha256':hashlib.sha256(successor.read_bytes()).hexdigest()}
    assert configuration_path({'nav2_configuration':binding})==successor
    binding['sha256']='0'*64
    with pytest.raises(ValueError,match='changed'):configuration_path({'nav2_configuration':binding})


def test_configuration_outside_owned_component_is_rejected():
    binding={'path':'docs/roboboat_terminal_evidence/task_contract_v1.json','sha256':'unused'}
    with pytest.raises(ValueError,match='isolated component'):configuration_path({'nav2_configuration':binding})
