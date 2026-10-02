"""Additive development-only public-context packets; no judge execution or scoring."""
import copy
import json
from pathlib import Path
from evidence_calibration_io import canonical_sha256
from run_roboboat_population_responses_v1 import BASIS, binding, checked
import run_roboboat_full_population_responses_v2 as responses
from run_evidence_calibration_agent_annotation import _annotation_payload

NAMESPACE = 'roboboat-public-configuration-judging/v1-development'
PACKET_KEYS = {'schema', 'forms', 'response_text', 'independent_reference', 'inventory_origin',
               'abstraction_tags_qualified', 'endpoint_status'}
FORM_KEYS = {'abstraction_level_options','allowed_claim_labels','annotator_attestation',
             'annotator_slot','atomic_statements','false_premise_handling','form_id',
             'highest_asserted_abstraction_level','limitation_preservation','packet_id',
             'question_text','required_unit_coverage','robot_visible_evidence','sanitized_physical_facts'}
CONTEXT_SCOPE = ('Public method-visible configuration provenance. Readback establishes configured '
                 'settings; it does not prove internal consumption of observations or why stopping occurred.')


def authenticated_basis(declaration_path):
    """Verify retained original declaration/source bytes; export no identities or joins."""
    declaration_path = Path(declaration_path).resolve()
    d = json.loads(declaration_path.read_text())
    if (d.get('schema') != 'roboboat-full-population-response-declaration/v2'
            or d.get('disposition') != 'DEVELOPMENT_ONLY_NO_CONFIRMATORY_INFERENCE'
            or d.get('configuration_basis') != BASIS):
        raise ValueError('original public configuration basis/declaration required')
    runner = checked(d['runner'])
    if binding(runner)['sha256'] != binding(Path(responses.__file__))['sha256']:
        raise ValueError('unrecognized original staging runner')
    # The original declaration retains BASIS verbatim. Its source provider was
    # imported by the bound runner, not staged in method_sources; authenticate
    # the supplied semantics through that original declaration, not a invented
    # legacy source binding. Current provider bytes are a separate audit input.
    provider = Path(__import__('run_roboboat_population_responses_v1').__file__).resolve()
    checked(d['prompt'])
    return copy.deepcopy(BASIS), [binding(declaration_path), binding(runner), binding(provider), d['prompt']]


def reject_join_metadata(value):
    forbidden = {'method', 'method_identity', 'method_identity_visible', 'evaluator_join',
                 'condition_key', 'condition_key_joined', 'response_id', 'cluster_id'}
    if isinstance(value, dict):
        if set(value) & forbidden:
            raise ValueError('nested identity/join metadata leak')
        for child in value.values(): reject_join_metadata(child)
    elif isinstance(value, list):
        for child in value: reject_join_metadata(child)


def build_packet(packet, basis):
    reject_join_metadata(packet)
    if basis != BASIS:
        raise ValueError('altered public configuration basis')
    if set(packet) - PACKET_KEYS or packet.get('schema') != 'crane-blinded-agent-atomic-annotation-packet-set/v1':
        raise ValueError('unsupported packet or identity/join metadata leak')
    forms = packet.get('forms', [])
    if len(forms) != 2 or {f.get('annotator_slot') for f in forms} != {'A','B'}:
        raise ValueError('exactly two blind forms required')
    for form in forms:
        if set(form) - FORM_KEYS:
            raise ValueError('form identity/join metadata leak')
    for name in ('robot_visible_evidence','atomic_statements','required_unit_coverage','limitation_preservation'):
        if forms[0][name] != forms[1][name]:
            raise ValueError('unequal original decision inventory')
    result = copy.deepcopy(packet)
    context = {'schema': NAMESPACE, 'configuration_basis': copy.deepcopy(basis), 'scope': CONTEXT_SCOPE}
    identity = canonical_sha256({'namespace': NAMESPACE, 'original_packet': packet, 'public_context': context})[:24]
    for form in result['forms']:
        form['public_configuration_context'] = copy.deepcopy(context)
        form['packet_id'] = identity
        form['form_id'] = identity + '-' + form['annotator_slot']
    return result


def annotation_payload(packet, slot):
    form = next(f for f in packet['forms'] if f['annotator_slot'] == slot)
    validate_context(packet)
    return _annotation_payload(packet, form, slot)


def adjudication_payload(packet, handoff):
    validate_context(packet)
    if handoff.get('packet_id') != packet['forms'][0]['packet_id'] or handoff.get('packet_set_sha256') != canonical_sha256(packet):
        raise ValueError('adjudication handoff packet mismatch')
    return {'task':'BLINDED_DISAGREEMENT_ONLY_ADJUDICATION','annotation_origin':'automated_agent',
            'agent_identity':'agent-C-astra-v4','blinded_form':packet['forms'][0],
            'handoff':handoff,'required_attestation':'DISAGREEMENT_ONLY_BLINDED_COMPLETE'}


def validate_context(packet):
    reject_join_metadata(packet)
    original = copy.deepcopy(packet)
    contexts = [f.pop('public_configuration_context', None) for f in original['forms']]
    expected = {'schema':NAMESPACE,'configuration_basis':BASIS,'scope':CONTEXT_SCOPE}
    if contexts != [expected, expected]:
        raise ValueError('exact equal public context required')
    # IDs are validated against retained original packet at preparation; never
    # infer statistical identity or authenticate provenance from a blind ID.
    if set(original)-PACKET_KEYS or any(set(f)-FORM_KEYS for f in original['forms']):
        raise ValueError('identity/join metadata leak')
    return True


def verify_source_lock(lock_path, declaration_path):
    lock = json.loads(Path(lock_path).read_text())
    if (lock.get('schema') != 'roboboat-public-configuration-engineering-lock/v1'
            or lock.get('calls_authorized') is not False
            or lock.get('qualification_status') != 'PENDING_BALANCED_CONSTRUCTION_QUALIFICATION'):
        raise ValueError('engineering-only public-context source lock required')
    bindings = lock['dependencies']
    for value in bindings: checked(value)
    expected = binding(Path(declaration_path))
    if expected not in lock['original_response_declarations']:
        raise ValueError('original public context declaration not source-locked')
    from roboboat_runtime_source_closure_v1 import source_closure
    required = {str(p.resolve()) for p in source_closure([Path(__file__)])}
    if not required <= {b['path'] for b in bindings}:
        raise ValueError('complete public context runtime closure required')
    for b in lock['original_response_declarations']:
        checked(b)
    return lock


def prepare(packet_path, declaration_path, target, receipt, *, source_lock):

    target, receipt = Path(target), Path(receipt)
    if target.exists() or receipt.exists():
        raise FileExistsError('immutable public-context namespace exists')
    verify_source_lock(source_lock, declaration_path)
    basis, inputs = authenticated_basis(declaration_path)
    packet_path = Path(packet_path)
    original = json.loads(packet_path.read_text())
    result = build_packet(original, basis)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('x') as stream: json.dump(result, stream, indent=2)
    record = {'schema':NAMESPACE,'original_packet':binding(packet_path),'new_packet':binding(target),
              'inputs':inputs,'source':binding(Path(__file__)), 'source_lock':binding(Path(source_lock)), 'source_answer_changed':False,
              'core_evidence_changed':False,'calls_authorized':False,'scores_released':False,
              'qualification_required_before_calls':True,'confirmation_n':0,'replication_n':0}
    receipt.parent.mkdir(parents=True, exist_ok=True)
    with receipt.open('x') as stream: json.dump(record, stream, indent=2)
    return record
