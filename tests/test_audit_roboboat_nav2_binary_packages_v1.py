import io
import tarfile
import pytest
from audit_roboboat_nav2_binary_packages_v1 import deb_files, stanzas


def ar_payload(member_path='opt/ros/jazzy/include/public.hpp',content=b'public header'):
    stream=io.BytesIO()
    with tarfile.open(fileobj=stream,mode='w:gz') as tar:
        entry=tarfile.TarInfo(member_path);entry.size=len(content);tar.addfile(entry,io.BytesIO(content))
    payload=stream.getvalue()
    header=('data.tar.gz/').ljust(16)+str(0).ljust(12)+str(0).ljust(6)+str(0).ljust(6)+str(0o644).ljust(8)+str(len(payload)).ljust(10)+'`\n'
    return b'!<arch>\n'+header.encode()+payload+(b'\n' if len(payload)%2 else b'')


def test_exact_deb_payload_mapping_and_signed_trust_not_invented():
    assert deb_files(ar_payload())=={'/opt/ros/jazzy/include/public.hpp':b'public header'}


@pytest.mark.parametrize('raw',[b'notdeb',b'!<arch>\ninvalid'])
def test_invalid_debian_archive_rejected(raw):
    with pytest.raises(ValueError):deb_files(raw)


def test_debian_payload_traversal_rejected():
    with pytest.raises(ValueError,match='unsafe'):deb_files(ar_payload('../escape'))


def test_package_index_requires_explicit_identity_fields():
    parsed=stanzas(b'Package: public-package\nVersion: 1.3.12-1noble.20260615.165600\nSHA256: abc\n\n')
    assert parsed==[{'Package':'public-package','Version':'1.3.12-1noble.20260615.165600','SHA256':'abc'}]
