"""Supplemental same-process clock and ROS payload checks; no admission proof."""
import hashlib
import json
import math
from pathlib import Path
import struct

ROS_SOURCE='ros:/crane/cmd_vel_stamped'

def audit(records):
    issues=[]
    events=sorted(records[1:-1],key=lambda e:e['ordinal'])
    clocks=[e['monotonic'] for e in events]
    if any(b<a for a,b in zip(clocks,clocks[1:])):issues.append('SESSION_CLOCK_REVERSED')
    decoded=[]; epochs=[]; by_key={}
    for e in events:
        if e['kind'] in ('gate_episode_reset','gate_configure'):
            epochs.append({k:e[k] for k in ('kind','ordinal','decisionEpisode','policy','maximumLagTicks')})
        if e.get('source')!=ROS_SOURCE:continue
        key=(e['episode'],e['sequence'])
        prior=by_key.setdefault(key,{})
        if e['kind']=='ros_callback':prior['raw']=e
        if e['kind']=='receive':
            raw=prior.get('raw')
            if raw is None or raw['monotonic']>e['monotonic']:issues.append('RAW_CALLBACK_RECEIPT_CLOCK_ORDER')
        if e['kind']=='post_apply_callback':
            payload=e.get('payload')
            if e.get('payloadEncoding')!='float32-le[]' or not isinstance(payload,list) or len(payload)!=12 or any(type(v)is not int or not 0<=v<=255 for v in payload):
                issues.append('ROS_THREE_FLOAT_PAYLOAD_REQUIRED');continue
            values=struct.unpack('<fff',bytes(payload))
            if not all(math.isfinite(v) for v in values):issues.append('NONFINITE_DESIRED_VELOCITY')
            if e['callbackCompletionTick']!=e['applicationTick']:issues.append('ROS_CALLBACK_CROSSED_FIXED_STEP')
            decoded.append(values)
    return {'schema':'roboboat-trace-semantics/v1-development','issues':sorted(set(issues)),
            'checks_pass':not issues,'gate_boundaries':epochs,'ros_payloads_decoded':len(decoded),
            'desired_velocity_component_ranges':[{'minimum':min(x[i] for x in decoded),'maximum':max(x[i] for x in decoded)} for i in range(3)] if decoded else [],
            'zero_desired_velocity_callbacks':sum(all(v==0 for v in x) for x in decoded),
            'raw_input_payload_linkage_proven':False,'physical_actuation_proven':False,
            'timeout_transition_tick_reconstructed':False,'scientific_admission_authorized':False,
            'limitations':['ROS payloads encode accepted clamped desired forward/lateral/yaw velocity after SetDesiredVelocity; raw Twist values were not recorded.',
                'Session timestamps establish within-process event order only; no cross-process clock or network-delay inference.',
                'Timeout aggregate and warning are separate from command-receipt traces; timeout transition tick and motor response are not reconstructed.']}

def read(path):
    path=Path(path); result=audit([json.loads(x) for x in path.read_text().splitlines() if x.strip()])
    result['input']={'path':str(path.resolve()),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    return result
