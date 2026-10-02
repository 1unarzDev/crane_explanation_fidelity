"""Additive development renderer: preserve visible near-bound distinctions.

The frozen v1 renderer and already executed comparisons remain unchanged.
This successor requires its own method/source freeze before a new comparison.
"""
from roboboat_temporal_certificate import COMPONENTS, render


def distinct_decimals(value, bound):
    for digits in range(4, 13):
        observed, threshold=f'{value:.{digits}f}',f'{bound:.{digits}f}'
        if float(observed)>float(threshold):
            return observed,threshold
    return repr(value),repr(bound)


def render_v2(packet, cert):
    answer=render(packet,cert)
    if cert['sampled_task_support']!='false':return answer
    component=next(k for k in COMPONENTS if k in cert['witnesses'])
    witness=cert['witnesses'][component]
    definitions={
        'position':('position_error_m','position_tolerance_m','m'),
        'speed':('speed_mps','speed_tolerance_mps','m/s'),
        'heading':('heading_error_rad','heading_tolerance_rad','rad'),
        'yaw_rate':(None,'yaw_rate_tolerance_radps','rad/s')}
    if component in definitions:
        field,requirement,unit=definitions[component]
        bound=packet['task'][requirement]
        value=witness[field] if field else bound-witness['signed_margins'][component]
        observed,threshold=distinct_decimals(value,bound)
        old=f'{value:.4f} {unit}, exceeding the {bound:.4f} {unit} bound'
        new=f'{observed} {unit}, exceeding the {threshold} {unit} bound'
        return answer.replace(old,new,1)
    if component=='hull':
        margin=witness['signed_margins']['hull']
        if float(f'{margin:.4f}')==0:
            answer=answer.replace(f'{margin:.4f} m, below zero',f'{margin:.12g} m, below zero',1)
    return answer
