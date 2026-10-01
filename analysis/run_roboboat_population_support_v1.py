#!/usr/bin/env python3
"""Generic reviewed marine development support; citation review precedes scoring."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
from build_roboboat_terminal_batch import ROOT, DOC, save, digest
from run_roboboat_population_responses_v1 import binding, checked
from roboboat_material_workflow_v3 import prepare as prepare_packet
from run_evidence_calibration_agent_annotation import (run as annotate, StructuredCodexCliAgentCaller,
    PROMPT, RETURN_SCHEMA, ADJUDICATION_SCHEMA, AMENDMENT, MODEL, EFFORT)
from roboboat_isolated_transport import isolated_run


def prepare(bank, response_declaration, response_root, output_root, declaration):
    bank, response_root, output_root = map(lambda p: Path(p).resolve(), (bank, response_root, output_root))
    response_declaration = Path(response_declaration).resolve()
    source = json.loads(response_declaration.read_text())
    if source['disposition'] != 'DEVELOPMENT_ONLY_NO_CONFIRMATORY_INFERENCE':
        raise ValueError('development response declaration required')
    material_disposition = DOC/'material_qualification_development_disposition_v3.json'
    if json.loads(material_disposition.read_text())['status'] != 'BOUNDED_CONSTRUCTION_EXTENSION_PASS_AGENT_ASSESSED':
        raise ValueError('material development qualification gate closed')
    for b in source['method_sources']:
        checked(b)
    answers = {}
    dependencies = [response_declaration, bank/'blind-bank.json', bank/'evaluator-join.json', Path(__file__)]
    for e in json.loads((bank/'blind-bank.json').read_text())['entries']:
        if set(e) != {'opaque_response_id', 'response_text'}:
            raise ValueError('blind bank metadata leak')
        key = hashlib.sha256(e['response_text'].encode()).hexdigest()
        if e['opaque_response_id'] != key or key in answers:
            raise ValueError('blind bank identity mismatch')
        answers[key] = e['response_text']
    entries = {e['id']: e for e in source['entries']}
    if len(entries) != len(source['entries']):
        raise ValueError('duplicate response entry')
    dependencies += [checked(b) for b in source['method_sources']]
    joins = json.loads((bank/'evaluator-join.json').read_text())['entries']
    expected = {(key, method) for key in entries for method in ('B2', 'B4')}
    actual = {(j['response_id'], j['method']) for j in joins}
    if actual != expected or len(joins) != len(expected):
        raise ValueError('complete paired response join required')
    qpath = ROOT/'manifests/study/evidence-calibration-agent-qualification-disposition-v1.json'
    q = json.loads(qpath.read_text())['qualified_binding']
    if (q['model'], q['reasoning_effort'], q['isolated_passes']) != (MODEL, EFFORT, 2):
        raise ValueError('qualified support binding differs')
    dependencies += [qpath, PROMPT, RETURN_SCHEMA, ADJUDICATION_SCHEMA, AMENDMENT,
                     DOC/'material_qualification_development_disposition_v3.json']
    for value in q.values():
        if isinstance(value, dict) and 'path' in value:
            path = ROOT/value['path']
            if digest(path) != value['sha256']: raise ValueError('qualified dependency changed')
            dependencies.append(path)
    for name in ('roboboat_material_workflow_v3.py', 'roboboat_material_endpoint_v1.py',
                 'roboboat_material_endpoint_v2.py', 'roboboat_material_qualification_validation_v3.py',
                 'roboboat_reviewed_annotation_packet.py', 'run_roboboat_terminal_comparison.py',
                 'run_evidence_calibration_agent_annotation.py', 'adjudicate_evidence_calibration_annotations.py',
                 'roboboat_isolated_transport.py', 'roboboat_temporal_certificate.py',
                 'roboboat_temporal_certificate_v2.py', 'reference_roboboat_temporal.py',
                 'reference_roboboat_temporal_v2.py', 'evidence_calibration_io.py'):
        dependencies.append(ROOT/'analysis'/name)
    packets, evaluator, seen = [], [], set()
    for join in joins:
        key, response_id, method = join['opaque_response_id'], join['response_id'], join['method']
        entry = entries[response_id]
        terminal = response_root/'responses'/response_id/'response-terminal.json'
        record = json.loads(terminal.read_text())
        if record['status'] != 'COMPLETE_RESPONSE_SUPPORT_UNJUDGED' or record['source_identity'] != {
            'declaration_sha256': digest(response_declaration), 'entry': entry}:
            raise ValueError('response terminal source mismatch')
        retained_answer = response_root/'responses'/response_id/f'{method}.json'
        if 'answer_source' in join:
            answer_path = checked(join['answer_source'])
            expected_source = checked(entry['candidate']) if method == 'B4' else retained_answer.resolve()
            expected_provenance = 'DETERMINISTIC_BOUND_CANDIDATE' if method == 'B4' else 'SOURCE_BOUND_METHOD_RETURN'
            if answer_path.resolve() != expected_source.resolve() or join['answer_provenance'] != expected_provenance:
                raise ValueError('answer source/provenance mismatch')
        else:
            answer_path = retained_answer
            if digest(answer_path) != join['answer_file_sha256']:
                raise ValueError('source response changed')
        answer = json.loads(answer_path.read_text())['answer']
        if answer != answers[key] or json.loads(retained_answer.read_text())['answer'] != answer:
            raise ValueError('source response changed')
        packet_path = checked(entry['packet'])
        review_path = bank/'project_reviews'/f'{key}.json'
        review = json.loads(review_path.read_text())
        returns_paths = {slot: bank/'returns'/f'{key}-{slot}.json' for slot in ('A', 'B')}
        packet, meta = prepare_packet(json.loads(packet_path.read_text()), answer, review,
                                    {slot: path.read_bytes() for slot, path in returns_paths.items()})
        opaque = packet['forms'][0]['packet_id']
        if opaque not in seen:
            target = output_root/'blind_packets'/f'{opaque}.json'
            save(target, packet); packets.append(binding(target)); seen.add(opaque)
        evaluator.append({**join, 'support_packet_id': opaque, **meta})
        dependencies += [terminal, answer_path, retained_answer, packet_path, review_path, *returns_paths.values()]
    # Every blind text must correspond to an actual retained response instance.
    if {j['opaque_response_id'] for j in joins} != set(answers):
        raise ValueError('orphan extraction-bank response')
    save(output_root/'evaluator-join.json', {'entries': evaluator, 'annotation_input': False})
    dependencies.append(output_root/'evaluator-join.json')
    result = {'schema': 'roboboat-population-reviewed-support/v1',
              'disposition': 'DEVELOPMENT_ONLY_CITATION_REVIEW_PENDING',
              'dependencies': [binding(p) for p in dict.fromkeys(dependencies)], 'packets': packets,
              'judge': {'model': MODEL, 'effort': EFFORT, 'passes': 2, 'adjudication': 'disagreement only'},
              'max_concurrent_packets': 2, 'timeout_s': 300, 'quality_retries': 0,
              'original_answers': len(joins), 'unique_support_packets': len(packets),
              'primary_candidate': 'complete supported diagnostic answers', 'coverage': 'supporting outcome',
              'scoring_release_authorized': False, 'complete_source_citation_review_required': True,
              'confirmation_n': 0, 'replication_n': 0, 'alpha_consumed': 0}
    save(Path(declaration), result)
    return result


def run_one(packet_binding, d, declaration_path, output_root, *, annotator=annotate):
    path = checked(packet_binding); key = path.stem
    terminal = Path(output_root)/'terminals'/f'{key}.json'
    identity = {'packet': packet_binding, 'declaration_sha256': digest(declaration_path)}
    if terminal.exists():
        previous = json.loads(terminal.read_text())
        if previous['source_identity'] != identity: raise ValueError('terminal identity mismatch')
        return previous
    intent = Path(output_root)/'intents'/f'{key}.json'; intent.parent.mkdir(parents=True, exist_ok=True)
    with intent.open('x') as stream: json.dump(identity, stream)
    target = Path(output_root)/'annotations'/key
    try:
        summary = annotator(path, target, caller=StructuredCodexCliAgentCaller(target/'calls',
            model=d['judge']['model'], effort=d['judge']['effort'], timeout_s=d['timeout_s'], runner=isolated_run))
        record = {'status': 'SUPPORT_COMPLETE_CITATION_REVIEW_PENDING', 'summary': summary,
                  'unresolved_judgments_retained_in': str(target/'final.json')}
    except Exception as error:
        record = {'status': 'TECHNICAL_SUPPORT_FAILURE', 'error': str(error),
                  'unresolved_judgments': 'ALL_UNFINISHED_JUDGMENTS_UNAVAILABLE', 'retained_partial_root': str(target)}
    record.update(source_identity=identity, scoring_release_authorized=False, confirmation_n=0,
                  replication_n=0, alpha_consumed=0, quality_retries=0)
    save(terminal, record)
    return record


def run(declaration_path, output_root, *, annotator=annotate):
    d = json.loads(Path(declaration_path).read_text())
    if d['disposition'] != 'DEVELOPMENT_ONLY_CITATION_REVIEW_PENDING' or d['scoring_release_authorized']:
        raise ValueError('development support declaration required')
    for b in d['dependencies'] + d['packets']: checked(b)
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = [pool.submit(run_one, b, d, declaration_path, output_root, annotator=annotator) for b in d['packets']]
        for job in as_completed(jobs): print(job.result()['status'], flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    commands = p.add_subparsers(dest='phase', required=True)
    prep = commands.add_parser('prepare')
    for name in ('bank', 'response-declaration', 'response-root', 'output-root', 'declaration'):
        prep.add_argument('--'+name, type=Path, required=True)
    execute = commands.add_parser('run')
    execute.add_argument('--declaration', type=Path, required=True)
    execute.add_argument('--output-root', type=Path, required=True)
    a = p.parse_args()
    if a.phase == 'prepare': prepare(a.bank, a.response_declaration, a.response_root, a.output_root, a.declaration)
    else: run(a.declaration, a.output_root)


if __name__ == '__main__': main()
