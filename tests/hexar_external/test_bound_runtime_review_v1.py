import json
from pathlib import Path

import pytest

from analysis.hexar_external.acquisition import bound_runtime_review_v1 as review
from analysis.hexar_external.acquisition.plan import make_plan


def test_live_or_unbound_run_rejected_before_review_namespace(tmp_path,monkeypatch):
    p,r=tmp_path/'plan.json',tmp_path/'run.json'
    p.write_text(json.dumps(make_plan('fixture',1,0,ordinal_start=40)))
    r.write_text(json.dumps(dict(schema='hexar-bound-runtime-development-qualification/v1',
        phase='development_only',status='IN_PROGRESS',image_id=review.EXPECTED_IMAGE,
        acquisition_phase='development_adapter_qualification',acquisition_binding_sha256=review.digest(p),
        plan_sha256=review.digest(p),episodes=[])))
    monkeypatch.setattr(review.subprocess,'run',lambda *_a,**_k:pytest.fail('no native dispatch'))
    with pytest.raises(ValueError,match='complete declared'):
        review.execute(p,r,tmp_path/'review')
    assert not (tmp_path/'review').exists()


@pytest.mark.parametrize('change',['image','binding','order','incomplete'])
def test_changed_schedule_or_binding_rejected_before_mutation(tmp_path,change):
    p,r=tmp_path/'plan.json',tmp_path/'run.json'
    plan=make_plan('fixture',1,0,ordinal_start=40);p.write_text(json.dumps(plan))
    value=dict(schema='hexar-bound-runtime-development-qualification/v1',phase='development_only',
        status='DEVELOPMENT_RUNS_RECORDED_UNQUALIFIED',image_id=review.EXPECTED_IMAGE,
        acquisition_phase='development_adapter_qualification',acquisition_binding_sha256=review.digest(p),
        plan_sha256=review.digest(p),episodes=[dict(episode_id=row['episode_id']) for row in plan['records']])
    if change=='image':value['image_id']='wrong-image'
    elif change=='binding':value['acquisition_binding_sha256']='f'*64
    elif change=='order':value['episodes'].reverse()
    else:value['episodes'].pop()
    r.write_text(json.dumps(value))
    with pytest.raises(ValueError):review.execute(p,r,tmp_path/'review')
    assert not (tmp_path/'review').exists()
