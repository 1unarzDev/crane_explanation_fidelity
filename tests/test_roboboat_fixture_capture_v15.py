"""Exercise the actual candidate timer method without requiring ROS imports."""
import ast
from pathlib import Path
from types import SimpleNamespace


def fixture(now, received, status='succeeded', post=8, drain=0):
    path = Path(__file__).resolve().parents[1] / 'analysis/roboboat_fixture_capture_v15/nav2_follow_path_fixture.py'
    tree = ast.parse(path.read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'FollowPathFixture')
    tick = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'tick')
    namespace = {'time': SimpleNamespace(monotonic=lambda: now)}
    exec(compile(ast.Module(body=[tick], type_ignores=[]), str(path), 'exec'), namespace)
    finished = []
    f = SimpleNamespace(started_wall=0, done=False, result_received_wall=received,
        result_status=status, args=SimpleNamespace(duration=310, post_result_seconds=post,
        bt_terminal_drain_seconds=drain), sample_trajectory=lambda elapsed: None,
        finish=finished.append, request_costmap=lambda: None,
        goal_handle=object(), initial_odom=None)
    namespace['tick'](f)
    return finished


def test_late_received_result_retains_full_capture_window():
    assert fixture(310, 309) == []
    assert fixture(316.999, 309) == []
    assert fixture(317, 309) == ['succeeded']


def test_pending_action_still_times_out_at_unchanged_deadline():
    assert fixture(309.999, None, None) == []
    assert fixture(310, None, None) == ['timeout']


def test_longer_terminal_drain_and_failure_status_retained():
    assert fixture(317, 309, 'aborted', drain=10) == []
    assert fixture(319, 309, 'aborted', drain=10) == ['aborted']
    assert fixture(317, 309, 'canceled') == ['canceled']
