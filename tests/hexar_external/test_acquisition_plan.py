"""Development planner checks; plans never count as acquired episodes."""
import pytest
from analysis.hexar_external.acquisition.plan import make_plan,episode_seed,FAMILIES


def test_independent_family_episode_seed_plan():
    plan=make_plan('development-test-master',3,2)
    records=plan['records']
    assert len(records)==30 and len({r['seed'] for r in records})==30
    assert len({r['episode_id'] for r in records})==30
    assert set(r['family'] for r in records)==set(FAMILIES)
    assert all(r['status']=='PLANNED_NOT_ACQUIRED' and not r['semantic_outputs_generated'] for r in records)
    assert make_plan('development-test-master',3,2)==plan
    assert episode_seed('development-test-master','development','success',0)!=episode_seed('different-master','development','success',0)


def test_development_planner_cannot_admit_confirmation():
    with pytest.raises(ValueError,match='Confirmation allocation'):
        make_plan('test',1,1,'confirmation')
    with pytest.raises(ValueError):make_plan('test',0,1)


def test_offset_plan_preserves_primary_reserve_roles_and_fresh_ids():
    plan=make_plan('new-master',2,1,ordinal_start=10)
    for family in FAMILIES:
        rows=[r for r in plan['records'] if r['family']==family]
        assert [r['ordinal'] for r in rows]==[10,11,12]
        assert [r['role'] for r in rows]==['primary','primary','reserve']
        assert rows[0]['episode_id']==f'hexar-tiago-dev-{family}-0010'
    with pytest.raises(ValueError):make_plan('test',1,1,ordinal_start=-1)


def test_qualification_refuses_old_episode_before_launch_or_receipt_write(tmp_path,monkeypatch):
    import json
    from analysis.hexar_external.acquisition import qualify
    plan=make_plan('new-master',1,0,ordinal_start=10)
    p=tmp_path/'plan.json';p.write_text(json.dumps(plan))
    old=tmp_path/plan['records'][0]['episode_id'];old.mkdir();receipt=old/'provenance.json';receipt.write_text('retained bytes')
    monkeypatch.setattr(qualify,'OUT',tmp_path)
    monkeypatch.setattr(qualify.subprocess,'run',lambda *a,**kw:pytest.fail('must not launch existing identity'))
    monkeypatch.setattr(qualify.subprocess,'check_output',lambda *a,**kw:pytest.fail('must not inspect runtime for rejected plan'))
    with pytest.raises(ValueError,match='prior development episode identity'):
        qualify.run(p,'unused-image')
    assert receipt.read_text()=='retained bytes'
    assert not p.with_name('plan_preflight.log').exists()
