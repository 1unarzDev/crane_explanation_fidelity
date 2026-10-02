import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from roboboat_launch_mount_v24 import launch_route, stage, binding

LAUNCHER = Path('/home/lunarz/worktrees/roboboat-command-shutdown-v17/crane_ml/Tools/Performance/run_nav2_controller_fixture_capture_v15.sh')


def actual_route_guard(root, path):
    source = LAUNCHER.read_text()
    # Execute the unchanged real guard. Nothing after it (Docker or Unity)
    # enters this preflight; root derivation is supplied exactly as the caller.
    code = source[source.index('path_file_container=""'):source.index('bt_xml_container=""')]
    return subprocess.run(['bash', '-eu', '-c', code], capture_output=True, text=True,
                          env={**os.environ, 'root_dir': str(root), 'path_file': str(path)})


class MountContractTests(unittest.TestCase):
    def test_actual_guard_accepts_caller_resolved_route(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp)/'public'; launch = Path(temp)/'isolated-launch'
            relative = 'packages/crane_ml/Tools/Performance/generated_populations/example/route.json'
            original = source/relative; original.parent.mkdir(parents=True); original.write_text('{"poses": []}')
            staged = launch/'Tools/Performance/generated_populations/example/route.json'
            staged.parent.mkdir(parents=True); staged.write_bytes(original.read_bytes())
            row = {'path_file': {'path': relative, 'sha256': hashlib.sha256(original.read_bytes()).hexdigest()}}
            result = actual_route_guard(launch, launch_route(launch, row, source))
            self.assertEqual(result.returncode, 0, 'real Nav2 path guard rejects the caller route')


    def test_real_guard_rejects_original_external_route_and_accepts_same_staged_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp)/'public'; launch = Path(temp)/'isolated-launch'
            relative = 'packages/crane_ml/Tools/Performance/generated_populations/example/route.json'
            original = source/relative; original.parent.mkdir(parents=True); original.write_text('{"poses": []}')
            staged = launch/'Tools/Performance/generated_populations/example/route.json'
            staged.parent.mkdir(parents=True); staged.write_bytes(original.read_bytes())
            row = {'path_file': {'path': relative, 'sha256': binding(original)['sha256']}}
            rejected = actual_route_guard(launch, original)
            self.assertEqual(rejected.returncode, 2)
            self.assertIn('Nav2 supplied path must be inside', rejected.stderr)
            self.assertEqual(actual_route_guard(launch, launch_route(launch, row, source)).returncode, 0)
            staged.write_text('{"changed": true}')
            with self.assertRaisesRegex(ValueError, 'declared bytes'): launch_route(launch, row, source)

    def test_staging_preserves_source_modes_bytes_and_canonical_mapping(self):
        import stat
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)/'platform'; tools = project/'Tools/Performance'; tools.mkdir(parents=True)
            for name in ('run_nav2_controller_fixture_capture_v15.sh', 'run_worker.sh', 'nav2_follow_path_fixture_capture_v15.py', 'roboboat_capture_completion_v1.py'):
                p = tools/name; p.write_text('exact launch source'); p.chmod(0o755)
            source = Path(temp)/'public'
            relative = 'packages/crane_ml/Tools/Performance/generated_populations/example/route.json'
            original = source/relative; original.parent.mkdir(parents=True); original.write_text('{"poses": []}')
            row = {'id': 'probe', 'path_file': {'path': relative, 'sha256': binding(original)['sha256']}}
            before = {str(p): binding(p) for p in tools.iterdir()}
            root = Path(temp)/'isolated-launch'; manifest = stage(project, root, [row], source)
            self.assertEqual(len(manifest['launch_files']), 4)
            self.assertEqual(before, {str(p): binding(p) for p in tools.iterdir()})
            for copied in manifest['launch_files']:
                self.assertEqual(copied['original']['sha256'], copied['snapshot']['sha256'])
                self.assertEqual(stat.S_IMODE(Path(copied['snapshot']['path']).stat().st_mode), 0o755)
            self.assertEqual(actual_route_guard(root, launch_route(root, row, source)).returncode, 0)
            with self.assertRaises(FileExistsError): stage(project, root, [row], source)

    def test_route_escape_symlink_and_changed_original_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp)/'public'; launch = Path(temp)/'isolated-launch'
            relative = 'packages/crane_ml/Tools/Performance/generated_populations/example/route.json'
            original = source/relative; original.parent.mkdir(parents=True); original.write_text('{"poses": []}')
            target = launch/'Tools/Performance/generated_populations/example/route.json'
            target.parent.mkdir(parents=True); target.symlink_to(original)
            row = {'path_file': {'path': relative, 'sha256': binding(original)['sha256']}}
            with self.assertRaisesRegex(ValueError, 'outside'): launch_route(launch, row, source)
            for path in ('/tmp/route.json', 'packages/crane_ml/../route.json', 'packages/crane_ml/Assets/route.json'):
                row['path_file']['path'] = path
                with self.assertRaises(ValueError): launch_route(launch, row, source)


if __name__ == '__main__': unittest.main()
