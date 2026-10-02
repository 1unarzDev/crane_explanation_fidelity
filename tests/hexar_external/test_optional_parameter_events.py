import json
from pathlib import Path
from analysis.hexar_external.acquisition import audit_controller_batch_v3 as review_module

BASE=Path(__file__).resolve().parents[2]/'manifests/hexar_external/acquisition'


def test_actual_missing_optional_channel_retains_valid_episode_and_all_packets():
    report=json.loads((BASE/'controller_boundary_qualification_v14_v3.json').read_text())
    manual=next(r for r in report['episodes'] if 'manual_joystick' in r['development_id'])
    assert manual['parameter_events_optional_observed_count']==0
    assert manual['candidate_integrity'] and manual['bag_integrity']['seed_applied_matches_plan']
    assert len(report['packets'])==54
    assert manual['absent_mux_commands_used_as_exclusion'] is False
    assert 'absence remains unknown' in manual['parameter_event_scope']


def test_optional_parameter_events_do_not_waive_required_raw_integrity(monkeypatch):
    monkeypatch.setattr(review_module,'audit',lambda folder:dict(bag_integrity_passed=False,issues=['missing required task messages']))
    value=review_module.review(BASE/'development_episode_plan_v14.json')
    assert value['status']=='FAILED_RETAINED' and not value['packets']
    assert len(value['episodes'])==6 and all(not r['candidate_integrity'] for r in value['episodes'])
