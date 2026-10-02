from pathlib import Path

import pytest

from analysis.hexar_external.acquisition.native_review_core_v1 import execute
from analysis.hexar_external.acquisition.project_raw_episode_v1 import review


@pytest.mark.parametrize('change',['phase','binding','method','judge'])
def test_unbound_or_exposed_native_capture_rejected_before_ros_import(tmp_path,change):
    receipt=dict(acquisition_phase='raw_confirmation',acquisition_binding_sha256='f'*64,
                 method_outputs_generated=False,judge_labels_generated=False)
    if change=='phase':receipt['acquisition_phase']='development_only'
    elif change=='binding':receipt['acquisition_binding_sha256']='a'*64
    elif change=='method':receipt['method_outputs_generated']=True
    else:receipt['judge_labels_generated']=True
    with pytest.raises(ValueError,match='phase/binding/semantic'):
        execute(tmp_path,tmp_path,receipt,'raw_confirmation','f'*64)
    assert not list(tmp_path.iterdir())


def test_unspecified_native_phase_rejected_before_reading_capture(tmp_path):
    with pytest.raises(ValueError,match='explicit acquisition phase'):
        execute(tmp_path,tmp_path,{},'unspecified','f'*64)


def test_missing_raw_interface_is_explicit_failure_without_mutating_capture(tmp_path):
    value=review(tmp_path,'fixture',[],[])
    assert value['episode']['candidate_integrity'] is False and value['packets']==[]
    assert value['method_or_judge_calls']==0 and value['original_capture_mutated'] is False
    assert not list(tmp_path.iterdir())
