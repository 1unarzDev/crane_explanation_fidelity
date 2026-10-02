import json
from pathlib import Path
import pytest
import run_roboboat_population_support_v1 as support


def declaration(tmp_path):
    packet = tmp_path/'packet.json'; packet.write_text('{}')
    d = {'disposition': 'DEVELOPMENT_ONLY_CITATION_REVIEW_PENDING',
         'scoring_release_authorized': False, 'dependencies': [], 'packets': [support.binding(packet)],
         'judge': {'model': 'gpt-6-astra', 'effort': 'high'}, 'timeout_s': 300}
    path = tmp_path/'declaration.json'; path.write_text(json.dumps(d))
    return d, path


def test_two_pass_existing_runner_delegation_and_no_retry(tmp_path):
    d, path = declaration(tmp_path)
    calls = []
    def annotate(packet, output, caller):
        calls.append(packet)
        assert caller.model == 'gpt-6-astra'
        return {'finalized': True, 'adjudication_agent_invoked': False}
    support.run(path, tmp_path/'output', annotator=annotate)
    support.run(path, tmp_path/'output', annotator=annotate)
    assert len(calls) == 1
    terminal = json.loads((tmp_path/'output/terminals/packet.json').read_text())
    assert terminal['scoring_release_authorized'] is False
    assert terminal['status'] == 'SUPPORT_COMPLETE_CITATION_REVIEW_PENDING'


def test_failure_retains_unavailable_and_does_not_retry(tmp_path):
    d, path = declaration(tmp_path)
    calls = []
    def annotate(*args, **kwargs):
        calls.append(1)
        raise RuntimeError('provider failure')
    support.run(path, tmp_path/'output', annotator=annotate)
    support.run(path, tmp_path/'output', annotator=annotate)
    terminal = json.loads((tmp_path/'output/terminals/packet.json').read_text())
    assert terminal['status'] == 'TECHNICAL_SUPPORT_FAILURE'
    assert terminal['unresolved_judgments'] == 'ALL_UNFINISHED_JUDGMENTS_UNAVAILABLE'
    assert len(calls) == 1


def test_preflight_integrity_and_unresolved_intent(tmp_path):
    d, path = declaration(tmp_path)
    packet = tmp_path/'packet.json'; packet.write_text('{"changed":true}')
    with pytest.raises(ValueError, match='bound input'):
        support.run(path, tmp_path/'output', annotator=lambda *a, **k: pytest.fail('called'))
    packet.write_text('{}')
    intent = tmp_path/'output/intents/packet.json'; intent.parent.mkdir(parents=True); intent.write_text('{}')
    with pytest.raises(FileExistsError):
        support.run(path, tmp_path/'output', annotator=lambda *a, **k: pytest.fail('called'))


def test_actual_inventory_prepare_integrates_with_support(tmp_path):
    import hashlib
    import run_roboboat_population_inventory_v1 as inventory
    from roboboat_temporal_certificate_v2 import certificate, render
    from roboboat_material_endpoint_v2 import MATERIAL_LIMIT
    from roboboat_material_endpoint_v1 import PARTIAL_UNIT
    packet = json.loads((support.ROOT/'artifacts/roboboat-material-qualification-fixtures-v2/03.json').read_text())['packet']
    evidence = tmp_path/'evidence.json'; evidence.write_text(json.dumps(packet))
    cert = certificate(packet)
    candidate = tmp_path/'candidate.json'; candidate.write_text(json.dumps({'answer': render(packet, cert), 'certificate': cert}))
    entry = {'id': 'real-schema-L2', 'row_id': 'real-schema', 'cluster_id': 'cluster', 'level': 2,
             'packet': support.binding(evidence), 'candidate': support.binding(candidate)}
    d = {'schema': 'roboboat-population-response-declaration/v1',
         'disposition': 'DEVELOPMENT_ONLY_NO_CONFIRMATORY_INFERENCE', 'entries': [entry],
         'method_sources': [], 'capture_accounting': []}
    response_declaration = tmp_path/'responses.json'; response_declaration.write_text(json.dumps(d))
    root = tmp_path/'responses'; output = root/'responses'/entry['id']; output.mkdir(parents=True)
    identity = {'declaration_sha256': support.digest(response_declaration), 'entry': entry}
    intents = root/'intents'; intents.mkdir(); (intents/(entry['id']+'.json')).write_text(json.dumps(identity))
    (output/'response-terminal.json').write_text(json.dumps({'source_identity': identity, 'status': 'COMPLETE_RESPONSE_SUPPORT_UNJUDGED'}))
    (output/'B2.json').write_text(json.dumps({'answer': 'Sampled conditions hold; contact is unknown.'}))
    (output/'B4.json').write_text(json.dumps({'answer': render(packet, cert)}))
    bank = tmp_path/'bank'
    inventory.prepare(response_declaration, root, bank, tmp_path/'inventory.json')
    # Construction extraction and project review artifacts match the real bank texts.
    for e in json.loads((bank/'blind-bank.json').read_text())['entries']:
        key, answer = e['opaque_response_id'], e['response_text']
        raws = {slot: json.dumps({'case_id': key, 'slot': slot, 'entry': {'response_text': answer},
              'validation': {'status': 'STRUCTURALLY_VALID_COMPLETENESS_UNQUALIFIED'}}).encode() for slot in ('A', 'B')}
        returns = bank/'returns'; returns.mkdir(exist_ok=True)
        for slot, raw in raws.items(): (returns/f'{key}-{slot}.json').write_bytes(raw)
        review = {'status': 'COMPLETE_FAITHFUL_PROJECT_REVIEW', 'opaque_response_id': key,
            'source_text_sha256': key, 'project_review_not_human_validation': True,
            'abstraction_tags_discarded': True, 'source_assertion_completeness_reviewed': True,
            'extractor_returns_sha256': {slot: hashlib.sha256(raw).hexdigest() for slot, raw in raws.items()},
            'claims': [{'response_span': answer, 'claim_text': answer}]}
        reviews = bank/'project_reviews'; reviews.mkdir(exist_ok=True)
        (reviews/f'{key}.json').write_text(json.dumps(review))
    result = support.prepare(bank, response_declaration, root, tmp_path/'support', tmp_path/'support.json')
    assert result['original_answers'] == 2
    for b in result['packets']:
        prepared = json.loads(Path(b['path']).read_text())
        for form in prepared['forms']:
            assert PARTIAL_UNIT in [u['unit_prompt'] for u in form['required_unit_coverage']]
            assert MATERIAL_LIMIT in [l['limitation_prompt'] for l in form['limitation_preservation']]
    joins = json.loads((bank/'evaluator-join.json').read_text())
    joins['entries'][0]['answer_provenance'] = 'INCORRECT'
    (bank/'evaluator-join.json').write_text(json.dumps(joins))
    with pytest.raises(ValueError, match='provenance'):
        support.prepare(bank, response_declaration, root, tmp_path/'bad-support', tmp_path/'bad-support.json')
