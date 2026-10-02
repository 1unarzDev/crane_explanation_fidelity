from concurrent.futures import ThreadPoolExecutor
import json
import threading

import pytest
from analysis.hexar_external.confirmatory_v1.streaming_registry_shards_v1 import write_sorted
from analysis.hexar_external.confirmatory_v1.streaming_registry_executor_v2 import StreamingExecutorV2
from analysis.hexar_external.confirmatory_v1.journal import canonical,fingerprint


def approve(payload):
    return dict(authorized=True,index_sha256=payload['index_sha256'],execution_root=payload['execution_root'])


def fixture(tmp_path):
    jobs=[dict(job_id=f'opaque-{i}',request=dict(role='method',maximum_response_bytes=1024)) for i in range(4)]
    index=write_sorted(tmp_path/'payloads','a'*64,'development_qualification','methods',iter(jobs))
    return StreamingExecutorV2(tmp_path/'run',tmp_path/'payloads',fingerprint(index),approve)


def response(_):
    return dict(raw_response=b'{"answer":"fixture"}',stdout=b'exact',stderr=b'',returncode=0,transport_policy_passed=True)


def test_concurrent_jobs_cannot_read_partial_initial_registry_and_provider_calls_overlap(tmp_path,monkeypatch):
    import analysis.hexar_external.confirmatory_v1.registered_attempt_executor_v2 as executor
    engine=fixture(tmp_path);opened=threading.Event();release=threading.Event();barrier=threading.Barrier(2);calls=[]
    original=executor.exclusive_json
    def paused(path,value):
        if path.name=='registered_jobs.json':
            with path.open('xb') as stream:
                opened.set()
                assert release.wait(5)
                stream.write(canonical(value)+b'\n')
        else:original(path,value)
    monkeypatch.setattr(executor,'exclusive_json',paused)
    def backend(request):
        calls.append(request);barrier.wait(timeout=5)
        return response(request)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first=pool.submit(engine.execute,'opaque-0',backend)
        assert opened.wait(5)
        second=pool.submit(engine.execute,'opaque-1',backend)
        # First writer has opened a zero-byte file; the second constructor
        # must wait for the lock rather than parse that file or dispatch.
        assert not second.done() and calls==[]
        release.set()
        assert first.result(timeout=10)['outcome']['status']=='VALID'
        assert second.result(timeout=10)['outcome']['status']=='VALID'
    assert len(calls)==2
    assert not engine.execute('opaque-0',lambda _:pytest.fail('no retry'))['dispatch_performed']


def test_concurrent_phase_initializers_never_read_partial_index(tmp_path,monkeypatch):
    import analysis.hexar_external.confirmatory_v1.streaming_registry_executor_v2 as module
    jobs=[dict(job_id='opaque',request=dict(role='method',maximum_response_bytes=1024))]
    index=write_sorted(tmp_path/'payloads','a'*64,'development_qualification','methods',iter(jobs))
    opened=threading.Event();release=threading.Event();original=module.exclusive_json
    def paused(path,value):
        if path.name=='phase_index.json':
            with path.open('xb') as stream:
                opened.set();assert release.wait(5);stream.write(canonical(value)+b'\n')
        else:original(path,value)
    monkeypatch.setattr(module,'exclusive_json',paused)
    with ThreadPoolExecutor(max_workers=2) as pool:
        make=lambda:StreamingExecutorV2(tmp_path/'run',tmp_path/'payloads',fingerprint(index),approve)
        first=pool.submit(make);assert opened.wait(5);second=pool.submit(make)
        release.set();assert first.result(timeout=10).index==second.result(timeout=10).index


def test_crashed_partial_registry_is_rejected_without_overwrite_or_provider(tmp_path):
    engine=fixture(tmp_path);path=tmp_path/'run/shard-000000';path.mkdir();(path/'registered_jobs.json').write_bytes(b'')
    with pytest.raises(ValueError):engine.execute('opaque-0',lambda _:pytest.fail('no provider'))
    assert (path/'registered_jobs.json').read_bytes()==b'' and not (path/'journal').exists()


def test_denied_constructor_does_not_create_root(tmp_path):
    jobs=[dict(job_id='opaque',request=dict(role='method',maximum_response_bytes=1024))]
    index=write_sorted(tmp_path/'payloads','a'*64,'development_qualification','methods',iter(jobs))
    with pytest.raises(ValueError,match='admission'):
        StreamingExecutorV2(tmp_path/'run',tmp_path/'payloads',fingerprint(index),lambda _:dict(authorized=False))
    assert not (tmp_path/'run').exists()
