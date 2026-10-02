#!/usr/bin/env python3
"""Marine v1: sampled temporal certificates; no evaluator or diagnostic-core imports."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import yaml

QUESTION = 'Did the boat complete the specified docking task, and what evidence explains the difference, if any, from the navigation result?'
COMPONENTS = ('position', 'heading', 'speed', 'yaw_rate', 'hull', 'contact')


def number(value):
    value = float(value)
    if not math.isfinite(value):
        raise ValueError('nonfinite measurement')
    return value


def scoped_config(config_bytes, plugin_id=None):
    params = yaml.safe_load(config_bytes)['controller_server']['ros__parameters']
    plugins = params['goal_checker_plugins']
    if plugin_id is None:
        if len(plugins) != 1:
            raise ValueError('ambiguous goal-checker selection')
        plugin_id = plugins[0]
    if plugin_id not in plugins:
        raise ValueError('goal checker is not registered')
    checker = params[plugin_id]
    if checker['plugin'] != 'nav2_controller::StoppedGoalChecker':
        raise ValueError('unsupported goal checker')
    return {'node': 'controller_server', 'plugin_id': plugin_id,
            'plugin': checker['plugin'], 'config_sha256': hashlib.sha256(config_bytes).hexdigest(),
            **{k: number(checker[k]) for k in ('xy_goal_tolerance', 'yaw_goal_tolerance',
                                               'trans_stopped_velocity', 'rot_stopped_velocity')}}


def observation(row, contract):
    if row.get('frameId', contract['frame']) != contract['frame']:
        raise ValueError('pose frame mismatch')
    if row.get('childFrameId', 'base_link') != 'base_link':
        raise ValueError('unsupported twist frame')
    # Legacy records lack frames: caller must retain their declared limitation.
    out = {k: number(row[k]) for k in ('x', 'y', 'yaw', 'simSeconds')}
    out['frame'] = contract['frame']
    if all(k in row for k in ('bodySurge', 'bodySway', 'bodyYawRate')):
        u, v, w = [number(row[k]) for k in ('bodySurge', 'bodySway', 'bodyYawRate')]
        out['velocity'] = {'vx': u*math.cos(out['yaw'])-v*math.sin(out['yaw']),
                           'vy': u*math.sin(out['yaw'])+v*math.cos(out['yaw']), 'yaw_rate': w,
                           'source': 'delivered-odometry-twist-body-to-odom'}
    return out


def build_ladder(summary, config_bytes, contract, opaque_id):
    if summary.get('provenance') != 'latest-delivered-odometry-not-proven-internal-consumption':
        raise ValueError('unsupported odometry provenance')
    goal = summary.get('plannedPath')
    goal = goal[-1] if goal else {**summary.get('goal', {}).get('position', {}),
                                'yaw': summary.get('goal', {}).get('yaw')}
    for key in ('x', 'y', 'yaw'):
        if abs(number(goal[key])-contract['goal'][key]) > 1e-6:
            raise ValueError('goal differs from declared task')
    trajectory = summary.get('trajectory', [])
    post = [r for r in trajectory if r['phase'] == 'post_result']
    before = [r for r in trajectory if r['phase'] == 'action']
    event = summary.get('terminalEventV2')
    action = {'status': summary['status'], 'name': summary['actionName'],
              'identity': event['goal_id'] if event else None,
              'receipt_wall_seconds': event['receipt_wall_seconds'] if event else None,
              'receipt_clock': 'fixture-monotonic' if event else None,
              'event_time_support': 'recorded-client-receipt' if event else 'historical-event-time-unavailable'}
    base = {'schema': 'roboboat-evidence-packet/v1', 'packet_id': opaque_id,
            'question': QUESTION, 'task': copy.deepcopy(contract), 'configuration': scoped_config(config_bytes),
            'action': action,
            'limits': ['Delivered measurements do not prove Nav2 internal consumption.',
                       'Samples do not prove continuous-time compliance or identify a physical cause.',
                       'Contact telemetry unavailable; evaluator labels excluded.']}
    if any('frameId' not in r for r in trajectory):
        base['limits'].append('Legacy odometry frame is documented odom, not captured per sample.')
    levels = [copy.deepcopy(base)]
    return_row = event['measurement'] if event else (before[-1] if before else None)
    # The first post-result sample is never silently substituted for the action event.
    if return_row:
        base['return_observation'] = observation(return_row, contract)
        base['return_observation']['alignment'] = 'latest-delivered-at-client-receipt' if event else 'last-pre-result-observation'
    levels.append(copy.deepcopy(base))
    base['post_result'] = [observation(r, contract) for r in post]
    levels.append(copy.deepcopy(base))
    for p in levels:
        validate_packet(p)
    audit_ladder(levels)
    return levels


def validate_packet(p):
    allowed = {'schema', 'packet_id', 'question', 'task', 'configuration', 'action', 'limits',
               'return_observation', 'post_result', 'contacts'}
    if set(p)-allowed:
        raise ValueError('unapproved packet field')
    if set(p['task']) - {'schema','id','frame','clock','goal','position_tolerance_m','heading_tolerance_rad','speed_tolerance_mps','yaw_rate_tolerance_radps','hull_length_m','hull_beam_m','berth_depth_m','berth_width_m','berth_center','contact_required','interval_policy','dwell_s','capture_s','max_sample_gap_s','position_uncertainty_m','heading_uncertainty_rad','speed_uncertainty_mps','yaw_rate_uncertainty_radps','measurement_scope','continuous_time_proof','uncertainty_basis'}:
        raise ValueError('task metadata leak')
    if set(p['configuration']) - {'node','plugin_id','plugin','config_sha256','xy_goal_tolerance','yaw_goal_tolerance','trans_stopped_velocity','rot_stopped_velocity'}:
        raise ValueError('configuration metadata leak')
    for pose in (p['task']['goal'],p['task']['berth_center']):
        if set(pose) != {'x','y','yaw'}: raise ValueError('public geometry metadata leak')
        for v in pose.values(): number(v)
    for k,v in p['task'].items():
        if k.endswith(('_m','_s','_rad','_mps','_radps')) and number(v)<0: raise ValueError('negative requirement')
    if p['task']['interval_policy'] != 'first-post-result-observation-fixed-dwell':
        raise ValueError('unsupported temporal contract')
    prohibited = {'diagnostic_result', 'checked_answer', 'verification', 'final_text_verification',
                  'dockingSuccessObserved', 'gold', 'source_path', 'fixture_summary', 'evaluator_truth'}
    def walk(v):
        if isinstance(v, dict):
            if set(v) & prohibited:
                raise ValueError('evaluator/answer/path leak')
            for x in v.values(): walk(x)
        elif isinstance(v, list):
            for x in v: walk(x)
    walk(p)
    # Nested dictionaries have explicit allowlists as well.
    if set(p['action'])-{'status','name','identity','receipt_wall_seconds','receipt_clock','event_time_support'}:
        raise ValueError('action metadata leak')
    for r in [p.get('return_observation'), *p.get('post_result', [])]:
        if r is None: continue
        if set(r)-{'x','y','yaw','simSeconds','frame','velocity','alignment'}:
            raise ValueError('observation metadata leak')
        for k in ('x','y','yaw','simSeconds'): number(r[k])
        if r['frame'] != p['task']['frame']: raise ValueError('frame mismatch')
        if 'velocity' in r:
            if set(r['velocity']) != {'vx','vy','yaw_rate','source'}: raise ValueError('velocity metadata leak')
            for k in ('vx','vy','yaw_rate'): number(r['velocity'][k])


def audit_ladder(levels):
    if len(levels) != 3: raise ValueError('expected L0–L2')
    if 'return_observation' in levels[0] or 'post_result' in levels[0] or 'post_result' in levels[1]:
        raise ValueError('masked observation leaked')
    for lower, upper in zip(levels, levels[1:]):
        if any(upper.get(k) != v for k,v in lower.items()):
            raise ValueError('ladder is not removal-only nested')
    return {'status': 'PASS', 'levels': 3, 'source_tool_access': 'isolated-packet-and-source-only',
            'endpoint_or_derivation_leak': False}


def measure(row, task):
    goal = task['goal']; yaw = row['yaw']
    err = math.hypot(row['x']-goal['x'], row['y']-goal['y'])
    angle = abs(math.atan2(math.sin(yaw-goal['yaw']), math.cos(yaw-goal['yaw'])))
    margins = {'position': task['position_tolerance_m']-err,
               'heading': task['heading_tolerance_rad']-angle}
    uncertainties = {'position':task['position_uncertainty_m'], 'heading':task['heading_uncertainty_rad']}
    v = row.get('velocity')
    if v:
        speed = math.hypot(v['vx'],v['vy'])
        margins.update(speed=task['speed_tolerance_mps']-speed,
                       yaw_rate=task['yaw_rate_tolerance_radps']-abs(v['yaw_rate']))
        uncertainties.update(speed=task['speed_uncertainty_mps'],yaw_rate=task['yaw_rate_uncertainty_radps'])
    # Public oriented hull footprint, not a collision/contact inference.
    b = task['berth_center']; corners=[]
    for lx in (-task['hull_length_m']/2, task['hull_length_m']/2):
        for ly in (-task['hull_beam_m']/2, task['hull_beam_m']/2):
            dx=row['x']+lx*math.cos(yaw)-ly*math.sin(yaw)-b['x']
            dy=row['y']+lx*math.sin(yaw)+ly*math.cos(yaw)-b['y']
            bx=dx*math.cos(b['yaw'])+dy*math.sin(b['yaw'])
            by=-dx*math.sin(b['yaw'])+dy*math.cos(b['yaw'])
            corners.append(min(task['berth_depth_m']/2-abs(bx),task['berth_width_m']/2-abs(by)))
    margins['hull']=min(corners)
    uncertainties['hull']=task['position_uncertainty_m']+math.hypot(task['hull_length_m']/2,task['hull_beam_m']/2)*task['heading_uncertainty_rad']
    states={k:('true' if m >= uncertainties[k] else 'false' if m < -uncertainties[k] else 'unknown') for k,m in margins.items()}
    return {'time_s':row['simSeconds'],'position_error_m':err,'heading_error_rad':angle,
            'speed_mps':math.hypot(v['vx'],v['vy']) if v else None,
            'signed_margins':margins,'states':states}


def certificate(packet):
    validate_packet(packet)
    task=packet['task']; rows=packet.get('post_result',[])
    times=[r['simSeconds'] for r in rows]
    if any(b <= a for a,b in zip(times,times[1:])): raise ValueError('nonmonotone observation clock')
    start=times[0] if times else None
    end=start+task['dwell_s'] if start is not None else None
    selected=[r for r in rows if r['simSeconds'] <= end] if rows else []
    # Require a sample reaching the prospective interval end (within gap); never shorten dwell.
    gaps=[b-a for a,b in zip(times,times[1:]) if a <= end] if times else []
    covered=bool(times and times[-1]>=end and gaps and max(gaps)<=task['max_sample_gap_s'])
    samples=[measure(r,task) for r in selected]
    states={k:'unknown' for k in COMPONENTS}; witnesses={}; intervals={}
    for k in COMPONENTS[:-1]:
        vals=[m['states'].get(k,'unknown') for m in samples]
        violating=[m for m in samples if m['states'].get(k)=='false']
        if violating:
            states[k]='false'; witnesses[k]=violating[0]
        elif covered and vals and all(x=='true' for x in vals): states[k]='true'
        intervals[k]=[]
        for m in samples:
            s=m['states'].get(k,'unknown')
            if intervals[k] and intervals[k][-1]['state']==s:
                intervals[k][-1]['last_sample_s']=m['time_s']
            else: intervals[k].append({'state':s,'first_sample_s':m['time_s'],'last_sample_s':m['time_s']})
    contact=packet.get('contacts')
    if contact and start is not None:
        in_window=[r for r in contact['samples'] if start<=r['time_s']<=end]
        hits=[r for r in in_window if r['count']>0]
        if hits: states['contact']='false'; witnesses['contact']=hits[0]
        elif (contact.get('complete') is True and contact.get('clock')==task['clock']
              and contact['coverage'][0]<=start and contact['coverage'][1]>=end): states['contact']='true'
    sampled='false' if 'false' in states.values() else 'true' if all(v=='true' for v in states.values()) else 'unknown'
    ret=measure(packet['return_observation'],task) if 'return_observation' in packet else None
    observed_growth=None
    if ret and samples: observed_growth=samples[-1]['position_error_m']-ret['position_error_m']
    crossing_brackets={}
    for k,w in witnesses.items():
        if k=='contact': continue
        earlier=[m for m in samples if m['time_s']<w['time_s'] and m['states'].get(k)=='true']
        crossing_brackets[k]=[earlier[-1]['time_s'],w['time_s']] if earlier else None
    return {'schema':'roboboat-temporal-certificate/v1','action':packet['action'],
            'sampled_task_support':sampled,'continuous_task_support':'false' if sampled=='false' else 'unknown',
            'component_support':states,'interval_s':[start,end],'interval_policy':task['interval_policy'],
            'coverage':{'complete_sampled_window':covered,'max_gap_s':max(gaps) if gaps else None,
                        'sample_count':len(samples),'intersample_bound':None},
            'return_observation':ret,'radial_error_growth_m':observed_growth,
            'witnesses':witnesses,'crossing_observation_brackets':crossing_brackets,'sample_runs':intervals,'measurements':samples,
            'physical_cause_support':'unknown','unavailable':[k for k,v in states.items() if v=='unknown']}


def render(packet, cert):
    status=packet['action']['status']; result=cert['sampled_task_support']
    parts=[f"The navigation action reported {'success' if status=='succeeded' else status}."]
    if result=='false':
        k=next(k for k in COMPONENTS if k in cert['witnesses']); w=cert['witnesses'][k]
        if k=='position':
            parts.append(f"The specified docking dwell failed: at observed time {w['time_s']:.3f} s, position error was {w['position_error_m']:.4f} m, exceeding the {packet['task']['position_tolerance_m']:.4f} m bound.")
        elif k=='speed':
            parts.append(f"The specified docking dwell failed: at observed time {w['time_s']:.3f} s, measured speed was {w['speed_mps']:.4f} m/s, exceeding the {packet['task']['speed_tolerance_mps']:.4f} m/s bound.")
        elif k=='heading':
            parts.append(f"The specified docking dwell failed: at observed time {w['time_s']:.3f} s, heading error was {w['heading_error_rad']:.4f} rad, exceeding the {packet['task']['heading_tolerance_rad']:.4f} rad bound.")
        elif k=='yaw_rate':
            rate=packet['task']['yaw_rate_tolerance_radps']-w['signed_margins']['yaw_rate']
            parts.append(f"The specified docking dwell failed: at observed time {w['time_s']:.3f} s, measured absolute yaw rate was {rate:.4f} rad/s, exceeding the {packet['task']['yaw_rate_tolerance_radps']:.4f} rad/s bound.")
        elif k=='hull':
            parts.append(f"The specified docking dwell failed: at observed time {w['time_s']:.3f} s, signed hull clearance was {w['signed_margins']['hull']:.4f} m, below zero.")
        else:
            parts.append(f"The specified docking dwell failed: {w['count']} prohibited contacts were observed at {w['time_s']:.3f} s.")
    elif result=='true':
        parts.append(f"All required conditions held at the observed samples across the declared {packet['task']['dwell_s']:g}-second dwell; continuous-time compliance remains unestablished between samples.")
    else:
        parts.append('Physical docking completion is unestablished by the available evidence.')
        if cert['return_observation']:
            r=cert['return_observation']; speed=r['speed_mps']
            parts.append(f"The result-adjacent observation had position error {r['position_error_m']:.4f} m"+(f" and measured speed {speed:.4f} m/s." if speed is not None else '.'))
        parts.append('Missing requirements: '+', '.join(cert['unavailable'])+'.')
    if cert['return_observation'] and cert['radial_error_growth_m'] is not None:
        r=cert['return_observation']
        parts.append(f"Observed radial error grew by {cert['radial_error_growth_m']:.4f} m from a result-adjacent position margin of {r['signed_margins']['position']:.4f} m.")
    parts.append('These observations do not identify the physical cause of motion; waves, current, wind, and actuation remain unresolved.')
    return ' '.join(parts)


def main():
    p=argparse.ArgumentParser(); p.add_argument('packet',type=Path);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args(); packet=json.loads(args.packet.read_text()); cert=certificate(packet)
    args.output.write_text(json.dumps({'certificate':cert,'answer':render(packet,cert)},indent=2)+'\n')

if __name__=='__main__':main()
