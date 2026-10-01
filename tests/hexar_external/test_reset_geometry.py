import math
import pytest
from analysis.hexar_external.acquisition.reset_geometry import review


def quaternion(yaw):return (0.,0.,math.sin(yaw/2),math.cos(yaw/2))


def test_heading_and_position_both_required_for_reset():
    assert review((1.,2.,.001),quaternion(.5),(1.,2.),.5)['in_tolerance']
    wrong=review((1.,2.,.001),quaternion(.7),(1.,2.),.5)
    assert wrong['position_in_tolerance'] and not wrong['heading_in_tolerance'] and not wrong['in_tolerance']
    wrong=review((1.1,2.,.001),quaternion(.5),(1.,2.),.5)
    assert wrong['heading_in_tolerance'] and not wrong['position_in_tolerance']


def test_heading_error_wraps_at_pi_instead_of_false_reset_failure():
    value=review((0.,0.,0.),quaternion(-math.pi+.01),(0.,0.),math.pi-.01)
    assert value['heading_error_rad']==pytest.approx(.02) and value['in_tolerance']


def test_invalid_or_unnormalized_geometry_fails_closed():
    with pytest.raises(ValueError):review((0.,0.,0.),(0.,0.,0.,0.),(0.,0.),0.)
    with pytest.raises(ValueError):review((float('nan'),0.,0.),quaternion(0.),(0.,0.),0.)
    with pytest.raises(ValueError):review((True,0.,0.),quaternion(0.),(0.,0.),0.)
