import copy
import hashlib
from pathlib import Path

import pytest

from analysis.hexar_external.confirmatory_v1.streaming_registry_shards_v1 import write_sorted,verify,RegistryHash
from analysis.hexar_external.confirmatory_v1.registry_shards_v1 import build,write
from analysis.hexar_external.confirmatory_v1.registered_attempt_executor_v2 import registry
from analysis.hexar_external.confirmatory_v1.journal import fingerprint,canonical,exclusive_json


def jobs(n=10,padding=100):
    for i in range(n):yield dict(job_id=f'opaque-{i:06d}',request=dict(role='method',maximum_response_bytes=1024,payload='x'*padding))


def test_incremental_hash_matches_complete_canonical_registry_with_unicode():
    values=list(jobs(4));values[0]['request']['payload']='λ 中文'
    complete=registry('f'*64,'development_qualification',values);stream=RegistryHash('f'*64,'development_qualification')
    for row in complete['jobs']:stream.append(row)
    assert stream.finish()==fingerprint(complete)


@pytest.mark.parametrize('padding,byte_limit,job_limit',[(20,10000,3),(1000,1800,100),(300,2200,4)])
def test_streamed_index_and_shards_are_byte_identical_to_prior_builder(tmp_path,padding,byte_limit,job_limit):
    values=list(jobs(15,padding));expected,shards=build('f'*64,'development_qualification','methods',values,byte_limit,job_limit)
    actual=write_sorted(tmp_path/'stream','f'*64,'development_qualification','methods',iter(values),byte_limit,job_limit)
    assert actual==expected and verify(tmp_path/'stream',fingerprint(actual))==actual
    for name,value in shards.items():assert (tmp_path/'stream'/name).read_bytes()==canonical(value)+b'\n'


def test_stream_verifier_accepts_prior_compatible_bundle(tmp_path):
    index,shards=build('f'*64,'development_qualification','methods',list(jobs()),3000,3)
    write(tmp_path/'old',index,shards)
    assert verify(tmp_path/'old',fingerprint(index))==index


@pytest.mark.parametrize('bad',['duplicate','reordered','oversize','empty'])
def test_partial_generation_never_publishes_index_or_reuses_root(tmp_path,bad):
    values=list(jobs(5));maximum_bytes=1000
    if bad=='duplicate':values[3]=values[2]
    elif bad=='reordered':values.reverse()
    elif bad=='oversize':values[-1]['request']['payload']='x'*2000
    else:values=[]
    with pytest.raises(ValueError):write_sorted(tmp_path/'partial','f'*64,'development_qualification','methods',iter(values),maximum_bytes,1)
    assert not (tmp_path/'partial/index.json').exists() and (tmp_path/'partial/generation_claim.json').exists()
    with pytest.raises(FileExistsError):write_sorted(tmp_path/'partial','f'*64,'development_qualification','methods',jobs(),maximum_bytes,1)


def test_modified_request_and_extra_files_revoke_complete_phase(tmp_path):
    index=write_sorted(tmp_path/'phase','f'*64,'development_qualification','methods',jobs())
    path=tmp_path/'phase/shard-000000.json';raw=path.read_bytes();path.write_bytes(raw.replace(b'xxxx',b'yyyy',1))
    with pytest.raises(ValueError,match='bytes changed'):verify(tmp_path/'phase',fingerprint(index))
    path.write_bytes(raw);(tmp_path/'phase/unplanned.json').write_text('{}')
    with pytest.raises(ValueError,match='unexpected'):verify(tmp_path/'phase',fingerprint(index))


def approved(payload):
    return dict(authorized=payload['index']['phase']=='development_qualification',
        index_sha256=payload['index_sha256'],execution_root=payload['execution_root'])


def response(_):
    return dict(raw_response=b'{"answer":"fixture"}',stdout=b'fixture',stderr=b'',returncode=0,transport_policy_passed=True)


def test_stream_execution_retains_single_attempts_and_crash_disposition(tmp_path):
    from analysis.hexar_external.confirmatory_v1.streaming_registry_shards_v1 import StreamingExecutor
    index=write_sorted(tmp_path/'phase','f'*64,'development_qualification','methods',jobs(4),2000,2)
    engine=StreamingExecutor(tmp_path/'run',tmp_path/'phase',fingerprint(index),approved);calls=[]
    assert engine.execute('opaque-000000',lambda req:calls.append(req) or response(req))['dispatch_performed']
    def crash(_):raise KeyboardInterrupt('synthetic interruption')
    with pytest.raises(KeyboardInterrupt):engine.execute('opaque-000001',crash)
    resumed=StreamingExecutor(tmp_path/'run',tmp_path/'phase',fingerprint(index),approved)
    assert not resumed.execute('opaque-000000',lambda _:pytest.fail('no retry'))['dispatch_performed']
    closed=resumed.execute('opaque-000001',lambda _:pytest.fail('no crash retry'))
    assert closed['outcome']['status']=='INDETERMINATE_AFTER_CRASH' and not closed['dispatch_performed']
    assert resumed.execute('opaque-000003',response)['dispatch_performed'] and len(calls)==1


def test_denied_stream_admission_creates_no_execution_root(tmp_path):
    from analysis.hexar_external.confirmatory_v1.streaming_registry_shards_v1 import StreamingExecutor
    index=write_sorted(tmp_path/'phase','f'*64,'development_qualification','methods',jobs())
    with pytest.raises(ValueError,match='admission'):
        StreamingExecutor(tmp_path/'run',tmp_path/'phase',fingerprint(index),lambda _:dict(authorized=False))
    assert not (tmp_path/'run').exists()


def test_changed_stream_requested_shard_prevents_new_provider_attempt(tmp_path):
    from analysis.hexar_external.confirmatory_v1.streaming_registry_shards_v1 import StreamingExecutor
    index=write_sorted(tmp_path/'phase','f'*64,'development_qualification','methods',jobs())
    engine=StreamingExecutor(tmp_path/'run',tmp_path/'phase',fingerprint(index),approved)
    p=tmp_path/'phase/shard-000000.json';p.write_bytes(p.read_bytes().replace(b'xxxx',b'yyyy',1))
    with pytest.raises(ValueError,match='bytes changed'):
        engine.execute('opaque-000000',lambda _:pytest.fail('no provider attempt'))
