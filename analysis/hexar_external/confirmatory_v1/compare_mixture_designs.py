"""Prospective theoretical procedure sensitivity; no semantic data read."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from .mixture_statistics import power as mixture_power
from .heterogeneous_statistics import power as fixed_power
from .journal import exclusive_json

ROOT=Path(__file__).resolve().parents[3]


def report():
    rows=[];grid=(72,96,144,192,288,384,576,768,1152,1920)
    for d in (.20,.35,.50,.65):
        for q in (.60,.65,.70,.75,.80):
            sensitivity={str(n):dict(uniform_mixture=mixture_power(n,d,q),fixed_fraction_04=fixed_power(n,d,q,fraction=.4)) for n in grid}
            required=next((n for n in range(6,1921,6) if mixture_power(n,d,q)>=.90),None)
            rows.append(dict(discordance=d,favorable_given_discordance=q,episode_mean_effect=d*(2*q-1),
                             conditional_expected_log_fixed_04=q*math.log(1.4)+(1-q)*math.log(.6),
                             power=sensitivity,balanced_n_for_90_mixture=required,maximum_scanned_n=1920))
    return dict(schema='hexar-uniform-mixture-design-sensitivity/v1',phase='prospective_design_only',alpha=.01,
        no_semantic_data_read=True,no_alpha_consumed=True,selected_procedure=None,selected_n=None,
        mixture='Fixed uniform lambda integral over [0,1]; one Markov-calibrated marginal test. Not a best-test selection.',
        fixed_fraction_04_blind_spot_q=math.log(1/.6)/(math.log(1.4)-math.log(.6)),
        assumptions='Exact enumeration under homogeneous paired probabilities for planning only; inferential validity allows independent nonidentical episodes.',
        rows=rows,source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path(__file__).with_name('mixture_statistics.py'),Path(__file__).with_name('heterogeneous_statistics.py'),Path(__file__).with_name('statistics.py')]})


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=ROOT/'manifests/hexar_external/confirmatory_v1/mixture_design_sensitivity_v1.json');args=ap.parse_args()
    value=report();exclusive_json(args.output,value);print('PROSPECTIVE_DESIGN_ONLY',len(value['rows']),'regimes; N/test unselected')
