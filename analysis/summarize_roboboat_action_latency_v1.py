"""Descriptive command-age decomposition; no root cause or scientific N."""
from collections import Counter, defaultdict
import json
from pathlib import Path
import hashlib
import math

from audit_roboboat_action_trace_v1 import audit, identity


def distribution(values):
    values = sorted(values)
    if not values: return {'count':0,'minimum':None,'p50':None,'p95':None,'p99':None,'maximum':None}
    def quantile(q):
        x = (len(values)-1)*q; i = math.floor(x); j = min(i+1,len(values)-1)
        return values[i]+(values[j]-values[i])*(x-i)
    return {'count':len(values),'minimum':values[0],'p50':quantile(.5),
            'p95':quantile(.95),'p99':quantile(.99),'maximum':values[-1]}


def summarize(records, *, worker=None, fixed_delta_time=.02):
    integrity = audit(records,worker=worker,fixed_delta_time=fixed_delta_time)
    frequency = records[0].get('frequency') if records else None
    groups = defaultdict(lambda:defaultdict(list))
    for event in records:
        if event.get('kind') in ('metadata','footer','gate_configure','gate_episode_reset','counter_snapshot'): continue
        try:key=identity(event)
        except ValueError:continue
        groups[key][event['kind']].append(event)
    rows = []; issues = []
    for key, kinds in groups.items():
        receives = kinds.get('receive',[])
        if len(receives) != 1:
            issues.append({'identity':key,'issue':'NONUNIQUE_OR_MISSING_RECEIVE'}); continue
        base = receives[0]
        row = {'source':key[0],'episode':key[1],'sequence':key[2],
               'source_tick':base['sourceTick'],'receive_tick':base['receiveTick'],
               'command_source_age_at_receive_ticks':base['receiveTick']-base['sourceTick'] if base['sourceTick'] >= 0 else None,
               'gate_attempts':len(kinds.get('gate_decision',[])), 'gate_reason':None,
               'terminal_disposition':None, 'intervals_wall_ms':{}}
        for kind, disposition in [('mailbox_consume','consumed'),('mailbox_clear','cleared'),('mailbox_overwrite','overwritten')]:
            if kinds.get(kind):
                if row['terminal_disposition'] is not None:issues.append({'identity':key,'issue':'MULTIPLE_TERMINAL_DISPOSITIONS'})
                row['terminal_disposition']=disposition
        if row['terminal_disposition'] is None:row['terminal_disposition']='pending_or_unaccounted'
        decisions = kinds.get('gate_decision',[])
        if len(decisions)==1:
            d=decisions[0];row['gate_reason']=d['reason']
            row['receive_to_application_ticks']=d['applicationTick']-d['receiveTick']
            row['command_source_age_at_application_ticks']=d['applicationTick']-d['sourceTick'] if d['sourceTick']>=0 else None
            row['configured_maximum_lag_ticks']=d['maximumLagTicks']
            row['configured_policy']=d['policy']
        elif decisions:issues.append({'identity':key,'issue':'REPEATED_GATE_ATTEMPT_NO_SINGLE_LATENCY_ESTIMATE'})
        pairs = [('ros_callback','receive','callback_to_receipt'),('receive','mailbox_enqueue','receipt_to_enqueue'),
                 ('mailbox_enqueue','mailbox_consume','mailbox_wait'),('mailbox_consume','gate_decision','consume_to_gate'),
                 ('gate_decision','post_apply_callback','gate_to_callback_completion')]
        for start,end,name in pairs:
            if len(kinds.get(start,[]))==len(kinds.get(end,[]))==1 and type(frequency) is int and frequency>0:
                delta = kinds[end][0]['monotonic']-kinds[start][0]['monotonic']
                row['intervals_wall_ms'][name] = delta*1000/frequency
                if delta<0:issues.append({'identity':key,'issue':'NEGATIVE_SAME_PROCESS_INTERVAL:'+name})
        rows.append(row)
    summaries = {}
    for reason in sorted({row['gate_reason'] or 'NO_UNIQUE_GATE_DECISION' for row in rows}):
        subset=[row for row in rows if (row['gate_reason'] or 'NO_UNIQUE_GATE_DECISION')==reason]
        values={name:distribution([row[name] for row in subset if row.get(name) is not None])
                for name in ('command_source_age_at_receive_ticks','command_source_age_at_application_ticks','receive_to_application_ticks')}
        wall_names=sorted({name for row in subset for name in row['intervals_wall_ms']})
        values['wall_intervals_ms']={name:distribution([row['intervals_wall_ms'][name] for row in subset if name in row['intervals_wall_ms']]) for name in wall_names}
        summaries[reason]={'receipts':len(subset),**values}
    return {'schema':'roboboat-command-age-decomposition/v1-development','integrity':integrity,
            'status':'TRACE_INTEGRITY_PASS_DESCRIPTIVE_ONLY' if integrity['trace_integrity_pass'] and not issues else 'UNQUALIFIED_TRACE_DEBUG_ONLY',
            'rows':rows,'gate_reason_summaries':summaries,'issues':issues,
            'dispositions':dict(Counter(row['terminal_disposition'] for row in rows)),
            'scope':'Source age follows command provenance, not network residence or Nav2 odometry consumption. Stopwatch differences are same-process only.',
            'root_cause_identified':False,'physical_actuation_proven':False,'scientific_admission_authorized':False,
            'independent_n_added':0,'confirmation_n':0,'replication_n':0}


def retain(trace_path,worker_path,output):
    trace_path,worker_path,output=map(Path,(trace_path,worker_path,output))
    if output.exists():raise FileExistsError('immutable decomposition namespace exists')
    trace_bytes=trace_path.read_bytes();worker_bytes=worker_path.read_bytes()
    result=summarize([json.loads(line) for line in trace_bytes.decode().splitlines()],worker=json.loads(worker_bytes))
    result['inputs']=[{'path':str(p.resolve()),'sha256':hashlib.sha256(data).hexdigest()}
                      for p,data in [(trace_path,trace_bytes),(worker_path,worker_bytes),(Path(__file__),Path(__file__).read_bytes())]]
    with output.open('x') as stream:json.dump(result,stream,indent=2)
    return result
