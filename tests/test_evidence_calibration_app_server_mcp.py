from pathlib import Path
import subprocess
import sys
import tempfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'analysis'))
from observe_evidence_calibration_app_server_mcp import OfflineClient, command, observe


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
        with pytest.raises(ValueError, match='never adopt'):
            observe(method, Path(temporary) / 'observation')
