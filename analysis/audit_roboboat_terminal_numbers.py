#!/usr/bin/env python3
"""Independent rounded-value audit; associations/temporal language remain semantic checks."""
import argparse,json,math,re
from pathlib import Path
from build_roboboat_terminal_batch import save


def allowed(packet):
    t=packet['task'];g=t['goal'];b=t['berth_center'];cfg=packet['configuration']
    values={'m':[t['position_tolerance_m'],t['hull_length_m'],t['hull_beam_m'],t['berth_width_m'],t['berth_depth_m'],cfg['xy_goal_tolerance']],
            'm/s':[t['speed_tolerance_mps'],cfg['trans_stopped_velocity']],
            'rad':[t['heading_tolerance_rad'],cfg['yaw_goal_tolerance']],
            'rad/s':[t['yaw_rate_tolerance_radps'],cfg['rot_stopped_velocity']],
            's':[t['dwell_s'],t['capture_s'],t['max_sample_gap_s']]}
    rows=packet.get('post_result',[]);ret=packet.get('return_observation');all_rows=([ret] if ret else [])+rows
    errors=[]
    for r in all_rows:
        error=math.sqrt((r['x']-g['x'])**2+(r['y']-g['y'])**2);errors.append(error)
        angle=abs((r['yaw']-g['yaw']+math.pi)%(2*math.pi)-math.pi)
        cx=(r['x']-b['x'])*math.cos(b['yaw'])+(r['y']-b['y'])*math.sin(b['yaw']);cy=-(r['x']-b['x'])*math.sin(b['yaw'])+(r['y']-b['y'])*math.cos(b['yaw']);rot=r['yaw']-b['yaw']
        clearance=min(t['berth_depth_m']/2-abs(cx)-abs(math.cos(rot))*t['hull_length_m']/2-abs(math.sin(rot))*t['hull_beam_m']/2,
                      t['berth_width_m']/2-abs(cy)-abs(math.sin(rot))*t['hull_length_m']/2-abs(math.cos(rot))*t['hull_beam_m']/2)
        values['m'] += [error,t['position_tolerance_m']-error,r['x'],r['y'],clearance]
        values['rad'] += [angle,r['yaw'],t['heading_tolerance_rad']-angle]
        values['s'].append(r['simSeconds'])
        if 'velocity' in r:
            v=r['velocity'];speed=math.sqrt(v['vx']**2+v['vy']**2)
            values['m/s'] += [speed,v['vx'],v['vy'],t['speed_tolerance_mps']-speed]
            values['rad/s'] += [v['yaw_rate'],abs(v['yaw_rate']),t['yaw_rate_tolerance_radps']-abs(v['yaw_rate'])]
    if ret:
        values['m'] += [e-errors[0] for e in errors]
        values['m'] += [math.sqrt((r['x']-ret['x'])**2+(r['y']-ret['y'])**2) for r in rows]
    if rows:
        values['s'] += [rows[0]['simSeconds']+t['dwell_s']]+[r['simSeconds']-rows[0]['simSeconds'] for r in rows]
        values['s'] += [rows[i]['simSeconds']-rows[i-1]['simSeconds'] for i in range(1,len(rows))]
    event=packet['action'].get('receipt_wall_seconds')
    if event is not None:values['s'].append(event)
    return values


def audit(answer,packet):
    facts=allowed(packet);checks=[]
    for match in re.finditer(r'(?<![\w.])(-?\d+(?:\.\d+)?)\s*(m/s|rad/s|rad|m|s|seconds)\b',answer):
        token,unit=match.groups();unit='s' if unit=='seconds' else unit
        decimals=len(token.split('.')[1]) if '.' in token else 0
        tolerance=.5*10**(-decimals)+1e-9
        closest=min(facts[unit],key=lambda x:abs(x-float(token)))
        checks.append({'span':match.group(),'unit':unit,'matched_reference_value':closest,
                       'rounded_value_supported':abs(closest-float(token))<=tolerance})
    return {'checks':checks,'pass':all(c['rounded_value_supported'] for c in checks),
            'limitation':'Rounded numeric value/unit inventory only; association, modality, ranges and temporal scope require the complete qualified semantic packet.'}


def main():
    p=argparse.ArgumentParser();p.add_argument('comparison',type=Path);p.add_argument('--batch-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();rows=[]
    for path in sorted(a.comparison.glob('*/L*/B[24].json')):
        batch=path.parent.parent.name;level=path.parent.name;packet=json.loads((a.batch_root/batch/'method_packets'/f'{level}.json').read_text());answer=json.loads(path.read_text())['answer']
        rows.append({'batch':batch,'level':level,'method':path.stem,**audit(answer,packet)})
    result={'schema':'roboboat-numeric-value-unit-audit/v1','rows':rows,'all_pass':all(r['pass'] for r in rows)};save(a.output,result);print('rows',len(rows),'all_pass',result['all_pass'])
if __name__=='__main__':main()
