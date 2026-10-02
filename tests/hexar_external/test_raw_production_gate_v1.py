import hashlib
import json
from pathlib import Path

import pytest

from analysis.hexar_external.acquisition import raw_acquisition_admission_v1 as gate
from analysis.hexar_external.acquisition.raw_runtime_v1 import Runtime,command
from analysis.hexar_external.acquisition.raw_schedule_v1 import make_plan
from analysis.hexar_external.confirmatory_v1.journal import fingerprint

ROOT=Path(__file__).resolve().parents[2]


def unfrozen(root):
    base=root/gate.BASE;base.mkdir(parents=True)
    (base/'freeze_manifest.json').write_text(json.dumps(dict(schema='hexar-confirmatory-freeze/v1',status='CANDIDATE',acquisition_authorized=False)))


def test_unbound_study_cannot_admit_raw_acquisition(tmp_path):
    unfrozen(tmp_path)
    with pytest.raises(ValueError,match='committed prospective acquisition freeze'):
        gate.load_context(tmp_path)


def test_runtime_gate_fails_before_docker_or_output_mutation(tmp_path,monkeypatch):
    unfrozen(tmp_path)
    from analysis.hexar_external.acquisition import raw_runtime_v1 as runtime
    monkeypatch.setattr(runtime.subprocess,'run',lambda *_a,**_k:pytest.fail('no Docker dispatch'))
    monkeypatch.setattr(runtime.subprocess,'check_output',lambda *_a,**_k:pytest.fail('no Docker inspection'))
    record=make_plan('a'*64,1,0)['records'][0]
    with pytest.raises(ValueError,match='committed prospective acquisition freeze'):
        Runtime(tmp_path).capture(record,tmp_path/'attempt')
    assert not (tmp_path/'attempt').exists()


def test_raw_command_preserves_qualified_physics_resources_and_owns_exact_cid(tmp_path):
    config=dict(cpus='3',memory='5g',memory_swap='6g',shared_memory='1g',ros_domain_id=70,
        source_bank_path='bank',capture_root='capture',execution_root='execution',image_id='sha256:'+'e'*64)
    record=make_plan('a'*64,1,0)['records'][0];argv=command(config,record,'f'*64,tmp_path)
    assert argv[:2]==['docker','run']
    for flag,value in (('--network','none'),('--cpus','3'),('--memory','5g'),('--memory-swap','6g'),('--shm-size','1g'),('-e','ROS_DOMAIN_ID=70')):
        assert argv[argv.index(flag)+1]==value
    assert argv[argv.index('--cidfile')+1]==str(tmp_path/'execution'/'attempts'/record['acquisition_id']/'container_id.txt')
    assert argv[-6:]==['/acquisition/run_bound_episode_v1.sh',record['family'],str(record['seed']),record['episode_id'],'raw_confirmation','f'*64]
    assert not list(tmp_path.iterdir())


def test_qualification_binding_is_noncircular_and_detects_runtime_change():
    config=dict(schema=gate.CONFIG_SCHEMA,image_id='sha256:'+'e'*64,qualification=dict(path='report.json',sha256='a'*64))
    binding=lambda c:fingerprint({k:v for k,v in c.items() if k!='qualification'})
    first=binding(config);config['qualification']['sha256']='b'*64
    assert binding(config)==first
    config['image_id']='sha256:'+'a'*64
    assert binding(config)!=first


def test_prior_container_is_never_stopped_or_reused_by_capture_failure(tmp_path,monkeypatch):
    from types import SimpleNamespace
    from analysis.hexar_external.acquisition import raw_runtime_v1 as runtime
    record=make_plan('a'*64,1,0)['records'][0];attempt=tmp_path/'attempt';attempt.mkdir()
    config=dict(cpus='3',memory='5g',memory_swap='6g',shared_memory='1g',ros_domain_id=70,
        source_bank_path='bank',capture_root='capture',execution_root='execution',image_id='sha256:'+'e'*64,
        source_hashes={},execution_source_bank_sha256='a'*64,episode_wall_timeout_seconds=230)
    obj=Runtime(tmp_path);obj.context=lambda *_:dict(config=config,freeze_sha256='f'*64)
    calls=[]
    def call(argv,**kwargs):
        calls.append(argv)
        assert argv==['docker','inspect','crane-'+record['episode_id']]
        return SimpleNamespace(returncode=0,stdout=b'[{"Id":"prior","State":{"Running":true}}]',stderr=b'')
    monkeypatch.setattr(runtime.subprocess,'run',call)
    receipt=obj.capture(record,attempt)
    assert len(calls)==1 and receipt['fresh_container'] is False and receipt['exit_code']==-1
    assert 'prior container' in receipt['error'] and receipt['container_id'] is None


def test_capture_without_docker_preserves_explicit_no_container_receipt(tmp_path,monkeypatch):
    from analysis.hexar_external.acquisition import raw_runtime_v1 as runtime
    record=make_plan('a'*64,1,0)['records'][0];attempt=tmp_path/'attempt';attempt.mkdir()
    config=dict(cpus='3',memory='5g',memory_swap='6g',shared_memory='1g',ros_domain_id=70,
        source_bank_path='bank',capture_root='capture',execution_root='execution',image_id='sha256:'+'e'*64,
        source_hashes={},execution_source_bank_sha256='a'*64,episode_wall_timeout_seconds=230)
    obj=Runtime(tmp_path);obj.context=lambda *_:dict(config=config,freeze_sha256='f'*64)
    monkeypatch.setattr(runtime.subprocess,'run',lambda *_a,**_k:(_ for _ in ()).throw(OSError('fixture unavailable Docker')))
    receipt=obj.capture(record,attempt)
    assert receipt['fresh_container'] is False and receipt['container_id'] is None
    assert receipt['exit_code']==-1 and (attempt/'host_launch_claim.json').exists()
    assert (tmp_path/'capture'/record['episode_id']/'provenance.json').exists()


def test_missing_capture_exports_invalid_attempt_without_native_or_provider_dispatch(tmp_path,monkeypatch):
    from analysis.hexar_external.acquisition import raw_review_v1 as module
    from analysis.hexar_external.acquisition.raw_archive_v1 import digest
    record=make_plan('a'*64,1,0)['records'][0];attempt=tmp_path/'attempt';attempt.mkdir()
    base=tmp_path/'base';base.mkdir()
    (base/'technical_validity.json').write_text(json.dumps(dict(
        machine_predicate_implementation='analysis/hexar_external/acquisition/raw_review_v1.py',
        machine_predicate_sha256=digest(Path(module.__file__)))))
    config=dict(capture_root='capture',image_id='sha256:'+'e'*64,source_hashes={},execution_source_bank_sha256='a'*64)
    obj=module.Review(tmp_path);obj.context=lambda *_:dict(config=config,freeze_sha256='f'*64,base=base,
        excluded_ids=set(),excluded_seeds=set(),excluded_hashes=set())
    monkeypatch.setattr(module.subprocess,'run',lambda *_a,**_k:pytest.fail('no native/provider dispatch'))
    result=obj(record,dict(technical_capture_error='fixture failure'),attempt)
    assert result['technical_valid'] is False and 'NO_RAW_RECORDING' in result['reasons']
    assert (attempt/'raw_archive.json').exists() and (attempt/'validity_receipt.json').exists()
    assert (attempt/'exported_attempt.json').exists()


def test_native_timeout_preserves_partial_transport_bytes_and_owned_cleanup(tmp_path,monkeypatch):
    import subprocess
    from analysis.hexar_external.acquisition import raw_review_v1 as module
    from analysis.hexar_external.acquisition.raw_archive_v1 import digest,read
    record=make_plan('a'*64,1,0)['records'][0];attempt=tmp_path/'attempt';attempt.mkdir()
    base=tmp_path/'base';base.mkdir()
    (base/'technical_validity.json').write_text(json.dumps(dict(
        machine_predicate_implementation='analysis/hexar_external/acquisition/raw_review_v1.py',
        machine_predicate_sha256=digest(Path(module.__file__)))))
    config=dict(capture_root='capture',image_id='sha256:'+'e'*64,source_hashes={},
        execution_source_bank_sha256='a'*64,native_reader=dict(path='reader.py'),source_bank_path='bank',
        memory='5g',native_wall_timeout_seconds=180)
    obj=module.Review(tmp_path);obj.context=lambda *_:dict(config=config,freeze_sha256='f'*64,base=base,
        excluded_ids=set(),excluded_seeds=set(),excluded_hashes=set())
    capture=tmp_path/'capture'/record['episode_id'];capture.mkdir(parents=True)
    receipt=dict(episode_id=record['episode_id'],seed_hidden=record['seed'],family_hidden=record['family'],
        acquisition_phase='raw_confirmation',acquisition_binding_sha256='f'*64,image_id=config['image_id'],
        observed_image_id=config['image_id'],fresh_container=True,exit_code=0,
        method_outputs_generated=False,judge_labels_generated=False)
    (capture/'provenance.json').write_text(json.dumps(receipt))
    (capture/'raw').mkdir();(capture/'raw'/'bag.db3').write_bytes(b'synthetic raw')
    calls=[]
    def dispatch(argv,**kwargs):
        calls.append(argv)
        if argv[:2]==['docker','run']:
            (attempt/'native_reader_id.txt').write_text('b'*64)
            raise subprocess.TimeoutExpired(argv,180,output=b'partial native stdout',stderr=b'partial native stderr')
        assert argv==['docker','kill','b'*64]
    monkeypatch.setattr(module.subprocess,'run',dispatch)
    result=obj(record,receipt,attempt)
    assert result['technical_valid'] is False and len(calls)==2
    assert (attempt/'native_stdout.bin').read_bytes()==b'partial native stdout'
    assert (attempt/'native_stderr.bin').read_bytes()==b'partial native stderr'
    assert 'TimeoutExpired' in result['reasons'][0]
    assert read(attempt/'validity_receipt.json')['method_outcomes_accessed'] is False
