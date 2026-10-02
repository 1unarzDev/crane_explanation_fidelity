"""Candidate operational validity from outcome-blind, byte-verified reviews.

The frozen adapter must recompute and hash-bind all inputs from raw artifacts;
this pure function alone cannot authorize or seal confirmation.
"""
from .technical_predicate import evaluate as episode_checks

NATIVE_CHECKS = (
    'applied_sampling_matches_seed_and_captured_map',
    'metadata_counts_match_actual_raw_messages',
    'metadata_types_match_actual_raw_messages', 'sqlite_integrity',
    'receipt_clock_monotone', 'native_simulated_clock_monotone',
    'odometry_clock_strictly_increases',
    'historical_interface_extraction_reproduces', 'motion_action_extraction_reproduces',
    'action_boundaries_within_clock_envelope',
    'task_window_odometry_within_clock_envelope',
)


def evaluate(receipt, episode, planned, interface, native):
    result = episode_checks(receipt, episode, planned, interface)
    reasons = list(result['reasons'])
    if native.get('episode_id') != planned.get('episode_id'):
        reasons.append('NATIVE_REVIEW_EPISODE_MISMATCH')
    for name in NATIVE_CHECKS:
        if native.get('checks', {}).get(name) is not True:
            reasons.append('NATIVE_' + name.upper())
    envelope = native.get('clock_envelope_diagnostic', {})
    window = interface.get('observed_action_window', {})
    if envelope.get('observed_action_stamp_range_ns') != [window.get('start_stamp_ns'), window.get('end_stamp_ns')]:
        reasons.append('NATIVE_AND_INTERFACE_ACTION_WINDOWS_DIFFER')
    count = envelope.get('task_window_odometry_n')
    outside = envelope.get('task_window_odometry_outside_envelope_n')
    if type(count) is not int or count < 0 or type(outside) is not int or outside != 0:
        reasons.append('RETAINED_TASK_WINDOW_MEASUREMENTS_INVALID')
    return dict(schema='hexar-operational-validity-candidate/v1',
        technical_valid=not reasons, reasons=reasons, method_outcomes_accessed=False,
        navigation_success_used_as_exclusion=False,
        early_terminal_or_missing_task_window_odometry_excluded=False,
        full_stream_clock_tail_used_as_exclusion=False,
        full_admission_authorized=False,
        scope='Outcome-blind candidate predicate; raw/source/image/freshness and adapter '
              'closure must also be independently verified before final admission.')
