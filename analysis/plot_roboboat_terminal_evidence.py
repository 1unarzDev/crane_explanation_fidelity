#!/usr/bin/env python3
"""Standalone measured path/pose/velocity panel, with observed—not causal—witnesses."""
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    p=argparse.ArgumentParser();p.add_argument('batch',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    packet=json.loads((a.batch/'method_packets/L2.json').read_text());cert=json.loads((a.batch/'contract_outputs/L2.json').read_text())['certificate'];rows=packet['post_result'];task=packet['task'];start=rows[0]['simSeconds'];measurements=cert['measurements']
    fig,axes=plt.subplots(2,2,figsize=(10,6));path,error,speed,heading=axes.flat
    path.plot([r['x'] for r in rows],[r['y'] for r in rows],label='8-second capture')
    path.add_patch(plt.Circle((task['goal']['x'],task['goal']['y']),task['position_tolerance_m'],fill=False,linestyle='--',color='tab:red',label='position bound'))
    path.scatter([task['goal']['x']],[task['goal']['y']],marker='x',label='dock target');path.set_aspect('equal',adjustable='datalim');path.set(title='Post-result path (8-second capture)',xlabel='odom X (m)',ylabel='odom Y (m)');path.legend(fontsize=8)
    times=[m['time_s']-start for m in measurements]
    for ax,values,bound,title,unit in [(error,[m['position_error_m'] for m in measurements],task['position_tolerance_m'],'Position error','m'),(speed,[m['speed_mps'] for m in measurements],task['speed_tolerance_mps'],'Measured speed','m/s'),(heading,[m['heading_error_rad'] for m in measurements],task['heading_tolerance_rad'],'Wrapped heading error','rad')]:
        ax.plot(times,values,label='observed samples');ax.axhline(bound,color='tab:red',linestyle='--',label='task bound');ax.set(title=title,xlabel='time from first post-result sample (s)',ylabel=unit);ax.legend(fontsize=8)
    fig.suptitle('Navigation success and fixed terminal dwell — measured evidence')
    fig.text(.02,.015,'Sampled window only; contact telemetry unavailable; no physical cause identified.',fontsize=9)
    fig.tight_layout(rect=(0,.05,1,.95));a.output.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(a.output);fig.savefig(a.output.with_suffix('.png'),dpi=160)
if __name__=='__main__':main()
