"""Dual-clock post-result capture gate; no action or task-outcome decisions."""
import math


def capture_gate(trajectory, elapsed_wall, *, minimum_wall=8., minimum_sim=8., bt_drain=.5, maximum_wall=120.):
    settings=(elapsed_wall,minimum_wall,minimum_sim,bt_drain,maximum_wall)
    if any(type(v) not in (int,float) or not math.isfinite(v) or v<0 for v in settings):
        raise ValueError('finite nonnegative timing values required')
    if maximum_wall<max(minimum_wall,bt_drain) or minimum_sim<=0:
        raise ValueError('positive simulation window and adequate bounded wall cap required')
    stamps=[]
    for row in trajectory:
        if row.get('phase')!='post_result':continue
        value=row.get('simSeconds')
        if type(value) not in (int,float) or not math.isfinite(value):
            raise ValueError('finite recorded post-result simulator stamps required')
        if stamps and value<stamps[-1]:raise ValueError('post-result clock regression')
        stamps.append(value)
    span=stamps[-1]-stamps[0] if len(stamps)>=2 else 0.
    wall_ready=elapsed_wall>=max(minimum_wall,bt_drain)
    sim_ready=len(stamps)>=2 and span>=minimum_sim
    capped=elapsed_wall>=maximum_wall
    ready=wall_ready and (sim_ready or capped)
    return {'schema':'roboboat-dual-clock-post-result-capture/v28','ready':ready,
        'reason':('simulation-window-complete' if ready and sim_ready else
                  'bounded-wall-cap-incomplete' if ready else 'awaiting-dual-clock-window'),
        'observed_wall_seconds':elapsed_wall,'observed_sim_span_seconds':span,'post_result_samples':len(stamps),
        'minimum_wall_seconds':minimum_wall,'minimum_sim_seconds':minimum_sim,
        'maximum_wall_seconds':maximum_wall,'bt_drain_seconds':bt_drain,
        'simulation_window_complete':sim_ready,
        'scope':'Delivered simulator-header stamps; no continuous-time, sensing completeness, physical-stop or task-success claim.'}
