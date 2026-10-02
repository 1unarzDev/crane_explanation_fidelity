"""Check the uniform exact-category interval, including the zero-discordance edge."""
import math
import pytest
from summarize_handoff_response_development import paired_interval


def test_zero_counts_use_simultaneous_category_bounds():
    for n in [2,22,42,1200]:
        expected=1-.0125**(1/n)
        assert paired_interval(0,0,n)==pytest.approx([-expected,expected],abs=1e-12)


def test_swap_directions_reflects_interval():
    low,high=paired_interval(7,2,40)
    assert low < 5/40 < high
    assert paired_interval(2,7,40)==pytest.approx([-high,-low],abs=1e-12)


def test_all_pairs_discordant_retains_boundary_and_contains_estimate():
    low,high=paired_interval(20,0,20)
    assert 0 < low < high == 1
    assert paired_interval(0,20,20)==pytest.approx([-1,-low])


def test_two_look_category_tail_gives_the_registered_zero_bound():
    expected=1-.00625**(1/600)
    assert paired_interval(0,0,600,tail_probability=.00625)==pytest.approx([-expected,expected],abs=1e-12)
