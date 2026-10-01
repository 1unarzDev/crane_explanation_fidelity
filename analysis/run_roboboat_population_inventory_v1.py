#!/usr/bin/env python3
"""Immutable development response bank and two-pass qualified marine extraction.

Extraction deduplication never changes response joins or independent N. Structural
returns still require exact-source complete-source project review before scoring.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path

from build_roboboat_terminal_batch import ROOT, DOC, digest, save
from run_roboboat_atomization_extension_v5 import execute
from roboboat_temporal_certificate_v2 import certificate, render

DISPOSITION = 'DEVELOPMENT_EXTRACTION_ONLY_NO_CONFIRMATORY_INFERENCE'


def binding(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': digest(path)}


def checked(b):
    path = Path(b['path'])
    if not path.is_absolute():
        path = ROOT/path
    if digest(path) != b['sha256']:
        raise ValueError('bound source changed: ' + str(path))
    return path


def source_bindings(value):
    if isinstance(value, dict):
        if 'path' in value and 'sha256' in value:
            yield value
        else:
            for item in value.values():
                yield from source_bindings(item)
    elif isinstance(value, list):
        for item in value:
            yield from source_bindings(item)


def extractor_sources():
    freeze_path = DOC/'marine_atomization_freeze_v5.json'
    review_path = DOC/'marine_atomization_semantic_review_v5.json'
    freeze = json.loads(freeze_path.read_text())
    review = json.loads(review_path.read_text())
    if review['status'] != 'PASS_BOUNDED_MARINE_ACTOR_CLOCK_PHASE_COMPLETENESS_EXTRACTION':
        raise ValueError('marine extractor semantic qualification gate closed')
    disposition = json.loads(checked(freeze['qualified_disposition']).read_text())
    if disposition['status'] != 'QUALIFIED_SYNTHETIC_ATOMIC_INVENTORY_ONLY':
        raise ValueError('qualified base extractor gate closed')
    sources = [freeze_path, review_path]
    sources.extend(checked(b) for b in source_bindings(freeze))
    if freeze['passes'] != 2 or freeze['quality_retries'] != 0 or freeze['max_concurrent_calls'] != 2:
        raise ValueError('unexpected extractor execution contract')
    return freeze, sources


def prepare(response_declaration, response_root, output_root, declaration):
    declaration, output_root = Path(declaration).resolve(), Path(output_root).resolve()
    response_declaration, response_root = Path(response_declaration).resolve(), Path(response_root).resolve()
    if declaration.exists() or output_root.exists():
        raise ValueError('one-shot extraction declaration/bank already exists')
    d = json.loads(response_declaration.read_text())
    if d['schema'] != 'roboboat-population-response-declaration/v1' or d['disposition'] != 'DEVELOPMENT_ONLY_NO_CONFIRMATORY_INFERENCE':
        raise ValueError('immutable development response snapshot required')
    if len({e['id'] for e in d['entries']}) != len(d['entries']):
        raise ValueError('duplicate response identity')
    freeze, extractor_paths = extractor_sources()
    dependencies = [response_declaration, Path(__file__), *extractor_paths]
    dependencies.extend(checked(b) for b in source_bindings(d))
    missing, accounting, joins, texts = [], [], [], {}

    def add_answer(entry, method, path, answer, provenance):
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError('invalid nonempty answer: ' + str(path))
        key = hashlib.sha256(answer.encode('utf-8')).hexdigest()
        if key in texts and texts[key] != answer:
            raise ValueError('answer hash collision')
        texts[key] = answer
        dependencies.append(path)
        joins.append({'opaque_response_id': key, 'response_id': entry['id'],
                      'row_id': entry['row_id'], 'cluster_id': entry['cluster_id'],
                      'level': entry['level'], 'method': method,
                      'answer_source': binding(path), 'answer_provenance': provenance})

    for entry in d['entries']:
        source = response_root/'responses'/entry['id']
        terminal = source/'response-terminal.json'
        expected = {'declaration_sha256': digest(response_declaration), 'entry': entry}
        item = {'response_id': entry['id'], 'row_id': entry['row_id'], 'cluster_id': entry['cluster_id'],
                'level': entry['level'], 'source_identity': expected, 'methods': {}}
        record = None
        intent = response_root/'intents'/(entry['id']+'.json')
        if intent.exists():
            if json.loads(intent.read_text()) != expected:
                raise ValueError('response intent source identity mismatch')
            dependencies.append(intent)
            item['method_call_intent'] = binding(intent)
        else:
            missing.append(str(intent))
        if terminal.exists():
            record = json.loads(terminal.read_text())
            if record['source_identity'] != expected:
                raise ValueError('response terminal source identity mismatch')
            if record['status'] not in ('COMPLETE_RESPONSE_SUPPORT_UNJUDGED', 'TECHNICAL_RESPONSE_FAILURE'):
                raise ValueError('unsupported response terminal disposition')
            dependencies.append(terminal)
            item.update(method_call_status=record['status'], terminal=binding(terminal), error=record.get('error'))
        else:
            item['method_call_status'] = 'MISSING_RESPONSE_TERMINAL'
            missing.append(str(terminal))
        # B4 is deterministic and source-bound even when the B2 call failed or is absent.
        candidate_path = checked(entry['candidate'])
        candidate = json.loads(candidate_path.read_text())
        evidence = json.loads(checked(entry['packet']).read_text())
        cert = certificate(evidence)
        if candidate['certificate'] != cert or candidate['answer'] != render(evidence, cert):
            raise ValueError('candidate differs from source-bound deterministic B4')
        add_answer(entry, 'B4', candidate_path, candidate['answer'], 'DETERMINISTIC_BOUND_CANDIDATE')
        item['methods']['B4'] = 'INCLUDED_DETERMINISTIC_SOURCE'
        for method in ('B2', 'B4'):
            path = source/f'{method}.json'
            if not path.exists():
                missing.append(str(path))
                if method == 'B2':
                    item['methods']['B2'] = 'MISSING_ANSWER'
                    if record and record['status'] == 'COMPLETE_RESPONSE_SUPPORT_UNJUDGED':
                        raise ValueError('complete terminal missing B2 answer')
                continue
            dependencies.append(path)
            value = json.loads(path.read_text())
            if method == 'B4':
                if value['answer'] != candidate['answer']:
                    raise ValueError('retained B4 differs from deterministic source')
            elif record is None:
                item['methods']['B2'] = 'ORPHAN_ANSWER_UNBOUND_TERMINAL_EXCLUDED'
                item['orphan_answer'] = binding(path)
            else:
                add_answer(entry, 'B2', path, value['answer'], 'SOURCE_BOUND_METHOD_RETURN')
                item['methods']['B2'] = 'INCLUDED_VALID_ANSWER'
        accounting.append(item)
    blind = output_root/'blind-bank.json'
    join = output_root/'evaluator-join.json'
    ledger = output_root/'response-accounting.json'
    save(blind, {'entries': [{'opaque_response_id': key, 'response_text': value} for key, value in sorted(texts.items())]})
    save(join, {'entries': joins, 'annotation_input': False})
    save(ledger, {'entries': accounting, 'capture_accounting': d['capture_accounting'], 'annotation_input': False})
    dependencies.extend([blind, join, ledger])
    result = {'schema': 'roboboat-population-inventory-declaration/v1', 'disposition': DISPOSITION,
              'dependencies': [binding(p) for p in dict.fromkeys(dependencies)],
              'missing_source_paths': sorted(set(missing)), 'output_root': str(output_root),
              'response_declaration': binding(response_declaration), 'extractor_freeze': binding(DOC/'marine_atomization_freeze_v5.json'),
              'snapshot_entry_count': len(d['entries']), 'original_answers': len(joins),
              'method_answer_counts': {m: sum(j['method'] == m for j in joins) for m in ('B2', 'B4')},
              'unique_answer_texts': len(texts), 'model': freeze['candidate'], 'passes': 2,
              'max_concurrent_calls': 2, 'quality_retries': 0,
              'selection': 'All immutable snapshot entries, valid source-bound B2 returns and every deterministic B4; failures and missing calls retained without outcome-based selection.',
              'qualification': 'Unchanged qualified atomizer and marine actor/clock/phase appendix v5; exact-source complete-source project review required before support scoring.',
              'semantic_completeness_established': False, 'support_annotation_authorized': False,
              'endpoint_scoring_authorized': False, 'new_independent_configuration_n': 0,
              'confirmation_n': 0, 'replication_n': 0, 'alpha_consumed': 0}
    save(declaration, result)
    return result


def run(declaration, output_root, *, executor=execute):
    declaration, output_root = Path(declaration).resolve(), Path(output_root).resolve()
    d = json.loads(declaration.read_text())
    if d['disposition'] != DISPOSITION or d['output_root'] != str(output_root):
        raise ValueError('development extraction/output identity mismatch')
    if (d['passes'], d['max_concurrent_calls'], d['quality_retries']) != (2, 2, 0):
        raise ValueError('two passes, two workers and zero retries required')
    for b in d['dependencies']:
        checked(b)
    # Presence of a previously missing source cannot silently revise the snapshot.
    if any(Path(p).exists() for p in d['missing_source_paths']):
        raise ValueError('missing source now exists; create a fresh immutable bank')
    freeze, _ = extractor_sources()
    if freeze['candidate'] != d['model']:
        raise ValueError('extractor model changed')
    bank = json.loads((output_root/'blind-bank.json').read_text())
    if len(bank['entries']) != d['unique_answer_texts']:
        raise ValueError('blind bank size mismatch')
    for entry in bank['entries']:
        if set(entry) != {'opaque_response_id', 'response_text'} or hashlib.sha256(entry['response_text'].encode()).hexdigest() != entry['opaque_response_id']:
            raise ValueError('blind metadata leak or answer identity mismatch')
    identity = {'declaration_sha256': digest(declaration), 'output_root': str(output_root)}
    result_path = output_root/'structural-result.json'
    if result_path.exists():
        previous = json.loads(result_path.read_text())
        if previous['source_identity'] != identity:
            raise ValueError('retained extraction identity mismatch')
        return previous
    with (output_root/'extraction-run-intent.json').open('x') as stream:
        json.dump(identity, stream)

    def attempt(entry, slot):
        case = {'case_id': entry['opaque_response_id'], 'response_text': entry['response_text']}
        item = {'opaque_response_id': case['case_id'], 'slot': slot, 'source_identity': identity}
        try:
            value = executor(case, slot, freeze, output_root)
            if value['validation']['status'] != 'STRUCTURALLY_VALID_COMPLETENESS_UNQUALIFIED':
                raise ValueError('extractor structural validation failed')
            item['status'] = 'STRUCTURALLY_VALID_COMPLETENESS_UNQUALIFIED'
        except Exception as error:
            item.update(status='TECHNICAL_OR_STRUCTURAL_EXTRACTION_FAILURE', error=str(error))
        save(output_root/'extraction-attempts'/f"{case['case_id']}-{slot}.json", item)
        return item

    attempts = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = [pool.submit(attempt, entry, slot) for entry in bank['entries'] for slot in ('A', 'B')]
        for job in as_completed(jobs):
            attempts.append(job.result())
    failed = sum(a['status'] != 'STRUCTURALLY_VALID_COMPLETENESS_UNQUALIFIED' for a in attempts)
    result = {'source_identity': identity, 'status': 'EXTRACTION_FAILURES_RETAINED_NO_RETRIES' if failed else 'COMPLETE_EXTRACTION_PROJECT_COMPLETENESS_REVIEW_PENDING',
              'original_answers': d['original_answers'], 'unique_answer_texts': d['unique_answer_texts'],
              'passes': 2, 'failed_extraction_attempts': failed,
              'attempts': sorted(attempts, key=lambda a: (a['opaque_response_id'], a['slot'])),
              'quality_retries': 0, 'semantic_completeness_established': False,
              'support_annotation_authorized': False, 'endpoint_scoring_authorized': False,
              'new_independent_configuration_n': 0, 'confirmation_n': 0, 'replication_n': 0, 'alpha_consumed': 0}
    save(result_path, result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('prepare', 'run'))
    parser.add_argument('--response-declaration', type=Path)
    parser.add_argument('--response-root', type=Path)
    parser.add_argument('--output-root', required=True, type=Path)
    parser.add_argument('--declaration', required=True, type=Path)
    args = parser.parse_args()
    if args.phase == 'prepare':
        if args.response_declaration is None or args.response_root is None:
            parser.error('prepare requires --response-declaration and --response-root')
        result = prepare(args.response_declaration, args.response_root, args.output_root, args.declaration)
    else:
        result = run(args.declaration, args.output_root)
    print(json.dumps({k: result[k] for k in ('original_answers', 'unique_answer_texts')}, sort_keys=True))


if __name__ == '__main__':
    main()
