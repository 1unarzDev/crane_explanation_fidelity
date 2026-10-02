import pytest
from analysis.hexar_external.confirmatory_v1.measurement_rounding import check


def test_rounding_preserves_grounded_measurement_without_claiming_exactness():
    assert check(8.183021,'8.18')['numerical_presentation_matches']
    assert check(4.64001e-6,'4.64e-6')['numerical_presentation_matches']
    assert not check(4.64e-6,'4.64')['numerical_presentation_matches']
    assert not check(8.183021,'8.18',literal_exact=True)['numerical_presentation_matches']
    assert check(8.18,'8.18',literal_exact=True)['numerical_presentation_matches']


def test_rounded_zero_is_not_literal_zero_or_physical_immobility():
    result=check(.00000464,'0.000')
    assert result['numerical_presentation_matches']
    assert not result['physical_no_motion_inferred'] and not result['useful_coverage_decided']
    assert not check(.00000464,'0',literal_exact=True)['numerical_presentation_matches']
    assert not check(.00000464,'0.000000')['numerical_presentation_matches']


@pytest.mark.parametrize('reference,text',[(True,'1'),(-1.,'0'),(float('inf'),'0'),(1.,'NaN'),(1.,'1 m'),(1.,'1e999999')])
def test_invalid_or_unbounded_presentations_fail(reference,text):
    with pytest.raises(ValueError):check(reference,text)
