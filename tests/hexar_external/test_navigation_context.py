import copy

import pytest

from analysis.hexar_external.acquisition.navigation_context import QUESTIONS, project


def packet(status='succeeded'):
    return {
        'schema': 'hexar-permitted-method-packet/v2',
        'question': "Why didn't you bring it?",
        'evidence': {
            'navigation_outcomes': [{'evidence_id': 's0', 'status': status}],
            'manual_state': [], 'charging_state': [], 'navigation_logs': [],
            'recorded_task': [{'value': {'instruction': 'go to kitchen'}}],
        },
        'source_context': {},
        'availability': {'manual_state': 'unavailable'},
    }


def test_navigation_queries_preserve_unexpected_status_and_missing_evidence():
    original = packet(); saved = copy.deepcopy(original)
    for question_id, wording in QUESTIONS.items():
        projected = project(original, question_id)
        assert projected['question'] == wording
        assert projected['evidence'] == saved['evidence']
        assert projected['availability'] == saved['availability']
        assert 'software outcome' in projected['source_context']['outcome_measurement_scope']
        assert 'describe both' in projected['source_context']['outcome_measurement_scope']
        assert 'not a measured semantic location' in projected['source_context']['navigation_task_scope']
        assert not any(k in projected for k in ('family', 'seed', 'method', 'expected_winner'))
    assert original == saved


def test_projection_has_no_outcome_dependent_question_or_false_measurement():
    for status in ('succeeded', 'failed', 'running'):
        projected = project(packet(status), 'q3')
        assert projected['question'] == QUESTIONS['q3']
        assert 'motion_measurement' not in projected['evidence']
        assert 'goal_attainment' not in projected['evidence']
    with pytest.raises(ValueError, match='unknown navigation question'):
        project(packet(), 'delivery')
