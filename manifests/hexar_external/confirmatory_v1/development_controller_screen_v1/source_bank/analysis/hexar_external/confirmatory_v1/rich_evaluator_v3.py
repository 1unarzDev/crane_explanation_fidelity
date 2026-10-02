"""Development candidate with auditable unsupported/ambiguous answer spans.

Previous prompts, calls and dispositions remain unchanged. No runtime admission.
"""
import copy
from .rich_evaluator_v2 import PROMPT as PREVIOUS_PROMPT, SCHEMA as OLD_SCHEMA, validate as old_validate

AMBIGUITY_POLICY = '''Judge asserted propositions, not an unnecessarily strong interpretation you invent. Distinguish a requested/accepted navigation intention or software execution from realized physical spatial progress. Explicit request/execution language can be supported by recorded request/action evidence without a map-to-odom transform. Claims of arrival, becoming closer to the map-frame goal, or measured world-space progress require appropriate visible physical/frame evidence; odometry distance alone is insufficient. If a material phrase has both a plausible supported intention/execution reading and a plausible unsupported realized-spatial-progress reading and the answer/context does not resolve the reading, list that exact phrase in ambiguous_spans. Do not select a reading based on answer style or expected method. Do not mark that same ambiguous proposition as definitively unsupported; independently unequivocal unsupported propositions still count. Preserve independently clear required units. Ambiguity is not a supported pass, and it is not automatically a definite failure. It requires the prospectively specified unresolved/adjudication policy. Ordinary explicitly scoped odometry measurements and configured rules are not ambiguous merely because physical truth remains unknown.
Quote every unequivocally unsupported material proposition in unsupported_spans and every overlicensed mechanistic/diagnostic proposition in overlicensed_spans. Each quoted string must occur literally in the answer. overlicensed_spans must be a subset of unsupported_spans. unsupported_material equals whether unsupported_spans is nonempty; overlicensed_specificity equals whether overlicensed_spans is nonempty. ambiguous_spans contains exact answer quotations only, never evidence quotations or invented paraphrases. Do not use a broad quotation to label an ambiguous and an independently unsupported proposition as the same proposition. These span lists support auditing; they are not proof that all material claims were extracted. Return all seven required fields.'''
PROMPT = PREVIOUS_PROMPT + '\n' + AMBIGUITY_POLICY
SCHEMA = copy.deepcopy(OLD_SCHEMA)
for name in ('unsupported_spans', 'overlicensed_spans', 'ambiguous_spans'):
    SCHEMA['properties'][name] = {'type':'array','items':{'type':'string'}}
    SCHEMA['required'].append(name)


def validate(value, payload):
    if type(value) is not dict or set(value)!=set(SCHEMA['required']):
        raise ValueError('exact span-aware evaluator object required')
    old_validate({k:value[k] for k in OLD_SCHEMA['required']},payload)
    for name in ('unsupported_spans','overlicensed_spans','ambiguous_spans'):
        spans=value[name]
        if type(spans) is not list or any(type(s) is not str or not s.strip() or s not in payload['answer'] for s in spans):
            raise ValueError('literal nonempty answer quotations required')
        if len(spans)!=len(set(spans)):raise ValueError('duplicate quoted spans')
    if set(value['overlicensed_spans'])-set(value['unsupported_spans']):
        raise ValueError('specificity quotations must also be unsupported')
    if set(value['ambiguous_spans']) & set(value['unsupported_spans']):
        raise ValueError('one proposition cannot be both ambiguous and definitively unsupported')
    if value['unsupported_material']!=bool(value['unsupported_spans']) or value['overlicensed_specificity']!=bool(value['overlicensed_spans']):
        raise ValueError('component flags must match quoted assertions')
    return value
