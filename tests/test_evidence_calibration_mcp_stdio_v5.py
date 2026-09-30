from dataclasses import asdict
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'analysis'))
from evidence_calibration_io import canonical_sha256
from evidence_calibration_local_tool_sandbox_v2 import Limits
from evidence_calibration_local_tool_sandbox_v10 import TreeLimits, ScratchLimits, CpuBudget
from evidence_calibration_mcp_stdio_v5 import Server, PROTOCOL, encode
from evidence_calibration_tool_broker_v7 import READ, COMPUTE, tool_definitions
from evidence_calibration_computation_cpu_ledger_v2 import ComputationCpuLimit
from stage_evidence_calibration_workspace import inventory

LIMITS = Limits(wall_seconds=2, cpu_seconds_per_process=1,
                address_space_bytes_per_process=128*1024**2, combined_output_bytes=1024)


def config(tmp_path, method='B2', **overrides):
    workspace = tmp_path / 'job'
    workspace.mkdir()
    (workspace / 'visible.txt').write_text('αβ visible')
    identity = {'method_id': method, 'inventory': inventory(workspace)}
    identity['workspace_sha256'] = canonical_sha256(identity)
    return {'workspace': str(workspace), 'identity': identity, 'records': str(tmp_path / 'events'),
            'limits': asdict(LIMITS), 'tree_limits': asdict(TreeLimits(64*1024**2,16,100)), 'scratch_limits': asdict(ScratchLimits(1024**2,1024**2)), 'cpu_budget': asdict(CpuBudget(1_000_000_000,20,250)), 'computation_cpu_limit': asdict(ComputationCpuLimit(5_000_000_000)), 'max_calls': 5, 'max_messages': 30,
            'max_request_bytes': 4096, **overrides}


def server(c):
    return Server(Path(c['workspace']), c['identity'], Path(c['records']), limits=Limits(**c['limits']), tree_limits=TreeLimits(**c['tree_limits']), scratch_limits=ScratchLimits(**c['scratch_limits']), cpu_budget=CpuBudget(**c['cpu_budget']), computation_cpu_limit=ComputationCpuLimit(**c['computation_cpu_limit']),
                  max_calls=c['max_calls'], max_messages=c['max_messages'], max_request_bytes=c['max_request_bytes'])


def rpc(method, params=None, id=1):
    obj = {'jsonrpc': '2.0', 'method': method}
    if params is not None: obj['params'] = params
    if id is not None: obj['id'] = id
    return encode(obj)


def initialized(s):
    result = json.loads(s.handle(rpc('initialize', {'protocolVersion': '2099-01-01',
        'capabilities': {}, 'clientInfo': {'name': 'synthetic-client', 'version': 'test'}}, id=0)))
    assert result['result']['protocolVersion'] == PROTOCOL
    assert result['result']['capabilities'] == {'tools': {'listChanged': False}}
    assert s.handle(rpc('notifications/initialized', id=None)) is None


def tool(s, name, arguments, id=2):
    return json.loads(s.handle(rpc('tools/call', {'name': name, 'arguments': arguments}, id=id)))


@pytest.mark.parametrize('method', ['B0', 'B1', 'B2', 'B3', 'B4'])
def test_wire_definitions_exactly_match_assigned_method(tmp_path, method):
    s = server(config(tmp_path, method))
    initialized(s)
    result = json.loads(s.handle(rpc('tools/list')))
    assert result['result']['tools'] == tool_definitions(method)
    record = json.loads((s.records / 'rpc-00000003.result.json').read_text())
    assert record['response'] == result
    assert record['response_sha256'] == hashlib.sha256(encode(result)).hexdigest()
    denied = tool(s, 'host_shell', {'command': 'anything'})
    assert denied['error']['code'] == -32602 and s.broker.calls == 0
    if method in {'B0', 'B1'}:
        assert tool(s, COMPUTE, {'code': 'print(1)'}, id=3)['error']['code'] == -32602


def test_lossless_read_and_actual_namespaced_computation(tmp_path):
    s = server(config(tmp_path))
    initialized(s)
    read = tool(s, READ, {'path': 'visible.txt', 'offset': 0, 'length': None})['result']
    assert not read['isError'] and read['structuredContent']['result']['text'] == 'αβ visible'
    assert json.loads(read['content'][0]['text']) == read['structuredContent']
    compute = tool(s, COMPUTE, {'code': "import pathlib; print(pathlib.Path('visible.txt').read_text()); print(pathlib.Path('/home').exists())"}, id=3)['result']
    assert compute['structuredContent']['result']['stdout'] == 'αβ visible\nFalse\n'
    assert not compute['isError']
    assert (s.records / 'tool-00000004.result.json').is_file()


def test_failure_bytes_stay_in_audit_and_repeated_call_id_is_not_reexecuted(tmp_path):
    s = server(config(tmp_path))
    initialized(s)
    failed = tool(s, COMPUTE, {'code': 'print("x"*2048)'})['result']
    assert failed['isError'] and failed['structuredContent']['result'] is None
    assert 'base64' not in json.dumps(failed)
    terminal = json.loads((s.records / 'tool-00000003.result.json').read_text())
    assert terminal['execution_audit']['execution_audit']['captured_bytes'] == 1024
    again = tool(s, COMPUTE, {'code': 'print(1)'})
    assert again['error']['code'] == -32600 and s.broker.calls == 1


def test_bad_read_and_nonzero_exit_are_tool_errors(tmp_path):
    s = server(config(tmp_path))
    initialized(s)
    assert tool(s, READ, {'path': '../truth', 'offset': 0, 'length': None})['result']['isError']
    error = tool(s, COMPUTE, {'code': "raise RuntimeError('synthetic')"}, id=3)['result']
    assert error['isError'] and error['structuredContent']['status'] == 'TOOL_RUNTIME_FAILURE'
    assert 'synthetic' in error['structuredContent']['result']['stderr']


@pytest.mark.parametrize('raw,code', [
    (b'{"jsonrpc":"2.0","id":1,"method":"ping","method":"tools/list"}\n', -32700),
    (b'{"jsonrpc":"2.0","id":NaN,"method":"ping"}\n', -32700),
    (b'{"jsonrpc":"2.0","id":1,"method":"ping","params":{"n":1e999}}\n', -32700),
    (b'{"jsonrpc":"2.0","id":"\\ud800","method":"ping"}\n', -32700),
    (b'[]\n', -32600), (rpc('ping', id=True), -32600), (b'\xff\n', -32700)])
def test_strict_wire_parser_rejects_ambiguous_records(tmp_path, raw, code):
    s = server(config(tmp_path))
    response = json.loads(s.handle(raw))
    assert response['error']['code'] == code
    assert s.broker.calls == 0


def test_lifecycle_unknown_routes_and_budget_denied(tmp_path):
    s = server(config(tmp_path, max_calls=1))
    assert json.loads(s.handle(rpc('tools/list')))['error']['code'] == -32000
    initialized(s)
    for index, method in enumerate(('resources/read', 'prompts/get', 'sampling/createMessage'), start=10):
        assert json.loads(s.handle(rpc(method, id=index)))['error']['code'] == -32601
    tool(s, COMPUTE, {'code': 'print(1)'}, id=20)
    assert tool(s, COMPUTE, {'code': 'print(2)'}, id=21)['error']['code'] == -32000
    assert s.broker.calls == 1


@pytest.mark.parametrize('raw', [b'x'*4097, b'{"jsonrpc":"2.0","method":"ping","id":1}'])
def test_framing_failure_stops_without_processing_following_request(tmp_path, raw):
    s = server(config(tmp_path))
    response = json.loads(s.handle(raw))
    assert response['error']['code'] == -32000 and s.finished
    assert json.loads((s.records / 'session.result.json').read_text())['status'] == 'REQUEST_FRAMING_FAILURE'
    with pytest.raises(ValueError, match='terminal'):
        s.handle(rpc('ping'))


@pytest.mark.parametrize('method', ['B0', 'B1', 'B2', 'B3', 'B4'])
def test_real_stdio_subprocess_has_only_jsonrpc_stdout_and_fresh_namespace(tmp_path, method):
    c = config(tmp_path, method)
    path = tmp_path / 'configuration.json'
    path.write_text(json.dumps(c))
    messages = [rpc('initialize', {'protocolVersion': PROTOCOL, 'capabilities': {},
        'clientInfo': {'name': 'synthetic', 'version': '1'}}, id=0),
        rpc('notifications/initialized', id=None), rpc('tools/list'),
        rpc('tools/call', {'name': COMPUTE, 'arguments': {'code': 'print(6*7)'}}, id=2)]
    argv = [sys.executable, str(ROOT / 'analysis/evidence_calibration_mcp_stdio_v5.py'), '--configuration', str(path)]
    result = subprocess.run(argv, input=b''.join(messages), capture_output=True, timeout=10)
    assert result.returncode == 0 and result.stderr == b''
    responses = [json.loads(line) for line in result.stdout.splitlines()]
    assert len(responses) == 3 and all(row['jsonrpc'] == '2.0' for row in responses)
    assert responses[1]['result']['tools'] == tool_definitions(method)
    if method in {'B0', 'B1'}:
        assert responses[-1]['error']['code'] == -32602
    else:
        assert responses[-1]['result']['structuredContent']['result']['stdout'] == '42\n'
    terminal = Path(c['records']) / 'session.result.json'
    assert json.loads(terminal.read_text())['status'] == 'STDIN_EOF'
    # A restart cannot adopt any prior session/event namespace.
    restart = subprocess.run(argv, input=b'', capture_output=True, timeout=10)
    assert restart.returncode != 0 and restart.stdout == b''
    assert b'fresh event namespace' in restart.stderr


def test_message_budget_stops_and_retains_terminal(tmp_path):
    s = server(config(tmp_path, max_messages=1))
    out = io.BytesIO()
    s.serve(io.BytesIO(rpc('ping') + rpc('ping', id=2)), out)
    assert len(out.getvalue().splitlines()) == 1
    assert json.loads((s.records / 'session.result.json').read_text())['status'] == 'MESSAGE_BUDGET_EXHAUSTED'


def test_retention_failure_stops_instead_of_returning_tool_result(tmp_path, monkeypatch):
    s = server(config(tmp_path))
    initialized(s)
    import evidence_calibration_tool_broker_v7 as broker_module
    original = broker_module._write_once
    def fail_terminal(path, value):
        if path.name.endswith('.result.json'): raise OSError('synthetic storage failure')
        return original(path, value)
    monkeypatch.setattr(broker_module, '_write_once', fail_terminal)
    sink = io.BytesIO()
    with pytest.raises(OSError, match='storage failure'):
        s.serve(io.BytesIO(rpc('tools/call', {'name': COMPUTE, 'arguments': {'code': 'print(1)'}})), sink)
    assert sink.getvalue() == b'' and s.finished
    assert json.loads((s.records / 'session.result.json').read_text())['status'] == 'LOCAL_SERVER_FAILURE'
    assert (s.records / 'tool-00000003.intent.json').exists()
    assert not (s.records / 'tool-00000003.result.json').exists()
    assert not (s.records / 'rpc-00000003.result.json').exists()


def test_real_stdio_framing_failure_exits_nonzero_and_does_not_resume(tmp_path):
    c = config(tmp_path)
    path = tmp_path / 'configuration.json'
    path.write_text(json.dumps(c))
    result = subprocess.run([sys.executable, str(ROOT / 'analysis/evidence_calibration_mcp_stdio_v5.py'),
        '--configuration', str(path)], input=b'x'*4097 + b'\n' + rpc('ping'), capture_output=True, timeout=10)
    assert result.returncode == 65 and result.stderr == b''
    responses = result.stdout.splitlines()
    assert len(responses) == 1 and json.loads(responses[0])['error']['code'] == -32000
    terminal = json.loads((Path(c['records']) / 'session.result.json').read_text())
    assert terminal['status'] == 'REQUEST_FRAMING_FAILURE' and terminal['messages_received'] == 1


def test_incomplete_namespace_lifecycle_is_null_error_without_audit_bytes(tmp_path,monkeypatch):
    import evidence_calibration_local_tool_sandbox_v10 as executor
    original=executor.bounded_namespace_command
    def fault(*args):
        argv=original(*args);i=argv.index('--')
        argv[i:i]=['--ro-bind',str(tmp_path/'registered-absent-source'),'/absent'];return argv
    monkeypatch.setattr(executor,'bounded_namespace_command',fault)
    s=server(config(tmp_path));initialized(s)
    result=tool(s,COMPUTE,{'code':"print('must not execute')"})['result']
    assert result['isError'] and result['structuredContent']['result'] is None
    assert 'NAMESPACE_LIFECYCLE_INCOMPLETE' in result['structuredContent']['error']
    assert 'base64' not in json.dumps(result)
    terminal=json.loads((s.records/'tool-00000003.result.json').read_text())
    assert not terminal['execution_audit']['namespace_lifecycle']['payload_exit_verified']


def test_setup_looking_program_error_retains_runtime_failure_on_wire(tmp_path):
    s=server(config(tmp_path));initialized(s)
    result=tool(s,COMPUTE,{'code':"import sys;print('bwrap: synthetic mount error',file=sys.stderr);sys.exit(7)"})['result']
    assert result['isError'] and result['structuredContent']['status']=='TOOL_RUNTIME_FAILURE'
    assert result['structuredContent']['result']['return_code']==7
    inner=json.loads((s.records/'tool-00000003.execution/terminal.json').read_text())
    assert inner['namespace_lifecycle']['payload_exit_verified']


def test_explicit_scratch_configuration_is_required(tmp_path):
    c=config(tmp_path);del c['scratch_limits']
    with pytest.raises(KeyError):server(c)


def test_explicit_cpu_configuration_is_required_and_bound(tmp_path):
    c=config(tmp_path)
    saved=c.pop('cpu_budget')
    with pytest.raises(KeyError):server(c)
    assert not Path(c['records']).exists()
    c['cpu_budget']=saved
    s=server(c);initialized(s)
    assert s.descriptor['cpu_budget']==saved
    session=json.loads((s.records/'session.intent.json').read_text())
    assert session['cpu_budget']==saved
    assert session['schema']=='crane-local-mcp-session/v5-development'


def test_sampled_cpu_cutoff_is_null_error_without_audit_bytes_on_wire(tmp_path):
    c=config(tmp_path,cpu_budget=asdict(CpuBudget(300_000_000,20,250)))
    s=server(c);initialized(s)
    code="import subprocess,sys\ncs=[subprocess.Popen([sys.executable,'-c','while True: pass'],start_new_session=True) for _ in range(4)]\nprint('partial',flush=True)\nfor child in cs:child.wait()"
    reply=tool(s,COMPUTE,{'code':code})['result']
    assert reply['isError']
    assert reply['structuredContent']['status']=='TECHNICAL_FAILURE'
    assert reply['structuredContent']['result'] is None
    assert reply['structuredContent']['error']=='CUMULATIVE_CPU_LIMIT'
    assert 'base64' not in json.dumps(reply) and 'partial' not in json.dumps(reply)
    outer=json.loads((s.records/'tool-00000003.result.json').read_text())
    inner=outer['execution_audit']
    assert inner['cpu_accounting']['budget']==c['cpu_budget']
    assert inner['cpu_accounting']['final_cpu_nanoseconds']>=300_000_000
    assert inner['cleanup']['final_state']['stdout'].strip()=='not-found'


def test_total_is_required_in_constructor_and_strict_configuration(tmp_path):
    c=config(tmp_path)
    saved=c.pop('computation_cpu_limit')
    with pytest.raises(KeyError): server(c)
    path=tmp_path/'config.json';path.write_text(json.dumps(c))
    result=subprocess.run([sys.executable,str(ROOT/'analysis/evidence_calibration_mcp_stdio_v5.py'),
        '--configuration',str(path)],input=b'',capture_output=True,timeout=10)
    assert result.returncode!=0 and result.stdout==b''
    assert b'exact coordinator configuration' in result.stderr
    assert not Path(c['records']).exists()
    c['computation_cpu_limit']=saved
    s=server(c)
    assert s.descriptor['computation_cpu_limit']==saved
    assert json.loads((s.records/'session.intent.json').read_text())['computation_cpu_limit']==saved
    s.finish('SYNTHETIC_TERMINAL')
    terminal=json.loads((s.records/'session.result.json').read_text())
    assert terminal['schema']=='crane-local-mcp-terminal/v5-development'
    assert terminal['computation_cpu_ledger']['limit']==saved


def test_shared_total_charges_failed_work_denies_compute_and_preserves_read(tmp_path):
    c=config(tmp_path,cpu_budget=asdict(CpuBudget(300_000_000,20,250)),
        computation_cpu_limit=asdict(ComputationCpuLimit(310_000_000)))
    s=server(c);initialized(s)
    first=tool(s,COMPUTE,{'code':'print(1)'},id=10)['result']
    assert not first['isError']
    first_record=json.loads((s.records/'tool-00000003.result.json').read_text())
    first_cpu=first_record['cpu_ledger_settlement']['actual_cpu_nanoseconds']
    code="import subprocess,sys\ncs=[subprocess.Popen([sys.executable,'-c','while True: pass'],start_new_session=True) for _ in range(4)]\nprint('partial',flush=True)\nfor child in cs:child.wait()"
    failed=tool(s,COMPUTE,{'code':code},id=11)['result']
    assert failed['isError'] and failed['structuredContent']['result'] is None
    assert 'partial' not in json.dumps(failed) and 'ledger' not in json.dumps(failed)
    charged=json.loads((s.records/'tool-00000004.result.json').read_text())['cpu_ledger_settlement']
    assert charged['reservation']['effective_cpu_budget']['cumulative_nanoseconds']==310_000_000-first_cpu
    assert s.broker.cpu_ledger.spent==first_cpu+charged['actual_cpu_nanoseconds']>=310_000_000
    denied=tool(s,COMPUTE,{'code':'print(2)'},id=12)['result']
    assert denied['isError'] and denied['structuredContent']['result'] is None
    assert 'EXHAUSTED' in denied['structuredContent']['error']
    assert not (s.records/'tool-00000005.execution').exists()
    read=tool(s,READ,{'path':'visible.txt','offset':0,'length':None},id=13)['result']
    assert not read['isError'] and read['structuredContent']['result']['text']=='αβ visible'
    s.finish('SYNTHETIC_TERMINAL')
    assert json.loads((s.records/'session.result.json').read_text())['computation_cpu_ledger']==s.broker.cpu_ledger.snapshot()


def test_injected_unknown_accounting_withholds_success_and_closes_all_tools(tmp_path,monkeypatch):
    from copy import deepcopy
    import evidence_calibration_computation_cpu_ledger_v2 as ledger
    original=ledger.bounded_json
    def corrupt(path,*args):
        row,sha=original(path,*args)
        if path.name=='terminal.json':
            row=deepcopy(row);row['cpu_accounting']['final_cpu_nanoseconds']=None
        return row,sha
    monkeypatch.setattr(ledger,'bounded_json',corrupt)
    s=server(config(tmp_path));initialized(s)
    withheld=tool(s,COMPUTE,{'code':"print('withheld')"},id=10)['result']
    assert withheld['isError'] and withheld['structuredContent']['result'] is None
    assert 'withheld' not in json.dumps(withheld)
    inner=json.loads((s.records/'tool-00000003.execution/terminal.json').read_text())
    assert inner['status']=='RETURNED' and inner['result']['stdout']=='withheld\n'
    for index,(name,args) in enumerate([(READ,{'path':'visible.txt','offset':0,'length':None}),
        (COMPUTE,{'code':'print(1)'})],start=11):
        denied=tool(s,name,args,id=index)['result']
        assert denied['isError'] and denied['structuredContent']['result'] is None
        assert 'UNKNOWN' in denied['structuredContent']['error']
    assert not (s.records/'tool-00000005.execution').exists()
    s.finish('SYNTHETIC_TERMINAL')
    snapshot=json.loads((s.records/'session.result.json').read_text())['computation_cpu_ledger']
    assert snapshot['unknown_accounting'] and snapshot['remaining_nanoseconds'] is None


def test_settlement_storage_failure_stays_pending_and_cannot_replay_or_adopt(tmp_path,monkeypatch):
    import evidence_calibration_computation_cpu_ledger_v2 as ledger
    original=ledger.write_once
    def fail(path,value):
        if path.name.endswith('.result.json'): raise OSError('injected settlement retention failure')
        return original(path,value)
    monkeypatch.setattr(ledger,'write_once',fail)
    c=config(tmp_path);s=server(c);initialized(s)
    failed=tool(s,COMPUTE,{'code':'print(1)'},id=10)['result']
    assert failed['isError'] and failed['structuredContent']['result'] is None
    assert s.broker.cpu_ledger.snapshot()['pending_event']=='tool-00000003'
    with pytest.raises(ValueError,match='replay'): s.broker.cpu_ledger.settle('tool-00000003')
    assert tool(s,COMPUTE,{'code':'print(1)'},id=10)['error']['code']==-32600
    denied=tool(s,READ,{'path':'visible.txt','offset':0,'length':None},id=11)['result']
    assert denied['isError'] and denied['structuredContent']['result'] is None
    with pytest.raises(ValueError,match='fresh event namespace'): server(c)
    assert not list((s.records/'cpu-ledger').glob('*.result.json'))
    assert json.loads((s.records/'tool-00000003.execution/terminal.json').read_text())['status']=='RETURNED'
