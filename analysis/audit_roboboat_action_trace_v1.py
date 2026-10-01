"""Development-only v9 receipt/gate/callback audit; no scientific admission."""
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import struct


def identity(event):
    values = (event.get('source'), event.get('episode'), event.get('sequence'))
    if not isinstance(values[0], str) or not values[0] or any(type(v) is not int for v in values[1:]):
        raise ValueError('invalid receipt identity')
    return values


def audit(records, *, fixed_delta_time=.02, worker=None, raw_ros_source='ros:/crane/cmd_vel_stamped'):
    """Require a whole process trace; retain issues rather than infer missing facts.

    Whole-trace receipt accounting and worker-episode counter comparison have
    different scopes. Callback completion proves no motor/physics response.
    """
    issues = []
    def need(condition, code):
        if not condition: issues.append(code)
    if not records:
        return {'schema':'roboboat-action-trace-audit/v1-development', 'issues':['EMPTY_TRACE'],
                'trace_integrity_pass':False, 'scientific_admission_authorized':False}
    meta, footer = records[0], records[-1]
    need(meta.get('kind') == 'metadata' and meta.get('schema') == 'action-timing-v9', 'V9_METADATA_REQUIRED')
    need(meta.get('clock') == 'same-process-stopwatch' and type(meta.get('frequency')) is int and meta['frequency'] > 0, 'INVALID_CLOCK_METADATA')
    need(footer.get('kind') == 'footer', 'COMPLETE_FOOTER_REQUIRED')
    for field in ('dropped','buffered','bufferedPayloadBytes'):
        need(type(footer.get(field)) is int and footer[field] == 0, 'FOOTER_'+field.upper())
    need(footer.get('writerFailed') is False, 'WRITER_FAILED_OR_UNKNOWN')
    need(footer.get('acceptedObserverSubscribed') is False, 'OBSERVER_LIFECYCLE_INCOMPLETE')
    events = records[1:-1]
    ordinals = [e.get('ordinal') for e in events]
    need(all(type(o) is int and o > 0 for o in ordinals), 'INVALID_EVENT_ORDINAL')
    if not all(type(o) is int for o in ordinals):
        return {'schema':'roboboat-action-trace-audit/v1-development','issues':issues,
                'trace_integrity_pass':False,'scientific_admission_authorized':False}
    need(sorted(ordinals) == list(range(1,len(events)+1)), 'EVENT_LOSS_OR_DUPLICATE_ORDINAL')
    need(footer.get('written') == len(events) and type(footer.get('written')) is int, 'WRITTEN_COUNT_MISMATCH')
    for field in ('enqueued','eventAttempts'):
        need(type(footer.get(field)) is int and footer[field] == len(events), 'FOOTER_'+field.upper()+'_COUNT_MISMATCH')
    # Interlocked ordinal allocation can precede enqueue on concurrent threads.
    events = sorted(events, key=lambda e:e['ordinal'])
    receipts = {}; states = {}; pending = {}; enqueues = Counter(); attempts = defaultdict(list)
    callbacks = defaultdict(list); raw = defaultdict(list); last_applied = {}
    dispositions = Counter(); gate_counts = Counter(); source_lags = []; receive_lags = []
    try: step = struct.unpack('<f',struct.pack('<f',fixed_delta_time))[0]
    except (TypeError, OverflowError, struct.error): step = float('nan')
    need(math.isfinite(step) and step > 0, 'INVALID_FIXED_DELTA_TIME')
    known_kinds = {'receive','ros_callback','mailbox_enqueue','mailbox_overwrite','mailbox_consume',
                   'mailbox_clear','gate_decision','gate_configure','gate_episode_reset','post_apply_callback',
                   'counter_snapshot'}
    snapshots = []; snapshot_checks = []
    for e in events:
        kind = e.get('kind')
        need(kind in known_kinds, 'UNKNOWN_EVENT_KIND:'+str(kind))
        need(type(e.get('monotonic')) is int and e['monotonic'] >= 0, 'INVALID_EVENT_CLOCK')
        if kind in ('gate_configure','gate_episode_reset'):
            last_applied.clear(); continue
        if kind == 'counter_snapshot':
            snapshots.append(e)
            episode = e.get('episode')
            current = [a for values in attempts.values() for a in values if a.get('decisionEpisode') == episode]
            reasons = Counter(a.get('reason') for a in current)
            expected = {'acceptedActions':reasons['None'], 'rejectedActions':len(current)-reasons['None'],
                        'staleActions':reasons['Stale'], 'crossEpisodeActions':reasons['CrossEpisode'],
                        'duplicateActions':reasons['DuplicateOrOutOfOrder'],
                        'unknownSourceActions':sum(base.get('sourceTick',0) < 0 for key,base in receipts.items() if key[1] == episode)}
            checks = {field:type(e.get(field)) is int and e[field] == count for field,count in expected.items()}
            need(all(checks.values()) and type(episode) is int and type(e.get('snapshotTick')) is int, 'COUNTER_SNAPSHOT_RECONCILIATION_FAILED')
            snapshot_checks.append({'ordinal':e['ordinal'],'episode':episode,'checks':checks})
            continue
        if kind == 'mailbox_clear' and e.get('hadPending') is False:
            need(e.get('mailbox') not in pending, 'EMPTY_CLEAR_HIDES_PENDING_RECEIPT')
            continue
        try: key = identity(e)
        except ValueError:
            issues.append('INVALID_RECEIPT_IDENTITY'); continue
        if kind == 'ros_callback':
            raw[key].append(e)
            sec, nano = e.get('rawSeconds'), e.get('rawNanoseconds')
            need(type(sec) is int and type(nano) is int and 0 <= nano < 1000000000, 'INVALID_ROS_RAW_STAMP')
            if type(sec) is int and type(nano) is int and step > 0:
                seconds = sec + nano*1e-9
                expected = -1 if seconds < 0 else math.floor(seconds/step+.5)
                need(e.get('sourceTick') == expected, 'ROS_SOURCE_TICK_CONVERSION_MISMATCH')
            continue
        if kind == 'receive':
            need(key not in receipts, 'DUPLICATE_RECEIPT_IDENTITY')
            receipts[key] = e; states[key] = 'received'; continue
        need(key in receipts, 'EVENT_WITHOUT_RECEIVE:'+str(kind))
        if key not in receipts: continue
        base = receipts[key]
        need(all(e.get(f) == base.get(f) for f in ('sourceTick','receiveTick')), 'RECEIPT_PROVENANCE_MUTATED')
        if kind == 'mailbox_enqueue':
            box = e.get('mailbox')
            need(type(box) is int and box > 0, 'INVALID_MAILBOX_ID')
            need(box not in pending and states[key] == 'received', 'MAILBOX_ENQUEUE_WITHOUT_DISPOSAL')
            enqueues[key] += 1; pending[box] = key; states[key] = 'pending'
        elif kind in ('mailbox_overwrite','mailbox_clear','mailbox_consume'):
            box = e.get('mailbox')
            need(pending.get(box) == key and states[key] == 'pending' and e.get('hadPending') is True, 'MAILBOX_DISPOSITION_MISMATCH')
            pending.pop(box,None)
            state = {'mailbox_overwrite':'overwritten','mailbox_clear':'cleared','mailbox_consume':'consumed'}[kind]
            states[key] = state; dispositions[state] += 1
        elif kind == 'gate_decision':
            need(states[key] == 'consumed', 'GATE_WITHOUT_CONSUMED_RECEIPT')
            attempts[key].append(e)
            episode, application, source, receive, maximum = [e.get(f) for f in ('decisionEpisode','applicationTick','sourceTick','receiveTick','maximumLagTicks')]
            if not all(type(v) is int for v in (episode,application,source,receive,maximum)):
                issues.append('INVALID_GATE_INTEGER_FIELDS'); continue
            need(receive >= 0 and application >= receive, 'INVALID_RECEIVE_APPLICATION_ORDER')
            need(source < 0 or source <= application, 'FUTURE_SOURCE_TICK')
            need(e.get('policy') in ('LatestValid','BoundedLag') and maximum >= 0, 'INVALID_GATE_POLICY')
            previous = last_applied.get(key[0])
            expected = ('CrossEpisode' if key[1] != episode else
                        'DuplicateOrOutOfOrder' if previous and previous[0] == episode and key[2] <= previous[1] else
                        'Stale' if e.get('policy') == 'BoundedLag' and application-(source if source >= 0 else receive) > maximum else 'None')
            need(e.get('reason') == expected, 'GATE_POLICY_DECISION_MISMATCH')
            gate_counts[e.get('reason')] += 1
            if e.get('reason') == 'None':
                last_applied[key[0]] = (episode,key[2])
                if source >= 0: source_lags.append(application-source)
                receive_lags.append(application-receive)
        elif kind == 'post_apply_callback':
            callbacks[key].append(e)
            accepted = [a for a in attempts[key] if a.get('reason') == 'None']
            need(len(accepted) == 1, 'CALLBACK_WITHOUT_UNIQUE_ACCEPTANCE')
            if len(accepted) == 1:
                need(e.get('applicationTick') == accepted[0].get('applicationTick'), 'CALLBACK_APPLICATION_TICK_MISMATCH')
            need(type(e.get('callbackCompletionTick')) is int and type(e.get('applicationTick')) is int
                 and e['callbackCompletionTick'] >= e['applicationTick'], 'CALLBACK_COMPLETION_ORDER')
            payload = e.get('payload')
            need(isinstance(payload,list) and all(type(v) is int and 0 <= v <= 255 for v in payload), 'INVALID_PAYLOAD_BYTES')
            need(isinstance(e.get('payloadEncoding'),str) and bool(e['payloadEncoding']), 'MISSING_PAYLOAD_ENCODING')
            if isinstance(payload,list): need(len(payload) <= meta.get('maxPayloadBytes',0), 'PAYLOAD_LIMIT_EXCEEDED')
    for key in receipts:
        need(enqueues[key] == 1, 'RECEIPT_ENQUEUE_NOT_ONE_TO_ONE')
        if states[key] == 'consumed': need(bool(attempts[key]), 'CONSUMED_WITHOUT_GATE_ATTEMPT')
        accepts = sum(e.get('reason') == 'None' for e in attempts[key])
        need(accepts == len(callbacks[key]), 'ACCEPTANCE_CALLBACK_COUNT_MISMATCH')
        if key[0] == raw_ros_source:
            need(len(raw[key]) == 1, 'ROS_CALLBACK_NOT_ONE_TO_ONE')
            if len(raw[key]) == 1:
                r = raw[key][0]
                need(r.get('sourceTick') == receipts[key].get('sourceTick'), 'ROS_RECEIPT_SOURCE_TICK_MISMATCH')
                need(r.get('receiveTick',-1) <= receipts[key].get('receiveTick',-2), 'ROS_CALLBACK_RECEIVE_ORDER')
    need(set(raw) <= set(receipts), 'ROS_CALLBACK_WITHOUT_RECEIPT')
    need(len(receipts) == sum(dispositions.values())+len(pending), 'RECEIPT_CONSERVATION_MISMATCH')
    worker_checks = {}
    if worker is not None:
        episode = worker.get('episodeId')
        matches = [s for s in snapshots if s.get('episode') == episode]
        need(len(matches) == 1, 'EXACT_WORKER_COUNTER_SNAPSHOT_REQUIRED')
        cutoff = matches[0]['ordinal'] if len(matches) == 1 else -1
        decisions = sorted([e for v in attempts.values() for e in v if e.get('decisionEpisode') == episode and e['ordinal'] < cutoff], key=lambda e:e['ordinal'])
        reasons = Counter(e.get('reason') for e in decisions)
        expected_counts = {'acceptedActions':reasons['None'], 'rejectedActions':len(decisions)-reasons['None'],
                           'staleActions':reasons['Stale'], 'crossEpisodeActions':reasons['CrossEpisode'],
                           'duplicateActions':reasons['DuplicateOrOutOfOrder'],
                           'unknownSourceActions':sum(base.get('sourceTick',0) < 0 for key,base in receipts.items()
                                                     if key[1] == episode and base['ordinal'] < cutoff)}
        worker_checks = {field: type(worker.get(field)) is int and worker[field] == count for field,count in expected_counts.items()}
        if len(matches) == 1:
            worker_checks.update({field+'_snapshot':worker.get(field) == matches[0].get(field) for field in expected_counts})
        accepted = [e for e in decisions if e.get('reason') == 'None']
        known = [e for e in accepted if e['sourceTick'] >= 0]
        sl = [max(0,e['applicationTick']-e['sourceTick']) for e in known]
        rl = [max(0,e['applicationTick']-e['receiveTick']) for e in accepted]
        gaps = [max(0,b['applicationTick']-a['applicationTick']) for a,b in zip(accepted,accepted[1:])]
        expected_timing = {'acceptedActions':len(accepted), 'knownSourceActions':len(known),
                           'meanSourceToApplicationTicks':sum(sl)/len(sl) if sl else -1,
                           'maximumSourceToApplicationTicks':max(sl,default=0),
                           'meanReceiveToApplicationTicks':sum(rl)/len(rl) if rl else -1,
                           'maximumReceiveToApplicationTicks':max(rl,default=0),
                           'maximumInterApplicationTicks':max(gaps,default=0)}
        timing = worker.get('actionTiming',{})
        for field,value in expected_timing.items():
            observed=timing.get(field)
            worker_checks['timing_'+field] = (type(observed) in (float,int) and math.isfinite(observed)
                                              and math.isclose(observed,value,rel_tol=1e-12,abs_tol=1e-12))
        # Use the instrumented fixed snapshot seam, never trim to desired counts.
        need(type(episode) is int and all(worker_checks.values()), 'WORKER_EPISODE_COUNTER_RECONCILIATION_PENDING_OR_FAILED')
    return {'schema':'roboboat-action-trace-audit/v1-development', 'issues':sorted(set(issues)),
            'trace_integrity_pass':not issues, 'metadata':meta, 'footer':footer,
            'receipts':len(receipts), 'dispositions':dict(dispositions), 'pending_receipts':len(pending),
            'gate_attempts':sum(len(v) for v in attempts.values()), 'gate_reasons':dict(gate_counts),
            'post_apply_callbacks':sum(len(v) for v in callbacks.values()), 'worker_checks':worker_checks,
            'counter_snapshots_retained':len(snapshots), 'counter_snapshot_checks':snapshot_checks,
            'source_lags':source_lags,'receive_lags':receive_lags,
            'payload_source_command_equality_proven':False, 'physical_actuation_proven':False,
            'scientific_admission_authorized':False, 'confirmation_n':0,'replication_n':0}


def read(path, **kwargs):
    return audit([json.loads(line) for line in Path(path).read_text().splitlines()], **kwargs)
