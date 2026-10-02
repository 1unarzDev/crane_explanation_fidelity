"""Development-only inversion of finite-N heterogeneous-mean e-tests.

No real-study inference or sequential validity is authorized by this module.
"""
import math
import numpy as np
from roboboat_fixed_bet_sensitivity_v1 import checked_bets, log_weighted_sum


def scores_checked(scores, origin):
    if origin != 'SIMULATED':raise ValueError('SIMULATED only; prospective study freeze required')
    x=np.asarray(scores,dtype=float)
    if x.ndim!=1 or not len(x) or not np.all(np.isfinite(x)) or np.any(np.abs(x)>1):
        raise ValueError('finite nonempty bounded independent-geometry score vector required')
    return x


def log_e_value(scores, null_mean, lambdas, weights, *, origin='SIMULATED'):
    x=scores_checked(scores,origin);lambdas,weights=checked_bets(lambdas,weights)
    if not math.isfinite(null_mean) or not -1 < null_mean <= 1:raise ValueError('null mean in (-1,1] required')
    # Center and scale preserve factor nonnegativity at every possible D in [-1,1].
    y=(x-null_mean)/(1+null_mean)
    logs=np.log1p(y[:,None]*lambdas[None,:]).sum(axis=0)
    return float(log_weighted_sum(logs,weights))


def lower_bound(scores,lambdas,weights,*,alpha=.025,origin='SIMULATED'):
    x=scores_checked(scores,origin);checked_bets(lambdas,weights)
    if not math.isfinite(alpha) or not 0 < alpha < 1:raise ValueError('alpha in (0,1) required')
    critical=math.log(1/alpha);lo=-1+1e-12;hi=1.0
    if log_e_value(x,lo,lambdas,weights,origin=origin)<critical:return -1.0
    for _ in range(80):
        middle=(lo+hi)/2
        if log_e_value(x,middle,lambdas,weights,origin=origin)>=critical:lo=middle
        else:hi=middle
    # Lower numerical bracket preserves a conservative confidence set.
    return lo


def interval(scores,lambdas,weights,*,alpha_per_tail=.025,origin='SIMULATED'):
    x=scores_checked(scores,origin)
    return [lower_bound(x,lambdas,weights,alpha=alpha_per_tail,origin=origin),
            -lower_bound(-x,lambdas,weights,alpha=alpha_per_tail,origin=origin)]
