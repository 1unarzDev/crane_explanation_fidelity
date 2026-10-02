#!/usr/bin/env python3
"""Independently reconstruct frozen causal-report counts from retained labels."""
import json
import math
from collections import Counter
from pathlib import Path

from audit_release import sha, write
from verify_v3 import V3, study


def main():
    study()
    base = V3 / 'reserved'
    ann = base / 'annotation'
    load = lambda path: json.loads(path.read_text())
    inventory = load(ann / 'atomic_inventory.json')
    atoms = {r['response_id']: r['atoms'] for r in inventory['items']}
    sides = [load(ann / name) for name in ('causal_roles.coder.json', 'causal_roles.parent.json')]
    for side in sides:
        assert side['inventory_sha256'] == sha(ann / 'atomic_inventory.json')
        assert side['method_blind'] and not side['support_labels_accessed']
    roles = [{r['item_id']: r['causal_role'] for r in side['items']} for side in sides]
    report = load(base / 'causal_reporting.json')
    key = load(ann / 'join_key.evaluator-only.json')['key']
    assert len(key) == 324 and len({r['response_id'] for r in key}) == 324
    counts = {method: Counter() for method in report['methods']}
    dispositions = {}
    for response in key:
        rid = response['response_id']
        dest = ann / 'judgments' / rid
        conclusion = None
        summary = load(dest / 'external-summary.json')
        if summary['status'] == 'EXTERNAL_V2_AGENT_ASSESSED_QUALIFIED':
            assert summary['external_qualification_sha256'] == sha(V3 / 'qualification/qualification-result.json')
            labels = load(dest / 'final.json')['final_decisions']
            known_failure = False
            unresolved = False
            for atom in atoms[rid]:
                aid = atom['item_id']
                role = roles[0][aid] if roles[0][aid] == roles[1][aid] else None
                label = labels['claim:' + aid]
                assert label in {'SUPPORTED_BY_VISIBLE_EVIDENCE', 'CONTRADICTED_BY_VISIBLE_EVIDENCE',
                                 'INSUFFICIENT_VISIBLE_EVIDENCE', 'PHYSICALLY_TRUE_BUT_UNSUPPORTED',
                                 'UNINTERPRETABLE'}
                if role is True:
                    if label == 'UNINTERPRETABLE':
                        unresolved = True
                    elif label != 'SUPPORTED_BY_VISIBLE_EVIDENCE':
                        known_failure = True
                elif role is None and label != 'SUPPORTED_BY_VISIBLE_EVIDENCE':
                    unresolved = True
            conclusion = True if known_failure else None if unresolved else False
        else:
            assert summary['status'] == 'TECHNICAL_FAILURE'
        dispositions[rid] = conclusion
        counts[response['method']][conclusion] += 1
    retained = load(base / 'causal_reporting_jobs.evaluator-only.json')['rows']
    assert all(dispositions[r['response_id']] is r['unsupported_causal_relation'] for r in retained)
    for method, values in counts.items():
        expected = report['methods'][method]
        assert sum(values.values()) == expected['n_jobs'] == 108
        assert values[True] == expected['known_causal_failures']
        assert values[None] == expected['unknown_answers']
        bounds = [values[True] / 108, (values[True] + values[None]) / 108]
        assert all(math.isclose(a, b) for a, b in zip(bounds, expected['fixed_denominator_bounds']))
    write(base / 'causal_reporting_accounting_audit.json', {
        'schema': 'hexar-independent-causal-accounting/v3', 'passed': True,
        'responses': 324, 'independent_recordings': 12,
        'report_sha256': sha(base / 'causal_reporting.json'),
        'auditor_sha256': sha(Path(__file__)), 'semantic_validity_proven': False,
        'endpoint_changed': False, 'alpha_consumed': 0,
    })
    print('INDEPENDENT_CAUSAL_ACCOUNTING_PASS')


if __name__ == '__main__':
    main()
