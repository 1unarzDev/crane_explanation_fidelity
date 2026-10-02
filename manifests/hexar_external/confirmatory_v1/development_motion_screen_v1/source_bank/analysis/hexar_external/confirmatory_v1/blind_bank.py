"""Strict field projection and sealed opaque mapping for blinded scoring.

Pure constructor, not a confirmation executor. Test/development fixtures may use
it. Real confirmation must first pass committed runtime admission; this module
never reads alpha/results, calls judges or assigns semantic labels.
"""
import copy
import hashlib
import hmac
import json
import random
from .journal import canonical

PACKET_KEYS=('schema','question','task_window','evidence','availability',
             'diagnostic_channels','source_context','public_communication_requirements')
REFERENCE_KEYS=('required_units','licensed_propositions','specificity_ceiling','non_entailments')


FORBIDDEN_METADATA={'method','method_id','method_identity','family','situation_family',
                    'development_result','expected_winner','alpha','previous_labels',
                    'ground_truth','root_cause','hidden_intervention','scenario_truth'}


def reject_metadata(value):
    if isinstance(value,dict):
        if FORBIDDEN_METADATA.intersection(value):
            raise ValueError('forbidden nested identity/truth/evaluation metadata')
        for item in value.values():reject_metadata(item)
    elif isinstance(value,list):
        for item in value:reject_metadata(item)


def build(entries,secret_key,shuffle_seed):
    if not isinstance(secret_key,bytes) or len(secret_key)<32:
        raise ValueError('at least 256-bit independently generated sealed key required')
    bank,mapping,seen=[],[],set()
    for entry in entries:
        identity=(entry['recording_id'],entry['method'],entry['question_id'],entry['condition'])
        if identity in seen:raise ValueError('duplicate scoring entry')
        seen.add(identity)
        method_packet=entry['method_packet']
        if set(method_packet)!=set(PACKET_KEYS):
            raise ValueError('method packet missing fields or contains unapproved metadata')
        reference=entry['reference']
        if set(reference)!=set(REFERENCE_KEYS):
            raise ValueError('reference must use the qualified method-neutral projection')
        reject_metadata(method_packet)
        reject_metadata(reference)
        if not isinstance(entry['answer'],str):raise ValueError('raw text answer required')
        handle=hmac.new(secret_key,canonical(identity),hashlib.sha256).hexdigest()
        bank.append(dict(answer_id=handle,answer=entry['answer'],
                         method_packet={k:copy.deepcopy(method_packet[k]) for k in PACKET_KEYS},
                         reference={k:copy.deepcopy(reference[k]) for k in REFERENCE_KEYS}))
        mapping.append(dict(answer_id=handle,recording_id=identity[0],method=identity[1],
                            question_id=identity[2],condition=identity[3],
                            raw_answer_sha256=hashlib.sha256(entry['answer'].encode()).hexdigest()))
    # Sorting before randomization avoids accidental inheritance of method order.
    bank.sort(key=lambda item:item['answer_id'])
    random.Random(shuffle_seed).shuffle(bank)
    return dict(schema='hexar-blind-bank-candidate/v1',entries=bank),dict(schema='hexar-sealed-method-map/v1',entries=mapping)
