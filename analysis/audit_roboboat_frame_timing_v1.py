#!/usr/bin/env python3
"""Read-only sparse frame audit. Association is not a causal diagnosis."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def audit(path):
    records=[json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if not records or records[0].get('schema') != 'crane-frame-timing-audit/v1-development':
        raise ValueError('declared frame audit metadata required')
    metadata=records[0]
    rows=records[1:]
    last_frame=-1; last_wall=-1; stale_rows=[]; issues=[]
    for row in rows:
        if row['kind'] != 'frame' or row['frame'] <= last_frame or row['wallSeconds'] < last_wall:
            raise ValueError('ordered unique timestamped frame rows required')
        for key in ('simulationSeconds','wallSeconds','deltaTime','unscaledDeltaTime','fixedDeltaTime','maximumDeltaTime'):
            if not isinstance(row[key],(int,float)) or not math.isfinite(row[key]):
                raise ValueError('finite recorded clock values required')
        for key in ('fixedUpdates','staleIncrement','staleObservations','failedObservations'):
            if type(row[key]) is not int or row[key] < 0:
                raise ValueError('nonnegative integer timing counters required')
        if abs(row['fixedDeltaTime']-metadata['fixedDeltaTime']) > 1e-7:
            issues.append('fixed_step_changed')
        if abs(row['maximumDeltaTime']-metadata['appliedMaximumDeltaTime']) > 1e-6:
            issues.append('maximum_delta_time_changed_after_install')
        if row['staleIncrement']:
            stale_rows.append({key:row[key] for key in ('frame','episode','simulationSeconds','wallSeconds',
                'fixedUpdates','unscaledDeltaTime','maximumDeltaTime','simulationTick','observationTick',
                'staleIncrement','staleObservations','pendingDepthReadbacks')})
        last_frame=row['frame'];last_wall=row['wallSeconds']
    return {'schema':'roboboat-frame-timing-audit-result/v1-development',
            'source':{'path':str(path.resolve()),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()},
            'metadata':metadata,'retained_frame_rows':len(rows), 'all_frames_retained':False,
            'stale_frames':stale_rows,'stale_increments':sum(r['staleIncrement'] for r in stale_rows),
            'stale_frames_with_four_or_more_fixed_updates':sum(r['fixedUpdates']>=4 for r in stale_rows),
            'stale_frames_without_four_or_more_fixed_updates':sum(r['fixedUpdates']<4 for r in stale_rows),
            'stale_frames_with_pending_queue_full_at_late_update':sum(r['pendingDepthReadbacks']>=2 for r in stale_rows),
            'issues':sorted(set(issues)), 'root_cause_established':False,
            'limitations':['LateUpdate queue count does not reconstruct request-time queue occupancy or GPU completion.',
                           'Clock catch-up association does not separate CPU, GPU, GC or compositor causes.',
                           'Optional maximum-delta setting changes simulation/wall catch-up; equivalence to the original platform is not assumed.',
                           'Sparse anomaly/one-second retention is not a complete frame or sensor-event trace.'],
            'configuration_n_added':0,'confirmation_n':0,'replication_n':0}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('trace',type=Path)
    p.add_argument('--output',type=Path)
    p.add_argument('--require-no-stale',action='store_true')
    a=p.parse_args();result=audit(a.trace)
    text=json.dumps(result,indent=2,allow_nan=False)+'\n'
    if a.output:
        with a.output.open('x') as stream:stream.write(text)
    else:print(text,end='')
    if result['issues'] or (a.require_no_stale and result['stale_increments']):raise SystemExit(1)


if __name__=='__main__':main()
