"""Secondary summaries must retain missingness and avoid double-counting spans."""
from analysis.hexar_external.confirmatory_v1.development_unique_secondary import summarize_method


def output(uid,valid=True):
    return dict(unique_request_id=uid,status='VALID' if valid else 'TECHNICAL_FAILURE',
                word_count=20 if valid else None,output_word_allowance_met=valid,
                model_calls=1,latency_seconds=2)


def label(unsupported=False,ambiguous=False):
    return dict(status='FAIL' if unsupported else 'UNRESOLVED' if ambiguous else 'PASS',
        label=dict(covered_units=['outcome'],unsupported_material=unsupported,
                   overlicensed_specificity=False,ambiguous_spans=['unclear'] if ambiguous else []))


def test_timeout_stays_in_planned_denominator_and_unknown_coverage():
    outputs=[output('a'),output('b',False)]
    labels={'a':label(),'b':dict(status='UNRESOLVED',label=None)}
    row=summarize_method(outputs,labels,{'a':['outcome'],'b':['outcome','motion']})
    assert row['useful_supported_answer_rate_bounds']==[.5,1]
    assert row['complete_required_unit_coverage_bounds']==[.5,1]
    assert row['required_unit_recall_bounds']==[1/3,1]
    assert row['unsupported_material_rate_bounds']==[0,.5]
    assert row['model_calls']==2 and row['valid_outputs']==1


def test_definite_unsupported_and_other_ambiguous_material_count_once():
    row=summarize_method([output('a')],{'a':label(True,True)},{'a':['outcome']})
    assert row['unsupported_material_rate_bounds']==[1,1]
    assert row['useful_supported_answer_rate_bounds']==[0,0]
    assert row['complete_required_unit_coverage_bounds']==[1,1]
