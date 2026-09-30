"""Independent evaluator arithmetic: no production/certificate imports."""
import math


def calculate(packet):
    t=packet['task']; rows=packet.get('post_result',[])
    if not rows:return {'sampled_task_support':'unknown','position_violation':None,'position_errors':[]}
    start=rows[0]['simSeconds'];end=start+t['dwell_s']
    times=[r['simSeconds'] for r in rows]
    if any(times[i]<=times[i-1] for i in range(1,len(times))):raise ValueError('nonmonotone clock')
    covered=times[-1]>=end and max((times[i]-times[i-1] for i in range(1,len(times)) if times[i-1]<=end),default=float('inf'))<=t['max_sample_gap_s']
    outcomes=[];errors=[];violation=None
    for row in rows:
        if row['simSeconds']>end:continue
        error=((row['x']-t['goal']['x'])**2+(row['y']-t['goal']['y'])**2)**0.5
        errors.append(error)
        delta=(row['yaw']-t['goal']['yaw']+math.pi)%(2*math.pi)-math.pi
        bad=error>t['position_tolerance_m']+t['position_uncertainty_m'] or abs(delta)>t['heading_tolerance_rad']+t['heading_uncertainty_rad']
        good=error<=t['position_tolerance_m']-t['position_uncertainty_m'] and abs(delta)<=t['heading_tolerance_rad']-t['heading_uncertainty_rad']
        if error>t['position_tolerance_m']+t['position_uncertainty_m'] and violation is None:violation=row['simSeconds']
        velocity=row.get('velocity')
        if velocity:
            speed=(velocity['vx']**2+velocity['vy']**2)**0.5
            bad |= speed>t['speed_tolerance_mps']+t['speed_uncertainty_mps'] or abs(velocity['yaw_rate'])>t['yaw_rate_tolerance_radps']+t['yaw_rate_uncertainty_radps']
            good &= speed<=t['speed_tolerance_mps']-t['speed_uncertainty_mps'] and abs(velocity['yaw_rate'])<=t['yaw_rate_tolerance_radps']-t['yaw_rate_uncertainty_radps']
        else:good=False
        # Independent footprint calculation in berth coordinates using relative rotation.
        b=t['berth_center'];cx=(row['x']-b['x'])*math.cos(b['yaw'])+(row['y']-b['y'])*math.sin(b['yaw'])
        cy=-(row['x']-b['x'])*math.sin(b['yaw'])+(row['y']-b['y'])*math.cos(b['yaw'])
        rot=row['yaw']-b['yaw'];extent_x=abs(math.cos(rot))*t['hull_length_m']/2+abs(math.sin(rot))*t['hull_beam_m']/2
        extent_y=abs(math.sin(rot))*t['hull_length_m']/2+abs(math.cos(rot))*t['hull_beam_m']/2
        clearance=min(t['berth_depth_m']/2-abs(cx)-extent_x,t['berth_width_m']/2-abs(cy)-extent_y)
        uncertainty=t['position_uncertainty_m']+((t['hull_length_m']/2)**2+(t['hull_beam_m']/2)**2)**0.5*t['heading_uncertainty_rad']
        bad |= clearance < -uncertainty;good &= clearance>=uncertainty
        outcomes.append('false' if bad else 'true' if good else 'unknown')
    contacts=packet.get('contacts');contact_state='unknown'
    if contacts:
        if any(r['count']>0 for r in contacts['samples'] if start<=r['time_s']<=end):contact_state='false'
        elif contacts.get('complete') and contacts.get('clock')==t['clock'] and contacts['coverage'][0]<=start and contacts['coverage'][1]>=end:contact_state='true'
    state='false' if 'false' in outcomes or contact_state=='false' else 'true' if covered and all(o=='true' for o in outcomes) and contact_state=='true' else 'unknown'
    return {'sampled_task_support':state,'position_violation':violation,'position_errors':errors,'covered':covered}
