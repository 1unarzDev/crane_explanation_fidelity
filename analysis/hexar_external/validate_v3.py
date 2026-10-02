#!/usr/bin/env python3
"""Audit recorded v3 provenance/completeness; never infer an effectiveness claim."""
import argparse
import json
import math
import statistics
from collections import Counter
from pathlib import Path

from audit_release import ROOT, sha, write
from verify_v3 import V3, qualified, study
from evidence_calibration_io import canonical_sha256
import validate_v2


def read(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--require-final', action='store_true')
    parser.add_argument('--require-preservation', action='store_true')
    args = parser.parse_args()
    assert not args.require_preservation or args.require_final
    validate_v2.V2 = V3
    validate_v2.qualified = qualified
    validate_v2.study = study
    validate_v2.main()
    rows = []
    for cohort, n, questions in [('development', 6, {'q1'}),
                                ('reserved', 12, {'q1', 'q2', 'q3'})]:
        base = V3 / cohort
        if not (base / 'packets.json').exists():
            assert not args.require_final, 'Missing declared reserved inputs.'
            continue
        packets = read(base / 'packets.json')['packets']
        accounting = read(base / 'accounting.evaluator-only.json')['records']
        assert len(accounting) == n
        assert len({r['recording_id'] for r in accounting}) == n
        families = Counter(r['situation_family'] for r in accounting)
        assert len(families) == 6 and set(families.values()) == {n // 6}
        expected = {(r['recording_id'], q, c) for r in accounting for q in questions
                    for c in ('intact', 'irrelevant_removal', 'diagnostic_removal')}
        assert len(packets) == len(expected)
        assert {(p['recording_id'], p['question_id'], p['condition']) for p in packets} == expected
        for p in packets:
            assert canonical_sha256(p['method_packet']) == p['packet_sha256']
            if p['condition'] == 'diagnostic_removal':
                evidence = p['method_packet']['evidence']
                assert not evidence['manual_state'] and not evidence['charging_state']
        for rid, q, _ in expected:
            pair = [p for p in packets if p['recording_id'] == rid and p['question_id'] == q
                    and p['condition'] != 'diagnostic_removal']
            assert pair[0]['method_packet'] == pair[1]['method_packet']
            assert pair[0]['upstream_request'] == pair[1]['upstream_request']
        ann = base / 'annotation'
        summary = read(ann / 'annotation_summary.json') if (ann / 'annotation_summary.json').exists() else None
        responses = list((base / 'responses').glob('*.json'))
        row = {'cohort': cohort, 'recordings': n, 'families': dict(families),
               'packets': len(packets), 'responses': len(responses), 'assessment_closed': summary is not None}
        if summary:
            key = read(ann / 'join_key.evaluator-only.json')['key']
            assert len(key) == 3 * len(packets)
            assert len({r['job_id'] for r in key}) == len(key)
            valid = [r for r in key if r['status'] == 'VALID']
            assert summary['n_responses'] == len(valid)
            dispositions = [read(ann / 'judgments' / r['response_id'] / 'external-summary.json') for r in valid]
            assert summary['qualified_completed'] == sum(r['status'] == 'EXTERNAL_V2_AGENT_ASSESSED_QUALIFIED' for r in dispositions)
            assert summary['technical_failures'] == sum(r['status'] == 'TECHNICAL_FAILURE' for r in dispositions)
            assert summary['qualified_completed'] + summary['technical_failures'] == len(valid)
            row['assessment'] = summary
        if args.require_final:
            assert len(responses) == 3 * len(packets), 'Incomplete three-method generation.'
            assert summary is not None, 'Assessment still active or absent.'
            if cohort == 'reserved':
                study()
                result = read(base / 'results.json')
                assert result['independent_recordings'] == 12 and result['physical_families'] == 6
                assert all(r['n_jobs'] == 108 for r in result['methods'].values())
                scored = read(base / 'scored_jobs.evaluator-only.json')['rows']
                assert len(scored) == 324
                for method, values in result['methods'].items():
                    jobs = [r for r in scored if r['method'] == method]
                    known = [r['success'] for r in jobs if r['success'] is not None]
                    bounds = [sum(known) / 108, (sum(known) + 108 - len(known)) / 108]
                    assert values['unresolved_or_technical'] == 108 - len(known)
                    assert all(math.isclose(x, y) for x, y in zip(bounds, values['fixed_denominator_bounds']))
                recording_bounds = []
                complete_pairs = 0
                for recording in accounting:
                    bounds = {}
                    for method in ('HX-PROMPT', 'HX-CONTRACT'):
                        jobs = [r for r in scored if r['recording_id'] == recording['recording_id'] and r['method'] == method]
                        assert len(jobs) == 9
                        known = [r['success'] for r in jobs if r['success'] is not None]
                        bounds[method] = [sum(known) / 9, (sum(known) + 9 - len(known)) / 9]
                    complete_pairs += all(bounds[m][0] == bounds[m][1] for m in bounds)
                    recording_bounds.append([bounds['HX-CONTRACT'][0] - bounds['HX-PROMPT'][1],
                                             bounds['HX-CONTRACT'][1] - bounds['HX-PROMPT'][0]])
                expected_bounds = [statistics.mean(r[i] for r in recording_bounds) for i in (0, 1)]
                assert all(math.isclose(x, y, abs_tol=1e-12) for x, y in zip(expected_bounds, result['primary_full_cohort_effect_bounds']))
                assert result['paired_complete_recordings'] == complete_pairs
                if complete_pairs < 12:
                    assert result['descriptive_family_t95'] is None
                assert all(r['success'] is None for r in scored if r['technical_failure'])
                causal = read(base / 'causal_reporting.json')
                assert causal['independent_recordings'] == 12
                assert not causal['primary_endpoint_changed'] and causal['alpha_consumed'] == 0
                assert causal['p_value'] is None and not causal['human_validated']
                assert all(r['n_jobs'] == 108 for r in causal['methods'].values())
                assert all(p.exists() for p in [base / 'result_table.md', base / 'evidence_results.svg', base / 'evidence_results.png'])
        rows.append(row)
    if args.require_preservation:
        receipt = read(V3 / 'final_restore_receipt.json')
        archive = Path(receipt['archive_location'])
        for name, field in [('private-assets.tar.gz', 'assets_sha256'),
                            ('code.bundle', 'code_bundle_sha256'),
                            ('upstream.bundle', 'upstream_bundle_sha256'),
                            ('assets_manifest.json', 'manifest_sha256')]:
            assert sha(archive / name) == receipt[field]
        assert receipt['scoped_tests_restored'] and receipt['files_restored_and_sha256_checked'] > 0
    write(V3 / 'integrity_audit.json', {'schema': 'hexar-provenance-completeness-audit/v3',
          'required_final': args.require_final, 'cohorts': rows, 'alpha_consumed': 0,
          'private_preservation_checked': args.require_preservation,
          'effectiveness_or_human_validity_proven': False,
          'auditor_sha256': sha(ROOT / 'analysis/hexar_external/validate_v3.py')})
    print('V3_PROVENANCE_COMPLETENESS_PASS', 'FINAL' if args.require_final else 'RESUMABLE')


if __name__ == '__main__':
    main()
