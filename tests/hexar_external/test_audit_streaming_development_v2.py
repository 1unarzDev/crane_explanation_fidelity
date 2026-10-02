import json

import pytest

from analysis.hexar_external.confirmatory_v1.audit_streaming_development_v2 import check


def test_live_or_partial_run_cannot_be_closed_by_audit(tmp_path):
    folder = tmp_path / 'run'
    folder.mkdir()
    (folder / 'declaration.json').write_text('{}')
    before = sorted(p.name for p in folder.iterdir())
    with pytest.raises(ValueError, match='terminal development report'):
        check(tmp_path, 'run')
    assert sorted(p.name for p in folder.iterdir()) == before


@pytest.mark.parametrize('phase,confirmatory_n,allowed', [
    ('confirmation', 6, True), ('development_only', 1, False),
    ('development_only', 0, True),
])
def test_confirmation_metadata_is_never_admitted(tmp_path, phase, confirmatory_n, allowed):
    folder = tmp_path / 'run'
    folder.mkdir()
    (folder / 'declaration.json').write_text(json.dumps(dict(
        phase=phase, confirmatory_N=confirmatory_n, confirmation_authorized=allowed)))
    (folder / 'report.json').write_text('{}')
    with pytest.raises(ValueError, match='development-only'):
        check(tmp_path, 'run')
