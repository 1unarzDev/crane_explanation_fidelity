#!/usr/bin/env python3
"""Repair ladder identity only; retain physical recordings and original failed exports."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
from build_roboboat_terminal_batch import runtime_config, save
from generate_roboboat_population_v1 import ROOT, digest
from roboboat_temporal_certificate import build_ladder
from roboboat_temporal_certificate_v2 import upgrade_development_packet, certificate, render, audit_ladder
from reference_roboboat_temporal_v2 import calculate
from run_roboboat_population_development_v1 import technical_checks, bound


def project(row, capture, output, config):
    contract = json.loads(bound(row['task_contract']).read_text())
    effective = runtime_config(config.read_bytes(), json.loads((capture/'runtime-parameters.json').read_text()), row['internal_xy_tolerance_m'])
    output.mkdir(parents=True, exist_ok=False)
    (output/'effective-configuration.yaml').write_bytes(effective)
    legacy = copy.deepcopy(contract)
    legacy.update(schema='roboboat-terminal-task/v1', id=contract['id']+'-legacy-build', contact_required=True)
    legacy.pop('contact_policy')
    opaque = 'opaque-geometry-v2-' + hashlib.sha256(row['id'].encode()).hexdigest()[:20]
    packets = [upgrade_development_packet(packet, opaque, contract) for packet in
               build_ladder(json.loads((capture/'fixture-summary.json').read_text()), effective, legacy, opaque+'-raw')]
    # Audit before publishing any packet. One ladder identity is shared by all
    # evidence levels; level lives in the declared external question identity.
    audit = audit_ladder(packets)
    outcomes = []
    for level, packet in enumerate(packets):
        cert = certificate(packet); reference = calculate(packet)
        if cert['sampled_task_support'] != reference['sampled_task_support']:
            raise ValueError('independent outcome reference mismatch')
        if len(cert['measurements']) != len(reference['position_errors']):
            raise ValueError('independent measurement count mismatch')
        for measurement, error in zip(cert['measurements'], reference['position_errors']):
            if abs(measurement['position_error_m']-error) > 1e-12:
                raise ValueError('independent position arithmetic mismatch')
        save(output/'method_packets'/f'L{level}.json',packet)
        save(output/'candidate_outputs'/f'L{level}.json',{'answer':render(packet,cert),'certificate':cert,'model_calls':0})
        save(output/'evaluator'/f'L{level}.json',reference)
        outcomes.append(cert['sampled_task_support'])
    save(output/'evaluator/ladder-audit.json',audit)
    return outcomes


def publish_terminal(row, registry_path, capture, config):
    original = capture/'capture-attempt.json'
    terminal = capture/'capture-export-terminal-v2.json'
    if terminal.exists():
        value = json.loads(terminal.read_text())
        if value['original_capture_terminal']['sha256'] != digest(original): raise ValueError('original capture changed')
        return value
    old = json.loads(original.read_text())
    if old['row'] != row or old['registry_sha256'] != digest(registry_path): raise ValueError('capture identity differs')
    summary = json.loads((capture/'navigation-reset-summary.json').read_text())
    worker = json.loads((capture/'worker-0/result.json').read_text())
    fixture = json.loads((capture/'fixture-summary.json').read_text())
    checks = technical_checks(summary,worker,fixture)
    if not all(checks.values()) or old['return_code'] not in (0,1): raise ValueError('physical recording is technically invalid; cannot salvage')
    if old['return_code']==1 and fixture['status']==summary['expectedNavigationStatus']: raise ValueError('non-outcome launcher failure')
    if old['status']=='TECHNICAL_FAILURE' and old.get('error')!='ladder is not removal-only nested': raise ValueError('unsupported repair; original failure retained')
    output = capture/'exports-v2'
    outcomes = project(row,capture,output,config) if not output.exists() else [json.loads((output/'candidate_outputs'/f'L{i}.json').read_text())['certificate']['sampled_task_support'] for i in range(3)]
    # Validate complete output even when projection was created by successor collector.
    packets = [json.loads((output/'method_packets'/f'L{i}.json').read_text()) for i in range(3)]
    audit_ladder(packets)
    value = {'status':'VALID_DEVELOPMENT','row':row,'registry_sha256':digest(registry_path),
             'export_directory':'exports-v2','level_outcomes':outcomes,'recording_technical_valid':True,
             'original_capture_terminal':{'path':str(original),'sha256':digest(original)},
             'exporter':{'path':str(Path(__file__).resolve()),'sha256':digest(Path(__file__))},
             'repair':'Shared opaque ladder identity; measurements, thresholds, task, method code and raw recording unchanged. Original failure retained.',
             'raw_sources':[{'path':str(capture/name),'sha256':digest(capture/name)} for name in ('fixture-summary.json','runtime-parameters.json','navigation-reset-summary.json','worker-0/result.json')],
             'new_physical_runs':0,'independent_n_added_by_repair':0,'confirmation_n':0}
    save(terminal,value)
    return value


def main():
    p=argparse.ArgumentParser();p.add_argument('--registry',required=True,type=Path);p.add_argument('--capture-root',required=True,type=Path);a=p.parse_args()
    registry=json.loads(a.registry.read_text());config=bound(registry['nav2_configuration'])
    for row in registry['rows']:
        capture=a.capture_root/row['id']
        if (capture/'capture-attempt.json').exists():
            print(row['id'],publish_terminal(row,a.registry,capture,config)['status'])

if __name__=='__main__':main()
