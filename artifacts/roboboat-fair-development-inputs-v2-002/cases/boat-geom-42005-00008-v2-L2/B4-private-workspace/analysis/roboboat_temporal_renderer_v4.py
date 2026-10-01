"""Unpromoted development successor: communicate established sampled components.

The running stopping-pilot comparison remains frozen on v3. This candidate only
adds a positive interval witness when full kinematic/hull sample coverage exists;
missing contact and continuous-time limits remain explicit.
"""
from roboboat_temporal_renderer_v3 import render_v3

KINEMATIC=('position','heading','speed','yaw_rate','hull')


def render_v4(packet,cert):
    text=render_v3(packet,cert)
    if (cert['sampled_task_support']=='unknown'
        and cert['coverage']['complete_sampled_window']
        and all(cert['component_support'][k]=='true' for k in KINEMATIC)):
        start,end=cert['interval_s'];count=cert['coverage']['sample_count']
        gap=cert['coverage']['max_gap_s']
        witness=(f'All {count} observed samples in the declared {start:.6f}–{end:.6f} s dwell '
            'met the position, heading, translational-speed, yaw-rate and hull-containment requirements '
            f'(maximum sample gap {gap:.4f} s). Continuous-time compliance remains unestablished between samples.')
        marker='These observations do not identify the physical cause of motion;'
        text=text.replace(marker,witness+' '+marker,1)
    return text
