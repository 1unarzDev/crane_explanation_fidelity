import numpy as np
import pytest

from analysis.hexar_external.confirmatory_v1.mixture_unknown_dependence_power import dependent_cells
from analysis.hexar_external.confirmatory_v1.mixture_family_power import simulate
from analysis.hexar_external.confirmatory_v1.mixture_statistics import power


def test_targeted_favorable_pairs_reverse_with_both_unknowns():
    assert dependent_cells(.5,.8,.5,.05,'favorable_targeted') == pytest.approx([.35,.15,.25,.25])
    cells=dependent_cells(.5,.7,.5,.05,'favorable_targeted')
    assert cells[0]-cells[1] == pytest.approx(.1)
    assert cells[0]+cells[1] == pytest.approx(.5)


def test_targeted_mapping_attains_minimum_mean_with_budget_upper_bounds():
    for d in (0,.2,.5,1):
        for q in (0,.2,.7,1):
            for share in (0,.5,1):
                for budget in (0,.01,.05,.5,1):
                    f,u,ss,ff=dependent_cells(d,q,share,0,'independent')
                    cells=dependent_cells(d,q,share,budget,'favorable_targeted')
                    assert sum(cells)==pytest.approx(1)
                    assert min(cells)>=-1e-15
                    expected=f-u-min(budget,f+ss)-min(budget,f+ff)
                    assert cells[0]-cells[1]==pytest.approx(expected)


def test_correlated_simulation_matches_homogeneous_analytic_power():
    cells=dependent_cells(.5,.7,.5,.05,'favorable_targeted')
    estimate=simulate(np.random.default_rng(1801),[216]*6,[cells]*6,40000)
    assert abs(estimate-power(1296,.5,.6))<.008


@pytest.mark.parametrize('bad',[True,float('nan'),float('inf'),-.1,1.1])
def test_invalid_budget_rejected(bad):
    with pytest.raises(ValueError): dependent_cells(.5,.8,.5,bad,'favorable_targeted')


def test_shared_flag_and_unknown_mechanism():
    assert dependent_cells(.5,.8,.5,1,'shared_outcome_independent')==[0,1,0,0]
    with pytest.raises(ValueError): dependent_cells(.5,.8,.5,.05,'unrecognized')
