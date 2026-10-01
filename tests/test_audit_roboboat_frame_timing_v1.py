import json
import pytest
from audit_roboboat_frame_timing_v1 import audit


def trace(tmp_path,steps=17,stale=3):
    metadata={'schema':'crane-frame-timing-audit/v1-development','kind':'metadata',
              'fixedDeltaTime':.02,'appliedMaximumDeltaTime':1/3}
    frame={'kind':'frame','frame':10,'wallSeconds':1,'simulationSeconds':1,
           'deltaTime':.34,'unscaledDeltaTime':.34,'fixedDeltaTime':.02,'maximumDeltaTime':1/3,
           'fixedUpdates':steps,'staleIncrement':stale,'staleObservations':stale,'failedObservations':0,
           'episode':1,'simulationTick':50,'observationTick':33,'pendingDepthReadbacks':0}
    path=tmp_path/'trace.jsonl';path.write_text(json.dumps(metadata)+'\n'+json.dumps(frame)+'\n')
    return path,metadata,frame


def test_stale_catchup_is_recorded_without_inventing_causality(tmp_path):
    path,_,_=trace(tmp_path);result=audit(path)
    assert result['stale_increments']==3
    assert result['stale_frames_with_four_or_more_fixed_updates']==1
    assert result['stale_frames_with_pending_queue_full_at_late_update']==0
    assert result['root_cause_established'] is False


def test_stale_without_catchup_remains_separate(tmp_path):
    path,_,_=trace(tmp_path,steps=1,stale=1);result=audit(path)
    assert result['stale_frames_without_four_or_more_fixed_updates']==1


def test_changed_fixed_step_fails_clock_version_check(tmp_path):
    path,metadata,frame=trace(tmp_path);frame['fixedDeltaTime']=.01
    path.write_text(json.dumps(metadata)+'\n'+json.dumps(frame)+'\n')
    assert audit(path)['issues']==['fixed_step_changed']


def test_malformed_reordered_frame_trace_rejected(tmp_path):
    path,metadata,frame=trace(tmp_path)
    path.write_text('\n'.join(map(json.dumps,[metadata,frame,frame])))
    with pytest.raises(ValueError,match='ordered unique'):audit(path)
