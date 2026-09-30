import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'analysis'))
from observe_evidence_calibration_cgroup_limits import validate_observation, write_once


def valid():
    return {'kernel_settings': {'memory.max': '67108864', 'memory.swap.max': '0',
                               'pids.max': '8', 'cpu.max': '100000 100000'},
            'children_started': 7, 'task_creation_blocked': True, 'children_reaped': True}


def test_expected_kernel_values_and_task_limit():
    validate_observation(valid())


@pytest.mark.parametrize('field,value', [('memory.max', 'max'), ('memory.swap.max', 'max'),
                                        ('pids.max', 'max'), ('cpu.max', 'max 100000'),
                                        ('cpu.max', '200000 100000')])
def test_unbounded_or_different_kernel_values_rejected(field, value):
    row = valid()
    row['kernel_settings'][field] = value
    with pytest.raises(ValueError):
        validate_observation(row)


@pytest.mark.parametrize('field,value', [('children_started', 8), ('children_started', True),
                                        ('task_creation_blocked', False), ('children_reaped', False)])
def test_missing_enforcement_or_cleanup_rejected(field, value):
    row = valid()
    row[field] = value
    with pytest.raises(ValueError):
        validate_observation(row)


def test_record_cannot_overwrite_intent(tmp_path):
    path = tmp_path / 'intent.json'
    write_once(path, {'first': True})
    with pytest.raises(FileExistsError):
        write_once(path, {'first': False})
    assert 'true' in path.read_text()
