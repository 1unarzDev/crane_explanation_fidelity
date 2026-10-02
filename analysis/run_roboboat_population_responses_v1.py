#!/usr/bin/env python3
"""Predeclare and execute paired population responses; development only, no retries."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from build_roboboat_terminal_batch import ROOT, DOC, save, digest
from roboboat_isolated_transport import call
from roboboat_temporal_certificate_v2 import certificate, render

SCHEMA = {'type': 'object', 'properties': {'answer': {'type': 'string'}},
          'required': ['answer'], 'additionalProperties': False}
BASIS = {'goal_checker_values': 'pre-action-node-plugin-specific-ROS-readback',
         'remaining_configuration': 'declared-launch-profile',
         'serialization': 'config_sha256 identifies derived effective YAML',
         'internal-consumption-of-odometry-proven': False}


def binding(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': digest(path)}


def checked(b):
    path = Path(b['path'])
    if digest(path) != b['sha256']:
        raise ValueError('bound input changed: ' + str(path))
    return path


def prepare(registry_path, capture_root, declaration_path, *, allow_completed_subset=False,
            source_declaration=DOC/'contact_policy_response_declaration_v2.json', prior_declarations=()):
    """Snapshot all valid completed rows without selecting on response or task outcome."""
    registry_path, capture_root = Path(registry_path).resolve(), Path(capture_root).resolve()
    registry = json.loads(registry_path.read_text())
    if registry['status'] != 'DEVELOPMENT_EXPLORATORY_NOT_CONFIRMATION':
        raise ValueError('development population required')
    rows = registry['rows']
    if len({r['id'] for r in rows}) != len(rows):
        raise ValueError('duplicate population identity')
    source = json.loads(Path(source_declaration).read_text())
    if (source['B2'].get('model') not in ('gpt-6-sol', 'gpt-6-astra') or
            source['B2'].get('effort') != 'high' or source['B2'].get('tools') is not True or
            source['B2'].get('quality_retry') is not False):
        raise ValueError('unexpected baseline binding')
    methods = []
    for b in source['method_sources']:
        path = ROOT / b['path']
        if digest(path) != b['sha256']:
            raise ValueError('method source closure changed: ' + str(path))
        methods.append(binding(path))
    entries, accounting = [], []
    prior_bindings, already_declared = [], set()
    for prior in prior_declarations:
        previous = json.loads(Path(prior).read_text())
        if previous['registry']['sha256'] != digest(registry_path) or previous['B2'] != source['B2']:
            raise ValueError('prior declaration belongs to a different population/baseline')
        prior_bindings.append(binding(prior))
        already_declared.update(e['id'] for e in previous['entries'])
    for row in rows:
        capture = capture_root / row['id']
        terminal = capture / 'capture-attempt.json'
        successor = capture / 'capture-export-terminal-v2.json'
        if successor.exists(): terminal = successor
        if not terminal.exists():
            accounting.append({'id': row['id'], 'status': 'PENDING'})
            continue
        record = json.loads(terminal.read_text())
        if record['registry_sha256'] != digest(registry_path) or record['row'] != row:
            raise ValueError('capture population identity mismatch')
        status = record['status']
        if status not in ('VALID_DEVELOPMENT', 'TECHNICAL_FAILURE'):
            raise ValueError('unresolved capture attempt: ' + row['id'])
        accounting.append({'id': row['id'], 'status': status, 'capture_terminal': binding(terminal),
                           'error': record.get('error')})
        if status != 'VALID_DEVELOPMENT':
            continue
        if 'original_capture_terminal' in record:
            checked(record['original_capture_terminal'])
            accounting[-1]['original_capture_terminal'] = record['original_capture_terminal']
            for raw in record['raw_sources']: checked(raw)
            accounting[-1]['raw_sources'] = record['raw_sources']
        export = capture / record.get('export_directory', '.')
        for level in range(3):
            if row['id'] + f'-L{level}' in already_declared: continue
            packet = export / 'method_packets' / f'L{level}.json'
            candidate = export / 'candidate_outputs' / f'L{level}.json'
            evidence = json.loads(packet.read_text())
            result = json.loads(candidate.read_text())
            cert = certificate(evidence)
            if result['answer'] != render(evidence, cert) or result['certificate'] != cert:
                raise ValueError('candidate differs from source-bound B4')
            entries.append({'id': row['id'] + f'-L{level}', 'row_id': row['id'],
                            'cluster_id': row['cluster_id'], 'level': level,
                            'packet': binding(packet), 'candidate': binding(candidate),
                            'effective_configuration': binding(export/'effective-configuration.yaml')})
    if any(a['status'] == 'PENDING' for a in accounting) and not allow_completed_subset:
        raise ValueError('population incomplete; use explicit development completed-subset snapshot')
    declaration = {'schema': 'roboboat-population-response-declaration/v1',
                   'disposition': 'DEVELOPMENT_ONLY_NO_CONFIRMATORY_INFERENCE',
                   'registry': binding(registry_path), 'source_declaration': binding(source_declaration),
                   'runner': binding(__file__), 'transport': binding(ROOT/'analysis/roboboat_isolated_transport.py'),
                   'prompt': binding(DOC/'marine_b2_contact_policy_prompt_v2.txt'),
                   'method_sources': methods, 'B2': source['B2'], 'B4': 'certificate-v2/render-v2',
                   'return_schema': SCHEMA, 'configuration_basis': BASIS,
                   'capture_accounting': accounting, 'entries': entries, 'prior_declarations': prior_bindings,
                   'selection': 'Every VALID_DEVELOPMENT row present in this immutable snapshot; all L0-L2 not already registered for this baseline in bound prior declarations; technical failures retained separately',
                   'completed_subset': allow_completed_subset, 'max_workers': 2,
                   'timeout_s': 300, 'quality_retries': 0, 'confirmation_n': 0,
                   'replication_n': 0, 'alpha_consumed': 0, 'annotation_status': 'NOT_RUN'}
    save(Path(declaration_path), declaration)
    return declaration


def execute(entry, declaration, declaration_path, output_root, *, caller=call):
    output = Path(output_root) / 'responses' / entry['id']
    terminal = output / 'response-terminal.json'
    identity = {'declaration_sha256': digest(declaration_path), 'entry': entry}
    if terminal.exists():
        previous = json.loads(terminal.read_text())
        if previous['source_identity'] != identity:
            raise ValueError('retained terminal identity mismatch')
        return previous
    intent = Path(output_root) / 'intents' / (entry['id'] + '.json')
    intent.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation is the concurrency guard and unresolved-restart refusal.
    with intent.open('x') as stream:
        json.dump(identity, stream, indent=2)
    try:
        with tempfile.TemporaryDirectory(prefix='boat-population-b2-') as tmp:
            work = Path(tmp)
            shutil.copyfile(checked(entry['packet']), work/'evidence.json')
            for source in declaration['method_sources']:
                path = checked(source)
                shutil.copyfile(path, work/path.name)
            shutil.copyfile(checked(entry['effective_configuration']), work/'effective-configuration.yaml')
            save(work/'configuration-basis.json', declaration['configuration_basis'])
            result = caller(Path(output_root)/'calls', entry['id'], work,
                            checked(declaration['prompt']).read_text(), declaration['B2']['model'],
                            declaration['B2']['effort'], declaration['return_schema'],
                            allow_tools=True, timeout=declaration['timeout_s'])
        answer = result['parsed_final']
        if set(answer) != {'answer'} or not isinstance(answer['answer'], str) or not answer['answer'].strip():
            raise ValueError('invalid response answer')
        save(output/'B2.json', {'answer': answer['answer'], 'cache_key': result['cache_key'],
                               'latency_s': result['latency_s'], 'model_calls': 1})
        save(output/'B4.json', {'answer': json.loads(checked(entry['candidate']).read_text())['answer'], 'model_calls': 0})
        record = {'status': 'COMPLETE_RESPONSE_SUPPORT_UNJUDGED', 'source_identity': identity}
    except Exception as error:
        record = {'status': 'TECHNICAL_RESPONSE_FAILURE', 'error': str(error), 'source_identity': identity}
    record.update(confirmation_n=0, replication_n=0, alpha_consumed=0, quality_retries=0)
    save(terminal, record)
    return record


def run(declaration_path, output_root, workers=2, *, caller=call):
    if not 1 <= workers <= 2:
        raise ValueError('one or two isolated response workers required')
    d = json.loads(Path(declaration_path).read_text())
    if d['disposition'] != 'DEVELOPMENT_ONLY_NO_CONFIRMATORY_INFERENCE':
        raise ValueError('development declaration required')
    # Verify the complete snapshot before the first provider request.
    for b in [d['registry'], d['source_declaration'], d['runner'], d['transport'], d['prompt'], *d['method_sources'], *d.get('prior_declarations', [])]:
        checked(b)
    for a in d['capture_accounting']:
        if 'capture_terminal' in a: checked(a['capture_terminal'])
        if 'original_capture_terminal' in a: checked(a['original_capture_terminal'])
        for raw in a.get('raw_sources', []): checked(raw)
    for entry in d['entries']:
        for key in ('packet', 'candidate', 'effective_configuration'): checked(entry[key])
    with ThreadPoolExecutor(max_workers=workers) as pool:
        jobs = [pool.submit(execute, e, d, declaration_path, output_root, caller=caller) for e in d['entries']]
        for job in as_completed(jobs):
            result = job.result()
            print(result['status'], flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    commands = p.add_subparsers(dest='command', required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('--registry', type=Path, required=True)
    prep.add_argument('--capture-root', type=Path, required=True)
    prep.add_argument('--declaration', type=Path, required=True)
    prep.add_argument('--allow-completed-subset', action='store_true')
    prep.add_argument('--prior-declaration', action='append', type=Path, default=[])
    prep.add_argument('--source-declaration', type=Path, default=DOC/'contact_policy_response_declaration_v2.json')
    execute_parser = commands.add_parser('run')
    execute_parser.add_argument('--declaration', type=Path, required=True)
    execute_parser.add_argument('--output-root', type=Path, required=True)
    execute_parser.add_argument('--workers', type=int, default=2)
    a = p.parse_args()
    if a.command == 'prepare':
        d = prepare(a.registry, a.capture_root, a.declaration, allow_completed_subset=a.allow_completed_subset, source_declaration=a.source_declaration, prior_declarations=a.prior_declaration)
        print('Predeclared development responses:', len(d['entries']))
    else:
        run(a.declaration, a.output_root, a.workers)


if __name__ == '__main__':
    main()
