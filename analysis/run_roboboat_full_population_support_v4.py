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
from roboboat_annotation_deadline_v2 import safe_annotate, execution_sources, EXECUTION_CONTRACT
import run_roboboat_population_support_v1 as base
import run_roboboat_full_population_inventory_v3 as inventory_v3
import run_roboboat_full_population_inventory_v2 as inventory_v2
from roboboat_reviewed_annotation_packet import validate_review_provenance
import run_roboboat_full_population_responses_v2 as responses
from roboboat_runtime_source_closure_v1 import source_closure as runtime_source_closure


AVAILABILITY_SCHEMA='roboboat-full-inventory-availability/v4'


def snapshot_availability(bank, target, *, _retained_paths=None):
    """Mechanically lock every text's exact review/return existence before support."""
    bank,target=Path(bank).resolve(),Path(target).resolve()
    if target.exists(): raise FileExistsError('immutable availability snapshot exists')
    dependencies=[bank/'blind-bank.json',bank/'evaluator-join.json',bank/'response-accounting.json',bank/'inventory-binding.json']
    inventory_path=checked(json.loads((bank/'inventory-binding.json').read_text())['declaration'])
    dependencies.append(inventory_path)
    # Internal reconstruction can see only paths retained by the pre-call snapshot.
    # Later files never promote an unavailable answer in that namespace.
    exists=lambda path: path.exists() if _retained_paths is None else str(path) in _retained_paths
    missing=[];answers=[]
    texts=json.loads((bank/'blind-bank.json').read_text())['entries']
    for text in texts:
        key,answer=text['opaque_response_id'],text['response_text']
        if key!=hashlib.sha256(answer.encode()).hexdigest(): raise ValueError('blind answer identity mismatch')
        files={slot:bank/'returns'/f'{key}-{slot}.json' for slot in ('A','B')}
        review_path=bank/'project_reviews'/f'{key}.json'
        records={};failure=[]
        for slot,path in files.items():
            if exists(path):
                dependencies.append(path);record=json.loads(path.read_text());records[slot]=record
                if record.get('case_id')!=key or record.get('slot')!=slot or record.get('entry',{}).get('response_text')!=answer:
                    raise ValueError('extraction return source identity mismatch')
                if record.get('validation',{}).get('status')!='STRUCTURALLY_VALID_COMPLETENESS_UNQUALIFIED':
                    failure.append(slot+':STRUCTURAL_RETURN_UNAVAILABLE')
            else:
                missing.append(str(path));failure.append(slot+':MISSING_OR_PENDING_RETURN')
            attempt=bank/'extraction-attempts'/f'{key}-{slot}.json'
            if exists(attempt):
                dependencies.append(attempt);attempt_record=json.loads(attempt.read_text())
                expected_identity={'declaration_sha256':digest(inventory_path),'output_root':str(bank)}
                if (attempt_record.get('opaque_response_id')!=key or attempt_record.get('slot')!=slot
                        or attempt_record.get('source_identity')!=expected_identity):
                    raise ValueError('extraction attempt receipt identity mismatch')
                if slot not in records:
                    failure[-1]=slot+':'+str(attempt_record.get('status','MISSING_ATTEMPT_STATUS'))
            else: missing.append(str(attempt))
        review=None
        if exists(review_path):dependencies.append(review_path);review=json.loads(review_path.read_text())
        else:missing.append(str(review_path))
        if review and review.get('status')=='COMPLETE_FAITHFUL_PROJECT_REVIEW':
            if failure: raise ValueError('complete source review cannot hide unavailable extraction pass')
            validate_review_provenance(answer,review,{slot:path.read_bytes() for slot,path in files.items()})
            claims=review.get('claims',[])
            if not claims or any(set(c)!={'response_span','claim_text'} or not c['claim_text'].strip()
                or not c['response_span'].strip() or c['response_span'] not in answer for c in claims):
                raise ValueError('faithful review source spans incomplete')
            status='REVIEWED_EXTRACTION_AVAILABLE';reason='BOTH_VALID_PASSES_AND_EXACT_COMPLETE_FAITHFUL_SOURCE_REVIEW'
        elif failure:
            status='EXTRACTION_RETURN_UNAVAILABLE';reason=';'.join(failure)
        else:
            status='UNREVIEWED_SOURCE_EXISTS';reason='REVIEW_PENDING_OR_ABSENT' if review is None else 'REVIEW_STATUS_'+str(review.get('status'))
        answers.append({'opaque_response_id':key,'status':status,'reason':reason,
                        'returns':{slot:binding(path) if exists(path) else {'path':str(path),'observed_missing':True} for slot,path in files.items()},
                        'review':binding(review_path) if exists(review_path) else {'path':str(review_path),'observed_missing':True}})
    if len({a['opaque_response_id'] for a in answers})!=len(answers):raise ValueError('duplicate blind text')
    result={'schema':AVAILABILITY_SCHEMA,'bank':str(bank),'answers':answers,
            'dependencies':[binding(p) for p in dict.fromkeys(dependencies)],'missing_paths':sorted(set(missing)),
            'selection':'Mechanical source/extraction/review availability only; no support labels inspected.',
            'support_calls_already_authorized':False,'confirmation_n':0,'replication_n':0,'alpha_consumed':0}
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('x') as stream:json.dump(result,stream,indent=2)
    return result


def verify_availability(path, bank=None, *, require_current=True):
    snapshot=json.loads(Path(path).read_text())
    if snapshot['schema']!=AVAILABILITY_SCHEMA or (bank is not None and snapshot['bank']!=str(Path(bank).resolve())):
        raise ValueError('exact availability snapshot required')
    for value in snapshot['dependencies']:checked(value)
    if require_current and any(Path(p).exists() for p in snapshot['missing_paths']):
        raise ValueError('observed missing path now exists; prepare a new exact availability namespace')
    expected={e['opaque_response_id'] for e in json.loads((Path(snapshot['bank'])/'blind-bank.json').read_text())['entries']}
    if {a['opaque_response_id'] for a in snapshot['answers']}!=expected or len(snapshot['answers'])!=len(expected):
        raise ValueError('availability must retain every original blind text')
    # Preparation checks the exhaustive live view: existing reviews cannot be
    # omitted. After its hash is bound in the declaration, reconstruct solely
    # from retained files; later arrivals cannot alter eligibility or bounds.
    import tempfile
    with tempfile.TemporaryDirectory(prefix='boat-availability-check-') as temp:
        regenerated=snapshot_availability(snapshot['bank'],Path(temp)/'snapshot.json',
            _retained_paths=None if require_current else {b['path'] for b in snapshot['dependencies']})
    if regenerated!=snapshot: raise ValueError('availability snapshot differs from exact observed files')
    return snapshot


def prepare(bank, response_declaration, response_root, output_root, declaration, *, availability):
    bank, response_root, output_root = map(lambda p: Path(p).resolve(), (bank, response_root, output_root))
    response_declaration = Path(response_declaration).resolve()
    source = json.loads(response_declaration.read_text())
    if source['disposition'] != 'DEVELOPMENT_ONLY_NO_CONFIRMATORY_INFERENCE':
        raise ValueError('development response declaration required')
    if Path(declaration).exists() or output_root.exists():
        raise ValueError('immutable full support declaration/root already exists')
    inventory_binding = bank/'inventory-binding.json'
    inventory_path = checked(json.loads(inventory_binding.read_text())['declaration'])
    inventory_declaration = json.loads(inventory_path.read_text())
    inventory = {'roboboat-full-population-inventory-declaration/v2':inventory_v2,
                 'roboboat-full-population-inventory-declaration/v3':inventory_v3}.get(inventory_declaration['schema'])
    if inventory is None: raise ValueError('genuine full inventory v2/v3 required')
    inventory.verify_response_snapshot(source,response_declaration)
    snapshot=verify_availability(availability,bank)
    selection={item['opaque_response_id']:item for item in snapshot['answers']}
    if (inventory_declaration['schema'] not in ('roboboat-full-population-inventory-declaration/v2','roboboat-full-population-inventory-declaration/v3')
            or inventory_declaration['response_declaration'] != binding(response_declaration)
            or inventory_declaration['output_root'] != str(bank)
            or inventory_declaration['response_root'] != str(response_root)):
        raise ValueError('full inventory source identity mismatch')
    for b in inventory_declaration['dependencies']: checked(b)
    if any(Path(p).exists() for p in inventory_declaration['missing_source_paths']):
        raise ValueError('missing source now exists; use a fresh immutable inventory')
    material_disposition = DOC/'material_qualification_development_disposition_v3.json'
    if json.loads(material_disposition.read_text())['status'] != 'BOUNDED_CONSTRUCTION_EXTENSION_PASS_AGENT_ASSESSED':
        raise ValueError('material development qualification gate closed')
    for b in source['method_sources']:
        checked(b)
    answers = {}
    dependencies = [response_declaration, bank/'blind-bank.json', bank/'evaluator-join.json', Path(__file__), Path(base.__file__), Path(inventory.__file__), Path(responses.__file__),
                    inventory_binding, inventory_path, bank/'response-accounting.json',
                    ROOT/'tests/test_roboboat_full_population_support_v4.py', Path(availability).resolve(),
                    ROOT/'analysis/summarize_roboboat_full_population_support_v4.py',
                    ROOT/'tests/test_summarize_roboboat_full_population_support_v4.py']
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
    expected_sources, accounting = {}, []
    for entry in source['entries']:
        item, admitted, paths, missing = inventory.answer_sources(entry,source,response_declaration,response_root)
        accounting.append(item); dependencies.extend(paths)
        for answer in admitted:
            expected_sources[(entry['id'],answer['method'])]=answer
    actual={(j['response_id'],j['method']) for j in joins}
    if actual != set(expected_sources) or len(joins)!=len(expected_sources):
        raise ValueError('all available full snapshot answers required; no selective join')
    if json.loads((bank/'response-accounting.json').read_text())['entries'] != accounting:
        raise ValueError('response accounting differs from immutable full snapshot')
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
                 'reference_roboboat_temporal_v2.py', 'evidence_calibration_io.py', 'summarize_roboboat_population_support_v1.py'):
        dependencies.append(ROOT/'analysis'/name)
    dependencies.extend(execution_sources())
    dependencies.extend(runtime_source_closure([Path(__file__), *execution_sources(), ROOT/"analysis/summarize_roboboat_full_population_support_v4.py"]))
    dependencies.extend(checked(b) for b in snapshot['dependencies'])
    packets, evaluator, seen = [], [], set()
    for join in joins:
        key, response_id, method = join['opaque_response_id'], join['response_id'], join['method']
        entry = entries[response_id]
        terminal = response_root/'responses'/response_id/'response-terminal.json'
        expected_answer=expected_sources[(response_id,method)]
        answer_path=checked(join['answer_source'])
        if (answer_path.resolve()!=expected_answer['path'].resolve()
                or join['answer_provenance']!=expected_answer['provenance']):
            raise ValueError('full answer source/provenance mismatch')
        answer=expected_answer['answer']
        if answer!=answers[key]: raise ValueError('source response changed')
        retained_answer=expected_answer['path']
        packet_path = checked(entry['packet'])
        availability_item=selection[key]
        if availability_item['status']!='REVIEWED_EXTRACTION_AVAILABLE':
            evaluator.append({**join,'support_packet_id':None,'availability':availability_item,
                              'primary_bounds_if_unavailable':[0,1]})
            continue
        review_path = bank/'project_reviews'/f'{key}.json'
        review = json.loads(review_path.read_text())
        returns_paths = {slot: bank/'returns'/f'{key}-{slot}.json' for slot in ('A', 'B')}
        packet, meta = prepare_packet(json.loads(packet_path.read_text()), answer, review,
                                    {slot: path.read_bytes() for slot, path in returns_paths.items()})
        opaque = packet['forms'][0]['packet_id']
        if opaque not in seen:
            target = output_root/'blind_packets'/f'{opaque}.json'
            save(target, packet); packets.append(binding(target)); seen.add(opaque)
        evaluator.append({**join, 'support_packet_id': opaque, 'availability':availability_item, **meta})
        dependencies += [terminal, answer_path, retained_answer, packet_path, review_path, *returns_paths.values()]
    # Every blind text must correspond to an actual retained response instance.
    if {j['opaque_response_id'] for j in joins} != set(answers):
        raise ValueError('orphan extraction-bank response')
    save(output_root/'evaluator-join.json', {'entries': evaluator, 'annotation_input': False})
    dependencies.append(output_root/'evaluator-join.json')
    result = {'schema': 'roboboat-full-population-reviewed-support/v4',
              'disposition': 'DEVELOPMENT_ONLY_CITATION_REVIEW_PENDING',
              'method_scope':responses.B4, 'output_root':str(output_root), 'response_declaration':binding(response_declaration),
              'response_accounting':binding(bank/'response-accounting.json'),
              'snapshot_entries':source['entries'], 'registry':source['registry'],
              'dependencies': [binding(p) for p in dict.fromkeys(dependencies)], 'packets': packets,
              'judge': {'model': MODEL, 'effort': EFFORT, 'passes': 2, 'adjudication': 'disagreement only'},
              'max_concurrent_packets': 2, 'timeout_s': 600, 'quality_retries': 0,
              'original_answers': len(joins), 'unique_support_packets': len(packets),
              'execution_contract': EXECUTION_CONTRACT,
              'availability_snapshot':binding(availability), 'availability_missing_paths':snapshot['missing_paths'],
              'selection':'All exact paired-valid-extraction and complete-faithful-review texts mechanically available in the locked pre-support snapshot; all other original response slots remain unknown.',
              'reviewed_available_answers':sum(j['support_packet_id'] is not None for j in evaluator),
              'primary_candidate': 'complete supported diagnostic answers', 'coverage': 'supporting outcome',
              'scoring_release_authorized': False, 'complete_source_citation_review_required': True,
              'confirmation_n': 0, 'replication_n': 0, 'alpha_consumed': 0}
    # Close the preparation window before the declaration authorizes calls.
    # Concurrent arrivals during preparation require a fresh snapshot; arrivals
    # after this bound lock stay unavailable and need no worker interruption.
    if binding(availability) != result['availability_snapshot']:
        raise ValueError('availability snapshot changed during preparation')
    verify_availability(availability,bank,require_current=True)
    save(Path(declaration), result)
    return result


# Execution reuses genuine qualified annotation packets and the unchanged
# two-pass/adjudication implementation. No legacy method identity is synthesized.
run_one = base.run_one


def run(declaration_path, output_root, *, annotator=safe_annotate):
    d=json.loads(Path(declaration_path).read_text())
    if (d['schema']!='roboboat-full-population-reviewed-support/v4' or d['method_scope']!=responses.B4
            or d['output_root']!=str(Path(output_root).resolve()) or d['max_concurrent_packets']!=2 or d['timeout_s']!=600 or d['quality_retries']!=0
            or d['judge']!={'model':MODEL,'effort':EFFORT,'passes':2,'adjudication':'disagreement only'}):
        raise ValueError('full support contract changed')
    verify_availability(checked(d['availability_snapshot']),require_current=False)
    if d['execution_contract']!=EXECUTION_CONTRACT: raise ValueError('annotation runtime override changed')
    return base.run(declaration_path,output_root,annotator=annotator)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    commands = p.add_subparsers(dest='phase', required=True)
    prep = commands.add_parser('prepare')
    for name in ('bank', 'response-declaration', 'response-root', 'output-root', 'declaration'):
        prep.add_argument('--'+name, type=Path, required=True)
    execute = commands.add_parser('run')
    execute.add_argument('--declaration', type=Path, required=True)
    execute.add_argument('--output-root', type=Path, required=True)
    prep.add_argument('--availability',type=Path,required=True)
    snapshot = commands.add_parser('snapshot')
    snapshot.add_argument('--bank',type=Path,required=True)
    snapshot.add_argument('--availability',type=Path,required=True)
    a = p.parse_args()
    if a.phase=='snapshot':
        result=snapshot_availability(a.bank,a.availability)
        print(json.dumps({'answer_texts':len(result['answers']),'snapshot':str(a.availability)}));return
    if a.phase == 'prepare': prepare(a.bank, a.response_declaration, a.response_root, a.output_root, a.declaration, availability=a.availability)
    else: run(a.declaration, a.output_root)


if __name__ == '__main__': main()
