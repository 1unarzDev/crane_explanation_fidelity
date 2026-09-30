#!/usr/bin/env python3
"""Build isolated ladder batches with evaluator provenance separated from method packets."""
import argparse,hashlib,json,subprocess,time
from pathlib import Path
from roboboat_temporal_certificate import build_ladder,certificate,render,audit_ladder
from reference_roboboat_temporal import calculate
ROOT=Path(__file__).resolve().parents[1];DOC=ROOT/'docs/roboboat_terminal_evidence'

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path, value):
    b=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
    if path.exists():
        if path.read_bytes()!=b:raise ValueError('immutable output differs')
        return
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp');tmp.write_bytes(b);tmp.replace(path)

def build(summary_path, config_bytes, output, opaque_id, status):
    contract=json.loads((DOC/'task_contract_v1.json').read_text())
    summary=json.loads(summary_path.read_text());packets=build_ladder(summary,config_bytes,contract,opaque_id)
    results=[]
    for level,packet in enumerate(packets):
        production=certificate(packet);reference=calculate(packet)
        assert production['sampled_task_support']==reference['sampled_task_support']
        if reference['position_violation'] is not None:
            assert production['witnesses']['position']['time_s']==reference['position_violation']
        assert len(production['measurements'])==len(reference['position_errors'])
        for row,err in zip(production['measurements'],reference['position_errors']):
            assert abs(row['position_error_m']-err)<1e-12
        save(output/'method_packets'/f'L{level}.json',packet)
        save(output/'evaluator'/f'L{level}-reference.json',reference)
        save(output/'contract_outputs'/f'L{level}.json',{'certificate':production,'answer':render(packet,production)})
        results.append({'level':level,'outcome':production['sampled_task_support'],
                        'position':production['component_support']['position'],
                        'witness':production['witnesses'].get('position'),
                        'return':production['return_observation'],
                        'coverage':production['coverage'],
                        'packet_sha256':digest(output/'method_packets'/f'L{level}.json')})
    audit=audit_ladder(packets)
    # Source hashes/paths never go into the method workspace.
    save(output/'evaluator/provenance.json',{'source_path':str(summary_path.resolve()),'sha256':digest(summary_path),
      'study_status':status,'opaque_id':opaque_id,'certificate_tool_sha256':digest(ROOT/'analysis/roboboat_temporal_certificate.py'),
      'reference_tool_sha256':digest(ROOT/'analysis/reference_roboboat_temporal.py'),'leakage_audit':audit})
    save(output/'summary.json',{'status':status,'opaque_id':opaque_id,'levels':results,'independent_reference_match':True})
    return results


def main():
    p=argparse.ArgumentParser();p.add_argument('--historical',action='store_true');p.add_argument('--capture-root',type=Path);p.add_argument('--output-root',required=True,type=Path);a=p.parse_args()
    if a.historical:
        summary=Path('/home/lunarz/worktrees/roboboat-docking/packages/crane_ml/PerformanceResults/roboboat-gate5-known-dock-1/fixture-summary.json')
        assert digest(summary)=='6bcc1c1f7d926a45b6d3ec2f9b0f06cfe8770d067d57ed2a92a45ebbd8c2223a'
        config=subprocess.check_output(['git','-C',str(ROOT/'packages/crane_ml'),'show','4ae5124c12c39af93ee5b256e33778aec490ecd3:Tools/Performance/nav2_controller_fixture.yaml'])
        result=build(summary,config,a.output_root/'historical-replay','opaque-dev-001','INSPECTED_HISTORICAL_DEVELOPMENT_REPLAY')
        print(json.dumps(result,indent=2))
    else:
        registry=json.loads((DOC/'pilot_registry_v1.json').read_text())
        for index,row in enumerate(registry['rows']):
            source=a.capture_root/row['id'];record=source/'capture-attempt.json'
            if not record.exists() or json.loads(record.read_text())['status']!='complete':continue
            b=(DOC/'configs/validated_boat_nav2.yaml').read_bytes()
            # Exact effective per-run values; overrides are also retained in the capture ledger.
            b=b.replace(b'xy_goal_tolerance: 0.20',f"xy_goal_tolerance: {row['internal_xy_tolerance_m']:.2f}".encode())
            result=build(source/'fixture-summary.json',b,a.output_root/row['id'],f'opaque-fresh-{index+1:03d}','FRESH_EXPLORATORY_PILOT')
            print(row['id'],[r['outcome'] for r in result])
if __name__=='__main__':main()
