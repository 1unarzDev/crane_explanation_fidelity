import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import pytest
from audit_roboboat_compiled_sources_v1 import compare_document


def test_source_corruption_and_outside_root_are_retained(tmp_path):
    source = tmp_path/'Code.cs'; source.write_bytes(b'class Code {}\n')
    doc = {'name': str(source), 'algorithm': '8829d00f-11b8-4213-878b-770e8597ac16',
           'checksum': hashlib.sha256(source.read_bytes()).hexdigest()}
    assert compare_document(doc, tmp_path)['status'] == 'MATCH'
    source.write_bytes(b'class Different {}\n')
    assert compare_document(doc, tmp_path)['status'] == 'MISMATCH'
    assert compare_document(doc, tmp_path/'other')['status'] == 'OUTSIDE_DECLARED_PROJECT_NOT_READ'
    source.unlink()
    assert compare_document(doc, tmp_path)['status'] == 'SOURCE_UNAVAILABLE'


@pytest.fixture(scope='module')
def compiled(tmp_path_factory):
    if not shutil.which('dotnet'): pytest.skip('dotnet SDK required')
    root = tmp_path_factory.mktemp('pdb')
    utility = Path(__file__).resolve().parents[1]/'analysis/portable_pdb_audit_v1'
    shutil.copytree(utility, root/'utility', ignore=shutil.ignore_patterns('bin','obj'))
    subprocess.run(['dotnet','build',str(root/'utility/portable_pdb_audit_v1.csproj'),'-o',str(root/'audit')], check=True, capture_output=True)
    for name in ['one','two']:
        folder = root/name; folder.mkdir()
        (folder/'sample.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework></PropertyGroup></Project>')
        (folder/'Sample.cs').write_text('public class '+name+' {}\n')
        subprocess.run(['dotnet','build',str(folder/'sample.csproj'),'-o',str(folder/'out')],check=True,capture_output=True)
    return root


def run(compiled, assembly, pdb):
    return subprocess.run(['dotnet',str(compiled/'audit/portable_pdb_audit_v1.dll'),str(assembly),str(pdb)],capture_output=True,text=True)


def test_real_metadata_id_checksum_and_document_binding(compiled):
    out = compiled/'one/out'
    call = run(compiled,out/'sample.dll',out/'sample.pdb')
    assert call.returncode == 0, call.stderr
    data = json.loads(call.stdout)
    assert data['assembly_pdb_identity_match'] and data['pe_pdb_checksum_match']
    doc = next(d for d in data['documents'] if d['name'].endswith('/Sample.cs'))
    assert compare_document(doc,compiled/'one')['status'] == 'MATCH'


def test_swapped_valid_pdb_and_damaged_metadata_rejected(compiled):
    call = run(compiled,compiled/'one/out/sample.dll',compiled/'two/out/sample.pdb')
    assert call.returncode != 0
    assert not json.loads(call.stdout)['assembly_pdb_identity_match']
    bad = compiled/'bad.pdb'; bad.write_bytes(b'bad metadata')
    assert run(compiled,compiled/'one/out/sample.dll',bad).returncode != 0
