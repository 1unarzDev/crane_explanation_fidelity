import json
from pathlib import Path
import tempfile
import unittest
from roboboat_after_collection_v29 import predecessor_ready
from generate_roboboat_population_v1 import digest
from run_roboboat_dual_clock_navigation_operational_v29 import capture_clock_checks
from roboboat_post_result_clock_v28 import capture_gate

class SuccessorSafetyTests(unittest.TestCase):
    def test_wait_on_exact_identity_and_refuse_dead_or_reused_pid(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=root/'d.json';p.write_text(json.dumps({'rows':['a','b'],'output_root':str(root)}))
            r={'declaration':{'path':str(p),'sha256':digest(p)},'process':{'pid':123,'start':456}}
            self.assertFalse(predecessor_ready(r,identity=lambda pid:{'pid':123,'start':456}))
            for actual in (None,{'pid':123,'start':457}):
                with self.assertRaises(RuntimeError):predecessor_ready(r,identity=lambda pid:actual)
            t={'status':'TRACE_QUALIFIED_DEVELOPMENT_BATCH_FINISHED','declaration_sha256':digest(p),'physical_attempts':2,
                'results':[{'row':{'id':id},'status':status} for id,status in (('a','VALID_TRACE_QUALIFIED_DEVELOPMENT'),('b','TECHNICAL_FAILURE'))]}
            (root/'terminal.json').write_text(json.dumps(t))
            self.assertTrue(predecessor_ready(r,identity=lambda pid:None))
            t['results'][1]['row']['id']='a';(root/'terminal.json').write_text(json.dumps(t))
            with self.assertRaises(ValueError):predecessor_ready(r,identity=lambda pid:None)

    def test_runtime_clock_metadata_is_reconstructed_not_trusted(self):
        rows=[{'phase':'post_result','simSeconds':0.},{'phase':'post_result','simSeconds':8.1}]
        f={'trajectory':rows,'postResultCaptureClockV28':capture_gate(rows,8.2),'postResultSecondsObserved':8.2}
        self.assertTrue(all(capture_clock_checks(f).values()))
        f['postResultCaptureClockV28']['observed_sim_span_seconds']=9.
        self.assertFalse(all(capture_clock_checks(f).values()))
        f['postResultCaptureClockV28']=capture_gate(rows,7.)
        self.assertFalse(all(capture_clock_checks(f).values()))
        capped=[{'phase':'post_result','simSeconds':0.},{'phase':'post_result','simSeconds':.3}]
        f={'trajectory':capped,'postResultCaptureClockV28':capture_gate(capped,120.),'postResultSecondsObserved':120.}
        self.assertTrue(all(capture_clock_checks(f).values()))
        self.assertFalse(f['postResultCaptureClockV28']['simulation_window_complete'])

if __name__=='__main__':unittest.main()
