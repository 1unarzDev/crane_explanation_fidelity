import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import run_roboboat_clock_repair_operational_v11 as collector

class OperationalIdentityTests(unittest.TestCase):
    def setup_declaration(self, root):
        original=root/'original.json'; registry=root/'registry.json'; build=root/'build.json'
        original.write_text(json.dumps({'rows':[{'id':'old','seed':1,'goal':{'x':2}}]}))
        rows=[{'id':f'replay-{i}','seed':1,'goal':{'x':2}} for i in range(4)]
        registry.write_text(json.dumps({'status':'NONSTUDY_OPERATIONAL_REPLAYS_ZERO_INDEPENDENT_N','rows':rows}));build.write_text('{}')
        required=[Path(collector.__file__).resolve(),registry,original,build]
        required += [collector.ROOT/'analysis'/name for name in ('export_roboboat_trace_qualified_v3.py','audit_roboboat_launcher_terminal_v1.py','export_roboboat_population_v2.py','roboboat_trace_qualified_validity_v1.py','audit_roboboat_trace_semantics_v1.py','audit_roboboat_action_trace_v1.py','audit_roboboat_frame_timing_v1.py','roboboat_owned_player_bundle_v1.py','roboboat_hidden_render_v3.py')]
        return {'schema':'roboboat-clock-repair-operational-declaration/v1','independent_n_added':0,'confirmation_n':0,'replication_n':0,'registry':str(registry),'original_registry':str(original),'rows':[r['id'] for r in rows],'origin_rows':{r['id']:'old' for r in rows},'domain':196,'port':11486,'maximum_delta_time':.04,'dependencies':[{'path':str(p),'sha256':collector.digest(p)} for p in required]},build

    def test_same_geometry_replays_are_allowed_only_as_zero_n(self):
        with tempfile.TemporaryDirectory() as tmp:
            d,build=self.setup_declaration(Path(tmp))
            with patch.object(collector,'BUILD_IDENTITY',build),patch.object(collector,'verify_player'):
                self.assertEqual(len(collector.validate_declaration(d,Path(tmp)/'declaration.json')[2]),4)
                for key in ('independent_n_added','confirmation_n','replication_n'):
                    changed=copy.deepcopy(d);changed[key]=1
                    with self.assertRaises(ValueError):collector.validate_declaration(changed,Path(tmp)/'declaration.json')

    def test_changed_physical_configuration_cannot_be_called_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            d,build=self.setup_declaration(Path(tmp));p=Path(d['registry']);r=json.loads(p.read_text());r['rows'][0]['goal']['x']=3;p.write_text(json.dumps(r))
            for item in d['dependencies']:
                if item['path']==str(p):item['sha256']=collector.digest(p)
            with patch.object(collector,'BUILD_IDENTITY',build),patch.object(collector,'verify_player'):
                with self.assertRaisesRegex(ValueError,'physical configuration'):collector.validate_declaration(d,Path(tmp)/'declaration.json')

    def test_changed_bound_input_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            d,build=self.setup_declaration(Path(tmp));build.write_text('{"changed":true}')
            with patch.object(collector,'BUILD_IDENTITY',build),patch.object(collector,'verify_player'):
                with self.assertRaisesRegex(ValueError,'declared input changed'):collector.validate_declaration(d,Path(tmp)/'declaration.json')

if __name__=='__main__':unittest.main()
