#!/usr/bin/env python3
"""Standalone measured path/pose/velocity panel, with observed—not causal—witnesses."""
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    p=argparse.ArgumentParser();p.add_argument('batch',type=Path);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--terminal-detail',action='store_true',help='Include yaw rate and signed hull clearance')
    p.add_argument('--mark-dwell',action='store_true',help='Distinguish declared dwell samples from later captured motion')
    a=p.parse_args()
    packet=json.loads((a.batch/'method_packets/L2.json').read_text());cert=json.loads((a.batch/'contract_outputs/L2.json').read_text())['certificate'];rows=packet['post_result'];task=packet['task'];start=rows[0]['simSeconds'];measurements=cert['measurements']
    fig,axes=plt.subplots(2,3 if a.terminal_detail else 2,figsize=(14 if a.terminal_detail else 10,6))
    panels=list(axes.flat);path,error,speed,heading=panels[:4]
    path.plot([r['x'] for r in rows],[r['y'] for r in rows],label='8-second capture')
    path.add_patch(plt.Circle((task['goal']['x'],task['goal']['y']),task['position_tolerance_m'],fill=False,linestyle='--',color='tab:red',label='position bound'))
    path.scatter([task['goal']['x']],[task['goal']['y']],marker='x',label='dock target');path.set_aspect('equal',adjustable='datalim');path.set(title='Post-result path (8-second capture)',xlabel='odom X (m)',ylabel='odom Y (m)');path.legend(fontsize=8)
    if a.mark_dwell:
        dwell=[r for r in rows if cert['interval_s'][0]<=r['simSeconds']<=cert['interval_s'][1]]
        path.plot([r['x'] for r in dwell],[r['y'] for r in dwell],color='tab:green',linewidth=3,label=f"declared {task['dwell_s']:g}-second dwell samples")
        path.scatter([dwell[-1]['x']],[dwell[-1]['y']],color='tab:green',marker='o',label='last dwell sample')
        path.scatter([rows[-1]['x']],[rows[-1]['y']],color='tab:blue',marker='s',label='last captured sample (~8 s)')
        path.get_legend().remove()
        handles,labels=path.get_legend_handles_labels()
        fig.legend(handles,labels,fontsize=8,loc='upper center',bbox_to_anchor=(.5,.95),ncol=3)
    times=[m['time_s']-start for m in measurements]
    curves=[(error,[m['position_error_m'] for m in measurements],task['position_tolerance_m'],'Position error','m'),(speed,[m['speed_mps'] for m in measurements],task['speed_tolerance_mps'],'Measured speed','m/s'),(heading,[m['heading_error_rad'] for m in measurements],task['heading_tolerance_rad'],'Wrapped heading error','rad')]
    if a.terminal_detail:
        curves.extend([(panels[4],[task['yaw_rate_tolerance_radps']-m['signed_margins']['yaw_rate'] for m in measurements],task['yaw_rate_tolerance_radps'],'Absolute measured yaw rate','rad/s'),
                       (panels[5],[m['signed_margins']['hull'] for m in measurements],0,'Signed hull clearance','m')])
    for ax,values,bound,title,unit in curves:
        ax.plot(times,values,label='observed samples');ax.axhline(bound,color='tab:red',linestyle='--',label='task bound');ax.set(title=title,xlabel='time from first post-result sample (s)',ylabel=unit);ax.legend(fontsize=8)
    fig.suptitle('Navigation success and fixed terminal dwell — measured evidence')
    fig.text(.02,.015,'Sampled window only; contact telemetry unavailable; no physical cause identified.',fontsize=9)
    fig.tight_layout(rect=(0,.05,1,.9 if a.mark_dwell else .95));a.output.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(a.output);fig.savefig(a.output.with_suffix('.png'),dpi=160)
if __name__=='__main__':main()
