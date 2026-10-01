import copy
import hashlib
import json
from pathlib import Path

import pytest

from analysis.hexar_external.acquisition.technical_batch_candidate import (
    build, digest, verify_capture,
)

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'manifests/hexar_external/acquisition'


def capture(tmp_path):
    source = b'captured executed driver'
    source_hash = hashlib.sha256(source).hexdigest()
    sources = {'analysis/hexar_external/acquisition/episode_driver.py': source_hash}
    bank_id = hashlib.sha256(json.dumps(sources, sort_keys=True).encode()).hexdigest()
    bank = tmp_path / 'manifests/hexar_external/acquisition/source_banks' / bank_id
    bank.mkdir(parents=True)
    (bank / 'episode_driver.py').write_bytes(source)
    folder = tmp_path / 'manifests/hexar_external/acquisition/dev-test'
    raw_files = []
    for name in ('episode.json', 'controller_start.json', 'controller_end.json',
                 'raw/metadata.yaml', 'raw/raw_0.db3'):
        path = folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(name.encode())
        raw_files.append(dict(path=str(path.relative_to(tmp_path)), sha256=digest(path),
                              size=path.stat().st_size))
    receipt = dict(episode_id='dev-test', image_id='pinned-image', fresh_container=True,
                   execution_source_bank_sha256=bank_id, source_hashes=sources,
                   raw_files=raw_files)
    (folder / 'provenance.json').write_text(json.dumps(receipt))
    return receipt, folder, bank


def test_capture_rechecks_actual_source_and_raw_bytes(tmp_path):
    receipt, folder, bank = capture(tmp_path)
    assert len(verify_capture(tmp_path, receipt, 'pinned-image')) == 1
    (bank / 'episode_driver.py').write_bytes(b'changed source')
    with pytest.raises(ValueError, match='executed source bytes changed'):
        verify_capture(tmp_path, receipt, 'pinned-image')


@pytest.mark.parametrize('change', ['raw', 'image', 'provenance', 'missing', 'duplicate'])
def test_capture_rejects_incomplete_or_changed_evidence(tmp_path, change):
    receipt, folder, bank = capture(tmp_path)
    if change == 'raw':
        (folder / 'raw/raw_0.db3').write_bytes(b'edited recording')
    elif change == 'image':
        receipt['image_id'] = 'different-image'
    elif change == 'provenance':
        (folder / 'provenance.json').write_text('{}')
    else:
        if change == 'missing':
            receipt['raw_files'] = [r for r in receipt['raw_files']
                                    if not r['path'].endswith('controller_start.json')]
        else:
            receipt['raw_files'].append(copy.deepcopy(receipt['raw_files'][0]))
        (folder / 'provenance.json').write_text(json.dumps(receipt))
    with pytest.raises(ValueError):
        verify_capture(tmp_path, receipt, 'pinned-image')


def test_actual_v15_review_reproduces_and_all_development_remains_excluded():
    exposure = ROOT / 'manifests/hexar_external/confirmatory_v1/development_exposure_v10.json'
    image = json.loads((BASE / 'development_episode_plan_v15_qualification_run.json').read_text())['image_id']
    result = build(BASE / 'development_episode_plan_v15.json',
                   BASE / 'development_episode_plan_v15_qualification_run.json',
                   BASE / 'controller_boundary_qualification_v15.json',
                   dict(path=str(exposure.relative_to(ROOT)), sha256=digest(exposure)), image)
    assert result['status'] == 'TECHNICAL_BATCH_SCOPE_PASSED_NOT_FINAL_ADMISSION'
    assert all(result['batch_checks'].values())
    assert all(r['permanently_excluded_from_confirmation'] for r in result['episodes'])
    assert result['confirmatory_N'] == 0
    assert result['full_acquisition_qualified'] is False
