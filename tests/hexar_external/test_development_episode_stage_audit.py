import json
from pathlib import Path

import pytest
from analysis.hexar_external.confirmatory_v1.audit_development_episode_stage_v1 import audit_stage
from analysis.hexar_external.confirmatory_v1.staged_episode_dispatch_v2 import dispatch
from analysis.hexar_external.acquisition.raw_archive_v1 import digest


def fixture(tmp_path,empty=False):
    path=tmp_path/'prior.json';path.write_text('{}')
    def factory(_):
        return lambda _:dict(raw_response=b'{"answer":"test"}',stdout=b'{"answer":"test"}',stderr=b'',returncode=0,transport_policy_passed=True)
    # Deterministic-role fixture avoids manufacturing a CLI transcript.
    jobs=[] if empty else [dict(job_id=f'opaque-{i}',request=dict(role='contract',maximum_response_bytes=1024)) for i in range(6)]
    dispatch(tmp_path/'stage','a'*64,'methods',jobs,{path:digest(path)},lambda:None,factory)
    return tmp_path/'stage'


def test_closed_stage_reproduces_all_raw_shards_without_writing(tmp_path):
    folder=fixture(tmp_path)
    before={str(p):digest(p) for p in tmp_path.rglob('*') if p.is_file()}
    receipt=audit_stage(folder,'a'*64,'methods')
    assert receipt['raw_attempts_verified']==6 and receipt['provider_calls']==0
    assert before=={str(p):digest(p) for p in tmp_path.rglob('*') if p.is_file()}


def test_empty_stage_reproduces_explicit_no_call_receipt(tmp_path):
    assert audit_stage(fixture(tmp_path,True),'a'*64,'methods')['attempts']==0


def test_raw_tamper_and_prerequisite_tamper_are_rejected(tmp_path):
    folder=fixture(tmp_path);raw=next((folder/'attempts').glob('shard-*/*/stdout.bin'));raw.write_bytes(b'changed')
    with pytest.raises(ValueError,match='raw bytes'):audit_stage(folder,'a'*64,'methods')
    (tmp_path/'prior.json').write_text('{"changed":true}')
    with pytest.raises(ValueError,match='prerequisite'):audit_stage(folder,'a'*64,'methods')


def test_pending_completion_and_wrong_binding_cannot_be_audited_as_complete(tmp_path):
    folder=fixture(tmp_path)
    with pytest.raises(ValueError,match='binding'):audit_stage(folder,'b'*64,'methods')
    (folder/'completion_receipt.json').unlink()
    with pytest.raises(FileNotFoundError):audit_stage(folder,'a'*64,'methods')
