from pathlib import Path
import subprocess
import sys
import tempfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'analysis'))
from observe_evidence_calibration_app_server_mcp_v5 import OfflineClient, command, observe


def test_outer_namespace_device_regression_without_client_or_broker():
    code = "with open('/dev/null','rb') as stream: assert stream.read()==b''"
    failed = subprocess.run(['/usr/bin/bwrap', '--unshare-net', '--bind', '/', '/', '--',
                             '/usr/bin/python3', '-c', code], capture_output=True, timeout=5)
    assert failed.returncode != 0 and b'PermissionError' in failed.stderr
    fixed = subprocess.run(['/usr/bin/bwrap', '--unshare-net', '--bind', '/', '/', '--dev', '/dev', '--',
                            '/usr/bin/python3', '-c', code], capture_output=True, timeout=5)
    assert fixed.returncode == 0 and fixed.stderr == b''


def test_outer_namespace_has_no_access_to_parent_loopback():
    import socket
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0)); listener.listen()
        port = listener.getsockname()[1]
        code = f"import socket\ntry:\n socket.create_connection(('127.0.0.1',{port}),timeout=1)\nexcept OSError:\n print('parent network denied')\nelse:\n raise AssertionError('parent network reached')"
        result = subprocess.run(['/usr/bin/bwrap', '--unshare-net', '--bind', '/', '/', '--dev', '/dev', '--',
                                 '/usr/bin/python3', '-c', code], capture_output=True, timeout=5)
        assert result.returncode == 0 and result.stdout == b'parent network denied\n'


@pytest.mark.parametrize('method', ['turn/start', 'turn/steer', 'thread/resume', 'command/exec'])
def test_observer_rejects_model_and_execution_methods_before_any_transport(method):
    client = OfflineClient.__new__(OfflineClient)
    with pytest.raises(ValueError, match='no model turn'):
        client.request(method, {})


def test_profile_uses_installed_feature_spelling_and_private_devices():
    argv = command(Path('/tmp/synthetic-config'), Path('/tmp/synthetic-job'), 'B2')
    assert '--strict-config' in argv and argv[argv.index('--dev')+1] == '/dev'
    assert 'features.remote_plugin=false' in argv
    assert not any('features.remote_plugins=' in item for item in argv)
    assert not any('turn/start' in item for item in argv)


@pytest.mark.parametrize('method', ['B0', 'B1', 'B2', 'B3', 'B4'])
def test_actual_installed_client_synthetic_tool_discovery_and_routing(method):
    with tempfile.TemporaryDirectory(prefix='crane-client-test-') as temporary:
        result = observe(method, Path(temporary) / 'observation')
        assert result['status'] == 'PASS' and result['stderr_bytes'] == 0
        assert result['runtime_status'] == 'connected'
        assert result['model_call_attempted'] is False
        assert 'turn/start' not in result['request_methods']
        assert result['provider_request_tools_verified'] is False
        expected = [] if method in {'B0', 'B1'} else ['compute_visible_python', 'read_staged_file']
        assert sorted(result['tools']) == expected
        assert result['synthetic_read_and_computation_passed'] is (True if expected else None)
        assert result['bounded_tool_failure_passed'] is (True if expected else None)
        if expected:
            records = result['execution_records']
            assert len(records) == 2
            assert all(row['unit_absent'] and row['limits_match_configuration'] for row in records)
            assert records[0]['payload_exit_verified'] is True
            assert records[1]['status'] == 'TECHNICAL_FAILURE'
            for row in records:
                assert row['cpu_accounting']['final_cpu_nanoseconds'] > 0
                assert row['cpu_accounting']['hard_cpu_cap_verified'] is False
                assert row['cpu_sample_sha256']
            assert records[1]['cpu_accounting']['final_cpu_nanoseconds'] >= records[1]['cpu_accounting']['budget']['cumulative_nanoseconds']
            assert result['exhausted_compute_denied_read_preserved'] is True
            assert result['computation_cpu_ledger']['snapshot_after_fixed_calls']['spent_nanoseconds'] >= 310_000_000
        with pytest.raises(ValueError, match='never adopt'):
            observe(method, Path(temporary) / 'observation')


def test_profile_selects_new_adapter_and_only_service_control_environment():
    import json
    from observe_evidence_calibration_app_server_mcp_v5 import SERVER
    argv=command(Path('/tmp/synthetic-config'),Path('/tmp/synthetic-job'),'B2')
    settings=dict(item.split('=',1) for item in argv if item.startswith('mcp_servers.'))
    assert json.loads(settings[f'mcp_servers.{SERVER}.env_vars'])==['XDG_RUNTIME_DIR','DBUS_SESSION_BUS_ADDRESS']
    assert json.loads(settings[f'mcp_servers.{SERVER}.args'])[0].endswith('evidence_calibration_mcp_stdio_v5.py')


def test_constructor_failure_retains_intent_error_and_sanitized_disposition(monkeypatch):
    import json
    import observe_evidence_calibration_app_server_mcp_v5 as module
    def fail(argv):
        raise OSError('synthetic client launch failure')
    monkeypatch.setattr(module,'OfflineClient',fail)
    with tempfile.TemporaryDirectory(prefix='crane-launch-test-') as temporary:
        directory=Path(temporary)/'observation'
        with pytest.raises(OSError,match='synthetic'):
            module.observe('B2',directory)
        assert (directory/'observer.intent.json').is_file()
        assert json.loads((directory/'observer.error.json').read_text())['error_type']=='OSError'
        result=json.loads((directory/'sanitized-result.json').read_text())
        assert result['status']=='FAILED_NO_RETRY' and result['model_call_attempted'] is False
        assert result['process_exit_code'] is None




@pytest.mark.parametrize('defect', [
    'missing_terminal','status_hash','cleanup','scratch_intent','scratch_terminal','lifecycle',
    'success_text','cutoff_result','cpu_intent','cpu_budget','cpu_missing','cpu_bool',
    'cpu_success_threshold','cpu_cutoff_threshold','cpu_overshoot','cpu_sample_count',
    'cpu_sample_identity','cpu_raw_missing','cpu_raw_mismatch','cpu_nonquiescent',
    'cpu_incomplete','cpu_hardcap_claim','cpu_turn_claim',
])
def test_nested_cpu_record_verification_rejects_invalid_accounting(tmp_path, defect):
    import hashlib,json
    from observe_evidence_calibration_app_server_mcp_v5 import verify_execution_records
    from observe_evidence_calibration_tree_cpu_accounting_v3 import FIELDS
    config={'limits':{'synthetic':1},'tree_limits':{'synthetic':2},
            'scratch_limits':{'temporary_bytes':1048576,'shared_memory_bytes':1048576},
            'cpu_budget':{'cumulative_nanoseconds':300_000_000,'poll_milliseconds':20,'query_timeout_milliseconds':250},
            'computation_cpu_limit':{'total_nanoseconds':310_000_000}}
    paths=[]
    for ordinal,cpu in enumerate([20_000_000,350_000_000]):
        directory=tmp_path/f'tool-{ordinal:08d}.execution';directory.mkdir()
        status=b'synthetic opaque status bytes';(directory/'namespace-status.bin').write_bytes(status)
        limits={'local_limits':config['limits'],'tree_limits':config['tree_limits'],'scratch_limits':config['scratch_limits']}
        budget={**config['cpu_budget'],'cumulative_nanoseconds':300_000_000 if ordinal==0 else 290_000_000}
        intent={'unit':f'synthetic-{ordinal}',**limits,'cpu_budget':budget}
        terminal={'schema':'crane-service-computation-terminal/v10-development','unit':intent['unit'],
                  'namespace_status_sha256':hashlib.sha256(status).hexdigest(),
                  'cleanup':{'final_state':{'return_code':0,'stdout':'not-found\n'}},
                  'execution_audit':{**limits,'reason':None if ordinal==0 else 'CUMULATIVE_CPU_LIMIT'},
                  'status':'RETURNED' if ordinal==0 else 'TECHNICAL_FAILURE',
                  'result':{'return_code':0,'stdout':'%n ${HOME} $$ αβ\n','stderr':''} if ordinal==0 else None,
                  'cpu_accounting':{'budget':budget,'final_cpu_nanoseconds':cpu,
                       'last_observed_cpu_nanoseconds':cpu,'sample_count':1,
                       'observed_overshoot_nanoseconds':max(0,cpu-budget['cumulative_nanoseconds']),
                       'hard_cpu_cap_verified':False,'whole_turn_cpu_accounting_verified':False}}
        if ordinal==0:terminal['namespace_lifecycle']={'disposition':'PAYLOAD_EXIT_VERIFIED','payload_exit_verified':True}
        properties={'LoadState':'loaded','ActiveState':'active' if ordinal==0 else 'failed',
                    'SubState':'exited' if ordinal==0 else 'failed','Result':'success' if ordinal==0 else 'signal',
                    'ExecMainCode':'1' if ordinal==0 else '2','ExecMainStatus':'0' if ordinal==0 else '9',
                    'ControlGroup':'','TasksCurrent':'[not set]','CPUUsageNSec':str(cpu)}
        sample={'unit':intent['unit'],'return_code':0,'stdout':'\n'.join(f'{key}={properties[key]}' for key in FIELDS.split(','))+'\n'}
        (directory/'cpu-sample-00000000.json').write_text(json.dumps(sample))
        (directory/'intent.json').write_text(json.dumps(intent))
        path=directory/'terminal.json';path.write_text(json.dumps(terminal));paths.append(path)
    assert len(verify_execution_records(tmp_path,config))==2
    if defect=='missing_terminal':paths[1].unlink()
    else:
        path=paths[1] if defect in {'cutoff_result','cpu_cutoff_threshold'} else paths[0]
        terminal=json.loads(path.read_text());a=terminal['cpu_accounting']
        sample_path=path.with_name('cpu-sample-00000000.json');sample=json.loads(sample_path.read_text())
        if defect=='status_hash':terminal['namespace_status_sha256']='0'*64
        elif defect=='cleanup':terminal['cleanup']['final_state']['stdout']='loaded\n'
        elif defect in {'scratch_intent','cpu_intent'}:
            intent_path=path.with_name('intent.json');intent=json.loads(intent_path.read_text())
            if defect=='scratch_intent':intent['scratch_limits']['temporary_bytes']=2**30
            else:intent['cpu_budget']['cumulative_nanoseconds']=2**30
            intent_path.write_text(json.dumps(intent))
        elif defect=='scratch_terminal':terminal['execution_audit']['scratch_limits']['temporary_bytes']=2**30
        elif defect=='lifecycle':terminal['namespace_lifecycle']['payload_exit_verified']=False
        elif defect=='success_text':terminal['result']['stdout']='altered'
        elif defect=='cutoff_result':terminal['result']={'stdout':'partial'}
        elif defect=='cpu_budget':a['budget']['cumulative_nanoseconds']=2**30
        elif defect=='cpu_missing':a['final_cpu_nanoseconds']=None
        elif defect=='cpu_bool':a['final_cpu_nanoseconds']=True
        elif defect in {'cpu_success_threshold','cpu_cutoff_threshold'}:
            value=350_000_000 if defect=='cpu_success_threshold' else 20_000_000
            sample['stdout']=sample['stdout'].replace(f"CPUUsageNSec={a['final_cpu_nanoseconds']}",f'CPUUsageNSec={value}')
            a['final_cpu_nanoseconds']=a['last_observed_cpu_nanoseconds']=value
            a['observed_overshoot_nanoseconds']=max(0,value-a['budget']['cumulative_nanoseconds'])
        elif defect=='cpu_overshoot':a['observed_overshoot_nanoseconds']=999
        elif defect=='cpu_sample_count':a['sample_count']=2
        elif defect=='cpu_sample_identity':sample['unit']='other-unit'
        elif defect=='cpu_raw_missing':sample['stdout']=sample['stdout'].replace('CPUUsageNSec=20000000\n','')
        elif defect=='cpu_raw_mismatch':sample['stdout']=sample['stdout'].replace('CPUUsageNSec=20000000','CPUUsageNSec=123')
        elif defect=='cpu_nonquiescent':sample['stdout']=sample['stdout'].replace('TasksCurrent=[not set]','TasksCurrent=2').replace('ControlGroup=\n','ControlGroup=/running\n')
        elif defect=='cpu_incomplete':sample['stdout']=sample['stdout'].replace('SubState=exited','SubState=running')
        elif defect=='cpu_hardcap_claim':a['hard_cpu_cap_verified']=True
        elif defect=='cpu_turn_claim':a['whole_turn_cpu_accounting_verified']=True
        sample_path.write_text(json.dumps(sample));path.write_text(json.dumps(terminal))
    with pytest.raises(RuntimeError):verify_execution_records(tmp_path,config)


def synthetic_ledger_records(tmp_path):
    """No client/service: synthetic retained records exercise observer validation."""
    import hashlib,json
    from dataclasses import asdict
    from evidence_calibration_computation_cpu_ledger_v2 import ComputationCpuLedger,ComputationCpuLimit
    from evidence_calibration_local_tool_sandbox_v10 import CpuBudget
    from evidence_calibration_io import canonical_sha256
    from test_evidence_calibration_computation_cpu_ledger import evidence,SHA
    from observe_evidence_calibration_app_server_mcp_v5 import READ,COMPUTE
    config={'identity':{'workspace_sha256':SHA,'method_id':'B2'},
        'cpu_budget':asdict(CpuBudget(300_000_000,20,250)),
        'computation_cpu_limit':asdict(ComputationCpuLimit(310_000_000))}
    l=ComputationCpuLedger(tmp_path/'cpu-ledger',SHA,limit=ComputationCpuLimit(**config['computation_cpu_limit']),per_call=CpuBudget(**config['cpu_budget']))
    session={'schema':'crane-local-mcp-session/v5-development','workspace_sha256':SHA,'method_id':'B2',
        'cpu_budget':config['cpu_budget'],'computation_cpu_limit':config['computation_cpu_limit']}
    (tmp_path/'session.intent.json').write_text(json.dumps(session))
    def request(event,name):return {'event_id':event,'name':name,'workspace_sha256':SHA,
        'cpu_budget':config['cpu_budget'],'cpu_ledger_before':l.snapshot()}
    first_read={'request':request('tool-00000003',READ),'status':'RETURNED','result':{'text':'synthetic visible αβ'}}
    (tmp_path/'tool-00000003.result.json').write_text(json.dumps(first_read))
    records=[]
    for index,cpu,status in [(4,20_000_000,'RETURNED'),(5,350_000_000,'TECHNICAL_FAILURE')]:
        event=f'tool-{index:08d}';r=request(event,COMPUTE)
        (tmp_path/(event+'.intent.json')).write_text(json.dumps({'request':r,'request_sha256':canonical_sha256(r)}))
        reservation=l.reserve(event,tmp_path/(event+'.execution'),canonical_sha256(r))
        evidence(tmp_path/(event+'.execution'),reservation,cpu,status)
        settled=l.settle(event)
        (tmp_path/(event+'.result.json')).write_text(json.dumps({'request':r,'cpu_ledger_settlement':settled}))
        terminal=tmp_path/(event+'.execution')/'terminal.json'
        records.append({'cpu_accounting':{'final_cpu_nanoseconds':cpu},'terminal_sha256':hashlib.sha256(terminal.read_bytes()).hexdigest()})
    denied={'request':request('tool-00000006',COMPUTE),'status':'TECHNICAL_FAILURE','result':None,
        'error':'COMPUTATION_CPU_BUDGET_EXHAUSTED_OR_BELOW_EXECUTOR_MINIMUM','cpu_ledger_settlement':None}
    read={'request':request('tool-00000007',READ),'status':'RETURNED','result':{'text':'synthetic visible αβ'}}
    for index,row in [(6,denied),(7,read)]:
        (tmp_path/f'tool-{index:08d}.result.json').write_text(json.dumps(row))
    return config,records


@pytest.mark.parametrize('defect',[
    'session_total','ledger_total','ledger_source','ledger_adoption','missing_settlement',
    'reservation_spent','reservation_remaining','reservation_threshold','reservation_request',
    'settlement_actual','settlement_spent','settlement_overshoot','settlement_evidence',
    'broker_settlement','broker_request','denied_result','denied_snapshot','denied_launch',
    'read_text','read_snapshot','raw_counter_regression','sample_sequence',
])
def test_ledger_verifier_rejects_corrupt_retained_transactions_without_client(tmp_path,defect):
    import json
    from observe_evidence_calibration_app_server_mcp_v5 import verify_ledger_records
    config,records=synthetic_ledger_records(tmp_path)
    assert verify_ledger_records(tmp_path,config,records)['snapshot_after_fixed_calls']['spent_nanoseconds']==370_000_000
    def mutate(path,change):
        row=json.loads(path.read_text());change(row);path.write_text(json.dumps(row))
    ledger=tmp_path/'cpu-ledger'
    if defect=='session_total':mutate(tmp_path/'session.intent.json',lambda r:r['computation_cpu_limit'].update(total_nanoseconds=999))
    elif defect=='ledger_total':mutate(ledger/'ledger.intent.json',lambda r:r['limit'].update(total_nanoseconds=999))
    elif defect=='ledger_source':mutate(ledger/'ledger.intent.json',lambda r:r.update(ledger_sha256='f'*64))
    elif defect=='ledger_adoption':mutate(ledger/'ledger.intent.json',lambda r:r.update(existing_ledgers_may_be_adopted=True))
    elif defect=='missing_settlement':(ledger/'reservation-00000002.result.json').unlink()
    elif defect.startswith('reservation_'):
        def change(r):
            if defect=='reservation_spent':r['spent_before_nanoseconds']=0
            elif defect=='reservation_remaining':r['remaining_before_nanoseconds']=310_000_000
            elif defect=='reservation_threshold':r['effective_cpu_budget']['cumulative_nanoseconds']=300_000_000
            elif defect=='reservation_request':r['tool_request_sha256']='f'*64
        mutate(ledger/'reservation-00000002.intent.json',change)
    elif defect.startswith('settlement_'):
        def change(r):
            if defect=='settlement_actual':r['actual_cpu_nanoseconds']=300_000_000
            elif defect=='settlement_spent':r['spent_after_nanoseconds']=310_000_000
            elif defect=='settlement_overshoot':r['unclamped_overshoot_nanoseconds']=0
            elif defect=='settlement_evidence':r['evidence_hashes']['execution_terminal_sha256']='f'*64
        mutate(ledger/'reservation-00000002.result.json',change)
    elif defect=='broker_settlement':mutate(tmp_path/'tool-00000005.result.json',lambda r:r['cpu_ledger_settlement'].update(actual_cpu_nanoseconds=300_000_000))
    elif defect=='broker_request':mutate(tmp_path/'tool-00000005.result.json',lambda r:r['request'].update(name='other'))
    elif defect=='denied_result':mutate(tmp_path/'tool-00000006.result.json',lambda r:r.update(result={'stdout':'fabricated'}))
    elif defect=='denied_snapshot':mutate(tmp_path/'tool-00000006.result.json',lambda r:r['request']['cpu_ledger_before'].update(spent_nanoseconds=310_000_000))
    elif defect=='denied_launch':(tmp_path/'tool-00000006.execution').mkdir()
    elif defect=='read_text':mutate(tmp_path/'tool-00000007.result.json',lambda r:r['result'].update(text='truncated'))
    elif defect=='read_snapshot':mutate(tmp_path/'tool-00000007.result.json',lambda r:r['request']['cpu_ledger_before'].update(remaining_nanoseconds=None))
    elif defect=='raw_counter_regression':
        path=tmp_path/'tool-00000004.execution'
        mutate(path/'terminal.json',lambda r:r['cpu_accounting'].update(sample_count=2))
        sample=json.loads((path/'cpu-sample-00000000.json').read_text())
        (path/'cpu-sample-00000001.json').write_text(json.dumps(sample))
        sample['stdout']=sample['stdout'].replace('CPUUsageNSec=20000000','CPUUsageNSec=30000000').replace('SubState=exited','SubState=running')
        (path/'cpu-sample-00000000.json').write_text(json.dumps(sample))
    elif defect=='sample_sequence':
        path=tmp_path/'tool-00000004.execution'
        (path/'cpu-sample-00000000.json').rename(path/'cpu-sample-00000002.json')
    with pytest.raises(RuntimeError,match='ledger verification failed'):
        verify_ledger_records(tmp_path,config,records)
