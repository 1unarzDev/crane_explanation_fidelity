"""Committed raw-acquisition admission; never requires or opens H1 outcomes.

No raw launches or semantic calls occur here. A permissive development callback
cannot substitute for this production gate. Full freeze/qualification remain
unbound until the authoritative preconfirmation audit genuinely passes.
"""
import hashlib
import json
import re
from pathlib import Path
import subprocess

from ..confirmatory_v1.gatekeeping import validate_family,validate_scientific_binding,load_pinned,LEDGER_PATH
from ..confirmatory_v1.development_exposure import load_exclusions
from ..confirmatory_v1.journal import fingerprint
from ..confirmatory_v1.seal_cohort import committed
from .raw_schedule_v1 import validate_plan
from .raw_archive_v1 import digest,rooted,read
from .bound_cli_guard_v1 import verify_allocations

BASE='manifests/hexar_external/confirmatory_v1'
CONFIG_SCHEMA='hexar-frozen-raw-acquisition-runtime/v1'
QUALIFICATION_CASES=('committed_freeze_required','raw_requires_no_h1_outcome',
    'frozen_source_image_roots','fresh_id_seed_exclusions','durable_single_robot_launch',
    'owned_cid_cleanup','read_only_native_reproduction','no_semantic_dispatch',
    'missing_bag_invalid_export','conservative_crash_no_replay','fixed_family_reserves',
    'full_disposition_binding','immutable_seal_resume')
CRITICAL_FILES=tuple('analysis/hexar_external/'+p for p in (
    'acquisition/raw_acquisition_admission_v1.py','acquisition/raw_schedule_v1.py','acquisition/bound_cli_guard_v1.py',
    'acquisition/raw_runtime_v1.py','acquisition/raw_review_v1.py','acquisition/raw_archive_v1.py',
    'acquisition/raw_recovery_v1.py','acquisition/raw_cohort_pipeline_v1.py',
    'acquisition/project_raw_episode_v1.py','acquisition/native_review_core_v1.py',
    'acquisition/operational_validity_candidate.py','acquisition/technical_predicate.py',
    'acquisition/family_delivery.py','confirmatory_v1/seal_archived_attempts_v2.py',
    'confirmatory_v1/journal.py','confirmatory_v1/gatekeeping.py','confirmatory_v1/seal_cohort.py',
    'confirmatory_v1/strict_json.py','confirmatory_v1/registered_attempt_executor_v2.py'))


def load_context(root,base=BASE):
    root=Path(root).resolve();base=rooted(root,base)
    freeze_path=base/'freeze_manifest.json';freeze=read(freeze_path)
    if (freeze.get('schema')!='hexar-confirmatory-freeze/v1' or freeze.get('status')!='FROZEN'
            or freeze.get('acquisition_authorized') is not True or freeze.get('confirmation_authorized') is not False
            or freeze.get('semantic_n')!=0 or not committed(root,freeze_path)):
        raise ValueError('committed prospective acquisition freeze required before raw dispatch')
    hashes=freeze.get('file_hashes')
    if type(hashes) is not dict or not hashes:raise ValueError('complete frozen file closure required')
    # The authoritative ledger may legitimately record H1 consumption later;
    # verify its live family assignment separately without rebinding science.
    for name,expected in hashes.items():
        path=rooted(root,name)
        if name==LEDGER_PATH:continue
        if digest(path)!=expected or not committed(root,path):raise ValueError('frozen file changed or uncommitted: '+name)
    for name in CRITICAL_FILES:
        if hashes.get(name)!=digest(rooted(root,name)):
            raise ValueError('running raw adapter/predicate omitted from freeze or changed: '+name)
    audit_path=base/'preconfirmation_audit.json'
    if digest(audit_path)!=freeze.get('audit_sha256') or not committed(root,audit_path) or read(audit_path).get('passed') is not True:
        raise ValueError('committed passed prospective acquisition audit required')
    pin=freeze['sequence_document'];family=load_pinned(root,pin['path'],pin['sha256'])
    validate_family(family,read(root/LEDGER_PATH),activation=False)
    if family.get('status')!='FROZEN' or family.get('bound_alpha')!=.01:
        raise ValueError('ordered family and both scientific designs must be prospectively bound')
    validate_scientific_binding(root,family,freeze)
    h1=family['sequence'][0]
    if not h1.get('freeze_path') or not h1.get('freeze_sha256') or h1.get('sidedness') not in ('one-sided','two-sided'):
        raise ValueError('complete H1 procedure must be bound in the prospective family')
    h1_path=rooted(root,h1['freeze_path']);h1_freeze=load_pinned(root,h1['freeze_path'],h1['freeze_sha256'])
    if h1_freeze.get('status')!='FROZEN' or h1_freeze.get('alpha')!=.01 or not h1_freeze.get('decision_rule_sha256') or not committed(root,h1_path):
        raise ValueError('committed complete H1 scientific procedure required; no H1 outcome is read')
    shared=subprocess.check_output(['git','show','main:'+pin['path']],cwd=root)
    if hashlib.sha256(shared).hexdigest()!=pin['sha256']:raise ValueError('ordered-family freeze not reconciled with main')
    shared_ledger=subprocess.check_output(['git','show','main:'+LEDGER_PATH],cwd=root)
    if shared_ledger!=(root/LEDGER_PATH).read_bytes():raise ValueError('authoritative main/local ledger diverged')
    cohort=read(base/'cohort.json');decision=read(base/'fixed_n_decision.json')
    plan_path=rooted(root,cohort['episode_plan_path'])
    if digest(plan_path)!=cohort['episode_plan_sha256'] or not committed(root,plan_path):raise ValueError('frozen fresh seed schedule changed')
    plan=read(plan_path);validate_plan(plan)
    if plan.get('phase')!='confirmation':raise ValueError('development schedule cannot enter production admission')
    if (decision.get('final_valid_n')!=6*plan['valid_per_family']
            or cohort.get('valid_per_family')!=plan['valid_per_family']
            or cohort.get('maximum_attempts_per_family')!=plan['maximum_attempts_per_family']
            or cohort.get('families')!=plan['family_order']):
        raise ValueError('frozen N/family/reserve schedule disagrees')
    config_pin=cohort['generation_process']
    if set(config_pin)!={'path','sha256'}:raise ValueError('exact runtime configuration pin required')
    config_path=rooted(root,config_pin['path'])
    if hashes.get(config_pin['path'])!=config_pin['sha256'] or digest(config_path)!=config_pin['sha256']:
        raise ValueError('runtime configuration omitted from freeze or changed')
    config=read(config_path)
    required={'schema','status','image_id','source_bank_path','source_hashes','execution_source_bank_sha256',
              'execution_root','capture_root','native_reader','qualification','ros_domain_id','cpus','memory',
              'memory_swap','shared_memory','episode_wall_timeout_seconds','native_wall_timeout_seconds'}
    if set(config)!=required or config['schema']!=CONFIG_SCHEMA or config['status']!='READY_FOR_FREEZE':
        raise ValueError('complete qualified final raw runtime configuration required')
    if not isinstance(config['image_id'],str) or not re.fullmatch('sha256:[0-9a-f]{64}',config['image_id']):
        raise ValueError('immutable qualified simulator image ID required')
    expected=dict(ros_domain_id=70,cpus='3',memory='5g',memory_swap='6g',shared_memory='1g',
                  episode_wall_timeout_seconds=230,native_wall_timeout_seconds=180)
    if any(config[k]!=v for k,v in expected.items()):raise ValueError('runtime differs from qualified resources/domain/time bounds')
    for key in ('execution_root','capture_root'):
        path=rooted(root,config[key]);path.relative_to(root/'manifests/hexar_external')
    if rooted(root,config['execution_root']).is_relative_to(rooted(root,config['capture_root'])) or rooted(root,config['capture_root']).is_relative_to(rooted(root,config['execution_root'])):
        raise ValueError('capture and journal roots must be distinct nonoverlapping namespaces')
    sources=config['source_hashes']
    bank_id=hashlib.sha256(json.dumps(sources,sort_keys=True).encode()).hexdigest()
    if not sources or bank_id!=config['execution_source_bank_sha256']:raise ValueError('executed source-bank binding incomplete')
    bank=rooted(root,config['source_bank_path'])
    for original,expected_hash in sources.items():
        relative=Path(original).relative_to('analysis/hexar_external/acquisition')
        if digest(rooted(bank,relative))!=expected_hash:raise ValueError('executed acquisition source bytes changed')
    verify_allocations(bank/'run_bound_episode_v1.sh',plan['records'],'raw_confirmation',digest(freeze_path))
    native=config['native_reader']
    if set(native)!={'path','sha256'} or hashes.get(native['path'])!=native['sha256'] or digest(rooted(root,native['path']))!=native['sha256']:
        raise ValueError('native reader is not bound in complete scientific/runtime freeze')
    q=config['qualification'];qualified=read(rooted(root,q['path']))
    if (digest(rooted(root,q['path']))!=q['sha256'] or hashes.get(q['path'])!=q['sha256']
            or qualified.get('schema')!='hexar-raw-technical-adapter-qualification/v1'
            or qualified.get('status')!='QUALIFIED_PRECONFIRMATION_TECHNICAL_ADAPTER'
            or set(qualified.get('scenarios',{}))!=set(QUALIFICATION_CASES)
            or any(qualified['scenarios'][name] is not True for name in QUALIFICATION_CASES)
            or qualified.get('runtime_binding_sha256')!=fingerprint({k:v for k,v in config.items() if k!='qualification'})
            or qualified.get('image_id')!=config['image_id']
            or qualified.get('confirmatory_outputs_generated')!=0
            or any(qualified.get('source_hashes',{}).get(name)!=hashes[name] for name in CRITICAL_FILES)):
        # Qualification binds runtime fields excluding its own pointer. The
        # complete config then pins the report; this avoids reciprocal hashes.
        raise ValueError('actual final acquisition adapter qualification missing/changed')
    for key,status in (('physics_scope','BOUND_PROVENANCE_RUNTIME_SCOPE_QUALIFIED_NOT_FINAL_ADMISSION'),
                       ('native_scope','READ_ONLY_PHASE_AWARE_NATIVE_CORE_QUALIFIED_NOT_PRODUCTION_ADMISSION')):
        scope_pin=qualified.get(key)
        if not isinstance(scope_pin,dict) or set(scope_pin)!={'path','sha256'}:
            raise ValueError('actual captured development physics/native scope pins required')
        scope_path=rooted(root,scope_pin['path'])
        if digest(scope_path)!=scope_pin['sha256'] or hashes.get(scope_pin['path'])!=scope_pin['sha256']:
            raise ValueError('qualified actual physics/native evidence omitted or changed')
        scope=read(scope_path)
        if scope.get('status')!=status or len(scope.get('rows',[]))!=6:
            raise ValueError('complete six-family actual qualification scope required')
        passed_key='technical_valid' if key=='physics_scope' else 'passed'
        if any(row.get(passed_key) is not True for row in scope['rows']):
            raise ValueError('every declared physics/native development case must pass')
        if key=='physics_scope' and scope.get('image_id')!=config['image_id']:
            raise ValueError('runtime image differs from actual physics qualification')
        if key=='native_scope' and (scope.get('reader_calls')!=6 or scope.get('packet_projections')!=54
                or scope.get('robot_episode_replays')!=0 or scope.get('method_or_judge_calls')!=0
                or scope.get('source_hashes',{}).get(native['path'])!=native['sha256']):
            raise ValueError('actual read-only native reproduction differs from final reader')
        for source,expected_sha in scope.get('source_hashes',{}).items():
            if digest(rooted(root,source))!=expected_sha:
                raise ValueError('actual physics/native qualification source evidence changed')
    freshness=read(base/'freshness_ledger.json')
    original_manifest='data/hexar_external/audit/source_data_manifest.json'
    original_path=rooted(root,original_manifest)
    if digest(original_path)!=freshness['source_hashes'].get(original_manifest) or not committed(root,original_path):
        raise ValueError('original HEXAR source/exclusion manifest missing, changed or uncommitted')
    exposure=freshness['development_acquisition_exclusions']
    excluded_hashes,excluded_ids,excluded_seeds=load_exclusions(root,exposure,require_current=True)
    excluded_hashes.update(item['sha256'] for item in read(original_path)['files'] if 'bagfiles/' in item['path'])
    if any(r['acquisition_id'] in excluded_ids or r['seed'] in excluded_seeds for r in plan['records']):
        raise ValueError('fresh raw plan collides with development identities/seeds')
    return dict(root=root,base=base,freeze_path=freeze_path,freeze_sha256=digest(freeze_path),
                freeze=freeze,plan=plan,config=config,config_path=config_path,
                excluded_hashes=excluded_hashes,excluded_ids=excluded_ids,excluded_seeds=excluded_seeds)


class Admission:
    def __init__(self,root,base=BASE):self.root,self.base=Path(root).resolve(),base
    def __call__(self,request):
        ctx=load_context(self.root,self.base);config=ctx['config']
        expected_root=str(rooted(self.root,config['execution_root']))
        identity=dict(schema='hexar-raw-schedule-execution/v1',binding_sha256=ctx['freeze_sha256'],
                      plan_sha256=fingerprint(ctx['plan']),execution_root=expected_root)
        if request!=dict(identity,plan=ctx['plan']):raise ValueError('raw dispatcher uses unfrozen root/plan/binding')
        return dict(authorized=True,**identity)
