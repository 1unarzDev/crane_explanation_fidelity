import json
from pathlib import Path

import pytest

from analysis.hexar_external.acquisition import bound_runtime_review_v2 as review
from analysis.hexar_external.acquisition.plan import make_plan


def test_relative_repository_inputs_are_normalized_before_mutation(tmp_path,monkeypatch):
    monkeypatch.setattr(review,'ROOT',tmp_path);monkeypatch.chdir(tmp_path)
    p=Path('plan.json');p.write_text(json.dumps(make_plan('fixture',1,0,ordinal_start=40)))
    Path('run.json').write_text(json.dumps(dict(schema='hexar-bound-runtime-development-qualification/v1',
        phase='development_only',status='IN_PROGRESS',image_id=review.EXPECTED_IMAGE,
        acquisition_phase='development_adapter_qualification',acquisition_binding_sha256=review.digest(p),
        plan_sha256=review.digest(p),episodes=[])))
    with pytest.raises(ValueError,match='complete declared'):
        review.execute(p,Path('run.json'),Path('review'))
    assert not Path('review').exists()


def test_outside_repository_destination_rejected_before_read_or_mutation(tmp_path,monkeypatch):
    root=tmp_path/'root';root.mkdir();monkeypatch.setattr(review,'ROOT',root)
    with pytest.raises(ValueError):
        review.execute(root/'missing_plan.json',root/'missing_run.json',tmp_path/'outside')
    assert not (tmp_path/'outside').exists()
