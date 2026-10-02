import copy
import json
import math
from pathlib import Path
import tempfile
import unittest

from roboboat_initial_pose_contract_v1 import assess, launch_args, PREFIX, UNITS, OPTION


class InitialPoseContractTests(unittest.TestCase):
    def setUp(self):
        self.row = {'id': 'operational-pose-1', 'initial_pose_request': {'x': -2., 'y': -5., 'yaw': .25},
                    'initial_pose_units': UNITS, 'initial_pose_cli_option': OPTION}
        t = (math.pi/2 - .25)/2
        self.receipt = {'scene': 'Roboboat Course', 'body': 'boat', 'bodyType': 'ArticulationBody',
            'phase': 'sceneLoaded-before-Start-and-physics',
            'requestedRosXYAndYaw': {'x': -2., 'y': -5., 'z': .25},
            'observedUnityPosition': {'x': 5., 'y': .7, 'z': -2.},
            'observedUnityRotation': {'x': 0., 'y': math.sin(t), 'z': 0., 'w': math.cos(t)}}

    def audit(self, receipts, extra=''):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)/'worker.log'
            p.write_text('unrelated message\n' + ''.join(PREFIX + json.dumps(r) + '\n' for r in receipts) + extra)
            return assess(self.row, p)

    def test_valid_receipt_and_quaternion_sign_have_narrow_scope(self):
        for sign in (1, -1):
            for k in self.receipt['observedUnityRotation']:
                self.receipt['observedUnityRotation'][k] *= sign
            result = self.audit([self.receipt])
            self.assertTrue(result['initialization_readback_pass'])
            self.assertFalse(result['platform_qualified'])
            self.assertFalse(result['navigation_qualified'])
            self.assertEqual(result['independent_n_added'], 0)

    def test_missing_duplicate_and_malformed_receipts_fail(self):
        for records, extra in (([], ''), ([self.receipt]*2, ''), ([self.receipt], PREFIX+'{bad}\n')):
            self.assertFalse(self.audit(records, extra)['initialization_readback_pass'])

    def test_mismatched_pose_phase_body_and_rotation_fail(self):
        changes = [('requestedRosXYAndYaw', 'x', 9), ('observedUnityPosition', 'z', 8),
                   ('observedUnityRotation', 'w', 4), ('observedUnityRotation', 'x', .1)]
        for group, key, value in changes:
            receipt = copy.deepcopy(self.receipt); receipt[group][key] = value
            self.assertFalse(self.audit([receipt])['initialization_readback_pass'])
        for key, value in (('phase', 'late'), ('scene', 'Other'), ('bodyType', 'Transform'), ('body', '')):
            receipt = copy.deepcopy(self.receipt); receipt[key] = value
            self.assertFalse(self.audit([receipt])['initialization_readback_pass'])

    def test_nonfinite_incomplete_and_boolean_receipt_fail(self):
        for value in (float('nan'), float('inf'), True, '5'):
            receipt = copy.deepcopy(self.receipt); receipt['observedUnityPosition']['x'] = value
            self.assertFalse(self.audit([receipt])['initialization_readback_pass'])
        self.assertFalse(self.audit([{}])['initialization_readback_pass'])

    def test_argv_exact_roundtrip_and_duplicate_override_rejection(self):
        args = launch_args(self.row, ['--crane-frame-timing-audit', '/tmp/a'])
        self.assertEqual(tuple(map(float, args[-1].split(','))), (-2., -5., .25))
        for arg in (OPTION, OPTION+'=1,2,3'):
            with self.assertRaises(ValueError): launch_args(self.row, [arg])

    def test_invalid_requests_rejected_before_launch(self):
        for value in (float('nan'), float('inf'), True, '2', 1e39):
            row = copy.deepcopy(self.row); row['initial_pose_request']['x'] = value
            with self.assertRaises(ValueError): launch_args(row)
        row = copy.deepcopy(self.row); row['initial_pose_request']['yaw'] = math.pi+.01
        with self.assertRaises(ValueError): launch_args(row)
        row = copy.deepcopy(self.row); row['initial_pose_units']['frame'] = 'map'
        with self.assertRaises(ValueError): launch_args(row)


if __name__ == '__main__': unittest.main()
