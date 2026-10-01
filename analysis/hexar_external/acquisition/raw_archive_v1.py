"""Hash-bound raw attempt archives, including failed launches with no bag.

Packaging is not technical qualification or acquisition authorization. Final
native validity, frozen runtime/source/image and freshness admission remain
separate. Never fabricates a recording hash for an absent recording.
"""
import hashlib
from pathlib import Path

from ..confirmatory_v1.journal import exclusive_json
from ..confirmatory_v1.strict_json import load

MAX_BYTES = 32 * 1024 * 1024
HOST_FILES = {'acquisition_intent.json','episode.json','provenance.json','host_execution.log',
              'runtime.log','readiness.log','recorder.log','driver.log','runtime_probe.json',
              'controller_start.json','controller_end.json'}


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def rooted(root,name):
    root=Path(root).resolve();path=(root/name).resolve();path.relative_to(root)
    return path


def read(path):return load(Path(path).read_bytes(),MAX_BYTES)


def file_records(root,folder):
    """Archive original capture artifacts only; derived evidence has its own pins."""
    rows=[]
    folder=Path(folder).resolve();folder.relative_to(Path(root).resolve())
    for path in sorted(folder.rglob('*')):
        if not path.is_file():continue
        resolved=path.resolve();resolved.relative_to(folder)
        relative=path.relative_to(folder)
        allowed=(len(relative.parts)==1 and relative.name in HOST_FILES) or (
            len(relative.parts)==2 and relative.parts[0]=='raw'
            and (relative.name=='metadata.yaml' or relative.suffix in ('.db3','.mcap')
                 or relative.name.endswith(('.db3-wal','.db3-shm','.db3-journal','.mcap.active'))))
        if not allowed:raise ValueError('unrecognized or semantic artifact in raw capture archive: '+str(relative))
        rows.append(dict(path=str(resolved.relative_to(Path(root).resolve())),size=resolved.stat().st_size,
                         sha256=digest(resolved)))
    return rows


def create(root, destination, folder, allocated, freeze_sha256, capture_pin,
           expected_image, excluded_ids=(),excluded_seeds=(),excluded_raw_hashes=()):
    """Retain a real raw file inventory even when technical capture failed."""
    root=Path(root).resolve();folder=Path(folder).resolve();folder.relative_to(root)
    destination=rooted(root,destination)
    if destination.is_relative_to(folder):
        raise ValueError('raw archive manifest must be outside immutable original capture folder')
    if not isinstance(freeze_sha256,str) or len(freeze_sha256)!=64:
        raise ValueError('exact acquisition freeze hash required')
    if (allocated['acquisition_id']!=allocated['episode_id']
            or allocated['acquisition_id'] in excluded_ids or allocated['seed'] in excluded_seeds):
        raise ValueError('development identity/seed cannot enter raw confirmation archive')
    receipt_path=rooted(root,capture_pin['path'])
    if digest(receipt_path)!=capture_pin['sha256']:raise ValueError('capture provenance pin changed')
    receipt=read(receipt_path)
    if (receipt.get('episode_id')!=allocated['episode_id'] or receipt.get('seed_hidden')!=allocated['seed']
            or receipt.get('family_hidden')!=allocated['family']
            or receipt.get('acquisition_phase')!='raw_confirmation'
            or receipt.get('acquisition_binding_sha256')!=freeze_sha256
            or receipt.get('image_id')!=expected_image or type(receipt.get('fresh_container')) is not bool
            or receipt.get('method_outputs_generated') is not False
            or receipt.get('judge_labels_generated') is not False):
        raise ValueError('original raw capture provenance is not frozen untouched confirmation')
    files=file_records(root,folder)
    bags=[r['sha256'] for r in files if Path(r['path']).suffix in ('.db3','.mcap')]
    if set(bags)&set(excluded_raw_hashes):raise ValueError('development recording bytes reused')
    # Never repair or relabel existing metadata. Missing records remain absent
    # and must make the final technical reviewer invalid, not be filled here.
    for name in ('acquisition_intent.json','episode.json'):
        p=folder/name
        if p.exists():
            original=read(p)
            if original.get('phase')!='raw_confirmation' or original.get('acquisition_binding_sha256')!=freeze_sha256:
                raise ValueError('captured development/runtime metadata cannot be relabeled')
    value=dict(schema='hexar-raw-attempt-archive/v1',phase='raw_confirmation',freeze_sha256=freeze_sha256,
        allocated=allocated,capture_provenance=capture_pin,image_id=expected_image,
        folder=str(folder.relative_to(root)),artifacts=files,bag_sha256s=bags,
        bag_missing=not bool(bags),fresh_container=receipt['fresh_container'],semantic_outputs_generated=False,
        independently_validated=False,scope='Raw packaging only; every attempt needs frozen native technical disposition.')
    exclusive_json(destination,value)
    return value


def verify(root,path,expected_sha256,freeze_sha256,allocated,expected_image,excluded_raw_hashes=()):
    path=rooted(root,path)
    if digest(path)!=expected_sha256:raise ValueError('raw attempt archive changed')
    archive=read(path)
    if (archive.get('schema')!='hexar-raw-attempt-archive/v1' or archive.get('phase')!='raw_confirmation'
            or archive.get('freeze_sha256')!=freeze_sha256 or archive.get('allocated')!=allocated
            or archive.get('image_id')!=expected_image or archive.get('semantic_outputs_generated') is not False
            or archive.get('independently_validated') is not False):
        raise ValueError('raw archive has wrong allocation/freeze/provenance')
    folder=rooted(root,archive['folder'])
    if file_records(root,folder)!=archive['artifacts']:
        raise ValueError('raw artifact inventory or bytes changed')
    pin=archive['capture_provenance'];receipt_path=rooted(root,pin['path'])
    if digest(receipt_path)!=pin['sha256']:raise ValueError('original capture provenance changed')
    receipt=read(receipt_path)
    if (receipt.get('episode_id')!=allocated['episode_id'] or receipt.get('seed_hidden')!=allocated['seed']
            or receipt.get('family_hidden')!=allocated['family'] or receipt.get('image_id')!=expected_image
            or type(receipt.get('fresh_container')) is not bool or receipt.get('acquisition_phase')!='raw_confirmation'
            or receipt.get('acquisition_binding_sha256')!=freeze_sha256
            or receipt.get('method_outputs_generated') is not False or receipt.get('judge_labels_generated') is not False):
        raise ValueError('capture provenance violates raw confirmation binding')
    if archive.get('fresh_container')!=receipt['fresh_container']:
        raise ValueError('original container presence differs from raw archive')
    bags=[r['sha256'] for r in archive['artifacts'] if Path(r['path']).suffix in ('.db3','.mcap')]
    if archive.get('bag_sha256s')!=bags or archive.get('bag_missing')!= (not bool(bags)):
        raise ValueError('raw bag presence/hash inventory differs')
    if set(bags)&set(excluded_raw_hashes):raise ValueError('development recording bytes reused')
    for name in ('acquisition_intent.json','episode.json'):
        p=folder/name
        if p.exists():
            original=read(p)
            if original.get('phase')!='raw_confirmation' or original.get('acquisition_binding_sha256')!=freeze_sha256:
                raise ValueError('captured development metadata cannot enter raw confirmation')
    return archive
