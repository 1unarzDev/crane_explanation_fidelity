import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'analysis'))
from observe_evidence_calibration_cgroup_sandbox import validate_result, service_command, LIMITS
from evidence_calibration_local_tool_sandbox_v2 import command
from evidence_calibration_io import canonical_sha256
from stage_evidence_calibration_workspace import inventory


def row(probe):
    result = {'cleanup': {'load_state': 'not-found'}, 'return_code': 1, 'stdout': '',
              'unit_properties': {'Result': 'oom-kill' if probe == 'memory_pressure' else 'timeout'}}
    if probe == 'isolation':
        result.update(return_code=0, stdout='{"visible_read":true,"home_absent":true,"sysfs_absent":true,"environment_cleared":true,"arithmetic":true,"visible_write_denied":true}')
    elif probe == 'task_limit':
        result.update(return_code=0, stdout='{"children_started":12,"task_creation_blocked":true,"children_reaped":true}')
    return result


@pytest.mark.parametrize('probe', ['isolation', 'task_limit', 'memory_pressure', 'service_wall'])
def test_registered_results(probe):
    validate_result(probe, row(probe))


@pytest.mark.parametrize('probe', ['memory_pressure', 'service_wall'])
def test_generic_nonzero_is_not_proof_of_resource_enforcement(probe):
    value = row(probe)
    value['unit_properties']['Result'] = 'exit-code'
    with pytest.raises(ValueError):
        validate_result(probe, value)


def test_uncollected_service_is_not_success():
    value = row('isolation')
    value['cleanup']['load_state'] = 'loaded'
    with pytest.raises(ValueError, match='cleanup'):
        validate_result('isolation', value)


def test_outer_service_preserves_entire_v2_namespace_command(tmp_path):
    identity = {'inventory': inventory(tmp_path)}
    identity['workspace_sha256'] = canonical_sha256(identity)
    argv = service_command(tmp_path, identity, 'task_limit', 'test-unit')
    start = argv.index('/usr/bin/bwrap')
    from observe_evidence_calibration_cgroup_sandbox import PROBES
    assert argv[start:] == command(tmp_path, identity, ['-c', PROBES['task_limit']], LIMITS)
    assert 'KillMode=control-group' in argv and 'MemoryOOMGroup=yes' in argv
    with pytest.raises(ValueError, match='fixed'):
        service_command(tmp_path, identity, 'arbitrary-code', 'test-unit')
