import copy
import json
from pathlib import Path
from export_roboboat_population_v2 import project, ROOT
from roboboat_temporal_certificate_v2 import audit_ladder


def test_projection_preserves_nested_identity_and_independent_arithmetic(tmp_path):
    registry = json.loads((ROOT/'docs/roboboat_terminal_evidence/settling_pilot_registry_v1.json').read_text())
    config = ROOT/registry['nav2_configuration']['path']
    capture = ROOT/'artifacts/roboboat-terminal-settling-v1/captures/boat-terminal-settling-001'
    contract = ROOT/'docs/roboboat_terminal_evidence/task_contract_v2.json'
    import hashlib
    row = {'id':'constructed-projection-test', 'internal_xy_tolerance_m':0.2,
           'task_contract':{'path':str(contract),'sha256':hashlib.sha256(contract.read_bytes()).hexdigest()}}
    outcomes = project(row, capture, tmp_path/'projection', config)
    packets = [json.loads((tmp_path/'projection/method_packets'/f'L{i}.json').read_text()) for i in range(3)]
    assert len({p['packet_id'] for p in packets}) == 1
    assert audit_ladder(packets)['status'] == 'PASS'
    assert all('post_result' not in p for p in packets[:2])
    assert 'return_observation' not in packets[0]
    assert len(packets[2]['post_result']) > 250
    assert outcomes == ['unknown','unknown','unknown']
