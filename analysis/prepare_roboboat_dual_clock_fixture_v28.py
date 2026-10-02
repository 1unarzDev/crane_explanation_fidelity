"""Immutable capture-only candidate; original platform and bound workers untouched."""
import argparse
import ast
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=Path('/home/lunarz/worktrees/roboboat-command-shutdown-v17/crane_ml/Tools/Performance/nav2_follow_path_fixture_capture_v15.py')
HELPER=ROOT/'analysis/roboboat_post_result_clock_v28.py'
OLD='''        if (
                self.result_received_wall is not None
                and time.monotonic() - self.result_received_wall
                >= max(self.args.post_result_seconds,
                       self.args.bt_terminal_drain_seconds)):
'''
NEW='''        if (
                self.result_received_wall is not None
                and capture_gate(self.trajectory, time.monotonic() - self.result_received_wall,
                                 minimum_wall=self.args.post_result_seconds, minimum_sim=8.,
                                 bt_drain=self.args.bt_terminal_drain_seconds,
                                 maximum_wall=120.)['ready']):
'''


def binding(path):
    p=Path(path).resolve();return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}


def prepare(root):
    root=Path(root).resolve()
    if root.exists():raise FileExistsError('fresh capture-only candidate namespace required')
    original=ORIGINAL.read_text()
    if original.count(OLD)!=1 or original.count('import time\n')!=1:
        raise ValueError('exact reviewed wall-only tick seam required')
    anchor="            'postResultSecondsRequested': self.args.post_result_seconds,\n"
    if original.count(anchor)!=1:raise ValueError('exact original summary seam required')
    new=original.replace('import time\n','import time\nfrom roboboat_post_result_clock_v28 import capture_gate\n').replace(OLD,NEW)
    new=new.replace(anchor,anchor+"            'postResultCaptureClockV28': (capture_gate(self.trajectory, time.monotonic() - self.result_received_wall, minimum_wall=self.args.post_result_seconds, minimum_sim=8., bt_drain=self.args.bt_terminal_drain_seconds, maximum_wall=120.) if self.result_received_wall is not None else None),\n")
    before=ast.parse(original);after=ast.parse(new)
    def methods(tree):return {n.name:ast.dump(n,include_attributes=False) for c in tree.body if isinstance(c,ast.ClassDef) for n in c.body if isinstance(n,ast.FunctionDef)}
    a,b=methods(before),methods(after)
    changed=sorted(k for k in a if a[k]!=b[k])
    if changed!=['finish','tick'] or set(a)!=set(b):raise ValueError('unexpected fixture method change')
    root.mkdir(parents=True);base=root/'fixture-source-original-v15.py';base.write_bytes(ORIGINAL.read_bytes())
    target=root/'fixture-source-v28.py';target.write_text(new)
    helper=root/HELPER.name;helper.write_bytes(HELPER.read_bytes())
    d={'schema':'roboboat-capture-clock-candidate/v28','status':'PREPARED_UNLAUNCHED_UNQUALIFIED',
        'original':binding(ORIGINAL),'original_snapshot':binding(base),'candidate':binding(target),
        'helper':binding(HELPER),'helper_snapshot':binding(helper),'builder':binding(__file__),
        'changed_fixture_methods':changed,'unchanged_methods':sorted(set(a)-set(changed)),
        'minimum_post_result_wall_seconds':8.,'minimum_post_result_sim_span_seconds':8.,'maximum_post_result_wall_seconds':120.,
        'bounded_missingness_retained':True,'action_deadline_unchanged':True,
        'compiled_player_modified':False,'physics_navigation_task_endpoint_modified':False,
        'existing_development_records_relabelled':False,'operationally_qualified':False,
        'model_calls':0,'independent_n_added':0,'confirmation_n':0,'replication_n':0,
        'future_requirements':'Separate prospectively bound isolated runtime mount, worker/outer deadline accommodating bounded post-result cap, full original trace/sensor/transport/render/capture admission and actual complete/incomplete-timeout operational qualification. Current v27 workers/source/declared schedule unchanged.'}
    (root/'candidate.json').write_text(json.dumps(d,indent=2)+'\n');return d


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True);a=p.parse_args();d=prepare(a.root)
    print(json.dumps({'status':d['status'],'changed_methods':d['changed_fixture_methods'],'compiled_player_modified':False}))
