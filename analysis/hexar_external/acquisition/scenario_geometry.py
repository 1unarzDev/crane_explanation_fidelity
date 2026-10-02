"""Independently namespaced, seeded kinematic obstacle trajectory candidate."""
import hashlib
import json
import math
import random


def trajectory(seed,start_xy,goal_xy):
    if type(seed) is not int or not 0<=seed<2**32:
        raise ValueError('unsigned 32-bit episode seed required')
    if len(start_xy)!=2 or len(goal_xy)!=2 or any(type(v) not in (int,float) or not math.isfinite(v) for v in (*start_xy,*goal_xy)):
        raise ValueError('finite start/goal XY coordinates required')
    digest=hashlib.sha256(json.dumps(['hexar-dynamic-trajectory/v1',seed],separators=(',',':')).encode()).digest()
    derived=int.from_bytes(digest[:8],'big')
    return dict(profile='midpoint_lateral_sine_sim_time_v1',seed=derived,
        anchor_xy=[(start_xy[0]+goal_xy[0])/2,(start_xy[1]+goal_xy[1])/2],
        amplitude_m=.8,angular_frequency_rad_per_sim_second=1.,
        phase_rad=random.Random(derived).uniform(-math.pi,math.pi),
        motion_type='kinematic repositioning of a static simulated collision object',
        body_box_xyz_m=[.55,.65,1.2])


def position(profile,elapsed_sim_seconds):
    if type(elapsed_sim_seconds) not in (int,float) or not math.isfinite(elapsed_sim_seconds) or elapsed_sim_seconds<0:
        raise ValueError('finite nonnegative native simulated elapsed time required')
    x,y=profile['anchor_xy']
    return [x,y+profile['amplitude_m']*math.sin(profile['phase_rad']+profile['angular_frequency_rad_per_sim_second']*elapsed_sim_seconds),.6]
