import pytest
from publish_roboboat_terminal_capsule import publication_gate


def test_retained_timeout_is_accounted_without_becoming_complete_annotation():
    result={'schema':'roboboat-atomic-missing-judgment-development-sensitivity/v1',
        'rows':[{} for _ in range(36)],'accounted_original_answers':36,
        'finalized_answers':35,'unavailable_judgments':1,'missing_annotations':['one'],
        'original_complete_bank_score_released':False}
    publication_gate(result,'atomic-v1',36)
    with pytest.raises(RuntimeError,match='incomplete comparison'):publication_gate(result,'v3',36)
    result['finalized_answers']=34
    with pytest.raises(RuntimeError,match='complete explicit'):publication_gate(result,'atomic-v1',36)
    result['finalized_answers']=35;result['original_complete_bank_score_released']=True
    with pytest.raises(RuntimeError,match='complete explicit'):publication_gate(result,'atomic-v1',36)
