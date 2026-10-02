import hashlib
import json
from pathlib import Path

from analysis.hexar_external.confirmatory_v1.gatekeeping import concurrent_commitment_errors


def fixture(tmp_path):
    snapshot=tmp_path/'snapshot.json';snapshot.write_text('{}')
    report=tmp_path/'report.json'
    report.write_text(json.dumps(dict(schema='hexar-concurrent-h1-commitment-audit/v1',source_snapshots={
        'ledger':dict(snapshot_path='snapshot.json',sha256=hashlib.sha256(snapshot.read_bytes()).hexdigest())})))
    return {'concurrent_commitment_audit':dict(path='report.json',sha256=hashlib.sha256(report.read_bytes()).hexdigest())}


def test_retained_consumption_blocks_even_with_bare_status_or_ready_flags(tmp_path):
    amendment=fixture(tmp_path);amendment.update(status='READY_FOR_FREEZE',confirmation_authorized=True)
    assert 'explicit prospective reconciliation' in concurrent_commitment_errors(tmp_path,amendment)[0]


def test_changed_audit_and_original_snapshot_fail_closed(tmp_path):
    amendment=fixture(tmp_path);(tmp_path/'snapshot.json').write_text('{"changed":true}')
    assert 'snapshot changed' in concurrent_commitment_errors(tmp_path,amendment)[0]
    (tmp_path/'report.json').write_text('{}')
    assert 'hash mismatch' in concurrent_commitment_errors(tmp_path,amendment)[0]


def test_old_fixture_absence_is_no_extra_conflict_or_authority(tmp_path):
    assert concurrent_commitment_errors(tmp_path,{})==[]


def test_actual_candidate_is_explicitly_closed():
    root=Path(__file__).resolve().parents[2]
    amendment=json.loads((root/'manifests/hexar_external/confirmatory_v1/alpha_amendment.json').read_text())
    assert amendment['confirmation_authorized'] is False
    assert concurrent_commitment_errors(root,amendment)
