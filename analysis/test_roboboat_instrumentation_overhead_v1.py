import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock
import run_roboboat_instrumentation_overhead_v1 as assay

class AssayTests(unittest.TestCase):
    def test_launch_toggle_preserves_other_inputs_and_never_exports(self):
        registry_path = assay.ROOT/'docs/roboboat_terminal_evidence/populations/development-42005/registry.json'
        registry = json.loads(registry_path.read_text())
        physical = next(r for r in registry['rows'] if r['id']=='boat-geom-42005-00001-v1')
        launches = []
        with tempfile.TemporaryDirectory() as temp:
            for toggle in (True, False):
                row = copy.deepcopy(physical)
                row['id'] = 'boat-reliability-test-'+str(toggle)
                bundle = {'executable':{'path':'/fixed/mock/player'},'expected_class':'mock'}
                process = Mock(); process.wait.return_value = 0
                with patch.object(assay,'verify_player'), patch.object(assay,'prepare_bundle',return_value=bundle), patch.object(assay,'verify_bundle'), patch.object(assay,'default_affinity',return_value=[0]), patch.object(assay.subprocess,'Popen',return_value=process) as launch:
                    result = assay.capture(row,registry,registry_path,Path(temp),194,11484,.04,trace_enabled=toggle)
                    launches.append(launch.call_args.kwargs['env'])
                self.assertEqual(result['status'],'TECHNICAL_FAILURE') # mock emits no measurements
                self.assertFalse(result['scientific_admission_authorized'])
                self.assertEqual(result['new_independent_n'],0)
                self.assertEqual(result['row']['seed'],physical['seed'])
                self.assertFalse(list((Path(temp)/row['id']).glob('*explanation*')))
                again = assay.capture(row,registry,registry_path,Path(temp),194,11484,.04,trace_enabled=toggle)
                self.assertEqual(again,result) # no reissue
        for env,toggle in zip(launches,(True,False)):
            self.assertEqual('--crane-action-timing-audit' in env['CRANE_NAV2_UNITY_EXTRA_ARGS'],toggle)
            self.assertIn('--crane-frame-timing-audit',env['CRANE_NAV2_UNITY_EXTRA_ARGS'])
            self.assertIn('--crane-maximum-delta-time 0.04',env['CRANE_NAV2_UNITY_EXTRA_ARGS'])
        for key in ('CRANE_SEED_BASE','CRANE_NAV2_PARAMS','CRANE_NAV2_PATH_FILE','CRANE_NAV2_GOAL_X','CRANE_NAV2_GOAL_Y','CRANE_NAV2_GOAL_YAW','CRANE_NAV2_CONTROLLER_EXTRA_ARGS'):
            self.assertEqual(launches[0].get(key),launches[1].get(key))

    def test_declaration_rejects_reuse_nonbool_and_one_condition(self):
        d={'schema':'roboboat-tracing-overhead-declaration/v1','new_independent_n':0,
           'schedule':[{'operational_run_id':'boat-reliability-a','trace_enabled':True},{'operational_run_id':'boat-reliability-b','trace_enabled':False}],
           'registry':'/mock/registry','dependencies':[{'path':'/mock/registry','sha256':'x'},{'path':str(Path(assay.__file__).resolve()),'sha256':'x'}]}
        with patch.object(assay,'digest',return_value='x'):
            assay.validate_declaration(d)
            for change in ('reuse','nonbool','single','study_id','changed_hash'):
                bad=copy.deepcopy(d)
                if change=='reuse':bad['schedule'][1]['operational_run_id']='boat-reliability-a'
                if change=='nonbool':bad['schedule'][0]['trace_enabled']=1
                if change=='single':bad['schedule'][1]['trace_enabled']=True
                if change=='study_id':bad['schedule'][0]['operational_run_id']='boat-geom-42005-00001-v1'
                if change=='changed_hash':bad['dependencies'][0]['sha256']='wrong'
                with self.subTest(change=change),self.assertRaises(ValueError):assay.validate_declaration(bad)

    def test_completed_reliability_capture_is_terminal(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); registry=root/'registry.json';registry.write_text('{}')
            out=root/'boat-reliability-terminal';out.mkdir()
            terminal={'status':'OVERHEAD_CAPTURE_COMPLETE','registry_sha256':assay.digest(registry)}
            (out/'capture-attempt.json').write_text(json.dumps(terminal))
            with patch.object(assay.subprocess,'Popen',side_effect=AssertionError('must not launch')):
                self.assertEqual(assay.capture({'id':out.name},{},registry,root,194,11484),terminal)

if __name__=='__main__':unittest.main()
