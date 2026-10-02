import copy
import fcntl

import pytest

from analysis.hexar_external.acquisition.raw_schedule_v1 import RawSchedule, make_plan, validate_plan
from analysis.hexar_external.acquisition.plan import FAMILIES
from analysis.hexar_external.confirmatory_v1.journal import exclusive_json


def admit(request):
    return dict(authorized=True, **{k:v for k,v in request.items() if k!='plan'})


def capture(record, folder):
    return dict(method_outputs_generated=False, judge_labels_generated=False,
                seed=record['seed'], synthetic_fixture=True)


def valid(record, runtime, folder):
    return dict(technical_valid=True,reasons=[],method_outcomes_accessed=False)


def engine(tmp_path, quota=1, reserves=1):
    return RawSchedule(tmp_path/'run',make_plan('a'*64,quota,reserves),'f'*64,admit)


def test_plan_is_deterministic_balanced_and_fresh():
    p=make_plan('a'*64,2,3)
    assert validate_plan(p) and make_plan('a'*64,2,3)==p
    assert len(p['records'])==30 and len({r['seed'] for r in p['records']})==30
    assert [r['family'] for r in p['records'][:6]]==list(FAMILIES)
    assert all(r['acquisition_id']==r['episode_id'] for r in p['records'])
    assert p['confirmation_authorized'] is False
    with pytest.raises(ValueError,match='collision'):
        make_plan('a'*64,2,3,excluded_seeds=[p['records'][10]['seed']])
    with pytest.raises(ValueError,match='collision'):
        make_plan('a'*64,2,3,excluded_ids=[p['records'][10]['episode_id']])
    for args in [('bad',2,3),('a'*64,False,3),('a'*64,1,-1)]:
        with pytest.raises(ValueError):make_plan(*args)


def test_complete_valid_quotas_skip_reserve_without_semantics(tmp_path):
    e=engine(tmp_path);calls=[]
    for _ in range(6):
        r=e.advance(lambda record,folder:calls.append(record) or capture(record,folder),valid)
        assert r['launch_performed']
    result=e.advance(lambda *_:pytest.fail('no extra run'),valid)
    assert result['status']=='VALID_QUOTAS_COMPLETE_NOT_SEALED' and result['attempted_episodes']==6
    assert len(calls)==6 and all(c['attempt_order']==1 for c in calls)
    assert not e.advance(lambda *_:pytest.fail('no optional extension'),valid)['launch_performed']


def test_invalid_episode_uses_only_next_within_family_reserve(tmp_path):
    e=engine(tmp_path);calls=[]
    def review(record,runtime,folder):
        if record['family']=='charging' and record['attempt_order']==1:
            return dict(technical_valid=False,reasons=['fixture_missing_bag'],method_outcomes_accessed=False)
        return valid(record,runtime,folder)
    for _ in range(7):e.advance(lambda r,f:calls.append(r) or capture(r,f),review)
    assert [r['family'] for r in calls]==list(FAMILIES)+['charging']
    assert [r['attempt_order'] for r in calls]==[1]*6+[2]
    assert e.advance(capture,review)['status']=='VALID_QUOTAS_COMPLETE_NOT_SEALED'
    attempts,counts,_,_=e.state()
    assert attempts[0]['disposition']=='TECHNICAL_INVALID' and counts==dict.fromkeys(FAMILIES,1)


def test_exhausted_reserve_never_expands_or_launches(tmp_path):
    e=engine(tmp_path,reserves=0)
    bad=lambda *_:dict(technical_valid=False,reasons=['fixture'],method_outcomes_accessed=False)
    e.advance(capture,bad)
    result=e.advance(lambda *_:pytest.fail('cap exhausted'),valid)
    assert result['status']=='FINITE_RESERVE_EXHAUSTED_NO_COHORT'


def test_crash_claim_is_retained_not_rerun(tmp_path):
    e=engine(tmp_path)
    def interrupted(*_):raise KeyboardInterrupt('fixture host interruption')
    with pytest.raises(KeyboardInterrupt):e.advance(interrupted,valid)
    e=engine(tmp_path)
    closed=e.advance(lambda *_:pytest.fail('no crash replay'),valid)
    assert not closed['launch_performed'] and closed['outcome']['disposition']=='INDETERMINATE_NO_REISSUE'
    assert e.advance(capture,valid)['outcome']['claim']['planned']['family']=='dynamic_env'


def test_ordinary_capture_failure_preserves_claim_and_invalid_review(tmp_path):
    e=engine(tmp_path)
    def fail(*_):raise RuntimeError('fixture capture failure')
    def reviewer(record,runtime,folder):
        assert runtime['technical_capture_error']=='RuntimeError: fixture capture failure'
        return dict(technical_valid=False,reasons=['CAPTURE_FAILED'],method_outcomes_accessed=False)
    result=e.advance(fail,reviewer)
    assert result['outcome']['disposition']=='TECHNICAL_INVALID'


def test_unavailable_review_closes_as_indeterminate_without_relaunch(tmp_path):
    e=engine(tmp_path)
    with pytest.raises(RuntimeError):
        e.advance(capture,lambda *_:(_ for _ in ()).throw(RuntimeError('review failure')))
    r=e.advance(lambda *_:pytest.fail('no duplicate capture'),valid)
    assert r['outcome']['disposition']=='INDETERMINATE_NO_REISSUE'
    assert 'runtime.json' in r['outcome']['retained_artifacts']


@pytest.mark.parametrize('at_review',[False,True])
def test_semantic_exposure_permanently_closes_acquisition(tmp_path,at_review):
    e=engine(tmp_path)
    cap=capture if at_review else lambda *_:dict(method_outputs_generated=True,judge_labels_generated=False)
    rev=(lambda *_:dict(technical_valid=False,reasons=['bad'],method_outcomes_accessed=True)) if at_review else valid
    with pytest.raises(ValueError,match='semantic exposure'):e.advance(cap,rev)
    with pytest.raises(ValueError,match='contamination'):
        e.advance(lambda *_:pytest.fail('no replacement after contamination'),valid)


def test_admission_denial_or_revocation_precedes_launch(tmp_path):
    p=make_plan('a'*64,1,1)
    with pytest.raises(ValueError,match='admission'):
        RawSchedule(tmp_path/'denied',p,'f'*64,lambda _:dict(authorized=False))
    assert not (tmp_path/'denied').exists()
    e=engine(tmp_path);e.admit=lambda _:dict(authorized=False)
    with pytest.raises(ValueError,match='admission'):e.advance(lambda *_:pytest.fail('no launch'),valid)
    assert not list((e.root/'attempts').iterdir())


def test_active_dispatch_lock_never_closes_as_crashed(tmp_path):
    e=engine(tmp_path)
    with (e.root/'acquisition.lock').open('a+b') as lock:
        fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        with pytest.raises(ValueError,match='still active'):
            e.advance(lambda *_:pytest.fail('no duplicate launch'),valid)


def test_changed_schedule_or_runtime_archive_blocks_further_attempts(tmp_path):
    e=engine(tmp_path);e.advance(capture,valid)
    record=e.plan['records'][0]
    (e.folder(record)/'runtime.json').write_text('{}')
    with pytest.raises(ValueError,match='archive changed'):e.advance(lambda *_:pytest.fail('no launch'),valid)


def test_unallocated_or_skipped_attempt_cannot_enter_schedule(tmp_path):
    e=engine(tmp_path)
    r=e.plan['records'][1];folder=e.folder(r);folder.mkdir();exclusive_json(folder/'claim.json',e.claim(r))
    with pytest.raises(ValueError,match='interleaved order'):
        e.advance(lambda *_:pytest.fail('no launch'),valid)


def test_cannot_rebind_existing_acquisition_root(tmp_path):
    e=engine(tmp_path)
    with pytest.raises(ValueError,match='already bound'):
        RawSchedule(e.root,make_plan('b'*64,1,1),'f'*64,admit)
