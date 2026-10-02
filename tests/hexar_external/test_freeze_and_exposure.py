import hashlib
import json
from pathlib import Path
import pytest
from analysis.hexar_external.confirmatory_v1 import audit,development_exposure
from analysis.hexar_external.confirmatory_v1.seal_cohort import select,verify_attempt_schedule


def test_acquisition_freeze_contains_transitive_code_and_excludes_later_artifacts(tmp_path):
    base=tmp_path/'manifests';base.mkdir()
    for name in ('endpoint.json','raw_cohort_seal.json','h1_gate_attestation.json','freeze_manifest.json'):
        (base/name).write_text('{}')
    code=tmp_path/'analysis.py';code.write_text('qualified runtime')
    h=hashlib.sha256(code.read_bytes()).hexdigest()
    files=audit.acquisition_file_hashes(base,tmp_path,{'files':{'analysis.py':h}})
    assert files=={'analysis.py':h,'manifests/endpoint.json':audit.digest(base/'endpoint.json')}
    code.write_text('changed runtime')
    with pytest.raises(ValueError,match='scientific file changed'):
        audit.acquisition_file_hashes(base,tmp_path,{'files':{'analysis.py':h}})


def test_development_exclusion_pin_and_identity_are_required(tmp_path):
    path=tmp_path/'dev.json'
    value=dict(schema='hexar-development-exposure/v1',phase='development_only',records=[
        dict(raw_sha256s=['devhash'],acquisition_id='dev-id',seed=23,eligible_for_confirmation=False)])
    path.write_text(json.dumps(value));pin=dict(path='dev.json',sha256=audit.digest(path))
    assert development_exposure.load_exclusions(tmp_path,pin)==({'devhash'},{'dev-id'},{23})
    path.write_text('{}')
    with pytest.raises(ValueError,match='ledger changed'):
        development_exposure.load_exclusions(tmp_path,pin)


def test_renaming_development_bag_does_not_restore_freshness(tmp_path):
    # Reject development identity/seed even if the renamed bytes are different.
    attempt=dict(family='success',acquisition_id='dev-id',seed=23,raw_sha256='newhash')
    for ids,seeds in (({'dev-id'},set()),(set(),{23})):
        with pytest.raises(ValueError,match='development acquisition'):
            select([attempt],1,['success'],tmp_path,set(),ids,seeds)


def test_admission_rejects_development_added_after_snapshot(tmp_path):
    base=tmp_path/'manifests/hexar_external/acquisition'
    receipt=base/'hexar-tiago-dev-one/provenance.json'
    receipt.parent.mkdir(parents=True)
    receipt.write_text(json.dumps(dict(episode_id='dev-one',seed_hidden=23,raw_files=[])))
    value=development_exposure.inventory(tmp_path)
    development_exposure.verify_current_inventory(tmp_path,value)
    plan=base/'development_episode_plan_new.json'
    plan.write_text(json.dumps(dict(phase='development',records=[dict(episode_id='dev-two',seed=24)])))
    with pytest.raises(ValueError,match='inventory stale: planned'):
        development_exposure.verify_current_inventory(tmp_path,value)
    refreshed=development_exposure.inventory(tmp_path)
    development_exposure.verify_current_inventory(tmp_path,refreshed)
    receipt.write_text(json.dumps(dict(episode_id='dev-one',seed_hidden=25,raw_files=[])))
    with pytest.raises(ValueError,match='inventory stale: records'):
        development_exposure.verify_current_inventory(tmp_path,refreshed)


def test_seal_rejects_schedule_deviation_even_with_a_matching_claimed_plan_hash():
    records=[dict(acquisition_id='fresh-'+str(i),seed=i,family='success',attempt_order=i) for i in range(1,4)]
    plan=dict(phase='confirmation',records=records)
    verify_attempt_schedule(plan,records[:2],['success'],3)
    for key,changed in [('seed',12),('acquisition_id','other')]:
        altered=[{**records[0],key:changed}]
        with pytest.raises(ValueError,match='ordered prefix'):
            verify_attempt_schedule(plan,altered,['success'],3)
    with pytest.raises(ValueError,match='ordered prefix'):
        verify_attempt_schedule(plan,records[1:],['success'],3)
    with pytest.raises(ValueError,match='duplicate planned'):
        verify_attempt_schedule(dict(phase='confirmation',records=[records[0],records[0],records[2]]),[],['success'],3)
