import copy
import pytest
from audit_roboboat_action_trace_v1 import audit


def trace(*, stale=False, overwrite=False, pending=False):
    rows = [{'kind':'metadata','schema':'action-timing-v9','clock':'same-process-stopwatch',
             'frequency':10000000,'capacity':100000,'maxPayloadBytes':65536}]
    base = {'source':'ros:/crane/cmd_vel_stamped','episode':4,'sequence':1,'sourceTick':10,
            'receiveTick':12,'applicationTick':13,'mailbox':1,'hadPending':True,
            'decisionEpisode':4,'policy':'BoundedLag','maximumLagTicks':10}
    def add(kind, **changes): rows.append(dict(base,kind=kind,ordinal=len(rows),monotonic=len(rows)*100,**changes))
    add('ros_callback',rawSeconds=0,rawNanoseconds=200000000)
    add('receive'); add('mailbox_enqueue')
    if overwrite:
        add('mailbox_overwrite')
        base['sequence'] = 2
        add('ros_callback',rawSeconds=0,rawNanoseconds=200000000)
        add('receive');add('mailbox_enqueue')
    if not pending:
        add('mailbox_consume')
        add('gate_decision',reason='Stale' if stale else 'None',applicationTick=22 if stale else 13)
        if not stale: add('post_apply_callback',payloadEncoding='float32-le',payload=[0,0,0,0],callbackCompletionTick=13)
        counts=worker(stale);counts.pop('episodeId')
        add('counter_snapshot',snapshotTick=30,**counts)
    rows.append({'kind':'footer','dropped':0,'buffered':0,'bufferedPayloadBytes':0,
                 'writerFailed':False,'acceptedObserverSubscribed':False,'written':len(rows)-1,
                 'enqueued':len(rows)-1,'eventAttempts':len(rows)-1})
    return rows


def worker(stale=False):
    return {'episodeId':4,'acceptedActions':0 if stale else 1,'rejectedActions':1 if stale else 0,
            'staleActions':1 if stale else 0,'crossEpisodeActions':0,'duplicateActions':0}


@pytest.mark.parametrize('stale,overwrite,pending',[(False,False,False),(True,False,False),(False,True,False),(False,False,True)])
def test_conserved_receipts_include_rejection_overwrite_and_pending_without_physics_claim(stale,overwrite,pending):
    result = audit(trace(stale=stale,overwrite=overwrite,pending=pending),worker=None if pending else worker(stale))
    assert result['trace_integrity_pass'], result['issues']
    assert result['receipts'] == (2 if overwrite else 1)
    assert not result['physical_actuation_proven'] and not result['scientific_admission_authorized']
    assert result['post_apply_callbacks'] == (0 if stale or pending else 1)


@pytest.mark.parametrize('attack,expected',[
    ('dropped','FOOTER_DROPPED'),('no_footer','COMPLETE_FOOTER_REQUIRED'),
    ('no_callback','ACCEPTANCE_CALLBACK_COUNT_MISMATCH'),
    ('mutated_receipt','RECEIPT_PROVENANCE_MUTATED'),('future','FUTURE_SOURCE_TICK'),
    ('wrong_gate','GATE_POLICY_DECISION_MISMATCH'),('duplicate_ordinal','EVENT_LOSS_OR_DUPLICATE_ORDINAL'),
    ('clock','ROS_SOURCE_TICK_CONVERSION_MISMATCH'),('unknown','UNKNOWN_EVENT_KIND:unknown'),
    ('payload','INVALID_PAYLOAD_BYTES'),('worker','WORKER_EPISODE_COUNTER_RECONCILIATION_PENDING_OR_FAILED')])
def test_loss_clock_corruption_unlawful_gate_and_counter_drift_cannot_pass(attack,expected):
    rows=trace(); w=worker()
    if attack=='dropped': rows[-1]['dropped']=1
    elif attack=='no_footer': rows.pop()
    elif attack=='no_callback': rows.pop(-3)
    elif attack=='mutated_receipt': rows[-3]['sourceTick']=9
    elif attack=='future':
        for row in rows[1:-1]:row['sourceTick']=15
    elif attack=='wrong_gate': rows[-4]['reason']='Stale'
    elif attack=='duplicate_ordinal':rows[-3]['ordinal']=1
    elif attack=='clock':rows[1]['rawNanoseconds']=400000000
    elif attack=='unknown':rows[2]['kind']='unknown'
    elif attack=='payload':rows[-3]['payload']=[256]
    else:w['acceptedActions']=2
    assert expected in audit(rows,worker=w)['issues']


def test_queue_file_order_is_not_event_ordinal_order():
    rows=trace();rows[2],rows[3]=rows[3],rows[2]
    assert audit(rows)['trace_integrity_pass']


def test_rejected_receipt_cannot_have_callback_even_when_footer_claims_no_drops():
    rows=trace(stale=True)
    extra=copy.deepcopy(rows[-3]);extra.update(kind='post_apply_callback',ordinal=7,
        payloadEncoding='float32-le',payload=[0,0,0,0],callbackCompletionTick=22)
    rows.insert(-1,extra);rows[-1]['written']+=1
    assert 'CALLBACK_WITHOUT_UNIQUE_ACCEPTANCE' in audit(rows)['issues']


def test_empty_and_invalid_step_are_retained_as_unqualified():
    assert not audit([])['trace_integrity_pass']
    assert 'INVALID_FIXED_DELTA_TIME' in audit(trace(),fixed_delta_time=float('inf'))['issues']


def test_worker_must_bind_fixed_snapshot_not_shutdown_total():
    rows=trace();rows[-2]['acceptedActions']=2
    assert 'COUNTER_SNAPSHOT_RECONCILIATION_FAILED' in audit(rows,worker=worker())['issues']
    rows=trace();rows.pop(-2)
    assert 'EXACT_WORKER_COUNTER_SNAPSHOT_REQUIRED' in audit(rows,worker=worker())['issues']
