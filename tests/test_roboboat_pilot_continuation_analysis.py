from pathlib import Path
import pytest
import analyze_roboboat_pilot_continuation as module


def answer_rows(batch, b2=True, b4=True):
    return [{'batch':batch,'method':method,'level':level,'answer_success':success}
            for method,success in [('B2',b2),('B4',b4)] for level in range(3)]


def test_evidence_levels_and_unpaired_variant_do_not_inflate_cluster_n(monkeypatch):
    rows=answer_rows('boat-terminal-pilot-001')+answer_rows('boat-terminal-pilot-002')
    rows+=answer_rows('boat-terminal-pilot-004-render-successor-v3',False,True)
    monkeypatch.setattr(module,'analyze',lambda _: {'rows':rows})
    result=module.summarize([Path('one')])
    assert result['finalized_fresh_answers']==18
    assert result['complete_configuration_recordings']==3
    assert result['complete_independent_paired_clusters']==1
    assert result['mean_cluster_difference_B4_minus_B2']==0
    assert result['clusters'][1]['difference_B4_minus_B2'] is None


def test_average_is_over_clusters_within_original_pairing(monkeypatch):
    rows=answer_rows('boat-terminal-pilot-001')+answer_rows('boat-terminal-pilot-002')
    rows+=answer_rows('boat-terminal-pilot-005',False,True)
    rows+=answer_rows('boat-terminal-pilot-006',False,True)
    monkeypatch.setattr(module,'analyze',lambda _: {'rows':rows})
    result=module.summarize([Path('one')])
    assert result['complete_independent_paired_clusters']==2
    assert result['mean_cluster_difference_B4_minus_B2']==.5
    assert result['p_value'] is None and result['confirmation_n']==0


def test_duplicate_comparison_root_cannot_add_samples(monkeypatch):
    monkeypatch.setattr(module,'analyze',lambda _: {'rows':answer_rows('boat-terminal-pilot-001')})
    with pytest.raises(ValueError,match='duplicate answer'):
        module.summarize([Path('one'),Path('copy')])
