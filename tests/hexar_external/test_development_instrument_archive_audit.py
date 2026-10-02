import shutil
from pathlib import Path

import pytest

from analysis.hexar_external.confirmatory_v1.development_instrument_archive_audit import audit

RUN = Path(__file__).resolve().parents[2] / 'manifests/hexar_external/confirmatory_v1/development_v4_complete_instrument_screen_v1'


def test_completed_screen_reproduces_raw_journal_and_retains_ambiguity():
    result = audit(RUN)
    assert result['exact_initial_agreements'] == result['raw_attempts_verified'] == 256
    assert result['unresolved_dispositions'] == 2
    assert result['C_calls'] == result['provider_calls'] == result['confirmatory_N'] == 0


def test_changed_raw_archive_is_detected_without_calls_or_repairs(tmp_path):
    copied = tmp_path / 'screen'
    shutil.copytree(RUN, copied)
    path = next(copied.glob('*/raw_final.json'))
    path.write_bytes(path.read_bytes() + b' ')
    with pytest.raises(ValueError, match='raw response archive changed'):
        audit(copied)
