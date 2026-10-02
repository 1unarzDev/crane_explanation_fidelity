import copy
from pathlib import Path
import unittest

from probe_roboboat_parallel_players_v20 import simultaneous_progress, assess_worker


class ConcurrentPlayerTests(unittest.TestCase):
    def sample(self, time, counts=(2, 2)):
        return {'elapsed_wall_s': time, 'observations': [
            {'case_id': str(i), 'wrapper_live': True, 'validation_records': counts[i],
             'clients': [{'pid': i+10, 'class': f'nonce-{i}', 'mapped': True,
                          'monitor': i+20, 'workspace': {'name': f'ws-{i}'}}]}
            for i in range(2)]}

    def test_growing_streams_in_distinct_simultaneous_windows(self):
        self.assertTrue(simultaneous_progress([self.sample(0), self.sample(2, (4, 3))]))

    def test_no_pass_from_sequential_or_static_or_one_growing_player(self):
        for counts in ((2, 2), (2, 4), (4, 2)):
            self.assertFalse(simultaneous_progress([self.sample(0), self.sample(2, counts)]))
        samples = [self.sample(0), self.sample(2, (4, 4))]
        samples[0]['observations'][0]['wrapper_live'] = False
        samples[1]['observations'][1]['wrapper_live'] = False
        self.assertFalse(simultaneous_progress(samples))
        self.assertFalse(simultaneous_progress([self.sample(0), self.sample(.5, (4, 4))]))

    def test_duplicate_pid_class_monitor_workspace_or_windows_refused(self):
        for key in ('pid', 'class', 'monitor', 'workspace'):
            samples = [self.sample(0), self.sample(2, (4, 4))]
            for sample in samples:
                clients = [o['clients'][0] for o in sample['observations']]
                clients[1][key] = copy.deepcopy(clients[0][key])
            self.assertFalse(simultaneous_progress(samples), key)
        samples = [self.sample(0), self.sample(2, (4, 4))]
        for sample in samples:
            sample['observations'][0]['clients'] *= 2
        self.assertFalse(simultaneous_progress(samples))

    def test_case_ids_match_even_when_observation_order_changes(self):
        samples = [self.sample(0), self.sample(2, (4, 4))]
        samples[1]['observations'].reverse()
        self.assertTrue(simultaneous_progress(samples))
        samples[1]['observations'][0]['case_id'] = 'other'
        self.assertFalse(simultaneous_progress(samples))

    def worker_fixture(self):
        output = Path('/tmp/operational-player')
        case = {'worker_id': 20, 'seed': 43220}
        worker = {'valid': True, 'workerId': 20, 'randomSeed': 43220, 'scene': 'Assets/Scenes/Roboboat Course.unity',
            'runtimeProfile': 'train-gpu', 'imageSignatures': True, 'screenWidth': 640, 'screenHeight': 360,
            'enabledCameras': 1, 'enabledSensorCameras': 1, 'enabledSpectatorCameras': 0,
            'enabledWaterDriverCameras': 0, 'depthCamera': {'acquisitionCount': 100, 'width': 1280, 'height': 720},
            'timeScale': 1, 'validationStream': str(output/'validation.jsonl'), 'validationSamplesCaptured': 20,
            'acceptedActions': 0, 'rejectedActions': 0}
        for key in ('loggedErrors', 'loggedExceptions', 'invalidWaterSearches', 'staleObservations', 'failedObservations', 'depthBufferValidationMismatches'):
            worker[key] = 0
        frames = {'retained_frame_rows': 20, 'metadata': {'fixedDeltaTime': .02, 'appliedMaximumDeltaTime': .04}, 'issues': []}
        pose = {'initialization_readback_pass': True}
        render = {'status': 'COMPLETE_DEVELOPMENT_ONLY', 'placement_verified': True,
                  'owned_output_removed': True, 'cleanup_errors': []}
        return case, worker, frames, pose, render, output, 0, False

    def test_instrumented_sensor_benchmark_requires_all_original_gates(self):
        args = self.worker_fixture()
        self.assertTrue(all(assess_worker(*args).values()))
        for key, value in (('randomSeed', 0), ('valid', False), ('failedObservations', 1),
                           ('loggedErrors', 1), ('imageSignatures', False), ('acceptedActions', 1)):
            changed = copy.deepcopy(args); changed[1][key] = value
            self.assertFalse(all(assess_worker(*changed).values()), key)
        for width in (640, 1279):
            changed = copy.deepcopy(args); changed[1]['depthCamera']['width'] = width
            self.assertFalse(all(assess_worker(*changed).values()))
        for index, key, value in ((2, 'issues', ['clock_changed']), (3, 'initialization_readback_pass', False),
                                  (4, 'cleanup_errors', ['failed']), (4, 'owned_output_removed', False)):
            changed = copy.deepcopy(args); changed[index][key] = value
            self.assertFalse(all(assess_worker(*changed).values()))
        changed = list(copy.deepcopy(args)); changed[-1] = True
        self.assertFalse(all(assess_worker(*changed).values()))


if __name__ == '__main__': unittest.main()
