#!/usr/bin/env python3
"""Independent full-capture radial references, separate from fixed-dwell truth."""
import argparse
import json
import math
from pathlib import Path
from roboboat_temporal_certificate import measure


def inspect(root):
    rows=[]
    for name in ('boat-terminal-settling-001','boat-terminal-settling-002'):
        batch=root/'batches'/name
        packet=json.loads((batch/'method_packets/L2.json').read_text());task=packet['task']
        observations=packet['post_result']
        interval=json.loads((batch/'contract_outputs/L2.json').read_text())['certificate']['interval_s']
        # Independent arithmetic from primitive positions; production is only a
        # checked comparator, never the reference generator.
        reference=[(o['simSeconds'],math.sqrt((o['x']-task['goal']['x'])**2+
                    (o['y']-task['goal']['y'])**2)) for o in observations]
        for observation,(_,distance) in zip(observations,reference):
            if abs(measure(observation,task)['position_error_m']-distance)>1e-12:
                raise ValueError('full-capture position arithmetic differs')
        violation=next(((t,d) for t,d in reference if d-task['position_uncertainty_m']>
                        task['position_tolerance_m']),None)
        rows.append({'configuration':name,'declared_dwell_s':interval,
            'observed_capture_interval_s':[reference[0][0],reference[-1][0]],
            'last_observed_position_error_m':reference[-1][1],
            'first_capture_position_violation':{'time_s':violation[0],'position_error_m':violation[1],
                'outside_declared_dwell':violation[0]>interval[1]} if violation else None,
            'reference':'independent direct Euclidean distance over allowed full post-result positions; agrees with production primitive at every retained sample',
            'scope':'Observed crossing in the longer capture does not falsify an earlier fixed dwell; no continuous-time proof or physical-cause attribution.'})
    return {'rows':rows,'new_physical_n':0,'new_statistical_n':0,'alpha_consumed':0}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=inspect(args.root)
    if args.output.exists():
        if json.loads(args.output.read_text())!=result:raise ValueError('immutable reference differs')
    else:args.output.write_text(json.dumps(result,indent=2)+'\n')
    print('independent full-capture reference verified; fixed-dwell scope preserved')
