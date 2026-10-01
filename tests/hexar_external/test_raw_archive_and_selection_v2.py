import json
from pathlib import Path

import pytest

from analysis.hexar_external.acquisition.raw_archive_v1 import create, digest, verify
from analysis.hexar_external.confirmatory_v1.seal_archived_attempts_v2 import select

FREEZE='f'*64
PREDICATE='d'*64
IMAGE='sha256:'+'e'*64


def fixture(root,order=1,with_bag=True,phase='raw_confirmation'):
    identity=f'hexar-tiago-confirm-'+'a'*16+f'-success-{order:04d}'
    allocated=dict(acquisition_id=identity,episode_id=identity,family='success',seed=100+order,attempt_order=order)
    folder=root/identity;folder.mkdir()
    receipt=root/f'capture-{order}.json'
    receipt.write_text(json.dumps(dict(episode_id=identity,seed_hidden=100+order,family_hidden='success',
        acquisition_phase=phase,acquisition_binding_sha256=FREEZE,image_id=IMAGE,fresh_container=True,
        method_outputs_generated=False,judge_labels_generated=False)))
    for name in ('acquisition_intent.json','episode.json'):
        (folder/name).write_text(json.dumps(dict(phase=phase,acquisition_binding_sha256=FREEZE)))
    if with_bag:
        (folder/'raw').mkdir()
        (folder/'raw'/f'bag-{order}.db3').write_bytes(f'synthetic capture bytes {order}'.encode())
        (folder/'raw'/'metadata.yaml').write_text('synthetic metadata')
        for name in ('controller_start.json','controller_end.json'):(folder/name).write_text('{}')
    pin=dict(path=receipt.name,sha256=digest(receipt))
    return allocated,folder,pin


def archived(root,order=1,with_bag=True,technical_valid=None):
    allocated,folder,pin=fixture(root,order,with_bag)
    archive=root/f'archive-{order}.json'
    create(root,archive,folder,allocated,FREEZE,pin,IMAGE)
    if technical_valid is None:technical_valid=with_bag
    receipt=root/f'validity-{order}.json'
    validity=dict(schema='hexar-frozen-raw-validity/v1',acquisition_id=allocated['acquisition_id'],
        freeze_sha256=FREEZE,raw_archive_sha256=digest(archive),validity_predicate_sha256=PREDICATE,
        method_outcomes_accessed=False,technical_valid=technical_valid,
        independent_reset_measured=with_bag,reasons=[] if technical_valid else ['MISSING_OR_INVALID_CAPTURE'])
    receipt.write_text(json.dumps(validity))
    attempt=dict(allocated,raw_archive_path=archive.name,raw_archive_sha256=digest(archive),
        validity_receipt_path=receipt.name,validity_receipt_sha256=digest(receipt),validity_predicate_sha256=PREDICATE)
    return allocated,attempt,validity


def selection(root,records,attempts,quota=1,excluded_raw_hashes=()):
    plan=dict(phase='confirmation',records=records)
    return select(root,plan,attempts,quota,len(records),['success'],FREEZE,PREDICATE,IMAGE,
                  excluded_raw_hashes=excluded_raw_hashes)


def test_missing_bag_has_real_archive_hash_and_can_be_retained_invalid_attempt(tmp_path):
    r1,a1,_=archived(tmp_path,1,False);r2,a2,_=archived(tmp_path,2,True)
    archive=json.loads((tmp_path/a1['raw_archive_path']).read_text())
    assert archive['bag_missing'] and archive['bag_sha256s']==[]
    assert a1['raw_archive_sha256']==digest(tmp_path/a1['raw_archive_path'])
    selected,dispositions=selection(tmp_path,[r1,r2],[a1,a2])
    assert len(selected)==1 and selected[0]['acquisition_id']==r2['acquisition_id']
    assert [r['disposition'] for r in dispositions]==['TECHNICAL_INVALID','SELECTED']


def test_missing_bag_cannot_be_declared_valid(tmp_path):
    r,a,_=archived(tmp_path,with_bag=False,technical_valid=True)
    with pytest.raises(ValueError,match='actual bag'):selection(tmp_path,[r],[a])


def test_absent_reset_cannot_support_valid_recording(tmp_path):
    r,a,v=archived(tmp_path);v['independent_reset_measured']=False
    p=tmp_path/a['validity_receipt_path'];p.write_text(json.dumps(v));a['validity_receipt_sha256']=digest(p)
    with pytest.raises(ValueError,match='independent reset'):selection(tmp_path,[r],[a])


def test_invalid_bag_never_silently_dropped_or_reserve_expanded(tmp_path):
    r,a,_=archived(tmp_path,with_bag=False)
    with pytest.raises(ValueError,match='reserve exhausted'):selection(tmp_path,[r],[a])


@pytest.mark.parametrize('which',['phase','binding','image','exposure'])
def test_wrong_original_provenance_fails_before_archive_creation(tmp_path,which):
    r,folder,pin=fixture(tmp_path)
    p=tmp_path/pin['path'];v=json.loads(p.read_text())
    if which=='phase':v['acquisition_phase']='development_adapter_qualification'
    elif which=='binding':v['acquisition_binding_sha256']='a'*64
    elif which=='image':v['image_id']='wrong-image'
    else:v['method_outputs_generated']=True
    p.write_text(json.dumps(v));pin['sha256']=digest(p)
    with pytest.raises(ValueError,match='untouched confirmation'):
        create(tmp_path,tmp_path/'archive.json',folder,r,FREEZE,pin,IMAGE)
    assert not (tmp_path/'archive.json').exists()


def test_captured_development_metadata_cannot_be_relabelled(tmp_path):
    r,folder,pin=fixture(tmp_path)
    (folder/'episode.json').write_text(json.dumps(dict(phase='development_only',acquisition_binding_sha256=FREEZE)))
    with pytest.raises(ValueError,match='cannot be relabeled'):
        create(tmp_path,tmp_path/'archive.json',folder,r,FREEZE,pin,IMAGE)


def test_unknown_or_semantic_file_cannot_enter_raw_archive(tmp_path):
    r,folder,pin=fixture(tmp_path);(folder/'answers.json').write_text('{}')
    with pytest.raises(ValueError,match='semantic artifact'):
        create(tmp_path,tmp_path/'archive.json',folder,r,FREEZE,pin,IMAGE)


def test_changed_raw_capture_or_new_artifact_blocks_sealing(tmp_path):
    r,a,_=archived(tmp_path)
    (tmp_path/r['episode_id']/'raw'/'bag-1.db3').write_bytes(b'changed capture')
    with pytest.raises(ValueError,match='inventory or bytes changed'):selection(tmp_path,[r],[a])


def test_actual_development_bag_hash_is_checked_in_archive_not_only_wrapper_hash(tmp_path):
    r,a,_=archived(tmp_path)
    bag=digest(tmp_path/r['episode_id']/'raw'/'bag-1.db3')
    assert bag!=a['raw_archive_sha256']
    with pytest.raises(ValueError,match='development recording bytes'):
        selection(tmp_path,[r],[a],excluded_raw_hashes={bag})


def test_duplicate_recording_content_between_independent_claims_rejected(tmp_path):
    r1,a1,_=archived(tmp_path,1,True,False)
    r2,folder,pin=fixture(tmp_path,2,True)
    (folder/'raw'/'bag-2.db3').write_bytes((tmp_path/r1['episode_id']/'raw'/'bag-1.db3').read_bytes())
    archive=tmp_path/'archive-2.json';create(tmp_path,archive,folder,r2,FREEZE,pin,IMAGE)
    v=tmp_path/'validity-2.json';v.write_text(json.dumps(dict(schema='hexar-frozen-raw-validity/v1',acquisition_id=r2['acquisition_id'],freeze_sha256=FREEZE,raw_archive_sha256=digest(archive),validity_predicate_sha256=PREDICATE,method_outcomes_accessed=False,technical_valid=True,independent_reset_measured=True,reasons=[])))
    a2=dict(r2,raw_archive_path=archive.name,raw_archive_sha256=digest(archive),validity_receipt_path=v.name,validity_receipt_sha256=digest(v),validity_predicate_sha256=PREDICATE)
    with pytest.raises(ValueError,match='recording bytes duplicated'):selection(tmp_path,[r1,r2],[a1,a2])


@pytest.mark.parametrize('field,value',[('method_outcomes_accessed',True),('freeze_sha256','a'*64),('raw_archive_sha256','a'*64),('validity_predicate_sha256','a'*64)])
def test_native_disposition_must_bind_same_frozen_outcome_blind_attempt(tmp_path,field,value):
    r,a,v=archived(tmp_path);v[field]=value
    p=tmp_path/a['validity_receipt_path'];p.write_text(json.dumps(v));a['validity_receipt_sha256']=digest(p)
    with pytest.raises(ValueError,match='native validity binding'):selection(tmp_path,[r],[a])


def test_no_attempts_allowed_after_frozen_family_valid_quota(tmp_path):
    r1,a1,_=archived(tmp_path,1);r2,a2,_=archived(tmp_path,2)
    with pytest.raises(ValueError,match='quota completed'):selection(tmp_path,[r1,r2],[a1,a2])


def test_archive_is_exclusive_and_cannot_replace_original_capture(tmp_path):
    r,a,_=archived(tmp_path)
    archive=tmp_path/a['raw_archive_path'];folder=tmp_path/r['episode_id']
    pin=json.loads(archive.read_text())['capture_provenance']
    with pytest.raises(FileExistsError):create(tmp_path,archive,folder,r,FREEZE,pin,IMAGE)


def test_archive_manifest_cannot_be_written_inside_original_raw_capture(tmp_path):
    r,folder,pin=fixture(tmp_path)
    with pytest.raises(ValueError,match='outside immutable'):
        create(tmp_path,folder/'archive.json',folder,r,FREEZE,pin,IMAGE)
    assert not (folder/'archive.json').exists()


def test_failed_sqlite_sidecars_are_retained_without_fabricated_bag(tmp_path):
    r,folder,pin=fixture(tmp_path,with_bag=False)
    (folder/'raw').mkdir();(folder/'raw'/'failed.db3-wal').write_bytes(b'failed captured sqlite journal')
    archive=tmp_path/'archive.json';value=create(tmp_path,archive,folder,r,FREEZE,pin,IMAGE)
    assert value['bag_missing'] and value['bag_sha256s']==[]
    assert any(f['path'].endswith('.db3-wal') for f in value['artifacts'])
    assert verify(tmp_path,archive.name,digest(archive),FREEZE,r,IMAGE)==value
