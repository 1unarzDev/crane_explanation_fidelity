#!/usr/bin/env python3
"""Frozen descriptive secondary report; preserve the principal report unchanged."""
import json
from collections import defaultdict

from audit_release import sha, write
from verify_v3 import V3, study

SUPPORTED = 'SUPPORTED_BY_VISIBLE_EVIDENCE'
UNKNOWN = 'UNINTERPRETABLE'
UNSUPPORTED = {'CONTRADICTED_BY_VISIBLE_EVIDENCE', 'INSUFFICIENT_VISIBLE_EVIDENCE',
               'PHYSICALLY_TRUE_BUT_UNSUPPORTED'}


def causal_status(roles_and_labels):
    pairs = list(roles_and_labels)
    if any(role is True and label in UNSUPPORTED for role, label in pairs):
        return True
    if any((role is True and label == UNKNOWN) or
           (role is None and label != SUPPORTED) for role, label in pairs):
        return None
    return False


def main():
    study()
    base = V3 / 'reserved'
    ann = base / 'annotation'
    inventory_path = ann / 'atomic_inventory.json'
    inventory = json.loads(inventory_path.read_text())['items']
    atoms = {a['item_id']: a for r in inventory for a in r['atoms']}
    sidecars = []
    for name in ('causal_roles.coder.json', 'causal_roles.parent.json'):
        data = json.loads((ann / name).read_text())
        assert data['inventory_sha256'] == sha(inventory_path)
        assert data['method_blind'] and not data['support_labels_accessed']
        roles = {r['item_id']: r['causal_role'] for r in data['items']}
        assert len(roles) == len(data['items']) and set(roles) == set(atoms)
        assert all(v is None or type(v) is bool for v in roles.values())
        sidecars.append(roles)
    roles = {key: sidecars[0][key] if sidecars[0][key] == sidecars[1][key] else None
             for key in atoms}
    by_response = {r['response_id']: r['atoms'] for r in inventory}
    key = json.loads((ann / 'join_key.evaluator-only.json').read_text())['key']
    assert len(key) == 324
    assert (ann / 'annotation_summary.json').exists()
    rows = []
    for row in key:
        status = None
        directory = ann / 'judgments' / row['response_id']
        summary_file = directory / 'external-summary.json'
        if row['status'] == 'VALID' and summary_file.exists():
            summary = json.loads(summary_file.read_text())
            if summary['status'] == 'EXTERNAL_V2_AGENT_ASSESSED_QUALIFIED':
                assert summary['external_qualification_sha256'] == sha(V3 / 'qualification/qualification-result.json')
                labels = json.loads((directory / 'final.json').read_text())['final_decisions']
                status = causal_status((roles[a['item_id']], labels['claim:' + a['item_id']])
                                       for a in by_response[row['response_id']])
        rows.append({**row, 'unsupported_causal_relation': status})
    methods = {}
    for method in ('HX-ORIGINAL', 'HX-PROMPT', 'HX-CONTRACT'):
        jobs = [r for r in rows if r['method'] == method]
        assert len(jobs) == 108
        failed = sum(r['unsupported_causal_relation'] is True for r in jobs)
        missing = sum(r['unsupported_causal_relation'] is None for r in jobs)
        recordings = defaultdict(list)
        for r in jobs:
            recordings[r['recording_id']].append(r['unsupported_causal_relation'])
        assert len(recordings) == 12 and all(len(v) == 9 for v in recordings.values())
        methods[method] = {'n_jobs': 108, 'known_causal_failures': failed,
                           'unknown_answers': missing,
                           'fixed_denominator_bounds': [failed / 108, (failed + missing) / 108],
                           'known_answer_rate': failed / (108 - missing) if missing < 108 else None}
    write(base / 'causal_reporting.json', {
        'schema': 'hexar-descriptive-causal-report/v3', 'independent_recordings': 12,
        'primary_endpoint_changed': False, 'alpha_consumed': 0, 'p_value': None,
        'role_coding_qualified': False, 'human_validated': False, 'support_agent_assessed': True,
        'inventory_sha256': sha(inventory_path),
        'sidecar_sha256': {name: sha(ann / name) for name in ('causal_roles.coder.json', 'causal_roles.parent.json')},
        'role_disagreements': sum(sidecars[0][k] != sidecars[1][k] for k in atoms),
        'unresolved_roles': sum(v is None for v in roles.values()), 'methods': methods,
        'scope': 'positive task/software/physical causal or mechanism relations, including modality; no causal classification from support labels',
        'limitations': 'Unqualified developer role coding and atom extraction; missingness bounds, not inferential intervals. Earlier versions unaltered.',
    })
    write(base / 'causal_reporting_jobs.evaluator-only.json', {'rows': rows})
    print('DESCRIPTIVE_CAUSAL_REPORT_CLOSED_PRIMARY_UNCHANGED_ZERO_ALPHA')


if __name__ == '__main__':
    main()
