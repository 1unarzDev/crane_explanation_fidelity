#!/usr/bin/env python3
"""Read-only reproduction of the retained bounded material/citation extension."""
import hashlib
import json
from pathlib import Path
from evidence_calibration_io import canonical_sha256
from run_evidence_calibration_agent_qualification import _packet, aggregate, gates_pass
from roboboat_material_qualification_validation_v3 import validate
from roboboat_qualification_boolean_fields_v2 import score_case

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'docs/roboboat_terminal_evidence'
OUT = ROOT / 'artifacts/roboboat-material-qualification-v3'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    freeze = json.loads((DOC / 'material_qualification_operational_freeze_v3.json').read_text())
    for b in freeze['dependencies']:
        if digest(ROOT / b['path']) != b['sha256']:
            raise ValueError('frozen dependency differs: ' + b['path'])
    suite = json.loads((DOC / 'material_qualification_suite_v2.json').read_text())
    suite_hash = canonical_sha256(suite)
    if suite_hash != freeze['qualification_suite_sha256']:
        raise ValueError('suite changed')
    result = json.loads((OUT / 'qualification-result.json').read_text())
    audit = json.loads((OUT / 'semantic-citation-project-review.json').read_text())
    accounting = json.loads((OUT / 'complete-call-accounting.json').read_text())
    disposition = json.loads((DOC / 'material_qualification_development_disposition_v3.json').read_text())
    for b in disposition['bindings']:
        if digest(ROOT / b['path']) != b['sha256']:
            raise ValueError('disposition binding differs')
    if disposition['inference_activation_authorized'] or disposition['whole_confirmatory_endpoint_ready']:
        raise ValueError('this development verifier cannot activate inference')
    reviews = {(r['slot'], r['case_id']): r for r in audit['reviews']}
    if len(reviews) != 20 or len(audit['reviews']) != 20:
        raise ValueError('incomplete or duplicate citation reviews')
    seen = set()
    for slot in ('A', 'B'):
        records = {}
        for path in (OUT / f'pass-{slot}/calls').glob('*.json'):
            record = json.loads(path.read_text())
            role = record['request_identity']['logical_role']
            if role in records or record['status'] != 'VALID' or record['attempt_count'] != 1:
                raise ValueError('duplicate/invalid retained call')
            records[role] = (path, record)
        if len(records) != 10:
            raise ValueError('incomplete call bank')
        rows = []
        for case in suite['cases']:
            path, record = records[f'material-v2-{slot}-{case["case_id"]}']
            source = case['form']['response_text']
            validate(_packet(case, slot, suite_hash), record['parsed_final'], source)
            rows.append(score_case(case, record['parsed_final']))
            review = reviews[(slot, case['case_id'])]
            if review['call_sha256'] != digest(path) or review['source_text'] != source:
                raise ValueError('review source/call differs')
            expected_fields = []
            for category, prompt, value in (
                ('required_unit_coverage', 'unit_prompt', 'communicated'),
                ('limitation_preservation', 'limitation_prompt', 'preserved')):
                for field in record['parsed_final'][category]:
                    expected_fields.append((category, field[prompt], field[value], field['response_span']))
            actual_fields = [(f['category'], f['prompt'], f['value'], f['response_span']) for f in review['field_reviews']]
            if actual_fields != expected_fields or not review['full_source_review_complete']:
                raise ValueError('review coverage differs')
            if not all(f['project_semantic_citation_valid'] and f['complete_source_stance_considered'] and f['rationale'] for f in review['field_reviews']):
                raise ValueError('semantic project review missing')
            seen.add(str(path.relative_to(ROOT)))
        metrics = aggregate(rows, 'heldout')
        passed, checks = gates_pass(metrics, freeze['heldout_gates'])
        actual = {'slot': slot, 'heldout_metrics': metrics, 'gate_checks': checks, 'passed': passed, 'case_scores': rows}
        if actual != next(p for p in result['passes'] if p['slot'] == slot):
            raise ValueError('automatic result does not reproduce')
    if seen != {r['path'] for r in accounting['calls']} or len(accounting['calls']) != 20:
        raise ValueError('call accounting differs')
    for call in accounting['calls']:
        if digest(ROOT / call['path']) != call['sha256']:
            raise ValueError('accounted return differs')
    old = ROOT / freeze['retained_call_reuse'][0]['path']
    if old.read_bytes() != (OUT / 'pass-A/calls' / old.name).read_bytes():
        raise ValueError('cached original call differs')
    return {'automatic_status': result['status'], 'bounded_disposition': disposition['status'],
            'valid_unique_calls': 20, 'reviewed_boolean_fields': sum(len(r['field_reviews']) for r in reviews.values()),
            'configuration_n_added': 0, 'inference_activation_authorized': False,
            'human_validation': False}


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
