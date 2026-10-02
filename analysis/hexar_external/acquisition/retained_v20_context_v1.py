"""Read-only V20 context after an explicit nonexecuted admission-source change.

Never authorizes capture/semantic execution. Exact computational sources remain
required; only the unused gatekeeping module is verified at its original commit.
"""
import hashlib
import json
import subprocess
from pathlib import Path

from .raw_archive_v1 import digest,read,rooted
from .raw_schedule_v1 import validate_plan
from .bound_cli_guard_v1 import verify_allocations
from ..confirmatory_v1.development_exposure import inventory,load_exclusions
from ..confirmatory_v1.journal import fingerprint
from ..confirmatory_v1.seal_cohort import committed

ROOT=Path(__file__).resolve().parents[3]
BASE='manifests/hexar_external/acquisition/development_integrated_raw_v20'
PHASE='development_adapter_qualification'
HISTORICAL_COMMIT='83bac08d'

def context(root=ROOT):
    root=Path(root).resolve();base=root/BASE;declaration=read(base/'declaration.json')
    if (declaration.get('phase')!='development_only' or declaration.get('confirmation_authorized') is not False
            or declaration.get('robot_attempts')!=6 or declaration.get('semantic_calls')!=0
            or not committed(root,base/'declaration.json')):
        raise ValueError('committed fixed-six development-only declaration required')
    resources=declaration.get('captured_readonly_resources',{})
    for name,sha in declaration['source_hashes'].items():
        if digest(root/name)!=sha:
            # Gatekeeping is a nonexecuted admission dependency in this read-only
            # development verifier. Its original bytes remain hash-bound in Git.
            if name != 'analysis/hexar_external/confirmatory_v1/gatekeeping.py':
                raise ValueError('retained raw computational source changed: '+name)
            original = subprocess.check_output(['git','show',HISTORICAL_COMMIT+':'+name],cwd=root)
            if hashlib.sha256(original).hexdigest()!=sha:
                raise ValueError('original historical gatekeeping source unavailable or changed')
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
    verify_allocations(root/config['source_bank_path']/'run_bound_episode_v1.sh',plan['records'],PHASE,digest(base/'declaration.json'))
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

