"""Fixed-six development qualification of the actual integrated raw adapters.

Independent committed development admission is used; production admission stays
closed. Every generated episode and planned reserve is permanently development.
"""
import argparse
import json
from pathlib import Path

from .raw_acquisition_admission_v1 import CRITICAL_FILES
from .raw_archive_v1 import digest,read,rooted
from .raw_schedule_v1 import RawSchedule,validate_plan
from .raw_runtime_v1 import Runtime
from .raw_review_v1 import Review
from .raw_recovery_v1 import Recovery
from .runtime_closure_v1 import candidate
from ..confirmatory_v1.development_exposure import inventory,load_exclusions
from ..confirmatory_v1.journal import exclusive_json,fingerprint
from ..confirmatory_v1.seal_cohort import committed
from ..confirmatory_v1.seal_archived_attempts_v2 import select

ROOT=Path(__file__).resolve().parents[3]
BASE='manifests/hexar_external/acquisition/development_integrated_raw_v19'
PHASE='development_adapter_qualification'


def context(root=ROOT):
    root=Path(root).resolve();base=root/BASE;declaration=read(base/'declaration.json')
    if (declaration.get('phase')!='development_only' or declaration.get('confirmation_authorized') is not False
            or declaration.get('robot_attempts')!=6 or declaration.get('semantic_calls')!=0
            or not committed(root,base/'declaration.json')):
        raise ValueError('committed fixed-six development-only declaration required')
    resources=declaration.get('captured_readonly_resources',{})
    for name,sha in declaration['source_hashes'].items():
        if digest(root/name)!=sha:
            raise ValueError('declared integrated development source changed: '+name)
        if name in resources:
            pin=resources[name];snapshot=rooted(root,pin['path'])
            if pin['sha256']!=sha or digest(snapshot)!=sha or not committed(root,snapshot):
                raise ValueError('original callback resource lacks committed identical capture: '+name)
        elif not committed(root,root/name):
            raise ValueError('declared integrated development source uncommitted: '+name)
    plan_path=root/declaration['plan_path'];plan=read(plan_path);validate_plan(plan)
    if plan['phase']!='development' or plan['valid_per_family']!=1 or plan['maximum_attempts_per_family']!=2:
        raise ValueError('fixed six primary development attempts and no dispatched reserves required')
    config=read(base/'runtime.json')
    if config['status']!='DEVELOPMENT_ONLY' or config['capture_root']!='manifests/hexar_external/acquisition':
        raise ValueError('development capture namespace required')
    if config['execution_root']!=BASE+'/execution':raise ValueError('fixed development execution root required')
    for source,sha in config['source_hashes'].items():
        bank=root/config['source_bank_path'];rel=Path(source).relative_to('analysis/hexar_external/acquisition')
        if digest(bank/rel)!=sha:raise ValueError('qualified captured physics bank changed')
    # Snapshot precedes acquisition and includes this complete planned schedule.
    exposure_pin=declaration['exposure_snapshot'];exposure=read(root/exposure_pin['path'])
    excluded_hashes,excluded_ids,excluded_seeds=load_exclusions(root,exposure_pin)
    current=inventory(root);planned_ids={r['episode_id'] for r in plan['records']}
    baseline={json.dumps(r,sort_keys=True) for r in exposure['records']}
    current_baseline={json.dumps(r,sort_keys=True) for r in current['records'] if r['acquisition_id'] not in planned_ids}
    if baseline!=current_baseline or current['planned_development_acquisitions']!=exposure['planned_development_acquisitions']:
        raise ValueError('unrelated development inventory changed during fixed-six qualification')
    for row in current['records']:
        if row['acquisition_id'] in planned_ids:
            receipt=read(root/row['provenance_path'])
            if receipt.get('acquisition_phase')!=PHASE or receipt.get('acquisition_binding_sha256')!=digest(base/'declaration.json'):
                raise ValueError('new development capture has wrong phase/binding')
    original=read(root/'data/hexar_external/audit/source_data_manifest.json')
    excluded_hashes.update(item['sha256'] for item in original['files'] if 'bagfiles/' in item['path'])
    return dict(root=root,base=base,plan=plan,config=config,freeze_sha256=digest(base/'declaration.json'),
        excluded_ids=excluded_ids-planned_ids,excluded_seeds=excluded_seeds-{r['seed'] for r in plan['records']},
        excluded_hashes=excluded_hashes)


def admission(root):
    def admit(request):
        ctx=context(root)
        identity=dict(schema='hexar-raw-schedule-execution/v1',binding_sha256=ctx['freeze_sha256'],
            plan_sha256=fingerprint(ctx['plan']),execution_root=str(rooted(root,ctx['config']['execution_root'])))
        if request!=dict(identity,plan=ctx['plan']):raise ValueError('development schedule/binding changed')
        return dict(authorized=True,**identity)
    return admit


class DevelopmentContext:
    def context(self,record,attempt_folder):
        ctx=context(self.root)
        if record not in ctx['plan']['records'][:6]:raise ValueError('development reserve dispatch forbidden')
        expected=rooted(self.root,ctx['config']['execution_root'])/'attempts'/record['acquisition_id']
        if Path(attempt_folder).resolve()!=expected:raise ValueError('development execution root changed')
        claim=read(expected/'claim.json')
        if (claim.get('planned')!=record or claim.get('binding_sha256')!=ctx['freeze_sha256']
                or claim.get('launch_limit')!=1 or claim.get('method_or_judge_calls_permitted') is not False):
            raise ValueError('durable development-only claim required')
        return ctx


class DevelopmentRuntime(DevelopmentContext,Runtime):pass
class DevelopmentReview(DevelopmentContext,Review):pass
class DevelopmentRecovery(DevelopmentContext,Recovery):pass


def execute(root=ROOT):
    root=Path(root).resolve();ctx=context(root);base=ctx['base'];report_path=base/'report.json'
    if report_path.exists():raise ValueError('terminal development report exists; no reissue')
    scheduler=RawSchedule(rooted(root,ctx['config']['execution_root']),ctx['plan'],ctx['freeze_sha256'],admission(root))
    runtime=DevelopmentRuntime(root,phase=PHASE);review=DevelopmentReview(root,phase=PHASE)
    recovery=DevelopmentRecovery(root,phase=PHASE)
    while True:
        attempts,counts,_,pending=scheduler.state()
        if len(attempts)==6:
            if pending is not None:raise ValueError('unexpected development pending reserve')
            break
        # Exactly six original interleaved primaries, regardless of validity.
        result=scheduler.advance(runtime.capture,review,recovery.export_invalid)
        if result['status']!='ATTEMPT_CLOSED':raise ValueError('development initial battery stopped unexpectedly')
        print(json.dumps(dict(status='DEVELOPMENT_ATTEMPT_CLOSED',episode_id=result['outcome']['claim']['planned']['episode_id'],
            disposition=result['outcome']['disposition'])),flush=True)
    exported=[]
    for closed in attempts:
        record=closed['claim']['planned'];folder=scheduler.folder(record)
        name='recovered_exported_attempt.json' if closed['disposition']=='INDETERMINATE_NO_REISSUE' else 'exported_attempt.json'
        row=read(folder/name);validity=read(root/row['validity_receipt_path'])
        if validity['technical_valid']!=closed['technical_valid'] or validity['reasons']!=closed['reasons']:
            raise ValueError('development native/scheduler disposition differs')
        exported.append(row)
    passed=all(c['technical_valid'] for c in attempts)
    selected=[];dispositions=[]
    if passed:
        selected,dispositions=select(root,ctx['plan'],exported,1,2,ctx['plan']['family_order'],ctx['freeze_sha256'],
            digest(Path(__file__).with_name('raw_review_v1.py')),ctx['config']['image_id'],ctx['excluded_ids'],
            ctx['excluded_seeds'],ctx['excluded_hashes'],expected_phase=PHASE)
        exclusive_json(base/'development_archive_seal.json',dict(status='DEVELOPMENT_ONLY_ARCHIVE_SEALED',phase='development_only',
            declaration_sha256=ctx['freeze_sha256'],records=selected,dispositions=dispositions,
            eligible_for_confirmation=False,confirmatory_N=0,semantic_outputs_generated=False))
    final=dict(schema='hexar-integrated-raw-development-qualification/v1',phase='development_only',
        status='INTEGRATED_RAW_RUNTIME_DEVELOPMENT_SCOPE_PASSED_NOT_PRODUCTION_ADMISSION' if passed else 'FAILED_QUALIFICATION_RETAINED',
        declaration_sha256=ctx['freeze_sha256'],rows=[dict(episode_id=c['claim']['planned']['episode_id'],
            technical_valid=c['technical_valid'],reasons=c['reasons'],disposition=c['disposition']) for c in attempts],
        exported_attempts=exported,valid_by_family=counts,selected_development_episodes=len(selected),
        reserves_dispatched=0,method_or_judge_calls=0,confirmatory_N=0,alpha_consumed=0,
        full_production_qualification=False,confirmation_authorized=False,
        evidence_hashes={str(p.relative_to(root)):digest(p) for p in sorted((base/'execution').rglob('*')) if p.is_file() and p.name!='acquisition.lock'})
    context(root);exclusive_json(report_path,final)
    return final


if __name__=='__main__':print(execute()['status'])
