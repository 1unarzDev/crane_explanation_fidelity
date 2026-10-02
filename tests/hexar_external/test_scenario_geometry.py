import math
import pytest
from analysis.hexar_external.acquisition.scenario_geometry import trajectory,position


def test_dynamic_trajectory_is_seeded_bounded_and_uses_native_elapsed_time():
    value=trajectory(71,(0.,0.),(4.,1.))
    assert value==trajectory(71,(0.,0.),(4.,1.))
    assert value['seed']!=trajectory(72,(0.,0.),(4.,1.))['seed']
    for t in (0.,.5,1.,3.,35.):
        x,y,z=position(value,t)
        assert x==2. and abs(y-.5)<=.8 and z==.6
    assert position(value,0.)!=position(value,1.)


def test_seed_and_elapsed_time_are_not_permitted_to_be_unbound_or_nonfinite():
    with pytest.raises(ValueError):trajectory(True,(0.,0.),(4.,1.))
    with pytest.raises(ValueError):trajectory(2**32,(0.,0.),(4.,1.))
    with pytest.raises(ValueError):position(trajectory(1,(0.,0.),(4.,1.)),float('nan'))
