import numpy as np
import pytest

from analysis.hexar_external.confirmatory_v1.mixture_family_power import allocate, mapped_cells, simulate
from analysis.hexar_external.confirmatory_v1.mixture_statistics import power


def test_balanced_and_weighted_allocations_preserve_independent_n():
    assert allocate(114,[1]*6) == [19]*6
    assert allocate(72,[2,1,1,2,3,3]) == [12,6,6,12,18,18]
    assert sum(allocate(114,[2,1,1,2,3,3])) == 114
    with pytest.raises(ValueError):
        allocate(5,[1]*6)


def test_conservative_missingness_mapping_preserves_pairs_and_cannot_improve_effect():
    assert mapped_cells(.5,.8,.5,0,0) == pytest.approx([.4,.1,.25,.25])
    assert mapped_cells(.5,.8,.5,1,1) == pytest.approx([0,1,0,0])
    for d in (0,.2,.5,1):
        for q in (0,.5,.8,1):
            for ties in (0,.5,1):
                for c,p in ((.01,0),(0,.1),(.05,.05)):
                    cells=mapped_cells(d,q,ties,c,p)
                    assert sum(cells) == pytest.approx(1)
                    assert min(cells)>=0
                    assert cells[0]-cells[1] <= d*(2*q-1)+1e-14


def test_episode_simulation_reproduces_exact_homogeneous_power():
    cells=[mapped_cells(.5,.8,.5,0,0)]*6
    estimate=simulate(np.random.default_rng(2701),[19]*6,cells,60000)
    expected=power(114,.5,.8)
    assert abs(estimate-expected) < .007
    assert simulate(np.random.default_rng(3),[12]*6,[[0,1,0,0]]*6,100) == 0
    assert simulate(np.random.default_rng(3),[12]*6,[[1,0,0,0]]*6,100) == 1


def test_opposing_family_null_does_not_trigger_excess_rejections():
    qs=[.2,.35,.45,.55,.65,.8]
    cells=[mapped_cells(.5,q,.5,0,0) for q in qs]
    estimate=simulate(np.random.default_rng(7001),[12]*6,cells,60000)
    assert estimate < .013
