import copy
import json
from pathlib import Path

from analysis.hexar_external.acquisition.operational_validity_candidate import evaluate

BASE = Path(__file__).resolve().parents[2] / 'manifests/hexar_external/acquisition'


def fixtures():
    plan = json.loads((BASE / 'development_episode_plan_v15.json').read_text())
    run = json.loads((BASE / 'development_episode_plan_v15_qualification_run.json').read_text())
    interface = json.loads((BASE / 'controller_boundary_qualification_v15.json').read_text())
    native = json.loads((BASE / 'native_sampling_clock_qualification_v15_v2.json').read_text())
    return [(receipt, json.loads((BASE / planned['episode_id'] / 'episode.json').read_text()),
             planned, review, clocks) for receipt, planned, review, clocks in
            zip(run['episodes'], plan['records'], interface['episodes'], native['episodes'])]


def test_all_six_actual_development_inputs_pass_without_authorizing_confirmation():
    for args in fixtures():
        result = evaluate(*args)
        assert result['technical_valid']
        assert result['full_admission_authorized'] is False


def test_short_valid_action_does_not_require_motion_samples_or_navigation_success():
    for n in (0, 1):
        receipt, episode, planned, interface, native = copy.deepcopy(fixtures()[0])
        native['clock_envelope_diagnostic']['task_window_odometry_n'] = n
        native['checks']['at_least_two_task_window_odometry_samples'] = False
        episode.update(terminal_action_status=6, timeout=True)
        assert evaluate(receipt, episode, planned, interface, native)['technical_valid']


def test_false_native_checks_or_mismatched_action_window_fail_closed():
    for change in ('window', 'schema', 'sampling', 'outside', 'other_episode'):
        receipt, episode, planned, interface, native = copy.deepcopy(fixtures()[0])
        if change == 'window':
            native['clock_envelope_diagnostic']['observed_action_stamp_range_ns'][1] += 1
        elif change == 'schema':
            native['checks']['metadata_types_match_actual_raw_messages'] = False
        elif change == 'sampling':
            native['checks']['applied_sampling_matches_seed_and_captured_map'] = False
        elif change == 'outside':
            native['clock_envelope_diagnostic']['task_window_odometry_outside_envelope_n'] = 1
        else:
            native['episode_id'] = 'other'
        assert not evaluate(receipt, episode, planned, interface, native)['technical_valid']
