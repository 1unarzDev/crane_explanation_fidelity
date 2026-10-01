"""Exercise genuine admission validators in isolated Git with synthetic pins.

Synthetic qualification assertions test gate wiring, not robot/provider readiness.
No repository study manifests are changed; no Docker/provider is dispatched.
"""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from analysis.hexar_external.acquisition import raw_acquisition_admission_v1 as gate
from analysis.hexar_external.acquisition.raw_archive_v1 import digest,read
from analysis.hexar_external.acquisition.raw_schedule_v1 import make_plan
from analysis.hexar_external.confirmatory_v1.development_exposure import inventory
from analysis.hexar_external.confirmatory_v1.gatekeeping import FAMILY_PATH,FAMILY_ID,H2,SCIENTIFIC_FILES
from analysis.hexar_external.confirmatory_v1.journal import fingerprint

SOURCE=Path(__file__).resolve().parents[2]


def git(root,*args):
    return subprocess.check_output(['git',*args],cwd=root,stderr=subprocess.PIPE)


def build(root):
    def write(name,value):
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(value,sort_keys=True)+'\n')
        return dict(path=name,sha256=digest(path))
    git(root,'init','-q','-b','main');git(root,'config','user.name','Synthetic admission fixture')
    git(root,'config','user.email','synthetic@example.invalid')
    for name in gate.CRITICAL_FILES:
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(SOURCE/name,path)
    sources={name:digest(root/name) for name in gate.CRITICAL_FILES}
    image='sha256:'+'e'*64
    bank=root/'bank';bank.mkdir();(bank/'run_bound_episode_v1.sh').write_text('synthetic unused source\n')
    bank_sources={'analysis/hexar_external/acquisition/run_bound_episode_v1.sh':digest(bank/'run_bound_episode_v1.sh')}
    native_name='analysis/hexar_external/acquisition/native_review_core_v1.py'
    physics=write('fixtures/physics.json',dict(status='BOUND_PROVENANCE_RUNTIME_SCOPE_QUALIFIED_NOT_FINAL_ADMISSION',
        image_id=image,rows=[dict(technical_valid=True) for _ in range(6)],source_hashes={}))
    native=write('fixtures/native.json',dict(status='READ_ONLY_PHASE_AWARE_NATIVE_CORE_QUALIFIED_NOT_PRODUCTION_ADMISSION',
        rows=[dict(passed=True) for _ in range(6)],reader_calls=6,packet_projections=54,robot_episode_replays=0,
        method_or_judge_calls=0,source_hashes={native_name:sources[native_name]}))
    config=dict(schema=gate.CONFIG_SCHEMA,status='READY_FOR_FREEZE',image_id=image,
        source_bank_path='bank',source_hashes=bank_sources,
        execution_source_bank_sha256=hashlib.sha256(json.dumps(bank_sources,sort_keys=True).encode()).hexdigest(),
        execution_root='manifests/hexar_external/synthetic/execution',capture_root='manifests/hexar_external/synthetic/capture',
        native_reader=dict(path=native_name,sha256=sources[native_name]),qualification=None,
        ros_domain_id=70,cpus='3',memory='5g',memory_swap='6g',shared_memory='1g',
        episode_wall_timeout_seconds=230,native_wall_timeout_seconds=180)
    q=write('fixtures/qualification.json',dict(schema='hexar-raw-technical-adapter-qualification/v1',
        status='QUALIFIED_PRECONFIRMATION_TECHNICAL_ADAPTER',scenarios={k:True for k in gate.QUALIFICATION_CASES},
        runtime_binding_sha256=fingerprint({k:v for k,v in config.items() if k!='qualification'}),
        image_id=image,confirmatory_outputs_generated=0,source_hashes=sources,physics_scope=physics,native_scope=native))
    config['qualification']=q;config_pin=write('fixtures/runtime.json',config)
    base=gate.BASE
    plan=make_plan('a'*64,1,1);plan_pin=write('fixtures/plan.json',plan)
    write(base+'/cohort.json',dict(episode_plan_path=plan_pin['path'],episode_plan_sha256=plan_pin['sha256'],
        valid_per_family=1,maximum_attempts_per_family=2,families=plan['family_order'],generation_process=config_pin))
    write(base+'/fixed_n_decision.json',dict(final_valid_n=6))
    for path in SCIENTIFIC_FILES:
        if not (root/path).exists():write(path,dict(synthetic=True))
    write(base+'/runtime_dependencies.json',dict(complete_transitive_closure=True,files=sources))
    dev='manifests/hexar_external/acquisition/hexar-tiago-dev-synthetic/provenance.json'
    write(dev,dict(episode_id='hexar-tiago-dev-synthetic',seed_hidden=1,raw_files=[]))
    exposure=write('fixtures/development.json',inventory(root))
    original='data/hexar_external/audit/source_data_manifest.json'
    original_pin=write(original,dict(files=[dict(path='bagfiles/original.db3',sha256='b'*64)]))
    write(base+'/freshness_ledger.json',dict(development_acquisition_exclusions=exposure,
        source_hashes={original:original_pin['sha256']}))
    files=dict(sources)
    for path in SCIENTIFIC_FILES:files[path]=digest(root/path)
    for pin in (physics,native,q,config_pin,plan_pin,original_pin,exposure):files[pin['path']]=pin['sha256']
    files[base+'/freshness_ledger.json']=digest(root/(base+'/freshness_ledger.json'))
    binding=write('fixtures/scientific_binding.json',dict(status='FROZEN',claim_id=H2,files=files))
    h1=write('fixtures/h1_freeze.json',dict(status='FROZEN',alpha=.01,decision_rule_sha256='c'*64))
    family=write(FAMILY_PATH,dict(family_id=FAMILY_ID,family_alpha=.01,previously_consumed_alpha=.02,
        protected_replication_alpha=.02,allocation_id='candidate-revision-reserve',status='FROZEN',bound_alpha=.01,
        sequence=[dict(hypothesis_id='H1',order=1,claim_id='b4-versus-b2-evidence-calibration-primary',alpha=.01,
            sidedness='one-sided',freeze_path=h1['path'],freeze_sha256=h1['sha256']),
            dict(hypothesis_id='H2',order=2,claim_id=H2,alpha=.01,sidedness='one-sided',
                protocol_binding_path=binding['path'],protocol_binding_sha256=binding['sha256'])]))
    ledger=read(SOURCE/gate.LEDGER_PATH);ledger['allocations'][1]['campaign_id']=FAMILY_ID
    ledger_pin=write(gate.LEDGER_PATH,ledger)
    audit=write(base+'/preconfirmation_audit.json',dict(passed=True,synthetic_fixture=True))
    for pin in (family,binding,h1,ledger_pin):files[pin['path']]=pin['sha256']
    write(base+'/freeze_manifest.json',dict(schema='hexar-confirmatory-freeze/v1',status='FROZEN',
        acquisition_authorized=True,confirmation_authorized=False,semantic_n=0,file_hashes=files,
        audit_sha256=audit['sha256'],sequence_document=family))
    git(root,'add','.');git(root,'commit','-qm','Isolated synthetic admission fixture')
    return plan,config


def test_real_positive_admission_requires_no_h1_result_or_docker(tmp_path):
    plan,config=build(tmp_path)
    ctx=gate.load_context(tmp_path)
    assert ctx['plan']==plan and ctx['config']==config
    assert 'b'*64 in ctx['excluded_hashes'] and 1 in ctx['excluded_seeds']
    identity=dict(schema='hexar-raw-schedule-execution/v1',binding_sha256=ctx['freeze_sha256'],
        plan_sha256=fingerprint(plan),execution_root=str(tmp_path/config['execution_root']))
    assert gate.Admission(tmp_path)(dict(identity,plan=plan))==dict(authorized=True,**identity)
    assert not (tmp_path/config['execution_root']).exists()
    assert not list(tmp_path.rglob('*result*'))
    altered=copy.deepcopy(plan);altered['valid_per_family']=2
    with pytest.raises(ValueError,match='unfrozen root/plan/binding'):
        gate.Admission(tmp_path)(dict(identity,plan=altered))


def test_uncommitted_critical_source_edit_revokes_positive_admission(tmp_path):
    build(tmp_path);path=tmp_path/gate.CRITICAL_FILES[0]
    path.write_text(path.read_text()+'\n# synthetic tamper\n')
    with pytest.raises(ValueError,match='changed or uncommitted'):gate.load_context(tmp_path)


def test_current_main_ledger_divergence_revokes_positive_admission(tmp_path):
    build(tmp_path);path=tmp_path/gate.LEDGER_PATH;ledger=read(path)
    ledger['updated']='synthetic change'
    path.write_text(json.dumps(ledger))
    with pytest.raises(ValueError,match='main/local ledger diverged'):gate.load_context(tmp_path)
