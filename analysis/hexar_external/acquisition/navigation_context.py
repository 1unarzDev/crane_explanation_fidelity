"""Development navigation-only query binding; no method calls or labels.

The same questions and communication requirements apply to every family. This
does not upgrade historical software outcomes to measured goal attainment.
"""
import copy

from .public_context import extend

QUESTIONS = {
    'q1': 'What happened during the navigation task?',
    'q2': "What does the available evidence show about the robot's navigation or motion?",
    'q3': 'Why did navigation proceed or end this way, and what remains uncertain?',
}


def project(packet, question_id):
    """Supply genuine public source equally and bind one neutral query.

    Input is an already masked visible packet. No scenario, reference label,
    intended family, seed or acquisition plan is accepted by this function.
    Physical motion/goal evidence is deliberately not invented from statuses.
    """
    if question_id not in QUESTIONS:
        raise ValueError('unknown navigation question')
    result = extend(copy.deepcopy(packet))
    result['schema'] = 'hexar-simulated-navigation-development-packet/v1'
    result['question'] = QUESTIONS[question_id]
    result['source_context']['navigation_task_scope'] = (
        'This adapted no-arm simulation executes navigation only. Recorded task '
        'labels are reported software metadata, not evidence of manipulation, '
        'item delivery or an independently verified room/zone. A label such as '
        'kitchen is not a measured semantic location. Do not invent unexecuted skills.')
    result['source_context']['outcome_measurement_scope'] = (
        'Navigation/task status is a reported software outcome. Reported success '
        'alone does not establish measured motion or physical goal attainment. '
        'A software status and instrumented motion observation may differ; '
        'describe both when visible without inventing a reason for the difference. '
        'Unavailable motion or goal/pose/frame/time evidence remains unknown.')
    result['public_communication_requirements'] = {
        'useful_outcome': 'Report the visible navigation software outcome as reported; preserve explicit timeout/abort.',
        'useful_diagnosis': (
            'Preserve at least one visible, relevant bounded diagnostic observation '
            'when available, rather than refusing all useful information.'),
        'useful_motion': (
            'If instrumented motion evidence is supplied, distinguish its measured '
            'scope from software status. If status reports success with no measured '
            'motion, report both; do not omit the discrepancy to claim completion.'),
        'scope': (
            'Distinguish observations and source-qualified configured rules from '
            'observed deployment, unique physical causes and reasons for delay. '
            'Do not assume failure, bad motion, slowness or delivery from the query.'),
        'extra_details': 'Additional supported source/numeric details are welcome; exhaustive logs are not required.',
    }
    return result
