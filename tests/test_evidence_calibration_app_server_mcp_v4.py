from pathlib import Path
import subprocess
import sys
import tempfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'analysis'))
from observe_evidence_calibration_app_server_mcp_v4 import OfflineClient, command, observe


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
            assert records[1]['cpu_accounting']['final_cpu_nanoseconds'] >= 300_000_000
        with pytest.raises(ValueError, match='never adopt'):
            observe(method, Path(temporary) / 'observation')


def test_profile_selects_new_adapter_and_only_service_control_environment():
    import json
    from observe_evidence_calibration_app_server_mcp_v4 import SERVER
    argv=command(Path('/tmp/synthetic-config'),Path('/tmp/synthetic-job'),'B2')
    settings=dict(item.split('=',1) for item in argv if item.startswith('mcp_servers.'))
    assert json.loads(settings[f'mcp_servers.{SERVER}.env_vars'])==['XDG_RUNTIME_DIR','DBUS_SESSION_BUS_ADDRESS']
    assert json.loads(settings[f'mcp_servers.{SERVER}.args'])[0].endswith('evidence_calibration_mcp_stdio_v4.py')


def test_constructor_failure_retains_intent_error_and_sanitized_disposition(monkeypatch):
    import json
    import observe_evidence_calibration_app_server_mcp_v4 as module
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
    from observe_evidence_calibration_app_server_mcp_v4 import verify_execution_records
    from observe_evidence_calibration_tree_cpu_accounting_v3 import FIELDS
    config={'limits':{'synthetic':1},'tree_limits':{'synthetic':2},
            'scratch_limits':{'temporary_bytes':1048576,'shared_memory_bytes':1048576},
            'cpu_budget':{'cumulative_nanoseconds':300_000_000,'poll_milliseconds':20,'query_timeout_milliseconds':250}}
    paths=[]
    for ordinal,cpu in enumerate([20_000_000,350_000_000]):
        directory=tmp_path/f'tool-{ordinal:08d}.execution';directory.mkdir()
        status=b'synthetic opaque status bytes';(directory/'namespace-status.bin').write_bytes(status)
        limits={'local_limits':config['limits'],'tree_limits':config['tree_limits'],'scratch_limits':config['scratch_limits']}
        intent={'unit':f'synthetic-{ordinal}',**limits,'cpu_budget':config['cpu_budget']}
        terminal={'schema':'crane-service-computation-terminal/v10-development','unit':intent['unit'],
                  'namespace_status_sha256':hashlib.sha256(status).hexdigest(),
                  'cleanup':{'final_state':{'return_code':0,'stdout':'not-found\n'}},
                  'execution_audit':{**limits,'reason':None if ordinal==0 else 'CUMULATIVE_CPU_LIMIT'},
                  'status':'RETURNED' if ordinal==0 else 'TECHNICAL_FAILURE',
                  'result':{'return_code':0,'stdout':'%n ${HOME} $$ αβ\n','stderr':''} if ordinal==0 else None,
                  'cpu_accounting':{'budget':config['cpu_budget'],'final_cpu_nanoseconds':cpu,
                       'last_observed_cpu_nanoseconds':cpu,'sample_count':1,
                       'observed_overshoot_nanoseconds':max(0,cpu-300_000_000),
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
            a['observed_overshoot_nanoseconds']=max(0,value-300_000_000)
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
