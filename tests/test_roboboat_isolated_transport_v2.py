import json
import subprocess
from pathlib import Path

import pytest
import roboboat_isolated_transport_v2 as transport


def test_timeout_never_serializes_provider_command_secret(tmp_path, monkeypatch):
    packet = tmp_path/'packet'; packet.mkdir(); (packet/'evidence.json').write_text('{}')
    secret = 'synthetic-provider-secret-do-not-retain'
    def fail(command, **kwargs):
        raise subprocess.TimeoutExpired(['bwrap','--setenv','TEST_KEY',secret], 3,
                                        output=b'{"type":"progress"}\n', stderr=b'partial diagnostic')
    monkeypatch.setattr(transport, 'isolated_run', fail)
    with pytest.raises(RuntimeError, match='retained failure'):
        transport.call(tmp_path/'calls', 'test', packet, 'prompt', 'model', 'high', {}, timeout=3)
    files=list((tmp_path/'calls').glob('*.json')); assert len(files)==1
    record=json.loads(files[0].read_text())
    assert secret not in files[0].read_text()
    assert 'bwrap' not in record['error']
    assert record['return_code']==124 and record['attempt_count']==1
    assert record['events']==[{'type':'progress'}]
    assert record['timeout_s']==3


def test_partial_trace_redacts_secret_in_stdout_and_stderr(tmp_path, monkeypatch):
    packet=tmp_path/'packet';packet.mkdir();(packet/'evidence.json').write_text('{}')
    secret='synthetic-key'
    monkeypatch.setattr(transport,'provider_secret_values',lambda:(secret,))
    def fail(*args, **kwargs):
        raise subprocess.TimeoutExpired(['hidden-command',secret],3,
            output=json.dumps({'message':secret}).encode(),stderr=('error '+secret).encode())
    monkeypatch.setattr(transport,'isolated_run',fail)
    with pytest.raises(RuntimeError):transport.call(tmp_path/'calls','r',packet,'p','m','high',{},timeout=3)
    p=next((tmp_path/'calls').glob('*.json'));record=json.loads(p.read_text())
    assert secret not in p.read_text()
    assert record['events']==[{'message':'[PROVIDER_CREDENTIAL_REDACTED]'}]
    assert record['partial_trace'] and '[PROVIDER_CREDENTIAL_REDACTED]' in record['stderr']


def test_valid_cache_and_timeout_identity_preserve_one_call_per_request(tmp_path, monkeypatch):
    packet=tmp_path/'packet';packet.mkdir();(packet/'evidence.json').write_text('{}')
    calls=[]
    monkeypatch.setattr(transport,'provider_secret_values',lambda:())
    def success(command, **kwargs):
        calls.append(kwargs['timeout'])
        Path(command[command.index('--output-last-message')+1]).write_text('{"answer":"supported"}')
        return subprocess.CompletedProcess(command,0,'{"type":"done"}\n','')
    monkeypatch.setattr(transport,'isolated_run',success)
    args=(tmp_path/'calls','r',packet,'p','m','high',{})
    a=transport.call(*args,timeout=3);assert transport.call(*args,timeout=3)==a
    b=transport.call(*args,timeout=6)
    assert a['cache_key']!=b['cache_key'] and calls==[3,6]
    assert a['parsed_final']=={'answer':'supported'}


def test_failed_cache_never_reissues_and_answer_secret_is_excluded(tmp_path, monkeypatch):
    packet=tmp_path/'packet';packet.mkdir();(packet/'evidence.json').write_text('{}')
    secret='synthetic-key';calls=[]
    monkeypatch.setattr(transport,'provider_secret_values',lambda:(secret,))
    def success(command, **kwargs):
        calls.append(1)
        Path(command[command.index('--output-last-message')+1]).write_text(json.dumps({'answer':secret}))
        return subprocess.CompletedProcess(command,0,'','')
    monkeypatch.setattr(transport,'isolated_run',success)
    args=(tmp_path/'calls','r',packet,'p','m','high',{})
    with pytest.raises(RuntimeError):transport.call(*args)
    with pytest.raises(RuntimeError):transport.call(*args)
    p=next((tmp_path/'calls').glob('*.json'));d=json.loads(p.read_text())
    assert calls==[1] and secret not in p.read_text() and d['status']=='failed'
    assert d['parsed_final']['answer']=='[PROVIDER_CREDENTIAL_REDACTED]'


def test_invalid_structured_return_retains_only_safe_error_kind(tmp_path, monkeypatch):
    packet=tmp_path/'packet';packet.mkdir();(packet/'evidence.json').write_text('{}')
    monkeypatch.setattr(transport,'provider_secret_values',lambda:())
    def invalid(command, **kwargs):
        Path(command[command.index('--output-last-message')+1]).write_text('invalid-json')
        return subprocess.CompletedProcess(command,0,'','')
    monkeypatch.setattr(transport,'isolated_run',invalid)
    with pytest.raises(RuntimeError):transport.call(tmp_path/'calls','r',packet,'p','m','high',{})
    d=json.loads(next((tmp_path/'calls').glob('*.json')).read_text())
    assert d['error_kind']=='ValueError' and d['error']=='Provider output could not be parsed.'
