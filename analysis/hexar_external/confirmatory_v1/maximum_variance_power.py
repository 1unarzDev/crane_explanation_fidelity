"""Effect-floor sensitivity at maximum paired discordance; no study data read.

This is an explicit stress regime, not a universally least-favorable power
theorem or a prediction from inspected development answers. N stays unset.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import numpy as np

from .journal import exclusive_json
from .mixture_statistics import critical_count, conditional_power

ROOT = Path(__file__).resolve().parents[3]
NS = (72, 114, 192, 384, 768, 1296, 1920, 3072, 6144, 12288)
EFFECTS = (.05, .10, .20)


def report(replications=100000, seed=2026100110):
    rng = np.random.default_rng(seed)
    rows = []
    for effect in EFFECTS:
        regimes = (
            ('homogeneous', [effect]*6),
            ('unequal_positive', [x + effect - .10 for x in (0., 0., .05, .10, .15, .30)]),
            ('opposed_families', [x + effect - .10 for x in (-.80, -.60, 0., .60, .60, .80)]),
        )
        for n in NS:
            threshold = critical_count(n, .01)
            for name, effects in regimes:
                probabilities = [(1+x)/2 for x in effects]
                favorable = np.zeros(replications, dtype=int)
                for q in probabilities:
                    favorable += rng.binomial(n//6, q, size=replications)
                simulated = float(np.mean(favorable >= threshold))
                exact = conditional_power(n, (1+effect)/2, .01) if name == 'homogeneous' else None
                rows.append(dict(n=n, family_n=[n//6]*6, total_discordance_probability=1.,
                    mapped_endpoint_average_effect=effect, family_effects=effects,
                    family_favorable_probabilities=probabilities, regime=name,
                    exact_homogeneous_power=exact, simulated_power=simulated,
                    simulation_standard_error=math.sqrt(simulated*(1-simulated)/replications),
                    exact_favorable_rejection_threshold=threshold))
    sources = [Path(__file__), Path(__file__).with_name('mixture_statistics.py'),
               Path(__file__).with_name('statistics.py')]
    return dict(schema='hexar-maximum-discordance-effect-floor-sensitivity/v1',
        phase='prospective_design_only', selected_n=None, selected_effect_floor=None,
        alpha=.01, confirmatory_N=0, alpha_consumed=0, no_semantic_data_read=True,
        replications=replications, seed=seed, rows=rows,
        homogeneous_null_sizes={str(n): conditional_power(n, .5, .01) for n in NS},
        interpretation='Maximum-discordance stress scenarios; not proof of universally least-favorable power. '
            'Effects refer to the primary least-favorable mapped endpoint, not the old answer-level difference.',
        unknown_rate_limit='A complete-label effect can be degraded by outcome-dependent unknown mappings. '
            'If the allowed two-method unknown budget equals the complete-label effect, no positive '
            'mapped effect or finite-N power guarantee follows. Separate those planning quantities.',
        source_hashes={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    value = report()
    exclusive_json(args.output, value)
    for effect in EFFECTS:
        candidates = [r for r in value['rows'] if r['regime'] == 'homogeneous'
                      and r['mapped_endpoint_average_effect'] == effect and r['exact_homogeneous_power'] >= .90]
        print('Mapped effect', effect, 'first >=90% sampled grid N:', candidates[0]['n'] if candidates else None)
