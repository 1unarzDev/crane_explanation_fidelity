#!/usr/bin/env python3
"""Publish the fixed stopping-threshold development recordings without outcome selection."""
import argparse
import hashlib
import json
from pathlib import Path
from build_roboboat_terminal_batch import ROOT,DOC,build,runtime_config,save,digest
from roboboat_temporal_certificate import certificate
from roboboat_temporal_renderer_v3 import render_v3


def checked_configuration(base,readback,row):
    selected=readback['nodes']['/controller_server']['goal_checker_plugins']
    if len(selected)!=1:raise ValueError('ambiguous selected runtime checker')
    node=readback['nodes']['/controller_server'];name=selected[0]
    if node[name+'.plugin']!='nav2_controller::StoppedGoalChecker':
        raise ValueError('runtime checker identity differs')
    expected={'xy_goal_tolerance':row['internal_xy_tolerance_m'],
        'trans_stopped_velocity':row['internal_trans_stopped_velocity_mps'],
        'rot_stopped_velocity':row['internal_rot_stopped_velocity_radps']}
    for key,value in expected.items():
        if abs(float(node[name+'.'+key])-value)>1e-12:
            raise ValueError('runtime stopping override differs: '+key)
    return runtime_config(base,readback,row['internal_xy_tolerance_m'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture-root',type=Path,required=True)
    parser.add_argument('--output-root',type=Path,required=True);args=parser.parse_args()
    registry_path=DOC/'settling_pilot_registry_v1.json';registry=json.loads(registry_path.read_text())
    if registry['confirmation']['authorized'] or registry['configuration_n']!=2:
        raise ValueError('bounded development gate closed')
    binding=registry['nav2_configuration'];base=(ROOT/binding['path']).read_bytes()
    if digest(ROOT/binding['path'])!=binding['sha256']:
        raise ValueError('registered stopping profile changed')
    if digest(DOC/'task_contract_v1.json')!=registry['contract_sha256']:
        raise ValueError('independent physical requirements changed')
    for row in registry['rows']:
        source=args.capture_root/row['id'];record=json.loads((source/'capture-attempt.json').read_text())
        if record['status']!='complete' or record['registry_sha256']!=digest(registry_path):
            raise ValueError('incomplete/invalid capture or registry identity mismatch')
        if record['config_sha256']!=binding['sha256']:
            raise ValueError('captured launch profile mismatch')
        runtime_path=source/'runtime-parameters.json';readback=json.loads(runtime_path.read_text())
        config=checked_configuration(base,readback,row)
        output=args.output_root/row['id']
        opaque='opaque-dev-'+hashlib.sha256(row['id'].encode()).hexdigest()[:16]
        build(source/'fixture-summary.json',config,output,opaque,
              'FRESH_FIXED_INTERNAL_STOPPING_DEVELOPMENT',runtime_path)
        # Keep the original producer's v1 output distinct. Never overwrite it
        # with the candidate renderer or mount either output to the agent.
        for level in range(3):
            packet=json.loads((output/'method_packets'/f'L{level}.json').read_text())
            cert=certificate(packet)
            save(output/'candidate_v3_outputs'/f'L{level}.json',{'certificate':cert,'answer':render_v3(packet,cert),
                'renderer_sha256':digest(ROOT/'analysis/roboboat_temporal_renderer_v3.py')})
        save(output/'evaluator/settling-provenance.json',{'registry_sha256':digest(registry_path),
            'capture_record_sha256':digest(source/'capture-attempt.json'),'existing_approach_cluster':row['cluster_id'],
            'new_independent_cluster_n':0,'confirmation_n':0,'replication_n':0,
            'nominal_success_required_for_admission':False})
        print('published',row['id'],flush=True)


if __name__=='__main__':main()
