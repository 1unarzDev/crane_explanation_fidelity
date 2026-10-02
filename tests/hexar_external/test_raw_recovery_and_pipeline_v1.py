import json
from pathlib import Path

import pytest

from analysis.hexar_external.acquisition.raw_schedule_v1 import make_plan
from analysis.hexar_external.acquisition.raw_recovery_v1 import Recovery
from analysis.hexar_external.acquisition.raw_cohort_pipeline_v1 import execute
from analysis.hexar_external.acquisition.raw_archive_v1 import digest,read


def recovery(root):
    record=make_plan('a'*64,1,0)['records'][0]
    attempt=root/'attempt';attempt.mkdir()
    base=root/'base';base.mkdir()
    (base/'technical_validity.json').write_text(json.dumps(dict(machine_predicate_sha256='d'*64)))
    config=dict(capture_root='capture',image_id='sha256:'+'e'*64,source_hashes={},execution_source_bank_sha256='a'*64)
    obj=Recovery(root);obj.context=lambda *_:dict(config=config,freeze_sha256='f'*64,base=base,
        excluded_ids=set(),excluded_seeds=set(),excluded_hashes=set())
    return obj,record,attempt


def test_interrupted_raw_claim_exports_empty_invalid_archive_without_replay(tmp_path,monkeypatch):
    from analysis.hexar_external.acquisition import raw_recovery_v1 as module
    obj,record,attempt=recovery(tmp_path)
    monkeypatch.setattr(module.subprocess,'run',lambda *_a,**_k:pytest.fail('no replay or native dispatch'))
    exported=obj.export_invalid(record,attempt)
    validity=read(tmp_path/exported['validity_receipt_path']);archive=read(tmp_path/exported['raw_archive_path'])
    assert validity['technical_valid'] is False and validity['reasons']==['HOST_INTERRUPTION_AFTER_DURABLE_CLAIM']
    assert validity['method_outcomes_accessed'] is False and validity['independent_reset_measured'] is False
    assert archive['bag_missing'] and archive['fresh_container'] is False
    assert obj.export_invalid(record,attempt)==exported


def test_recovery_cleans_only_exact_recorded_container_ids(tmp_path,monkeypatch):
    from analysis.hexar_external.acquisition import raw_recovery_v1 as module
    obj,record,attempt=recovery(tmp_path)
    (attempt/'container_id.txt').write_text('a'*64)
    (attempt/'native_reader_id.txt').write_text('b'*64)
    calls=[]
    monkeypatch.setattr(module.subprocess,'run',lambda argv,**kwargs:calls.append(argv))
    obj.export_invalid(record,attempt)
    assert calls==[['docker','kill','a'*64],['docker','kill','b'*64]]


def test_invalid_container_identity_never_authorizes_name_based_cleanup(tmp_path,monkeypatch):
    from analysis.hexar_external.acquisition import raw_recovery_v1 as module
    obj,record,attempt=recovery(tmp_path);(attempt/'container_id.txt').write_text('prior-container-name')
    monkeypatch.setattr(module.subprocess,'run',lambda *_a,**_k:pytest.fail('no unknown container cleanup'))
    obj.export_invalid(record,attempt)


def test_prior_native_and_export_artifacts_remain_unchanged_on_interruption(tmp_path,monkeypatch):
    from analysis.hexar_external.acquisition import raw_recovery_v1 as module
    obj,record,attempt=recovery(tmp_path)
    previous=attempt/'exported_attempt.json';previous.write_text('{"prior":"retained artifact"}')
    before=digest(previous)
    monkeypatch.setattr(module.subprocess,'run',lambda *_a,**_k:pytest.fail('no replay'))
    exported=obj.export_invalid(record,attempt)
    assert digest(previous)==before and exported!=read(previous)
    assert (attempt/'recovered_exported_attempt.json').exists()


def test_changed_recovered_raw_bytes_prevent_resume(tmp_path,monkeypatch):
    from analysis.hexar_external.acquisition import raw_recovery_v1 as module
    obj,record,attempt=recovery(tmp_path)
    monkeypatch.setattr(module.subprocess,'run',lambda *_a,**_k:pytest.fail('no replay'))
    exported=obj.export_invalid(record,attempt)
    archive=read(tmp_path/exported['raw_archive_path'])
    (tmp_path/archive['capture_provenance']['path']).write_text('{}')
    with pytest.raises(ValueError):obj.export_invalid(record,attempt)


def test_unbound_complete_pipeline_never_launches_or_seals(tmp_path,monkeypatch):
    from analysis.hexar_external.acquisition import raw_runtime_v1 as module
    base=tmp_path/'manifests/hexar_external/confirmatory_v1';base.mkdir(parents=True)
    (base/'freeze_manifest.json').write_text(json.dumps(dict(schema='hexar-confirmatory-freeze/v1',status='CANDIDATE')))
    monkeypatch.setattr(module.subprocess,'run',lambda *_a,**_k:pytest.fail('no Docker dispatch'))
    with pytest.raises(ValueError,match='committed prospective acquisition freeze'):execute(tmp_path)
    assert not (base/'raw_cohort_seal.json').exists()
