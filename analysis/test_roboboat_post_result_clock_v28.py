"""Exercise the actual fixture tick AST on retained clocks, without ROS startup."""
import ast
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

from roboboat_post_result_clock_v28 import capture_gate

ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path('/home/lunarz/worktrees/roboboat-command-shutdown-v17/crane_ml/Tools/Performance/nav2_follow_path_fixture_capture_v15.py')


def fixture_tick(path,now):
    tree=ast.parse(Path(path).read_text())
    method=next(n for c in tree.body if isinstance(c,ast.ClassDef) for n in c.body if isinstance(n,ast.FunctionDef) and n.name=='tick')
    namespace={'time':SimpleNamespace(monotonic=lambda:now),'capture_gate':capture_gate}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),str(path),'exec'),namespace)
    return namespace['tick']


def fake(trajectory):
    obj=SimpleNamespace(started_wall=0.,result_received_wall=100.,done=False,result_status='succeeded',trajectory=trajectory,
        args=SimpleNamespace(post_result_seconds=8.,bt_terminal_drain_seconds=.5,duration=310.))
    obj.sample_trajectory=lambda elapsed:None
    obj.request_costmap=lambda:None
    def finish(status):obj.done=True;obj.finished_status=status
    obj.finish=finish
    return obj


class PostResultClockTests(unittest.TestCase):
    def rows(self,end):return [{'phase':'post_result','simSeconds':10.},{'phase':'post_result','simSeconds':10.+end}]

    def test_original_actual_tick_demonstrates_wall_only_termination(self):
        obj=fake(self.rows(.3));fixture_tick(SOURCE,108.1)(obj)
        self.assertTrue(obj.done)
        self.assertFalse(capture_gate(obj.trajectory,8.1)['simulation_window_complete'])

    def test_candidate_actual_tick_waits_on_retained_incomplete_episode(self):
        candidate=ROOT/'artifacts/roboboat-dual-clock-capture-candidate-v28-001/fixture-source-v28.py'
        if not candidate.exists():candidate=SOURCE
        p=ROOT/'artifacts/roboboat-varied-start-development-v27-001/captures/boat-geom-42007-00062-v2/fixture-summary.json'
        summary=json.loads(p.read_text());obj=fake(summary['trajectory'])
        fixture_tick(candidate,108.1)(obj)
        self.assertFalse(obj.done,'Wall-only capture stopped before the task simulator-time dwell was observed')

    def test_complete_clock_requires_wall_and_bt_drain_and_cap_retains_missingness(self):
        self.assertFalse(capture_gate(self.rows(8.1),7.9)['ready'])
        self.assertTrue(capture_gate(self.rows(8.1),8.1)['simulation_window_complete'])
        partial=capture_gate(self.rows(.3),120.)
        self.assertTrue(partial['ready']);self.assertFalse(partial['simulation_window_complete'])
        self.assertEqual(partial['reason'],'bounded-wall-cap-incomplete')
        self.assertFalse(capture_gate([],8.1)['ready'])
        self.assertTrue(capture_gate([],120.)['ready'])

    def test_bad_clock_values_and_regressions_rejected(self):
        for rows in (self.rows(-1),[{'phase':'post_result','simSeconds':float('nan')} ]):
            with self.assertRaises(ValueError):capture_gate(rows,8.)
        for settings in ({'maximum_wall':1.},{'minimum_sim':0.},{'elapsed_wall':float('inf')}):
            args={'elapsed_wall':8.};args.update(settings)
            with self.assertRaises(ValueError):capture_gate([],**args)

if __name__=='__main__':unittest.main()
