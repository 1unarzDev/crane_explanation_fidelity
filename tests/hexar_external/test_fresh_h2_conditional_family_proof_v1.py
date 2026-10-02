from fractions import Fraction as F
import pytest
from analysis.hexar_external.confirmatory_v1.fresh_h2_conditional_family_proof_v1 import family_false_rejection,witnesses,ALPHA


def test_all_finite_truth_history_witnesses_and_selected_truth_example_control_family():
    rows,adaptive=witnesses()
    assert len(rows)==42 and max(F(r['family_false_rejection']) for r in rows)==ALPHA
    assert adaptive==F(1,400)


def test_invalid_h1_gate_or_conditional_h2_size_cannot_be_certified():
    hist=[dict(weight=F(1),gate=True,h2_true=True,h2_conditional_reject=ALPHA)]
    with pytest.raises(ValueError,match='H1 frozen'):family_false_rejection(True,hist)
    hist[0]['h2_conditional_reject']=F(1,2)
    with pytest.raises(ValueError,match='conditional'):family_false_rejection(False,hist)


def test_wrong_or_negative_history_mass_is_rejected():
    hist=[dict(weight=F(1,2),gate=False,h2_true=False,h2_conditional_reject=F(1))]
    with pytest.raises(ValueError,match='weights'):family_false_rejection(False,hist)
    hist.append(dict(hist[0],weight=F(-1,2)))
    with pytest.raises(ValueError):family_false_rejection(False,hist)
