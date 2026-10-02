#!/usr/bin/env python3
"""Full-CRANE paired development method-reuse sensitivity; never confirmation."""
import argparse
import ast
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from build_roboboat_terminal_batch import ROOT, DOC, save, digest
from roboboat_isolated_transport import call
from run_roboboat_population_development_v1 import technical_checks
from run_roboboat_population_responses_v1 import SCHEMA, BASIS

DECLARATION_SCHEMA = 'roboboat-full-population-response-declaration/v2'
DISPOSITION = 'DEVELOPMENT_ONLY_NO_CONFIRMATORY_INFERENCE'
B2 = {'model': 'gpt-6-astra', 'effort': 'high', 'tools': True, 'quality_retry': False}
B4 = 'full-crane-v2/deterministic-zero-model-closed-template'
PROMPT = DOC / 'marine_full_b2_reuse_prompt_v2.txt'


def binding(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': digest(path)}


def checked(value):
    path = Path(value['path'])
    if not path.is_absolute():
        path = ROOT / path
    if digest(path) != value['sha256']:
        raise ValueError('bound input changed: ' + str(path))
    return path


def source_closure(source_declaration):
    source = json.loads(Path(source_declaration).read_text())
    paths = set()
    for value in source['method_sources']:
        paths.add(checked(value))
    pending = [ROOT / 'analysis' / name for name in ('roboboat_full_crane_v2.py',
        'maximal_supported_diagnosis.py', 'realize_evidence_calibrated_explanation.py',
        'evidence_calibration.py', 'evidence_calibration_io.py')]
    while pending:
        path = pending.pop().resolve()
        if path in paths:
            continue
        paths.add(path)
        for node in ast.walk(ast.parse(path.read_text())):
            names = ([node.module.split('.')[0]] if isinstance(node, ast.ImportFrom) and node.module
                     else [item.name.split('.')[0] for item in node.names] if isinstance(node, ast.Import) else [])
            for name in names:
                dependency = ROOT / 'analysis' / (name + '.py')
                if dependency.is_file() and dependency.resolve() not in paths:
                    pending.append(dependency)
    paths.add(ROOT / 'configs/roboboat_claim_contracts_v2_development.json')
    result = []
    for path in sorted(paths):
        relative = path.relative_to(ROOT).as_posix()
        if not relative.startswith(('analysis/', 'configs/')) or any(
                token in relative for token in ('reference_', 'evaluator', 'judge', 'gold')):
            raise ValueError('forbidden method source: ' + relative)
        result.append({**binding(path), 'relative_path': relative})
    return result


def capture_bindings(capture, terminal, record, registry_path, row):
    if record['registry_sha256'] != digest(registry_path) or record['row'] != row:
        raise ValueError('capture population identity mismatch')
    raw = []
    if 'original_capture_terminal' in record:
        checked(record['original_capture_terminal'])
        raw.append(record['original_capture_terminal'])
        for value in record['raw_sources']:
            checked(value)
            raw.append(value)
    for name in ('navigation-reset-summary.json', 'worker-0/result.json', 'fixture-summary.json',
                 'runtime-parameters.json'):
        path = capture / name
        if not path.is_file():
            raise ValueError('incomplete valid capture: ' + name)
        raw.append(binding(path))
    summary = json.loads((capture / 'navigation-reset-summary.json').read_text())
    worker = json.loads((capture / 'worker-0/result.json').read_text())
    fixture = json.loads((capture / 'fixture-summary.json').read_text())
    if not all(technical_checks(summary, worker, fixture).values()):
        raise ValueError('valid terminal contradicts strict capture admission')
    original = json.loads(checked(record['original_capture_terminal']).read_text()) if 'original_capture_terminal' in record else record
    if original.get('return_code') not in (0, 1):
        raise ValueError('capture launcher incomplete')
    if original['return_code'] == 1 and fixture['status'] == summary['expectedNavigationStatus']:
        raise ValueError('non-outcome launcher failure')
    return {'capture_terminal': binding(terminal), 'raw_sources': raw}


def prepare(registry_path, capture_root, declaration_path, *, allow_completed_subset=False,
            source_declaration=DOC/'contact_policy_response_declaration_v2.json', prior_declarations=()):
    registry_path, capture_root, declaration_path = map(lambda x: Path(x).resolve(),
                                                       (registry_path, capture_root, declaration_path))
    snapshots = declaration_path.with_name(declaration_path.stem + '-sources')
    if declaration_path.exists() or snapshots.exists():
        raise ValueError('immutable declaration/source snapshot already exists')
    registry = json.loads(registry_path.read_text())
    if registry['status'] != 'DEVELOPMENT_EXPLORATORY_NOT_CONFIRMATION':
        raise ValueError('development population required')
    if len({row['id'] for row in registry['rows']}) != len(registry['rows']):
        raise ValueError('duplicate population identity')
    methods = source_closure(source_declaration)
    entries, accounting, already, prior_bindings = [], [], set(), []
    for prior in prior_declarations:
        previous = json.loads(Path(prior).read_text())
        if (previous['schema'] != DECLARATION_SCHEMA or previous['registry']['sha256'] != digest(registry_path)
                or previous['B2'] != B2 or previous['B4'] != B4
                or previous['prompt']['sha256'] != digest(PROMPT)
                or previous['return_schema'] != SCHEMA or previous['timeout_s'] != 300
                or previous['transport']['sha256'] != digest(ROOT/'analysis/roboboat_isolated_transport.py')
                or previous['runner']['sha256'] != digest(Path(__file__))
                or [(s['relative_path'], s['sha256']) for s in previous['method_sources']] !=
                   [(s['relative_path'], s['sha256']) for s in methods]):
            raise ValueError('prior declaration belongs to different population/method interface')
        prior_bindings.append(binding(prior))
        already.update(entry['id'] for entry in previous['entries'])
    for row in registry['rows']:
        capture = capture_root / row['id']
        terminal = capture/'capture-export-terminal-v2.json'
        if not terminal.exists():
            terminal = capture/'capture-attempt.json'
        if not terminal.exists():
            accounting.append({'id':row['id'], 'status':'PENDING'})
            continue
        record = json.loads(terminal.read_text())
        if record['registry_sha256'] != digest(registry_path) or record['row'] != row:
            raise ValueError('capture population identity mismatch')
        if record['status'] not in ('VALID_DEVELOPMENT', 'TECHNICAL_FAILURE'):
            raise ValueError('unresolved capture attempt: ' + row['id'])
        item = {'id':row['id'], 'status':record['status'], 'capture_terminal':binding(terminal),
                'error':record.get('error')}
        accounting.append(item)
        if record['status'] != 'VALID_DEVELOPMENT':
            continue
        item.update(capture_bindings(capture, terminal, record, registry_path, row))
        export = capture / record.get('export_directory', '.')
        for level in range(3):
            identifier = row['id'] + f'-L{level}'
            if identifier in already:
                continue
            entries.append({'id':identifier, 'row_id':row['id'], 'cluster_id':row['cluster_id'],
                'level':level, 'packet':binding(export/'method_packets'/f'L{level}.json'),
                'effective_configuration':binding(export/'effective-configuration.yaml'),
                'capture_terminal':binding(terminal),
                'candidate_generation':{'method':B4,'generator':'analysis/roboboat_full_crane_v2.py',
                    'configuration_id':row['cluster_id'],'episode_id':row['id'],'condition_id':identifier,
                    'output_relative_path':'responses/'+identifier+'/B4.json',
                    'full_pipeline_relative_path':'responses/'+identifier+'/full-pipeline-B4.json',
                    'output_binding':'post-declaration response terminal; no precomputed answers staged'}})
    if any(item['status']=='PENDING' for item in accounting) and not allow_completed_subset:
        raise ValueError('population incomplete; explicit completed-subset snapshot required')
    snapshots.mkdir(parents=True, exist_ok=False)
    for source in methods:
        destination = snapshots / source['relative_path']
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(checked(source), destination)
        source['snapshot'] = binding(destination)
    declaration = {'schema':DECLARATION_SCHEMA, 'disposition':DISPOSITION,
        'comparison':'METHOD_REUSE_SENSITIVITY_FULL_DETERMINISTIC_B4_NO_PRIMARY_PROMOTION',
        'registry':binding(registry_path), 'source_declaration':binding(source_declaration),
        'runner':binding(__file__), 'transport':binding(ROOT/'analysis/roboboat_isolated_transport.py'),
        'capture_admission':binding(ROOT/'analysis/run_roboboat_population_development_v1.py'),
        'prompt':binding(PROMPT), 'method_sources':methods, 'B2':B2, 'B4':B4,
        'return_schema':SCHEMA, 'configuration_basis':BASIS, 'entries':entries,
        'capture_accounting':accounting, 'prior_declarations':prior_bindings,
        'selection':'All technically valid completed rows/all L0-L2 absent from same-interface prior declarations; no physical/method outcome selection',
        'completed_subset':allow_completed_subset, 'max_workers':2, 'timeout_s':300,
        'quality_retries':0, 'confirmation_n':0, 'replication_n':0, 'alpha_consumed':0,
        'annotation_status':'NOT_RUN'}
    declaration_path.parent.mkdir(parents=True, exist_ok=True)
    with declaration_path.open('x') as stream:
        json.dump(declaration, stream, indent=2)
    return declaration


def verify(declaration, declaration_path):
    if json.loads(Path(declaration_path).read_text()) != declaration:
        raise ValueError('in-memory declaration differs from locked declaration')
    if declaration['schema'] != DECLARATION_SCHEMA or declaration['disposition'] != DISPOSITION:
        raise ValueError('full paired development declaration required')
    if declaration['B2'] != B2 or declaration['B4'] != B4 or declaration['timeout_s'] != 300 or declaration['quality_retries'] != 0:
        raise ValueError('method settings changed')
    for key in ('registry','source_declaration','runner','transport','capture_admission','prompt'):
        checked(declaration[key])
    for source in declaration['method_sources']:
        checked(source)
        if checked(source['snapshot']).read_bytes() != checked(source).read_bytes():
            raise ValueError('source snapshot differs')
    for value in declaration['prior_declarations']:
        checked(value)
    for item in declaration['capture_accounting']:
        if 'capture_terminal' in item:
            checked(item['capture_terminal'])
        for value in item.get('raw_sources', []):
            checked(value)
    for entry in declaration['entries']:
        for key in ('packet','effective_configuration','capture_terminal'):
            checked(entry[key])


def stage(entry, declaration, work):
    for source in declaration['method_sources']:
        destination = work / source['relative_path']
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(checked(source['snapshot']), destination)
    shutil.copyfile(checked(entry['packet']), work/'evidence.json')
    shutil.copyfile(checked(entry['effective_configuration']), work/'effective-configuration.yaml')
    save(work/'configuration-basis.json', declaration['configuration_basis'])


def generate_b4(entry, declaration):
    with tempfile.TemporaryDirectory(prefix='boat-full-b4-') as temporary:
        work = Path(temporary)
        stage(entry, declaration, work)
        output = work/'full-pipeline.json'
        command = [sys.executable, '-B', str(work/'analysis/roboboat_full_crane_v2.py'),
            '--packet',str(work/'evidence.json'), '--output',str(output),
            '--configuration-id',entry['cluster_id'], '--episode-id',entry['row_id'], '--condition-id',entry['id']]
        subprocess.run(command, cwd=work, env={'PATH':os.environ.get('PATH','/usr/bin:/bin'),
            'PYTHONPATH':str(work/'analysis'), 'PYTHONDONTWRITEBYTECODE':'1'},
            check=True, capture_output=True, text=True, timeout=60)
        result = json.loads(output.read_text())
    if result['schema'] != 'roboboat-full-crane/v2-development' or not result['realization']['final_response'].strip():
        raise ValueError('invalid full B4 output')
    return result


def execute(entry, declaration, declaration_path, output_root, *, caller=call):
    verify(declaration, declaration_path)
    output = Path(output_root)/'responses'/entry['id']
    terminal = output/'response-terminal.json'
    identity = {'declaration_sha256':digest(declaration_path), 'entry':entry}
    if terminal.exists():
        previous = json.loads(terminal.read_text())
        if previous['source_identity'] != identity:
            raise ValueError('retained terminal identity mismatch')
        return previous
    if output.exists():
        raise RuntimeError('unresolved response output retained; never overwrite/reissue')
    intent = Path(output_root)/'intents'/(entry['id']+'.json')
    intent.parent.mkdir(parents=True, exist_ok=True)
    with intent.open('x') as stream:
        json.dump(identity, stream, indent=2)
    try:
        full = generate_b4(entry, declaration)
        save(output/'full-pipeline-B4.json', full)
        save(output/'B4.json', {'answer':full['realization']['final_response'], 'model_calls':0,
            'method':B4, 'full_pipeline':binding(output/'full-pipeline-B4.json'),
            'generation_provenance':{'declaration_sha256':identity['declaration_sha256'],
                'packet':entry['packet'],'effective_configuration':entry['effective_configuration'],
                'capture_terminal':entry['capture_terminal'],'candidate_generation':entry['candidate_generation'],
                'source_snapshots':[{'relative_path':source['relative_path'],**source['snapshot']} for source in declaration['method_sources']]}})
        with tempfile.TemporaryDirectory(prefix='boat-full-b2-') as temporary:
            work = Path(temporary)
            stage(entry, declaration, work)
            result = caller(Path(output_root)/'calls',entry['id'],work,
                checked(declaration['prompt']).read_text(),B2['model'],B2['effort'],
                declaration['return_schema'],allow_tools=True,timeout=300)
        if result.get('status', 'valid') != 'valid' or result.get('attempt_count', 1) != 1:
            raise ValueError('provider response status/attempt count invalid')
        answer = result['parsed_final']
        if set(answer) != {'answer'} or not isinstance(answer['answer'],str) or not answer['answer'].strip():
            raise ValueError('invalid baseline answer')
        save(output/'B2.json', {'answer':answer['answer'], 'cache_key':result['cache_key'],
            'latency_s':result['latency_s'], 'model_calls':1})
        record = {'status':'COMPLETE_RESPONSE_SUPPORT_UNJUDGED', 'source_identity':identity,
            'B4_full_pipeline':binding(output/'full-pipeline-B4.json')}
    except Exception as error:
        record = {'status':'TECHNICAL_RESPONSE_FAILURE', 'source_identity':identity, 'error':str(error)}
    record['retained_outputs'] = {name:binding(output/name) for name in
        ('B2.json','B4.json','full-pipeline-B4.json') if (output/name).is_file()}
    if 'B4.json' in record['retained_outputs']:
        record['B4_candidate'] = record['retained_outputs']['B4.json']
    record.update(quality_retries=0,confirmation_n=0,replication_n=0,alpha_consumed=0)
    save(terminal,record)
    return record


def run(declaration_path, output_root, workers=2, *, caller=call):
    if not 1 <= workers <= 2:
        raise ValueError('one or two workers required')
    declaration = json.loads(Path(declaration_path).read_text())
    verify(declaration, declaration_path)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        jobs = [pool.submit(execute,entry,declaration,declaration_path,output_root,caller=caller)
                for entry in declaration['entries']]
        for job in as_completed(jobs):
            print(job.result()['status'],flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command',required=True)
    prep = commands.add_parser('prepare')
    for name in ('registry','capture-root','declaration'):
        prep.add_argument('--'+name,type=Path,required=True)
    prep.add_argument('--allow-completed-subset',action='store_true')
    prep.add_argument('--prior-declaration',action='append',type=Path,default=[])
    execution = commands.add_parser('run')
    execution.add_argument('--declaration',type=Path,required=True)
    execution.add_argument('--output-root',type=Path,required=True)
    execution.add_argument('--workers',type=int,default=2)
    args = parser.parse_args()
    if args.command=='prepare':
        declaration = prepare(args.registry,args.capture_root,args.declaration,
            allow_completed_subset=args.allow_completed_subset,prior_declarations=args.prior_declaration)
        print('Declared full development pairs:',len(declaration['entries']))
    else:
        run(args.declaration,args.output_root,args.workers)


if __name__=='__main__':
    main()
