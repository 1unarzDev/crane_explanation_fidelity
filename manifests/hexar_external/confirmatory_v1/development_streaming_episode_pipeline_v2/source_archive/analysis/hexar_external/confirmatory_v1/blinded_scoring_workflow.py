"""Pure method-neutral scoring schedule and whole-episode disposition workflow.

No provider calls, confirmation admission, significance calculation or model
qualification. Real execution must separately enforce the committed freeze,
H1 gate, opaque-job registry, durable single attempts and raw response archive.
"""
import copy
import hashlib
import hmac
import random

from .journal import canonical, fingerprint
from .rich_adjudication import needs_c, resolve, endpoint_components
from .rich_blind_projection import project
from .unique_result_expansion import requests, expand_outputs

METHODS = ('HX-CONTRACT', 'HX-PROMPT')
JOBS = {f'q{q}-{condition}' for q in (1, 2, 3)
        for condition in ('intact', 'irrelevant_removal', 'diagnostic_removal')}
CLOSED_ATTEMPTS = {'VALID', 'TECHNICAL_FAILURE', 'INDETERMINATE_AFTER_CRASH'}


def reference_registry(entries):
    """Construct/save this method-neutral registry before method dispatch."""
    records = []
    seen = set()
    for entry in entries:
        key = (entry['episode_id'], entry['job_id'])
        if key in seen or entry['job_id'] not in JOBS:
            raise ValueError('unique complete evidence/query registry required')
        seen.add(key)
        packet, reference = entry['packet'], entry['reference']
        project(packet, reference, 'Pre-generation method-neutral projection probe.')
        records.append(dict(episode_id=key[0], job_id=key[1],
                            packet=copy.deepcopy(packet), reference=copy.deepcopy(reference),
                            packet_sha256=fingerprint(packet), reference_sha256=fingerprint(reference)))
    if not records:
        raise ValueError('nonempty pre-generation reference registry required')
    for episode in {r['episode_id'] for r in records}:
        if {r['job_id'] for r in records if r['episode_id'] == episode} != JOBS:
            raise ValueError('registry must retain all nine query/evidence cells per episode')
    return dict(schema='hexar-method-neutral-reference-registry/v1', entries=records,
                method_outputs_read=False, provider_calls=0)


def prepare(method_plan, outputs, registry, secret_key, shuffle_seed):
    """Return separate public judge jobs and sealed private method linkage."""
    if not isinstance(secret_key, bytes) or len(secret_key) < 32:
        raise ValueError('at least 256 bits of independent sealed blinding key required')
    if registry.get('schema') != 'hexar-method-neutral-reference-registry/v1':
        raise ValueError('known pre-generation reference registry required')
    byid = requests(method_plan)
    cells = expand_outputs(method_plan, outputs)
    lookup = {(r['episode_id'], r['job_id']): r for r in registry['entries']}
    if len(lookup) != len(registry['entries']):
        raise ValueError('duplicate reference registry identity')
    episodes = {r['episode_id'] for r in byid.values()}
    if set(lookup) != {(episode, job) for episode in episodes for job in JOBS}:
        raise ValueError('reference registry differs from exact method battery')
    for episode in episodes:
        if {r['method'] for r in byid.values() if r['episode_id'] == episode} != set(METHODS):
            raise ValueError('both primary methods required on every episode')
        for method in METHODS:
            if sum(r['episode_id'] == episode and r['method'] == method for r in byid.values()) != 6:
                raise ValueError('six unique requests required per method/episode')
            if {r['job_id'] for r in cells if r['episode_id'] == episode and r['method'] == method} != JOBS:
                raise ValueError('complete nine-cell primary battery required')
    unique = {}
    for cell in cells:
        reference = lookup[(cell['episode_id'], cell['job_id'])]
        packet, refs = reference['packet'], reference['reference']
        if (fingerprint(packet) != reference['packet_sha256']
                or fingerprint(refs) != reference['reference_sha256']
                or fingerprint(packet) != cell['packet_sha256']):
            raise ValueError('method packet or pre-generation reference changed')
        payload = project(packet, refs, cell['answer']) if cell['status'] == 'VALID' else None
        uid = cell['source_unique_request_id']
        signature = dict(payload=payload, method_status=cell['status'])
        if uid in unique and unique[uid] != signature:
            raise ValueError('identical request aliases have different scoring inputs')
        unique[uid] = signature
    scope = dict(method_plan_sha256=fingerprint(method_plan),
                 method_outputs_sha256=fingerprint(outputs), registry_sha256=fingerprint(registry))
    initial, reserved, mapping = [], [], []
    for uid in sorted(unique):
        answer_id = hmac.new(secret_key, canonical([scope, uid]), hashlib.sha256).hexdigest()
        entry = unique[uid]
        ids = {}
        if entry['method_status'] == 'VALID':
            for slot in ('A', 'B', 'C'):
                handle = hmac.new(secret_key, canonical([answer_id, slot]), hashlib.sha256).hexdigest()
                ids[slot] = handle
                job = dict(opaque_job=handle, answer_id=answer_id, slot=slot,
                           payload=copy.deepcopy(entry['payload']))
                (reserved if slot == 'C' else initial).append(job)
        mapping.append(dict(unique_request_id=uid, answer_id=answer_id,
                            method_status=entry['method_status'], opaque_slots=ids))
    random.Random(shuffle_seed).shuffle(initial)
    random.Random(shuffle_seed + 1).shuffle(reserved)
    private = dict(schema='hexar-sealed-unique-method-linkage/v1', entries=mapping, scope=scope)
    public = dict(schema='hexar-blinded-scoring-workflow/v1', scope=scope,
                  initial_jobs=initial, reserved_C_jobs=reserved,
                  method_linkage_sha256=fingerprint(private),
                  public_payload_fields=['question', 'visible_evidence', 'required_units', 'answer'],
                  agent_assessed=True, human_validated=False, dispatch_authorized=False)
    private['public_plan_sha256'] = fingerprint(public)
    return public, private


def checked_attempts(jobs, attempts):
    expected = {j['opaque_job'] for j in jobs}
    if len(expected) != len(jobs) or set(attempts) != expected:
        raise ValueError('every scheduled judge attempt needs one explicit closed outcome')
    if any(type(v) is not dict or v.get('status') not in CLOSED_ATTEMPTS for v in attempts.values()):
        raise ValueError('pending/unknown judge outcome cannot enter final scoring')


def select_C(public, initial_attempts):
    checked_attempts(public['initial_jobs'], initial_attempts)
    pairs = {}
    for job in public['initial_jobs']:
        slots = pairs.setdefault(job['answer_id'], {})
        if job['slot'] in slots:
            raise ValueError('duplicate initial slot')
        slots[job['slot']] = job
    reserved = {j['answer_id']: j for j in public['reserved_C_jobs']}
    if len(reserved) != len(public['reserved_C_jobs']) or set(reserved) != set(pairs):
        raise ValueError('C reservation differs from initial answer registry')
    selected = []
    for answer_id, slots in pairs.items():
        if set(slots) != {'A', 'B'} or slots['A']['payload'] != slots['B']['payload']:
            raise ValueError('independent A/B must share exact method-neutral evidence')
        c = reserved[answer_id]
        if c['slot'] != 'C' or c['payload'] != slots['A']['payload']:
            raise ValueError('C must see the same evidence/answer without previous labels')
        if needs_c(initial_attempts[slots['A']['opaque_job']],
                   initial_attempts[slots['B']['opaque_job']], slots['A']['payload']):
            selected.append(copy.deepcopy(c))
    return sorted(selected, key=lambda j: j['opaque_job'])


def finalize(method_plan, outputs, registry, public, private, initial_attempts, C_attempts):
    if (private.get('public_plan_sha256') != fingerprint(public)
            or fingerprint({k: v for k, v in private.items() if k != 'public_plan_sha256'})
                != public.get('method_linkage_sha256')
            or private.get('scope') != public.get('scope')
            or public['scope'] != dict(method_plan_sha256=fingerprint(method_plan),
                method_outputs_sha256=fingerprint(outputs), registry_sha256=fingerprint(registry))):
        raise ValueError('scoring workflow input/linkage hashes changed')
    selected = select_C(public, initial_attempts)
    checked_attempts(selected, C_attempts)
    expected = requests(method_plan)
    entries = {r['unique_request_id']: r for r in private['entries']}
    if len(entries) != len(private['entries']) or set(entries) != set(expected):
        raise ValueError('sealed mapping does not cover exact unique method requests')
    jobs = {j['opaque_job']: j for j in public['initial_jobs'] + public['reserved_C_jobs']}
    labels, components, scoring_hashes = {}, {}, {}
    for uid, entry in entries.items():
        slots = entry['opaque_slots']
        if entry['method_status'] != 'VALID':
            if slots:
                raise ValueError('failed method output cannot receive repair/scoring calls')
            result = dict(status='UNRESOLVED', reason='unique_method_technical_failure', label=None)
            payload = None
            evidence = dict(method_status=entry['method_status'])
        else:
            if set(slots) != {'A', 'B', 'C'}:
                raise ValueError('complete isolated A/B/C slot registry required')
            for slot, handle in slots.items():
                if jobs[handle]['answer_id'] != entry['answer_id'] or jobs[handle]['slot'] != slot:
                    raise ValueError('sealed mapping points to another answer or judge slot')
            payload = jobs[slots['A']]['payload']
            a, b = (initial_attempts[slots[s]] for s in ('A', 'B'))
            c = C_attempts.get(slots['C'])
            result = resolve(a, b, payload, c)
            if result['status'] == 'NEEDS_C':
                raise ValueError('adjudication must close explicitly')
            evidence = dict(A=a, B=b, C=c)
        labels[uid] = result
        components[uid] = endpoint_components(result, payload)
        scoring_hashes[uid] = fingerprint(evidence)
    cells = expand_outputs(method_plan, outputs)
    rows = []
    for cell in cells:
        uid = cell['source_unique_request_id']
        question, condition = cell['job_id'].split('-', 1)
        rows.append(dict(recording_id=cell['episode_id'], method=cell['method'],
                         question_id=question, condition=condition, source_unique_request_id=uid,
                         response_sha256=cell['answer_sha256'], scoring_artifact_sha256=scoring_hashes[uid],
                         attempt_count=1, blind_disposition_closed=True, **components[uid]))
    endpoints, counts = [], [0, 0, 0, 0]
    for episode in sorted({r['recording_id'] for r in rows}):
        states, bounds, mapped = {}, {}, {}
        for method in METHODS:
            values = [row[field] for row in rows if row['recording_id'] == episode and row['method'] == method
                      for field in ('unsupported_material', 'overlicensed_specificity', 'missing_required_unit')]
            if len(values) != 27:
                raise ValueError('nine battery cells required at whole-episode aggregation')
            state = 'FAIL' if any(v is True for v in values) else 'UNRESOLVED' if any(v is None for v in values) else 'PASS'
            states[method] = state
            bounds[method] = [state == 'FAIL', state != 'PASS']
            mapped[method] = bounds[method][1 if method == 'HX-CONTRACT' else 0]
        cf, pf = mapped['HX-CONTRACT'], mapped['HX-PROMPT']
        cell = 0 if not cf and pf else 1 if cf and not pf else 2 if not cf and not pf else 3
        counts[cell] += 1
        endpoints.append(dict(recording_id=episode, method_states=states,
                              failure_bounds=bounds, mapped_failures=mapped))
    return dict(schema='hexar-blinded-scoring-dispositions/v1', agent_assessed=True,
                human_validated=False, labels=labels, jobs=rows, recording_endpoints=endpoints,
                paired_counts=counts, unique_scoring_outcomes=len(labels),
                initial_judge_calls=len(initial_attempts), adjudication_C_calls=len(C_attempts),
                public_plan_sha256=fingerprint(public), method_linkage_sha256=fingerprint(private),
                scope='Pure operational endpoint disposition; no inferential result or confirmation authorization.')
