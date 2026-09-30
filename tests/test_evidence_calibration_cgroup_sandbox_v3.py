import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'analysis'))
import observe_evidence_calibration_cgroup_sandbox as v1
import observe_evidence_calibration_cgroup_sandbox_v2 as v2
import observe_evidence_calibration_cgroup_sandbox_v3 as v3
from test_evidence_calibration_cgroup_sandbox import row
from evidence_calibration_local_tool_sandbox_v2 import command
from evidence_calibration_io import canonical_sha256
from stage_evidence_calibration_workspace import inventory


def test_repairs_have_only_the_two_disclosed_changes():
    original = (ROOT / 'analysis/observe_evidence_calibration_cgroup_sandbox.py').read_text()
    repaired = original.replace("'-p', 'CPUQuota=100%', '-p', 'MemoryOOMGroup=yes', '-p', 'OOMPolicy=kill',",
                                "'-p', 'CPUQuota=100%', '-p', 'OOMPolicy=kill',")
    assert (ROOT / 'analysis/observe_evidence_calibration_cgroup_sandbox_v2.py').read_text() == repaired
    repaired = repaired.replace("'environment_cleared': set(os.environ) <= {'PATH', 'LC_ALL'},",
                                "'environment_cleared': dict(os.environ) == {'PATH': '/usr/bin:/bin', 'LC_ALL': 'C.UTF-8', 'PWD': '/work'},")
    assert (ROOT / 'analysis/observe_evidence_calibration_cgroup_sandbox_v3.py').read_text() == repaired
    assert v1.LIMITS == v2.LIMITS == v3.LIMITS


def test_repaired_service_preserves_v2_namespace_and_staged_access(tmp_path):
    identity = {'inventory': inventory(tmp_path)}
    identity['workspace_sha256'] = canonical_sha256(identity)
    argv = v3.service_command(tmp_path, identity, 'task_limit', 'test-unit')
    assert 'MemoryOOMGroup=yes' not in argv
    assert 'OOMPolicy=kill' in argv and 'KillMode=control-group' in argv
    assert argv[argv.index('/usr/bin/bwrap'):] == command(tmp_path, identity, ['-c', v3.PROBES['task_limit']], v3.LIMITS)


@pytest.mark.parametrize('probe', list(v3.PROBES))
def test_fixed_results_remain_valid_under_repair(probe):
    v3.validate_result(probe, row(probe))


@pytest.mark.parametrize('probe', ['memory_pressure', 'service_wall'])
def test_resource_failure_cannot_be_generic_failure_or_success_output(probe):
    value = row(probe)
    value['unit_properties']['Result'] = 'exit-code'
    with pytest.raises(ValueError):
        v3.validate_result(probe, value)
    value = row(probe)
    value['stdout'] = 'partial output'
    with pytest.raises(ValueError):
        v3.validate_result(probe, value)
