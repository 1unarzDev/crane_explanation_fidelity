import ast
import hashlib
import json
from pathlib import Path

import pytest

from analysis.hexar_external.acquisition import bound_runtime_completion_v3 as completion
from analysis.hexar_external.acquisition.plan import make_plan


def setup_inputs(root):
    plan=make_plan('fixture',1,0,ordinal_start=40)
    paper=root/'declaration.md';paper.write_text('synthetic fixture declaration')
    plan['qualification_design']=dict(path='declaration.md',sha256=completion.digest(paper))
    p=root/'plan.json';p.write_text(json.dumps(plan))
    r=root/'run.json';r.write_text(json.dumps(dict(schema='hexar-bound-runtime-development-qualification/v1',
        phase='development_only',status='DEVELOPMENT_RUNS_RECORDED_UNQUALIFIED',image_id=completion.EXPECTED_IMAGE,
        acquisition_phase='development_adapter_qualification',acquisition_binding_sha256=completion.digest(p),
        plan_sha256=completion.digest(p),episodes=[dict(episode_id=row['episode_id']) for row in plan['records']])))
    stage=root/'retained';stage.mkdir()
    for name in ('capture_review.json','native_inputs.json','native_review.json'):(stage/name).write_text('{}')
    pins={f.name:completion.digest(f) for f in stage.iterdir()}
    return p,r,stage,pins


def test_changed_retained_native_stage_fails_before_mutation(tmp_path,monkeypatch):
    monkeypatch.setattr(completion,'ROOT',tmp_path)
    p,r,stage,pins=setup_inputs(tmp_path)
    (stage/'native_review.json').write_text('changed retained native stage')
    with pytest.raises(ValueError,match='artifact changed'):
        completion.execute(p,r,tmp_path/'complete',stage,pins)
    assert not (tmp_path/'complete').exists()


def test_terminal_review_cannot_be_recompleted(tmp_path,monkeypatch):
    monkeypatch.setattr(completion,'ROOT',tmp_path)
    p,r,stage,pins=setup_inputs(tmp_path);(stage/'report.json').write_text('{}')
    with pytest.raises(ValueError,match='terminal qualification'):
        completion.execute(p,r,tmp_path/'complete',stage,pins)
    assert not (tmp_path/'complete').exists()


def test_exact_three_retained_pins_required_before_completion(tmp_path,monkeypatch):
    monkeypatch.setattr(completion,'ROOT',tmp_path)
    p,r,stage,pins=setup_inputs(tmp_path);pins.pop('native_inputs.json')
    with pytest.raises(ValueError,match='exact retained'):
        completion.execute(p,r,tmp_path/'complete',stage,pins)
    assert not (tmp_path/'complete').exists()


def test_completion_contains_no_new_native_or_semantic_dispatch():
    tree=ast.parse(Path(completion.__file__).read_text())
    calls=[ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n,ast.Call)]
    assert 'subprocess.run' not in calls and 'subprocess.Popen' not in calls
    assert not any('backend' in c or 'provider' in c for c in calls)
