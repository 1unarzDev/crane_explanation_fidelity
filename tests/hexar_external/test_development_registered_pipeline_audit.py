from pathlib import Path
import shutil

import pytest

from analysis.hexar_external.confirmatory_v1.development_registered_pipeline_audit import audit

RUN = Path(__file__).resolve().parents[2]/'manifests/hexar_external/confirmatory_v1/development_registered_pipeline_v1'


def test_actual_registered_pipeline_is_reproduced_without_provider_calls():
    result = audit(RUN)
    assert result['raw_unique_attempts_verified'] == 36
    assert result['paired_counts'] == [0,0,1,0]
    assert result['provider_calls'] == result['confirmatory_N'] == result['alpha_consumed'] == 0


def test_changed_registered_raw_bytes_fail_without_repair(tmp_path):
    copied = tmp_path/'pipeline'
    shutil.copytree(RUN, copied)
    path = next((copied/'initial_judges').glob('*/raw_response.json'))
    path.write_bytes(path.read_bytes()+b' ')
    with pytest.raises(ValueError, match='transport bytes changed'):
        audit(copied)
