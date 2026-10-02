import json
from pathlib import Path
import shutil

import pytest

from analysis.hexar_external.confirmatory_v1.conditional_extension_review_v1 import COMPANION, review

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def candidate(tmp_path):
    companion = json.loads((ROOT / COMPANION).read_text())
    paths = [COMPANION]
    paths += [companion[k]['path'] for k in ('authorization', 'proposal', 'supersedes_only')]
    paths += [companion[k]['snapshot_path'] for k in ('authoritative_consumed_ledger', 'h1_freeze')]
    for path in paths:
        dest = tmp_path / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, dest)
    return tmp_path


def edit(root, transform):
    path = root / COMPANION
    obj = json.loads(path.read_text())
    transform(obj)
    path.write_text(json.dumps(obj))


def test_authorization_preserves_h1_and_cannot_activate(candidate):
    result = review(candidate)
    assert result['preparation_integrity_passed']
    assert not result['h2_semantic_activation_authorized']
    assert not result['raw_confirmation_acquisition_authorized']
    assert len(result['qualification_missing']) == 5
    assert result['shared_reconciliation_missing']


@pytest.mark.parametrize('key,value', [
    ('protected_replication_alpha', .01), ('new_independent_alpha_allocation', .01),
    ('consumption_refunded', True), ('h2_semantic_activation_authorized', True),
    ('full_h2_freeze_before_fresh_acquisition_required', False),
    ('conditional_control_required', False), ('family_alpha', .02),
])
def test_accounting_and_execution_changes_fail_closed(candidate, key, value):
    edit(candidate, lambda obj: obj.update({key: value}))
    with pytest.raises(ValueError):
        review(candidate)


def test_consumed_timestamp_cannot_be_refunded_or_rebound(candidate):
    edit(candidate, lambda obj: obj['h1_allocation'].update(consumed_at=None))
    with pytest.raises(ValueError, match='H1 commitment'):
        review(candidate)


def test_changed_authorization_or_original_freeze_fails(candidate):
    obj = json.loads((candidate / COMPANION).read_text())
    path = candidate / obj['authorization']['path']
    path.write_bytes(path.read_bytes() + b'\n')
    with pytest.raises(ValueError, match='changed companion'):
        review(candidate)


def test_missing_qualification_requirement_fails(candidate):
    edit(candidate, lambda obj: obj['qualification'].pop('provider_binding'))
    with pytest.raises(ValueError, match='requirements omitted'):
        review(candidate)


def test_bare_qualification_or_reconciliation_flag_never_opens_gate(candidate):
    edit(candidate, lambda obj: obj.update(shared_reconciliation=True))
    with pytest.raises(ValueError, match='separately reviewed'):
        review(candidate)
