import copy
import json
from pathlib import Path

from analysis.hexar_external.acquisition.sampling_clock_qualification import check_timestamps
from analysis.hexar_external.acquisition.sampling_clock_qualification_v2 import window_checks


def test_clock_values_must_be_nonnegative_integer_and_monotone():
    assert check_timestamps([0, 1, 1, 2])
    assert not check_timestamps([0, 1, 1, 2], strict=True)
    for values in ([], [True], [1., 2.], [-1, 0], [0, 2, 1]):
        assert not check_timestamps(values)


def test_task_window_qualification_rejects_missing_or_outside_required_measurements():
    row = dict(action_boundaries_within_clock_envelope=True, task_window_odometry_n=3,
               task_window_odometry_outside_envelope_n=0)
    assert all(window_checks(row).values())
    for key, value in (('action_boundaries_within_clock_envelope', False),
                       ('task_window_odometry_n', 1),
                       ('task_window_odometry_outside_envelope_n', 1)):
        changed = copy.deepcopy(row); changed[key] = value
        assert not all(window_checks(changed).values())


def test_failed_whole_stream_audit_is_retained_and_no_clock_tolerance_added():
    base = Path(__file__).resolve().parents[2] / 'manifests/hexar_external/acquisition'
    initial = json.loads((base / 'native_sampling_clock_qualification_v15.json').read_text())
    scoped = json.loads((base / 'native_sampling_clock_qualification_v15_v2.json').read_text())
    assert initial['status'] == 'FAILED_RETAINED'
    assert scoped['prior_failed_report_reproduced'] is True
    assert scoped['status'] == 'NATIVE_TASK_WINDOW_SCOPE_PASSED_NOT_FINAL_ADMISSION'
    obstacle = next(r for r in scoped['episodes'] if r['episode_id'].endswith('obstacle-0015'))
    assert obstacle['full_stream_clock_envelope_passed'] is False
    assert len(obstacle['clock_envelope_diagnostic']['outside_full_envelope']) == 1
    assert obstacle['clock_envelope_diagnostic']['task_window_odometry_outside_envelope_n'] == 0
    assert all(obstacle['checks'].values())
    assert scoped['full_acquisition_qualified'] is False
    assert scoped['confirmatory_N'] == 0
