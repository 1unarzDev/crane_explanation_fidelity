import copy
import unittest
from roboboat_parallel_navigation_contract_v26 import own_stream_checks, simultaneous_navigation_progress
from test_roboboat_parallel_players_v20 import ConcurrentPlayerTests

class NavigationIsolationTests(unittest.TestCase):
    def test_stream_identity_transport_and_route(self):
        row={'id':'own','action_mode':'follow-path','path_file':{'path':'packages/crane_ml/Tools/Performance/generated_populations/a.json','sha256':'abc'}}
        fixture={'run_id':'own','episode_id':'own-worker-0','actionMode':'follow-path','suppliedPathFile':'/workspace/crane_sim/Tools/Performance/generated_populations/a.json','suppliedPathFileSha256':'abc'}
        summary={'transport':{'rosDomainId':202,'rosTcpPort':11492}}
        self.assertTrue(all(own_stream_checks(row,fixture,summary,202,11492).values()))
        for key in fixture:
            changed=copy.deepcopy(fixture);changed[key]='foreign'
            self.assertFalse(all(own_stream_checks(row,changed,summary,202,11492).values()),key)
        for key in summary['transport']:
            changed=copy.deepcopy(summary);changed['transport'][key]=-1
            self.assertFalse(all(own_stream_checks(row,fixture,changed,202,11492).values()),key)

    def test_goal_and_missing_or_foreign_path(self):
        row={'id':'own','action_mode':'navigate-to-pose','goal':{'x':1.,'y':2.,'yaw':.3}}
        fixture={'run_id':'own','episode_id':'own-worker-0','actionMode':'navigate-to-pose','goal':{'frame_id':'odom','position':{'x':1.,'y':2.},'yaw':.3}}
        summary={'transport':{'rosDomainId':203,'rosTcpPort':11493}}
        self.assertTrue(all(own_stream_checks(row,fixture,summary,203,11493).values()))
        for value in (None,float('nan'),99):
            changed=copy.deepcopy(fixture);changed['goal']['position']['x']=value
            self.assertFalse(all(own_stream_checks(row,changed,summary,203,11493).values()))
        changed=copy.deepcopy(fixture);changed['suppliedPathFile']='foreign'
        self.assertFalse(all(own_stream_checks(row,changed,summary,203,11493).values()))

    def test_observed_concurrent_commands_required(self):
        maker=ConcurrentPlayerTests();samples=[maker.sample(0),maker.sample(2,(4,4))]
        self.assertFalse(simultaneous_navigation_progress(samples))
        for sample in samples:
            for o in sample['observations']:o['action_records']=o['validation_records']
        self.assertTrue(simultaneous_navigation_progress(samples))
        samples[1]['observations'][1]['action_records']=2
        self.assertFalse(simultaneous_navigation_progress(samples))

if __name__=='__main__':unittest.main()
