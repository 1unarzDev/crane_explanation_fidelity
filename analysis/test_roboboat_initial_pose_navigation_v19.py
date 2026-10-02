import ast
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import run_roboboat_initial_pose_navigation_operational_v19 as candidate
import run_roboboat_command_shutdown_operational_v18 as parent


class NavigationContractTests(unittest.TestCase):
    declaration = candidate.ROOT/'artifacts/roboboat-initial-pose-navigation-operational-v19-001/declaration.json'

    def checked(self, change=None, omit_helper=False):
        d = json.loads(self.declaration.read_text())
        registry = json.loads(Path(d['registry']).read_text())
        if change:
            change(registry)
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)/'registry.json'; p.write_text(json.dumps(registry))
            old = d['registry']; d['registry'] = str(p)
            d['dependencies'] = [v for v in d['dependencies'] if v['path'] != old]
            d['dependencies'].append({'path': str(p), 'sha256': candidate.digest(p)})
            if omit_helper:
                d['dependencies'] = [v for v in d['dependencies'] if not v['path'].endswith('roboboat_initial_pose_contract_v1.py')]
            with patch.object(candidate, 'verify_player'):
                return candidate.validate_declaration(d, self.declaration)

    def test_fixed_origins_cover_six_families_three_distance_bands(self):
        rows = self.checked()[2]
        self.assertEqual(len({r['family'] for r in rows}), 6)
        self.assertEqual({r['distance_band'] for r in rows}, {'near', 'medium', 'far'})
        self.assertEqual(len({r['cluster_id'] for r in rows}), 6)
        self.assertEqual(sum('path_file' not in r for r in rows), 1)

    def test_start_changes_cannot_hide_as_same_operational_origin(self):
        def change(registry): registry['rows'][0]['initial_pose_request']['x'] += .1
        with self.assertRaisesRegex(ValueError, 'physical configuration'):
            self.checked(change)

    def test_receipt_helper_must_be_prospectively_bound(self):
        with self.assertRaisesRegex(ValueError, 'dependencies'):
            self.checked(omit_helper=True)

    def test_all_inherited_technical_and_sensor_checks_are_unchanged(self):
        def functions(module):
            tree = ast.parse(Path(module.__file__).read_text())
            return {node.name: ast.dump(node, include_attributes=False) for node in tree.body if isinstance(node, ast.FunctionDef)}
        before, after = functions(parent), functions(candidate)
        for name in ('technical_checks', 'operational_probe_checks', 'digest_token', 'verify_player', 'default_affinity'):
            self.assertEqual(before[name], after[name], name)
        # Capture keeps every parent gate and adds only the startup readback gate.
        def check_keys(module):
            tree = ast.parse(Path(module.__file__).read_text())
            function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'capture')
            return {n.slice.value for n in ast.walk(function) if isinstance(n, ast.Subscript) and
                    isinstance(n.value, ast.Name) and n.value.id == 'checks' and isinstance(n.slice, ast.Constant)}
        self.assertEqual(check_keys(candidate)-check_keys(parent), {'initial_pose_readback'})
        self.assertTrue(check_keys(parent) <= check_keys(candidate))


if __name__ == '__main__': unittest.main()
