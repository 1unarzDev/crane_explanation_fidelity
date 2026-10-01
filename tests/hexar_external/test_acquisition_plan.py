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
