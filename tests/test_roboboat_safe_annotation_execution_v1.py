import json
import subprocess
from types import SimpleNamespace
import pytest
import roboboat_safe_annotation_execution_v1 as safe


def test_timeout_never_exposes_command_and_retains_sanitized_partial(monkeypatch):
    monkeypatch.setattr(safe.transport, 'provider_secret_values', lambda: ('secret-value',))
    def fail(*args, **kwargs):
        raise subprocess.TimeoutExpired(['--setenv', 'secret-value'], 300,
            output=b'partial secret-value', stderr=b'error secret-value')
    monkeypatch.setattr(safe.transport, 'isolated_run', fail)
    with pytest.raises(subprocess.TimeoutExpired) as caught:
        safe.safe_isolated_run(['codex'], timeout=300)
    assert 'secret-value' not in str(caught.value)
    assert caught.value.output == 'partial [PROVIDER_CREDENTIAL_REDACTED]'
    assert caught.value.timeout == 300


def test_normal_call_preserves_settings_and_output(monkeypatch, tmp_path):
    output=tmp_path/'answer.json'; output.write_text('{"answer":"valid"}')
    command=['codex','--output-last-message',str(output)]
    monkeypatch.setattr(safe.transport,'provider_secret_values',lambda: ('secret-value',))
    def run(cmd, **kwargs):
        assert cmd is command
        assert kwargs == {'input':'frozen prompt','timeout':300}
        return subprocess.CompletedProcess(['secret-value'],0,'normal','secret-value')
    monkeypatch.setattr(safe.transport,'isolated_run',run)
    result=safe.safe_isolated_run(command,input='frozen prompt',timeout=300)
    assert result.returncode == 0 and result.stdout == 'normal'
    assert 'secret-value' not in str(result)
    assert output.read_text() == '{"answer":"valid"}'


def test_credential_final_is_excluded(monkeypatch,tmp_path):
    output=tmp_path/'answer.json';output.write_text('secret-value')
    monkeypatch.setattr(safe.transport,'provider_secret_values',lambda: ('secret-value',))
    monkeypatch.setattr(safe.transport,'isolated_run',lambda *a,**k: subprocess.CompletedProcess([],0,'',''))
    result=safe.safe_isolated_run(['codex','--output-last-message',str(output)])
    assert result.returncode == 125 and 'secret-value' not in output.read_text()


def test_private_atomizer_override_preserves_frozen_request_and_no_retry(monkeypatch,tmp_path):
    text='Completion is unknown.'
    freeze=json.loads((safe.atomizer.DOC/'marine_atomization_freeze_v5.json').read_text())
    original=safe.atomizer.call
    calls=[]
    def call(cache,role,work,prompt,model,effort,schema,allow_tools,timeout=300):
        calls.append(role)
        assert model == freeze['candidate']['model'] and effort == freeze['candidate']['reasoning_effort']
        assert timeout == 300 and allow_tools is False and 'secret-gold' not in prompt
        assert text in prompt
        entry=json.loads((work/'response.json').read_text())
        assert set(entry) == {'opaque_response_id','response_text'}
        return {'cache_key':'test','parsed_final':{
            'schema':'crane-evidence-calibration-atomization-return/v1',
            'opaque_response_id':entry['opaque_response_id'],
            'claims':[{'response_span':text,'claim_text':text,'asserted_abstraction_level':'task_outcome'}],
            'unresolved_spans':[], 'attestation':'METHOD_BLIND_EXHAUSTIVE_EXTRACTION_ATTEMPT'}}
    monkeypatch.setattr(safe.transport,'call',call)
    case={'case_id':'opaque','response_text':text,'expected':['secret-gold']}
    first=safe.safe_execute(case,'A',freeze,tmp_path)
    assert safe.safe_execute(case,'A',freeze,tmp_path) == first
    assert len(calls) == 1 and safe.atomizer.call is original
    assert first['endpoint_scoring_authorized'] is False


def test_support_override_uses_only_fresh_caller(monkeypatch):
    caller=SimpleNamespace(runner='old',model='frozen',effort='high',timeout_s=300)
    other=SimpleNamespace(runner='old')
    def annotate(packet,output,*,caller):
        assert caller.runner is safe.safe_isolated_run
        assert (caller.model,caller.effort,caller.timeout_s) == ('frozen','high',300)
        return 'done'
    monkeypatch.setattr(safe,'qualified_annotate',annotate)
    assert safe.safe_annotate('packet','output',caller=caller) == 'done'
    assert other.runner == 'old'
