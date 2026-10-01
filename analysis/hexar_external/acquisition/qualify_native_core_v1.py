"""Actual fixed-six DEVELOPMENT native-core qualification, no semantic outputs."""
import argparse
import json
from pathlib import Path
import subprocess

from .technical_batch_candidate import ROOT,digest,verify_capture,canonical_review_episodes
from .project_raw_episode_v1 import review as project
from ..confirmatory_v1.journal import exclusive_json

BASE=ROOT/'manifests/hexar_external/acquisition'
DEST=BASE/'development_native_core_v18'
PRIOR=BASE/'development_bound_runtime_v17_v3'


def execute():
    DEST.mkdir(exist_ok=False)
    run_path=BASE/'development_episode_plan_v17_qualification_run.json'
    run=json.loads(run_path.read_text());receipts=run['episodes']
    report=json.loads((PRIOR/'report.json').read_text())
    native=json.loads((PRIOR/'native_review.json').read_text())
    interface=json.loads((PRIOR/'interface_review.json').read_text())
    if (report['status']!='BOUND_PROVENANCE_RUNTIME_SCOPE_QUALIFIED_NOT_FINAL_ADMISSION'
            or len(receipts)!=6 or len(native)!=6 or len(interface['episodes'])!=6
            or run['phase']!='development_only' or run['acquisition_phase']!='development_adapter_qualification'
            or run['status']!='DEVELOPMENT_RUNS_RECORDED_UNQUALIFIED'):
        raise ValueError('complete already exposed six-family development source required')
    for name,expected in report['evidence_hashes'].items():
        if digest(PRIOR/name)!=expected:raise ValueError('prior qualification evidence changed')
    sources=[Path(__file__),Path(__file__).with_name('native_review_core_v1.py'),
             Path(__file__).with_name('project_raw_episode_v1.py'),
             ROOT/'docs/hexar_external/confirmatory_v1/NATIVE_CORE_QUALIFICATION.md',run_path,PRIOR/'report.json']
    source_hashes={str(p.relative_to(ROOT)):digest(p) for p in sources}
    for receipt in receipts:verify_capture(ROOT,receipt,run['image_id'])
    declaration=dict(schema='hexar-native-core-development-declaration/v1',phase='development_only',
        source_hashes=source_hashes,exposed_episodes=[r['episode_id'] for r in receipts],native_reader_calls=6,
        timeout_seconds=180,retries=0,robot_episode_replays=0,semantic_calls=0,confirmatory_N=0,alpha_consumed=0)
    exclusive_json(DEST/'declaration.json',declaration)
    rows=[];all_packets=[]
    for receipt in receipts:
        uid=receipt['episode_id'];folder=DEST/uid;folder.mkdir()
        bank=BASE/'source_banks'/receipt['execution_source_bank_sha256']
        command=['docker','run','--rm','--network','none','--memory','5g',
            '-v',str(BASE)+':/input:ro','-v',str(bank)+':/bank:ro',
            '-v',str(Path(__file__).with_name('native_review_core_v1.py'))+':/review.py:ro',
            '--entrypoint','bash',run['image_id'],'-lc',
            'source /ws/install/setup.bash; python3 /review.py --folder "$1" --bank /bank --receipt "$2" --phase development_adapter_qualification --binding "$3"',
            'native-core','/input/'+uid,'/input/'+uid+'/provenance.json',run['acquisition_binding_sha256']]
        exclusive_json(folder/'claim.json',dict(command=command,launch_limit=1,development_only=True))
        row=dict(episode_id=uid,passed=False,error=None)
        try:
            result=subprocess.run(command,capture_output=True,timeout=180)
            (folder/'stdout.bin').write_bytes(result.stdout);(folder/'stderr.bin').write_bytes(result.stderr)
            if result.returncode!=0:raise ValueError('native transport return code '+str(result.returncode))
            value=json.loads(result.stdout)
            expected_native=next(r['review'] for r in native if r['episode_id']==uid)
            if (value['events']!=json.loads((BASE/uid/'events_development.json').read_text())
                    or value['motion']!=json.loads((BASE/uid/'motion_events_v3.json').read_text())
                    or value['native_review']!=expected_native or value['method_or_judge_calls']!=0
                    or value['original_capture_mutated'] is not False):
                raise ValueError('original extraction/native result differs')
            projected=project(BASE/uid,uid,value['events'],value['motion'])
            expected_episode=next(r for r in interface['episodes'] if r['development_id']==uid)
            expected_packets=[r for r in interface['packets'] if r['development_id']==uid]
            if (canonical_review_episodes(ROOT,[projected['episode']])!=canonical_review_episodes(ROOT,[expected_episode])
                    or projected['packets']!=expected_packets):
                raise ValueError('original query/reference/interface differs')
            verify_capture(ROOT,receipt,run['image_id'])
            exclusive_json(folder/'projection.json',projected)
            all_packets.extend(projected['packets']);row['passed']=True
        except Exception as exc:row['error']=type(exc).__name__+': '+str(exc)
        exclusive_json(folder/'outcome.json',row);rows.append(row)
    if any(digest(ROOT/name)!=sha for name,sha in source_hashes.items()):
        raise ValueError('declared qualification sources changed during run')
    final=dict(schema='hexar-native-core-development-qualification/v1',phase='development_only',
        status='READ_ONLY_PHASE_AWARE_NATIVE_CORE_QUALIFIED_NOT_PRODUCTION_ADMISSION'
            if all(r['passed'] for r in rows) else 'FAILED_QUALIFICATION_RETAINED',rows=rows,
        declaration_sha256=digest(DEST/'declaration.json'),reader_calls=6,packet_projections=len(all_packets),
        source_hashes=source_hashes,robot_episode_replays=0,method_or_judge_calls=0,confirmatory_N=0,alpha_consumed=0,
        confirmation_authorized=False)
    exclusive_json(DEST/'report.json',final)
    return final


if __name__=='__main__':print(execute()['status'])
