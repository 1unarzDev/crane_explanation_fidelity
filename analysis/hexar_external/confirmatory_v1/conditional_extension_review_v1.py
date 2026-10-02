"""Read-only review of the authorized companion; never grants execution."""
import hashlib
import json
from pathlib import Path

COMPANION = 'manifests/study/evidence-calibration-fresh-h2-conditional-extension-v1.json'


def _pinned(root, pin, path_key='path'):
    path = Path(pin[path_key])
    if path.is_absolute() or '..' in path.parts:
        raise ValueError('pin must be repository-relative')
    raw = (root / path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != pin['sha256']:
        raise ValueError('changed companion dependency: ' + str(path))
    return json.loads(raw)


def review(root, path=COMPANION):
    root = Path(root)
    companion = json.loads((root / path).read_text())
    if companion['schema'] != 'crane-fresh-h2-conditional-family-companion/v1':
        raise ValueError('wrong companion schema')
    if companion['status'] != 'AUTHORIZED_DESIGN_PENDING_QUALIFICATION_AND_SHARED_RECONCILIATION':
        raise ValueError('this reader cannot admit a bound or activated family')
    expected = dict(family_alpha=.01, program_alpha=.05, previously_consumed_alpha=.02,
                    protected_replication_alpha=.02, new_independent_alpha_allocation=0,
                    consumption_refunded=False, conditional_control_required=True,
                    full_h2_freeze_before_fresh_acquisition_required=True,
                    valid_immutable_h1_rejection_required=True,
                    nonrejecting_or_invalid_h1_closes_h2=True,
                    h2_semantic_activation_authorized=False,
                    raw_confirmation_acquisition_authorized=False, development_authorized=True)
    for key, value in expected.items():
        if type(companion[key]) is not type(value) or companion[key] != value:
            raise ValueError('unauthorized accounting or gate change: ' + key)
    authorization = _pinned(root, companion['authorization'])
    proposal = _pinned(root, companion['proposal'])
    if (authorization['schema'] != 'hexar-fresh-h2-timing-authorization/v1'
            or authorization['timing_change_authorized'] is not True
            or authorization['proposal_path'] != companion['proposal']['path']
            or authorization['proposal_sha256'] != companion['proposal']['sha256']):
        raise ValueError('authorization does not bind the reviewed proposal')
    for key in ('qualification_waived', 'shared_reconciliation_waived',
                'h2_confirmation_authorized', 'replication_borrowing_authorized',
                'h1_frozen_procedure_change_authorized'):
        if authorization[key] is not False:
            raise ValueError('authorization overextended: ' + key)
    old_family = _pinned(root, companion['supersedes_only'])
    ledger = _pinned(root, companion['authoritative_consumed_ledger'], 'snapshot_path')
    h1 = _pinned(root, companion['h1_freeze'], 'snapshot_path')
    allocation = companion['h1_allocation']
    allocations = {r['allocation_id']: r for r in ledger['allocations']}
    if (len(allocations) != len(ledger['allocations'])
            or allocations['candidate-revision-reserve'] != allocation
            or allocation != proposal['preserved_h1_allocation']
            or h1['study_id'] != allocation['campaign_id']
            or h1['alpha'] != .01
            or companion['h1_freeze']['sha256'] != allocation['freeze_sha256']
            or companion['family_id'] != old_family['family_id']):
        raise ValueError('original consumed H1 commitment changed')
    if (ledger['program_alpha'] != .05 or ledger['consumed_alpha'] != .03
            or abs(sum(a['alpha'] for a in allocations.values()) - .05) > 1e-12
            or allocations['candidate-v1-confirmation']['alpha'] != .02
            or allocations['candidate-v1-confirmation']['status'] != 'CONSUMED'
            or allocations['selected-method-replication']['alpha'] != .02
            or allocations['selected-method-replication']['status'] != 'AVAILABLE'):
        raise ValueError('historical/protected program budget changed')
    # These fields intentionally remain null. This version reviews preparation,
    # not adequacy of future qualification evidence or an H1 inferential result.
    required = {'conditional_assumptions', 'scientific_binding', 'acquisition_binding',
                'provider_binding', 'h1_gate_adapter'}
    if set(companion['qualification']) != required:
        raise ValueError('qualification requirements omitted or expanded')
    if any(v is not None for v in companion['qualification'].values()) or companion['shared_reconciliation'] is not None:
        raise ValueError('qualified companion requires a separately reviewed admission reader')
    return dict(schema='hexar-conditional-extension-preparation-review/v1',
                preparation_integrity_passed=True, development_authorized=True,
                h2_semantic_activation_authorized=False, raw_confirmation_acquisition_authorized=False,
                qualification_missing=sorted(required), shared_reconciliation_missing=True,
                h1_semantic_results_read=False, provider_calls=0,
                companion_sha256=hashlib.sha256((root / path).read_bytes()).hexdigest())
