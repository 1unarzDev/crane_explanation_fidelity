"""Versioned read-only V20 verification; preserves historical admission source."""
import argparse
from pathlib import Path

from .retained_v20_context_v1 import ROOT,BASE,PHASE,context,admission,HISTORICAL_COMMIT
from .raw_schedule_v1 import RawSchedule
from .raw_archive_v1 import digest,read,verify
from .project_raw_episode_v1 import review as project
from .operational_validity_candidate import evaluate
from ..confirmatory_v1.journal import exclusive_json
from ..confirmatory_v1.seal_archived_attempts_v2 import select


def check(root=ROOT):
    root=Path(root);ctx=context(root);base=ctx['base'];report=read(base/'report.json')
    if (report['status']!='INTEGRATED_RAW_RUNTIME_DEVELOPMENT_SCOPE_PASSED_NOT_PRODUCTION_ADMISSION'
            or report['declaration_sha256']!=ctx['freeze_sha256'] or len(report['rows'])!=6
            or report['method_or_judge_calls']!=0 or report['confirmatory_N']!=0
            or report['reserves_dispatched']!=0 or report['confirmation_authorized'] is not False):
        raise ValueError('complete terminal six-primary development scope required')
    for name,sha in report['evidence_hashes'].items():
        if digest(root/name)!=sha:raise ValueError('retained integrated evidence changed: '+name)
    execution=root/ctx['config']['execution_root']
    if not (execution/'schedule.json').exists() or not (execution/'binding.json').exists():
        raise ValueError('retained scheduler root missing')
    scheduler=RawSchedule(execution,ctx['plan'],ctx['freeze_sha256'],admission(root))
    attempts,counts,_,pending=scheduler.state()
    if len(attempts)!=6 or pending is not None or not all(c['technical_valid'] for c in attempts):
        raise ValueError('retained scheduler dispositions differ')
    exported=[];rows=[];containers=set();bags=set();packet_count=0;reader_claims=0
    for closed in attempts:
        record=closed['claim']['planned'];folder=scheduler.folder(record);uid=record['episode_id']
        row=read(folder/'exported_attempt.json');exported.append(row)
        if row!=next(r for r in report['exported_attempts'] if r['acquisition_id']==uid):
            raise ValueError('retained exported attempt differs')
        archive=verify(root,row['raw_archive_path'],row['raw_archive_sha256'],ctx['freeze_sha256'],record,
            ctx['config']['image_id'],ctx['excluded_hashes'],expected_phase=PHASE)
        capture=root/archive['folder'];receipt=read(capture/'provenance.json');episode=read(capture/'episode.json')
        containers.add(receipt['container_id']);bags.update(archive['bag_sha256s'])
        # Preserve original transport key order for pretty-JSON compatibility
        # stream hashes; the derived JSON archive canonicalizes key order.
        value=read(folder/'native_stdout.bin')
        if (read(folder/'derived_native_review.json')!=value or value['phase']!=PHASE
                or value['acquisition_binding_sha256']!=ctx['freeze_sha256']
                or value['episode_id']!=uid or value['original_capture_mutated'] is not False
                or value['method_or_judge_calls']!=0):
            raise ValueError('retained original native transport differs')
        claim=read(folder/'native_dispatch_claim.json')
        if claim['launch_limit']!=1 or claim['freeze_sha256']!=ctx['freeze_sha256'] or claim['method_or_judge_calls_permitted'] is not False:
            raise ValueError('native dispatch scope differs')
        reader_claims+=1
        derived=project(capture,uid,value['events'],value['motion'])
        if derived!=read(folder/'derived_interface_review.json'):
            raise ValueError('original packet/reference reproduction differs')
        verdict=evaluate(receipt,episode,record,derived['episode'],value['native_review'])
        validity=read(root/row['validity_receipt_path'])
        if (digest(root/row['validity_receipt_path'])!=row['validity_receipt_sha256']
                or verdict['technical_valid'] is not True or verdict['reasons']!=closed['reasons']
                or validity['reasons']!=closed['reasons'] or validity['method_outcomes_accessed'] is not False):
            raise ValueError('native predicate/disposition reproduction differs')
        if len(derived['packets'])!=9:raise ValueError('complete fixed battery required')
        packet_count+=len(derived['packets']);rows.append(dict(episode_id=uid,technical_valid=True,packets=9))
    records,dispositions=select(root,ctx['plan'],exported,1,2,ctx['plan']['family_order'],ctx['freeze_sha256'],
        digest(Path(__file__).with_name('raw_review_v1.py')),ctx['config']['image_id'],ctx['excluded_ids'],
        ctx['excluded_seeds'],ctx['excluded_hashes'],expected_phase=PHASE)
    seal=read(base/'development_archive_seal.json')
    if (seal['status']!='DEVELOPMENT_ONLY_ARCHIVE_SEALED' or seal['phase']!='development_only'
            or seal['declaration_sha256']!=ctx['freeze_sha256'] or seal['records']!=records
            or seal['dispositions']!=dispositions or seal['eligible_for_confirmation'] is not False
            or seal['confirmatory_N']!=0 or seal['semantic_outputs_generated'] is not False):
        raise ValueError('development-only archive selection differs')
    if len(containers)!=6 or len(bags)!=6 or reader_claims!=6:
        raise ValueError('distinct actual capture containers/bags and six reader claims required')
    if any((base/'execution/attempts'/r['episode_id']).exists() for r in ctx['plan']['records'][6:]):
        raise ValueError('undeclared development reserve dispatched')
    return dict(schema='hexar-integrated-raw-development-verification/v1',passed=True,
        phase='read_only_development_archive_verification',report_sha256=digest(base/'report.json'),
        declaration_sha256=ctx['freeze_sha256'],development_seal_sha256=digest(base/'development_archive_seal.json'),
        rows=rows,packet_projections_reproduced=packet_count,distinct_original_containers=6,distinct_bag_hashes=6,
        retained_reader_claims=6,robot_or_native_calls_reissued=0,method_or_judge_calls=0,confirmatory_N=0,
        alpha_consumed=0,production_authorized=False,confirmation_authorized=False,
        verifier_sha256=digest(Path(__file__)),context_sha256=digest(Path(__file__).with_name('retained_v20_context_v1.py')),
        historical_commit=HISTORICAL_COMMIT,original_gatekeeping_source_verified_in_git=True,
        current_production_admission_relaxed=False,scope='Full retained V20 technical path reproduction; final production/provider/scientific freeze remains unbound.')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    value=check();exclusive_json(args.output,value);print({k:v for k,v in value.items() if k!='rows'})
