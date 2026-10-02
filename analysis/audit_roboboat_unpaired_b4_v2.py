"""Read-only engineering audit of unpaired outputs; no support labels or N."""
import argparse
import json
from pathlib import Path

from evidence_calibration_io import canonical_sha256
from prepare_roboboat_fair_inputs_v3 import verify
from run_roboboat_population_responses_v1 import binding, checked


def audit(root):
    root = Path(root).resolve()
    declaration = json.loads((root / 'declaration.json').read_text())
    for source in declaration['sources']:
        checked(source)
    snapshot = verify(checked(declaration['input_snapshot']))
    terminal = json.loads((root / 'terminal.json').read_text())
    checked(terminal['declaration'])
    entries = snapshot['entries']
    expected = {(e['row_id'], e['level']): e for e in entries}
    actual = {(r['row_id'], r['level']): r for r in terminal['results']}
    if len(actual) != len(terminal['results']) or actual.keys() != expected.keys():
        raise ValueError('fixed condition denominator changed')
    results = []
    for key, entry in expected.items():
        row = actual[key]
        checks = {}
        if row['status'] != 'CANDIDATE_GENERATED_UNPAIRED_UNJUDGED':
            results.append({'row_id': key[0], 'level': key[1], 'generation_failure': True})
            continue
        pipeline = json.loads(checked(row['full_pipeline']).read_text())
        answer = json.loads(checked(row['answer']).read_text())
        packet = json.loads((Path(entry['B4_private_workspace']) / 'evidence.json').read_text())
        catalog = json.loads((Path(entry['B4_private_workspace']) /
                              'configs/roboboat_claim_contracts_v3_development.json').read_text())
        realization, plan = pipeline['realization'], pipeline['plan']
        report = realization['audit']
        checks['packet_catalog_binding'] = (pipeline['packet_sha256'] == canonical_sha256(packet)
                                            and pipeline['ontology_sha256'] == canonical_sha256(catalog))
        checks['common_input_signature'] = row['common_input_signature'] == entry['common_file_hash_signature']
        checks['plan_candidate_binding'] = (realization['plan_sha256'] == canonical_sha256(plan)
                                           and realization['candidate_sha256'] == canonical_sha256(pipeline['candidate']))
        checks['diagnostic_binding'] = (plan['diagnostic_result_sha256'] ==
                                       report['diagnostic_result_sha256'] == canonical_sha256(pipeline['diagnostic_result']))
        checks['response_binding'] = (answer['answer'] == realization['final_response'] and
                                     report['final_response_sha256'] == canonical_sha256(answer['answer']))
        checks['literal_clause_coverage'] = (realization['final_response'] ==
                                            ' '.join(c['text'] for c in realization['final_clauses']))
        checks['internal_audit_clean'] = (report['status'] == 'ACCEPTED' and all(not report[k] for k in
            ('missing_limitation_ids', 'missing_required_claim_ids', 'numeric_mismatches', 'unapproved_claim_ids')))
        ids = [c['contract_id'] for c in realization['final_clauses']]
        checks['exact_required_contracts'] = (len(ids) == len(set(ids)) and set(ids) ==
            set(plan['required_claim_ids']) | set(plan['required_non_entailment_ids']))
        numeric = {(v['claim_id'], v['slot_id']): v for v in plan['approved_numeric_values']}
        bindings = pipeline['numeric_source_bindings']
        checks['numeric_binding_coverage'] = (len(bindings) == len(numeric) and
            {(v['claim_id'], v['slot_id']) for v in bindings} == set(numeric) and
            all(v['packet_sha256'] == pipeline['packet_sha256'] for v in bindings))
        checks['direct_numeric_pointer_values'] = True
        direct_count = 0
        for item in bindings:
            if not item['source'].startswith('/'):
                continue
            value = packet
            for part in item['source'][1:].split('/'):
                value = value[part.replace('~1', '/').replace('~0', '~')]
            direct_count += 1
            checks['direct_numeric_pointer_values'] &= value == numeric[item['claim_id'], item['slot_id']]['value']
        checks['zero_model_unpaired'] = (row['model_calls'] == answer['model_calls'] == 0 and
                                        answer['unpaired'] is True and row['endpoint_score'] is None)
        results.append({'row_id': key[0], 'level': key[1], 'checks': checks,
                        'passed': all(checks.values()), 'direct_numeric_values_checked': direct_count,
                        'pipeline': row['full_pipeline'], 'answer': row['answer']})
    return {'schema': 'roboboat-unpaired-B4-engineering-audit/v1', 'terminal': binding(root / 'terminal.json'),
            'auditor': binding(__file__), 'conditions': len(results),
            'passed_conditions': sum(r.get('passed', False) for r in results), 'results': results,
            'scope': 'Internal hashes, literal plan coverage and direct packet values only. Derived numeric semantics and independent diagnostic completeness/support require qualified source-complete judges. Internal acceptance is not endpoint success.',
            'model_calls': 0, 'judge_calls': 0, 'independent_n_added': 0,
            'candidate_promoted': False, 'confirmation_frozen': False}


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--root', required=True); p.add_argument('--output', required=True)
    a = p.parse_args(); output = Path(a.output)
    if output.exists():
        raise FileExistsError('fresh audit output required')
    result = audit(a.root); output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('conditions', 'passed_conditions', 'independent_n_added')}))
