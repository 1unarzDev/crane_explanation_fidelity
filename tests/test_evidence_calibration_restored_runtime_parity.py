import json
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analysis'))
from audit_evidence_calibration_restored_runtime_parity import probe,PRIMITIVE
from stage_evidence_calibration_workspace import inventory
from evidence_calibration_io import canonical_sha256


def identity(workspace):
    result={'inventory':inventory(workspace)};result['workspace_sha256']=canonical_sha256(result);return result


def test_stdlib_probe_executes_in_original_registered_namespace(tmp_path):
    result=probe(tmp_path,identity(tmp_path),['-c',PRIMITIVE],None)
    rows=json.loads(result.stdout)
    assert rows['hypot']==5 and rows['sqlite']==7 and rows['decimal']=='0.3'
    assert all(rows[key] for key in ('gzip_roundtrip','bz2_roundtrip','lzma_roundtrip'))


def test_invalid_restored_root_never_falls_back_to_host(tmp_path):
    with pytest.raises(ValueError,match='bind seam'):
        probe(tmp_path,identity(tmp_path),['-c','print(1)'],tmp_path/'missing-runtime')


def test_runtime_failure_is_not_a_successful_parity_result(tmp_path):
    with pytest.raises(ValueError,match='probe failed'):
        probe(tmp_path,identity(tmp_path),['-c',"raise RuntimeError('synthetic')"],None)
