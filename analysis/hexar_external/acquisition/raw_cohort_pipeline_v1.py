"""Frozen finite raw acquisition through immutable seal; no semantic backend."""
import argparse
from pathlib import Path

from .raw_acquisition_admission_v1 import Admission,load_context,BASE
from .raw_schedule_v1 import RawSchedule
from .raw_runtime_v1 import Runtime
from .raw_review_v1 import Review
from .raw_recovery_v1 import Recovery
from .raw_archive_v1 import digest,rooted,read
from ..confirmatory_v1.journal import exclusive_json
from ..confirmatory_v1.seal_archived_attempts_v2 import select

ROOT=Path(__file__).resolve().parents[3]


def execute(root=ROOT,base=BASE):
    ctx=load_context(root,base);config=ctx['config']
    execution=rooted(root,config['execution_root']);seal=ctx['base']/'raw_cohort_seal.json'
    if seal.exists():raise ValueError('raw cohort seal exists; no reacquisition or replacement')
    scheduler=RawSchedule(execution,ctx['plan'],ctx['freeze_sha256'],Admission(root,base))
    runtime,review,recovery=Runtime(root,base),Review(root,base),Recovery(root,base)
    while True:
        result=scheduler.advance(runtime.capture,review,recovery.export_invalid)
        if result['status']=='ATTEMPT_CLOSED':continue
        ctx=load_context(root,base)
        attempts,counts,_,pending=scheduler.state()
        if pending is not None:raise ValueError('unclosed raw attempt cannot be sealed')
        exported=[]
        for closed in attempts:
            record=closed['claim']['planned'];folder=scheduler.folder(record)
            path=folder/('recovered_exported_attempt.json' if closed['disposition']=='INDETERMINATE_NO_REISSUE' else 'exported_attempt.json')
            row=read(path);validity=read(rooted(root,row['validity_receipt_path']))
            if validity['technical_valid']!=closed['technical_valid'] or validity['reasons']!=closed['reasons']:
                raise ValueError('native disposition and frozen scheduler disagree')
            exported.append(row)
        manifest=dict(schema='hexar-frozen-raw-attempt-manifest/v2',phase='confirmation',
            freeze_sha256=ctx['freeze_sha256'],episode_plan_sha256=digest(rooted(root,read(ctx['base']/'cohort.json')['episode_plan_path'])),
            attempts=exported,valid_by_family=counts,terminal_status=result['status'],
            semantic_outputs_generated=False,method_or_judge_calls=0)
        manifest_path=execution/'terminal_attempt_manifest.json'
        if manifest_path.exists():
            if read(manifest_path)!=manifest:raise ValueError('retained terminal raw manifest changed')
        else:exclusive_json(manifest_path,manifest)
        if result['status']!='VALID_QUOTAS_COMPLETE_NOT_SEALED':
            terminal=dict(status='FINITE_RESERVE_EXHAUSTED_NO_COHORT',freeze_sha256=ctx['freeze_sha256'],
                attempt_manifest_sha256=digest(manifest_path),confirmatory_semantic_outputs=0,alpha_consumed=0)
            path=execution/'terminal_result.json'
            if path.exists():
                if read(path)!=terminal:raise ValueError('retained exhausted-cohort disposition changed')
            else:exclusive_json(path,terminal)
            return 'FINITE_RESERVE_EXHAUSTED_NO_COHORT'
        validity=read(ctx['base']/'technical_validity.json')
        records,dispositions=select(root,ctx['plan'],exported,ctx['plan']['valid_per_family'],
            ctx['plan']['maximum_attempts_per_family'],ctx['plan']['family_order'],ctx['freeze_sha256'],
            validity['machine_predicate_sha256'],config['image_id'],ctx['excluded_ids'],ctx['excluded_seeds'],ctx['excluded_hashes'])
        # Compatibility identifiers are private bookkeeping. raw_sha256 denotes
        # the inventory object; actual bag hashes remain explicitly separate.
        selected=[]
        for record in records:
            archive=read(rooted(root,record['raw_archive_path']))
            selected.append(dict(record,recording_id=record['episode_id'],raw_path=record['raw_archive_path'],
                raw_sha256=record['raw_archive_sha256'],bag_sha256s=archive['bag_sha256s'],
                raw_object_type='hash-bound original capture inventory',independent_reset=True,
                semantic_outputs_generated=False))
        exclusive_json(seal,dict(schema='hexar-raw-cohort-seal/v2',status='SEALED',freeze_sha256=ctx['freeze_sha256'],
            attempt_manifest_sha256=digest(manifest_path),attempt_manifest_path=str(manifest_path.relative_to(Path(root))),
            records=selected,dispositions=dispositions,n=len(selected),semantic_outputs_generated=False,
            method_or_judge_calls=0,alpha_consumed=0,
            provenance='adapted simulated HEXAR external-validation benchmark'))
        return 'FRESH_RAW_COHORT_SEALED_SEMANTIC_CONFIRMATION_GATED'


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--base',default=BASE);args=ap.parse_args()
    print(execute(base=args.base))
