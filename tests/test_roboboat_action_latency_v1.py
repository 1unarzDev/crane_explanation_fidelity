from summarize_roboboat_action_latency_v1 import summarize, distribution
from test_roboboat_action_trace_v1 import trace, worker


def test_known_clock_units_and_source_age_do_not_become_network_or_cause_claims():
    result=summarize(trace(),worker=worker())
    assert result['status']=='TRACE_INTEGRITY_PASS_DESCRIPTIVE_ONLY'
    row=result['rows'][0]
    assert row['command_source_age_at_receive_ticks']==2
    assert row['command_source_age_at_application_ticks']==3
    assert row['receive_to_application_ticks']==1
    assert row['intervals_wall_ms']['mailbox_wait']==.01
    assert not result['root_cause_identified'] and not result['physical_actuation_proven']
    assert result['independent_n_added']==0


def test_rejections_remain_separate_and_overwritten_receipts_are_not_removed():
    result=summarize(trace(stale=True),worker=worker(True))
    assert result['gate_reason_summaries']['Stale']['receipts']==1
    assert 'gate_to_callback_completion' not in result['rows'][0]['intervals_wall_ms']
    result=summarize(trace(overwrite=True),worker=worker())
    assert len(result['rows'])==2 and result['dispositions']=={'overwritten':1,'consumed':1}


def test_missing_footer_is_debug_only_and_negative_clock_intervals_are_retained():
    rows=trace();rows.pop()
    assert summarize(rows)['status']=='UNQUALIFIED_TRACE_DEBUG_ONLY'
    rows=trace();rows[4]['monotonic']=0
    result=summarize(rows)
    assert result['status']=='UNQUALIFIED_TRACE_DEBUG_ONLY'
    assert any('NEGATIVE_SAME_PROCESS' in x['issue'] for x in result['issues'])


def test_empty_distribution_retains_unknown_and_quantiles_are_interpolated():
    assert distribution([])['p95'] is None
    assert distribution([0,10])['p50']==5
    assert distribution([0,10])['p95']==9.5
