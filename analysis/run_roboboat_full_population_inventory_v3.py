#!/usr/bin/env python3
"""600-second fresh development arm. Immutable development response bank and two-pass qualified marine extraction.

Extraction deduplication never changes response joins or independent N. Structural
returns still require exact-source complete-source project review before scoring.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import tempfile

from build_roboboat_terminal_batch import ROOT, DOC, digest, save
from roboboat_annotation_deadline_v2 import safe_execute as execute, execution_sources, EXECUTION_CONTRACT
import run_roboboat_population_inventory_v1 as base
import run_roboboat_full_population_responses_v2 as responses
from roboboat_runtime_source_closure_v1 import source_closure as runtime_source_closure

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


def provider_receipt(entry, declaration, declaration_path, response_root, answer):
    """Bind the actual one-call provider return, including operational amendments."""
    key=answer.get('cache_key')
    if not isinstance(key,str) or len(key)!=64 or any(c not in '0123456789abcdef' for c in key):
        raise ValueError('provider receipt cache identity required')
    path=Path(response_root)/'calls'/(key+'.json')
    raw=json.loads(path.read_text());request=raw['request'];dependencies=[path]
    if (raw.get('status')!='valid' or raw.get('attempt_count')!=1 or raw.get('return_code')!=0
            or raw.get('cache_key')!=key or hashlib.sha256(json.dumps(request,sort_keys=True).encode()).hexdigest()!=key
            or raw.get('parsed_final')!={'answer':answer['answer']}):
        raise ValueError('B2 answer differs from valid single-call provider receipt')
    with tempfile.TemporaryDirectory(prefix='boat-receipt-verify-') as temporary:
        work=Path(temporary);responses.stage(entry,declaration,work)
        hashes={p.relative_to(work).as_posix():digest(p) for p in work.rglob('*') if p.is_file()}
    expected={'role':entry['id'],'model':declaration['B2']['model'],'effort':declaration['B2']['effort'],
        'prompt':checked(declaration['prompt']).read_text(),'schema':declaration['return_schema'],
        'allow_tools':True,'workspace_files':hashes}
    if any(request.get(k)!=v for k,v in expected.items()):
        raise ValueError('provider receipt differs from declared source/tool/request interface')
    if request.get('transport')=='marine-isolated-login-cli/v1':
        if request.get('transport_sha256')!=declaration['transport']['sha256']:
            raise ValueError('original provider transport source mismatch')
    elif request.get('transport') in ('marine-isolated-login-cli/v2-safe-errors','marine-isolated-login-cli/v3-decoded-safe-errors'):
        marker=Path(response_root)/'transport-amendment-bindings.json'
        table=json.loads(marker.read_text());dependencies.append(marker);matching=[]
        if table['schema']!='roboboat-response-operational-amendments/v1' or table['quality_reissues']!=0:
            raise ValueError('operational transport amendment scope mismatch')
        for b in table['amendments']:
            amendment_path=checked(b);a=json.loads(amendment_path.read_text())
            dependencies += [amendment_path,*[checked(v) for v in source_bindings(a)]]
            if entry['id'] in a['untouched_entry_ids']:
                matching.append(a)
        if len(matching)!=1:raise ValueError('provider receipt needs one registered untouched-request amendment')
        a=matching[0]
        expected_amendment_schema='roboboat-full-response-transport-safety-amendment/'+('v2' if request['transport']=='marine-isolated-login-cli/v3-decoded-safe-errors' else 'v1')
        if (a['schema']!=expected_amendment_schema
                or a['phase']!='DEVELOPMENT_ONLY_BEFORE_UNTOUCHED_CALLS'
                or a['output_root']!=str(Path(response_root).resolve())
                or a['original_declaration']!=binding(declaration_path) or a['reissued_entries']
                or a['quality_retries']!=0 or request.get('transport_sha256')!=a['safe_transport']['sha256']
                or request.get('isolation_source_sha256')!=declaration['transport']['sha256']
                or request.get('timeout_s')!=declaration['timeout_s']):
            raise ValueError('safe provider transport receipt/amendment mismatch')
        settings={'B2':declaration['B2'],'B4':declaration['B4'],'timeout_s':declaration['timeout_s'],
                  'prompt':declaration['prompt'],'max_workers':2}
        if a['settings_unchanged']!=settings:raise ValueError('operational amendment changed scientific settings')
    else:
        raise ValueError('unregistered provider transport receipt')
    return path,dependencies


def verify_response_snapshot(declaration,path):
    responses.verify(declaration,path)
    if (declaration['max_workers']!=2 or declaration['return_schema']!=responses.SCHEMA
            or declaration['configuration_basis']!=responses.BASIS):
        raise ValueError('full method interface changed')
    registry=json.loads(checked(declaration['registry']).read_text())
    rows={row['id']:row for row in registry['rows']}
    if len(rows)!=len(registry['rows']): raise ValueError('duplicate geometry row identity')
    for entry in declaration['entries']:
        row=rows.get(entry['row_id'])
        if (row is None or entry['cluster_id']!=row['cluster_id']
                or type(entry['level']) is not int or entry['level'] not in (0,1,2)
                or entry['id']!=entry['row_id']+f"-L{entry['level']}"):
            raise ValueError('full response geometry/ladder identity mismatch')
    closure=responses.source_closure(checked(declaration['source_declaration']))
    expected={(s['relative_path'],s['sha256']) for s in closure}
    actual={(s['relative_path'],s['sha256']) for s in declaration['method_sources']}
    if actual!=expected or len(actual)!=len(declaration['method_sources']):
        raise ValueError('full method source closure mismatch')


def answer_sources(entry, declaration, declaration_path, response_root):
    """Admit only genuine terminal-bound answers; retain every missing/failure slot."""
    generation=entry['candidate_generation']
    expected_generation={'method':responses.B4,'generator':'analysis/roboboat_full_crane_v2.py',
        'configuration_id':entry['cluster_id'],'episode_id':entry['row_id'],'condition_id':entry['id'],
        'output_relative_path':'responses/'+entry['id']+'/B4.json',
        'full_pipeline_relative_path':'responses/'+entry['id']+'/full-pipeline-B4.json',
        'output_binding':'post-declaration response terminal; no precomputed answers staged'}
    if generation != expected_generation: raise ValueError('full B4 generation intent mismatch')
    response_root = Path(response_root).resolve()
    folder = response_root/'responses'/entry['id']
    expected = {'declaration_sha256':digest(declaration_path), 'entry':entry}
    item = {'response_id':entry['id'], 'row_id':entry['row_id'], 'cluster_id':entry['cluster_id'],
            'level':entry['level'], 'source_identity':expected, 'methods':{}}
    dependencies, missing, answers = [], [], []
    intent = response_root/'intents'/(entry['id']+'.json')
    terminal = folder/'response-terminal.json'
    record = None
    if intent.exists():
        if json.loads(intent.read_text()) != expected: raise ValueError('response intent source mismatch')
        dependencies.append(intent); item['method_call_intent'] = binding(intent)
    else:
        missing.append(str(intent))
    if terminal.exists():
        record = json.loads(terminal.read_text())
        if record['source_identity'] != expected or record['status'] not in (
                'COMPLETE_RESPONSE_SUPPORT_UNJUDGED','TECHNICAL_RESPONSE_FAILURE'):
            raise ValueError('response terminal source mismatch')
        if not intent.exists(): raise ValueError('terminal lacks execution intent')
        if record['quality_retries'] != 0 or record['confirmation_n'] != 0 or record['replication_n'] != 0:
            raise ValueError('response execution scope changed')
        dependencies.append(terminal)
        item.update(method_call_status=record['status'],terminal=binding(terminal),error=record.get('error'))
        for value in record['retained_outputs'].values(): dependencies.append(checked(value))
    else:
        missing.append(str(terminal)); item['method_call_status']='MISSING_RESPONSE_TERMINAL'
    for method in ('B2','B4'):
        path = folder/(method+'.json')
        if not path.exists():
            missing.append(str(path)); item['methods'][method]='MISSING_ANSWER'
            if record and record['status']=='COMPLETE_RESPONSE_SUPPORT_UNJUDGED':
                raise ValueError('complete terminal missing answer')
            continue
        dependencies.append(path)
        if record is None:
            item['methods'][method]='ORPHAN_ANSWER_UNBOUND_TERMINAL_EXCLUDED'
            item[method+'_orphan_answer']=binding(path)
            continue
        if record['retained_outputs'].get(method+'.json') != binding(path):
            raise ValueError('retained answer binding mismatch')
        value=json.loads(path.read_text())
        if method=='B4':
            if record.get('B4_candidate') != binding(path): raise ValueError('full B4 candidate binding mismatch')
            full_path=folder/'full-pipeline-B4.json'
            if (record.get('B4_full_pipeline', record['retained_outputs'].get('full-pipeline-B4.json')) != binding(full_path)
                    or record['retained_outputs'].get('full-pipeline-B4.json') != binding(full_path)
                    or value.get('full_pipeline') != binding(full_path)):
                raise ValueError('full pipeline binding mismatch')
            generation={'declaration_sha256':expected['declaration_sha256'],
                'packet':entry['packet'],'effective_configuration':entry['effective_configuration'],
                'capture_terminal':entry['capture_terminal'],'candidate_generation':entry['candidate_generation'],
                'source_snapshots':[{'relative_path':source['relative_path'],**source['snapshot']}
                                    for source in declaration['method_sources']]}
            if (value.get('method') != responses.B4 or value.get('model_calls') != 0
                    or value.get('generation_provenance') != generation
                    or entry['candidate_generation']['method'] != responses.B4):
                raise ValueError('full B4 method/generation provenance mismatch')
            full=json.loads(full_path.read_text())
            regenerated=responses.generate_b4(entry,declaration)
            if full != regenerated or value['answer'] != full['realization']['final_response']:
                raise ValueError('candidate differs from genuine source-bound full B4')
            dependencies.append(full_path)
            provenance={'kind':'FULL_CRANE_V2_TERMINAL_BOUND_ZERO_MODEL','method':responses.B4,
                        'execution_intent':binding(intent),'terminal':binding(terminal),
                        'full_pipeline':binding(full_path),'generation':generation}
        else:
            if value.get('model_calls') != 1: raise ValueError('B2 call provenance mismatch')
            receipt,receipt_dependencies=provider_receipt(entry,declaration,declaration_path,response_root,value)
            dependencies.extend(receipt_dependencies)
            provenance={'kind':'SOURCE_BOUND_METHOD_RETURN','execution_intent':binding(intent),
                        'terminal':binding(terminal),'provider_receipt':binding(receipt)}
        if not isinstance(value.get('answer'),str) or not value['answer'].strip():
            raise ValueError('nonempty answer required')
        answers.append({'method':method,'path':path,'answer':value['answer'],'provenance':provenance})
        item['methods'][method]='INCLUDED_VALID_ANSWER'
    return item, answers, dependencies, missing


def prepare(response_declaration, response_root, output_root, declaration):
    declaration, output_root = Path(declaration).resolve(), Path(output_root).resolve()
    response_declaration, response_root = Path(response_declaration).resolve(), Path(response_root).resolve()
    if declaration.exists() or output_root.exists():
        raise ValueError('one-shot extraction declaration/bank already exists')
    d = json.loads(response_declaration.read_text())
    if d['schema'] != responses.DECLARATION_SCHEMA or d['disposition'] != 'DEVELOPMENT_ONLY_NO_CONFIRMATORY_INFERENCE':
        raise ValueError('immutable development response snapshot required')
    verify_response_snapshot(d, response_declaration)
    if len({e['id'] for e in d['entries']}) != len(d['entries']):
        raise ValueError('duplicate response identity')
    freeze, extractor_paths = extractor_sources()
    dependencies = [response_declaration, Path(__file__), Path(base.__file__), Path(responses.__file__), ROOT/'tests/test_roboboat_full_population_inventory_v2.py', *extractor_paths]
    dependencies.extend(execution_sources())
    dependencies.extend(runtime_source_closure([Path(__file__), *execution_sources(), Path(base.__file__), Path(responses.__file__)]))
    dependencies.extend(ROOT/"analysis"/name for name in (
        "validate_evidence_calibration_atomization.py", "build_roboboat_terminal_batch.py"))
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
        item, sources, retained, absent = answer_sources(entry, d, response_declaration, response_root)
        accounting.append(item)
        dependencies.extend(retained)
        missing.extend(absent)
        for answer in sources:
            add_answer(entry, answer['method'], answer['path'], answer['answer'], answer['provenance'])
    blind = output_root/'blind-bank.json'
    join = output_root/'evaluator-join.json'
    ledger = output_root/'response-accounting.json'
    save(blind, {'entries': [{'opaque_response_id': key, 'response_text': value} for key, value in sorted(texts.items())]})
    save(join, {'entries': joins, 'annotation_input': False})
    save(ledger, {'entries': accounting, 'capture_accounting': d['capture_accounting'], 'annotation_input': False})
    dependencies.extend([blind, join, ledger])
    result = {'schema': 'roboboat-full-population-inventory-declaration/v3', 'disposition': DISPOSITION,
              'method_scope': responses.B4, 'response_root':str(response_root),
              'dependencies': [binding(p) for p in dict.fromkeys(dependencies)],
              'missing_source_paths': sorted(set(missing)), 'output_root': str(output_root),
              'response_declaration': binding(response_declaration), 'extractor_freeze': binding(DOC/'marine_atomization_freeze_v5.json'),
              'snapshot_entry_count': len(d['entries']), 'original_answers': len(joins),
              'method_answer_counts': {m: sum(j['method'] == m for j in joins) for m in ('B2', 'B4')},
              'unique_answer_texts': len(texts), 'model': freeze['candidate'], 'passes': 2,
              'max_concurrent_calls': 2, 'quality_retries': 0, 'timeout_s':600,
              'selection': 'All immutable snapshot entries, valid source-bound B2 returns and every terminal-bound full-CRANE B4; failures and missing calls retained without outcome-based selection.',
              'execution_contract': EXECUTION_CONTRACT,
              'qualification': 'Unchanged qualified atomizer and marine actor/clock/phase appendix v5; exact-source complete-source project review required before support scoring.',
              'semantic_completeness_established': False, 'support_annotation_authorized': False,
              'endpoint_scoring_authorized': False, 'new_independent_configuration_n': 0,
              'confirmation_n': 0, 'replication_n': 0, 'alpha_consumed': 0}
    save(declaration, result)
    save(output_root/'inventory-binding.json', {'declaration':binding(declaration)})
    return result


def run(declaration, output_root, *, executor=execute):
    d = json.loads(Path(declaration).read_text())
    if (d['schema'] != 'roboboat-full-population-inventory-declaration/v3' or d['method_scope'] != responses.B4
            or d['timeout_s'] != 600):
        raise ValueError('full-method inventory required')
    # Generic execution accepts the genuine declaration and uses the same
    # qualified two-pass extractor. No legacy schema/candidate is fabricated.
    return base.run(declaration, output_root, executor=executor)


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
