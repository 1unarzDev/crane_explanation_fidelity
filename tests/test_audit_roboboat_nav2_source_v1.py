import hashlib
import io
import json
from pathlib import Path
import tarfile
import pytest
import audit_roboboat_nav2_source_v1 as audit


def archive(files):
    stream=io.BytesIO()
    with tarfile.open(fileobj=stream,mode='w:gz') as tar:
        for path,raw in files.items():
            row=tarfile.TarInfo('archive-root/'+path);row.size=len(raw);tar.addfile(row,io.BytesIO(raw))
    return stream.getvalue()


def observation(tmp_path):
    receipt=tmp_path/'controller.container-id';receipt.write_text('construction-container')
    header=tmp_path/'stopped_goal_checker.hpp';header.write_text('public header')
    result={'schema':'roboboat-deployed-nav2-observation/v1','container_id':'construction-container',
        'image_id':'sha256:construction','container_id_receipt':audit.binding(receipt),
        'package_versions':'\n'.join('\t'.join([name,'1.3.12-1noble.20260615.123456',name,'1.3.12-1noble.20260615.123456'])
            for name in ['ros-jazzy-'+p.replace('_','-') for p in audit.PACKAGES]),
        'installed_files':[{'container_path':'/opt/ros/jazzy/include/nav2_controller/plugins/stopped_goal_checker.hpp',
                           'snapshot':str(header),'sha256':audit.digest(header.read_bytes()),'bytes':len(header.read_bytes())}]}
    path=tmp_path/'observation.json';path.write_text(json.dumps(result));return path


def getter(url):
    if '/git/ref/tags/' in url:
        tag=url.split('/git/ref/tags/')[1]
        return json.dumps({'ref':'refs/tags/'+tag,'object':{'type':'commit','sha':'a'*40}}).encode()
    return archive({'include/nav2_controller/plugins/stopped_goal_checker.hpp':b'public header','src/implementation.cpp':b'public code'})


def test_exact_installed_header_comparison_never_claims_debian_or_binary_authentication(tmp_path):
    path=observation(tmp_path);out=tmp_path/'audit'
    result=audit.audit(path,out,getter=getter)
    assert result['byte_identical_count']==1 and result['byte_different_count']==0
    assert len(result['releases'])==8
    assert result['authentication']['installed_binary_source_build_equivalence']=='NOT_ESTABLISHED'
    assert result['authentication']['exact_debian_source_package']=='NOT_RETRIEVED_OR_SIGNATURE_AUTHENTICATED'
    assert not result['call_readiness']
    with pytest.raises(FileExistsError):audit.audit(path,out,getter=getter)


def test_altered_installed_bytes_refused_before_network(tmp_path):
    path=observation(tmp_path);(tmp_path/'stopped_goal_checker.hpp').write_text('changed')
    with pytest.raises(ValueError,match='snapshot changed'):
        audit.audit(path,tmp_path/'audit',getter=lambda _:pytest.fail('network before source check'))


def test_mismatched_package_version_refused(tmp_path):
    path=observation(tmp_path);v=json.loads(path.read_text());v['package_versions']=v['package_versions'].replace('1.3.12','1.3.13');path.write_text(json.dumps(v))
    with pytest.raises(ValueError,match='release does not match'):audit.audit(path,tmp_path/'audit',getter=getter)


def test_unsafe_archive_paths_refused():
    with pytest.raises(ValueError,match='unsafe archive'):audit.archive_files(archive({'../escaped':b'bad'}))


def test_mapping_keeps_libraries_out_of_source_equality_claim():
    assert audit.resolve_installed('/opt/ros/jazzy/lib/libstopped_goal_checker.so') is None
    assert audit.resolve_installed('/opt/ros/jazzy/include/nav2_controller/plugins/stopped_goal_checker.hpp')==('nav2_controller','include/nav2_controller/plugins/stopped_goal_checker.hpp')
