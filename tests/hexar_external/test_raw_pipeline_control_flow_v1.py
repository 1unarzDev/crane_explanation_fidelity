"""Synthetic control-flow tests; bypass admission explicitly, never qualify it."""
import fcntl
import json
from pathlib import Path

import pytest

from analysis.hexar_external.acquisition import raw_cohort_pipeline_v1 as pipeline
from analysis.hexar_external.acquisition.raw_schedule_v1 import RawSchedule, make_plan
from analysis.hexar_external.acquisition.raw_archive_v1 import create, digest, read
from analysis.hexar_external.confirmatory_v1.journal import exclusive_json

FREEZE='f'*64
PREDICATE='d'*64
IMAGE='sha256:'+'e'*64


def setup(root, monkeypatch, reserve=1, invalid=(), interrupt=False):
    plan=make_plan('a'*64,1,reserve)
    base=root/'base';base.mkdir()
    exclusive_json(base/'plan.json',plan)
    exclusive_json(base/'cohort.json',dict(episode_plan_path='base/plan.json'))
    exclusive_json(base/'technical_validity.json',dict(machine_predicate_sha256=PREDICATE))
    ctx=dict(base=base,config=dict(execution_root='execution',image_id=IMAGE),plan=plan,
        freeze_sha256=FREEZE,excluded_ids=set(),excluded_seeds=set(),excluded_hashes=set())
    monkeypatch.setattr(pipeline,'load_context',lambda *_:ctx)
    # Deliberate permissive fixture: these tests cannot establish admission.
    admit=lambda request:dict(authorized=True,**{k:v for k,v in request.items() if k!='plan'})
    monkeypatch.setattr(pipeline,'Admission',lambda *_:admit)
    launches=[]
    class Runtime:
        def __init__(self,*_):pass
        def capture(self,record,folder):
            launches.append(record['acquisition_id'])
            if interrupt and len(launches)==1:raise KeyboardInterrupt('synthetic host crash')
            return dict(method_outputs_generated=False,judge_labels_generated=False)
    class Review:
        def __init__(self,*_):pass
        def __call__(self,record,runtime,folder):return export(record,folder,False)
    class Recovery:
        def __init__(self,*_):pass
        def export_invalid(self,record,folder):export(record,folder,True)
    def export(record,folder,recovered):
        valid=not recovered and record['acquisition_id'] not in invalid
        capture=root/'capture'/record['episode_id'];capture.mkdir(parents=True)
        exclusive_json(capture/'provenance.json',dict(episode_id=record['episode_id'],seed_hidden=record['seed'],
            family_hidden=record['family'],acquisition_phase='raw_confirmation',acquisition_binding_sha256=FREEZE,
            image_id=IMAGE,fresh_container=valid,method_outputs_generated=False,judge_labels_generated=False))
        if valid:
            for name in ('episode.json','acquisition_intent.json'):
                exclusive_json(capture/name,dict(phase='raw_confirmation',acquisition_binding_sha256=FREEZE))
            for name in ('controller_start.json','controller_end.json'):exclusive_json(capture/name,{})
            (capture/'raw').mkdir();(capture/'raw'/'metadata.yaml').write_text('synthetic')
            (capture/'raw'/'bag.db3').write_bytes(record['acquisition_id'].encode())
        archive=folder/'raw_archive.json'
        create(root,archive,capture,record,FREEZE,dict(path=str((capture/'provenance.json').relative_to(root)),
            sha256=digest(capture/'provenance.json')),IMAGE)
        reasons=[] if valid else (['HOST_INTERRUPTION_AFTER_DURABLE_CLAIM'] if recovered else ['SYNTHETIC_TECHNICAL_FAILURE'])
        receipt=folder/'validity_receipt.json'
        exclusive_json(receipt,dict(schema='hexar-frozen-raw-validity/v1',acquisition_id=record['acquisition_id'],
            freeze_sha256=FREEZE,raw_archive_sha256=digest(archive),validity_predicate_sha256=PREDICATE,
            technical_valid=valid,reasons=reasons,method_outcomes_accessed=False,independent_reset_measured=valid))
        exclusive_json(folder/('recovered_exported_attempt.json' if recovered else 'exported_attempt.json'),dict(record,
            raw_archive_path=str(archive.relative_to(root)),raw_archive_sha256=digest(archive),
            validity_receipt_path=str(receipt.relative_to(root)),validity_receipt_sha256=digest(receipt),
            validity_predicate_sha256=PREDICATE))
        return dict(technical_valid=valid,reasons=reasons,method_outcomes_accessed=False)
    monkeypatch.setattr(pipeline,'Runtime',Runtime);monkeypatch.setattr(pipeline,'Review',Review)
    monkeypatch.setattr(pipeline,'Recovery',Recovery)
    return plan,launches,ctx,admit


def test_complete_balanced_raw_seal_uses_real_archive_selection(tmp_path,monkeypatch):
    plan,launches,_,_=setup(tmp_path,monkeypatch)
    assert pipeline.execute(tmp_path,'base')=='FRESH_RAW_COHORT_SEALED_SEMANTIC_CONFIRMATION_GATED'
    seal=read(tmp_path/'base/raw_cohort_seal.json')
    assert seal['n']==6 and len(set(r['family'] for r in seal['records']))==6
    assert len(launches)==6 and seal['alpha_consumed']==seal['method_or_judge_calls']==0
    assert all(r['bag_sha256s'] and r['independent_reset'] for r in seal['records'])
    before=list(launches)
    with pytest.raises(ValueError,match='seal exists'):pipeline.execute(tmp_path,'base')
    assert launches==before


def test_invalid_first_episode_consumes_only_its_fixed_family_reserve(tmp_path,monkeypatch):
    plan=make_plan('a'*64,1,1);invalid={plan['records'][0]['acquisition_id']}
    _,launches,_,_=setup(tmp_path,monkeypatch,invalid=invalid)
    pipeline.execute(tmp_path,'base')
    seal=read(tmp_path/'base/raw_cohort_seal.json')
    assert len(launches)==7 and launches[-1]==plan['records'][6]['acquisition_id']
    assert len(seal['dispositions'])==7 and len(seal['records'])==6
    assert not invalid.intersection(r['acquisition_id'] for r in seal['records'])


def test_reserve_exhaustion_retains_all_attempts_and_never_seals(tmp_path,monkeypatch):
    plan=make_plan('a'*64,1,1);invalid={r['acquisition_id'] for r in plan['records'] if r['family']==plan['family_order'][0]}
    _,launches,_,_=setup(tmp_path,monkeypatch,invalid=invalid)
    assert pipeline.execute(tmp_path,'base')=='FINITE_RESERVE_EXHAUSTED_NO_COHORT'
    assert len(launches)==7 and not (tmp_path/'base/raw_cohort_seal.json').exists()
    assert len(read(tmp_path/'execution/terminal_attempt_manifest.json')['attempts'])==7
    before=list(launches);assert pipeline.execute(tmp_path,'base')=='FINITE_RESERVE_EXHAUSTED_NO_COHORT'
    assert launches==before


def test_interruption_closes_claim_without_relaunch_and_preserves_prefix(tmp_path,monkeypatch):
    plan,launches,_,_=setup(tmp_path,monkeypatch,interrupt=True)
    with pytest.raises(KeyboardInterrupt):pipeline.execute(tmp_path,'base')
    assert pipeline.execute(tmp_path,'base')=='FRESH_RAW_COHORT_SEALED_SEMANTIC_CONFIRMATION_GATED'
    assert len(launches)==7 and len(set(launches))==7
    outcome=read(tmp_path/'execution/attempts'/plan['records'][0]['acquisition_id']/'outcome.json')
    assert outcome['disposition']=='INDETERMINATE_NO_REISSUE'


def test_live_dispatch_lock_prevents_recovery_or_launch(tmp_path,monkeypatch):
    plan,launches,ctx,admit=setup(tmp_path,monkeypatch)
    scheduler=RawSchedule(tmp_path/'execution',plan,FREEZE,admit)
    folder=scheduler.folder(plan['records'][0]);folder.mkdir()
    exclusive_json(folder/'claim.json',scheduler.claim(plan['records'][0]))
    with (scheduler.root/'acquisition.lock').open('a+b') as lock:
        fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        with pytest.raises(ValueError,match='still active'):pipeline.execute(tmp_path,'base')
    assert not launches and list(folder.iterdir())==[folder/'claim.json']


def test_publication_interruption_resumes_without_acquiring_more(tmp_path,monkeypatch):
    _,launches,_,_=setup(tmp_path,monkeypatch)
    original=pipeline.exclusive_json
    def interrupted(path,value):
        if Path(path).name=='raw_cohort_seal.json':raise KeyboardInterrupt('synthetic publication crash')
        return original(path,value)
    monkeypatch.setattr(pipeline,'exclusive_json',interrupted)
    with pytest.raises(KeyboardInterrupt):pipeline.execute(tmp_path,'base')
    assert len(launches)==6 and (tmp_path/'execution/terminal_attempt_manifest.json').exists()
    monkeypatch.setattr(pipeline,'exclusive_json',original)
    assert pipeline.execute(tmp_path,'base')=='FRESH_RAW_COHORT_SEALED_SEMANTIC_CONFIRMATION_GATED'
    assert len(launches)==6


def test_changed_terminal_manifest_stops_publication_without_new_launch(tmp_path,monkeypatch):
    _,launches,_,_=setup(tmp_path,monkeypatch)
    original=pipeline.exclusive_json
    def interrupted(path,value):
        if Path(path).name=='raw_cohort_seal.json':raise KeyboardInterrupt()
        return original(path,value)
    monkeypatch.setattr(pipeline,'exclusive_json',interrupted)
    with pytest.raises(KeyboardInterrupt):pipeline.execute(tmp_path,'base')
    path=tmp_path/'execution/terminal_attempt_manifest.json';value=read(path);value['method_or_judge_calls']=1
    path.write_text(json.dumps(value))
    monkeypatch.setattr(pipeline,'exclusive_json',original)
    with pytest.raises(ValueError,match='terminal raw manifest changed'):pipeline.execute(tmp_path,'base')
    assert len(launches)==6 and not (tmp_path/'base/raw_cohort_seal.json').exists()
