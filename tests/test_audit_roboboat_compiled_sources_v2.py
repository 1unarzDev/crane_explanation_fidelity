from pathlib import Path
import hashlib
from audit_roboboat_compiled_sources_v2 import map_document
from roboboat_owned_player_bundle_v1 import binding


def setup(tmp_path):
    old=tmp_path/'parent';new=tmp_path/'current'
    for root in (old,new):
        p=root/'Assets/publisher.cs';p.parent.mkdir(parents=True);p.write_text('exact compiler source')
    p=old/'Assets/publisher.cs';q=new/'Assets/publisher.cs'
    d={'name':str(p),'algorithm':'8829d00f-11b8-4213-878b-770e8597ac16','checksum':hashlib.sha256(p.read_bytes()).hexdigest()}
    return old,new,p,q,d


def test_exact_bound_compiler_root_mapping(tmp_path):
    old,new,p,q,d=setup(tmp_path)
    mapped=map_document(d,new,old,{str(p):binding(p)},{str(q):binding(q)})
    assert mapped['status']=='MATCH' and mapped['source']==binding(q) and mapped['compiler_source']==binding(p)


def test_no_basename_or_suffix_guess(tmp_path):
    old,new,p,q,d=setup(tmp_path);d['name']=str(tmp_path/'other/Assets/publisher.cs')
    assert map_document(d,new,old,{str(p):binding(p)},{str(q):binding(q)}) is None


def test_current_copy_must_equal_parent_compiler_bytes(tmp_path):
    old,new,p,q,d=setup(tmp_path);q.write_text('changed current source')
    assert map_document(d,new,old,{str(p):binding(p)},{str(q):binding(q)})['status']=='IMPORTED_CACHE_SOURCE_DIFFERS'


def test_correct_sources_cannot_override_wrong_compiler_checksum(tmp_path):
    old,new,p,q,d=setup(tmp_path);d['checksum']='0'*64
    assert map_document(d,new,old,{str(p):binding(p)},{str(q):binding(q)})['status']=='IMPORTED_CACHE_DOCUMENT_MISMATCH'


def test_unbound_source_is_not_read_or_promoted(tmp_path):
    old,new,p,q,d=setup(tmp_path);p.unlink();q.unlink()
    assert map_document(d,new,old,{}, {})['status']=='IMPORTED_CACHE_SOURCE_NOT_BOUND'
