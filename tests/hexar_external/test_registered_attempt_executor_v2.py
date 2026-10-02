import json
from pathlib import Path

import pytest

from analysis.hexar_external.confirmatory_v1.journal import fingerprint
from analysis.hexar_external.confirmatory_v1.registered_attempt_executor_v2 import registry, RegisteredExecutor


def registered():
    return registry('f'*64, 'development_qualification', [dict(job_id='opaque-fixture',
        request=dict(role='method', maximum_response_bytes=1024, payload={'visible': 'fixture only'}))])


def synthetic_admit(value):
    return dict(authorized=value['phase'] == 'development_qualification',
                registry_sha256=fingerprint(value), binding_sha256=value['binding_sha256'], phase=value['phase'])


def response(raw=b'{"answer":"Supported fixture answer."}'):
    return dict(raw_response=raw, stdout=b'fixture transport log', stderr=b'',
                returncode=0, transport_policy_passed=True)


def test_duplicate_dispatch_reuses_byte_verified_closed_outcome(tmp_path):
    engine = RegisteredExecutor(tmp_path / 'execution', registered(), synthetic_admit)
    calls = []
    first = engine.execute('opaque-fixture', lambda request: calls.append(request) or response())
    second = engine.execute('opaque-fixture', lambda request: pytest.fail('no retry'))
    assert first['outcome']['status'] == 'VALID'
    assert first['dispatch_performed'] and not second['dispatch_performed']
    assert len(calls) == 1 and first['outcome'] == second['outcome']
    (tmp_path / 'execution' / fingerprint({'opaque_job': 'opaque-fixture'}) / 'raw_response.json').write_bytes(b'changed')
    with pytest.raises(ValueError, match='archive changed'):
        engine.execute('opaque-fixture', lambda request: pytest.fail('no retry'))


@pytest.mark.parametrize('raw', [b'{"answer":"first","answer":"second"}', b'{"answer":NaN}',
                               b'{"answer":""}', b'{"answer":"ok","extra":1}'])
def test_invalid_response_is_retained_once_without_repair(tmp_path, raw):
    engine = RegisteredExecutor(tmp_path / 'execution', registered(), synthetic_admit)
    first = engine.execute('opaque-fixture', lambda request: response(raw))
    assert first['outcome']['status'] == 'TECHNICAL_FAILURE'
    assert (tmp_path / 'execution' / fingerprint({'opaque_job': 'opaque-fixture'}) / 'raw_response.json').read_bytes() == raw
    second = engine.execute('opaque-fixture', lambda request: pytest.fail('no repair retry'))
    assert second['outcome'] == first['outcome']


def test_crash_claim_never_reissues_and_retains_indeterminate_disposition(tmp_path):
    engine = RegisteredExecutor(tmp_path / 'execution', registered(), synthetic_admit)
    def crash(request):
        raise KeyboardInterrupt()
    with pytest.raises(KeyboardInterrupt):
        engine.execute('opaque-fixture', crash)
    result = engine.execute('opaque-fixture', lambda request: pytest.fail('claimed call cannot reissue'))
    assert result['outcome']['status'] == 'INDETERMINATE_AFTER_CRASH'
    assert result['dispatch_performed'] is False


def test_unknown_request_changed_registry_or_failed_admission_never_dispatch(tmp_path):
    engine = RegisteredExecutor(tmp_path / 'execution', registered(), synthetic_admit)
    with pytest.raises(ValueError, match='unscheduled'):
        engine.execute('unknown', lambda request: pytest.fail('unknown call'))
    changed = registered(); changed['jobs'][0]['request']['payload']['visible'] = 'different request'
    changed['jobs'][0]['request_sha256'] = fingerprint(changed['jobs'][0]['request'])
    with pytest.raises(ValueError, match='another registry'):
        RegisteredExecutor(tmp_path / 'execution', changed, synthetic_admit)
    (tmp_path / 'execution' / 'registered_jobs.json').write_text('{}')
    with pytest.raises(ValueError, match='on-disk registry changed'):
        engine.execute('opaque-fixture', lambda request: pytest.fail('changed registry'))
    confirmation = registered(); confirmation['phase'] = 'confirmation'
    with pytest.raises(ValueError, match='admission failed'):
        RegisteredExecutor(tmp_path / 'forbidden-confirmation', confirmation, synthetic_admit)
    assert not (tmp_path / 'forbidden-confirmation').exists()


def test_admission_is_rechecked_after_registration(tmp_path):
    allowed = [True]
    def admit(value):
        result = synthetic_admit(value); result['authorized'] = allowed[0]; return result
    engine = RegisteredExecutor(tmp_path / 'execution', registered(), admit)
    allowed[0] = False
    with pytest.raises(ValueError, match='admission failed'):
        engine.execute('opaque-fixture', lambda request: pytest.fail('gate closed'))
    assert not list((tmp_path / 'execution' / 'journal').glob('*.claim.json'))


def test_concurrent_caller_cannot_close_a_live_backend_as_a_crash(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    engine = RegisteredExecutor(tmp_path / 'execution', registered(), synthetic_admit)
    entered, release = Event(), Event()
    def backend(request):
        entered.set()
        assert release.wait(5)
        return response()
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(engine.execute, 'opaque-fixture', backend)
        try:
            assert entered.wait(5)
            with pytest.raises(ValueError, match='still active'):
                engine.execute('opaque-fixture', lambda request: pytest.fail('duplicate active dispatch'))
            assert engine.journal.state(dict(opaque_job='opaque-fixture')) == 'CLAIMED_NO_REISSUE'
        finally:
            release.set()
        retained = future.result(timeout=5)
    assert retained['outcome']['status'] == 'VALID'
    assert not engine.execute('opaque-fixture', lambda request: pytest.fail('no reissue'))['dispatch_performed']


def test_complete_registry_can_exceed_semantic_response_cap(tmp_path):
    sealed = registry('f'*64, 'development_qualification', [dict(job_id='opaque-fixture',
        request=dict(role='method', maximum_response_bytes=1024, payload={'fixture':'x'*(1100*1024)}))])
    engine = RegisteredExecutor(tmp_path/'execution', sealed, synthetic_admit)
    result = engine.execute('opaque-fixture', lambda request: response())
    assert result['outcome']['status'] == 'VALID'
    assert (tmp_path/'execution'/'registered_jobs.json').stat().st_size > 1024*1024
    assert not engine.execute('opaque-fixture', lambda request: pytest.fail('no retry'))['dispatch_performed']
