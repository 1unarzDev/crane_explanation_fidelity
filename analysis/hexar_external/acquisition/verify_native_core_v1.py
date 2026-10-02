"""Read-only reproduction of retained native qualification; no ROS dispatch."""
import argparse
import json
from pathlib import Path

from .technical_batch_candidate import ROOT,digest,verify_capture,canonical_review_episodes
from .project_raw_episode_v1 import review as project
from ..confirmatory_v1.journal import exclusive_json

BASE=Path('manifests/hexar_external/acquisition')


def verify(root=ROOT):
    root=Path(root);archive=root/BASE/'development_native_core_v18'
    prior=root/BASE/'development_bound_runtime_v17_v3'
    report=json.loads((archive/'report.json').read_text())
    declaration=json.loads((archive/'declaration.json').read_text())
    if digest(archive/'declaration.json')!=report['declaration_sha256']:
        raise ValueError('native qualification declaration changed')
    for name,sha in report['source_hashes'].items():
        if digest(root/name)!=sha:raise ValueError('native qualification source changed: '+name)
    run=json.loads((root/BASE/'development_episode_plan_v17_qualification_run.json').read_text())
    prior_report=json.loads((prior/'report.json').read_text())
    for name,sha in prior_report['evidence_hashes'].items():
        if digest(prior/name)!=sha:raise ValueError('prior qualification evidence changed')
    native=json.loads((prior/'native_review.json').read_text())
    interface=json.loads((prior/'interface_review.json').read_text())
    receipts=run['episodes']
    if (len(receipts)!=6 or len(report['rows'])!=6 or report['reader_calls']!=6
            or report['packet_projections']!=54 or report['robot_episode_replays']!=0
            or report['method_or_judge_calls']!=0 or report['confirmatory_N']!=0
            or report['confirmation_authorized'] is not False
            or declaration['exposed_episodes']!=[r['episode_id'] for r in receipts]):
        raise ValueError('native qualification scope differs')
    projections=0
    for receipt,row in zip(receipts,report['rows']):
        uid=receipt['episode_id'];folder=archive/uid
        if row!=json.loads((folder/'outcome.json').read_text()) or row!=dict(episode_id=uid,passed=True,error=None):
            raise ValueError('native qualification outcome differs')
        claim=json.loads((folder/'claim.json').read_text())
        if claim['launch_limit']!=1 or claim['development_only'] is not True:
            raise ValueError('native reader dispatch scope differs')
        verify_capture(root,receipt,run['image_id'])
        value=json.loads((folder/'stdout.bin').read_bytes())
        expected_native=next(r['review'] for r in native if r['episode_id']==uid)
        if (value['events']!=json.loads((root/BASE/uid/'events_development.json').read_text())
                or value['motion']!=json.loads((root/BASE/uid/'motion_events_v3.json').read_text())
                or value['native_review']!=expected_native or value['method_or_judge_calls']!=0
                or value['original_capture_mutated'] is not False):
            raise ValueError('retained native extraction differs')
        projected=project(root/BASE/uid,uid,value['events'],value['motion'])
        expected_episode=next(r for r in interface['episodes'] if r['development_id']==uid)
        expected_packets=[r for r in interface['packets'] if r['development_id']==uid]
        if (projected!=json.loads((folder/'projection.json').read_text())
                or projected['packets']!=expected_packets
                or canonical_review_episodes(root,[projected['episode']])!=canonical_review_episodes(root,[expected_episode])):
            raise ValueError('retained native packet/reference projection differs')
        projections+=len(projected['packets'])
    artifacts={str(p.relative_to(root)):digest(p) for p in sorted(archive.rglob('*')) if p.is_file()}
    return dict(schema='hexar-retained-native-qualification-verification/v1',passed=True,
        reader_calls_reissued=0,robot_episodes_replayed=0,method_or_judge_calls=0,
        confirmatory_N=0,retained_readers_verified=6,packet_projections_reproduced=projections,
        artifact_hashes=artifacts,verifier_sha256=digest(Path(__file__)),
        scope='Read-only archive reproduction; not integrated production admission.')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    result=verify();exclusive_json(args.output,result)
    print(json.dumps({k:v for k,v in result.items() if k!='artifact_hashes'}))
