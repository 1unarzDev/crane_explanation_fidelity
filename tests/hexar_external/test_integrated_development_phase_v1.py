import json
from pathlib import Path

import pytest

from analysis.hexar_external.acquisition.raw_schedule_v1 import make_plan,validate_plan
from analysis.hexar_external.acquisition.raw_runtime_v1 import Runtime,command
from analysis.hexar_external.acquisition.raw_archive_v1 import create,digest,verify
from analysis.hexar_external.acquisition.qualify_integrated_raw_v1 import context


def test_development_schedule_has_distinct_seed_namespace_and_permanent_ids():
    raw=make_plan('a'*64,1,1);dev=make_plan('a'*64,1,1,phase='development')
    assert validate_plan(dev) and dev['phase']=='development'
    assert all(r['episode_id'].startswith('hexar-tiago-dev-') for r in dev['records'])
    assert not {r['seed'] for r in raw['records']}&{r['seed'] for r in dev['records']}
    assert dev['confirmation_authorized'] is False


def test_production_context_cannot_authorize_development_mode(tmp_path):
    obj=Runtime(tmp_path,phase='development_adapter_qualification')
    with pytest.raises(ValueError,match='separate committed development admission'):obj.context({},tmp_path)


def test_uncommitted_development_declaration_never_authorizes_capture(tmp_path):
    base=tmp_path/'manifests/hexar_external/acquisition/development_integrated_raw_v19';base.mkdir(parents=True)
    (base/'declaration.json').write_text(json.dumps(dict(phase='development_only',confirmation_authorized=True)))
    with pytest.raises(ValueError,match='committed fixed-six'):context(tmp_path)


def test_development_metadata_can_archive_only_under_explicit_development_phase(tmp_path):
    record=make_plan('a'*64,1,1,phase='development')['records'][0]
    folder=tmp_path/record['episode_id'];folder.mkdir()
    receipt=folder/'provenance.json';receipt.write_text(json.dumps(dict(episode_id=record['episode_id'],
        seed_hidden=record['seed'],family_hidden=record['family'],acquisition_phase='development_adapter_qualification',
        acquisition_binding_sha256='f'*64,image_id='sha256:'+'e'*64,fresh_container=True,
        method_outputs_generated=False,judge_labels_generated=False)))
    pin=dict(path=str(receipt.relative_to(tmp_path)),sha256=digest(receipt))
    with pytest.raises(ValueError,match='untouched confirmation'):
        create(tmp_path,'bad.json',folder,record,'f'*64,pin,'sha256:'+'e'*64)
    archive=tmp_path/'dev.json';value=create(tmp_path,archive,folder,record,'f'*64,pin,'sha256:'+'e'*64,
        expected_phase='development_adapter_qualification')
    assert value['phase']=='development_adapter_qualification'
    with pytest.raises(ValueError,match='wrong allocation'):verify(tmp_path,archive.name,digest(archive),'f'*64,record,'sha256:'+'e'*64)
    assert verify(tmp_path,archive.name,digest(archive),'f'*64,record,'sha256:'+'e'*64,
        expected_phase='development_adapter_qualification')==value
