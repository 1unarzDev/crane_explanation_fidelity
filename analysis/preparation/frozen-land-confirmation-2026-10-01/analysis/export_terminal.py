#!/usr/bin/env python3
"""Post-release descriptive CSV/SVG export; never accepts a continuation flag."""
import argparse,csv,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--result',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
r=json.loads(a.result.read_text());assert r['terminal_analysis'] and not r['continuation_required'];q=r['primary'];assert not a.output.exists();a.output.mkdir(parents=True)
rows=[{'method':m,'independent_n':q['independent_episode_n'],**{k:v for k,v in d.items()}} for m,d in q['methods'].items()]
with (a.output/'failure-coverage.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
effect={'independent_n':q['independent_episode_n'],'B2_only_failure':q['B2_fails_B4_passes'],'B4_only_failure':q['B4_fails_B2_passes'],'risk_difference_B2_minus_B4':q['paired_risk_difference_B2_minus_B4'],'ci_low':q['conservative_whole_episode_95_ci'][0],'ci_high':q['conservative_whole_episode_95_ci'][1],'confirmatory_one_sided_p':r['exact_one_sided_confirmatory_p'],'descriptive_two_sided_p':q['descriptive_exact_two_sided_p'],'coverage_passed':r['useful_coverage_requirement_passed']}
with (a.output/'paired-effect.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=effect);w.writeheader();w.writerow(effect)
level_rows=[dict(method=m,level=l,**d) for m,dec in r['decomposition'].items() for l,d in dec['levels'].items()]
with (a.output/'evidence-levels-descriptive.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=level_rows[0]);w.writeheader();w.writerows(level_rows)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,ax=plt.subplots(figsize=(6,2.5));rd=effect['risk_difference_B2_minus_B4']*100;lo=effect['ci_low']*100;hi=effect['ci_high']*100
ax.errorbar([rd],[0],xerr=[[rd-lo],[hi-rd]],fmt='o',capsize=4);ax.axvline(0,color='gray',linestyle='--');ax.set_yticks([0],['B2 − B4']);ax.set_xlabel('Absolute episode failure risk difference (percentage points)');ax.set_title(f"Frozen terminal N={effect['independent_n']}; ≥95% simultaneous interval");fig.tight_layout();fig.savefig(a.output/'paired-effect.svg');plt.close(fig)
print('Post-release terminal tables and figure written.')
