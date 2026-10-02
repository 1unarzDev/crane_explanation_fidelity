"""Development successor: distinguish unavailable evidence and measured margins.

Already frozen comparisons use v1. This source requires a fresh method freeze
before any new comparative use; it does not revise historical scores.
"""
from roboboat_temporal_renderer_v2 import render_v2

LABELS={'position':'position','heading':'heading','speed':'translational speed',
        'yaw_rate':'yaw rate','hull':'hull containment','contact':'contact restrictions'}


def render_v3(packet,cert):
    answer=render_v2(packet,cert)
    if cert['sampled_task_support']=='unknown':
        old='Missing requirements: '+', '.join(cert['unavailable'])+'.'
        new='The following requirements remain unestablished over the declared dwell: '+', '.join(LABELS[k] for k in cert['unavailable'])+'.'
        answer=answer.replace(old,new,1)
    if cert['return_observation'] and cert['radial_error_growth_m'] is not None:
        growth=cert['radial_error_growth_m']
        margin=cert['return_observation']['signed_margins']['position']
        old=f'Observed radial error grew by {growth:.4f} m from a result-adjacent position margin of {margin:.4f} m.'
        direction='increased' if growth>=0 else 'decreased'
        magnitude=f'{abs(growth):.4f}'
        if growth and float(magnitude)==0:magnitude=f'{abs(growth):.12f}'
        new=f'From the result-adjacent observation to the last retained dwell sample, radial error {direction} by {magnitude} m. The remaining position margin at the result-adjacent observation was {margin:.4f} m.'
        answer=answer.replace(old,new,1)
    return answer
