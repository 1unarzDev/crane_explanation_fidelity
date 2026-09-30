#!/usr/bin/env python3
"""No-tool blind developer extraction/role coding; qualified support stays separate."""
import argparse
import hashlib
import json
import os
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

from audit_release import ROOT, sha, write
from verify_v3 import V3, study
from evidence_calibration_io import canonical_sha256
from run_evidence_calibration_agent_annotation import StructuredCodexCliAgentCaller

LEVELS = ['task_outcome', 'software_action_failure', 'recorded_override_state',
          'specific_physical_cause', 'limitation']
ATOM = {'type': 'object', 'additionalProperties': False, 'required': ['statement', 'response_span', 'asserted_abstraction_level'],
        'properties': {'statement': {'type': 'string'}, 'response_span': {'type': 'string'},
                       'asserted_abstraction_level': {'type': 'string', 'enum': LEVELS}}}
EXTRACT_SCHEMA = {'type': 'object', 'additionalProperties': False, 'required': ['items'],
                  'properties': {'items': {'type': 'array', 'items': {'type': 'object', 'additionalProperties': False,
                      'required': ['unique_text_id', 'atoms'], 'properties': {'unique_text_id': {'type': 'string'},
                          'atoms': {'type': 'array', 'items': ATOM}}}}}}
ROLE_SCHEMA = {'type': 'object', 'additionalProperties': False, 'required': ['items'],
               'properties': {'items': {'type': 'array', 'items': {'type': 'object', 'additionalProperties': False,
                   'required': ['atom_id', 'causal_role'], 'properties': {'atom_id': {'type': 'string'},
                       'causal_role': {'type': ['boolean', 'null']}}}}}}


def read(path):
    return json.loads(path.read_text())


def immutable(path, value):
    if path.exists():
        assert read(path) == value
    else:
        write(path, value)


def validate_spans(text, atoms):
    assert atoms and all(a['statement'].strip() and a['response_span'] in text and
                         a['asserted_abstraction_level'] in LEVELS for a in atoms)
    covered = set()
    for atom in atoms:
        start = 0
        while (position := text.find(atom['response_span'], start)) >= 0:
            covered.update(range(position, position + len(atom['response_span'])))
            start = position + 1
    assert all(i in covered for i, char in enumerate(text) if not char.isspace())


def project(ann):
    summary = read(V3 / 'reserved/run_summary.json')
    assert summary['n_recordings'] == 12 and summary['valid'] + summary['technical_failures'] == 324
    bank = read(ann / 'blind_bank.json')['items']
    by_hash = {}
    for row in bank:
        text = row['response_text']
        digest = hashlib.sha256(text.encode()).hexdigest()
        by_hash.setdefault(digest, {'unique_text_id': 'u-' + digest, 'response_text': text, 'response_ids': []})['response_ids'].append(row['response_id'])
    rows = [by_hash[key] for key in sorted(by_hash)]
    immutable(ann / 'extraction/blind_text_projection.json', {'items': rows, 'evidence_or_keys_exported': False})
    declaration = {'schema': 'hexar-blind-extraction-executor/v3', 'bank_sha256': sha(ann / 'blind_bank.json'),
                   'projection_sha256': sha(ann / 'extraction/blind_text_projection.json'),
                   'extract_prompt_sha256': sha(ROOT / 'docs/hexar_external/v3/EXTRACTION_TASK.txt'),
                   'role_prompt_sha256': sha(ROOT / 'docs/hexar_external/v3/ROLE_CODING_TASK.txt'),
                   'extract_schema_sha256': canonical_sha256(EXTRACT_SCHEMA), 'role_schema_sha256': canonical_sha256(ROLE_SCHEMA),
                   'executor_sha256': sha(ROOT / 'analysis/hexar_external/extract_v3.py'),
                   'model': 'gpt-6-astra', 'effort': 'high', 'workers': 2, 'batch_unique_texts': 6,
                   'tools': 'none', 'qualified_or_human_validated_extraction': False,
                   'quality_retries': 0, 'technical_retries': 0, 'primary_endpoint_changed': False,
                   'binding_time': 'after fixed method/reference release, before extraction/support calls; no comparative support outputs inspected',
                   'route': 'isolated structured developer agent, independent parent completeness/role review required'}
    immutable(ann / 'extraction/executor_binding.json', declaration)
    print('BLIND_EXTRACTION_PROJECTED', len(bank), len(rows))


def calls(ann, role=False):
    projection = read(ann / 'extraction/blind_text_projection.json')['items']
    binding = read(ann / 'extraction/executor_binding.json')
    assert binding['executor_sha256'] == sha(ROOT / 'analysis/hexar_external/extract_v3.py')
    task = 'roles' if role else 'atoms'
    prompt_name = 'ROLE_CODING_TASK.txt' if role else 'EXTRACTION_TASK.txt'
    prompt_path = ROOT / 'docs/hexar_external/v3' / prompt_name
    assert sha(prompt_path) == binding['role_prompt_sha256' if role else 'extract_prompt_sha256']
    schema = ROLE_SCHEMA if role else EXTRACT_SCHEMA
    if role:
        review = read(ann / 'parent_inventory_review.json')
        assert review['inventory_sha256'] == sha(ann / 'atomic_inventory.json')
        assert review['all_unique_texts_reviewed'] and not review['support_labels_accessed']
        inventory = read(ann / 'atomic_inventory.json')['items']
        by_response = {r['response_id']: r for r in inventory}
        inputs = []
        for text in projection:
            atoms = by_response[text['response_ids'][0]]['atoms']
            inputs.append({'unique_text_id': text['unique_text_id'], 'response_text': text['response_text'],
                           'atoms': [{'atom_id': text['unique_text_id'] + f'-a{i:03d}',
                                      'statement': a['statement'], 'response_span': a['response_span']}
                                     for i, a in enumerate(atoms, 1)]})
    else:
        inputs = [{k: row[k] for k in ('unique_text_id', 'response_text')} for row in projection]
    temp = V3 / 'tmp'; temp.mkdir(exist_ok=True); os.environ['TMPDIR'] = str(temp); tempfile.tempdir = str(temp)
    batches = [inputs[i:i + 6] for i in range(0, len(inputs), 6)]
    def job(pair):
        number, rows = pair
        dest = ann / 'extraction' / task / f'batch-{number:03d}.json'
        if dest.exists():
            return read(dest)
        caller = StructuredCodexCliAgentCaller(ann / 'extraction' / task / 'calls', model='gpt-6-astra', effort='high', timeout_s=240)
        try:
            returned = caller.call(logical_role=f'hexar-v3-blind-{task}-{number:03d}',
                                   payload={'task': task, 'items': rows}, schema=schema, prompt=prompt_path.read_text())['parsed_final']
            expected = {a['atom_id'] for r in rows for a in r['atoms']} if role else {r['unique_text_id'] for r in rows}
            field = 'atom_id' if role else 'unique_text_id'
            assert {r[field] for r in returned['items']} == expected and len(returned['items']) == len(expected)
            if not role:
                texts = {r['unique_text_id']: r['response_text'] for r in rows}
                for record in returned['items']:
                    validate_spans(texts[record['unique_text_id']], record['atoms'])
            result = {'status': 'VALID', 'items': returned['items'], 'payload_sha256': canonical_sha256(rows), 'retry': False}
        except Exception as error:
            result = {'status': 'TECHNICAL_FAILURE', 'error': str(error), 'payload_sha256': canonical_sha256(rows), 'retry': False}
        write(dest, result); print(task, number, result['status'], flush=True); return result
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(job, enumerate(batches, 1)))
    immutable(ann / 'extraction' / task / 'summary.json', {'batches': len(batches),
              'valid': sum(r['status'] == 'VALID' for r in results), 'technical_failures': sum(r['status'] != 'VALID' for r in results),
              'quality_retries': 0, 'technical_retries': 0, 'qualified_extraction': False})


def assemble(ann):
    projection = read(ann / 'extraction/blind_text_projection.json')['items']
    candidates = {}
    for path in sorted((ann / 'extraction/atoms').glob('batch-*.json')):
        batch = read(path)
        if batch['status'] == 'VALID':
            for row in batch['items']:
                assert row['unique_text_id'] not in candidates
                candidates[row['unique_text_id']] = row['atoms']
    manual = ann / 'extraction/manual_completion.json'
    if manual.exists():
        for row in read(manual)['items']:
            assert row['unique_text_id'] not in candidates, 'Cannot silently overwrite a valid extraction.'
            candidates[row['unique_text_id']] = row['atoms']
    assert set(candidates) == {r['unique_text_id'] for r in projection}, 'Missing extraction stays unresolved; manual independent completion requires separate provenance.'
    items = []
    for row in projection:
        text = row['response_text']; atoms = candidates[row['unique_text_id']]
        validate_spans(text, atoms)
        for response_id in row['response_ids']:
            items.append({'response_id': response_id, 'response_text_sha256': hashlib.sha256(text.encode()).hexdigest(),
                           'atoms': [{**a, 'item_id': response_id + f'-a{i:03d}'} for i, a in enumerate(atoms, 1)]})
    immutable(ann / 'extraction/inventory_candidate.json', {'schema': 'hexar-method-blind-developer-inventory/v3', 'items': items,
              'extractor_qualified': False, 'human_validated': False, 'parent_completeness_review_required': True})
    print('INVENTORY_CANDIDATE_ASSEMBLED_PARENT_REVIEW_REQUIRED', len(items), sum(len(r['atoms']) for r in items))


def assemble_roles(ann):
    projection = read(ann / 'extraction/blind_text_projection.json')['items']
    coded = {}
    for path in sorted((ann / 'extraction/roles').glob('batch-*.json')):
        batch = read(path)
        if batch['status'] == 'VALID':
            for row in batch['items']:
                coded[row['atom_id']] = row['causal_role']
    inventory = {r['response_id']: r for r in read(ann / 'atomic_inventory.json')['items']}
    rows = []; parent = []
    for text in projection:
        for response_id in text['response_ids']:
            for i, atom in enumerate(inventory[response_id]['atoms'], 1):
                uid = text['unique_text_id'] + f'-a{i:03d}'
                rows.append({'item_id': atom['item_id'], 'causal_role': coded.get(uid)})
                parent.append({'item_id': atom['item_id'], 'statement': atom['statement'],
                               'response_span': atom['response_span'], 'response_text': text['response_text']})
    immutable(ann / 'causal_roles.coder.json', {'inventory_sha256': sha(ann / 'atomic_inventory.json'),
              'method_blind': True, 'support_labels_accessed': False, 'items': rows,
              'failed_role_returns_remain_null': True, 'coder_qualified': False})
    immutable(ann / 'causal_roles.parent_projection.json', {'items': parent, 'coder_labels_exported': False})
    print('CAUSAL_ROLES_CODED_WITH_UNKNOWN_FAILURES', len(rows))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', choices=['project', 'extract', 'assemble', 'roles', 'assemble-roles'], required=True)
    args = parser.parse_args(); study()
    ann = V3 / 'reserved/annotation'
    {'project': project, 'extract': calls, 'assemble': assemble,
     'roles': lambda a: calls(a, role=True), 'assemble-roles': assemble_roles}[args.stage](ann)


if __name__ == '__main__':
    main()
