from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'analysis'))
from observe_evidence_calibration_tree_cpu_accounting_v3 import FIELDS, parse_properties, validate_observation
from audit_evidence_calibration_tree_cpu_accounting import audit


@pytest.fixture
def observation():
    row = {'cgroup': '/synthetic.service',
           'before': {'usage_usec': 10000, 'user_usec': 7000, 'system_usec': 3000},
           'after': {'usage_usec': 600000, 'user_usec': 500000, 'system_usec': 100000},
           'children': [{'cpu_seconds': .151} for _ in range(3)],
           'parent_work_cpu_seconds': .101, 'children_rusage_cpu_seconds': .49,
           'children_reaped': True, 'per_process_rlimit_cpu_seconds': 1,
           'cpu_max': '100000 100000'}
    sample = {'LoadState': 'loaded', 'ActiveState': 'active', 'SubState': 'exited',
              'Result': 'success', 'ExecMainCode': '1', 'ExecMainStatus': '0',
              'CPUUsageNSec': 610000000, 'ControlGroup': '', 'TasksCurrent': '[not set]'}
    running = {**sample, 'SubState': 'running', 'ControlGroup': row['cgroup'],
               'TasksCurrent': '4', 'CPUUsageNSec': 150000000}
    return row, [running, *[deepcopy(sample) for _ in range(3)]]


def test_exact_retired_cgroup_accounting_is_accepted(observation):
    validate_observation(*observation)


@pytest.mark.parametrize('defect', ['lost_children', 'bad_kernel_type', 'child_limit', 'parent_limit',
                                  'unreaped', 'rate', 'missing_samples', 'counter_regression',
                                  'unstable_exit', 'lost_final_cpu', 'exit_failure', 'wrong_identity',
                                  'live_cgroup', 'fabricated_zero_tasks'])
def test_accounting_validation_rejects_missing_or_inconsistent_evidence(observation, defect):
    row, samples = observation
    if defect == 'lost_children': row['after']['usage_usec'] = 100000
    elif defect == 'bad_kernel_type': row['before']['usage_usec'] = True
    elif defect == 'child_limit': row['children'][0]['cpu_seconds'] = 1.5
    elif defect == 'parent_limit': row['parent_work_cpu_seconds'] = 2
    elif defect == 'unreaped': row['children_reaped'] = False
    elif defect == 'rate': row['cpu_max'] = 'max 100000'
    elif defect == 'missing_samples': samples.pop()
    elif defect == 'counter_regression': samples[0]['CPUUsageNSec'] = 700000000
    elif defect == 'unstable_exit': samples[-1]['CPUUsageNSec'] += 1
    elif defect == 'lost_final_cpu':
        for sample in samples[-3:]: sample['CPUUsageNSec'] = 590000000
    elif defect == 'exit_failure': samples[-1]['ExecMainStatus'] = '1'
    elif defect == 'wrong_identity': samples[0]['ControlGroup'] = '/different.service'
    elif defect == 'live_cgroup': samples[-1]['ControlGroup'] = row['cgroup']
    elif defect == 'fabricated_zero_tasks': samples[-1]['TasksCurrent'] = '0'
    with pytest.raises(ValueError):
        validate_observation(row, samples)


def test_service_property_parser_requires_counter_and_exact_fields(observation):
    _, samples = observation
    sample = samples[-1]
    raw = '\n'.join(f'{key}={sample[key]}' for key in FIELDS.split(','))
    assert parse_properties(raw) == sample
    for invalid in [raw + '\nLoadState=loaded', raw.replace('CPUUsageNSec=610000000', 'CPUUsageNSec=[not set]'),
                    raw.replace('CPUUsageNSec=610000000', 'CPUUsageNSec=18446744073709551615'),
                    raw.replace('CPUUsageNSec=610000000', 'CPUUsageNSec=true'),
                    raw.replace('CPUUsageNSec=610000000', 'CPUUsageNSec=６１０００００００'),
                    raw + '\nCPUAccounting=yes', 'not a property']:
        with pytest.raises(ValueError): parse_properties(invalid)


def test_revalidation_keeps_original_failed_bytes_and_never_launches(monkeypatch, tmp_path, observation):
    import subprocess
    def forbidden(*args, **kwargs):
        raise AssertionError('revalidation may not launch any process')
    monkeypatch.setattr(subprocess, 'run', forbidden)
    row, samples = observation
    terminal = {'schema': 'crane-tree-cpu-accounting-terminal/v2-development', 'status': 'TECHNICAL_FAILURE',
                'error': 'retained accounting lacks successful empty process tree',
                'cleanup': {'final_state': {'return_code': 0, 'stdout': 'not-found\n'}},
                'observation': row, 'samples': samples}
    source = tmp_path / 'terminal.json'
    source.write_text(json.dumps(terminal))
    original = source.read_bytes()
    target = tmp_path / 'correction.json'
    result = audit(source, target)
    assert source.read_bytes() == original
    assert result['terminal_sha256'] == hashlib.sha256(original).hexdigest()
    assert result['original_transaction_status'] == 'TECHNICAL_FAILURE'
    assert result['post_exit_cgroup_retained'] is False
    assert result['tasks_current_measured_as_zero'] is False
    assert result['cumulative_budget_enforced'] is False
    assert result['transaction_relaunched'] is False
    with pytest.raises(FileExistsError): audit(source, target)
    terminal['status'] = 'PASS'
    source.write_text(json.dumps(terminal))
    with pytest.raises(ValueError, match='unexpected retained'):
        audit(source, tmp_path / 'unauthorized.json')


def test_repaired_versions_preserve_only_declared_schema_and_expectation_changes():
    first = (ROOT / 'analysis/observe_evidence_calibration_tree_cpu_accounting.py').read_text()
    second = (ROOT / 'analysis/observe_evidence_calibration_tree_cpu_accounting_v2.py').read_text()
    expected = first.replace('CPUAccounting,CPUUsageNSec','CPUUsageNSec').replace("                or sample['CPUAccounting'] != 'yes'\n",'').replace("'-p', 'RemainAfterExit=yes', '-p', 'CPUAccounting=yes',","'-p', 'RemainAfterExit=yes',").replace('accounting-intent/v1-development','accounting-intent/v2-development').replace('accounting-terminal/v1-development','accounting-terminal/v2-development')
    assert second == expected
    third = (ROOT / 'analysis/observe_evidence_calibration_tree_cpu_accounting_v3.py').read_text()
    expected = second.replace('accounting-intent/v2-development','accounting-intent/v3-development').replace('accounting-terminal/v2-development','accounting-terminal/v3-development')
    expected = expected.replace("                or sample['ControlGroup'] != row['cgroup']\n                or sample['TasksCurrent'] != '0'):","                or sample['ControlGroup'] != ''\n                or sample['TasksCurrent'] != '[not set]'):")
    expected = expected.replace("            raise ValueError('retained accounting lacks successful empty process tree')", "            raise ValueError('retained accounting lacks successful exit with retired cgroup')\n    if not any(sample['SubState'] == 'running' and sample['ControlGroup'] == row['cgroup']\n               for sample in snapshots[:-3]):\n        raise ValueError('running service identity does not match kernel probe cgroup')")
    assert third == expected
