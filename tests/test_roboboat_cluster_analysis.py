import copy
import math
import pytest
from roboboat_cluster_analysis import QUESTIONS,score_cluster,simulation_bounds
from sequential_diagnostic_monitor import log_mixture_e_value


def cluster():
    return {'cluster_id':'one','origin':'SIMULATED','recording_valid':{'a':True,'b':True},
            'questions':[{'question_id':q,'B2':True,'B4':True} for q in QUESTIONS]}


def test_six_question_scores_produce_one_fractional_cluster_difference():
    c=cluster();c['questions'][0]['B2']=False
    result=score_cluster(c)
    assert result['difference']==pytest.approx(1/6)
    assert result['independent_n']==1 and result['question_n']==6


def test_unresolved_labels_are_adverse_bounds_instead_of_dropped_questions():
    c=cluster();c['questions'][0]['B4']=None;c['questions'][1]['B2']=None
    result=score_cluster(c)
    assert result['difference'] is None
    assert result['adverse_difference']==pytest.approx(-1/6)
    assert result['favorable_difference']==pytest.approx(1/6)


def test_actual_bounded_primitive_matches_independent_product_arithmetic():
    observations=[1/6,-2/6,4/6];null=.1;fractions=[.1,.5]
    components=[math.prod(1+fraction/(1+null)*(x-null) for x in observations)
                for fraction in fractions]
    assert math.exp(log_mixture_e_value(observations,null,fractions))==pytest.approx(sum(components)/2)


def test_invalid_capture_duplicate_ladder_and_nonboolean_success_rejected():
    c=cluster();c['recording_valid']['b']=False
    with pytest.raises(ValueError):score_cluster(c)
    c=cluster();c['questions'][-1]=copy.deepcopy(c['questions'][0])
    with pytest.raises(ValueError):score_cluster(c)
    c=cluster();c['questions'][0]['B2']=float('nan')
    with pytest.raises(ValueError):score_cluster(c)


def test_simulation_cannot_open_real_inference_or_duplicate_a_cluster():
    c=cluster();c['origin']='REAL_CAPTURE'
    with pytest.raises(ValueError,match='coordinator'):simulation_bounds([c],.01,(.1,.5))
    c=cluster()
    with pytest.raises(ValueError,match='duplicate'):simulation_bounds([c,c],.01,(.1,.5))
