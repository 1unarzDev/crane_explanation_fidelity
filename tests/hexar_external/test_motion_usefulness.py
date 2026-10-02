import pytest
from analysis.hexar_external.confirmatory_v1.motion_usefulness import scalar,interval


def test_supported_coarse_number_does_not_earn_useful_coverage():
    coarse=scalar(3.14,'3',source_window_qualified=True)
    assert coarse['numerical_presentation_matches'] and not coarse['useful_motion_coverage']
    assert scalar(3.14,'3.1',source_window_qualified=True)['useful_motion_coverage']
    assert not scalar(3.14,'3.1',source_window_qualified=False)['useful_motion_coverage']


def test_tiny_approximate_distance_is_not_exact_zero_or_physical_immobility():
    value=scalar(.00000464,'0.0',source_window_qualified=True)
    assert value['useful_motion_coverage'] and not value['physical_no_motion_inferred']
    assert not scalar(.00000464,'0.0',source_window_qualified=True,literal_exact=True)['useful_motion_coverage']
    assert not scalar(.00000464,'4.64',source_window_qualified=True)['useful_motion_coverage']


def test_closed_and_open_quantitative_bounds_protect_usefulness():
    assert interval(.00000464,'0','0.1',upper_closed=False,source_window_qualified=True)['useful_motion_coverage']
    assert not interval(.1,'0','0.1',upper_closed=False,source_window_qualified=True)['numerical_presentation_matches']
    assert interval(.1,'0','0.1',source_window_qualified=True)['useful_motion_coverage']
    broad=interval(3.14,'0','100',source_window_qualified=True)
    assert broad['numerical_presentation_matches'] and not broad['useful_motion_coverage']
    assert not interval(3.14,'3.1','3.2',source_window_qualified=False)['useful_motion_coverage']


@pytest.mark.parametrize('reported',['-0.1','NaN','1e999','1 m',True])
def test_malformed_or_negative_distance_fails_closed(reported):
    with pytest.raises(ValueError):scalar(1,reported,source_window_qualified=True)


def test_invalid_boundary_or_grounding_types_fail_closed():
    with pytest.raises(ValueError):interval(1,'2','1',source_window_qualified=True)
    with pytest.raises(ValueError):interval(1,'1','1',upper_closed=False,source_window_qualified=True)
    with pytest.raises(ValueError):scalar(1,'1.0',source_window_qualified=1)
